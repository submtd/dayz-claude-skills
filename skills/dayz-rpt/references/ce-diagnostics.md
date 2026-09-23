# What the RPT says about the mission

The central economy is engine-native, `proto native` all the way down. None
of its messages are explained by any published source. What they mean below
comes from counting them against the mission files that produced them, on
four live servers. Where only a correlation exists, the entry says so and
tags the mechanism `[unverified]`. The operator's instruction was to
**document these as evidence**, not to explain them.

Tags as in [format.md](format.md).

## Contents

- [Load summary: did my edit load?](#load-summary-did-my-edit-load)
- [Load problems](#load-problems)
- [Defects Bohemia ships](#defects-bohemia-ships)
- [Runtime pressure](#runtime-pressure)
- [Storage](#storage)

---

## Load summary: did my edit load?

At boot the CE prints counts. Five of them equal a count you can take from
the mission files, **exactly, on all four servers** `[corpus]`:

| RPT line | Equals | Example |
|---|---|---|
| `[CE][IgnoreList] "cfgignorelist.xml" :: loaded N types` | entries in `cfgignorelist.xml` | 24 |
| `[CE][LoadPrototype] :: loaded N prototypes` (first of two) | uncommented `<group>`s in `mapgroupproto.xml` | 456 |
| `[CE][LoadMap] "Group" :: loaded N groups, groups failed: F` | uncommented `<group>`s in `mapgrouppos.xml` | 5275 |
| `[CE][DynamicEvent] Load  Events:[N] Primary spawners: P …` | `events.xml` events with `<active>1</active>` | 34 |
| `[CE][DE][SPAWNS] :: Total positions: N` | `<pos>` entries under **active** events in `cfgeventspawns.xml` | 460 |

**This is how you confirm a deploy.** Count the file you deployed, restart,
and compare. A match means the server loaded that exact file. A mismatch
means it loaded something else, or the edit sits inside a comment or under
an inactive event.

- **Comments count.** Clan Wars' `mapgrouppos.xml` has 5,287 `<group>` lines
  and loads 5,275. Twelve are commented out, and those are the locations
  with loot disabled. A naive `grep -c` gets the wrong number.
- **Inactive events do not count**, and neither do their spawn positions.
  `events.xml` has 60 events on Clan Wars and 34 are loaded.
- **`groups failed: 0`** on all four servers. A non-zero count means
  `mapgrouppos.xml` places groups that `mapgroupproto.xml` cannot resolve.
  `triage.py` fails on it.
- **`[CE][TypeSetup] :: N classes setuped`** (583–599) is **not** the
  `types.xml` count (about 1,970). What it counts is `[unverified]`.
- The second `[CE][LoadPrototype] :: loaded 0 prototypes`, and `[CE][LoadMap]
  "Dirt" :: loaded 0 groups`, are the dirt-group pass. They were 0 on every
  server.

## Load problems

**JSON files leave no trace.** In 24 boots, all running `cfggameplay.json`,
the RPT never mentions `cfggameplay` or any `.json`. A correct load is
silent. What a malformed one writes is `[unverified]`, so do not treat
silence as proof it loaded. Use `dayz-cfggameplay`'s validator.

```
!!! [CE][offlineDB] :: Type 'WinterMilitaryCoat_Greay' will be ignored. (Type does not exist. (Typo?))
!!! [CE][offlineDB] :: Type 'ChristmasTree_Green' will be ignored. (Not spawnable. (Scope is not public?))
!!! [CE][DE][SPAWNS] :: [WARNING] :: Skipping entry for non-existing event 'VehicleTransitBus'.
!!! [CE][LoadPrototype] 10 Errors during XML parse...
!!! [CE][LoadPrototype] 4 groups have no points...
!!! [CE][LoadPrototype] 1 groups have wrong points...
```

- **`Type does not exist. (Typo?)` is the game naming a `types.xml`
  classname it does not know.** One Life Livonia logs
  `WinterMilitaryCoat_Greay`, Bohemia's typo. Clan Wars fixed that line and
  does not log it `[corpus]`. So:
  - **The RPT can confirm a classname is wrong.** It says so explicitly.
  - **It cannot confirm a classname is right.** Silence means the class
    exists, not that the item spawns; `nominal`, usage and capacity decide
    that.
  - **This is a real exception to `CLAUDE.md`'s "a classname is confirmed
    by … nothing else"** for the negative case.
- **`Not spawnable. (Scope is not public?)`**: the class exists, but the
  game will not spawn it. The line is ignored like a typo.
- **`Skipping entry for non-existing event 'X'`**: `cfgeventspawns.xml` has
  `<event name="X">` and `events.xml` defines no event `X`.
- **The `[CE][LoadPrototype]` counts** (`Errors during XML parse`, `groups
  have no points`, `groups have wrong points`) come from `mapgroupproto.xml`.
  They sit between `loaded N prototypes` and `last group name: …`.
  - Clan Wars, One Life Chernarus and One Life Livonia each log 10 parse
    errors, yet every prototype still loads, so **a parse error here does
    not drop a group**.
  - Sakhal logs no parse errors, and 12 groups with wrong points.
  - `groups have no points` is 5 on Chernarus, the same number of
    point-less containers `dayz-mapgroups`' validator counts there. Livonia
    and Sakhal do not match that way.
  - What each count measures is `[unverified]`. Only the Chernarus
    correspondence has been seen, so do not treat any of the three numbers
    as a diagnosis.

## Defects Bohemia ships

Every load problem on the four live servers comes from Bohemia's own
`BohemiaInteractive/DayZ-Central-Economy@master` files for that map `[corpus
+ shipped files]`. `triage.py` knows these by name and does not fail on them:

| RPT name | Where Bohemia ships it | Complaint |
|---|---|---|
| `Static_FrozenScientist_DE` | Chernarus, Livonia `types.xml` | Type does not exist |
| `ChristmasTree` | Chernarus `types.xml` and `events.xml` | Not spawnable |
| `ChristmasTree_Green` | Livonia, Sakhal `types.xml` | Not spawnable |
| `Land_wreck_sed02_aban1_police`, `…aban2_police` | Sakhal `types.xml` | Not spawnable |
| `WinterMilitaryCoat_Greay` | Livonia `types.xml` (typo for `_Grey`) | Type does not exist |
| `VehicleTransitBus` | Chernarus, Livonia `cfgeventspawns.xml` | Non-existing event |

A name **not** on this list, on a mission derived from vanilla, is a local
edit gone wrong.

## Runtime pressure

These repeat for as long as the server runs. Counts are per two-hour
session.

### `[CE][LootRespawner] … Item [N] causing search overtime: "X"` and `… is hard to place, performance drops: "X"`

- **Evidence:** on Clan Wars the worst offender is `AK101`, whose `nominal`
  was raised from vanilla 2 to 13, with 235 overtime lines in one session.
  `R12` (5 → 25) is next. **Vanilla items appear too.** One Life Livonia's
  prison items (`PrisonerCap`, `GulagJacket_Grey`), with vanilla nominals
  and the prison loot intact, log "overtime" as well.
- **Reading, `[unverified]`:** the respawner is working hard to place items
  whose target count is high relative to the places they can go. That
  fits `dayz-types`' `nominal` and `dayz-mapgroups`' capacity, but no
  source says what the threshold is.
- **Use it as a lead, not a verdict.** A new item at the top of this list
  after a `nominal` change is the first thing to look at. An item that has
  always been there is baseline.
- The `(PRIDummy)` tag appeared on every one `[corpus]`.

### `!!! [CE][VehicleRespawner] (PRIxxx) :: Respawning: "Event" - Failed to spawn the requested amount (got < wanted) within N attempts.`

- A vehicle event could not place its count. On Clan Wars, three admin
  vehicle events (`VehicleAdminGunter`, `…Sarka`, `…Olga`) log "0 < 1"
  about 74 times per session, and that is **expected** there `[operator]`.
  Repetition alone does not make a line a problem.
- `StaticHeliCrash … got 1 of 3` is the same message for a crash-site
  event. It relates to `events.xml` `nominal`, `min` and `max` and to the
  event's spawn positions.

### `[CE][SpawnRandomLoot] (Event) :: Type: X :: !!! Sum of container LootMax is lower than event child LootMax (a < b)`

It usually comes with `!!! Wanting to spawn more loot than possible (a > b)`.

- An event's child in `events.xml` asks for more loot (`lootmax`) than the
  containers in that structure's `mapgroupproto.xml` group can hold.
  **This is a cross-file mismatch between `events.xml` and
  `mapgroupproto.xml`**, and the message says which numbers disagree.
- It appears on the vanilla-derived One Life servers too (supply crates,
  convoy wrecks), so some of it ships with Bohemia's files.
- A healthy spawn logs `Type: X, lootmin: …, lootmax: …, wanted: …, deloot:
  …, containermaxsum: …`. `containermaxsum` is the capacity side of the same
  comparison.

### `!!! [CE][Point] Removing x, z from Classname`

A spawn point near that object was dropped at runtime. Common objects are
`Haybale`, `Land_Roadblock_WoodenCrate` and tree stumps. The mechanism is
`[unverified]`. The counts are small and occur on all servers.

## Storage

```
[CE][Storage] Restoring file "…\storage_<service>\data\dynamic_000.bin" 763 items.
!!! [CE][Storage] Failed to read [Storage] data file "…\dynamic_011.001".
!!! Failed to write [Storage] data to file "…\types.bin" - failed to open the file.
```

- **Restore counts** (`building.bin N items`, `dynamic_NNN.bin N items`)
  show how much persistent state loaded. A sudden drop to near zero, with no
  intended wipe, is worth investigating.
- **Occasional failed reads and writes appear on all four servers:** 10 of
  24 boots had one or two, and 14 had none `[corpus]`. What they cost is
  `[unverified]`. Nothing in the corpus ties them to lost items.
- The storage path names the mission folder and the Nitrado service id.
  Anonymise it before sharing.
