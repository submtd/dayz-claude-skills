# The deploy workflow, input by input

All four live servers run the same `.github/workflows/deploy.yml`. The
Sakhal copy, reproduced in `bootstrap.md`, adds a guard that skips the
deploy cleanly while the FTP secrets are unset. Input semantics come from
the action's README at `v4.3.5` and its bundled source.

## Trigger

```yaml
on:
  release:
    types: [published]
```

**Only a published Release deploys.** A pushed tag does not, a draft does
not, and a push to `main` does not. That is deliberate: a commit can sit on
`main` safely until someone chooses to ship it. `audit.py` errors on any
other trigger, and warns if `push:` is added (every commit would then go
live).

## Checkout

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```

The action compares file hashes against its state file, not git history, so
`fetch-depth: 0` is harmless but not required. If `areaflags.map` is ever
moved to Git LFS, add `lfs: true`. It defaults to `false`, and without it
the deploy uploads a pointer file instead of the map
`[source: actions/checkout action.yml]`.

## The action's inputs

| Input | Live value | What it does, and the trap |
|---|---|---|
| `server` / `username` / `password` | `${{ secrets.FTP_* }}` | Nitrado's FTP credentials. Secrets are write-only; nobody can read them back from GitHub. |
| `protocol` / `port` | `ftp` / `21` | Plain FTP: the password crosses the network unencrypted. **[unverified]** whether Nitrado accepts `ftps`. Test it before switching. |
| `local-dir` | `./` | The repo root **is** the mission folder. It must end in `/` `[README]`. |
| `server-dir` | `${{ secrets.FTP_DIRECTORY }}` | `/dayzxb_missions/dayzOffline.<map>/`. It **must end in `/`** `[README]`. Because it is a secret, `audit.py` cannot check it, so check it when you set it. |
| `state-name` | `.ftp-deploy-sync-state.json` | The deploy's record of what it uploaded, kept on the server. Renaming it orphans the old record and forces one full upload. |
| `dangerous-clean-slate` | `false` | `true` "Deletes ALL contents of server-dir, even items in excluded" on every run `[README]`. **Never** set it. To force a full upload, delete the state file instead. |
| `exclude` | see below | Setting it **replaces** the action's defaults, so list everything. |

## How a deploy decides what to do

`[source: ftp-deploy HashDiff.ts, deploy.ts]`

1. Download the state file from `server-dir`. If there is none, treat the
   server as empty: this is a first deploy, so everything uploads and
   nothing is deleted.
2. Hash every local file that is not excluded.
3. Compare the local hashes with the state file:
   - **Only local** → `Upload`.
   - **Different hash** → `Replace`.
   - **Only in the state file** → `Delete`.
   - **Same hash** → nothing.
4. Write a new state file.

What each outcome looks like in the run log `[source: deploy.ts,
syncProvider.ts]`:

```
📄 Upload: custom/new-spawner.json
🔁 File replace: db/types.xml
📄 Delete: custom/old-spawner.json
⚖️  File content is the same, doing nothing: cfggameplay.json
Uploading: 338 kB -- Deleting: 21.3 kB -- Replacing: 9.21 kB
removing "custom/old-spawner.json"
🎉 Sync complete. Saving current server state to "….ftp-deploy-sync-state.json"
```

The real server is never listed. A file the state file does not know about
is invisible, and so is one it wrongly believes is present. That is what
`nitrado.py drift` is for.

## The exclude list

The live list:

```
.git/**            **/.git/**
.github/**         **/.github/**
.claude/**         **/.claude/**
.superpowers/**    **/.superpowers/**
docs/**
node_modules/**    **/node_modules/**
vendor/**          **/vendor/**
**/*.md
.gitignore
.gitattributes
```

Add `.driftignore` too if the repo has one (see `SKILL.md`). The live
repos do not have one yet.

**Anything not excluded lands on the game server.** When you add a tooling
directory (scripts, notes, an editor project), add it here in the same
commit. `**/*.md` is why a `CLAUDE.md` or `README.md` in the repo never
ships. `audit.py` errors if `.git/**` or `.github/**` is missing, and warns
if `**/*.md` is.

Excluded paths are also never deleted from the server. The action filters
them out of the state file before comparing (`deploy.ts`).

## Node 20 deprecation

Every live run currently prints:

> `Node.js 20 is deprecated. The following actions target Node.js 20 but are
> being forced to run on Node.js 24: actions/checkout@v4,
> SamKirkland/FTP-Deploy-Action@v4.3.5.`

The deploys still succeed, so treat it as a warning, not a failure. Watch
it when GitHub changes runners. **[unverified]** whether a Node 24-native
release of the action exists yet. Check upstream before bumping the pin.
