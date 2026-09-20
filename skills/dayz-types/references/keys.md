# `types.xml` element reference

Every claim is marked **[source]** (engine scripts), **[shipped]** (counted
from Bohemia's vanilla files at `master`), **[operator]** (confirmed on these
servers) or **[unverified]**. Do not promote an `[unverified]` claim.

**There is no wiki page for this file.** Bohemia's
`DayZ:Central_Economy_Configuration` documents `globals.xml` and
`cfgEconomyCore.xml` and stops — it has no `types.xml` element table at all.
Every per-element reference you will find online is community-written. That is
why this file leans on engine source and counted values instead.

Much of the CE is `proto native` C++ and absent from the script repo. Where
the accessor exists but the behavior does not, the entry says so.

## Structure

```xml
<types>
    <type name="AK101">
        <nominal>4</nominal>
        <lifetime>28800</lifetime>
        <restock>3600</restock>
        <min>2</min>
        <quantmin>30</quantmin>
        <quantmax>80</quantmax>
        <cost>100</cost>
        <flags count_in_cargo="0" count_in_hoarder="0" count_in_map="1"
               count_in_player="0" crafted="0" deloot="0"/>
        <category name="weapons"/>
        <usage name="Military"/>
        <value name="Tier3"/>
    </type>
</types>
```

Those `quantmin`/`quantmax` values are vanilla's real ones for `AK101` — a
weapon *does* take a quantity roll, for the ammo it spawns loaded with. Most
items take none and use `-1`/`-1`; see `quantmin` / `quantmax` below before
copying this block for something that has no quantity.

`<types>` contains only `<type>` elements — no other root child exists in any
shipped file. **[shipped]** `name` is the only attribute on `<type>`.

The seven scalar children and `<flags>` appear on **every** vanilla type
without exception. `category`, `usage`, `value` and `tag` are optional.
**[shipped]**

Keep this element order. Vanilla uses it uniformly and a reviewer diffing
economy numbers should not have to reorder in their head.

---

## Scalars

### `nominal`

Target population — roughly how many should exist in the world at once.
**[source]** `CEItemProfile::GetNominal()`, *"nominal - how many items should
be aproximately in map"* (`centraleconomy.c:753`).

`0` disables the type for normal loot placement. It is the standard way to
turn an item off, and **869 of 1,970 Chernarus types ship at `0`**
**[shipped]** — a zero is far more likely to be deliberate than a mistake.

A disabled type is still registered: events, `cfgspawnabletypes.xml` cargo and
admin spawning can still produce it, and `lifetime` still applies to copies
that exist.

**Setting `nominal 0` does not remove existing copies.** They run out their
`lifetime`, and anything in persistent storage does not expire at all. To
remove an item now, use `cfgignorelist.xml` — see `cross-file.md`.

**The sum of `nominal` across the file is a performance budget.** See the
table in `SKILL.md`; this is the operator's primary frame for the file.
**[operator]**

### `min`

The floor that triggers restocking; the CE refills toward `nominal` once the
live count drops below it. **[source]** `GetMin()`, *"min - minimal count
should be available in map"* (`centraleconomy.c:754`).

`min` should be ≤ `nominal`, but **this is not enforced and vanilla violates
it**: Sakhal ships `BatteryCharger` with `min 18` / `nominal 13`.
**[shipped]** What the CE actually does in that state is **[unverified]** —
no script-side code settles it. The validator warns rather than errors.

`min == nominal` is common and legitimate in Clan Wars (e.g. `CZ527_Black`
40/40) — it means "keep it topped up constantly."

### `lifetime`

Seconds an untouched copy survives on the ground before cleanup. **[source]**
*"maximum lifetime in (seconds) - what is the idle before item abandoned at
ground gets deleted"* (`centraleconomy.c:761`).

**Clamped to `[3, 316224000]`** — 3 seconds to 10 years. **[source]**
`centraleconomy.c:314`.

Common vanilla values **[shipped]** (Chernarus):

| Value | Meaning | Count |
|---|---|---|
| `14400` | 4h — the common-loot default | 1,079 |
| `28800` | 8h | 415 |
| `3888000` | **45 days — base parts and storage** | 22 |
| `1800` | 30 min | 220 |
| `0` | static map objects — see below | 66 |

**The 45-day entries are the ones base decay actually runs on.** A flag
postpones these; it does not replace them. This is the One Life issue recorded
in `SKILL.md`. Clan Wars sets its equivalent 35 types to `604800` (7 days).

`lifetime 0` is carried **only** by static map objects — `Land_*_DE` wrecks
and containers, and `StaticObj_*_DE` roadblocks, decals and loaded train
wagons. Counts differ per map: **66 Chernarus, 64 Livonia, 68 Sakhal**.
**[shipped]** (SKILL.md quotes no single number for exactly this reason.)

