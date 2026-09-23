---
name: dayz-deploy
description: Use when putting a DayZ server's mission folder under git or GitHub, shipping a mission change to a Nitrado server, rolling back a change that broke a server, checking whether the live server still matches the repo, or when an operator says a deploy "did nothing" or a file will not go away.
---

# DayZ mission deploys: GitHub to Nitrado

Most server operators edit files live in Nitrado's web file browser. When
an edit breaks the server, they have no record of what changed and no way
back. Putting the mission folder in a GitHub repo, with a Release-triggered
FTP deploy, gives them both. It also brings new ways to fail silently. This
skill is for Claude doing the typing, one step at a time, with a one-line
**plain-language gloss** after each step so the operator could manage
without Claude in an emergency.

The deploy is `SamKirkland/FTP-Deploy-Action@v4.3.5`, run by a workflow
that triggers only on a **published** Release. It uploads the repo root to
`/dayzxb_missions/dayzOffline.<map>/` on the Nitrado FTP server. The mission
folder holds config only. The world (`storage_1`) lives elsewhere, so no
deploy can reach bases or characters `[live listing]`.

## Never answer from memory

Two kinds of proof, and they answer different questions:
- **A change is shipped** when the deploy run's log lists its files. That
  is the report for every release (Everyday step 4).
- **The server matches the repo** when `nitrado.py drift` says so. Run it
  after bootstrap, after a rollback, and whenever something looks off.

"I published the Release" proves neither, and neither does "the Releases
page looks fine".

Asked eight routine questions with no tools, an agent got the mechanics
mostly right. It still gave two answers that would hurt a server:

