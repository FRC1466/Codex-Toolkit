# Tool reference

Run `python3 tools/frc/frc.py --help`. Python 3.10+ and the standard library are sufficient. `py -3` works on Windows. Git commands require Git. There is no background agent, paid API, required MCP server, or automatic hardware connection.

These are optional helpers executed by Codex or a maintainer with an existing runtime; they are not prerequisites for installing the skills. A detected existing `python` or Codex-provided Python is also usable when its version is 3.10+. If no interpreter/decoder exists, use available file/Git/build tools and report which helper checks or binary-log analyses could not run. Installation does not install a runtime or ask the user to open a terminal.

The default project root is the directory containing this toolkit, not the caller's working directory. To inspect another checkout, put `--root /path/to/project` before the subcommand. File arguments for hardware and experiment artifacts are resolved relative to that project root; the log path is resolved relative to the calling directory unless absolute. All tools emit JSON; errors go to stderr. Exit codes: 0 success, 1 failed/invalidated checks or missing requested signals, 2 configuration/input/parse/execution errors. `workspace` returns success with `is_repository: false` and an explanation when Git/repository information is unavailable; callers must inspect that field.

## Workspace and overlap

`workspace [--base <ref>]` reports branch, commit, changed/untracked paths, worktrees, and a SHA-256 fingerprint of the commit, staged/unstaged diffs and changed file contents. Ignored files are not fingerprinted. A staged change reverted in the working tree still affects the fingerprint. An unborn branch has no commit but can have a dirty fingerprint. Outside Git, source fingerprinting is unavailable; this is reported explicitly.

The base is supplied explicitly or read from `integration_target` in `frc-toolkit.json`. An unset target remains unknown. When a base exists, report its exact commit, merge base, and branch changes since that merge base. Invalid refs fail instead of falling back to a guessed branch.

`overlap --base <ref> --other <ref> [--other <ref>...]` compares each branch's committed changes since its merge base with the target. This checkout's changed/untracked paths are included in its candidate changes. It reports common paths. Disjoint paths can still have incompatible behavior; common paths do not necessarily cause a conflict. There is no semantic mergeability detector or exclusive claim mechanism.

Inspection never fetches, switches, creates, resets, stages, commits, merges, pushes, or publishes. Remote-tracking refs are local snapshots. The `observed_at` timestamp describes inspection time, not the freshness of the server. Private work on another computer is invisible until shared. Source fingerprints are evidence snapshots, not an atomic lock against concurrent edits.

## Verification

`verify [--check <name>...]` executes named configured checks, or all configured checks if no names are supplied. It validates every selected check before launching any. Example configuration for a hypothetical Java robot (review its real build hooks before adopting):

```json
{
  "schema_version": 1,
  "project_kind": "robot",
  "integration_target": "origin/main",
  "verification": {
    "robot-tests": {
      "scope": "robot-logic",
      "argv": ["./gradlew", "test", "spotlessCheck"],
      "windows_argv": ["cmd.exe", "/d", "/c", "gradlew.bat", "test", "spotlessCheck"],
      "cwd": ".",
      "timeout_seconds": 180
    }
  }
}
```

Each check needs a nonempty scope and argument array. `{python}` expands to the current interpreter. Working directories must exist inside the project. Timeouts must be finite and positive. There is no general shell interpolation; an explicitly configured interpreter such as `cmd.exe` has its own semantics. Commands come from trusted project configuration, not log contents. No command is guessed or generated from a task name. Do not configure robot deployment, hardware motion, or unreviewed remote code as a verification check.

Checks run sequentially and independently; all selected checks are recorded even if one fails. A missing executable is a failed check with an error, never a pass. Timeout termination includes the POSIX process group or Windows process tree. Each process's stdout/stderr is stored in temporary files while running; the report keeps the final 16,000 bytes of each and marks truncation. Commands may have their own side effects; the runner is not a sandbox. Do not run the runner recursively as one of its own checks.

Reports are uniquely written under ignored `.frc/verification/`. They include commands, scopes, exit status/time, configuration hash, and workspace snapshots. A detected source/configuration change during checks marks the result `invalidated` even if processes passed. Ignored/generated files are outside the Git fingerprint. Without Git only configuration changes can be detected; reports state this limitation. A fingerprint does not include environment variables, remote dependency contents, firmware, or physical hardware. Record those separately when they matter.

This toolkit's active check has scope `toolkit`. Passing it does not verify robot code. A zero exit code does not prove tests existed, assertions covered the requested behavior, or hardware worked; agents must inspect the test output and choose relevant checks.

## Experiments

`experiment <slug> --question <text> [--hardware <profile.json>] [--setting key=value] [--artifact <file>] [--operator <name>]`

