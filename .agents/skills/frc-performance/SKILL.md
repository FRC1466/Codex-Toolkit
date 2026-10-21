---
name: frc-performance
description: "Measure and improve FRC loop timing, CAN traffic, mechanism control, and cycle performance. Use for overruns, slow actions, PID/feedforward tuning, or comparing measured performance across revisions."
---

# Improve measured performance

Identify whether the objective is CPU/loop timing, device/network latency, mechanism response, or task cycle time. Establish the current hardware/code/settings, an observable metric, and the reliability/accuracy constraints it must preserve. Do not optimize from names or guessed bottlenecks.

For software timing, inspect profiler/tracer semantics and a real-robot baseline. Markers may measure time since the preceding marker rather than exclusive execution time. Examine typical and tail latency, overruns, calls that block, allocations, repeated configuration, logging, and signal frequencies. Do not sum overlapping timers or treat accelerated replay wall-clock timing as RoboRIO performance.

For control tuning, confirm mechanism units, gearing, sensor scale/direction, calibration, limits, and the controller's implementation before suggesting gains. Separate simulation and real-robot parameters. Inspect tracking error, settling/overshoot, saturation, current, battery conditions, and repeated trials. Controller gains depend on units; no universal starting gains or automatic transfer across changed hardware.

Use `frc-experiment` for bounded tuning/comparison trials and preserve a known baseline. Prepare an experiment for the operator rather than autonomously moving hardware. Change one explanatory factor at a time when practical. Respect the user's desired tradeoff and report inconclusive results.

Use `tools/frc/frc.py log <file> --signal '<pattern>' --stats` for scalar summaries. Timestamps are absolute log seconds; statistics count samples, not elapsed-time weighting. Read `docs/tooling.md` for percentile caps and nonfinite/missing-data behavior. Compare comparable intervals aligned to a documented event, not raw boot time. The helper does not automatically infer mechanism success, CPU causality, or tune PID.

The helper needs an existing Python 3.10+ interpreter. If unavailable, use another available decoder/analysis tool or provided numeric export, retaining the same evidence standards. Do not claim measurements without an available analysis path or require users to open a terminal/install a runtime for skill use.

Implement a supported improvement, use `frc-verify`, then compare against the same baseline conditions. Report measured benefit and accuracy/reliability tradeoffs. If no trustworthy baseline exists, instrument or propose the smallest useful test instead of claiming a speedup.