- For a server reset by Nitrado's **"Reset Mission-xml to default"**, it
  offered `dangerous-clean-slate: true` as a fix. That setting "Deletes ALL
  contents of server-dir, even items in excluded" `[source: action README
  v4.3.5]`. It destroys every hand-uploaded file and is never the fix. The
  fix is to delete the state file (see below).
- Its `.gitignore` was PC-shaped: `storage_*/`, `*.RPT`, `*.ADM`. None of
  those are in a Nitrado console mission folder. The things that *do* get
  committed by accident are `.DS_Store` and editor backups. Clan Wars
  deployed a `.DS_Store` to its live server.

**Paths.** The scripts live in this skill's `scripts/` directory. Call
them by the absolute path of the directory this skill was loaded from,
because the operator's shell is in their mission repo, not in this plugin.
Commands are bash/zsh. On Windows, run them in **Git Bash**, which comes
with Git for Windows, not in PowerShell.

## What to do

| The operator says | Go to |
|---|---|
| "Set this up" / "my files are only on Nitrado" | `references/bootstrap.md` |
| "Ship this" / "make this live" | **Everyday** below |
| "I broke the server" / "undo that" / "roll back" | `references/rollback.md` |
| "Is the server what the repo says?" / "a file won't go away" | `nitrado.py drift` |
| "Did my last release deploy?" / "the tag did nothing" | `audit.py` |
| "What does this workflow setting do?" | `references/deploy-yml.md` |
| "We have more admins now" / "we keep breaking things" | `references/keel.md` |

## Everyday: ship a change

The default is the shortest flow that cannot fail silently: commit to
`main`, tag it, publish the Release. Keel's PR flow is an upgrade (see
`references/keel.md`), not a prerequisite.

1. **Get up to date, edit, commit.** Run `git pull` first; someone may
   have changed the repo on github.com. Then make the edit, and run
   `git add -A && git commit -m "disable NVGoggles and Plastic_Explosive"`.
   The summary names the in-game effect, not the file: "disable NVGoggles",
   not "update types.xml". Put concrete before → after values in the body
   (`git commit` without `-m` opens an editor for both).
   *Gloss: "Saved a snapshot of the change with a note saying what it does
   in game."*
2. **Tag the next patch version**, then push both. Find the last version
   with `git tag --sort=-v:refname | head -1`, add one to the last number,
   then run `git tag v1.4.7 && git push origin main v1.4.7`.
   *Gloss: "Named this snapshot. A name on its own changes nothing on the
   server."*
3. **Publish the Release.** This is the deploy trigger:
   `gh release create v1.4.7 --title v1.4.7 --notes "…"`
   *Gloss: "Told GitHub to send this snapshot to the server."*
4. **Verify.** Run `gh run list -L 3` and wait for `completed / success` on
   `v1.4.7`. Then run
   `gh run view <id> --log | grep -E "(Upload|File replace|Delete): "` and
   check that the files you changed are listed. The action logs
   `📄 Upload: x`, `🔁 File replace: x` and `📄 Delete: x`
   `[source: deploy.ts]`. Note that it is `File replace`, not `Replace`.
   - **No lines at all means nothing shipped**, even though the run is
     green. If the log says `FTP_SERVER secret is not set — skipping
     deploy`, the secrets are missing.
   - If every file says `File content is the same, doing nothing`, the
     server already had this content. That is normal after a re-run
     rollback (`references/rollback.md`).
   *Gloss: "Checked that the upload actually happened and sent the right
   files."*
5. **It goes live at the next restart** (every 2 hours on the live
   servers). Lowering a `nominal` settles over the affected items'
   lifetimes. Do not judge a reduction after one restart. To confirm the
   files loaded, compare the RPT boot counts (`dayz-rpt`).

Never report a change as shipped after step 3. Step 4 is the report.

## Things that are not what they look like

- **A tag deploys nothing. A published Release does.** Clan Wars `v1.6.22`
  was tagged and never released, so its change only reached the server
  because `v1.6.23` carried it `[history]`. Draft Releases do not deploy
  either. `audit.py` finds both.
- **Ticking "pre-release" still deploys.** `published` fires for
  pre-releases `[GitHub docs]`. There is no staging channel here: the next
  restart runs whatever was published.
- **Deleting or editing a Release undoes nothing.** The files are already
  on the server. Undo means a rollback.
- **The deploy deletes only what it uploaded.** It compares the repo with
  its own record, `.ftp-deploy-sync-state.json` on the server, and never
  with the server itself `[source: ftp-deploy HashDiff.ts]`:
  - Removing a file from the repo **does** delete it from the server, if
    the deploy put it there. Clan Wars `v1.6.63` removed 48 airdrop files,
    and the API listing confirms they are gone `[live]`.
  - A file uploaded by hand is not in that record, so **no deploy and no
    rollback will ever remove it.** Six such files sit in Clan Wars'
    `custom/` today `[live]`.
- **The state file is the deploy's belief, not the server's reality.**
  - A file deleted by hand stays missing, and the deploy will not send it
    again until its content changes in the repo. Clan Wars'
    `flag-supplies.json` has been in git since `v1.0.0` and is absent on the
    server `[live]`.
  - A file edited by hand keeps the hand edit until the repo's version
    changes, and then it is silently overwritten.
- **"Reset Mission-xml to default" leaves you vanilla under a green deploy
  history.**
  - The Nitrado toggle restores defaults at the next restart, then turns
    itself off `[operator]`. The operator believes it resets the whole
    mission tree, not only the XML `[unverified]`.
  - The state file still says your files are there, so the next Release
    uploads only what changed since the last one. Everything else stays
    vanilla.
  - **The fix is to delete `.ftp-deploy-sync-state.json` from the server,
    then publish a Release.** With no state file, the deploy treats the
    server as empty. It uploads everything and deletes nothing
    `[source: deploy.ts]`.
  - **[unverified]** whether the reset removes the state file itself. If
    it does, the next Release re-uploads everything on its own. `drift`
    tells you which case you are in: it prints `no deploy state on the
    server` when the file is gone.
  - Also **[unverified]**: whether custom files (`custom/*.json`) survive
    a reset. Check with `drift` before assuming.
- **"Never delete the state file" is too strong.** Deleting it is the
  correct forced full upload after a reset or a hand-deleted file. Its only
  cost is one full upload, `areaflags.map` (~75 MB) included. What must
  never happen is `dangerous-clean-slate: true`.
- **Rolling back config does not roll back the world.**
  - Items the CE spawned under a bad `nominal` stay until their `lifetime`
    runs out or storage is wiped `[operator, observed]`.
  - The same goes for bases built under a bad rule, and for anything in
    player inventories.
  - A storage wipe is free before launch. Once a real population is
    building bases, it is the last resort `[operator]`. See
    `references/rollback.md`.
- **Hand-uploading through the live server leaves strays behind.**
  - The operator's own workflow: DayZ Editor on a Windows laptop, uploaded
    through Nitrado's file browser, downloaded on a Mac, committed.
  - Anything uploaded that way and then renamed or never committed stays
    on the server forever.
  - The route is fine. Run `drift` afterwards, or skip the hop by
    uploading to the repo on github.com or through GitHub Desktop.
- **A rename that only changes case leaves two files on the server.**
  - A Mac checkout is case-insensitive (`core.ignorecase true`). Nitrado's
    file system is not.
  - One Life Chernarus has both `cfgignorelist.xml` (Nitrado's original)
    and `cfgIgnoreList.xml` (deployed, and vanilla's spelling). One Life
    Sakhal has both `cfgEffectArea.json` and `cfgeffectarea.json` `[live]`.
  - The deploy never removes the copy it did not upload. **[unverified]**
    which one the game reads.
  - `drift` names these as case twins. Keep the repo's spelling identical
    to vanilla's, and remove the other by hand once confirmed.
- **A bot that writes to the server is a second deploy pipeline.**
  - Clan Wars' platform uploads object-spawner files through the Nitrado
    API: awards, booster kits, faction supplies and the teleport hub, each
    carrying live player names. Its bot also flips `cfggameplay.json` for
    the raid window and edits `events.xml` for truck wipes `[clan-wars
    source + live diff]`.
  - The repo holds `{}` placeholders for the spawner files. **A release
    that changes a bot-owned file overwrites the bot's live version**,
    until the bot writes it again.
  - Keep bot-owned files out of normal edits, and list them in a
    `.driftignore` at the repo root. `drift` then reports them as
    `managed` rather than drift. Add `.driftignore` to the workflow's
    `exclude` list, because the deploy uploads it otherwise.
  - `.driftignore` holds one glob per line, and `#` starts a comment. It
    uses the same glob rules as the workflow's `exclude` list, so
    `custom/awards.json` and `custom/*-supplies.json` both work, and a
    pattern with no `/` matches that name in any folder.
- **`init.c` deploys but does nothing.** Nitrado runs its own `init.c`
  `[operator]`.
- **Anything not in the workflow's `exclude` list lands on the game
  server.** That includes tooling directories added later. See
  `references/deploy-yml.md`.
- **`areaflags.map` in Git LFS needs `lfs: true` on `actions/checkout`.**
  The default is `false` `[source: actions/checkout action.yml]`.
  Without it, the deploy uploads a small pointer file in place of the map.
  At ~75 MB the file triggers git's 50 MiB warning but is under GitHub's
  100 MiB block `[GitHub docs]`, so plain git works and LFS is optional.
  The warning is expected, not an error.
- **`db/types.xml` is re-saved at every restart, content unchanged.**
  - Seen on all four live servers. Its timestamp lands a minute after each
    even-hour restart, long after the last release, and no other `db/` file
    is touched `[live]`.
  - The content is byte-identical to the repo (Clan Wars, by hash).
  - **[unverified]** what writes it. The operator expects nothing to write
    it outside a release.
  - `drift` therefore always reports it as `touched`. Run `--hash`; do not
    treat it as a hand edit.
- **Two Nitrado toggles act at the next restart and are visible only until
  then:** "Storage wipe" and "Reset Mission-xml to default". `drift` reads
  both from the API and flags them as `ARMED`.

## Scripts

Both use only the standard library. Exit status: 0 clean, 1 findings,
2 could not run.

```sh
python3 <skill-dir>/scripts/audit.py /path/to/mission-repo
```

`audit.py` needs `gh` for the release checks:
- **Tags with no Release.** A tag whose commit a later successful deploy
  carried is reported as a note.
- **Draft Releases.**
- **Releases whose deploy run failed.**
- **The deploy workflow itself:** wrong trigger, `dangerous-clean-slate`,
  missing `.git/**` or `.github/**` excludes, `server-dir` without a
  trailing `/`.

```sh
export NITRADO_TOKEN=…   # Nitrado long-life token, scopes: service + file
python3 <skill-dir>/scripts/nitrado.py drift /path/to/mission-repo [--service ID] [--hash]
python3 <skill-dir>/scripts/nitrado.py pull  /path/to/empty-dir    [--service ID]
```

`drift` lists the live mission folder and compares it with the repo and
with the state file. Each finding carries one of these labels:

| Label | Meaning |
|---|---|
| `stray` | Never uploaded by the deploy, or under a path the workflow now excludes |
| `missing` | The deploy believes the file is there, and it is not. With no state file: in the repo, not on the server |
| `modified` | The size differs from the last deploy. With `--hash`: the content differs |
| `touched` | Same size, written after the last deploy finished; confirm with `--hash` |
| `pending-upload` | In the repo but not yet released |
| `pending-delete` | The next release removes it |
| `ARMED` | A Nitrado toggle is set to act at the next restart |
| `managed` | Matches a pattern in the repo's `.driftignore`: written by a bot, so not drift |

`pull` downloads the mission folder for bootstrap.

- `drift` compares the **working tree**, not the last commit, so
  uncommitted edits show as `pending-upload`.
- **Xbox only.** Both commands read `/dayzxb_missions/`. **[unverified]**
  the folder names on PlayStation and PC Nitrado servers; there, the
  commands fail with a Nitrado API error.
- "After the last deploy finished" means the state file's own timestamp on
  the server. The deploy uploads that file last, and its recorded
  `generatedTime` is stamped before the upload starts
  `[source: localFiles.ts, syncProvider.ts]`.

Both commands only read from the server. With several servers on one
token, they list them and ask for `--service`. A walk takes about a minute,
because each Nitrado list call takes 0.4–12 s.
