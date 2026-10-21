#!/usr/bin/env python3
"""Small, dependency-free helpers for FRC development. See docs/tooling.md."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from uuid import uuid4

from wpilog import LogError, inspect_log


class ToolError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def config(root):
    path = root / "frc-toolkit.json"
    if not path.exists():
        return {}
    value = read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ToolError("frc-toolkit.json must be an object with schema_version 1")
    return value


def git(root, *args, binary=False):
    executable = shutil.which("git")
    if not executable:
        raise ToolError("Git is unavailable; install Git for workspace/branch inspection")
    result = subprocess.run([executable, "--no-optional-locks", "-C", str(root), *args],
                            capture_output=True, timeout=30)
    if result.returncode:
        raise ToolError(result.stderr.decode("utf-8", "replace").strip() or "Git command failed")
    return result.stdout if binary else result.stdout.decode("utf-8", "replace").strip()


def resolve_commit(root, ref):
    return git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")


def _paths(data):
    return [os.fsdecode(item) for item in data.split(b"\0") if item]


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def workspace(root, base=None):
    result = {"requested_root": str(root), "observed_at": now(), "git_available": bool(shutil.which("git")),
              "is_repository": False, "visibility": "local checkout and local refs only; no remote fetch performed"}
    if not result["git_available"]:
        result["error"] = "Git is unavailable"
        return result
    try:
        top = Path(git(root, "rev-parse", "--show-toplevel"))
    except ToolError as exc:
        result["error"] = str(exc)
        return result
    result.update(is_repository=True, root=str(top), branch=git(top, "branch", "--show-current") or None)
    try:
        head = resolve_commit(top, "HEAD")
    except ToolError:
        head = None
    result["commit"] = head
    tracked = _paths(git(top, "diff", "--name-only", "-z", "HEAD", binary=True)) if head else []
    tracked += _paths(git(top, "diff", "--name-only", "-z", binary=True))
    tracked += _paths(git(top, "diff", "--cached", "--name-only", "-z", binary=True))
    # In unborn repositories include staged files as well as untracked ones.
    if not head:
        tracked = _paths(git(top, "ls-files", "-z", binary=True))
    untracked = _paths(git(top, "ls-files", "--others", "--exclude-standard", "-z", binary=True))
    changed = sorted(set(tracked + untracked))
    status = git(top, "status", "--porcelain=v1", "-z", binary=True)
    result.update(dirty=bool(status), changed_paths=changed, untracked_paths=untracked)
    digest = hashlib.sha256((head or "unborn").encode())
    # Include staged and unstaged diffs, so a staged change reverted in the worktree is still represented.
    for args in (("diff", "--binary"), ("diff", "--cached", "--binary")):
        digest.update(git(top, *args, binary=True))
    for name in changed:
        path = top / name
        digest.update(os.fsencode(name))
        if path.is_symlink():
            digest.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            digest.update(file_hash(path).encode())
        else:
            digest.update(b"missing-or-directory")
    result["fingerprint"] = digest.hexdigest()
    result["worktrees"] = git(top, "worktree", "list", "--porcelain").splitlines()
    target = base if base is not None else config(root).get("integration_target")
    result["base"] = target
    if target:
        if not head:
            raise ToolError("Cannot compare an unborn branch to a base")
        base_sha = resolve_commit(top, target)
        common = git(top, "merge-base", head, base_sha)
        result.update(base_commit=base_sha, merge_base=common,
                      branch_changed_paths=_paths(git(top, "diff", "--name-only", "-z", common, head, binary=True)))
    return result


def overlap(root, base, others):
    current = workspace(root, base)
    if not current["is_repository"] or not current.get("commit"):
        raise ToolError("Branch overlap requires a Git repository with a commit")
    top = Path(current["root"])
    own = set(current["branch_changed_paths"]) | set(current["changed_paths"])
    comparisons = []
    for other in others:
        sha = resolve_commit(top, other)
        common = git(top, "merge-base", current["base_commit"], sha)
        paths = _paths(git(top, "diff", "--name-only", "-z", common, sha, binary=True))
        comparisons.append({"ref": other, "commit": sha, "merge_base": common,
                            "changed_paths": paths, "overlapping_paths": sorted(own & set(paths))})
    return {"workspace": current, "comparisons": comparisons,
            "limitation": "File overlap only; no guarantee of semantic compatibility or mergeability"}


def exclusive_json(directory, prefix, value):
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = directory / f"{prefix}-{stamp}-{uuid4().hex[:12]}.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return path


def resolve_inside(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ToolError(f"Path must remain inside project: {value}")
    return path


def tail(stream, limit=16000):
    stream.flush()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(max(0, size - limit))
    return {"text": stream.read().decode("utf-8", "replace"), "truncated": size > limit, "bytes": size}


def run_check(argv, cwd, timeout):
    """Bound output memory and terminate the check's process group on POSIX timeout."""
    start = time.monotonic()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        kwargs = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, **kwargs)
        except OSError as exc:
            return {"status": "error", "error": str(exc), "exit_code": None,
                    "elapsed_seconds": time.monotonic() - start}
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name != "nt":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                # A Windows batch/Gradle check may spawn descendants.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
                if process.poll() is None:
                    process.kill()
            process.wait()
        return {"status": "timeout" if timed_out else ("passed" if process.returncode == 0 else "failed"),
                "exit_code": process.returncode, "elapsed_seconds": time.monotonic() - start,
                "stdout": tail(stdout), "stderr": tail(stderr)}


