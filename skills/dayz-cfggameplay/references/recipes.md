# cfggameplay.json — task recipes

Each recipe: the goal, the exact JSON, the side effects, and how to verify.
Key names and defaults come from `keys.md` — check the map-specific spellings
there before pasting.

**Prerequisite for every recipe:** `enableCfgGameplayFile = 1;` in `server.cfg`.
Without it none of this is read.

---

## Build anywhere

Turn off every placement and construction restriction.

```json
"BaseBuildingData": {
    "HologramData": {
        "disableIsCollidingBBoxCheck": true,
        "disableIsCollidingPlayerCheck": true,
        "disableIsClippingRoofCheck": true,
        "disableIsBaseViableCheck": true,
        "disableIsCollidingGPlotCheck": true,
        "disableIsCollidingAngleCheck": true,
        "disableIsPlacementPermittedCheck": true,
        "disableHeightPlacementCheck": true,
        "disableIsUnderwaterCheck": true,
        "disableIsInTerrainCheck": true,
        "disableColdAreaBuildingCheck": true,
        "disallowedTypesInUnderground": ["FenceKit", "TerritoryFlagKit", "WatchtowerKit"]
    },
    "ConstructionData": {
        "disablePerformRoofCheck": true,
        "disableIsCollidingCheck": true,
        "disableDistanceCheck": true
    }
}
```

**On Sakhal, rename the cold-area key** to `disableColdAreaPlacementCheck`.
Keeping the Chernarus spelling on Sakhal means the frozen-ground check stays on
and nothing tells you.

**Side effects:**

- `disableIsPlacementPermittedCheck: true` also **disables territory permission
  enforcement** — anyone can build inside anyone's territory. If you want
  build-anywhere *and* territory protection, leave this one `false`.
- `disallowedTypesInUnderground` still applies. Underground restrictions are not
  part of the placement checks and survive build-anywhere.
- Players will build inside rocks, under terrain and underwater. That is the
  point, but it makes some structures unraidable and hard to remove.

**Verify:** place a fence kit clipping a wall in game after restart. To confirm
the file was read at all, flip something visible first — `MapData.displayPlayerPosition` shows up instantly.

---

## Stamina

Modifiers multiply consumption. `0` = free, `1.0` = vanilla, `2.0` = double drain.

### Unlimited stamina

```json
"StaminaData": {
    "sprintStaminaModifierErc": 0,
    "sprintStaminaModifierCro": 0,
    "staminaWeightLimitThreshold": 6000.0,
    "staminaMax": 100.0,
    "staminaKgToStaminaPercentPenalty": 0,
    "staminaMinCap": 100.0,
    "sprintSwimmingStaminaModifier": 0,
    "sprintLadderStaminaModifier": 0,
    "meleeStaminaModifier": 0,
    "obstacleTraversalStaminaModifier": 1.0,
    "holdBreathStaminaModifier": 1.0
}
```

Nests under `PlayerData`. This is Clan Wars' live configuration.

Two keys do the load work and are easy to miss: `staminaKgToStaminaPercentPenalty: 0`
removes the weight-to-stamina conversion, and `staminaMinCap: 100.0` raises the
floor so load cannot push the cap down. Zeroing only the sprint modifiers leaves
a heavily loaded player still capped.

`obstacleTraversalStaminaModifier` and `holdBreathStaminaModifier` stay at `1.0`
here deliberately — climbing and scope-steadying keep costing stamina. Zero them
too if you want those free.

**Never set `staminaMax` or `staminaMinCap` to `0`** — Bohemia documents that as
producing unexpected results. Use `100.0`.

### Vanilla-but-forgiving

Halve the drain instead of removing it: set the four sprint/swim/ladder/melee
modifiers to `0.5` and leave the rest alone.

**Verify:** sprint a long distance fully loaded after restart.

---

## Spawn gear

```json
"PlayerData": {
    "spawnGearPresetFiles": ["./custom/loadout.json"],
    ...
}
```

The key ships in **no** vanilla file — you add it. Absent or `[]` means vanilla
spawn gear.

