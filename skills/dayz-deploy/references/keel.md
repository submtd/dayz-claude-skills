# Growing past commit-to-main: keel

The default flow (commit to `main` → tag → Release) suits one admin who
checks each release. Upgrade when either of these becomes true:

- **More than one person edits the mission.** Two admins committing to
  `main` ship each other's unreviewed changes in the next Release.
- **The same kind of break keeps happening.** A second pair of eyes on the
  diff before it merges is cheaper than another rollback.

Keel is a Claude Code plugin that runs a branch → PR → review → merge
workflow and enforces it with a hook and GitHub branch protection. Use its
skills rather than restating them here:

| Step | Skill |
|---|---|
| Add keel to the mission repo (`.keel.json`, changelog, PR template, CI gate) | `keel:init` |
| Make GitHub refuse direct pushes to `main` | `keel:protect` |
| Start a change on its own branch | `keel:start-work` |
| Open the PR with a changelog entry | `keel:finish-work` |
| Review it | `keel:review` |
| Merge it | `keel:land` |
| Cut a version | `keel:release`, then `keel:ship` |

## What changes for a mission repo

- **Choose `trunk` topology.** `main` is production and the only long-lived
  branch. That matches a repo whose deploy is "publish a Release from
  `main`".
- **The deploy trigger does not change.** Merging a PR still ships nothing.
  Publishing the Release still ships everything. `keel:ship` runs
  `gh release create v<version>` `[source: keel 0.10.0 ship/SKILL.md]`,
  which publishes a non-draft Release, so shipping is deploying. Verify
  the deploy run exactly as in `SKILL.md` Everyday step 4.
- **The changelog becomes the release notes.** Keel's gate requires an
  `## [Unreleased]` entry in each PR. Write it for admins and players: the
  in-game effect, then before → after values.
- **Rollback is the same revert, through a PR.** Under protection, `git
  revert` happens on a branch and lands like any change. In an emergency the
  "re-run the last good deploy" step in `rollback.md` needs no PR, which is
  why it comes first.

## A server that does this by hand

One Life runs a two-branch flow without keel:
- Work lands on `develop` through PRs.
- A `release/x.y.z` branch rolls the Keep-a-Changelog file.
- It merges to `main`, and the Release is published from there.

It is heavier than `trunk` and buys a staging branch. That branch is only
worth having if something can actually test from it. On Nitrado console,
the only test server is another paid server.
