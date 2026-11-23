---
name: frc-verify
description: "Verify FRC behavior changes and prepare evidence for human review. Select meaningful build, logic, simulation, replay, and hardware checks appropriate to prototypes, V1, and integrated robot code."
---

# Verify what changed

Read the relevant change and project configuration. Select checks that could actually detect failure in the changed behavior. Do not add tests that merely mirror implementation or assert wording. Small nonbehavior edits may only need existing relevant checks.

For Team 1466, use [the team's compile, review, and test preferences](../frc-prototype/references/1466-subsystem-preferences.md#faults-diagnosis-and-review) when deciding how much verification to add.

Inspect build scripts/hooks before running commands. Formatting, generated source, and event-branch auto-commits are possible effects of a build. Use the intended checkout and preserve student work. Never equate 'run tests' with authorization to deploy or energize hardware.

Configured checks live under `verification` in `frc-toolkit.json`: each declares `scope`, `argv`, optional `windows_argv`, `cwd`, and `timeout_seconds`. Commands are argument arrays, not shell strings. Run `python3 tools/frc/frc.py verify --check <name>` from the root. See `docs/tooling.md`. This toolkit config only checks the toolkit; inspect and configure actual robot checks when adopting into robot code. If checks are absent, inspect the build and run suitable existing commands directly or configure explicit checks; never silently declare success.

The runner is optional and needs an existing Python 3.10+ interpreter. If unavailable, use available project build/test tools directly through Codex, record the commands/revision/results, and report the missing helper. Do not require a runtime installation or a user-opened terminal. An installed project's checks come from its configuration; source-only toolkit tests/CI are not installed robot checks.

Choose evidence for the stage and change:

- Logic: fake sensor/clock inputs, boundary units, state transitions, requested versus achieved state.
- Ownership: simultaneous requests, cancellation, manual/automatic handoff, disable/re-enable, stale targets.
- Failure paths: missing/stale sensor, unreachable setpoint, timeout, partial/no-op hardware, recovery.
- Integration: combined mechanisms, autonomous timing/termination, interface compatibility, target configuration.
- Physical performance: suitable simulation, logged experiment, and operator-run hardware test as needed.

Use the existing test framework where appropriate. Consider a focused reproducer when it can catch the original bug. An approximate physics model can test logic without validating real gains, collision clearance, or cycle time. Replay checks responses to recorded inputs, not the future physical inputs caused by new outputs.

Record exact commands, scope, code revision/dirty fingerprint, configuration, results and artifact paths. The helper detects source changes during checks; investigate invalidated results rather than calling them verified. A passing process exit alone does not prove that tests existed or cover the intended behavior. Inspect counts/reports and state material limitations.

End with behavior changed, meaningful checks passed/failed, and specific outstanding hardware/integration work. Do not claim robot verification from toolkit tests or compilation alone.
