---
name: frc-task
description: "Scope substantial FRC development, split work among students, establish interfaces, and coordinate branches. Use for new robot features or parallel work; skip planning ceremony for trivial edits."
---

# Start an FRC task

Users need not request this workflow by name. Infer scope from their request and carry out authorized work after the necessary discovery.

For Team 1466 work, follow the decision and priority guidance in [1466's preferences](../frc-prototype/references/1466-subsystem-preferences.md#how-to-work).

1. Read the applicable instructions, relevant source, `frc-toolkit.json`, and relevant current context under `docs/robot/`. Identify the season, prototype/robot revision, language, installed library versions, and architecture from evidence. Do not import a historical robot's design by default.
2. Establish checkout, dirty state, branch, and explicit or configured target. When an existing Python 3.10+ interpreter is available, use `tools/frc/frc.py workspace` from the repository root (or an absolute script path with `--root`). Otherwise inspect equivalent read-only Git/file information through available tools. A missing target is unknown, not automatically `main`. Do not run Git mutations merely to inspect the workspace or ask the user to open a terminal/install a runtime.
3. For shared work, inspect available GitHub issues/PRs through connected tools or an authenticated CLI when available. Read-only discovery is appropriate; creating/updating issues or messaging teammates requires the user's authorization. If access is unavailable, use supplied context, state the visibility gap, and continue independent local work. Local refs are snapshots; no helper silently fetches remote changes.
4. Define the smallest useful outcome and observable acceptance criteria. Separate facts from estimates and unknowns. Identify which missing facts actually block progress; implement independent parts while asking about blockers. Do not demand finished CAD or a complete robot to start a prototype.
5. Where concurrent work depends on a shared API, agree on units/frame, input/output ownership, readiness/completion, cancellation, and faults. Land a small common foundation or record the dependency and merge order. Prefer natural task boundaries over rigid file ownership.
6. Use a separate checkout for concurrent tasks; reuse an appropriate existing checkout before making one. Follow project branch conventions (`codex/` by default for new branches). Never switch a shared working directory out from under another task. Do not spawn additional agents unless the user or applicable instructions authorize delegation.

For a small feature, explain the approach briefly in chat and implement. Create a durable task/design record only when someone else needs it to coordinate or when the decision would otherwise be lost. Avoid a single branch-local task ledger that everyone edits.

Finish with the changed behavior, dependency/interface implications, exact verification, and remaining hardware tests. Use `frc-verify` after code changes and `frc-integrate` when combining or reviewing branches. Preserve human ownership of engineering decisions; an agent's proposal is not a team decision.
