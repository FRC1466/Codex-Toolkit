# Current robot project

Document the architecture and hardware actually present in this project. The toolkit does not select them. Current project details are unknown until code and hardware records have been inspected; preserve existing facts and label estimates explicitly.

## Working references

- Keep hardware/prototype revisions and measurement sources under `docs/robot/hardware/` when they exist. The [hardware example](examples/hardware.json) is a documentation example, not an installed mechanism.
- Record shared interface units, ownership, readiness, cancellation, and fault semantics under `docs/robot/interfaces/` when parallel tasks need an agreement.
- Record consequential accepted design decisions and their reasons under `docs/robot/decisions/`. A proposal is not an accepted team decision.
- Keep measured trial results, settings, hardware/code provenance, and artifacts under `docs/robot/experiments/`. An experiment plan contains no observed results yet.

Create records as they become useful; a small code change does not require all of these documents. Existing source and measured evidence take precedence over old plans. Update references when the design changes.

## Team work

Use the team's existing task/review workflow. When available, published issues and branches can describe ownership, dependencies and merge order. They do not expose private chats or another computer's uncommitted work. Coordinate use of physical hardware with the operator and record the revision actually tested.

`frc-toolkit.json` contains this project's verification and coordination settings. Empty checks and unknown hardware remain unconfigured/unknown, not verified. The installation source and version are recorded in `frc-toolkit.lock.json`.
