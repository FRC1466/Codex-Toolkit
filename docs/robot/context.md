# Current project context

This checkout is the source of an FRC development toolkit. There is no robot source, selected robot architecture, confirmed hardware profile, controller layout, or game-specific behavior here yet. `frc-toolkit.json` declares `project_kind: toolkit`.

When adopting into robot code, replace this paragraph with the current architecture and links to relevant source. Record current facts, not a wishlist. Treat historical robots as references rather than requirements.

## Maintained references

- Hardware: add one record per physical prototype or robot revision under `hardware/` when hardware exists. Use [the hardware example](examples/hardware.json) as a small documentation format. This is not runtime configuration.
- Interfaces: add only cross-task contracts under `interfaces/` when needed. Include API location, units/frame, command/output ownership, readiness/completion semantics, cancellation, fault behavior, and consuming tasks. Keep code the authority for executable behavior.
- Decisions: add a short file under `decisions/` for consequential accepted choices. Include date, reason, affected interfaces, and what decision it supersedes. A proposal is not an accepted decision.
- Experiments: `tools/frc/frc.py experiment` creates a separate JSON record for each run. Complete measurements and conclusions from actual observations. Link artifacts without assuming all students have the same absolute paths.

Create directories and documents when they have content; do not create empty records for every small change. Update the relevant reference in the same change that invalidates it. Git history preserves old revisions; use explicit superseded links when the reason matters.

## Team coordination

The proposed shared coordination surface is GitHub issues/PRs. No repository is configured or connected by this toolkit. The included issue/PR templates are available after these files are committed to a GitHub repository. Configure actual access and branch protection separately.

Before parallel work, agree on a small interface or land the shared foundation first. For dependent branches, record their base/dependency and merge order. Inspect combined behavior even when Git reports no text conflicts.

For physical tests, record the operator, installed hardware revision, code revision and dirty state, and settings. Agree who controls the robot before the session; this toolkit does not enforce reservations.
