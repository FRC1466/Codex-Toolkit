---
name: frc-diagnose
description: "Investigate FRC failures and unexpected robot behavior using WPILOG logs, code, settings, and hardware revisions. Use for stuck states, missed actions, intermittent faults, and differences between runs."
---

# Explain a failure with evidence

Identify the observed symptom, expected behavior, approximate time interval, code revision/dirty state, hardware revision, and active configuration. Do not assume current source matches a historical log; inspect logged build metadata and the corresponding source when available.

Use `tools/frc/frc.py log` to inspect WPILOG signals and extract a narrow interval. Read `docs/tooling.md` for supported types, absolute log timestamps, state carried into a window, bounded samples, and error behavior. Start with `--list --match '*RelevantMechanism*'`; use repeated `--signal` selectors with `--start` and `--end` for the event. Helpers do not decode arbitrary structs/protobufs or CTRE .hoot files.

This helper needs an existing Python 3.10+ interpreter. If unavailable, use an available log decoder/viewer or provided export. Continue useful source investigation, but report unavailable binary-log evidence; do not claim to have decoded it. Do not ask the user to open a terminal or install a runtime just to load the skill.

If strict parsing reports an interrupted final record, retry with `--allow-truncated` when prefix analysis is useful. Report `complete: false` and the warning; do not infer anything about the missing tail or treat unobserved selectors as proven absent. This option does not recover arbitrary internal corruption.

Trace intent -> arbitration/ownership -> requested target -> applied output -> measured response -> readiness/transition -> completion. Include inputs from driver controls, vision, power, connectivity, and interlocks where relevant. A boolean named 'ready' is not self-explanatory: inspect what computed it, whether it refers to requested or measured state, and which cycle it represents.

Reconstruct a chronological event timeline. A signal may not have a sample inside the interval because it last changed earlier; inspect `initial_values` and timestamps rather than interpreting absence as false. Respect missing selectors, truncation, duplicate entry lifetimes, and nonfinite samples. Do not align separate runs by raw boot timestamps; choose and document a common event before comparing.

Separate observations with signal/time/code references, competing explanations, and evidence needed to distinguish them. Current spikes alone do not prove a jam or shot. When the log is insufficient, identify the smallest additional measurement or test; avoid adding speculative fixes.

Reproduce a supported software failure with fake inputs, simulation, or replay where practical, then implement the authorized correction and a meaningful regression scenario using `frc-verify`. Recorded-input replay can check logic but does not prove the physical response to changed outputs. Present remaining mechanical/electrical hypotheses and a concrete next test when software evidence cannot decide.