**[unverified]** whether `0` means "never cleaned" or is clamped up to the
3-second floor. Every type carrying it is a static object, so the distinction
has not mattered.

### `restock`

**Seconds**, like `lifetime`. **Not a respawn cooldown in the way the name
suggests.** **[source]**
*"restock is oposite of lifetime - idle before item is allowed to respawn when
required"* (`centraleconomy.c:762`).

`0` means no wait, and **1,834 of 1,970 Chernarus types ship at `0`**
**[shipped]**. Non-zero values are the exception, used to stagger a few
high-value types.

Clan Wars sets `0` on all 1,979 types — a smaller deviation than it appears,
since vanilla was already 93% zeros.

The non-zero values Bohemia does use, so you have a scale rather than a guess
**[shipped]** (Chernarus): `1800` on 69 types, `600` on 30, `3600` on 19,
`43200` on 9, `180` on 4. So a deliberate stagger is minutes to hours, and
half a day is the documented ceiling in vanilla practice.

### `quantmin` / `quantmax`

**Percentages of the item's maximum quantity, not absolute amounts.**
**[source]** `GetQuantityMin()` / `GetQuantityMax()` return `float` documented
as *"min quantity (0.0 - 1.0) (like ammobox - this determine how many bullets
are there, or water bottle)"* (`centraleconomy.c:756`). The XML expresses the
same value as `0`–`100`.

A fresh copy rolls a random value in the range. **[source]** `GetQuantity()`,
*"random quantity (0.0 - 1.0)"*.

`-1` on **both** means no quantity roll. Vanilla uses `-1`/`-1` on 1,800 of
1,969 Livonia types **[shipped]** — everything without a quantity concept.

**Half-setting is a bug the game will not report.** Vanilla ships one:
`Crossbow_Black` has `quantmin 80` / `quantmax 0` on Livonia and Sakhal.
**[shipped]**

**[unverified]** what an inverted or out-of-range pair actually produces —
whether it clamps, spawns empty, or skips the roll. No script-side code
settles it and nobody has tested it on these servers. The validator errors on
it because it is certainly not intended, not because the outcome is known.

Clan Wars sets `100`/`100` on **all** types including ones with no quantity.
Deliberate blanket pass, no observed problems. **[operator]** Do not tidy it.

### `cost`

Priority weight — **for cleanup as well as respawn**. **[source]** *"cost of
item determines its 'value' for players (this serve as priority during respawn
and cleanup operation)"* (`centraleconomy.c:764`).

Effectively a constant: **1,969 of 1,970 Chernarus types are `100`**. The sole
exception on all three maps is `Mag_SVD_10Rnd` at `1000`. **[shipped]**

The operator has never changed it. **[operator]** Treat as leave-alone; if a
task seems to call for `cost`, the lever wanted is almost certainly `nominal`.

---

## `<flags>`

All six attributes appear on every vanilla type. **[shipped]** Vanilla usage
counts (Chernarus, value = `1`):

| Attribute | `=1` count | |
|---|---|---|
| `count_in_map` | 1,902 | the normal state |
| `crafted` | 313 | |
| `count_in_player` | 51 | |
| `deloot` | 53 | |
| `count_in_cargo` | 47 | |
| `count_in_hoarder` | 31 | |

### The `count_in_*` family

These decide **which copies count toward `nominal`**: loose in the world
(`count_in_map`), inside containers (`count_in_cargo`), in tents and stashes
(`count_in_hoarder`), or carried by players (`count_in_player`).

`count_in_map="1"` is the normal state and what you want on ordinary loot. The
68 Chernarus types that set it to `0` **[shipped]** are all static map objects
— `Land_*_DE` containers and wrecks — i.e. things the CE places but should not
be counting as loot population. **Do not set it to `0` on a real item**; the
effect of doing so is **[unverified]** and there is no vanilla precedent for
it on anything a player picks up.

> **Setting `count_in_cargo="1"` will make an item stop spawning.** Once
> players stockpile copies in containers, those copies count toward `nominal`,
> the CE sees the target met, and it places no more in the world. This is the
> real mechanism behind "the item disappeared from loot after a few weeks."

**Operator-confirmed on these servers** — the operator has flipped these flags
and states the behavior is real. **[operator]** The same logic applies to
`count_in_hoarder` and `count_in_player`.

The practical consequence: **turning one of these on is a way to let players
deplete an item permanently**, and turning one off is how you guarantee a
steady world supply regardless of hoarding. Both are legitimate; neither is
what someone usually means when they flip a flag to "make it count properly."

Suspect this first when an item *used to* spawn and no longer does.

### `crafted`

> **`crafted` must be `0` for an item to spawn.** **[operator]** A type with
> `crafted="1"` is craft-only — the CE will not place it, whatever its
> `nominal` says.

This is the flag to check when a type looks completely correct and still
produces nothing. It is easy to carry in by copying a neighbouring entry.

