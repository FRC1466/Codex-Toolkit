---
name: frc-experiment
description: "Plan and compare FRC prototype experiments, record hardware and code revisions, and interpret measured results. Use for design trials and repeatability studies, including early-season incomplete mechanisms."
---

# Make experiments useful

Frame the question and an observable success criterion. Identify the independent variable, measured outcomes, controlled conditions, and likely confounders. Match the number of trials to variability and available time; do not invent universal sample sizes or performance thresholds.

Record hardware revision, code commit and dirty fingerprint, actual applied settings, operator, and artifacts. An absent profile is unknown, not a measured revision. Distinguish proposed settings from settings logged during a run. Link geometry/CAD when useful, but proceed with measurable available hardware.

Use `python3 tools/frc/frc.py experiment <slug> --question "..."` from the root; add `--hardware <profile.json>`, repeated `--setting key=value`, `--operator`, and repeated `--artifact <file>` when known. It creates one uniquely named JSON record under `docs/robot/experiments/`, avoiding a shared append-only file. See `docs/tooling.md` for the record format. The command creates an unexecuted plan; it does not run a robot or invent results.

If Python is unavailable, use Codex's file tools to write a separate record with the same relevant fields, a unique non-overwriting path, and honest unknown provenance where measurements/hashing are unavailable. No runtime installation or user-opened terminal is needed to plan an experiment. Do not fabricate a hash, revision, actual setting, or trial result.

After real trials, fill in measurements with units, failed attempts and exclusions, observations, and conclusions. Keep artifacts and their hashes associated with the run. Use a shared artifact location when one exists; do not upload logs or share documents without authorization. Do not put large logs into ordinary Git commits by default.

Compare like conditions and report repeatability and uncertainty, not just the best attempt. Check whether changes in battery, game pieces, operator, firmware, code, or hardware make a comparison inconclusive. Say what evidence supports a design choice and which next experiment would most reduce uncertainty. A failed experiment is useful evidence and should not be erased.

Promote validated settings into the intended revision only after assessing their applicability. Update relevant hardware/decision records instead of turning an experimental result into a rule for all future mechanisms. Use `frc-change` for consequential adoption and `frc-performance` for control tuning.
