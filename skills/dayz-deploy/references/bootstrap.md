# From files on Nitrado to a repo that deploys

For an operator whose mission exists only on the Nitrado server. Claude
runs the commands. After each step, say in one sentence what it did.

**Needs:**
- A GitHub account, `git`, and the `gh` CLI signed in (`gh auth login`).
  - On a Mac: `brew install git gh`.
  - On Windows: install Git for Windows and GitHub CLI, then run
    everything below in **Git Bash**. **[unverified]** the `winget` IDs;
    check `winget search` before quoting one.
- For the download, a Nitrado long-life token with the `service` and
  `file` scopes (Nitrado web panel → Account → Security → Long-life access
  tokens).

## 1. Freeze hand edits

From now until the first Release is verified, **nobody edits files through
the Nitrado file browser.** The first deploy uploads every file in the repo
over whatever is on the server. If someone edits the server between the
download and that deploy, the edit is lost.

**A bot cannot be told to freeze.** If anything automated writes to the
mission folder (Clan Wars' platform does), list those files in a
`.driftignore` before the first Release. The first deploy overwrites them
with the repo's copies; the bot restores them on its next write. Ask the
operator which files their automation owns.

*Gloss: "Paused live edits so the copy we take stays the truth."*

## 2. Download the mission folder

**Default, with no extra software:**

```sh
export NITRADO_TOKEN=…
python3 <skill-dir>/scripts/nitrado.py pull ~/dayz/my-server
```

If the token sees several servers, the script lists them. Re-run with
`--service <id>`. It refuses to write into a non-empty directory, and it
skips `.ftp-deploy-sync-state.json`, which belongs to the deploy and not to
the mission.

**If the server already has a `.ftp-deploy-sync-state.json`** (from an
earlier attempt at this, or a previous admin), delete it through the
Nitrado file browser before the first Release. Otherwise the first deploy
trusts that stale record and uploads only part of the repo.

**Where the FTP login is:** in the Nitrado web panel, open the server,
go to its **Dashboard**, and find the **FTP Credentials** card. It shows
Hostname, Port (21), Username and Password; click the eye icon to reveal
the password `[operator screenshot]`.
- The FTP **Hostname** is a `….gamedata.io` name. It is **not** the game
  server IP shown at the top of the page; do not use the game IP for FTP.
- The pencil icon next to the password changes it. After a change,
  update the `FTP_PASSWORD` secret too, or every deploy fails.

**Fallback, FileZilla:** connect with those four values, then drag
`/dayzxb_missions/dayzOffline.<map>/` to an empty local folder. That
path is relative to the FTP login's root `[operator]`.

*Gloss: "Copied the server's mission files to this computer."*

## 3. Make it a repo

```sh
cd ~/dayz/my-server
cat > .gitignore <<'EOF'
.DS_Store
Thumbs.db
desktop.ini
*.bak
*~
EOF
git init -b main
git add -A
git commit -m "mission files as downloaded from the live server"
gh repo create my-server --private --source . --push
```

- **Private by default.** The mission files show loot positions, custom
  structures and admin-area coordinates. That is a recommendation, not a
  rule. A vanilla-style server may not care.
- **`.gitignore` is console-shaped.** A Nitrado console mission folder has
  no `storage_*`, `*.RPT` or `*.ADM` to ignore; those live elsewhere
  `[live listing]`. What gets committed by accident is operating-system
  clutter.
- **Ignoring a file does not untrack it.** If `.DS_Store` was committed
  before the `.gitignore`, it stays tracked and keeps deploying. Clan Wars
  has exactly this. Fix it with `git rm --cached .DS_Store`, then commit.
- `areaflags.map` (~75 MB) prints git's 50 MiB warning on push. That is
  expected. It is under GitHub's 100 MiB block `[GitHub docs]`.

*Gloss: "Saved the whole folder as version one, and put it on GitHub where
only you can see it."*

## 4. Add the four secrets

```sh
gh secret set FTP_SERVER       # Dashboard → FTP Credentials → Hostname
gh secret set FTP_USERNAME
gh secret set FTP_PASSWORD
gh secret set FTP_DIRECTORY    # /dayzxb_missions/dayzOffline.<map>/
```

Each command prompts for its value, so nothing lands in shell history.

- `FTP_DIRECTORY` **must end in `/`** `[action README]`. The maps are
  `chernarusplus`, `enoch` (Livonia) and `sakhal`.
- Secrets cannot be read back. If one is wrong, set it again.

*Gloss: "Gave GitHub the server's FTP login, locked so that nobody,
including you, can read it back."*

## 5. Add the workflow

Write `.github/workflows/deploy.yml`. This is the Sakhal variant: it skips
cleanly, rather than failing, until the secrets exist. That also means a
green run can have deployed nothing, which is why Everyday step 4 checks
the log. Its exclude list is the minimum. The live servers add
`.superpowers/**`, `node_modules/**` and `vendor/**` for their own tooling
(`deploy-yml.md`).

```yaml
name: FTP Deploy (on release)

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest

    # Map the secret to an env var so it can be used in step `if:` conditions
    # (the `secrets` context is not available in `if:` expressions).
    env:
      FTP_SERVER: ${{ secrets.FTP_SERVER }}

    steps:
      # Skip (rather than fail) the whole deploy until the FTP secrets exist.
      - name: Skip when FTP is not configured
        if: env.FTP_SERVER == ''
        run: echo "::notice::FTP_SERVER secret is not set — skipping deploy. Configure the FTP_* repository secrets to enable deployment."

      - name: Checkout repository
        if: env.FTP_SERVER != ''
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Deploy changed files via FTP
        if: env.FTP_SERVER != ''
        uses: SamKirkland/FTP-Deploy-Action@v4.3.5
        with:
          server: ${{ secrets.FTP_SERVER }}
          username: ${{ secrets.FTP_USERNAME }}
          password: ${{ secrets.FTP_PASSWORD }}
          protocol: ftp
          port: 21

          # Only changed files are uploaded; this state file on the server
          # records the last deploy. Deleting it forces one full upload.
          state-name: .ftp-deploy-sync-state.json

          local-dir: ./
          server-dir: ${{ secrets.FTP_DIRECTORY }}

          # NEVER true: it deletes everything in the mission folder.
          dangerous-clean-slate: false

          # Anything not listed here lands on the game server.
          exclude: |
            .git/**
            **/.git/**
            .github/**
            **/.github/**
            .claude/**
            **/.claude/**
            docs/**
            **/*.md
            .gitignore
            .gitattributes
            .driftignore
```

```sh
git add .github/workflows/deploy.yml
git commit -m "deploy the mission folder to Nitrado on each published Release"
python3 <skill-dir>/scripts/audit.py .
```

The workflow lint must come back clean.

*Gloss: "Added the rule: when you publish a Release, GitHub uploads the
changed files to the server."*

## 6. First Release, then check

```sh
git push
git tag v1.0.0 && git push origin v1.0.0
gh release create v1.0.0 --title v1.0.0 --notes "First deploy from GitHub."
gh run list -L 1
```

The first run's log says `No file exists on the server … this must be your
first publish! 🎉` and uploads every file. That is expected: the files are
identical to what is already there, so nothing changes in game.

Then:

```sh
python3 <skill-dir>/scripts/nitrado.py drift .
```

It should report **no `missing`, `modified` or `pending` entries.** `stray`
entries are files that were on the server but not in the repo. Usually these
are hand-uploaded leftovers: ask the operator about each one before deleting
anything.

From here on, the rule for hand edits in the Nitrado browser is simple:
**make the same change in the repo, or it does not exist.** The deploy
cannot see a hand edit. It survives only until the repo's copy of that file
next changes, and is then silently overwritten. After any hand edit, run
`drift`.

*Gloss: "Shipped for the first time, and checked that the server and GitHub
now agree."*
