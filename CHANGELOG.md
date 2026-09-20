# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-09-19

### Added

- **`dayz-cfggameplay`** — skill for `cfggameplay.json`: build anywhere,
  base and container damage, raid windows, stamina, spawn gear presets,
  object spawners, fast travel, seasonal temperatures, lighting, hit
  indicators, map and nav ownership, weapon obstruction, drowning, inertia,
  boat decay. Ships a validator.
- **`dayz-globals`** — skill for `db/globals.xml`: loot condition, cleanup
  and corpse lifetimes, loot respawn rates, territory flag refresh, idle
  mode, session timers, infected and animal caps, food decay. Its validator
  checks the cross-file pairs against `cfgspawnabletypes.xml`,
  `db/types.xml` and `env/zombie_territories.xml`.
- **`dayz-types`** — skill for `db/types.xml`: per-item nominal and min,
  lifetimes and base decay, quantity, loot tiers and usage, the `count_in_*`
  and `crafted` flags, disabling an item versus removing it, adding
  classnames vanilla omits, and the total-nominal loot budget. Its validator
  checks names against `cfglimitsdefinition.xml` and cross-checks
  `cfgignorelist.xml`, `cfgspawnabletypes.xml` and `db/events.xml`, and
  takes `--budget` to print total nominal by category.
- Repo lifecycle via keel — `.keel.json` (trunk topology, `main`,
  same-repo branches, comment-review policy, changelog required), changelog
  gate workflow, PR and issue templates, an inert `CODEOWNERS`, and an MIT
  `LICENSE`.
- CI via rigging — `.github/workflows/ci.yml` running `scripts/ci_check.py`,
  which checks the plugin manifest, every skill's frontmatter and
  name-matches-directory, that all Python compiles, and that each validator
  responds to `--help` and still exits 2 on a missing file.
- Secret scanning via hull — `.github/workflows/security.yml` running
  gitleaks on push and pull request.
- `.gitignore` baseline sections managed by stow (`base` and `python`).

### Notes

- Every skill documents its sources as `[source]` (engine scripts),
  `[shipped]` (counted from Bohemia's vanilla files), `[operator]`
  (confirmed on the live servers) or `[unverified]`, so a reader can tell
  what is settled from what is inferred.
- The validators are built to stay silent on a coherent config and to treat
  Bohemia's own shipped defects as tagged warnings rather than errors, so an
  untouched vanilla mission passes.
