# db/globals.xml — complete variable reference

All 30 variables. Defaults verified against
`BohemiaInteractive/DayZ-Central-Economy@master`, which ships an **identical
`globals.xml` for Chernarus, Livonia and Sakhal** — there is no per-map
variance.

Sources, in descending authority:

1. **[source]** — read out of engine script at
   `BohemiaInteractive/DayZ-Script-Diff`, cited with file and line.
2. **Shipped vanilla files** — authoritative for defaults.
3. **[wiki]** — [Central Economy Configuration](https://community.bistudio.com/wiki/DayZ:Central_Economy_Configuration).
   Wrong twice (below); where it disagrees with a shipped file, it loses.
4. **[unverified]** — operator experience or inference. Do not promote to fact.

Most of these variables are engine-side (C++) rather than script, so
`DayZ-Script-Diff` only covers a few. `FlagRefresh*` is the notable exception
and is the one the wiki phrasing most misleads on.

## File format

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<variables>
    <var name="AnimalMaxCount" type="0" value="200"/>
    <var name="LootDamageMax" type="1" value="0.82"/>
</variables>
```

`type` tells the parser how to read `value`: **`0` = integer, `1` = float,
`2` = string.** Only `LootDamageMin` and `LootDamageMax` ship as floats; no
string variables ship at all.

**[unverified]** A float written under `type="0"` is expected to truncate
silently rather than error — the same silent-failure family as the rest of the
mission tree. No operator has hit this; the attribute is copied from vanilla
and never changed.

## Where the wiki is wrong

| Variable | Wiki says | Every shipped file says |
|---|---|---|
| `LootDamageMax` | `0` | **`0.82`** |
| `LootSpawnAvoidance` | `50` | **`100`** |

The wiki's own note on `LootSpawnAvoidance` — "used to be hard-coded to 50" —
suggests the table was never updated after the default moved.

---

## Loot condition

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `LootDamageMin` | float | `0.0` | 0..1 | Minimum damage applied to any item spawned by the CE |
| `LootDamageMax` | float | `0.82` | 0..1 | Maximum damage applied to any item spawned by the CE |

Each CE-spawned item rolls a random damage in `[min, max]`. `0.0` is pristine,
`1.0` is ruined.

| Damage | Condition |
|---|---|
| `0.0` | Pristine |
| `0.25` | Worn |
| `0.8` | Badly damaged |
| `1.0` | Ruined |

**[unverified]** The badly-damaged → ruined boundary is not established.

**⚠ `cfgspawnabletypes.xml` overrides both of these per item.** Any `<damage>`
entry there wins, including `0.0/0.0`. See `cross-file.md` — this is the single
most important thing to know about these two variables.

**Damage is also a durability budget.** An item spawned at `0.8` ruins after
one use, which turns it into a single-use key. See `cross-file.md`.

## Cleanup and lifetimes

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `CleanupAvoidance` | int | `100` | m | Items are not deleted within this distance of a player |
| `CleanupLifetimeDeadPlayer` | int | `3600` | sec | Corpse and its loot — 1 hour |
| `CleanupLifetimeDeadAnimal` | int | `1200` | sec | 20 minutes |
| `CleanupLifetimeDeadInfected` | int | `330` | sec | 5½ minutes |
| `CleanupLifetimeRuined` | int | `330` | sec | Ruined loot |
| `CleanupLifetimeDefault` | int | `45` | sec | **Not a `types.xml` fallback** — see below |
| `CleanupLifetimeLimit` | int | `50` | — | How many items may be deleted in one cleanup pass |

**`CleanupLifetimeDefault` is the most-misread variable in the file.** [wiki]
defines it as the default lifetime for entities with no specific economy setup
**and damage ≥ 1.0 (i.e. dead)**. It is a 45-second sweeper for untracked dead
or ruined things, not a backstop for `types.xml` entries missing a `lifetime`.

**[unverified]** What happens to an untracked entity with damage **below** 1.0
is not documented — whether something else sweeps it or nothing does. Do not
assume this variable covers it.

`CleanupAvoidance: 100` is why loot does not vanish in front of you. It also
means a player camping a spot holds ruined items in place indefinitely.

`CleanupLifetimeDeadPlayer: 3600` has real gameplay weight on a one-life
server — a full kit sits as bait for an hour and the killer cannot force
cleanup.

## Loot supply

Two distinct mechanisms that the near-identical names invite conflating.

### Bulk fills

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `InitialSpawn` | int | `100` | % | How much loot spawns on a **first-ever** start with no storage |
| `RestartSpawn` | int | `0` | % | How much loot respawns **toward nominal on each restart** |
| `SpawnInitial` | int | `1200` | — | **Not a percentage** — how many placement attempts are allowed per item |

**`RestartSpawn: 0` means restarts do not top loot up.** The economy refills
gradually during uptime instead. "Restart the server to refresh loot" is wrong
on vanilla settings.

**[unverified]** Whether `SpawnInitial` is a per-item retry budget or a global
one is ambiguous in the wiki's phrasing, and it decides whether raising it
helps a map with awkward loot positions.

### Per-cycle throttle

| Variable | Type | Default | Effect |
|---|---|---|---|
| `RespawnAttempt` | int | `2` | Attempts performed during a single item respawn |
| `RespawnLimit` | int | `20` | How many items **of one type** can spawn at once |
| `RespawnTypes` | int | `12` | How many **different types** can respawn at once |

**[unverified]** Raising `RespawnTypes` is inferred to increase the *variety*
refilled per cycle without changing volume per type, so the catalogue converges
on nominal faster. The performance cost of raising it is unknown — Clan Wars
runs `25` and noticed nothing, which is weak evidence at best.

### Placement

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `LootProxyPlacement` | int | `1` | — | Enables `<dispatch>` blocks in `mapgroupproto.xml` |
| `LootSpawnAvoidance` | int | `100` | m | How far a player must be from a loot group for loot to spawn in it |

**`LootProxyPlacement` is narrower than "allow containers to receive loot."** It
enables the `<dispatch>` mechanism, which places a **named item type at a fixed
offset from its parent object**, each proxy rolling its own `dechance`. It is
how a crate modelled to hold grenades actually contains grenades. Worked
example in `cross-file.md`.

`LootSpawnAvoidance` is the anti-farming knob. With `CleanupAvoidance` also at
`100`, there is a symmetric 100m bubble around every player in which **nothing
spawns and nothing is deleted**.

## Territory flags

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `FlagRefreshFrequency` | int | `432000` | sec | How often the flag increases nearby item lifetimes — 5 days |
| `FlagRefreshMaxDuration` | int | `3456000` | sec | How long the refresher runs before stopping — 40 days |

**[source]** `scripts/4_world/entities/itembase/basebuildingbase/totem.c:12`,
with Bohemia's own comments:

```
m_FlagRefresherFrequency   // how often does the flag increase lifetimes
m_FlagRefresherMaxDuration // how long will the refresher run;
                           // multiple of m_FlagRefresherFrequency by default
```

Both are read via `GetCEApi().GetCEGlobalInt(...)` in `InitRefresherData()`,
and each is only applied if greater than zero.

**`MaxDuration` is not a grace period before decay.** Raising a flag starts a
refresher that bumps nearby item lifetimes every `Frequency` seconds for
`MaxDuration` total, then stops. **Re-raising the flag resets the full
`MaxDuration` clock.**

**These are meaningless without the `types.xml` lifetimes they act on.** See
`cross-file.md`.

## Idle mode

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `IdleModeStartup` | int | `1` | — | **0/1 flag.** `0` disables idle mode at server startup |
| `IdleModeCountdown` | int | `60` | sec | Activate economy idle mode on an empty server after this time |

`IdleModeStartup` is a flag, not a duration. [wiki] notes that with `0`, idle
mode will still switch on later if `IdleModeCountdown` is not `0`.

**⚠ That interaction rests on the wiki alone, and the wiki is wrong twice
elsewhere in this same file.** Idle mode is engine-side — `Hive.IsIdleMode()`
is `proto native` in `scripts/3_game/hive/hive.c`, i.e. C++ — so it cannot be
cross-checked against the published scripts. Treat the `Startup: 0` +
`Countdown: non-zero` behavior as **[unverified]**. If you want idle mode
genuinely off, set **both** to `0` as Clan Wars does, rather than relying on
the flag alone.

Idle mode suspends the central economy on an empty server to save host
resources. On rented hosting where the box is paid for regardless, there is
nothing to save, and a frozen economy overnight means a stale world in the
morning.

**`IdleModeCountdown` is session-scoped**, so the server's restart interval
caps it: a 2-hour restart cycle makes any value above 7200 unreachable.
Lifetimes and flag refresh are persistent in CE storage and are *not* reset by
restarts.

## Session timers

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `TimeLogin` | int | `15` | sec | Default login time (max 65536) |
| `TimeLogout` | int | `15` | sec | Default logout time (max 65536) |
| `TimeHopping` | int | `60` | sec | Penalty time for server hoppers |
| `TimePenalty` | int | `20` | sec | Penalty for a player still in a play session |

`TimeLogout` is the combat-logging deterrent — the player stands exposed for
this long before actually leaving.

**`TimeHopping` penalises incoming players.** It is added to the login timer
for anyone arriving from another server, which is every new player trying your
server for the first time. Its design intent — deter hopping — collides
directly with server growth. Zeroing it is a retention decision.

## Population caps

| Variable | Type | Default | Unit | Effect |
|---|---|---|---|---|
| `AnimalMaxCount` | int | `200` | — | Map-wide cap on spawned animals (not ambient) |
| `ZombieMaxCount` | int | `1000` | — | Map-wide cap on spawned infected |
| `ZoneSpawnDist` | int | `300` | m | Distance at which a nearby dynamic infected zone populates |

**These are ceilings, not levers.** Raising `ZombieMaxCount` spawns nothing on
its own — density comes from `env/zombie_territories.xml`. Lowering it silently
clips your zone definitions. See `cross-file.md` for the diagnostic.

Because infected only populate near players, an empty region has none, so the
cap rarely binds at low population. It bites when players are spread widely
enough to have many zones live at once.

## World simulation

| Variable | Type | Default | Effect |
|---|---|---|---|
| `WorldWetTempUpdate` | int | `1` | Allow wetness and temperature updates on all items in the world |
| `FoodDecay` | int | `1` | Allow decay on food |

**`FoodDecay` requires `WorldWetTempUpdate: 1`.** [wiki] states the dependency
explicitly. Turning off the parent silently disables food decay whether or not
that was intended.

`WorldWetTempUpdate` is the whole survival layer around clothing — gear getting
wet in rain, drying by a fire, warming and cooling. Disabling it is drastic and
takes `FoodDecay` with it.

---

## Verifying a default

```sh
gh api "repos/BohemiaInteractive/DayZ-Central-Economy/contents/dayzOffline.chernarusplus/db/globals.xml?ref=master" \
  --jq '.content' | base64 -d
```

Any of the three maps works — the file is identical across all of them. Live
Xbox servers track `master`, not a tagged release.
