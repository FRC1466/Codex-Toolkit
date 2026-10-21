# Project installation by Codex

This is the bootstrap entry point for an ordinary Codex session. Perform setup using the tools already available in that session. The user does not need to know the skills, open a terminal, install Python, or provide administrator access. These are agent instructions for local project changes, not an executable installer. Optional Python utilities still need an available Python 3.10+ interpreter to run.

Start from [the install prompt](INSTALL_PROMPT.md), or [the update prompt](UPDATE_PROMPT.md) for an existing installation. The authoritative file inventory and operation types are in [toolkit-manifest.json](toolkit-manifest.json).

## 1. Establish source and destination

The destination is the code project selected by the user, not the downloaded toolkit checkout. Read that destination's applicable instructions and inspect its existing files before editing. Do not treat the source repository's maintenance `AGENTS.md` as instructions for the destination; the reusable instructions come from the manifest's project fragment.

Identify the intended project root and record its current working changes when Git is available. Preserve those changes. Do not silently install into a nested subsystem folder or into the toolkit's own maintenance checkout. If the intended destination cannot be determined, ask for the project folder while continuing source discovery.

Use the source repository URL supplied by the user, or the existing installation lock for updates. Authenticate through available connected tools or existing credentials if necessary; never put tokens or credential-bearing URLs in records. If the session cannot access a private source, explain the access requirement and offer a local extracted source folder. Do not ask the user to type a shell command.

Resolve the requested ref to one full commit, or resolve the source repository's default branch when no ref was specified. Do not assume `main`, a `latest` release, or a version tag. Fetch the manifest, instructions, templates, and payload from that same commit. Use repository/file APIs, an archive, or a temporary checkout outside the destination. Include hidden `.agents` files; a visible-files-only download is incomplete. Read-only browsing of source is allowed; do not publish anything.

If source is a local folder/ZIP and the commit cannot be verified, record `source_commit: null` and its source kind. Do not fabricate a commit from a directory name or version string. The manifest's `version` labels the payload; the resolved commit identifies its exact revision. If source and destination resolve to the same directory, clarify the intended destination before applying installation changes.

## 2. Plan the edits from the manifest

Use `toolkit-manifest.json` schema version 1. Inspect each listed source file. All source/destination paths must be relative to their respective roots; reject absolute paths, `..` traversal, duplicate destinations, and symlinks that resolve outside a root. Do not overwrite `.git`, a submodule, or unrelated files. If the manifest schema is unsupported, explain it and leave the destination unchanged rather than guessing the mapping.

The manifest separates operations:

- `copy_files`: reusable skills, helper modules, and reference files installed at the same relative paths. A missing destination can be created. Identical content can be adopted. A different pre-existing file requires comparison and deliberate merging; do not overwrite it wholesale. If it is unrelated or its intended ownership is unclear, preserve it, report the collision, and complete independent work.
- `merge_files`: a project instructions fragment, project configuration defaults, and minimal ignore entries. Follow the rules below. Never replace an entire project's instructions or configuration with toolkit defaults.
- `create_if_missing`: the starter robot-context page. If that page already exists, preserve its facts and add only useful missing references without changing their meaning. On updates it remains project-owned.
- `optional_templates`: GitHub issue/PR templates. Add useful missing templates if appropriate to the project's existing workflow; merge or preserve existing templates. Their absence does not block skill installation. Do not enable branch protections or contact GitHub on the team's behalf as a side effect.
- `source_only`: maintenance files that must not be copied wholesale into a robot project. In particular, the toolkit source's test suite/CI, root configuration, README, and maintenance instructions are not robot-project defaults.

Briefly describe the edits and proceed within the user's installation request. An extra approval round is not required for routine local setup. Do not change robot source, wire up a new architecture, upgrade robot dependencies, create a nested Git repository, alter global PATH/Codex settings, install runtimes, commit, push, deploy, or energize hardware.

## 3. Merge project instructions

Use [templates/AGENTS.fragment.md](templates/AGENTS.fragment.md), surrounded by these markers in the destination root `AGENTS.md`:

```text
<!-- frc-codex-toolkit:begin -->
...project fragment...
<!-- frc-codex-toolkit:end -->
```

Create the file if absent, or append the marked block to existing instructions. Keep text outside the block unchanged. Keep only one block. If an existing block has local changes, merge its intent with the new fragment instead of replacing it blindly. Resolve conflicts in favor of explicit current project/user choices, and explain unresolved contradictions. Do not weaken meaningful existing rules.

Check for `AGENTS.override.md` and other project instruction discovery settings before assuming the new root `AGENTS.md` will be read. If a root override would shadow it, add a small marked pointer there to read the root toolkit block, preserving the override's own rules; record that extra managed block in the lock. Inspect relevant nested instructions for actual conflicts, but do not rewrite every subdirectory. Report settings that prevent discovery instead of declaring it verified.

The fragment routes ordinary development requests to local skill files and makes optional helper fallback explicit. All copied skill metadata must retain `policy.allow_implicit_invocation: true`. Do not install duplicate personal/global skills as a second copy.

## 4. Adapt project configuration and context

Use [templates/frc-toolkit.project.json](templates/frc-toolkit.project.json) for missing defaults in `frc-toolkit.json`, not the maintenance checkout's active configuration. Preserve existing keys and checks. If an existing file is malformed or uses an unsupported schema, preserve it and describe the conflict; do not silently replace it. Determine the project kind from actual code, leaving it unknown if not established. Determine target branch and GitHub repository only from reliable local/project information. Do not invent hardware or a framework.

