---
name: frc-prototype
description: "Build a first version of an FRC subsystem or bring up bench mechanisms, motors, sensors, and partial robots. Create useful controls, logging, and tests while CAD or hardware may still be incomplete."
---

# Bring up available hardware

Read current project conventions and the hardware revision before choosing an implementation. The goal is a useful experiment today with a clear path to V1; do not require final architecture or build a new framework for one motor.

For a student learning by building, give them ownership of a real subsystem and pick one observable first behavior. Explain the proposed change before editing and match the depth to their experience. Focus on robot loop timing, hardware boundaries, and how inputs become outputs. Carry out the requested implementation unless the student asks to take part of the edit. Walk through the result and how it was checked.

Follow subsystem standards adopted in the current project's `docs/robot/context.md` or repository instructions. When the user or destination robot project identifies Team 1466 (Webb Robotics), also read [1466's subsystem preferences](references/1466-subsystem-preferences.md). Use that reference for team defaults under the current robot project's decisions.

- Identify what is physically present, what is absent, which controller/sensor APIs are installed, units/gearing, and the experiment's objective. Use confirmed values, label estimates, and ask for consequential electrical/mechanical details that cannot be inferred. Never guess a CAN ID or physical travel limit.
- Match control complexity to evidence: bounded manual output for initial exploration, simple sequences once behavior is understood, closed loop after sensor scaling/direction and operating range are established. Unknown geometry need not block fake-input logic tests or controls for an unrelated roller.
- Use the project's current hardware abstraction. Keep hardware access separate from testable behavior where practical; existing IO abstractions, commands, and state machines are choices, not mandatory templates. Missing hardware must not silently report successful completion because a no-op input defaults to zero.
- Make partial configurations explicit. Log the selected prototype/revision and settings; distinguish absent, simulated, disconnected, and real hardware. Keep provisional geometry and gains visible and replaceable.
- Give manual testing and automatic coordination a clear ownership boundary. Define what happens on button release, command interruption, disable, sensor loss, and return from manual control. A previous target/output must not accidentally remain active after ownership changes.
- Add relevant observations immediately: requested versus measured output, mode/state, current, position/velocity, faults, and transition blockers as applicable. Include basic visualization when it helps and mark approximate geometry.
- Prepare a short bring-up sequence: select the revision, verify connectivity and sensor scale/direction at bounded motion, exercise stopping/cancellation, then run the experiment. Physical energization/deployment requires actual user authorization and an operator; writing the code/test procedure does not authorize moving hardware.

Run appropriate software checks using `frc-verify`. Hand off runnable code, controls and settings, assumptions, and the next physical test. Use `frc-experiment` when comparing alternatives. Do not claim physical performance from compilation or an uncalibrated simulation.
