---
name: dayz-cfggameplay
description: Use when working with a DayZ server's cfggameplay.json or gameplay settings — build anywhere, base/container damage, stamina, spawn gear presets, object spawners, player restricted areas, teleports, seasonal temperatures, lighting config, hit indicators, map and nav ownership, weapon obstruction, drowning, boat decay, inertia — or when a gameplay settings change did not take effect in game.
---

# DayZ cfggameplay.json

Server-side gameplay tunables, read from the **mission folder** at server start.
Vanilla source: `DZ\worlds\<map>\ce\cfggameplay.json`, mirrored at
`BohemiaInteractive/DayZ-Central-Economy` on GitHub.

## Never answer from memory

Every key name, default, and nesting path in this file **must** come from
`references/keys.md`, not from recall. This is not a style preference — an agent
tested on six routine questions about this file invented a `"BaseBuilding"`
section, a `territoryFlagRequired` key, a `"PlayerStamina": {"enabled": false}`
block and an `allowFrozenGroundPlanting` key. **None of them exist.** It also
placed the file in the profile directory instead of the mission folder. The
answers were fluent, specific, and wrong, and a wrong key name here is not a
no-op — see "Silent failure" below.

**Before naming any key, read `references/keys.md`.** Before writing an edit,
read the server's actual file. No exceptions:

- Not for "I only need one key."
- Not for "this one is obvious" — `disableBaseDamage` is obvious; the seven
  stamina modifiers and the two spellings of the cold-area check are not.
- Not for "I'll write it and validate after." Validation catches malformed
  JSON, not a plausible key the engine ignores.

## Read this before your first edit

**1. `enableCfgGameplayFile = 1;` must be in `server.cfg`.** Without it the
server never reads the file at all. This is the first thing to check when a
change "did nothing," and it is invisible from inside the mission folder.

**2. The file lives in the mission folder**, not the profile directory —
alongside `init.c` and `cfgeconomycore.xml`.

**3. Silent failure is the default.** Malformed JSON, an unknown key, or a key
at the wrong nesting depth produces no error the admin will see. The engine
falls back to built-in defaults and the server boots looking healthy. Anything
undefined inside a data class is read as zero, which is why
`hitDirectionOverrideEnabled` exists — it is how the engine tells "0 because
you set it" from "0 because the block never loaded."

**4. Key names differ between maps.** Bohemia's own shipped files disagree:

| Map | Cold-area check key |
|---|---|
| `dayzOffline.chernarusplus` | `disableColdAreaBuildingCheck` |
| `dayzOffline.enoch` (Livonia) | `disableColdAreaBuildingCheck` |
| `dayzOffline.sakhal` | `disableColdAreaPlacementCheck` |

The wiki documents only `disableColdAreaPlacementCheck`. **Use whichever name
your map's vanilla file ships** — copy it from upstream rather than typing it.
`playerRestrictedAreaFiles` and `lightingConfig: 2` likewise ship only on Sakhal.

**5. A deploy is not a live change.** Uploading the file puts it in place; the
server reads it on restart. Report a change as shipped only after the restart.

