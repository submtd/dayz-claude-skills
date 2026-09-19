---
name: dayz-cfggameplay
description: Use when working with a DayZ server's cfggameplay.json or gameplay settings — build anywhere, base/container damage, raid windows, stamina, spawn gear presets, object spawners, player restricted areas, fast travel, seasonal temperatures, lighting config, hit indicators, map and nav ownership, weapon obstruction, drowning, boat decay, inertia — or when a gameplay settings change did not take effect in game.
---

# DayZ cfggameplay.json

Server-side gameplay tunables, read from the **mission folder** at server start.
Vanilla source: `DZ\worlds\<map>\ce\cfggameplay.json`, mirrored at
`BohemiaInteractive/DayZ-Central-Economy` on GitHub.

**These servers are Xbox, hosted on Nitrado** — the only way to run a custom
Xbox server. Two consequences shape everything below.

**1. Console DayZ has no mod support.** This file plus the mission tree is the
entire customization surface. "Use a mod" is never an answer here.

**2. `init.c` is inert.** Nitrado loads its own `init.c` and never reads yours.
Nothing you put in it takes effect — not `StartingEquipSetup`, not
`CreateCharacter`, not anything. **Any advice that routes through `init.c` is
PC advice and does not apply.** Most DayZ documentation, including Bohemia's,
assumes `init.c` works; on Xbox it does not, which makes `cfggameplay.json`
carry work it was never meant to carry alone.

**[unverified]** The file probably still needs to be present for the server to
boot, even though it is ignored. Do not delete it to find out.

**[unverified]** `init.c` is believed to be the *only* mission file Nitrado
overrides this way. If a setting in some other file mysteriously does nothing,
that belief is the thing to re-test.

## Never answer from memory

Every key name, default, and nesting path **must** come from
`references/keys.md`, not from recall. An agent tested on six routine questions
about this file invented a `"BaseBuilding"` section, a `territoryFlagRequired`
key, a `"PlayerStamina": {"enabled": false}` block and an
`allowFrozenGroundPlanting` key. **None exist.** It also put the file in the
profile directory instead of the mission folder. Fluent, specific, wrong — and
a wrong key name here is silently ignored rather than rejected.

**Before naming any key, read `references/keys.md`.** Before writing an edit,
read the server's actual file. No exceptions:

- Not for "I only need one key."
- Not for "this one is obvious" — `disableBaseDamage` is obvious; the seven
  stamina modifiers and the two spellings of the cold-area check are not.
- Not for "I'll write it and validate after." Validation catches malformed
  JSON, not a plausible key the engine ignores.

**This applies to behavior, not just names.** The wiki is wrong or inverted in
several documented places, and several keys do far less than their names imply.
`keys.md` marks what was read from engine source **[source]** and what rests on
inference **[unverified]**. Do not promote an `[unverified]` claim to fact, and
do not fill a gap the reference explicitly leaves open.

## Read this before your first edit

**1. `enableCfgGameplayFile = 1;` must be in `server.cfg`.** Without it the
server never reads the file at all. First thing to check when a change "did
nothing," and invisible from inside the mission folder.

**2. The file lives in the mission folder**, not the profile directory —
alongside `init.c` and `cfgeconomycore.xml`.

**3. Silent failure is the default.** Malformed JSON, an unknown key, or a key
at the wrong nesting depth produces no error the admin will see. The engine
falls back to defaults and the server boots looking healthy.

**4. Key names differ between maps.** Bohemia's own shipped files disagree:

| Map | Cold-area check key |
|---|---|
| `dayzOffline.chernarusplus` | `disableColdAreaBuildingCheck` |
| `dayzOffline.enoch` (Livonia) | `disableColdAreaBuildingCheck` |
| `dayzOffline.sakhal` | `disableColdAreaPlacementCheck` |

The wiki documents only `disableColdAreaPlacementCheck`. **Use whichever name
your map's vanilla file ships.** `playerRestrictedAreaFiles` and
`lightingConfig: 2` likewise ship only on Sakhal.

**5. A deploy is not a live change.** Uploading puts the file in place; the
server reads it on restart. Report a change as shipped only after the restart.

**6. Some settings are overridden from outside this file.**
`WorldsData.lightingConfig` overrides `serverDZ.cfg`'s, and
`MapData.displayNavInfo: false` defeats `ignoreNavItemsOwnership`. A setting
that "does nothing" may be losing a precedence fight.

