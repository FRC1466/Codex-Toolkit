# FRC Codex toolkit

Describe the task normally in Codex. For example:

- “We have a motor and an encoder on a bench. Get the prototype running.”
- “We changed the gear ratio; update everything affected.”
- “Why did the robot wait here? Here is the log.”
- “Two students are changing the intake and auto. Help us combine their work.”

`AGENTS.md` routes these requests into nine repository skills under `.agents/skills/`. Each skill also has implicit invocation enabled. Students do not need to memorize commands, select skills, or install them into personal Codex settings. Open Codex in this folder or a descendant. If a running session does not discover new skills, start a fresh session.

The toolkit contains workflows and working utilities, not a robot implementation. No 2027 hardware or architecture has been selected.

## Add it to a code project

1. Open the **destination code project** in Codex.
2. Copy [the installation prompt](INSTALL_PROMPT.md), replace `TOOLKIT_REPOSITORY_URL` with this repository's GitHub URL, and send it to Codex. The prompt works with a fresh account/session; no toolkit skill needs to be installed first.
3. Codex reads [INSTALL.md](INSTALL.md) and [the file manifest](toolkit-manifest.json), installs the files, merges project instructions, and records the exact source revision in the destination's `frc-toolkit.lock.json`.
4. Review and commit those local changes through the team's normal workflow. Other students receive the toolkit with the code repository and need no separate account setup.

No standalone installer, executable download, plugin installation, administrator access, or user-opened terminal is required. Codex uses its existing file/network tools. File installation and skill use do not need Python; optional helpers need an existing Python 3.10+ interpreter. If repository access is unavailable, download/extract a ZIP in the browser/file manager and give Codex that local source folder. See the prompt for details.

Once you publish this source repository, its GitHub URL is the only substitution needed in the install prompt. No owner/repository name is hardcoded in the toolkit. Version `0.1.0` is a package label; installation resolves a real commit and never assumes a matching tag or release exists.

## Maintain installations

Use [the update prompt](UPDATE_PROMPT.md) in an installed project. Codex compares the recorded version and file hashes, preserves project customizations, and follows the update procedure in `INSTALL.md`. A project stays on its chosen version until someone requests an update.

The source repository owns reusable skills, tools, and installation guidance. Installed projects own hardware records, decisions, experiments, verification commands, and their existing instructions/configuration. The installation uses [project templates](templates/AGENTS.fragment.md), rather than copying this source checkout's maintenance context, checks, or CI into robot code. An incomplete installation is recorded as partial; missing helper execution is reported separately.

Keep installed `.agents/skills/`, `tools/frc/`, project references, configuration, and the lock versioned alongside the robot code. For actual robot work, configure commands from its real build system. The `toolkit` check in this **source repository** only tests the toolkit.

Use a named task branch and separate checkout for each concurrent task. Students on different computers share published work through GitHub issues and PRs. There is no background coordination service and no local file acts as a team-wide lock. Skills on an older branch remain at that branch's version until updated.

## Working tools

The following are agent/maintainer command examples, not installation steps for students. Codex can run them using its own execution tools when a suitable interpreter is available. Python 3.10+ and no third-party Python packages are needed for these helpers. Use an existing `python3` on macOS/Linux or `py -3`/`python` on Windows after checking its version. Git-backed inspection also needs Git. Run from the project root, or supply the absolute script path and `--root`. Without Python, the skills remain useful through available file/Git/build tools; log parsing requires an available decoder.

```sh
python3 tools/frc/frc.py workspace
python3 tools/frc/frc.py workspace --base origin/main
python3 tools/frc/frc.py overlap --base origin/main --other origin/intake-work
python3 tools/frc/frc.py verify --check toolkit
python3 tools/frc/frc.py experiment intake-a --question "Does wheel spacing affect acquisition?" --hardware docs/robot/examples/hardware.json --setting spacing_mm=45
python3 tools/frc/frc.py log /path/to/run.wpilog --list --match '*Choreographer*'
python3 tools/frc/frc.py log /path/to/run.wpilog --signal '*State' --signal '*Ready*' --start 30 --end 35 --changes
python3 tools/frc/frc.py log /path/to/run.wpilog --signal '*Loop*MS' --stats
```

`origin/main` and the hardware example above are examples, not configured project facts. The hardware example explicitly describes unknown hardware. Supply a real measured profile when one exists.

See [the tool reference](docs/tooling.md) for timestamps, bounded output, schema support, errors, and verification provenance. Experiment records are written individually under `docs/robot/experiments/`; transient reports go under ignored `.frc/`. Review experiments before committing them, especially when they reference local-only artifacts.

## Verification and evaluation

```sh
python3 -m unittest discover -s tools/frc/tests -v
```

The source-only suite exercises real temporary Git repositories and branches, command failures/timeouts, provenance, concurrent experiment creation, synthetic binary WPILOG files, and the installation payload in an isolated destination. [Behavioral evaluation scenarios](docs/skill-evaluation.md) cover natural-language skill routing, engineering decisions, installation, and updates. Passing deterministic tests does not prove that every future model invocation will choose the right workflow or merge instructions correctly.

Automatic discovery follows [Codex's skills documentation](https://learn.chatgpt.com/docs/build-skills) and [AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
