# Install from a fresh Codex session

Open the **destination code project** in Codex. Copy the prompt below into its chat and replace `TOOLKIT_REPOSITORY_URL` with this toolkit's GitHub repository URL after it has been published. No toolkit skill, plugin, shared chat history, or personal Codex configuration is needed beforehand.

```text
Install the FRC Codex toolkit from TOOLKIT_REPOSITORY_URL into the project currently open in this chat.

Read INSTALL.md and toolkit-manifest.json from that repository, then carry out the project installation described there. Use a single source revision: unless I specify a ref, resolve the repository's default branch to a commit and record that commit. Do not assume a release or tag exists.

Use your own available file, network, and execution tools. Do not ask me to open a terminal, run commands, install a runtime, or grant administrator access. The instructions and skills can be installed without Python; check optional helper availability separately and report it honestly.

Preserve this project's code, existing instructions, unrelated skills, configuration, hardware records, and experiments. Follow the manifest's copy/merge/create rules, merge the project instructions into AGENTS.md, and record provenance in frc-toolkit.lock.json. Do not clone another Git repository inside this project or change global Codex settings. If this project already has a toolkit installation, follow the update procedure instead.

Complete the authorized local installation and validate what you can. Ask only about consequential blockers or genuine conflicts that cannot be resolved from the project. Do not commit, push, publish, deploy, or operate hardware as part of setup. Finish with the installed revision, changed files, any conflicts or unavailable checks, and how to begin normal work.
```

To choose a particular version, append `Use ref <tag-or-commit>.` with an actual existing ref. The toolkit's version string is not proof that a matching Git tag or release has been published.

If repository access is unavailable, download and extract the toolkit ZIP using the browser/file manager, then tell Codex to use that local folder as the source and follow its `INSTALL.md`. If Codex cannot establish the source commit, it must record it as unknown. A private repository requires access through the account's available authentication; no credentials belong in the prompt or installation record.

After installation, keep the installed files and lock record in the code repository through your normal review process. Other students receive them when they get that repository. Start a fresh Codex chat in the project if the current session does not discover the new skills; ordinary development prompts are sufficient.

See [the installation procedure](INSTALL.md), [the update prompt](UPDATE_PROMPT.md), and [the toolkit overview](README.md).
