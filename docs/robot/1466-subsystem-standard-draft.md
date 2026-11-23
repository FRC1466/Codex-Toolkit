# Draft subsystem standard for 1466

This is a discussion draft for 1466's next robot project. The 2026 code supplies examples. The [prototype skill's 1466 reference](../../.agents/skills/frc-prototype/references/1466-subsystem-preferences.md) carries the preferences confirmed so far. The remaining decisions here are proposals until the team adopts them. Keep season-specific conventions in the robot repository and link them from `docs/robot/context.md` or `AGENTS.md` so the prototype skill can find them.

## What we want students to build

Students who know Java from AP Computer Science A can own a first version of a real mechanism. Give them one behavior they can show working, such as forward, reverse, and stop for intake rollers. Codex first explains the design and test approach at the depth the student wants, then implements the whole requested subsystem. End with a walkthrough of how a request becomes a motor output, what clears the request, and what was checked. Codex can prepare and open the PR when authorized. After a successful compile, 1466's designated maintainer manually merges it. Formal review approvals are optional.

Prioritize getting hardware testable. A disposable prototype can skip AdvantageKit and use a simple simulation. Give mechanisms with unknown constants basic manual controls for bring-up. Prefer motor-controller closed loops and use Motion Magic for profiled position where supported. Use timeouts for bounded waits and surface failures to the operator. Keep the handoff to what changed and what needs testing. For the complete defaults, follow the skill reference above.

## Patterns to consider