## Routing

| Goal | Section | Reference |
|---|---|---|
| Build anywhere | `BaseBuildingData` | `recipes.md` § Build anywhere |
| Open or close a raid window | `GeneralData` | `recipes.md` § Raid windows |
| Unlimited or tuned stamina | `PlayerData.StaminaData` | `recipes.md` § Stamina |
| Custom fresh-spawn loadout | `PlayerData.spawnGearPresetFiles` | `recipes.md` § Spawn gear |
| Place map objects, supply drops | `WorldsData.objectSpawnersArr` | `recipes.md` § Object spawners |
| Fast travel, restricted zones | `WorldsData.playerRestrictedAreaFiles` | `recipes.md` § Fast travel |
| Seasonal temperature curve | `WorldsData.environment*Temps` | `recipes.md` § Temperatures |
| Darker nights | `lightingConfig` + `disablePersonalLight` | `recipes.md` § Darker nights |
| Map / compass / GPS without the item | `MapData` | `recipes.md` § Map QoL |
| Hit direction indicator | `UIData.HitIndicationData` | `keys.md` § UIData |
| Unconscious respawn, respawn dialog | `GeneralData` | `keys.md` § GeneralData |
| Weapon obstruction, drowning, inertia | `PlayerData` | `keys.md` § PlayerData |
| Revert to vanilla | — | `recipes.md` § Reverting |

Full nesting tree, every key, type, vanilla default and per-map variance:
**`references/keys.md`** (schema `version: 123`).

## Things that are not what they look like

Documented in full in `keys.md`; listed here because each one has already cost
someone an afternoon.

- **`disableIsPlacementPermittedCheck` has nothing to do with territory.** It
  skips the item's own `CanBePlaced` rule and affects only tents, fireplaces,
  garden plots and traps. It does nothing for walls, gates, fences or
  watchtowers. Vanilla DayZ has **no territory build-permission system** to
  disable.
- **`disableDistanceCheck` is dead config** — its only consumer is commented
  out in Bohemia's source.
- **`disablePerformRoofCheck` affects watchtowers only.**
- **`disableIsClippingRoofCheck` and `disableIsBaseViableCheck` are client-only**
  — the server short-circuits both in multiplayer.
- **`disableRespawnDialog` is about the character, not the spawn point.** It
  picks custom vs random *character*; `true` forces random.
- **`playerRestrictedAreaFiles` triggers on login, not entry.** Walking into a
  PRA box does nothing at all.
- **`DrowningData` is effectively dead** — you cannot swim underwater, so
  drowning only fires on geometry edge cases.
- **`HitIndicationData` is dormant** until `hitDirectionOverrideEnabled: true`.
- **`displayNavInfo`'s wiki description is inverted.** `true` shows the legend.
- **`version` is never touched** — copy your map's upstream value.

## Editing safely

**Splice, don't reserialize.** Never `json.load` → edit → `json.dump`. The live
files are tab-indented with a meaningful key order; a round trip rewrites the
whole file and makes the diff unreviewable. Clan Wars' bot does this correctly
in `apps/bot/src/cfggameplay.ts` — a textual splice guarded by a parse before
and a read-back after.

**Read the value back after editing.** A key spliced at the wrong nesting depth
still parses. Parsing proves the file loads; only re-reading
`GeneralData.disableBaseDamage` proves you changed the key the server reads.

**Validate before releasing:**

```sh
python3 skills/dayz-cfggameplay/scripts/validate.py /path/to/mission/cfggameplay.json
```

Checks JSON parses, `version` is present, every key is known for the map,
positional arrays are the right length, and every referenced `custom/*.json`
exists and parses.

**Missing referenced files do not fail the boot.** All three path arrays log
via `ErrorEx` and carry on, so the server starts cleanly and silently lacks
the feature — and one bad `spawnGearPresetFiles` entry disables *every*
preset. The validator and the RPT are the only ways to catch this.

## Diagnosing "I changed it and nothing happened"

Work down this list. Each step is cheaper than the one after it.

1. **`enableCfgGameplayFile = 1;` in `server.cfg`?** Nothing below matters
   without it.
2. **Did the server restart** since the file was uploaded?
3. **Run the validator.** It catches malformed JSON, unknown keys, wrong-length
   arrays and missing referenced files — none of which the server reports.
