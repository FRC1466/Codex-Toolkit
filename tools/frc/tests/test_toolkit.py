"""Integration tests use isolated temporary repositories; no hardware or network."""

from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))
import frc
import wpilog


def invoke(root, *args):
    return subprocess.run([sys.executable, str(TOOLS / "frc.py"), "--root", str(root), *args],
                          capture_output=True, text=True, timeout=30, cwd=root)


def write_config(root, checks=None, **values):
    result = {"schema_version": 1, "verification": checks or {}, **values}
    (root / "frc-toolkit.json").write_text(json.dumps(result), encoding="utf-8")


def check(code, **values):
    return {"scope": "fixture-logic", "argv": ["{python}", "-c", code], "timeout_seconds": 10, **values}


def packet(entry, payload, timestamp=0):
    widths = [max(1, (value.bit_length() + 7) // 8) for value in (entry, len(payload), timestamp)]
    flags = (widths[0] - 1) | ((widths[1] - 1) << 2) | ((widths[2] - 1) << 4)
    return bytes([flags]) + b"".join(value.to_bytes(width, "little")
        for value, width in zip((entry, len(payload), timestamp), widths)) + payload


def string(value):
    data = value.encode("utf-8")
    return struct.pack("<I", len(data)) + data


def start(entry, name, kind, timestamp=0, metadata=""):
    return packet(0, b"\0" + struct.pack("<I", entry) + string(name) + string(kind) + string(metadata), timestamp)


def log_file(path, *parts):
    path.write_bytes(b"WPILOG\x00\x01\x00\x00\x00\x00" + b"".join(parts))
    return path


class FilesystemCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="frc fixture ")
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()


@unittest.skipUnless(shutil.which("git"), "Git is required for repository integration tests")
class GitTests(FilesystemCase):
    def git(self, *args):
        result = subprocess.run([shutil.which("git"), "-C", str(self.root), *args],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def setUp(self):
        super().setUp()
        self.git("init", "--initial-branch=main")
        self.git("config", "user.name", "Toolkit Tests")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "core.autocrlf", "false")
        (self.root / ".gitignore").write_text(".frc/\n", encoding="utf-8")
        (self.root / "source.txt").write_text("baseline\n", encoding="utf-8")
        write_config(self.root)
        self.commit("baseline")

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-m", message)

    def test_clean_and_dirty_fingerprints(self):
        before = frc.workspace(self.root)
        self.assertFalse(before["dirty"])
        self.assertEqual(before["branch"], "main")
        (self.root / "source.txt").write_text("changed\n", encoding="utf-8")
        (self.root / "file with spaces.txt").write_text("new", encoding="utf-8")
        after = frc.workspace(self.root)
        self.assertNotEqual(before["fingerprint"], after["fingerprint"])
        self.assertEqual(set(after["changed_paths"]), {"source.txt", "file with spaces.txt"})
        self.assertIsNone(after["base"])

    def test_staged_then_reverted_worktree_is_still_dirty(self):
        (self.root / "source.txt").write_text("staged change\n", encoding="utf-8")
        self.git("add", "source.txt")
        (self.root / "source.txt").write_text("baseline\n", encoding="utf-8")
        result = frc.workspace(self.root)
        self.assertTrue(result["dirty"])
        self.assertIn("source.txt", result["changed_paths"])

    def test_overlap_includes_uncommitted_paths_and_reports_commits(self):
        self.git("checkout", "-b", "other")
        (self.root / "source.txt").write_text("other student's change\n", encoding="utf-8")
        self.commit("other work")
        self.git("checkout", "main")
        self.git("checkout", "-b", "own")
        (self.root / "source.txt").write_text("local work\n", encoding="utf-8")
        result = frc.overlap(self.root, "main", ["other"])
        self.assertEqual(result["comparisons"][0]["overlapping_paths"], ["source.txt"])
        self.assertEqual(len(result["comparisons"][0]["commit"]), 40)
        self.assertEqual(self.git("branch", "--show-current"), "own")

    def test_disjoint_branches_and_configured_target(self):
        self.git("checkout", "-b", "other")
        (self.root / "different.txt").write_text("other", encoding="utf-8")
        self.commit("different work")
        self.git("checkout", "main")
        write_config(self.root, integration_target="main")
        result = frc.overlap(self.root, "main", ["other"])
        self.assertEqual(result["comparisons"][0]["overlapping_paths"], [])
        self.assertEqual(frc.workspace(self.root)["base"], "main")

    def test_invalid_target_does_not_fall_back(self):
        with self.assertRaises(frc.ToolError):
            frc.workspace(self.root, "missing-branch")

    def test_verification_records_actual_revision_and_detects_mutation(self):
        write_config(self.root, {"mutation": check("from pathlib import Path; Path('source.txt').write_text('mutated')")})
        self.commit("configure mutation check")
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "invalidated")
        self.assertTrue(report["source_changed_during_checks"])
        self.assertEqual(report["checks"][0]["status"], "passed")
        self.assertNotEqual(report["workspace_before"]["fingerprint"], report["workspace_after"]["fingerprint"])
        self.assertTrue(Path(report["report_path"]).exists())

    def test_verification_pass_does_not_change_source(self):
        write_config(self.root, {"ok": check("print('3 fixture assertions passed')")})
        self.commit("configure passing check")
        before = self.git("status", "--porcelain")
        result = invoke(self.root, "verify", "--check", "ok")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["checks"][0]["scope"], "fixture-logic")
        self.assertIsNone(report["provenance_limit"])
        self.assertEqual(before, self.git("status", "--porcelain"))

    def test_unborn_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            subprocess.run([shutil.which("git"), "init", "--initial-branch=main", str(path)], check=True, capture_output=True)
            (path / "pending.txt").write_text("not committed", encoding="utf-8")
            result = frc.workspace(path)
            self.assertTrue(result["is_repository"])
            self.assertIsNone(result["commit"])
            self.assertIn("pending.txt", result["changed_paths"])