def validate_check(root, name, value):
    if not isinstance(value, dict) or not isinstance(value.get("scope"), str) or not value["scope"].strip():
        raise ToolError(f"Check {name} must declare a nonempty scope")
    argv = value.get("windows_argv", value.get("argv")) if os.name == "nt" else value.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
        raise ToolError(f"Check {name} requires a nonempty argv array of strings (no shell command)")
    timeout = value.get("timeout_seconds", 120)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ToolError(f"Check {name} timeout must be finite and positive")
    cwd_value = value.get("cwd", ".")
    if not isinstance(cwd_value, str):
        raise ToolError(f"Check {name} cwd must be a project-relative path")
    cwd = resolve_inside(root, cwd_value)
    if not cwd.is_dir():
        raise ToolError(f"Check {name} cwd does not exist: {cwd}")
    return [item.replace("{python}", sys.executable) for item in argv], cwd, timeout


def verify(root, names):
    settings = config(root)
    checks = settings.get("verification", {})
    if not isinstance(checks, dict) or not checks:
        raise ToolError("No verification checks configured; inspect the project and configure explicit checks")
    chosen = names or list(checks)
    prepared = []
    for name in chosen:
        if name not in checks:
            raise ToolError(f"Unknown verification check: {name}")
        prepared.append((name, *validate_check(root, name, checks[name])))
    before = workspace(root)
    config_hash = file_hash(root / "frc-toolkit.json")
    results = []
    for name, argv, cwd, timeout in prepared:
        print(f"Running {name} ({checks[name]['scope']})", file=sys.stderr, flush=True)
        result = run_check(argv, cwd, timeout)
        results.append(dict(result, name=name, scope=checks[name]["scope"], argv=argv, cwd=str(cwd)))
    try:
        after = workspace(root)
    except (ToolError, OSError, ValueError, subprocess.SubprocessError) as exc:
        # Keep the check evidence even if a concurrent change breaks configuration inspection.
        after = {"observed_at": now(), "snapshot_error": str(exc), "fingerprint": None}
    config_path = root / "frc-toolkit.json"
    after_config_hash = file_hash(config_path) if config_path.is_file() else None
    changed = ("snapshot_error" in after or before.get("fingerprint") != after.get("fingerprint")
               or config_hash != after_config_hash)
    passed = all(item["status"] == "passed" for item in results)
    status = "invalidated" if changed else ("passed" if passed else "failed")
    report = {"schema_version": 1, "created_at": now(), "status": status,
              "project_kind": settings.get("project_kind", "unknown"), "config_sha256": config_hash,
              "workspace_before": before, "workspace_after": after, "checks": results,
              "source_changed_during_checks": changed,
              "provenance_limit": None if before.get("fingerprint") else "No Git source fingerprint; repository provenance unavailable",
              "interpretation": "Process results only; inspect test counts/coverage. Scope does not imply physical validation."}
    path = exclusive_json(root / ".frc" / "verification", "verification", report)
    return dict(report, report_path=str(path)), status == "passed"


def artifact_record(root, value):
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_file():
        raise ToolError(f"Artifact/profile file does not exist: {value}")
    return {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
            "sha256": file_hash(path), "bytes": path.stat().st_size}