**6. Two things here are genuinely unknown**, and `references/keys.md` marks
them as such: what the engine does with a wrong `version`, and what
`lightingConfig: 2` (Sakhal's vanilla value) renders. A gap flagged as unknown
is not an invitation to fill it in — say it is undocumented.

## Routing

| Goal | Section | Reference |
|---|---|---|
| Build anywhere / ignore placement checks | `BaseBuildingData` | `references/recipes.md` § Build anywhere |
| Stop base or tent/barrel damage | `GeneralData` | `keys.md` § GeneralData |
| Unlimited or tuned stamina | `PlayerData.StaminaData` | `recipes.md` § Stamina |
| Custom fresh-spawn loadout | `PlayerData.spawnGearPresetFiles` | `recipes.md` § Spawn gear |
| Place map objects | `WorldsData.objectSpawnersArr` | `recipes.md` § Object spawners |
| Restricted zones / teleports | `WorldsData.playerRestrictedAreaFiles` | `recipes.md` § Restricted areas |
| Seasonal temperature curve | `WorldsData.environment*Temps` | `recipes.md` § Temperatures |
| Night brightness | `WorldsData.lightingConfig` | `keys.md` § WorldsData |
| Map / compass / GPS without the item | `MapData` | `recipes.md` § Map QoL |
| Hit direction indicator | `UIData.HitIndicationData` | `keys.md` § UIData |
| Unconscious respawn, respawn dialog | `GeneralData` | `keys.md` § GeneralData |
| Weapon obstruction, drowning, inertia | `PlayerData` | `keys.md` § PlayerData |
| Revert to vanilla | — | `recipes.md` § Reverting |

Full nesting tree, every key, type, vanilla default and per-map variance:
**`references/keys.md`** (schema `version: 123`).

## Editing rules

**Splice, don't reserialize.** Never `json.load` → edit → `json.dump`. The live
files are tab-indented with a meaningful key order; a round trip rewrites the
whole file and makes the diff unreviewable. Change the bytes you mean to change
and leave the rest identical. (Clan Wars' bot does exactly this in
`apps/bot/src/cfggameplay.ts` — textual splice, guarded by a parse before and a
read-back after.)

**Read the value back after editing.** A key spliced at the wrong nesting depth
still parses. Parsing proves the file loads; only re-reading
`GeneralData.disableBaseDamage` proves you changed the key the server reads.

**Validate before releasing:**

```sh
python3 skills/dayz-cfggameplay/scripts/validate.py /path/to/mission/cfggameplay.json
```

Checks JSON parses, `version` is present, every key is known for the map, and
every `objectSpawnersArr` / `playerRestrictedAreaFiles` / `spawnGearPresetFiles`
path resolves on disk. A missing referenced file is a boot-time failure.

## House conventions (One Life / Clan Wars)

Verified against `BohemiaInteractive/DayZ-Central-Economy@master`. Live Xbox
servers track **`master`**, not a tagged release — diff against `master`.

- **Referenced paths are `./custom/<name>.json`**, relative to the mission root.
  (Vanilla Sakhal uses `pra/warheadstorage.json` — no `./`. Both work.)
- **Build-anywhere is on for every server.** All eleven `HologramData` checks and
  all three `ConstructionData` checks are `true`. Note this also turns off
  territory permission enforcement via `disableIsPlacementPermittedCheck`.
- **`BaseBuildingData` is the one block to re-apply by hand on an upstream
  merge.** On One Life servers it is the *only* deviation from vanilla — every
  other value, including the seasonal temperature curves and Sakhal's
  `lightingConfig: 2`, is already vanilla-for-that-map. Do not "fix" those.
- **Clan Wars adds**: `disableBaseDamage`, `disableRespawnInUnconsciousness`,
  zeroed stamina modifiers with `staminaMinCap: 100.0`,
  `shockRefillSpeedUnconscious: 5.0`, all three `MapData` QoL flags, a
  `spawnGearPresetFiles` loadout, four object spawners, and 33 PRAs.
- **Clan Wars uses PRAs as teleporters** — a small `PRABoxes` trigger volume
  with a distant `safePositions3D`, so entering the box ejects the player to the
  destination. One file per destination.
- **One Life uses vanilla spawn gear** plus `StartingEquipSetup` in `init.c` —
  it has no `spawnGearPresetFiles` key. Don't add one; change `init.c`.
- Files in `custom/` are not automatically live. Clan Wars' `custom/` holds
  `admin-castle-explosives.json`, `admin-castle-flag-kit.json` and
  `flag-supplies.json` that no array references — they spawn nothing.

## Common mistakes

| Mistake | What happens |
|---|---|
| Missing `enableCfgGameplayFile = 1;` | Entire file ignored, no error |
| Key invented from memory | Ignored, vanilla default applies, server looks fine |
| Right key, wrong nesting depth | Same — parses, does nothing |
| `disableColdAreaPlacementCheck` on Chernarus | Ignored; that map wants `...BuildingCheck` |
| Referenced `./custom/*.json` not uploaded | Boot-time failure |
| Parse-and-reserialize | Unreviewable diff, reformatted file |
| Reporting "shipped" at deploy | Change is live only after restart |
| `staminaMax` or `staminaMinCap` set to `0` | Bohemia documents this as producing unexpected results |
