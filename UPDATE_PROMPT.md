# Update an installed project

Open the destination code project in Codex and copy this prompt. It assumes an installation record already exists; if it does not, use [the installation prompt](INSTALL_PROMPT.md) and provide the source repository URL.

```text
Update the FRC Codex toolkit installed in this project.

Read frc-toolkit.lock.json to identify its source repository and installed revision. Retrieve INSTALL.md and toolkit-manifest.json from the desired source revision and follow their update procedure. Unless I specify a ref, resolve the source repository's default branch to one commit and use that same commit throughout. If the lock lacks a source repository, ask me for its URL rather than guessing it.

Use your own available tools; do not ask me to open a terminal or install a runtime, and do not request administrator access or change global Codex settings. Preserve project-specific instructions, checks, hardware facts, experiments, configuration, and unrelated files. Compare installed file hashes with the lock record and merge local changes deliberately; do not overwrite a customized file merely because it belongs to the toolkit. Complete independent updates and identify any unresolved conflicts without marking them fully installed.

Validate the resulting installation, update the provenance record accurately, and summarize the revision, changes, verification, conflicts, and unavailable helper checks. Do not commit, push, publish, deploy, or operate hardware as part of this update.
```

Append `Use ref <tag-or-commit>.` to request an actual existing ref. This is a normal Codex task; there is no update daemon, automatic background download, or executable installer.
