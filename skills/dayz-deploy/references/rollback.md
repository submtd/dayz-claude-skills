# Rolling back a change that broke the server

Operators usually arrive here in a panic, so Claude does the typing. Tell
the operator what each step did in one sentence. Go in order. The first two
steps often turn up that git has nothing to roll back.

## 1. Find what shipped, and when

```sh
gh release list -L 10
gh run list -L 10 --event release          # which releases actually deployed
git log --oneline v1.4.5..v1.4.7           # what changed between good and bad
git diff v1.4.5 v1.4.7 --stat
```

The bad change is the first release after the operator's last known-good
state. Ask when the server was last fine rather than guessing from dates.
Releases are cheap, and there may be several since then.

## 2. Confirm it is the config

Rule these out before reverting anything:

- **The change never deployed.** A tag with no Release, a draft, or a
  failed run. Run `audit.py`. If the "bad" release never reached the
  server, reverting it does nothing.
- **The server was changed by hand.** Run `nitrado.py drift`. It shows a
  file edited in the Nitrado browser, a hand-deleted file, or an armed
  "Reset Mission-xml to default". A git revert cannot touch any of these.
- **Something else broke.** Read the RPT (`dayz-rpt`). If it boots with
  the expected counts and no `!!! [CE]` complaints about your files, the
  config may be innocent.

## 3. Fastest option: re-run the last good deploy (within 30 days)

In the repo's **Actions** tab, open the deploy run for the last good
release, then click **Re-run all jobs**. A re-run uses "the same
`GITHUB_SHA` … and `GITHUB_REF`" as the original, and works "up to 30 days
after its initial run" `[GitHub docs]`. The deploy compares the old files
against the current state file. It sends the old versions back and deletes
any files the bad release added.

*Gloss: "Sent the last good version back to the server."*

**This is half a rollback.** `main` still contains the bad change, so the
next ordinary release ships it again. Do step 4 straight away. Re-running
buys time, and nothing more.

After 30 days the button is gone. Step 4 is the only path.

## 4. Standard: revert, then release

Pick **one** of these two, not both.

**One bad commit, and nothing good after it:**

```sh
git revert <bad-commit>        # opens an editor for the message; save and close
```

If `<bad-commit>` is a merge (a PR landed through keel, for example), add
`-m 1`.

**Put everything back exactly as it was at the last good tag:**

```sh
git restore --source=v1.4.5 --staged --worktree -- .
git commit -m "roll back to v1.4.5: <what broke in game>"
```

- This makes the repo identical to `v1.4.5`. Files added since are
  deleted, and files deleted since come back. It works across merge
  commits.
- **It also undoes any good changes made since `v1.4.5`.** That is the
  point when you do not yet know which change broke it. Re-apply the good
  ones later, one release at a time.
- It also rolls back `.github/workflows/deploy.yml` and `.driftignore`.
  If either has changed since `v1.4.5` (for example, a new exclude),
  keep the current version by adding `':!.github' ':!.driftignore'` after
  the `.`, or check `git diff --stat` before committing.
- Do not use `git revert --no-commit v1.4.5..HEAD` for this. It stops at
  the first merge commit with `is a merge but no -m option was given`
  `[tested]`.

**Then ship it like any release:**

```sh
git tag v1.4.8 && git push origin main v1.4.8
gh release create v1.4.8 --title v1.4.8 --notes "Rolls back v1.4.6–v1.4.7: …"
```

*Gloss: "Recorded an 'undo' as a new change, and shipped it the normal
way."*

Then verify exactly as for any release (`SKILL.md` Everyday step 4). The run
log should list the reverted files as `🔁 File replace:`, with these
exceptions:

- **If you did the step 3 re-run first**, the server already has the good
  files. This release then logs them as `File content is the same, doing
  nothing`. That is correct: `main` and the server now agree.
- A revert of a commit that **added** a file shows `📄 Delete:` for that
  file, and it is removed from the server `[source]`.
- A revert of a commit that **deleted** a file shows `📄 Upload:`, and it
  comes back.

Always a **new** version number. Never move or reuse a tag.

## 5. Never do these

- **`git push --force` / `git reset --hard` on `main`.** This rewrites the
  history that deploys come from, and loses the record of what was live.
- **Re-releasing an old tag as "the fix".** The server goes back, but
  `main` still carries the bad change into the next release. Step 3 is only
  allowed because step 4 follows at once.
- **`dangerous-clean-slate: true`** "to force a clean deploy". It "Deletes
  ALL contents of server-dir, even items in excluded" `[source: README]`,
  hand-uploaded files included. To force a full upload, delete
  `.ftp-deploy-sync-state.json` from the server through the Nitrado file
  browser, then release. That uploads everything and deletes nothing.
- **"Reset Mission-xml to default"** as a panic button. It puts vanilla
  files under a state file that still believes yours are there. See
  `SKILL.md`.

## 6. The world does not roll back

Reverting config stops further damage. It does not undo what the bad config
already did:

- **Surplus loot** from a raised `nominal` stays until each item's
  `lifetime` expires, or longer if players carry or stash it. Look up the
  affected types' `lifetime` in `db/types.xml` and tell the operator
  honestly how long that is. Whether carried or stashed copies count
  against `nominal` depends on the type's `count_in_*` flags. See
  `dayz-types`.
- **Bases, vehicles and inventories** created under a bad rule stay.
- **A storage wipe** (Nitrado settings → **Storage wipe**, which takes
  effect at the next restart and then switches itself off `[operator]`)
  clears all of it, bases included.
  - **Before launch, or with no real population:** wipe freely. It is the
    clean reset after testing.
  - **Once players are building bases:** it is the last resort. Say what
    it costs players, and let the operator decide.

**[unverified]** whether temporarily shortening a type's `lifetime` makes
items that already spawned age out sooner. The CE is `proto native`, and no
source settles it. Do not offer it as a fix without an in-game test.
