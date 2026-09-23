# dayz-claude-skills

Claude Code skills for DayZ server development — the things we keep re-learning,
written down once.

Packaged as a Claude Code plugin so every DayZ repo can install it and stay in
sync with a `git pull`.

## Install

From any DayZ repo (One Life, Clan Wars, a mission config repo — anywhere you
want the skills available):

```
/plugin marketplace add ~/Development/submtd/dayz-claude-skills
/plugin install dayz
```

Once this repo has a remote, the marketplace can be added by URL instead:

```
/plugin marketplace add submtd/dayz-claude-skills
```

Updating is `git pull` in this repo — installed plugins follow the source.

## Skills

| Skill | Covers |
|---|---|
| `dayz-cfggameplay` | `cfggameplay.json`: build anywhere, base/container damage, raid windows, stamina, spawn gear presets, object spawners, fast travel, seasonal temperatures, lighting, hit indicators, map and nav ownership, weapon obstruction, drowning, inertia, boat decay. Includes a validator. |
| `dayz-globals` | `db/globals.xml`: loot condition, cleanup and corpse lifetimes, loot respawn rates, territory flag refresh, idle mode, session timers, infected and animal caps, food decay. Its validator checks the cross-file pairs against `cfgspawnabletypes.xml`, `db/types.xml` and `env/zombie_territories.xml`. |
| `dayz-mapgroups` | `mapgroupproto.xml` and `mapgrouppos.xml`: where loot may sit inside a building type, how much fits, which buildings on the map are lootable, usage routing, fixed placement via `<dispatch>`/`<proxy>`, custom POIs and loot concentration, disabling loot at one location, loot-point thinning for performance. Its validator resolves pos against proto case-insensitively, checks the vocabulary against `cfglimitsdefinition.xml`, requires a `db/types.xml` registration for every proxy type, and notes usages carrying `nominal` that these files give no capacity — as information, since `areaflags.map` routes loot too. |
| `dayz-types` | `db/types.xml`: per-item nominal and min, lifetimes and base decay, quantity, loot tiers and usage, the `count_in_*` and `crafted` flags, disabling an item versus removing it, adding classnames vanilla omits, and the total-nominal loot budget. Its validator checks names against `cfglimitsdefinition.xml` and cross-checks `cfgignorelist.xml`, `cfgspawnabletypes.xml` and `db/events.xml`. |

Each skill is a directory under `skills/` holding a `SKILL.md`, optional
`references/` for heavy lookup material, and optional `scripts/` for tooling.

## Sources of truth

Vanilla mission files come from
[`BohemiaInteractive/DayZ-Central-Economy`](https://github.com/BohemiaInteractive/DayZ-Central-Economy).
**Live Xbox servers track `master`, not a tagged release** — diff against
`master`.

Key semantics come from the Bohemia wiki —
[Gameplay Settings](https://community.bistudio.com/wiki/DayZ:Gameplay_Settings)
and [Central Economy Configuration](https://community.bistudio.com/wiki/DayZ:Central_Economy_Configuration).
**The wiki has been wrong or inverted in seven places so far**, so where it
disagrees with a shipped file, the shipped file wins and the reference says so.

For behavior the wiki describes vaguely or gets backwards, read the engine:
[`BohemiaInteractive/DayZ-Script-Diff`](https://github.com/BohemiaInteractive/DayZ-Script-Diff)
publishes the game scripts. Searching a `CfgGameplayHandler` accessor or a
`GetCEGlobal*` call name finds every consumer, and has settled several
questions the wiki could not.

## Adding a skill

Skills here are written against the same bar: they exist to stop a specific
mistake that has already cost time, and they are tested before they land.

1. Establish the baseline — ask a fresh agent the questions the skill should
   answer, *without* the skill, and record what it gets wrong. Fluent
   fabrication is the usual failure, not a blank.
2. Write `SKILL.md` against those specific failures. The frontmatter
   `description` states only *when* to use the skill, never what it does.
3. Move heavy lookup material into `references/`, so `SKILL.md` stays small
   enough to be worth loading.
4. Re-run the baseline questions with the skill present and confirm they now
   come back right.
5. Verify any script against real mission files and against deliberately broken
   ones.

## Validating a mission file

```sh
python3 skills/dayz-cfggameplay/scripts/validate.py /path/to/mission/cfggameplay.json
python3 skills/dayz-globals/scripts/validate.py     /path/to/mission/db/globals.xml
python3 skills/dayz-types/scripts/validate.py       /path/to/mission/db/types.xml
python3 skills/dayz-mapgroups/scripts/validate.py   /path/to/mission
```

`dayz-types` also takes `--budget`, which prints total `nominal` by category —
the loot budget that governs how many objects the server has to track.
`dayz-mapgroups` takes `--capacity`, which prints loot capacity and saturation
by usage flag.

Checks that the JSON parses, that `version` is present, that every key is one
the engine actually reads for that map, that positional arrays are the right
length, and that every referenced `custom/*.json` exists and parses. Exits
non-zero on errors.
