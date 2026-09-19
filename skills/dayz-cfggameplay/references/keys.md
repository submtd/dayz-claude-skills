# cfggameplay.json — complete key reference

Schema `"version": 123`. Defaults verified against
`BohemiaInteractive/DayZ-Central-Economy@master` (`dayzOffline.chernarusplus`,
`dayzOffline.enoch`, `dayzOffline.sakhal`).

**Three sources, in descending order of authority:**

1. **Engine source** — `BohemiaInteractive/DayZ-Script-Diff`. Where a key's
   behavior was read out of the actual check, it is marked **[source]** and the
   file and line are cited. This beats everything else.
2. **Shipped vanilla files** — authoritative for defaults.
3. **The [Bohemia wiki](https://community.bistudio.com/wiki/DayZ:Gameplay_Settings)** —
   useful, but wrong or inverted in several documented places. Where it
   disagrees with 1 or 2, it loses and the disagreement is flagged.

Claims that came from neither source, and rest on an operator's experience or
on inference, are marked **[unverified]**. Do not promote one to fact.

Script-source findings reflect one game version. After a major patch, a key
marked dead or narrow is worth re-checking.

## Context: console has no mods

These servers are Xbox. **Console DayZ has no mod support**, so
`cfggameplay.json` plus the mission files are the *entire* customization
surface. A PC answer that says "use a mod for that" is not an answer here.

## Nesting tree

```
version                                    int
GeneralData
  disableBaseDamage                        bool
  disableContainerDamage                   bool
  disableRespawnDialog                     bool
  disableRespawnInUnconsciousness          bool
PlayerData
  spawnGearPresetFiles                     string[]   (not shipped; add to use)
  disablePersonalLight                     bool
  StaminaData
    sprintStaminaModifierErc               float
    sprintStaminaModifierCro               float
    staminaWeightLimitThreshold            float
    staminaMax                             float
    staminaKgToStaminaPercentPenalty       float
    staminaMinCap                          float
    sprintSwimmingStaminaModifier          float
    sprintLadderStaminaModifier            float
    meleeStaminaModifier                   float
    obstacleTraversalStaminaModifier       float
    holdBreathStaminaModifier              float
  ShockHandlingData
    shockRefillSpeedConscious              float
    shockRefillSpeedUnconscious            float
    allowRefillSpeedModifier               bool
  MovementData
    timeToStrafeJog                        float
    rotationSpeedJog                       float
    timeToSprint                           float
    timeToStrafeSprint                     float
    rotationSpeedSprint                    float
    allowStaminaAffectInertia              bool
  DrowningData
    staminaDepletionSpeed                  float
    healthDepletionSpeed                   float
    shockDepletionSpeed                    float
  WeaponObstructionData
    staticMode                             int
    dynamicMode                            int
WorldsData
  lightingConfig                           int
  objectSpawnersArr                        string[]
  environmentMinTemps                      float[12]
  environmentMaxTemps                      float[12]
  wetnessWeightModifiers                   float[5]
  playerRestrictedAreaFiles                string[]   (shipped on Sakhal only)
BaseBuildingData
  HologramData
    disableIsCollidingBBoxCheck            bool
    disableIsCollidingPlayerCheck          bool
    disableIsClippingRoofCheck             bool
    disableIsBaseViableCheck               bool
    disableIsCollidingGPlotCheck           bool
    disableIsCollidingAngleCheck           bool
    disableIsPlacementPermittedCheck       bool
    disableHeightPlacementCheck            bool
    disableIsUnderwaterCheck               bool
    disableIsInTerrainCheck                bool
    disableColdAreaBuildingCheck           bool   ← Chernarus, Livonia
    disableColdAreaPlacementCheck          bool   ← Sakhal
    disallowedTypesInUnderground           string[]
  ConstructionData
    disablePerformRoofCheck                bool
    disableIsCollidingCheck                bool
    disableDistanceCheck                   bool
UIData
  use3DMap                                 bool
  HitIndicationData
    hitDirectionOverrideEnabled            bool
    hitDirectionBehaviour                  int
    hitDirectionStyle                      int
    hitDirectionIndicatorColorStr          string
    hitDirectionMaxDuration                float
    hitDirectionBreakPointRelative         float
    hitDirectionScatter                    float
    hitIndicationPostProcessEnabled        bool
MapData
  ignoreMapOwnership                       bool
  ignoreNavItemsOwnership                  bool
  displayPlayerPosition                    bool
  displayNavInfo                           bool
VehicleData
  boatDecayMultiplier                      float
```

There is no `BaseBuilding`, `PlayerStamina`, `UnconsciousState` or
`territoryFlagRequired`. If you are reaching for one of those, you are
recalling, not reading.

---

## Root

| Key | Type | Default | Effect |
|---|---|---|---|
| `version` | int | `123` | File format version. **Never touch it** — copy your map's upstream value. What a wrong value does is undocumented and untested; do not claim a consequence. In practice no operator has seen a mismatch cause anything. |

## GeneralData

### `disableBaseDamage` — bool, `false`

`true` makes player-built base structures un-raidable.

- **Raid vectors it closes:** explosives, shooting walls, and punching walls
  given enough time.
- **Vehicles cannot damage bases at all**, with or without this flag. That is
  not what it controls.
- **Decay still runs.** Bases continue to decay on the lifetime set in
  `db/types.xml`. `true` means un-raidable, *not* permanent.
- Clan Wars toggles this on a schedule via its bot, making raiding a defendable
  scheduled window rather than a 4am surprise.

### `disableContainerDamage` — bool, `false`

`true` makes tents, barrels, sea chests and crates indestructible.

- **The usual reason to leave it `false` is admin ops, not balance:** a
  misplaced tent can get stuck in geometry, and destroying it is the only way
  to remove it. `true` means you are stuck with it.
- Players **cannot pack up a container that has gear inside**, so raiders were
  never going to haul storage away regardless. Loot leaves item by item.
- Operators who close a raid window usually toggle this **together with**
  `disableBaseDamage`, so nothing can be chipped at from outside. There is no
  overlap between the two — base parts and containers are cleanly separate —
  they are just set together for completeness.

### `disableRespawnDialog` — bool, `false`

Removes the prompt shown when a player respawns.

- **The prompt is about the character, not the spawn point.** It asks whether
  to respawn as your custom character or a random one. It has no effect on
  spawn location and nothing to do with `cfgplayerspawnpoints.xml`.
- `true` skips the prompt and gives **always a random character**.

### `disableRespawnInUnconsciousness` — bool, `false`

`true` removes the Esc-menu Respawn button while unconscious.

- **The body remains and is lootable.** Respawning kills your character in
  place; the killer is not denied the gear. What they lose is the chance to
  take a hostage, revive, or interrogate.
- **ADM gotcha:** when a player respawns out of unconsciousness the death line
  **names no killer**. The log shows the hits, the health, the unconscious
  line, then an unattributed death. A parser that only reads the death line
  loses the kill. The killer must be inferred from the preceding hit lines.
  Clan Wars solves this in `packages/domain/src/death-verdict.ts` — `finishedBy()`
  credits the last player hit when the victim was knocked out after it, and
  reports `cause = 'finished'` rather than claiming the log stated a kill.
- Clan Wars runs `true` alongside `shockRefillSpeedUnconscious: 5.0`, a
  deliberate pairing: you cannot escape being downed, but you are not down long.

## PlayerData

### `spawnGearPresetFiles` — string[], not shipped

Paths to Player Gear Spawn preset files. Absent or `[]` = vanilla spawn gear.

- **Multiple files mean random selection between presets**, not merged loadouts.
- **`spawnWeight` is an integer, minimum 1, and appears at every level** —
  preset, per-slot `discreteItemSets` variant, and `discreteUnsortedItemSets`.
  Higher is more likely. With one preset and one option per slot, every
  `spawnWeight` in the file is inert.
- **It overrides `StartingEquipSetup()` in `init.c`.** Adding this key to a
  server that sets gear in `init.c` silently disables that code. See
  [Spawning Gear Configuration](https://community.bistudio.com/wiki/DayZ:Spawning_Gear_Configuration).
- It **completely overrides character spawning**, including the character built
  in the main menu.
- `characterTypes: []` leaves the player the character type they last chose in
  the creation menu. Populating it takes that choice away.

### `disablePersonalLight` — bool, `false`

`true` removes the ambient light that follows the player at night.

- The mechanic is confirmed: vanilla attaches a faint light to the player so
  nights are never pitch black. `true` removes it.
- **[unverified]** Whether darker nights actually land depends on whether
  players can brighten their displays, and that has not been measured on
  console. The only known data point is a PC player using a driver-level gamma
  setting. Do not assert that console players do or don't do the same.
- Pairs with `lightingConfig: 1`. Doing only one is a half-measure — One Life
  ran `disablePersonalLight` without ever running `lightingConfig: 1`.

### PlayerData.StaminaData

Modifiers are multipliers on consumption rate: `0` = free, `1.0` = vanilla,
`2.0` = double drain.

| Key | Default | Activity |
|---|---|---|
| `sprintStaminaModifierErc` | `1.0` | Sprinting upright |
| `sprintStaminaModifierCro` | `1.0` | Sprinting crouched |
| `sprintSwimmingStaminaModifier` | `1.0` | Fast swimming |
| `sprintLadderStaminaModifier` | `1.0` | **Ladder climbing** |
| `meleeStaminaModifier` | `1.0` | Heavy melee attacks and evasion |
| `obstacleTraversalStaminaModifier` | `1.0` | **Jumping and vaulting walls** |
| `holdBreathStaminaModifier` | `1.0` | Holding breath to steady a scope |

**Ladders and obstacles are different keys.** `sprintLadderStaminaModifier` is
ladders; `obstacleTraversalStaminaModifier` is vaulting walls. Clan Wars sets
the first to `0` and leaves the second at `1.0`, so ladders are free and
wall-jumping is not. Do not describe either as "climbing."

**[unverified]** `holdBreathStaminaModifier: 0` is believed to give an infinite
breath hold — a real sniping advantage. Neither operator nor source has
confirmed it.

#### The load system

Carried weight reduces your *effective* maximum stamina, sliding it from
`staminaMax` down toward `staminaMinCap`.

| Key | Default | Effect |
|---|---|---|
| `staminaMax` | `100.0` | The ceiling — all available stamina. **Operators do not move this.** `0` is documented as producing unexpected results. |
| `staminaMinCap` | `5.0` | **A percentage.** Vanilla `5.0` means a fully loaded player has 5% of the stamina an unloaded player has. **This is the one to tune.** `0` is documented as producing unexpected results; use `100.0` to make load irrelevant. |
| `staminaWeightLimitThreshold` | `6000.0` | Free-carry allowance before any penalty. **[unverified]** Read as grams, i.e. 6kg. |
| `staminaKgToStaminaPercentPenalty` | `1.75` | **[unverified]** % of max stamina lost per kg over the threshold. `0` disables the whole mechanism. |

**[unverified]** Worked example, believed correct but not tested: 20kg carried
is 14kg over the 6kg threshold → 14 × 1.75 = 24.5% penalty → effective max of
75.5, floored at `staminaMinCap`.

**Zeroing `staminaKgToStaminaPercentPenalty` silently disables a cluster of
downstream mechanics** — `staminaWeightLimitThreshold`, the relevance of
`staminaMinCap`, and `wetnessWeightModifiers` all stop mattering, because
weight no longer feeds anything.

### PlayerData.ShockHandlingData

Shock is a pool that *depletes* when hit; you go unconscious when it bottoms
out. "Refill" is recovery back up.

| Key | Default | Effect |
|---|---|---|
| `shockRefillSpeedConscious` | `5.0` | Shock recovered per second while conscious. |
| `shockRefillSpeedUnconscious` | `1.0` | Per second while unconscious. **Raising this shortens how long players stay knocked out.** The vanilla 5:1 asymmetry is what makes knockouts last. Clan Wars uses `5.0`. |
| `allowRefillSpeedModifier` | `true` | Lets ammo-type settings modify shock recovery. **Mechanism not understood** — no operator experience and no source read. Negative evidence only: Clan Wars runs it at default `true` with unconscious refill at `5.0` and sees no pathologically short knockouts, so whatever it does is not dramatic at that configuration. |

### PlayerData.MovementData — **low confidence throughout**

| Key | Default | Note |
|---|---|---|
| `timeToStrafeJog` | `0.1` | Blend time for diagonal movement, jogging |
| `rotationSpeedJog` | `0.3` | **Wiki says `0.15`; every shipped file says `0.3`** |
| `timeToSprint` | `0.45` | Time from jog to sprint |
| `timeToStrafeSprint` | `0.3` | Blend time for diagonal movement, sprinting |
| `rotationSpeedSprint` | `0.15` | |
| `allowStaminaAffectInertia` | `true` | **[unverified]** Believed to make low stamina increase sluggishness. Plausible, untested. |

**Do not describe the direction of scale on the five floats.** In game, turning
while jogging or sprinting feels near-instant regardless, which does not match
a straightforward reading of these as turn rates. **[unverified]** The likely
explanation is that they govern the character model's rotation rather than the
camera or aim, so they are barely perceptible in first person. Vanilla on every
known server. Do not tune without testing in game.

Minimum accepted value for all five is `0.01`.

### PlayerData.DrowningData — effectively dead config

| Key | Default | Effect |
|---|---|---|
| `staminaDepletionSpeed` | `10.0` | Stamina lost per second while drowning |
| `healthDepletionSpeed` | `10.0` | Health lost per second while drowning |
| `shockDepletionSpeed` | `10.0` | Shock lost per second while drowning |

**Drowning is near-impossible in normal play, so these almost never fire.**

- **You cannot swim underwater.** There is no diving mechanic. Entering deep
  water toggles a surface swim animation — you float and cannot submerge.
- Drowning fires only when **your head is underwater while the game does not
  consider you swimming.** Known ways in: being trapped in geometry as water
  rises (the Livonia bunker water puzzle reliably does this), and going prone
  in water deep enough to cover you but shallow enough not to trigger the swim
  state.
- **[unverified]** A submerged vehicle is likely the same trigger — seated, not
  swimming, head underwater. Mods exist specifically to stop players drowning
  in submerged vehicles, which implies it happens.

Tuning these changes nothing on a normal server. Do not spend time here.

### PlayerData.WeaponObstructionData

Both default `1`. `0` = off (never obstruct), `1` = on (obstruct then lift),
`2` = always (obstruct, don't lift).

| Key | Applies to |
|---|---|
| `staticMode` | World geometry — walls, doorframes, trees |
| `dynamicMode` | Moving entities — players, vehicles, animals |

This is the gun-lift behavior: barrel contact raises the weapon and blocks
fire. It is what prevents shooting through walls.

- `dynamicMode` is why a teammate crowding you gun-lifts your weapon; in a
  firefight a player can body-block your ability to shoot. `0` removes that at
  the cost of letting players shoot through each other.
- **Value `2` has no known practitioner.** The wiki's "obstruct, don't lift"
  admits two readings — weapon stays raised while in contact, or fire is
  blocked with no lift animation. Unresolved.

## WorldsData

### `lightingConfig` — int

Defaults: `0` on Chernarus and Livonia, `2` on Sakhal.

- `0` = brighter nights, `1` = darker nights.
- **`2` is a Sakhal-specific lighting profile**, not a brightness level — an
  arctic map has different sun angles and snow reflectance. Leave it alone; do
  not copy it to another map.
- **Wiki claims the default is `1`. Every shipped file disagrees.**
- **Precedence:** `lightingConfig` also exists in `serverDZ.cfg`, and when
  `enableCfgGameplayFile` is on, `WorldsData.lightingConfig` **overrides it.**
  Changing it in `serverDZ.cfg` and seeing nothing happen is this rule biting.

### `objectSpawnersArr` — string[], `[]`

Object Spawner JSON files, loaded at mission start. See `recipes.md` for file
shape and constraints.

- **Spawned objects do not count against central economy limits.** This makes
  object spawners an **economy bypass**: guaranteed placement that never
  competes with CE nominals or cleanup. It is the reliable way to do supply
  drops, where a `types.xml` approach is at the mercy of the economy settling.
- **Objects respawn on every restart.** Take the item and a fresh one appears
  next restart — effectively infinite supply.
- **[source]** `scripts/3_game/objectspawner.c:48`. The spawner creates each
  object with `ECE_SETUP | ECE_UPDATEPATHGRAPH | ECE_CREATEPHYSICS |
  ECE_NOLIFETIME | ECE_DYNAMIC_PERSISTENCY`, then:

  ```
  if (item.enableCEPersistency)
  {
      flags &= ~ECE_DYNAMIC_PERSISTENCY;
      flags &= ~ECE_NOLIFETIME;
  }
  ```

  So `0` (the default) spawns the object with **no lifetime** — CE cleanup
  never removes it — and dynamic persistency. `1` clears both, giving the
  object a **normal lifetime**, which makes it subject to CE cleanup and
  standard persistence.

  Note the flag does not control respawning directly: **the spawner re-runs
  every mission start regardless**, which is where the observed
  respawn-each-restart behavior comes from. What `enableCEPersistency: 1`
  changes is that the object now has a lifetime and can be cleaned up.

### `environmentMinTemps` / `environmentMaxTemps` — float[12]

Monthly ambient temperature band, January→December. **Exactly 12 values.**

**The twelve values advance with the in-game month**, so
`serverTimeAcceleration` in `serverDZ.cfg` determines how often players
actually experience the cold ones. A heavily accelerated server cycles through
winter regularly; a slow one may sit in summer for weeks. These values are not
inert, but their relevance is set by a different file.

| Map | `environmentMinTemps` | `environmentMaxTemps` |
|---|---|---|
| Chernarus | `[-3, -2, 0, 4, 9, 14, 18, 17, 13, 11, 9, 0]` | `[3, 5, 7, 14, 19, 24, 26, 25, 18, 14, 10, 5]` |
| Livonia (enoch) | `[-7, -7.4, -4.1, 1.5, 7, 11.3, 20.4, 19.1, 18, 5.3, 0.8, -3.6]` | `[-2.5, -2.1, 2.3, 9, 15.5, 19.4, 25, 22, 21, 10.5, 4.2, 0.1]` |
| Sakhal | `[-6.5, -9.5, -6.5, -9.5, 2, 6, 9, 10, 6, 1, -5, -10]` | `[-3, -5, -3, -5, 9, 14, 16, 17, 14, 8, 1, -3]` |

The wiki's stated defaults match **no** shipped file. Use this table. A Livonia
or Sakhal server showing colder temps than Chernarus is at its own vanilla, not
modified — diff against the matching map.

### `wetnessWeightModifiers` — float[5], `[1.0, 1.0, 1.33, 1.66, 2.0]`

Item weight multiplier by wetness: DRY, DAMP, WET, SOAKED, DRENCHED. Drenched
doubles gear weight.

**Weight feeds the stamina calculation and nothing else** — DayZ's inventory is
slot-based, not weight-limited. So on a vanilla server a river crossing leaves
you compromised until you dry off, and on a server with
`staminaKgToStaminaPercentPenalty: 0` this key is completely inert.

### `playerRestrictedAreaFiles` — string[], Sakhal only (`["pra/warheadstorage.json"]`)

**The trigger is login, not entry.** A player who *logs in* inside a PRA box is
moved to one of the file's `safePositions3D`. Walking into the box while
already logged in does **nothing at all** — no ejection, no message.

- A PRA does nothing except move the player. No damage, no kill, no build block.
- A box may list multiple targets; the player is moved to one of them.
- Bohemia's Sakhal use is preventing players from logging in inside the warhead
  storage area.
- Because the check runs at login rather than continuously, many areas cost
  nothing. Clan Wars runs 33 with no performance or reliability issues.
- **Operators call the teleport use "fast travel."** It is known but not
  widely used. See `recipes.md`.
- **[source]** `cfgplayerrestrictedareahandler.c:34`. Each filename is tried as
  `$mission:<filename>` first, then falls back to
  `dz/worlds/<worldname>/ce/<filename>` — which is how vanilla Sakhal's
  `pra/warheadstorage.json` resolves from the game's own world folder. On total
  failure it calls `ErrorEx` and **`continue`s to the next file**; the server
  boots normally and that one area simply does not exist.

## Missing referenced files do not fail the boot — **[source]**

All three path arrays degrade quietly rather than stopping the server. Nothing
a player or admin sees says anything is wrong.

| Array | On load failure |
|---|---|
| `objectSpawnersArr` | `ErrorEx`, continues to the next file (`objectspawner.c:28`). That file's objects simply never spawn. |
| `playerRestrictedAreaFiles` | `ErrorEx`, continues (`cfgplayerrestrictedareahandler.c:43`). That area does not exist. |
| `spawnGearPresetFiles` | `ErrorEx` and **`return false` for the whole set** (`cfgplayerspawnhandler.c:22`). **One bad preset file disables every preset**, not just its own. |

This is why `scripts/validate.py` matters: a missing or malformed referenced
file produces a server that boots cleanly and silently lacks the feature.
Checking the RPT or running the validator is the only way to notice.

## BaseBuildingData

Building is two stages with a check gate on each. **`HologramData`** governs the
placement preview — the ghost you position before committing. **`ConstructionData`**
governs the build action itself. Disabling only one half gets you a broken
half-measure: the ghost turns green but the build fails, or you cannot position
the ghost at all. Build-anywhere needs both.

### HologramData — **[source]** `scripts/4_world/classes/hologram.c`

Every key is a **disable** flag: `true` turns the check off. All default `false`.

| Key | What it actually gates |
|---|---|
| `disableIsCollidingBBoxCheck` | `IsCollidingBBox()` **and** `IsCollidingGeometryProxy()`. **One flag, two checks** — there is no separate geometry-proxy key. |
| `disableIsCollidingPlayerCheck` | `m_IsCollidingPlayer`. |
| `disableIsClippingRoofCheck` | `IsClippingRoof()`. **The server short-circuits this** — `if (IsServer() && IsMultiplayer()) return false`. The server never enforces it; the flag only affects the client's preview. |
| `disableIsBaseViableCheck` | `IsBaseViable()`. Same server short-circuit, with Bohemia's comment that it is "not required to solve server-side fixes for clipping." |
| `disableIsCollidingGPlotCheck` | `m_IsCollidingGPlot` — separate state from the garden plot fertility rule below. |
| `disableIsCollidingAngleCheck` | Pitch and roll against the config limit. **Yaw is not checked**, despite the limit vector being named `m_YawPitchRollLimit` — only indices 1 and 2 are read. |
| `disableIsPlacementPermittedCheck` | The item type's own `CanBePlaced()`. **See below — this is not what its name suggests.** |
| `disableHeightPlacementCheck` | Vertical delta between player and placement point. Limit is **±1.5m** (`DEFAULT_MAX_PLACEMENT_HEIGHT_DIFF`). |
| `disableIsUnderwaterCheck` | Liquid group plus a four-corner sea-level test. **Snow is explicitly excluded** (`LIQUID_GROUP_WATER - LIQUID_SNOW`) — relevant on Sakhal. |
| `disableIsInTerrainCheck` | Four-corner raycast, 0.3m→1m. |
| `disableColdAreaBuildingCheck` | Garden plots on frozen ground. **Chernarus and Livonia spelling.** |
| `disableColdAreaPlacementCheck` | Same effect. **Sakhal spelling** — the only one the wiki documents. |

**Three checks have no disable flag and always run:** `IsFloating()`,
`IsHidden()`, and `IsCollidingZeroPos()` (blocks placement at world origin).
Build-anywhere is never unconditional.

#### `disableIsPlacementPermittedCheck` is not about territory — **[source]** `hologram.c:858`

```
bool IsPlacementPermitted()
{
    if (CfgGameplayHandler.GetDisableIsPlacementPermittedCheck())
        return true;
    return m_Parent && m_Parent.CanBePlaced(m_Player, GetProjectionPosition());
}
```

It skips **the item type's own `CanBePlaced` rule**. The base implementation in
`entityai.c` returns `true`, and only four classes override it:

| Item | Its rule |
|---|---|
| Tents | Vertical gap between player and placement within **±1.5m** |
| Fireplaces | Within **0.3m** of the ground surface |
| Garden plots | Within 0.3m of surface **and** `IsSurfaceFertile(surface_type)` |
| Traps | `IsPlaceableAtPosition(position)` |

**For walls, gates, fences and watchtowers it does nothing** — they do not
override `CanBePlaced`. Its real effects when `true` are tents at height
offsets, floating fireplaces, and garden plots on infertile surfaces.

**Vanilla DayZ has no territory build-permission system at all.** Territory
flags govern decay radius and base lifetime, not who may build where;
exclusive build rights are a mod feature. There is no permission here to
disable. Any claim that this flag affects territory enforcement is false.

Bohemia's own comment on the garden plot height constant reads *"this is
important when server has collision checks disabled"* — these limits were
written anticipating build-anywhere servers.

#### `disallowedTypesInUnderground` — string[], `["FenceKit","TerritoryFlagKit","WatchtowerKit"]`

Item types — **including inherited types** — that cannot be built in
underground areas. The three defaults are the tools for claiming and sealing
space, keeping the bunker a contested POI rather than real estate.

- **"Underground" is defined elsewhere**, in `cfgundergroundtriggers.json`.
  This list and that file are a pair.
- **It survives build-anywhere.** It is not a `disable*` flag, so setting all
  fourteen booleans `true` does not touch it.
- **Object spawners bypass it** — it gates player building only. A permanent
  fence or flag underground is possible via `objectSpawnersArr`.

### ConstructionData — **[source]**

All default `false`. **Two of the three are much narrower than the wiki implies.**

| Key | Reality |
|---|---|
| `disableIsCollidingCheck` | **Real.** Gates `IsColliding()` and `IsCollidingEx()` in `scripts/4_world/classes/basebuilding/construction.c`. |
| `disablePerformRoofCheck` | **Watchtowers only.** `PerformRoofCheckForBase` is overridden solely in `watchtower.c`, and only for parts `level_1_base`, `level_2_base`, `level_3_base`, `level_3_roof`. |
| `disableDistanceCheck` | **Dead config.** Its only consumer, `miscgameplayfunctions.c:904`, sits inside a `/* */` commented-out block. Setting it does nothing. |

Setting a dead flag costs nothing, so existing configs need no change — but do
not describe all three as equally load-bearing.

## UIData

### `use3DMap` — bool, `false`

`true` forces the 3D map and disables the 2D overlay.

**In both modes your character physically holds a map and is vulnerable.** The
difference is presentation: the 2D overlay is full-screen with scroll and zoom,
so it is far easier to read but blinds you; the 3D map is harder to read
because it is not full-screen, but you keep looking around. **If anything, 3D
leaves you less exposed** — the opposite of the intuitive reading.

### UIData.HitIndicationData

The directional damage indicator. **Vanilla on both servers, and dormant.**

| Key | Default | Effect |
|---|---|---|
| `hitDirectionOverrideEnabled` | `false` | **The gate. Nothing else in this block applies until it is `true`.** Undefined members of a data class read as zero, so Bohemia needed a flag to tell "set to 0" from "never loaded." The seven values below are inert in a file that leaves this `false`. |
| `hitDirectionBehaviour` | `1` | `0` = disabled, `1` = static, `2` = dynamic (moves while displayed, WIP). |
| `hitDirectionStyle` | `0` | `0` = splash, `1` = spike, `2` = arrow. |
| `hitDirectionIndicatorColorStr` | `"0xffbb0a1e"` | ARGB as a **string**: `0x` + AA RR GG BB, case-insensitive. JSON has no hex literal. |
| `hitDirectionMaxDuration` | `2.0` | Max display time; actual is 0.6–1.0× this, scaled by hit severity, so heavier hits linger. |
| `hitDirectionBreakPointRelative` | `0.2` | Fraction of duration before fade begins. `0.0` fades from the start, `1.0` never fades. |
| `hitDirectionScatter` | `10.0` | **Deliberate inaccuracy** — randomized ±10° for a 20° spread, so you learn roughly where the shot came from without snapping onto the shooter. A balance decision, not a rendering artifact. |
| `hitIndicationPostProcessEnabled` | `true` | `false` removes the legacy red screen flash while keeping the directional marker. |

PvP levers: `hitDirectionBehaviour: 0` removes directional feedback entirely and
is a large sniper buff; raising `hitDirectionScatter` weakens it gradually.

## MapData

| Key | Default | Effect |
|---|---|---|
| `ignoreMapOwnership` | `false` | `true` lets players open the map with `M` without carrying one. |
| `ignoreNavItemsOwnership` | `false` | `true` shows compass and GPS helpers without carrying those items. |
| `displayPlayerPosition` | `false` | `true` shows the player's position and facing as a red marker. |
| `displayNavInfo` | `true` | `true` **shows** the map's upper legend; `false` hides it. |

Together the first three turn navigation into a minimap. That is the dial
between hardcore (One Life: all vanilla) and coordinated PvP (Clan Wars: all
three `true`).

**`displayNavInfo`: the wiki description is inverted.** It reads "hide GPS and
Compass UI from the map legend completely," describing the `false` behavior
while documenting the default as `true`. The name is correct.

**[source]** `scripts/5_mission/gui/mapmenu.c:141`:

```
//! override the CfgGameplayHandler.GetMapIgnoreNavItemsOwnership()
if ((!m_HasGPS && !m_HasCompass) || !CfgGameplayHandler.GetMapDisplayNavigationInfo())
    SetUpperLegendVisibility(false);
```

**`displayNavInfo` overrides `ignoreNavItemsOwnership`.** Set ownership bypass
`true` but `displayNavInfo` `false` and the legend stays hidden anyway — the
bypass is silently defeated. The two keys are not independent;
`displayNavInfo` is the master switch.

## VehicleData

### `boatDecayMultiplier` — float, `1`

Multiplies boat decay rate.

**Boats are the only vehicle with a decay multiplier because they are the only
vehicle that despawns on its own.** Boat engines decay naturally and the boat
eventually despawns. **Cars never despawn unless a player destroys them.**
Raising this clears abandoned boats faster — most relevant on Sakhal, where
boats are primary transport.

---

## Verifying a default

```sh
gh api "repos/BohemiaInteractive/DayZ-Central-Economy/contents/dayzOffline.<map>/cfggameplay.json?ref=master" \
  --jq '.content' | base64 -d
```

`<map>` is `chernarusplus`, `enoch` or `sakhal`. Live Xbox servers track
`master`, not a tagged release.

## Resolving a key's real behavior

When the wiki is vague, ambiguous, or contradicts itself, read the engine.

```sh
gh api -X GET search/code -f q='GetDisableSomeCheck repo:BohemiaInteractive/DayZ-Script-Diff' \
  --jq '.items[]? | .path'
gh api "repos/BohemiaInteractive/DayZ-Script-Diff/contents/<path>" --jq '.content' | base64 -d
```

Config flags are read through `CfgGameplayHandler` accessors in
`scripts/3_game/cfggameplayhandler.c`; searching for the accessor name finds
every consumer. This is how `disableDistanceCheck` was found to be dead and
`disableIsPlacementPermittedCheck` was found to have nothing to do with
territory. **Prefer it over the wiki for any behavioral claim.**