The shipped files corroborate it: **all 313 Chernarus types with
`crafted="1"` have `nominal 0`** **[shipped]** — Bohemia does not bother
giving a craft-only item a population target.

There is exactly one exception across the vanilla maps, and it is the
contradiction this rule predicts: **Livonia's `Firewood` has `crafted="1"`
and `nominal 8`**. By the rule it cannot spawn, so the nominal is fiction.
Clan Wars inherited it unchanged. (`Firewood` also has no `<usage>`, so it is
dead twice over.) The validator flags this pairing.

When adding a type, copy vanilla's value — and if you are adding something you
expect to find as loot, that value is `0`.

### `deloot`

Dynamic-event loot. **[unverified]** in the same way — the flag is read
engine-side. Bohemia sets it on 53 Chernarus types, and it changes across
upstream versions (part of the One Life drift). Copy vanilla; do not reason
from the name.

---

## `<category>`

Zero or one per type. **Not required** — types with no category at all:
**348 Chernarus, 358 Livonia, 646 Sakhal**, mostly animals, infected and
static objects. **[shipped]** (So the Chernarus category counts below sum to
1,622, not 1,970.)

The seven real categories, with Chernarus counts **[shipped]**:

| Category | Count |
|---|---|
| `clothes` | 704 |
| `tools` | 271 |
| `weapons` | 262 |
| **`lootdispatch`** | 174 |
| `containers` | 102 |
| `food` | 94 |
| `explosives` | 15 |

There is no `vehiclesparts` category — the RED baseline invented it.
`lootdispatch` is the one that surprises people: every entry is a vehicle door
or panel, and it is how those parts reach `<dispatch>` proxies on wrecks.

The name must exist in that map's `cfglimitsdefinition.xml` `<categories>`.
See `cross-file.md`.

## `<usage>`

Repeatable. Area/usage flags decide **where** the type can spawn, matched
against building loot points. **[source]** `GetUsageFlags()`, *"area usage
flags (each bit has assigned group - which as part of map overlay effectively
affects spawning)"* (`centraleconomy.c:766`).

Distribution **[shipped]** (Chernarus): 719 types have none, 811 have one, 306
have two, and a tail up to five.

**A type with no `<usage>` cannot appear in building loot.** It can still
arrive as cargo, from an event, or via `cfgspawnabletypes.xml`. Several
vanilla types have `nominal > 0` and no usage — that is not automatically a
bug, but it is worth a look.

Names must exist in `cfglimitsdefinition.xml` `<usageflags>`. **Custom usage
flags are legitimate and useful** — see `classnames.md` for the POI-loot
technique that depends on them.

## `<value>`

Repeatable. The loot tier. **[source]** `GetValueFlags()`, same bit-flag
mechanism as usage (`centraleconomy.c:767`).

**Tiers differ by map. This is the most common silent failure in the file:**

| Map | Tiers available |
|---|---|
| Chernarus | `Tier1` `Tier2` `Tier3` `Tier4` `Unique` |
| **Livonia (enoch)** | **`Tier1` `Tier2` `Tier3` `Unique` — no Tier4** |
| Sakhal | `Tier1` `Tier2` `Tier3` `Tier4` `Unique` |

**[shipped]**, verified against all three `cfglimitsdefinition.xml` at
`master` and against all four live missions.

Copying a `<type>` block from a Chernarus file into a Livonia one carries a
`Tier4` that Livonia does not define. Nothing errors and the item does not
spawn. The RED baseline confidently answered "Tier1 through Tier4… possibly
Tier5" for Livonia.

A type with no `<value>` is unrestricted by tier. 449 of 1,969 Livonia types
carry one at all. **[shipped]**

**`Unique` is not a fifth tier.** It is a separate flag for a tiny hand-picked
set, and the set is map-specific **[shipped]**:

- Chernarus and Livonia — 5 types, all ordnance: `M79`, `ClaymoreMine`,
  `Plastic_Explosive`, `RemoteDetonator`, `Ammo_40mm_Explosive`.
- Sakhal — 6 types, all cold-weather survival gear: `HuntingKnife`,
  `HuntingVest`, `HuntingVest_Winter`, `PaddedGloves_Threat`,
  `SnowstormUshanka_Brown`, `SnowstormUshanka_Olive`.

**[unverified]** what the flag does mechanically — it pairs with whatever
loot points `mapgroupproto.xml` marks `Unique` on that map. Bohemia uses it
for "the map's signature item," which is a pattern, not a rule. Do not add it
to a new type without checking the map actually has `Unique` loot points.

## `<tag>`

Repeatable. Placement within a building — matched against loot point tags.
Vanilla Chernarus uses only `shelves` (206) and `floor` (87), though
`cfglimitsdefinition.xml` also defines `ground`. **[shipped]**

Only 293–427 types per map carry a tag at all.