4. **Grep the RPT.** The engine logs load failures there and nowhere else:
   - `Object spawner failed to spawn <name>` — bad class name or p3d path.
   - `Object spawner: invalid path` — p3d outside the allowed directories.
   - `ErrorEx` lines near startup — a referenced spawner, PRA or spawn-gear
     file that would not load. **The server boots normally either way.**
5. **Check precedence.** `serverDZ.cfg`'s `lightingConfig` loses to this file's;
   `displayNavInfo: false` defeats `ignoreNavItemsOwnership`.
6. **Check the key is real for your map** — `keys.md` lists several that do
   nothing, do far less than their name implies, or are spelled differently on
   Sakhal.
7. **Smoke test the file is read at all:** set
   `MapData.displayPlayerPosition: true`, restart, open the map. It is the
   fastest visible confirmation.

**Fast travel has no RPT breadcrumb for a *working* pad** — the only test is to
stand in the box, log out and log back in. A pad that does nothing is usually a
file that failed to load (step 4) or a box the player was not actually inside.

## Resolving behavior the wiki gets wrong

When the wiki is vague or self-contradictory, read the engine — the scripts are
public at `BohemiaInteractive/DayZ-Script-Diff`:

```sh
gh api -X GET search/code -f q='GetDisableSomeCheck repo:BohemiaInteractive/DayZ-Script-Diff' \
  --jq '.items[]? | .path'
gh api "repos/BohemiaInteractive/DayZ-Script-Diff/contents/<path>" --jq '.content' | base64 -d
```

Config flags are read through `CfgGameplayHandler` accessors in
`scripts/3_game/cfggameplayhandler.c`; searching the accessor name finds every
consumer. This is how `disableDistanceCheck` was found dead and
`disableIsPlacementPermittedCheck` was found to have nothing to do with
territory. Findings reflect one game version — re-check after a major patch.

## House conventions (One Life / Clan Wars)

Verified against `BohemiaInteractive/DayZ-Central-Economy@master`. Live Xbox
servers track **`master`**, not a tagged release — diff against `master`.

- **Referenced paths are `./custom/<name>.json`**, relative to the mission root.
  (Vanilla Sakhal uses `pra/warheadstorage.json` — no `./`. Both work.)
- **Build-anywhere is on for every server.** All eleven `HologramData` checks
  and all three `ConstructionData` checks are `true`.
- **`BaseBuildingData` is the one block to re-apply by hand on an upstream
  merge.** On One Life it is the *only* deviation from vanilla — the seasonal
  temperature curves and Sakhal's `lightingConfig: 2` are already
  vanilla-for-that-map. Do not "fix" those.
- **One Life's guiding policy is vanilla-as-possible.** Settings it once ran and
  reverted (`disablePersonalLight`, `disableRespawnInUnconsciousness`) were
  dropped as policy, not because they misbehaved.
- **One Life has vanilla spawn gear because nothing sets otherwise.** Its
  `init.c` contains a `StartingEquipSetup`, but that file is inert on Nitrado —
  the vanilla gear comes from Nitrado's own `init.c`. To change spawn gear
  there, `spawnGearPresetFiles` is the only route; editing `init.c` does
  nothing. (The repo's own `CLAUDE.md` describes the gear as coming from
  `init.c`; that is misleading.)
- **Clan Wars adds**: scheduled `disableBaseDamage`,
  `disableRespawnInUnconsciousness`, zeroed stamina modifiers with
  `staminaMinCap: 100.0`, `shockRefillSpeedUnconscious: 5.0`, all three `MapData`
  QoL flags, a `spawnGearPresetFiles` loadout, four object spawners, and 33
  fast-travel PRAs.
- **Clan Wars' bot toggles raid windows** by splicing `disableBaseDamage` — see
  Editing safely.
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
| Editing `init.c` on a Nitrado/Xbox server | Nothing happens — Nitrado loads its own |
| Changing `lightingConfig` in `serverDZ.cfg` | Overridden by this file |
| `ignoreNavItemsOwnership: true` with `displayNavInfo: false` | Legend stays hidden |
| Parse-and-reserialize | Unreviewable diff, reformatted file |
| Reporting "shipped" at deploy | Change is live only after restart |
| `staminaMax` or `staminaMinCap` set to `0` | Documented as producing unexpected results |
| Diffing Livonia against Chernarus vanilla | False positives on the temperature curves |
