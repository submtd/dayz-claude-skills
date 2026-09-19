# cfggameplay.json — complete key reference

Schema `"version": 123`. Defaults verified against
`BohemiaInteractive/DayZ-Central-Economy@master` (`dayzOffline.chernarusplus`,
`dayzOffline.enoch`, `dayzOffline.sakhal`) and the Bohemia wiki,
[DayZ:Gameplay Settings](https://community.bistudio.com/wiki/DayZ:Gameplay_Settings).

Where the wiki and the shipped file disagree, **the shipped file wins** and the
discrepancy is flagged. The wiki lists parameters as a flat table and does not
show the nesting; the tree below is the nesting the engine actually reads.

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
| `version` | int | `123` | File format version the engine checks. Copy it from your map's vanilla upstream file for the current build; do not invent or carry one over from an old backup. **Unverified:** what the engine does with a wrong value — ignore the file, partially misparse it, or nothing — is not documented and has not been tested here. Do not state a consequence you cannot cite; say the behavior is unknown and match upstream. |

## GeneralData

| Key | Type | Default | Effect |
|---|---|---|---|
| `disableBaseDamage` | bool | `false` | `true` makes player-built base structures immune to damage. Clan Wars toggles this per raid window. |
| `disableContainerDamage` | bool | `false` | `true` makes tents, barrels and similar containers immune to damage. |
| `disableRespawnDialog` | bool | `false` | `true` removes the dialog asking which respawn type the player wants after pressing respawn. |
| `disableRespawnInUnconsciousness` | bool | `false` | `true` removes the Esc-menu Respawn button while unconscious, so a downed player cannot suicide out of a fight. |

## PlayerData

| Key | Type | Default | Effect |
|---|---|---|---|
| `spawnGearPresetFiles` | string[] | not present | Paths to Player Gear Spawn JSON files. Non-empty enables custom fresh-spawn loadouts. Absent or `[]` = vanilla spawn gear. |
| `disablePersonalLight` | bool | `false` | `true` removes the ambient light that follows the player at night, making nights genuinely dark. |

### PlayerData.StaminaData

Modifiers are multipliers on consumption rate — `0` means that activity costs
no stamina, `1.0` is vanilla, `2.0` is double drain.

| Key | Type | Default | Effect |
|---|---|---|---|
| `sprintStaminaModifierErc` | float | `1.0` | Drain rate while sprinting upright. |
| `sprintStaminaModifierCro` | float | `1.0` | Drain rate while sprinting crouched. |
| `staminaWeightLimitThreshold` | float | `6000.0` | Stamina points (÷1000) exempt from the carried-weight deduction. |
| `staminaMax` | float | `100.0` | Maximum stamina. **`0` produces unexpected results** (Bohemia's wording). |
| `staminaKgToStaminaPercentPenalty` | float | `1.75` | Multiplier converting carried load into max-stamina reduction. `0` removes the weight penalty entirely. |
| `staminaMinCap` | float | `5.0` | Floor the max-stamina cap can be pushed down to by load. Set to `100.0` to make load irrelevant. **`0` produces unexpected results.** |
| `sprintSwimmingStaminaModifier` | float | `1.0` | Drain rate while fast-swimming. |
| `sprintLadderStaminaModifier` | float | `1.0` | Drain rate while fast-climbing ladders. |
| `meleeStaminaModifier` | float | `1.0` | Cost of heavy melee attacks and evasion. |
| `obstacleTraversalStaminaModifier` | float | `1.0` | Cost of jumping, climbing and vaulting. |
| `holdBreathStaminaModifier` | float | `1.0` | Drain rate while holding breath to steady a scope. |

### PlayerData.ShockHandlingData

| Key | Type | Default | Effect |
|---|---|---|---|
| `shockRefillSpeedConscious` | float | `5.0` | Shock recovered per second while conscious. |
| `shockRefillSpeedUnconscious` | float | `1.0` | Shock recovered per second while unconscious. Raising it shortens knockouts — Clan Wars uses `5.0`, matching the conscious rate. |
| `allowRefillSpeedModifier` | bool | `true` | Lets ammo-type settings modify shock recovery (typically faster wake-up after being shot). |

### PlayerData.MovementData

Inertia. Minimum accepted value for each float is `0.01`.

| Key | Type | Default | Effect |
|---|---|---|---|
| `timeToStrafeJog` | float | `0.1` | Blend time for diagonal movement while jogging. |
| `rotationSpeedJog` | float | `0.3` | Turn rate while jogging. **Wiki says `0.15`; every shipped file says `0.3`.** |
| `timeToSprint` | float | `0.45` | Time to accelerate from jog to sprint. |
| `timeToStrafeSprint` | float | `0.3` | Blend time for diagonal movement while sprinting. |
| `rotationSpeedSprint` | float | `0.15` | Turn rate while sprinting. |
| `allowStaminaAffectInertia` | bool | `true` | Lets current stamina influence inertia. |

### PlayerData.DrowningData

| Key | Type | Default | Effect |
|---|---|---|---|
| `staminaDepletionSpeed` | float | `10.0` | Stamina lost per second while drowning. |
| `healthDepletionSpeed` | float | `10.0` | Health lost per second while drowning. |
| `shockDepletionSpeed` | float | `10.0` | Shock lost per second while drowning. |

### PlayerData.WeaponObstructionData

Both take `0` = off (never obstruct), `1` = on (obstruct then lift),
`2` = always (obstruct, don't lift).

| Key | Type | Default | Effect |
|---|---|---|---|
| `staticMode` | int | `1` | Weapon obstruction against static world geometry. |
| `dynamicMode` | int | `1` | Weapon obstruction against dynamic entities. |

## WorldsData

| Key | Type | Default | Effect |
|---|---|---|---|
| `lightingConfig` | int | `0` (Chernarus, Livonia) / `2` (Sakhal) | Night lighting. `0` = bright, `1` = dark. **Wiki claims default `1`; every shipped file says `0` except Sakhal's `2`.** **`2` is undocumented** — the wiki describes only `0` and `1`, and what `2` renders is unknown. It ships as Sakhal's vanilla value; treat it as map-specific, leave it alone, and don't guess at its meaning or copy it to another map. |
| `objectSpawnersArr` | string[] | `[]` | Object Spawner JSON files, loaded at mission start. See `recipes.md`. |
| `environmentMinTemps` | float[12] | per map, below | Monthly minimum ambient temperature, January→December. Exactly 12 values. |
| `environmentMaxTemps` | float[12] | per map, below | Monthly maximum ambient temperature, January→December. Exactly 12 values. |
| `wetnessWeightModifiers` | float[5] | `[1.0, 1.0, 1.33, 1.66, 2.0]` | Item weight multiplier by wetness: DRY, DAMP, WET, SOAKED, DRENCHED. |
| `playerRestrictedAreaFiles` | string[] | not present (Sakhal: `["pra/warheadstorage.json"]`) | Player Restricted Area JSON files. See `recipes.md`. |

### Vanilla temperature curves by map

| Map | `environmentMinTemps` | `environmentMaxTemps` |
|---|---|---|
| Chernarus | `[-3, -2, 0, 4, 9, 14, 18, 17, 13, 11, 9, 0]` | `[3, 5, 7, 14, 19, 24, 26, 25, 18, 14, 10, 5]` |
| Livonia (enoch) | `[-7, -7.4, -4.1, 1.5, 7, 11.3, 20.4, 19.1, 18, 5.3, 0.8, -3.6]` | `[-2.5, -2.1, 2.3, 9, 15.5, 19.4, 25, 22, 21, 10.5, 4.2, 0.1]` |
| Sakhal | `[-6.5, -9.5, -6.5, -9.5, 2, 6, 9, 10, 6, 1, -5, -10]` | `[-3, -5, -3, -5, 9, 14, 16, 17, 14, 8, 1, -3]` |

The wiki's stated defaults (`[-3,-2,0,4,9,14,18,17,12,7,4,0]` /
`[3,5,7,14,19,24,26,25,21,16,10,5]`) match **no** shipped file. Use the table above.

A Livonia or Sakhal server showing "different" temps from Chernarus is at its
own vanilla, not modified. Diff against the matching map.

## BaseBuildingData.HologramData

Placement (ghost/preview) checks. Every key is a **disable** flag: `true` turns
the check off and permits the placement. All default `false`.

| Key | Effect when `true` |
|---|---|
| `disableIsCollidingBBoxCheck` | Allows placement colliding with world objects. |
| `disableIsCollidingPlayerCheck` | Allows placement colliding with a player. |
| `disableIsClippingRoofCheck` | Allows placement that clips a roof. |
| `disableIsBaseViableCheck` | Allows placement on dynamic objects and otherwise incompatible bases. |
| `disableIsCollidingGPlotCheck` | Allows garden plots on incompatible surfaces. |
| `disableIsCollidingAngleCheck` | Allows placement beyond roll/pitch/yaw limits. |
| `disableIsPlacementPermittedCheck` | Allows placement where not permitted. **This is what disables territory permission enforcement.** |
| `disableHeightPlacementCheck` | Allows placement with limited height clearance. |
| `disableIsUnderwaterCheck` | Allows underwater placement. |
| `disableIsInTerrainCheck` | Allows placement clipping into terrain. |
| `disableColdAreaBuildingCheck` | Allows garden plots on frozen ground. **Chernarus and Livonia spelling.** |
| `disableColdAreaPlacementCheck` | Same effect. **Sakhal spelling — the only one the wiki documents.** |

| Key | Type | Default | Effect |
|---|---|---|---|
| `disallowedTypesInUnderground` | string[] | `["FenceKit","TerritoryFlagKit","WatchtowerKit"]` | Item types (and inherited types) that cannot be built in underground areas. |

## BaseBuildingData.ConstructionData

Construction (actual build action) checks. All default `false`.

| Key | Effect when `true` |
|---|---|
| `disablePerformRoofCheck` | Allows construction clipping a roof. |
| `disableIsCollidingCheck` | Allows construction colliding with world objects. |
| `disableDistanceCheck` | Turns off the player-distance check on construction. (The wiki's phrasing, "prevents construction when player gets below specified range," describes the check, not the flag.) |

## UIData

| Key | Type | Default | Effect |
|---|---|---|---|
| `use3DMap` | bool | `false` | `true` forces the 3D map and disables the 2D map overlay. |

### UIData.HitIndicationData

| Key | Type | Default | Effect |
|---|---|---|---|
| `hitDirectionOverrideEnabled` | bool | `false` | Must be `true` for any other value in this block to be used. Undefined members of a data class read as zero, so this flag is how the engine distinguishes a loaded block from an absent one. |
| `hitDirectionBehaviour` | int | `1` | `0` = disabled, `1` = static, `2` = dynamic (moves while displayed, WIP). |
| `hitDirectionStyle` | int | `0` | `0` = splash, `1` = spike, `2` = arrow. |
| `hitDirectionIndicatorColorStr` | string | `"0xffbb0a1e"` | Indicator color, ARGB as a **string**: `0x` + AA + RR + GG + BB, case-insensitive. JSON has no hex literal, hence the string. |
| `hitDirectionMaxDuration` | float | `2.0` | Max display time. Actual is 0.6–1.0× this, scaled by hit severity. |
| `hitDirectionBreakPointRelative` | float | `0.2` | Fraction of duration before fade begins. `0.0` fades from the start, `1.0` never fades. |
| `hitDirectionScatter` | float | `10.0` | Randomized angular inaccuracy in degrees, applied ±, so `10.0` gives a 20° spread. |
| `hitIndicationPostProcessEnabled` | bool | `true` | `false` removes the legacy red-flash hit effect. |

## MapData

| Key | Type | Default | Effect |
|---|---|---|---|
| `ignoreMapOwnership` | bool | `false` | `true` lets players open the map with `M` without carrying one. |
| `ignoreNavItemsOwnership` | bool | `false` | `true` shows compass and GPS helpers on the map without carrying those items. |
| `displayPlayerPosition` | bool | `false` | `true` shows the player's position and facing as a red marker. |
| `displayNavInfo` | bool | `true` | Controls the GPS/compass legend on the map. |

## VehicleData

| Key | Type | Default | Effect |
|---|---|---|---|
| `boatDecayMultiplier` | float | `1` | Multiplies boat decay rate. |

---

## Verifying a default

```sh
gh api "repos/BohemiaInteractive/DayZ-Central-Economy/contents/dayzOffline.<map>/cfggameplay.json?ref=master" \
  --jq '.content' | base64 -d
```

`<map>` is `chernarusplus`, `enoch` or `sakhal`. Live Xbox servers track
`master`, not a tagged release — diff against `master`.
