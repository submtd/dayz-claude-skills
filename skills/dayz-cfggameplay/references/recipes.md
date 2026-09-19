# cfggameplay.json — task recipes

Each recipe: the goal, the exact JSON, the side effects, and how to verify.
Key names and defaults come from `keys.md` — check the map-specific spellings
there before pasting.

**Prerequisite for every recipe:** `enableCfgGameplayFile = 1;` in `server.cfg`.
Without it none of this is read.

**Console has no mods.** These servers are Xbox, so this file plus the mission
tree is the whole toolbox. "Use a mod" is never the answer.

---

## Build anywhere

Turn off the placement and construction restrictions.

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

**You need both blocks.** `HologramData` gates the placement preview,
`ConstructionData` gates the build action. Disabling one half gives you a ghost
that turns green but a build that fails, or the reverse.

**Which of these actually carry weight** (see `keys.md` for the source reads):

- `disableIsCollidingBBoxCheck` and `disableIsCollidingCheck` do the real work.
- `disableIsClippingRoofCheck` and `disableIsBaseViableCheck` affect only the
  **client preview** — the server already skips both in multiplayer.
- `disableIsPlacementPermittedCheck` does **nothing for walls, gates, fences or
  watchtowers**. It only affects tents, fireplaces, garden plots and traps.
- `disablePerformRoofCheck` affects **watchtowers only**.
- `disableDistanceCheck` is **dead config** — its only consumer is commented
  out in Bohemia's source.

Harmless to set them all; just don't believe all fourteen are load-bearing.

**Side effects:**

- **No territory downside.** Vanilla DayZ has no territory build-permission
  system, so nothing here weakens base ownership.
- `disallowedTypesInUnderground` still applies — underground restrictions
  survive build-anywhere entirely.
- Three checks can never be disabled: floating, hidden, and placement at world
  origin.
- Players will build inside rocks, under terrain and underwater. That is the
  point, but it makes some structures hard to raid and hard to remove.

**Verify:** place a fence kit clipping a wall in game after restart. To confirm
the file is being read at all, flip `MapData.displayPlayerPosition` first — it
shows up the moment a player opens the map.

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

**The two load keys are what people miss.** `staminaKgToStaminaPercentPenalty: 0`
removes the weight-to-stamina conversion, and `staminaMinCap: 100.0` raises the
floor so load cannot push the cap down. `staminaMinCap` is a **percentage** —
vanilla `5.0` means a fully loaded player gets 5% of an unloaded player's
stamina. Zeroing only the sprint modifiers leaves a heavily loaded player capped.

**Tune `staminaMinCap`, never `staminaMax`.** Operators do not move the max.
Neither should be set to `0` — Bohemia documents that as producing unexpected
results. Use `100.0`.

**What stays costly here, deliberately:** `obstacleTraversalStaminaModifier`
(vaulting walls) and `holdBreathStaminaModifier` (steadying a scope) are left
at `1.0`. Note that **ladders are a different key** —
`sprintLadderStaminaModifier` is at `0`, so ladders are free.

**Think before zeroing hold-breath.** It is believed — not confirmed — to give
an infinite breath hold, which is a real sniping advantage rather than a
quality-of-life tweak.

**Knock-on effects of `staminaKgToStaminaPercentPenalty: 0`:** it silently
disables everything downstream of weight. `staminaWeightLimitThreshold`,
`staminaMinCap`'s relevance, and `wetnessWeightModifiers` all stop mattering.
Do not later "fix" one of those and expect a result.

### Vanilla-but-forgiving

Halve the drain instead of removing it: set the sprint/swim/ladder/melee
modifiers to `0.5` and leave the load system alone.

**Verify:** sprint a long distance fully loaded after restart.

---

## Raid windows

Closing raiding for a period takes **both** damage flags:

```json
"GeneralData": {
    "disableBaseDamage": true,
    "disableContainerDamage": true
}
```

`disableBaseDamage` alone closes explosives, gunfire and fists against base
parts. Operators set `disableContainerDamage` with it so tents and barrels
cannot be chipped at either. The two cover cleanly separate object sets — the
pairing is for completeness, not because of overlap.

**Bases still decay** on their `db/types.xml` lifetime. `true` means
un-raidable, not permanent.

