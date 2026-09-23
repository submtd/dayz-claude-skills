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

```sh
git revert <bad-commit>                    # one bad commit
git revert --no-commit v1.4.5..HEAD        # everything since the last good tag
git commit -m "roll back <what it did in game>: <why>"
git tag v1.4.8 && git push origin main v1.4.8
gh release create v1.4.8 --title v1.4.8 --notes "Rolls back v1.4.6–v1.4.7: …"
```

*Gloss: "Recorded an 'undo' as a new change, and shipped it the normal
way."*

Then verify exactly as for any release (`SKILL.md` Everyday step 4). The run
log should list the reverted files as `Replace`:

- A revert of a commit that **added** a file shows `Delete` for that file,
  and it is removed from the server `[source]`.
- A revert of a commit that **deleted** a file shows it as an upload, and it
  comes back.

Always a **new** version number. Never move or reuse a tag.

## 5. Never do these

- **`git push --force` / `git reset --hard` on `main`.** This rewrites the
  history that deploys come from, and loses the record of what was live.
- **Re-releasing an old tag as "the fix".** The server goes back, but
  `main` still carries the bad change into the next release. It is the same
  trap as step 3 with no follow-up.
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
  honestly how long that is.
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
