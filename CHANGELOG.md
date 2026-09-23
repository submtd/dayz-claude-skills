# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] - 2026-09-22

### Added

- **`dayz-mapgroups`** — skill for `mapgroupproto.xml` and `mapgrouppos.xml`:
  where loot may sit inside a building type, how much fits, which buildings on
  the map are lootable, usage routing, fixed-offset item placement via
  `<dispatch>`/`<proxy>`, custom POIs and loot concentration, disabling loot at
  one location, and loot-point thinning for server performance. Records that
  loot tiers live in `areaflags.map` rather than in any mission XML, so
  `<value>` on a surface building does nothing — and that the raster is
  PC-authored but deploys to console fine.
- `dayz-mapgroups` ships a validator that resolves `mapgrouppos.xml` group
  names against `mapgroupproto.xml` **case-insensitively** (Bohemia's own
  files rely on this; a case-sensitive check reports 6–11 orphans on every
  untouched vanilla map), checks the proto vocabulary against
  `cfglimitsdefinition.xml`, requires a `db/types.xml` registration for every
  `<proxy type>`, and notes usages that carry `nominal` with no capacity in
  these files — as information only, since `areaflags.map` can grant a usage
  the XML never mentions. Takes `--capacity` to print loot capacity and
  saturation by usage, documented as a lower bound rather than a total.
- **`dayz-adm`**: skill for the `.ADM` admin log, built from engine source
  and checked against 146,308 production lines from four Xbox servers. It
  records the shapes parsers get wrong: `(DEAD)` is state, not an event;
  every respawn writes `is connected`; `is choosing to respawn` is a death
  only when the player is alive; ` died.` covers starvation, falls, logouts
  and blade suicides; `killed by  with …` (two spaces) is a kill whose killer
  the game lost; `id=ERROR` exists; `Dismantled` names parts differently from
  `Built`; player positions are `x, z, altitude`, while flag and teleport
  positions put altitude in the middle; and the clock offset's sign is easy
  to invert.
- `dayz-adm` ships `classify.py`, which sorts every line of real `.ADM` files
  into a known shape, errors on any it cannot place, on missing headers and
  on cut tails, and reports each trap it sees.

### Changed

- `dayz-cfggameplay`: `disableRespawnInUnconsciousness` is read only from
  `cfggameplay.json`, so Nitrado's panel toggle for it does nothing while
  the JSON is enabled. The ADM note now quotes the real respawn sequence and
  its `(DEAD)` form.
- `scripts/ci_check.py` runs its `--help` and missing-file checks on every
  script under `skills/*/scripts/`, not only `validate.py`.

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