**Vehicles never damage bases**, with or without these flags.

**Think before leaving `disableContainerDamage: true` permanently.** A tent
misplaced into geometry can only be removed by destroying it. Permanent
container immunity means permanent map clutter.

Clan Wars drives this on a schedule from its bot, splicing the boolean rather
than rewriting the file — see "Editing safely" in `SKILL.md`.

---

## Spawn gear

```json
"PlayerData": {
    "spawnGearPresetFiles": ["./custom/loadout.json"],
    ...
}
```

The key ships in **no** vanilla file — you add it. Absent or `[]` means vanilla
spawn gear. **Multiple files mean random selection between presets**, not
merged loadouts.

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

- **`spawnWeight` is an integer, minimum 1, and appears at every level** —
  preset, per-slot variant, and cargo set. Higher is more likely. With one
  preset and one option per slot, every `spawnWeight` in the file is inert.
  Three shirts at weight 1 = 33% each; bump one to 10 and it dominates.
- `quickBarSlot: -1` means unassigned.
- `characterTypes: []` leaves the player the character type they last chose in
  the creation menu. Populating it takes that choice away.
- `discreteUnsortedItemSets` is the sibling field for cargo rather than
  attachment slots.

**On PC this overrides `StartingEquipSetup()` in `init.c`** — adding the key
to a server that sets gear there silently disables that code.

**On Nitrado/Xbox there is nothing to override: `init.c` is inert.** Nitrado
loads its own, so `spawnGearPresetFiles` is the **only** way to customise
fresh-spawn gear. That is why Clan Wars uses it and why One Life, which does
not, gets vanilla gear regardless of the `StartingEquipSetup` sitting in its
`init.c`.

It also **completely overrides character spawning**, including the character
built in the main menu.

**Verify:** run `scripts/validate.py`. A missing or malformed preset file does
**not** fail the boot — it logs via `ErrorEx` and **disables every preset**
(`cfgplayerspawnhandler.c:22` returns false for the whole set), so players
quietly get vanilla gear instead.

---

## Object spawners

Place static map objects at mission start. On console this is the only way to
build custom POIs.

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

- `name` is either a class name (`Land_Wall_Gate_FenR`) or a p3d model path.
- p3d spawning is limited to `DZ/plants`, `DZ/plants_bliss`, `DZ/plants_sakhal`,
  `DZ/rocks`, `DZ/rocks_bliss`, `DZ/rocks_sakhal`. Anything else silently fails.
- `customString` is handled by overriding `OnSpawnByObjectSpawner` on the
  item's script class (`StaticFlagPole` is Bohemia's worked example).

**Two properties that make this powerful:**

1. **Spawned objects do not count against central economy limits.** This is an
   economy bypass — guaranteed placement that never competes with `types.xml`
   nominals or CE cleanup. It is why a spawner-based supply drop is reliable
   where a `types.xml` approach is at the mercy of the economy settling.
2. **Objects respawn on every restart.** Take the item and a fresh one appears
   next restart. Effectively infinite supply.

**[unverified]** `enableCEPersistency: 0` is read as "not persisted, re-created
each restart, becomes a normal CE-tracked item once a player takes it," and `1`
as "persisted from the start, does not respawn." Use `1` if you ever want a
spawner-placed object that does *not* duplicate itself.

**Object spawners bypass `disallowedTypesInUnderground`** — that list gates
player building only. A permanent fence or flag underground is possible here.

**A file in `custom/` that no array references spawns nothing.** Clan Wars has
three such orphans. Adding the file is half the job; listing it is the other
half. `validate.py` reports them.

**Verify:** a bad class name or model path logs `Object spawner failed to spawn`
in the server RPT. Grep the RPT after restart — the server boots fine either
way. High object counts cost server and client performance.

---

## Fast travel (player restricted areas)

```json
"WorldsData": {
    "playerRestrictedAreaFiles": ["./custom/pra-teleport-castle.json"],
    ...
}
```

Not shipped except on Sakhal (`["pra/warheadstorage.json"]`). Both
`./custom/x.json` and `pra/x.json` path styles work.

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
`[yaw, pitch, roll]`, **center position** `[x, y, z]`.

### ⚠ The trigger is login, not entry

