---
name: frc-auto
description: "Build, revise, and debug FRC autonomous routines, trajectories, mechanism events, and recovery behavior. Adapt to the project's actual planner and architecture, including incomplete early-season mechanisms."
---

# Develop autonomous behavior

Inspect current autonomous APIs, installed planner version, trajectory sources/generated files, field coordinates/alliance conventions, and mechanism interfaces. Verify season-specific field/rules from current official sources when needed. Do not choose Choreo, PathPlanner, commands, or a state-machine framework merely because a prior robot used it.

Translate the requested strategy into a sequence/graph with explicit starting conditions, driving segments, mechanism actions, completion conditions, time budgets, interruption, and fallback behavior. Keep operator intent separate from measured success. A missed pickup, failed homing, invalid pose, or unreachable mechanism target must not silently become success.

Define interface agreements with concurrently developed mechanisms: units, goal ownership, readiness, completion and failures. Prototype/stub mechanisms can allow sequencing work, but must visibly report unavailable behavior and cannot establish physical readiness.

Inspect both trajectory assets and runtime code. Check start-pose reset, coordinate frame, alliance flipping exactly once, path names/segments, event ordering, concurrent actions, outputs left running, timeout coverage, and total routine duration. Use the actual installed planner to regenerate assets when available; do not hand-edit generated samples and call them regenerated. If generation is unavailable, preserve source changes and report what remains unverified.

Use `frc-verify` for sequencing, cancellation, faults and integration. Test missed/delayed inputs with fake mechanisms before accurate CAD/physics exists. Explain simulation assumptions and prepare a field test with starting pose, configuration, expected events and abort/recovery. Real autonomous reliability requires recorded hardware trials.

Hand off the strategy, implementation/assets, assumptions, software evidence, and field-test steps. Use `frc-diagnose` for logged failures and `frc-performance` for measured timing improvements.