class UtilityTests(FilesystemCase):
    def test_workspace_outside_git_is_explicit(self):
        result = frc.workspace(self.root)
        self.assertFalse(result["is_repository"])
        self.assertIn("error", result)

    def test_root_does_not_depend_on_caller_directory(self):
        self.assertEqual(frc.parser().parse_args(["workspace"]).root, ROOT)

    def test_empty_checks_cannot_pass(self):
        write_config(self.root)
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 2)
        self.assertIn("No verification checks", result.stderr)

    def test_checks_validate_before_any_execution(self):
        write_config(self.root, {"first": check("from pathlib import Path; Path('should-not-exist').touch()"),
                                 "invalid": {"scope": "test", "argv": "echo unsafe"}})
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "should-not-exist").exists())

    def test_failed_check_does_not_hide_later_results(self):
        write_config(self.root, {"bad": check("raise SystemExit(7)"), "ok": check("print('ok')")})
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual([item["status"] for item in report["checks"]], ["failed", "passed"])
        self.assertEqual(report["checks"][0]["exit_code"], 7)
        self.assertIsNotNone(report["provenance_limit"])

    def test_timeout_is_failure(self):
        write_config(self.root, {"slow": check("import time; time.sleep(10)", timeout_seconds=.15)})
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["checks"][0]["status"], "timeout")

    def test_missing_executable_is_failure(self):
        write_config(self.root, {"missing": {"scope": "test", "argv": ["frc-nonexistent-executable-12345"]}})
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["checks"][0]["status"], "error")

    def test_output_is_bounded_and_arguments_are_literal(self):
        write_config(self.root, {"output": check("import sys; print('x'*20000); print(sys.argv[1])")})
        config = frc.read_json(self.root / "frc-toolkit.json")
        config["verification"]["output"]["argv"].append("$(not-a-command); literal")
        (self.root / "frc-toolkit.json").write_text(json.dumps(config), encoding="utf-8")
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["checks"][0]["stdout"]
        self.assertTrue(output["truncated"])
        self.assertLessEqual(len(output["text"]), 16000)
        self.assertIn("$(not-a-command); literal", output["text"])

    def test_check_paths_cannot_escape(self):
        with self.assertRaises(frc.ToolError):
            frc.validate_check(self.root, "outside", check("pass", cwd=".."))

    def test_bad_timeout_is_rejected(self):
        for timeout in (0, -1, True, float("nan"), "120"):
            with self.subTest(timeout=timeout), self.assertRaises(frc.ToolError):
                frc.validate_check(self.root, "bad", check("pass", timeout_seconds=timeout))

    def test_unknown_check_does_not_run_other_checks(self):
        write_config(self.root, {"ok": check("pass")})
        self.assertEqual(invoke(self.root, "verify", "--check", "unknown").returncode, 2)

    def test_experiment_captures_hashes_and_preserves_unknowns(self):
        (self.root / "hardware.json").write_text('{"name":"bench-a","revision":2,"status":"prototype"}', encoding="utf-8")
        (self.root / "result.txt").write_text("trial observation", encoding="utf-8")
        result = frc.experiment(self.root, "intake-a", "Does it acquire?", "hardware.json", ["gap_mm=40"], ["result.txt"], "Student")
        record = json.loads(Path(result["record_path"]).read_text())
        self.assertEqual(record["hardware"]["revision"], 2)
        self.assertEqual(record["artifacts"][0]["sha256"], frc.file_hash(self.root / "result.txt"))
        self.assertEqual(record["status"], "planned")
        self.assertIsNone(record["actual_settings"])
        self.assertIsNone(record["conclusion"])
        self.assertEqual(record["planned_settings"], {"gap_mm": "40"})

    def test_concurrent_experiments_do_not_overwrite(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            paths = list(pool.map(lambda _: frc.experiment(self.root, "same-trial", "Question")["record_path"], range(8)))
        self.assertEqual(len(set(paths)), 8)
        for path in paths:
            self.assertEqual(json.loads(Path(path).read_text())["hardware"], {"status": "unknown"})

    def test_experiment_bad_input_does_not_create_record(self):
        with self.assertRaises(frc.ToolError):
            frc.experiment(self.root, "../escape", "Question")
        with self.assertRaises(frc.ToolError):
            frc.experiment(self.root, "trial", "Question", settings=["a=1", "a=2"])
        with self.assertRaises(frc.ToolError):
            frc.experiment(self.root, "trial", "Question", artifacts=["missing.log"])
        self.assertFalse((self.root / "docs").exists())

    def test_malformed_config_is_error(self):
        (self.root / "frc-toolkit.json").write_text("[]", encoding="utf-8")
        with self.assertRaises(frc.ToolError):
            frc.config(self.root)

    def test_config_deleted_during_checks_keeps_invalidated_report(self):
        write_config(self.root, {"delete": check("from pathlib import Path; Path('frc-toolkit.json').unlink()")})
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "invalidated")
        self.assertEqual(report["checks"][0]["status"], "passed")
        self.assertTrue(Path(report["report_path"]).is_file())

    def test_config_rewritten_during_checks_is_invalidated(self):
        write_config(self.root, {"rewrite": check("from pathlib import Path; Path('frc-toolkit.json').write_text('not-json')")})
        result = invoke(self.root, "verify")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "invalidated")


