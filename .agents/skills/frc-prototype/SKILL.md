---
name: frc-prototype
description: "Bring up FRC bench mechanisms, motors, sensors, partial robots, and early V1 code while CAD or hardware is incomplete. Create useful controls, logging, and tests for the hardware available today."
---

# Bring up available hardware

Read current project conventions and the hardware revision before choosing an implementation. The goal is a useful experiment today with a clear path to V1; do not require final architecture or build a new framework for one motor.

- Identify what is physically present, what is absent, which controller/sensor APIs are installed, units/gearing, and the experiment's objective. Use confirmed values, label estimates, and ask for consequential electrical/mechanical details that cannot be inferred. Never guess a CAN ID or physical travel limit.
- Match control complexity to evidence: bounded manual output for initial exploration, simple sequences once behavior is understood, closed loop after sensor scaling/direction and operating range are established. Unknown geometry need not block fake-input logic tests or controls for an unrelated roller.
- Use the project's current hardware abstraction. Keep hardware access separate from testable behavior where practical; existing IO abstractions, commands, and state machines are choices, not mandatory templates. Missing hardware must not silently report successful completion because a no-op input defaults to zero.
- Make partial configurations explicit. Log the selected prototype/revision and settings; distinguish absent, simulated, disconnected, and real hardware. Keep provisional geometry and gains visible and replaceable.
- Give manual testing and automatic coordination a clear ownership boundary. Define what happens on button release, command interruption, disable, sensor loss, and return from manual control. A previous target/output must not accidentally remain active after ownership changes.
- Add relevant observations immediately: requested versus measured output, mode/state, current, position/velocity, faults, and transition blockers as applicable. Include basic visualization when it helps and mark approximate geometry.
- Prepare a short bring-up sequence: select the revision, verify connectivity and sensor scale/direction at bounded motion, exercise stopping/cancellation, then run the experiment. Physical energization/deployment requires actual user authorization and an operator; writing the code/test procedure does not authorize moving hardware.

Run appropriate software checks using `frc-verify`. Hand off runnable code, controls and settings, assumptions, and the next physical test. Use `frc-experiment` when comparing alternatives. Do not claim physical performance from compilation or an uncalibrated simulation.