Creates one exclusively opened JSON file per invocation, with a UTC timestamp and random suffix under `docs/robot/experiments/`. Runs do not overwrite one another or append to a shared ledger. Slugs use lowercase letters/digits separated by hyphens. Repeated settings need unique names. Settings remain strings to avoid silently assigning units/types. Hardware and artifact files must exist if supplied; each gets its size, SHA-256, and relative path when inside the project. Absolute external paths are local provenance and need a shared reference before another student can access them.

The hardware profile is a documentation JSON object, not a runtime control configuration. The tool captures name/revision/status and the source file hash; it does not certify the contents or infer a missing revision. Keep confirmed/provisional/unknown facts and measurement sources in that profile. The example profile is explicitly an example with unknown facts. Omitted hardware is recorded as unknown.

New records have `status: planned`, `actual_settings: null`, no measurements/observations, and `conclusion: null`. No experiment is executed. After trials, record actual settings, outcomes with units, trial counts, failed attempts/exclusions, and supported conclusions. Preserve the original code/hardware provenance. Add follow-up artifact hashes using the same record format. Do not substitute a later build's revision for the code actually tested.

## WPILOG

`log <file> --list [--match <glob>] [--limit N]`

Lists entry ID/lifetime generation, name, type, last metadata, count and first/last sample timestamps. By default at most 2,000 entries are returned, with a total and truncation flag. A matching declared signal with zero samples is distinguished from an absent selector.

`log <file> --signal <glob> [--signal <glob>...] [--start S] [--end S] [--limit N] [--changes | --stats]`

Glob patterns are case-sensitive and match complete signal names. Missing selectors appear explicitly and produce exit 1, with available data still returned. All timestamps are absolute seconds from the log clock's origin, generally robot boot; windows are inclusive. They are not wall time or relative to the requested window. `initial_values` contains the latest known value before the start for each selected entry lifetime. That value may be stale; inspect its timestamp. No values are interpolated or forward-filled across entry lifetimes. A catalog entry's count/first/last describe the whole log; `samples_in_window` and `window_samples` describe the selection.

The reader streams the file, processes control records in file order, and handles out-of-order timestamps and reused entry IDs. Extraction keeps the earliest N matching samples in timestamp order, where N defaults to 2,000 and is capped at 100,000. `truncated` reports omitted samples. `--changes` filters repeated values after this sample cap, with initial values as the baseline; it does not scan arbitrarily far to find N transitions. It cannot substitute for an uncapped full event analysis. Use a smaller time window when truncated.

`--stats` reports sample-weighted scalar min/max/mean and linearly interpolated p50/p95/p99. Boolean and array signals are not converted into scalar numeric statistics. Numeric summaries exclude nonfinite values and count them. Nonfinite values in extracted data become JSON `null`; they are never silently treated as zero. Percentile storage is capped per entry lifetime (default 200,000, maximum 1,000,000). If capped, percentiles use the first finite samples in file order and `percentiles_exact: false`; min/max/mean still use all finite samples in the window. Do not treat capped percentiles as an unbiased estimate or sample-weighted means as time-weighted means.

Standard boolean, int64, float, double, string and their array types are decoded. Other payloads (including raw, structs, protobufs, schemas) remain opaque: byte size, SHA-256 and a short hex preview. Changes to opaque payloads are detected by hash but their meaning is not inferred. Primitive array/string output is bounded by record size, not by sample count; select narrow signals/windows before returning large arrays to an agent. The reader rejects malformed/truncated records and unsupported major versions, and caps record/extra-header sizes at 64 MiB. On a parse error, no partial success report is emitted. This does not read .hoot or Driver Station .dslog formats, infer units for undocumented signals, replay robot code, or implement schema-aware pose decoding.

Compare runs by extracting comparable signals/windows from each, aligning to an explicit event, and checking configuration/hardware comparability. There is no automatic causal diagnosis or controller tuning in the parser.

Reader format source: [WPILib Data Log File Format Specification](https://github.com/wpilibsuite/allwpilib/blob/main/datalog/doc/datalog.adoc). The implementation is independent and uses no copied WPILib source.

### Interrupted final records

By default, a truncated record is a parse error with exit 2 and no partial report. If an interrupted robot log has an incomplete final record, add `--allow-truncated` to analyze only the intact prefix. This returns `complete: false` and a warning identifying truncation. All counts/times/statistics apply to the intact prefix only, and missing selectors mean unobserved in that prefix. With this explicitly selected mode, exit 0 means prefix analysis succeeded; it does not mean the log is complete. Invalid file headers, malformed control records, and other internal corruption still fail. The reader never edits or repairs the input file. A record-boundary loss cannot be detected merely by parsing; `complete: true` means no incomplete record was encountered, not proof that an entire match was recorded.