Preset file shape (Clan Wars' `custom/loadout.json`):

```json
{
    "spawnWeight": 1,
    "name": "loadout",
    "characterTypes": [],
    "attachmentSlotItemSets": [
        {
            "slotName": "Hands",
            "discreteItemSets": [
                {
                    "itemType": "Glock19",
                    "spawnWeight": 1,
                    "attributes": { "healthMin": 1.0, "healthMax": 1.0, "quantityMin": 1.0, "quantityMax": 1.0 },
                    "quickBarSlot": 3,
                    "simpleChildrenTypes": ["Mag_Glock_15Rnd"],
                    "simpleChildrenUseDefaultAttributes": false,
                    "complexChildrenTypes": []
                }
            ]
        }
    ]
}
```

`quickBarSlot: -1` means unassigned. Empty `characterTypes` applies the preset
to all characters.

**Alternative:** One Life sets fresh-spawn gear in `init.c` via
`StartingEquipSetup` and has no `spawnGearPresetFiles` key at all. On a One Life
server, edit `init.c` — don't introduce the key.

**Verify:** the referenced path must exist relative to the mission root, or the
server fails at boot. Run `scripts/validate.py`.

---

## Object spawners

Place static map objects at mission start.

```json
"WorldsData": {
    "objectSpawnersArr": [
        "./custom/admin-castle.json",
        "./custom/teleports.json"
    ],
    ...
}
```

Spawner file shape:

```json
{
    "Objects": [
        {
            "name": "SledgeHammer",
            "pos": [104.141, 998.621, 89.963],
            "ypr": [90.0, 0.0, -0.0],
            "scale": 1.0,
            "enableCEPersistency": 0,
            "customString": ""
        }
    ]
}
```

- `name` is either a class name (`Land_Wall_Gate_FenR`) or a p3d model path
  (`DZ/plants/tree/t_BetulaPendula_1fb.p3d`).
- p3d spawning is limited to `DZ/plants`, `DZ/plants_bliss`, `DZ/plants_sakhal`,
  `DZ/rocks`, `DZ/rocks_bliss`, `DZ/rocks_sakhal`. Anything else silently fails.
- `enableCEPersistency: 0` spawns without persistence; persistence turns on once
  a player takes the item.
- `customString` is handled by overriding `OnSpawnByObjectSpawner` on the item's
  script class (`StaticFlagPole` is Bohemia's worked example).

**A file in `custom/` that no array references spawns nothing.** Clan Wars has
three such orphans. Adding the file is half the job; listing it is the other half.

**Verify:** a bad class name or model path logs `Object spawner failed to spawn`
in the server RPT. Grep the RPT after restart — the server boots fine either way.

Heavy object counts cost both server and client performance.

---

## Restricted areas

```json
"WorldsData": {
    "playerRestrictedAreaFiles": ["./custom/pra-teleport-castle.json"],
    ...
}
```

Not shipped except on Sakhal (`["pra/warheadstorage.json"]`). Both `./custom/x.json`
and `pra/x.json` path styles work.

PRA file shape:

```json
{
    "areaName": "RestrictedAreaWarheadStorage",
    "PRABoxes": [
        [
            [27, 5.2, 11],
            [108, 0, 0],
            [2570, 15.22, 5963.8]
        ]
    ],
    "safePositions3D": [
        [2575.12, 15.25, 5954.31],
        [2577.76, 15.25, 5957.70]
    ]
}
```

Each `PRABoxes` entry is three vectors: **size** `[x, y, z]`, **orientation**
`[yaw, pitch, roll]`, **center position** `[x, y, z]`. A player entering the box
is moved to one of `safePositions3D`.

### PRAs as teleporters

Clan Wars exploits the eject behavior: a small trigger box with a **distant**
`safePositions3D` becomes a one-way teleporter.

```json
{
    "areaName": "TeleportToCastle",
    "PRABoxes": [
        [
            [2, 1.5, 2],
            [90, 0, 0],
            [12234.06, 293.85, 90.87]
        ]
    ],
    "safePositions3D": [
        [12742.34, 331.26, 59.52]
    ]
}
```

One file per destination, named `pra-teleport-<place>.json`, each listed in
`playerRestrictedAreaFiles`. Pair it with an object spawner placing something
visible on the pad so players know where the trigger is.

Keep the box small (2×1.5×2) or players get yanked while walking past.

**Verify:** walk into the box after restart. Missing files fail at boot.

---

## Temperatures

```json
"environmentMinTemps": [-7, -7.4, -4.1, 1.5, 7, 11.3, 20.4, 19.1, 18, 5.3, 0.8, -3.6],
"environmentMaxTemps": [-2.5, -2.1, 2.3, 9, 15.5, 19.4, 25, 22, 21, 10.5, 4.2, 0.1]
```

Under `WorldsData`. **Exactly 12 values each**, January→December. A wrong-length
array is a silent misread.

**Before changing these, check `keys.md` for your map's vanilla curve.** Livonia
and Sakhal ship colder curves than Chernarus. A Livonia server whose temps
differ from Chernarus's is at *its own vanilla*, not modified — "normalizing" it
to Chernarus values is a real gameplay change disguised as a cleanup.

To make winter harsher, shift the whole min array down a few degrees and leave
max alone; that widens the daily swing without making summer unplayable.

**Verify:** temperatures shift with the in-game month, so this is slow to
observe. Diff the file rather than waiting for the season.

---

## Map QoL

```json
"MapData": {
    "ignoreMapOwnership": true,
    "ignoreNavItemsOwnership": true,
    "displayPlayerPosition": true,
    "displayNavInfo": true
}
```

Clan Wars' configuration: map opens with `M` without carrying one, compass/GPS
helpers work without the items, and the player sees their own position and
facing. This is the fastest smoke test that the file is being read at all — it
is visible the moment a player opens the map after restart.

For a hardcore server leave all three `false` (vanilla) and make navigation
an actual skill.

---

## Reverting

Do not hand-revert. Pull your map's vanilla file and re-apply only what you mean
to keep:

```sh
gh api "repos/BohemiaInteractive/DayZ-Central-Economy/contents/dayzOffline.<map>/cfggameplay.json?ref=master" \
  --jq '.content' | base64 -d > cfggameplay.json
```

`<map>` is `chernarusplus`, `enoch` or `sakhal`. Live Xbox servers track
`master`, not a tagged release.

On One Life servers the only intentional deviation is the `BaseBuildingData`
block — re-apply that and you are done. Anything else that differs after this
was upstream drift, not a setting you chose.

To see what you actually changed:

```sh
python3 - <<'EOF'
import json
def flat(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items(): yield from flat(v, p + '.' + k)
    else: yield (p, json.dumps(o))
van = dict(flat(json.load(open('vanilla.json'))))
cur = dict(flat(json.load(open('cfggameplay.json'))))
for k in sorted(set(van) | set(cur)):
    a, b = van.get(k, '<absent>'), cur.get(k, '<absent>')
    if a != b:
        print(f'{k}\n  vanilla: {a}\n  yours  : {b}')
EOF
```

Diff against the **matching map**. Diffing Livonia against Chernarus reports the
temperature curves and produces a false positive every time.
