---
name: frc-integrate
description: "Review and combine FRC student or agent branches, resolve merge conflicts, and prepare integration-ready PR handoffs. Check behavioral compatibility beyond textual conflicts and coordinate dependent work."
---

# Integrate concurrent robot work

Identify the source branches, intended target, owners, shared interfaces, and dependency order. Inspect published task/PR context through available authorized access. Do not assume that local remote-tracking refs are current or that private chats/uncommitted work are visible.

For Team 1466, follow the [manual merge and handoff preference](../frc-prototype/references/1466-subsystem-preferences.md#faults-diagnosis-and-review). Prepare or open the PR when authorized and leave the final merge to the designated maintainer.

Use `tools/frc/frc.py workspace --base <target>` and `overlap --base <target> --other <branch>` for read-only inspection. The overlap helper compares committed changes since each branch's merge base and includes this checkout's dirty paths; it reports file overlap, not semantic compatibility or a mergeability guarantee. Fetch only when appropriate/authorized, and report inspected commits.

If no existing Python 3.10+ interpreter is available for the helpers, perform equivalent read-only Git inspection with available tools and report any gaps. Do not require runtime installation or a user-opened terminal for integration work.

For a review request, review without changing or merging code unless authorized. For local integration work, use an isolated integration checkout to combine dependencies and run checks before modifying a shared branch. Preserve unrelated work and never force-push shared history or choose conflict sides blindly. A locally tested merge candidate is not authorization to merge a PR.

Inspect combined behavior even with no text conflicts:

- Units/frame, coordinate transforms, source of truth, and renamed APIs.
- Output ownership, command requirements/state arbitration, loop ordering, cancellation and disable behavior.
- Meaning of readiness/completion, timeout/fault propagation, and autonomous event timing.
- Hardware profiles, CAN/sensor identities, dependencies/library versions, settings and deployment targets.
- Log paths, experiment provenance, and tests that must change together.

Resolve mechanical conflicts from intent and current contracts. Escalate genuine incompatible design choices with concrete alternatives and consequences while continuing independent integration checks. Update affected contracts and identify dependent branches that need changes; messaging others still requires authorization.

Use `frc-verify` on the actual combined revision. Summarize the problem and resulting behavior for a reviewer who has not read the chat, with dependencies, verification and outstanding physical tests. Use the existing PR template. Humans review merge/deployment decisions according to project policy and user authorization.

Shared coordination is GitHub, not a branch-local lock file. Check branch protection/required CI through actual settings when asked to configure enforcement; instructions and templates alone do not enforce it.