**A player who logs in inside a PRA box is moved to one of the file's
`safePositions3D`. Walking into the box while already logged in does nothing
at all** — no ejection, no message, no warning.

That is the whole mechanic. A PRA does not damage, kill, or block building. It
moves players at login and nothing else. Bohemia's Sakhal use is stopping
players from logging in inside the warhead storage area.

### Using it as fast travel

Operators call this **fast travel**. It is known but not widely used. A small
trigger box with a **distant** `safePositions3D` becomes a destination pad: the
player stands on it, logs out, logs back in, and arrives.

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
`playerRestrictedAreaFiles`. Clan Wars runs 33.

- **The logout/login cycle is the friction, and it is a feature** — nobody
  chain-teleports out of a firefight.
- A box may list multiple targets; the player is moved to one of them.
- **No performance cost at this scale.** The check runs at login, not
  continuously, so 33 areas are free. Clan Wars has seen no reliability issues.
- Pair each pad with an object spawner placing something visible on it, so
  players know where to stand. Clan Wars uses `teleports.json` for this.
- Keep boxes small (2 × 1.5 × 2). Players only need to be standing there at
  the moment of login.

**Verify:** stand in the box, log out, log back in.

A missing or malformed PRA file does **not** fail the boot — it logs via
`ErrorEx` and that area silently does not exist. Paths resolve as
`$mission:<file>` first, then `dz/worlds/<world>/ce/<file>`. Run
`scripts/validate.py` rather than trusting a clean startup.

---

## Temperatures

```json
"environmentMinTemps": [-7, -7.4, -4.1, 1.5, 7, 11.3, 20.4, 19.1, 18, 5.3, 0.8, -3.6],
"environmentMaxTemps": [-2.5, -2.1, 2.3, 9, 15.5, 19.4, 25, 22, 21, 10.5, 4.2, 0.1]
```

Under `WorldsData`. **Exactly 12 values each**, January→December. A wrong-length
array is a silent misread.

**The curve advances with the in-game month**, so `serverTimeAcceleration` in
`serverDZ.cfg` decides how often players actually see winter. An accelerated
server cycles through the cold months regularly; a slow one may sit in summer
for weeks. Check that setting before concluding these values do or don't matter.

**Check `keys.md` for your map's vanilla curve first.** Livonia and Sakhal ship
colder curves than Chernarus. A Livonia server whose temps differ from
Chernarus's is at *its own vanilla*, not modified — "normalizing" it is a real
gameplay change disguised as a cleanup.

To make winter harsher, shift the min array down a few degrees and leave max
alone; that widens the daily swing without making summer unplayable.

**Verify:** diff the file rather than waiting for the season to come round.

---

## Darker nights

Two halves, and doing only one is a half-measure:

```json
"WorldsData": { "lightingConfig": 1 },
"PlayerData":  { "disablePersonalLight": true }
```

`lightingConfig: 1` dims the world; `disablePersonalLight: true` removes the
faint light that follows the player. One Life ran the personal-light half
without ever running `lightingConfig: 1`.

**Do not set `lightingConfig: 2` outside Sakhal** — it is a Sakhal-specific
lighting profile, not a brightness level.

**Precedence:** `lightingConfig` also exists in `serverDZ.cfg`, and
`WorldsData.lightingConfig` **overrides it** when `enableCfgGameplayFile` is on.
Changing it in `serverDZ.cfg` and seeing nothing happen is this rule biting.

**[unverified]** Whether darker nights survive players brightening their
displays has not been measured on console. Gamma exploitation is known on PC
via driver settings.

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

Clan Wars' configuration: the map opens with `M` without carrying one,
compass/GPS helpers work without the items, and players see their own position
and facing. Together this turns navigation into a minimap — right for
coordinated faction PvP, wrong for a server where finding your way *is* the
gameplay. One Life leaves all three vanilla `false`.

**⚠ `displayNavInfo` overrides `ignoreNavItemsOwnership`.** Set the ownership
bypass `true` but `displayNavInfo` `false` and the legend stays hidden anyway.
Keep `displayNavInfo: true` or the bypass is silently defeated.

This is also the fastest smoke test that the file is being read at all —
`displayPlayerPosition` is visible the moment a player opens the map.

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
block — re-apply that and you are done. Anything else that differs was upstream
drift, not a setting anyone chose.

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
