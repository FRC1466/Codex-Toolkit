---
name: frc-change
description: "Adapt FRC software after changes to gearing, geometry, sensors, motors, interfaces, libraries, or architecture. Trace invalidated assumptions and dependent student branches through prototype and robot revisions."
---

# Trace a changing design

Establish the before/after change from the user, current source, and revision records. Identify confirmed differences and unresolved values. A complete redesign may supersede the entire mechanism; do not preserve old abstractions simply because they existed last year.

Inspect affected paths rather than replacing a constant blindly:

- Sensor scaling, motor/mechanism units, gearing conventions, signs, and zero references.
- Physical/software limits, homing assumptions, setpoints and completion tolerances.
- Control gains, feedforward units, profiles, achievable acceleration/velocity, current and voltage constraints.
- Kinematics, camera/shooter transforms, collision assumptions, visualization, and simulation parameters.
- Shared APIs, controller bindings, automation, and autonomous timing/recovery.
- Logs, hardware profiles, tests, configuration selection, and dependent tasks/branches.

Not every item applies. Explain only material consequences. Validate formulas dimensionally; vendor feedback scaling may already convert to mechanism units, so avoid double conversion. Never automatically reuse gains after changing units or extrapolate a provisional physical limit into a confirmed one.

Implement the authorized change and preserve independent work. If an interface changes, describe its units, ownership, completion/failure behavior, dependent branches, and integration order. Use existing coordination access where authorized; otherwise prepare a handoff without sending messages.

Update current references with provenance in the same change. Keep old experiment evidence tied to the old revision. Create a decision record only when the reason needs to survive; mark superseded decisions explicitly.

Use `frc-verify` for new behavior and regression scenarios. Include the physical checks needed after conversion/sign/calibration changes. For a prototype replacement, identify which prior results remain applicable and which must be measured again.