def experiment(root, slug, question, hardware=None, settings=(), artifacts=(), operator=None):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 64:
        raise ToolError("Experiment slug must be lowercase letters/digits separated by hyphens, at most 64 characters")
    if not question.strip():
        raise ToolError("Experiment question must not be blank")
    parsed = {}
    for setting in settings:
        key, separator, value = setting.partition("=")
        if not separator or not key.strip() or key in parsed:
            raise ToolError("Settings must be unique nonempty key=value pairs")
        parsed[key] = value
    profile = artifact_record(root, hardware) if hardware else {"status": "unknown"}
    if hardware:
        document = read_json(root / hardware)
        if not isinstance(document, dict):
            raise ToolError("Hardware profile must be a JSON object")
        profile.update(name=document.get("name"), revision=document.get("revision"), status=document.get("status", "unknown"))
    provenance = workspace(root)
    record = {"schema_version": 1, "created_at": now(), "slug": slug, "question": question,
              "status": "planned", "operator": operator, "hardware": profile,
              "workspace": provenance, "planned_settings": parsed, "actual_settings": None,
              "artifacts": [artifact_record(root, item) for item in artifacts],
              "measurements": [], "observations": [], "conclusion": None,
              "note": "Unexecuted plan. Fill results only from observations; planned settings are not proof of applied settings."}
    path = exclusive_json(root / "docs" / "robot" / "experiments", slug, record)
    return {"record_path": str(path), "record": record}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="Project root; defaults to this toolkit's root")
    commands = result.add_subparsers(dest="command", required=True)
    item = commands.add_parser("workspace", help="Inspect local Git state without fetching or changing branches")
    item.add_argument("--base", help="Target ref; defaults to configured integration_target if any")
    item = commands.add_parser("overlap", help="Compare file changes across local branch snapshots")
    item.add_argument("--base", required=True)
    item.add_argument("--other", action="append", required=True)
    item = commands.add_parser("verify", help="Run configured checks and record provenance")
    item.add_argument("--check", action="append", help="Check name, repeatable; defaults to all configured checks")
    item = commands.add_parser("experiment", help="Create a separate, unexecuted experiment record")
    item.add_argument("slug")
    item.add_argument("--question", required=True)
    item.add_argument("--hardware", help="JSON hardware profile; absence is recorded as unknown")
    item.add_argument("--operator")
    item.add_argument("--setting", action="append", default=[])
    item.add_argument("--artifact", action="append", default=[])
    item = commands.add_parser("log", help="Inspect standard WPILOG signals without changing the log")
    item.add_argument("file", type=Path)
    item.add_argument("--list", action="store_true", help="List declared signal lifetimes and sample counts")
    item.add_argument("--match", default="*", help="Case-sensitive glob for --list")
    item.add_argument("--signal", action="append", default=[], help="Case-sensitive signal-name glob; repeatable")
    item.add_argument("--start", type=float, help="Inclusive absolute log timestamp in seconds")
    item.add_argument("--end", type=float, help="Inclusive absolute log timestamp in seconds")
    item.add_argument("--limit", type=int, default=2000, help="Maximum catalog entries or selected samples; 1..100000")
    item.add_argument("--changes", action="store_true", help="Filter repeated values after selecting earliest limited samples")
    item.add_argument("--stats", action="store_true", help="Scalar sample statistics, instead of raw samples")
    item.add_argument("--max-values", type=int, default=200000, help="Per-signal percentile storage cap; 1..1000000")
    item.add_argument("--allow-truncated", action="store_true", help="Analyze intact prefix of a log with an interrupted final record; mark incomplete")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if not root.is_dir():
            raise ToolError(f"Project root does not exist: {root}")
        passed = True
        if args.command == "workspace":
            result = workspace(root, args.base)
        elif args.command == "overlap":
            result = overlap(root, args.base, args.other)
        elif args.command == "verify":
            result, passed = verify(root, args.check)
        elif args.command == "experiment":
            result = experiment(root, args.slug, args.question, args.hardware, args.setting, args.artifact, args.operator)
        else:
            if args.list and (args.signal or args.stats or args.changes or args.start is not None or args.end is not None):
                raise ToolError("--list is catalog-only; do not combine with extraction/window/statistics flags")
            if args.stats and args.changes:
                raise ToolError("--stats and --changes are separate output modes")
            result = inspect_log(args.file, patterns=args.signal, list_only=args.list, match=args.match,
                                 start=args.start, end=args.end, limit=args.limit, changes=args.changes,
                                 stats=args.stats, max_values=args.max_values, allow_truncated=args.allow_truncated)
            passed = not result.get("missing_selectors")
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if passed else 1
    except (ToolError, LogError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc), "command": args.command}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