class LogTests(FilesystemCase):
    def write(self, *parts):
        return log_file(self.root / "fixture.wpilog", *parts)

    def test_catalog_and_empty_declared_signal(self):
        path = self.write(start(1, "State", "string"), packet(1, b"Idle", 1000000), start(2, "Empty", "double"))
        result = wpilog.inspect_log(path, list_only=True, match="*", limit=1)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["total_entries"], 2)
        empty = wpilog.inspect_log(path, patterns=["Empty"])
        self.assertEqual(empty["missing_selectors"], [])
        self.assertEqual(empty["samples_in_window"], 0)

    def test_window_initial_values_and_changes(self):
        path = self.write(start(1, "State", "string"), packet(1, b"Idle", 1000000),
                          packet(1, b"Idle", 2000000), packet(1, b"Shooting", 3000000))
        result = wpilog.inspect_log(path, patterns=["State"], start=2, end=3, changes=True)
        self.assertEqual(result["initial_values"][0]["value"], "Idle")
        self.assertEqual([(row["timestamp"], row["value"]) for row in result["samples"]], [(3, "Shooting")])

    def test_out_of_order_and_limit_keep_earliest_timestamps(self):
        path = self.write(start(1, "State", "string"), packet(1, b"Third", 3000000),
                          packet(1, b"First", 1000000), packet(1, b"Second", 2000000))
        result = wpilog.inspect_log(path, patterns=["State"], limit=2)
        self.assertEqual([row["value"] for row in result["samples"]], ["First", "Second"])
        self.assertTrue(result["truncated"])
        self.assertEqual(result["log_first_timestamp"], 1)

    def test_initial_value_is_latest_by_timestamp_not_file_order(self):
        path = self.write(start(1, "State", "string"), packet(1, b"Later", 1500000), packet(1, b"Earlier", 500000))
        result = wpilog.inspect_log(path, patterns=["State"], start=2)
        self.assertEqual(result["initial_values"][0]["value"], "Later")

    def test_entry_reuse_does_not_mix_types_or_statistics(self):
        path = self.write(start(1, "Value", "double"), packet(1, struct.pack("<d", 3), 1000000),
                          packet(0, b"\x01" + struct.pack("<I", 1)), start(1, "Value", "string"), packet(1, b"new", 2000000))
        result = wpilog.inspect_log(path, patterns=["Value"], stats=True)
        self.assertEqual([item["generation"] for item in result["selected_entries"]], [1, 2])
        self.assertEqual(result["statistics"][0]["numeric"]["mean"], 3)
        self.assertIsNone(result["statistics"][1]["numeric"])

    def test_metadata_update(self):
        path = self.write(start(1, "State", "string"), packet(0, b"\x02" + struct.pack("<I", 1) + string('{"unit":"state"}')),
                          packet(1, b"Idle", 1))
        result = wpilog.inspect_log(path, list_only=True)
        self.assertEqual(result["entries"][0]["metadata"], '{"unit":"state"}')

    def test_missing_selector_returns_available_data_and_exit_one(self):
        path = self.write(start(1, "State", "string"), packet(1, b"Idle", 1))
        result = invoke(self.root, "log", str(path), "--signal", "State", "--signal", "Missing")
        self.assertEqual(result.returncode, 1, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["missing_selectors"], ["Missing"])
        self.assertEqual(output["samples"][0]["value"], "Idle")

    def test_statistics_nonfinite_and_percentiles(self):
        values = [1.0, 2.0, 3.0, float("nan"), float("inf")]
        path = self.write(start(1, "LoopMS", "double"), *(packet(1, struct.pack("<d", value), i) for i, value in enumerate(values)))
        result = wpilog.inspect_log(path, patterns=["LoopMS"], stats=True)
        summary = result["statistics"][0]["numeric"]
        self.assertEqual(summary["finite_samples"], 3)
        self.assertEqual(summary["nonfinite_samples"], 2)
        self.assertAlmostEqual(summary["mean"], 2)
        self.assertAlmostEqual(summary["p95"], 2.9)
        self.assertTrue(summary["percentiles_exact"])
        samples = wpilog.inspect_log(path, patterns=["LoopMS"])["samples"]
        self.assertIsNone(samples[-1]["value"])
        json.dumps(result, allow_nan=False)

    def test_percentile_cap_is_disclosed_but_mean_uses_all_samples(self):
        path = self.write(start(1, "Time", "double"), *(packet(1, struct.pack("<d", value), value) for value in (1, 2, 3, 4, 5)))
        summary = wpilog.inspect_log(path, patterns=["Time"], stats=True, max_values=2)["statistics"][0]["numeric"]
        self.assertFalse(summary["percentiles_exact"])
        self.assertEqual(summary["p50"], 1.5)
        self.assertAlmostEqual(summary["mean"], 3)

    def test_large_finite_statistics_remain_json_serializable(self):
        path = self.write(start(1, "Extreme", "double"), packet(1, struct.pack("<d", -1e308), 1),
                          packet(1, struct.pack("<d", 1e308), 2))
        result = wpilog.inspect_log(path, patterns=["Extreme"], stats=True)
        self.assertEqual(result["statistics"][0]["numeric"]["mean"], 0)
        json.dumps(result, allow_nan=False)

    def test_standard_types_decode(self):
        cases = [("boolean", b"\x01", True), ("int64", struct.pack("<q", -42), -42),
                 ("float", struct.pack("<f", 1.5), 1.5), ("double", struct.pack("<d", 2.5), 2.5),
                 ("string", "héllo".encode(), "héllo"), ("boolean[]", b"\x00\x01", [False, True]),
                 ("int64[]", struct.pack("<qq", -1, 2), [-1, 2]), ("double[]", struct.pack("<dd", 1, 2), [1, 2]),
                 ("float[]", struct.pack("<ff", 1, 2), [1, 2]),
                 ("string[]", struct.pack("<I", 2) + string("a") + string("b"), ["a", "b"])]
        for kind, data, expected in cases:
            with self.subTest(kind=kind):
                self.assertEqual(wpilog.decode(kind, data), expected)

    def test_opaque_changes_use_whole_payload_hash(self):
        path = self.write(start(1, "Pose", "struct:Pose2d"), packet(1, b"a" * 32 + b"x", 1),
                          packet(1, b"a" * 32 + b"y", 2))
        samples = wpilog.inspect_log(path, patterns=["Pose"], changes=True)["samples"]
        self.assertEqual(len(samples), 2)
        self.assertFalse(samples[0]["value"]["decoded"])
        self.assertNotEqual(samples[0]["value"]["sha256"], samples[1]["value"]["sha256"])

    def test_truncated_log_does_not_emit_partial_success(self):
        path = self.write(start(1, "State", "string"), packet(1, b"Idle", 1))
        path.write_bytes(path.read_bytes()[:-1])
        result = invoke(self.root, "log", str(path), "--signal", "State")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Truncated", json.loads(result.stderr)["error"])

    def test_invalid_record_and_type_payloads_fail(self):
        invalid = [b"not a log", b"WPILOG\x00\x02\x00\x00\x00\x00",
                   b"WPILOG\x00\x01\x00\x00\x00\x00" + packet(2, b"x", 1)]
        for data in invalid:
            path = self.root / "invalid.wpilog"
            path.write_bytes(data)
            with self.assertRaises(wpilog.LogError):
                wpilog.inspect_log(path, list_only=True)
        for kind, data in (("double", b"short"), ("boolean", b"\x02"), ("double[]", b"x"), ("string[]", b"\xff\xff\xff\xff")):
            with self.subTest(kind=kind), self.assertRaises(wpilog.LogError):
                wpilog.decode(kind, data)

    def test_explicit_tail_recovery_marks_prefix_incomplete(self):
        path = self.write(start(1, "State", "string"), packet(1, b"Idle", 1000000), packet(1, b"Shooting", 2000000))
        path.write_bytes(path.read_bytes()[:-3])
        result = invoke(self.root, "log", str(path), "--signal", "State", "--allow-truncated")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertFalse(output["complete"])
        self.assertEqual([row["value"] for row in output["samples"]], ["Idle"])
        self.assertIn("intact prefix", output["warnings"][0])
        self.assertEqual(output["log_last_timestamp"], 1)

    def test_tail_recovery_does_not_hide_internal_corruption(self):
        path = self.write(packet(2, b"invalid inactive entry", 1))
        with self.assertRaises(wpilog.LogError):
            wpilog.inspect_log(path, list_only=True, allow_truncated=True)

    def test_truncated_header_is_not_recovered(self):
        path = self.root / "header.wpilog"
        path.write_bytes(b"WPILOG\x00\x01\x04\x00\x00\x00x")
        with self.assertRaises(wpilog.LogError):
            wpilog.inspect_log(path, list_only=True, allow_truncated=True)

    def test_variable_width_record_headers(self):
        path = self.write(start(70000, "Long", "string"), packet(70000, b"x" * 300, 2**40))
        result = wpilog.inspect_log(path, patterns=["Long"])
        self.assertEqual(result["samples"][0]["timestamp"], 2**40 / 1e6)
        self.assertEqual(len(result["samples"][0]["value"]), 300)

    def test_invalid_bounds_and_modes(self):
        path = self.write()
        for kwargs in ({"start": 3, "end": 2}, {"start": float("nan")}, {"limit": 0}, {"max_values": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(wpilog.LogError):
                wpilog.inspect_log(path, patterns=["*"], **kwargs)
        self.assertEqual(invoke(self.root, "log", str(path), "--list", "--stats").returncode, 2)


class PackagingTests(unittest.TestCase):
    def test_all_nine_skills_are_discoverable_and_routed(self):
        skills = sorted((ROOT / ".agents" / "skills").iterdir())
        self.assertEqual(len(skills), 9)
        instructions = (ROOT / "AGENTS.md").read_text()
        for skill in skills:
            with self.subTest(skill=skill.name):
                text = (skill / "SKILL.md").read_text()
                self.assertTrue(text.startswith("---\n"))
                self.assertIn("name: " + skill.name + "\n", text)
                description = re.search(r'^description: (".*")$', text, re.MULTILINE)
                self.assertIsNotNone(description)
                self.assertTrue(json.loads(description.group(1)))
                self.assertNotIn("[TODO:", text)
                self.assertIn(skill.name, instructions)
                self.assertIn("allow_implicit_invocation: true", (skill / "agents" / "openai.yaml").read_text())

    def test_markdown_local_links_resolve(self):
        for path in list((ROOT / "docs").rglob("*.md")) + list(ROOT.glob("*.md")):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((path.parent / target.split("#")[0]).exists(), (path, target))

    def test_install_manifest_paths_are_complete_unique_and_contained(self):
        manifest = frc.read_json(ROOT / "toolkit-manifest.json")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["tracking_file"], "frc-toolkit.lock.json")
        sources = list(manifest["copy_files"]) + list(manifest["optional_templates"])
        destinations = sources.copy()
        for kind in ("merge_files", "create_if_missing"):
            sources.extend(item["source"] for item in manifest[kind])
            destinations.extend(item["destination"] for item in manifest[kind])
        self.assertEqual(len(destinations), len(set(destinations)))
        for relative in sources + destinations:
            with self.subTest(path=relative):
                self.assertFalse(PurePosixPath(relative).is_absolute())
                self.assertFalse(PureWindowsPath(relative).drive)
                self.assertNotIn("\\", relative)
                self.assertNotIn("..", PurePosixPath(relative).parts)
                self.assertNotIn(".git", PurePosixPath(relative).parts)
        for relative in sources:
            self.assertTrue((ROOT / relative).is_file(), relative)
            self.assertTrue((ROOT / relative).resolve().is_relative_to(ROOT))
        expected_skills = {str(path.relative_to(ROOT)).replace(os.sep, "/")
                           for path in (ROOT / ".agents" / "skills").rglob("*") if path.is_file()}
        copied_skills = {path for path in manifest["copy_files"] if path.startswith(".agents/skills/")}
        self.assertEqual(copied_skills, expected_skills)
        for source_only in manifest["source_only"]:
            for copied in manifest["copy_files"]:
                self.assertFalse(copied == source_only or
                                 (source_only.endswith("/") and copied.startswith(source_only)), copied)
        strategies = {item["destination"]: item["strategy"] for item in manifest["merge_files"]}
        self.assertEqual(strategies["AGENTS.md"], "managed-block")
        self.assertNotIn("frc-toolkit.json", manifest["copy_files"])

    def test_installed_payload_runs_without_source_checkout_dependencies(self):
        # Exercise the declared payload, not an executable installer or model's merge decisions.
        manifest = frc.read_json(ROOT / "toolkit-manifest.json")
        with tempfile.TemporaryDirectory(prefix="frc adopted project ") as folder:
            destination = Path(folder)
            for relative in manifest["copy_files"]:
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            for item in manifest["create_if_missing"]:
                target = destination / item["destination"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / item["source"], target)
            shutil.copyfile(ROOT / "templates/frc-toolkit.project.json", destination / "frc-toolkit.json")
            script = destination / "tools/frc/frc.py"
            # No --root: ensure the copied helper resolves its new project root itself.
            result = subprocess.run([sys.executable, str(script), "--help"], cwd=destination,
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([sys.executable, str(script), "workspace"], cwd=destination,
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Path(json.loads(result.stdout)["requested_root"]), destination.resolve())
            result = subprocess.run([sys.executable, str(script), "verify"], cwd=destination,
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertIn("No verification checks configured", result.stderr)
            log = log_file(destination / "fixture.wpilog", start(1, "State", "string"), packet(1, b"Idle", 1))
            result = subprocess.run([sys.executable, str(script), "log", str(log), "--signal", "State"],
                                    cwd=destination, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["samples"][0]["value"], "Idle")
            for source_only in ("tools/frc/tests", ".github/workflows/toolkit.yml", "README.md", "templates"):
                self.assertFalse((destination / source_only).exists())
            context = destination / "docs/robot/context.md"
            for target in re.findall(r"\]\(([^)]+)\)", context.read_text()):
                self.assertTrue((context.parent / target).exists())

    def test_active_configuration_checks_toolkit_only(self):
        settings = frc.config(ROOT)
        self.assertEqual(settings["project_kind"], "toolkit")
        self.assertIsNone(settings["integration_target"])
        self.assertEqual({value["scope"] for value in settings["verification"].values()}, {"toolkit"})
        for name, value in settings["verification"].items():
            frc.validate_check(ROOT, name, value)


if __name__ == "__main__":
    unittest.main()