Configure relevant existing verification commands only after reading the project's actual build scripts and hooks. Use argument arrays, explicit scope, and the correct Windows alternative where needed; do not run builds that would deploy or commit as a setup side effect. The defaults intentionally have no checks. Empty checks mean unconfigured, never success. Do not copy a `toolkit` check that points at a source-only test directory absent from the destination.

For `docs/robot/context.md`, use [the project context starter](templates/robot-context.md) only when the destination page is missing. Summarize inspected current architecture if useful; otherwise retain explicit unknowns. Preserve existing hardware/decision/experiment records. The example hardware JSON is an example, not an installed device or runtime configuration.

Append only missing ignore entries from [templates/gitignore.fragment](templates/gitignore.fragment). Preserve the project's existing rules; do not introduce a blanket log-file policy. Inspect actual Git ignore behavior if negation or nested patterns would keep reports from being ignored.

## 5. Record the installation

Create/update the project-root `frc-toolkit.lock.json` as a provenance record using [the lock format example](templates/frc-toolkit.lock.example.json). Fill real values; do not copy example nulls as verified facts. Record:

- Toolkit name/version; source repository, selected ref, full verified commit or explicit unknown, source kind, and UTC installation time.
- Installed payload paths, ownership (`toolkit` or `project`), operation and per-file hashes of both upstream and installed content. Mark intentionally merged/customized files as project-owned.
- Managed blocks separately from their containing files, with both upstream and installed block hashes. Track paths/markers for any override pointer as well.
- Configuration/context/ignore/template edits as project-owned integrations, so updates never replace them as plain toolkit payload.
- Availability of optional helper execution, actual validation results, and any unresolved files. Use `status: partial` when required payload/routing/configuration conflicts remain; use `status: installed` for complete file/routing setup even when optional Python checks are unavailable, recording that limitation separately.

For hashes use `utf8-lf-sha256`: decode UTF-8 text, normalize CRLF pairs to LF, re-encode UTF-8, and SHA-256 those bytes. Do not trim spaces, remove other content, or normalize away meaningful edits. This avoids artificial conflicts when Git uses Windows line endings. Hash actual installed content after merging. Use an existing hashing tool through Codex's execution tools if available; no Python or privileged installation is required. If no hashing capability exists, store null with a reason and require a full content comparison for future updates—never invent a hash or treat missing hashes as equality. The lock example contains no real installation evidence.

The lock is versioned with project code, not stored in a personal account. Do not include passwords, tokens, local machine usernames, or temporary source paths. A hash records provenance, not independent proof that the source is trustworthy. Do not auto-regenerate the lock during ordinary development to conceal local edits.

## 6. Validate without requiring a runtime

Use native file inspection to confirm every required payload exists, both helper modules are present, all nine skill packages have `SKILL.md` with name/description and implicit invocation metadata, relative references resolve, and the managed instructions match the actual installation. Inspect the project configuration and discovery/override handling. Confirm the installed payload contains no source `.git`, maintenance-root replacement, or copied source-only CI/test configuration.

If an existing Python 3.10+ interpreter is available (including an available Codex-provided runtime), use it to run the installed `tools/frc/frc.py --help` and read-only workspace inspection. On macOS `python3` may be available; on Windows `py -3` or `python` may be available. Detect the version; do not assume a command name proves availability or trigger system/Xcode installation prompts. Check known existing runtimes through the agent environment when possible. Do not install Python as part of setup.

If Python is unavailable, the instructions and skills still install. Record helper checks as unavailable. Use available Git/build/file tools directly during development; binary log parsing needs an available decoder. Never claim log parsing or test execution happened without one. If a robot verification command can be safely run with existing tools and is relevant, run it; otherwise report the exact remaining check.

Review the resulting file changes. Report the source revision, installed skill count, preserved/merged files, unresolved conflicts, and validation/helper availability. Explain that normal prompts activate the workflows and a fresh chat may be needed for discovery. Do not claim a model has behaviorally selected a skill merely because its metadata is present. The user can commit the installation through their normal review process; other students then receive it with the project and need no separate personal installation.

## Updating an existing installation

Read the old lock first, then fetch a single desired source revision and its manifest. A missing lock does not permit replacing existing files; treat that case as adoption and compare content. Do not attempt an automatic downgrade of an unsupported lock schema.

For each toolkit-owned file, compare its canonical current hash to the recorded installed hash. If unchanged and upstream changed, apply the new payload. If locally changed, perform a three-way merge against the recorded old source revision when available; preserve the local intent and mark an intentionally customized result project-owned. If old source/hashes are unavailable, do an explicit content comparison and retain ambiguous changes. A pre-existing conflict should not stop independent updates.

Always merge instruction blocks deliberately and retain outside instructions. Configuration, robot context, hardware facts, experiments, and project-owned integrations remain project-owned. Add new required payload. Remove a file dropped upstream only if the old lock proves it was toolkit-owned and its current content is unchanged; preserve/report modified or ambiguous obsolete files. Never delete anything merely because it is missing from the new manifest.

Update the lock to describe files and blocks actually installed. Do not claim the new revision was fully installed for paths still conflicted: retain their old per-file revision and record the pending source revision/status. Revalidate and summarize. No automatic update service, global installation, or external publication is part of this procedure.