Use the 2026 mechanism and IO split as the starting point and adapt it to the 2027 robot. Coordination is an open design choice. Commands v3 also has a state machine API, so the team can consider commands and explicit states together. A useful comparison would implement the same intake-to-indexer handoff under each proposed architecture and show who owns each output when the driver cancels or the sensor fails. See [WPILib's Commands v3 state machine documentation](https://docs.wpilib.org/en/latest/docs/software/commandbased/commands-v3/state-machines.html).

| Area | What 1466 did in 2026 | Proposed starting point |
| --- | --- | --- |
| File layout | `Indexer.java`, `IndexerIO.java`, `IndexerIOTalonFX.java`, and `IndexerIOSim.java` live together. The intake combines pivot and roller behavior while giving each its own IO. | Use the indexer as the first single-mechanism example. Consider separate pivot and roller subsystems when they have independent goals, lifecycles, or command requirements. Let a higher layer request coordinated behavior. |
| Control flow | `Indexer.periodic()` reads and logs sensor inputs and computes outputs. `Robot.java` runs the scheduler before calling `FullSubsystem.runAllPeriodicAfterScheduler()`, which ultimately applies indexer outputs. | Give each mechanism a clear output owner. Follow the current robot's update order and verify when new requests actually reach the output. Decide whether 2027 should standardize on `FullSubsystem` or another approach. |
| Commands and goals | `Indexer` exposes mechanism methods and named commands. Its run commands use `runEnd` with stop on end. `Choreographer` separately tracks requested goals and current state for coordinated behavior. | Keep the first mechanism API small enough for drivers, autonomous, and other subsystems to reuse. Define what clears requests on release, interruption, or disable. Decide which decisions belong to commands, local states, or a robot-wide coordinator. |
| Units and settings | Real indexer IO converts vendor sensor values into named units like `velocityRps` and `supplyCurrentAmps`. The subsystem uses `LoggedTunableNumber` for settings such as run voltage and stall timing. | Prefer typed WPILib units in new agent-written interfaces and support unit-named primitives in student and existing code. Convert gearing in IO. Keep mechanism settings in their subsystem folder and use live tunables for values adjusted at the robot. |
| Logs and varying hardware | The indexer logs running, stalled, reversing, and output voltage, along with measured IO. `RobotContainer` picks hardware for competition, development, and simulation modes and uses no-op IO when hardware is absent or in replay. | Build both real and simulation IO when the hardware is known, even before it arrives. Use simulation IO alone when the hardware choice is unknown. Use AdvantageKit and make all behavior-driving inputs replayable. Log enough to distinguish requests, decisions, and measurements. |

2026 reference points are `src/main/java/frc/robot/subsystems/indexer/`, `subsystems/intake/Intake.java`, `subsystems/Choreographer.java`, `util/FullSubsystem.java`, `Robot.java`, and `RobotContainer.java` in `2026RobotCode`. The repo's `.github/prompts/Robotics.prompt.md` describes the intended conventions. Consult current code for what actually runs. Carry forward the ideas the team chooses and confirm all physical settings for the new hardware.

One reason to check the implementation before reusing it is `Indexer.runVolts()`. It writes the requested voltage and marks the indexer as running. The next `periodic()` call can recompute that voltage as part of normal running and stall detection. If 2027 adds a manual voltage mode, define which request owns the output and check that it persists across multiple loops and clears when that mode ends.

`FullSubsystem` extends `SubsystemBase` and adds `periodicAfterScheduler()`. In 2026, `Robot.robotPeriodic()` ran the command scheduler and then called that extra method for each registered `FullSubsystem`. The hood uses it to resolve the goal or an open loop override and apply the output after commands run. A goal change can reach the motor in the same loop when output selection also happens there. An output calculated before the command runs can still use the previous goal, even when sent after the scheduler. The pattern controls ordering and can reduce response delay in some paths. Its implementation adds a pass over the registered subsystems, and the code alone does not establish a CPU speedup or fewer CAN messages.

## Recommendations to try on the intake

- Give the rollers and pivot separate subsystems with their own IO when they can be requested independently. Model joint actions like intake and stow at the coordination layer. Put interlocks where they still apply when an independent command takes control.
- Start with a small API expressed in mechanism terms. Rollers can expose named actions such as intake, reverse, and stop, with explicit interruption behavior. The pivot can accept a persistent position goal such as `setAngle(Angle angle)` and expose measured state and readiness. Use an enum internally when a mechanism has several persistent modes or competing flags. A robot-wide request such as acquire or score can be a goal on the coordinator if the project adopts one.
- Try deliberate held reverse taking priority over normal intake and automatic unjamming. For an initial trial, cancel the automatic unjam when the driver takes over and leave the rollers stopped on release until another valid request arrives. Apply the same limits and interlocks in reverse. Confirm this with drivers before treating it as the standard.
- Momentary controls require a fresh press after re-enable. A pivot retains its intended goal and returns to it through normal limits when enabled, subject to position validity and interlocks.

## Tunables and replay

Use `LoggedTunableNumber` now. The 2026 wrapper reads a `LoggedNetworkNumber` when tuning mode is enabled and uses the configured default otherwise. The 2027 alpha Tunables API provides typed values such as `TunableDouble` from `Tunables.addDouble(...)`, with a default NetworkTables backend. Dashboard publishing and recording an input for deterministic replay are separate steps. Check the installed WPILib and AdvantageKit versions, route the effective value through a replay-aware input, and verify a recording where a value changes during a maneuver. Replay should reproduce both the tune change and the resulting request or state transition. See [WPILib's migration guide](https://github.com/wpilibsuite/allwpilib/blob/v2027.0.0-alpha-8/tunables/doc/tunables.md#migration-from-wpilib-2026) and [AdvantageKit's dashboard input guide](https://docs.advantagekit.org/data-flow/recording-inputs/dashboard-inputs/).

Keep live edits behind tuning mode. BLine is the current autonomous candidate. Describe each routine as a short text sequence with its start, actions, and stop conditions.

## Example first assignment

Build intake rollers with forward, reverse, and stop. The student should be able to show which component decides the output and which one sends it. Check the normal controls and what happens after release, interruption, disable, and re-enable as applicable. If the motor or sensor is still unavailable, point out which behavior can be checked with fake inputs and what needs a bench run. Add beam-break behavior in a separate iteration once the basic controls work.

## Decisions to discuss

Use these questions to settle the specific conventions that Codex should apply consistently.

1. Which real subsystem should be the first assignment? Would you hand every student the same practice task or assign different mechanisms they can own?
2. Do we keep `FullSubsystem` and `periodicAfterScheduler()` once we pick the 2027 scheduler?
3. Within a subsystem folder, should settings live in a dedicated configuration class or beside the real IO code?
4. When can we verify integrated replay against a representative recording?
5. Does the proposed manual reverse priority feel right to drivers, including the stop on release?
6. What should count as ready for each integrated mechanism, and what should a disconnected sensor report?
