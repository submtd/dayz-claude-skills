# mapgroupproto.xml / mapgrouppos.xml — element reference

There is **no Bohemia wiki page for either file.** Every element below was
derived by parsing the shipped vanilla files for all three maps
(`DayZ-Central-Economy@master`). Counts are from those files and are the
evidence for each claim. Where a meaning is not established by source or by an
operator's in-game test it is marked `[unverified]` — **that is a gap to
report, not to fill in.**

Tag key: `[shipped]` derived from Bohemia's files · `[operator]` confirmed in
game · `[source]` engine script · `[unverified]`.

---

## mapgroupproto.xml

### Structure

```
<prototype>                                    ← root. NOT <proto>.
  <defaults>
    <default name="group"     lootmax="6"/>
    <default name="container" lootmax="4"/>
    <default name="keepInvalidPoints" enabled="yes"/>
    <default name="clusterMatrix" de="Trajectory…" width="12" height="12"/>
  </defaults>
  <group name lootmax?>
    <usage name/>*          ← 0..n
    <value name/>*          ← 0..n   (rare; see below)
    <container name lootmax?>+
      <category name/>*
      <tag name/>*
      <point pos range height flags?/>+
    <dispatch dechance?>*
      <proxy type pos rpy dechance?/>+
```

**Containers carry no `<usage>` and no `<value>`.** Filtering by usage and
tier is a property of the *group*; only `category` and `tag` narrow a
container. Chernarus and Livonia are clean — 0 of 831 and 0 of 852.

**Sakhal breaks its own schema twice.** `[shipped]` Two containers carry a
`<usage>` where it cannot apply (`Land_Factory_Small`,
`Land_Geoplant_MaintenanceHall`), and `Land_Construction_Crane` has a
`<category>` directly under `<group>` instead of inside a container.
**[unverified]** what the engine does with them — almost certainly ignores
them, which is the normal silent failure. **These are Bohemia's, not local
drift**; `scripts/validate.py` downgrades them to tagged warnings. Do not
"fix" them in a mission tree, and do not copy the shape.

**`<proxy>` never appears directly under `<group>`** — all 338 Livonia, 264
Chernarus and 250 Sakhal proxies sit inside a `<dispatch>`.

**Empty containers and `lootmax="0"` groups are shipped idioms, not faults.**
Vanilla carries containers with no `<point>` inside *placed* groups — 5 on
Chernarus, 2 on Livonia, 13 on Sakhal — and groups such as
`Land_Office_Municipal2` and `Land_Tenement_Big` sit at `lootmax="0"`. Both
look like a retired prototype left in place. Reporting them as errors fails an
untouched mission.

### Per-map shape

| | Chernarus | Livonia | Sakhal |
|---|---|---|---|
| `<group>` | 436 | 456 | 525 |
| …with explicit `lootmax` | 303 | 319 | 371 |
| `<container>` | 831 | 852 | 1024 |
| …with explicit `lootmax` | 614 | 609 | 742 |
| `<point>` | 11,074 | 11,304 | 13,878 |
| …with `flags` | 428 | 535 | 591 |
| `<dispatch>` | 75 | 87 | 71 |
| `<proxy>` | 264 | 338 | 250 |
| `<value>` anywhere | **1 name** | **14** | **5** |

A third of groups and a quarter of containers carry **no `lootmax`** and fall
back to `<defaults>`. Any analysis that treats a missing `lootmax` as
"unlimited" or as zero mis-reads that third of the file.

---

### `<defaults>` / `<default>`

Declared in the file itself, so the file is its own authority for these.

| `name` | Attribute | Value | Present on |
|---|---|---|---|
| `group` | `lootmax` | `6` | all three maps `[shipped]` |
| `container` | `lootmax` | `4` | all three maps `[shipped]` |
| `keepInvalidPoints` | `enabled` | `yes` | **Chernarus and Livonia only** `[shipped]` |
| `clusterMatrix` | `de`, `width`, `height` | `12`×`12` | 8 / 7 / 2 entries `[shipped]` |

**Sakhal ships no `keepInvalidPoints` default.** `[shipped]` What the engine
falls back to in its absence is `[unverified]`. Do not add it to a Sakhal
mission on the assumption it was an oversight.

`keepInvalidPoints` — **[unverified]**. The name suggests whether points that
fail a placement check are retained or discarded. Not confirmed from source;
the CE is `proto native`.

`clusterMatrix` — pairs a `Trajectory*` name with a `width`×`height` cell
size. These govern the vegetation clusters in `mapgroupcluster*.xml` (apples,
stones, conifers, pears, plums, humus, and on Sakhal `TrajectoryCraterellus`),
**not** building loot. They live in this file but are a separate mechanism;
editing loot never requires touching them.

---

### `<group>`

One per structure classname. The `name` must match a classname the terrain
actually uses.

| Attribute | Meaning |
|---|---|
| `name` | Structure classname. Matched **case-insensitively** against `mapgrouppos.xml` `[unverified]`, see SKILL.md |
| `lootmax` | Ceiling on simultaneous loot items for one instance. Default **6**. `[shipped]` |

**The group `lootmax` is the binding constraint**, not the sum of its
containers. See `capacity.md`.

Children: `<usage>`, `<value>`, `<container>`, `<dispatch>`.

---

### `<usage>`

Which loot pools this building type draws from. Cross-matched against the
`<usage>` entries on each `<type>` in `types.xml`; an item can spawn here only
if it shares a usage flag.

**This is not the only router.** `areaflags.map` grants usage by map area too,
so a building can spawn loot its `<usage>` does not mention — Polana on
Livonia is ordinary houses spawning military loot. `[operator]` See
`cross-file.md` rule 6 before concluding anything from a group's usage list.

Valid names come from `cfglimitsdefinition.xml` **in the same mission**, not
from a fixed list. A usage not declared there is silently ignored. Names in
use in vanilla proto:

| | Chernarus | Livonia | Sakhal |
|---|---|---|---|
| Common to all | `Coast` `Farm` `Firefighter` `Hunting` `Industrial` `Medic` `Military` `Office` `Police` `Prison` `School` `SeasonalEvent` `Town` `Village` | | |
| Also | — | `Lunapark` `Underground` | `Lunapark` `Underground` `ContaminatedArea` `Special` |

`cfglimitsdefinition.xml` declares more than proto uses — `ContaminatedArea`
and `Special` are declared on Livonia but referenced by no group there. That
is not an error; they are used by events and types.

**Custom usage flags work.** Declare one in `cfglimitsdefinition.xml` and it
becomes legal in both this file and `types.xml`. That is the basis of the POI
recipe in `recipes.md`.

Two vanilla Livonia groups have **no `<usage>`** — `Land_Mil_Airfield_HQ`,
`Land_Airfield_Radar_Tall`. Neither is placed. What a *placed* usage-less
group draws is `[unverified]`.

---

### `<value>`

Loot tier restriction. Valid names come from `cfglimitsdefinition.xml`:
`Tier1`–`Tier3` plus `Unique` on Livonia; Chernarus and Sakhal add `Tier4`.
**Livonia has no `Tier4`** — a `Tier4` copied from a Chernarus file is
silently ignored.

**Setting `<value>` on an ordinary surface building does not change its loot
tier.** `[operator]` Tiers live in **`areaflags.map`**, a binary raster in the
mission tree that also carries usage areas; tier is a property of *map
position*, not of the building. See `cross-file.md` rule 6.

The shipped usage pattern fits this exactly — `<value>` appears only where the
area raster has nothing to say:

| Map | Groups carrying `<value>` |
|---|---|
| Chernarus | 2 — `Land_Container_1Mo_DE`, `Land_Container_1Moh_DE` (`Unique`) |
| Livonia | 14 — the 12 `Land_Underground_*` bunker rooms (`Tier1`/`Tier2`/`Tier3`) and the 2 `_DE` containers (`Unique`) |
| Sakhal | 5 — `Land_Container_1Mo_DE` and `Land_WarheadStorage_Bunker_Facility` |

All are either **interiors** the surface raster does not cover or **containers
spawned dynamically** at no fixed map position. **[unverified]** that `<value>`
serves as the fallback in exactly those cases — the pattern fits and the
operator's negative result on surface buildings is consistent with it, but the
CE is `proto native` and not in the script repo.

**A group may carry several `<value>` entries**, meaning eligible for any of
them — Sakhal's `Land_WarheadStorage_Bunker_Facility` carries `Tier1`, `Tier2`
and `Tier3`. `[shipped]`

#### Editing tiers

`areaflags.map` ships in every mission tree (`~72–80 MB`; 75,497,496 bytes on
Livonia, 83,886,104 on Chernarus and Sakhal). Binary, short header, not
hand-editable. Authoring needs **DayZ Tools, PC-only**; the result **deploys
to a console server and works** `[operator]`, so the gate is the toolchain,
not the platform. `[unverified]` the internal format beyond the header.

Full treatment in `cross-file.md` rule 6 — the raster carries usage areas as
well as tiers, which is the part that catches people out.

---

### `<container>`

A named bundle of loot points. `name` values in vanilla include `lootFloor`,
`lootshelves`, `lootweapons`, `loot`, `lootGround`, `lootFactory` — and
Bohemia is inconsistent about case (`lootweapons` and `lootWeapons` both
appear in the same file). **The name is a label with no mechanical effect**
`[unverified]`; nothing cross-references it and no two spellings behave
differently in any observable way. Do not rename containers to "fix" the case.

| Attribute | Meaning |
|---|---|
| `name` | Label. No known effect. |
| `lootmax` | Cap for this container's points. Default **4**. `[shipped]` |

---

### `<category>`

Which loot categories this container accepts, matched against `<category>` in
`types.xml`. Valid names come from `cfglimitsdefinition.xml`.

All three maps use exactly seven: `books` `clothes` `containers` `explosives`
`food` `tools` `weapons`. `[shipped]`

**`lootdispatch` is declared in `cfglimitsdefinition.xml` but used by no
`<category>` in any map's proto.** It is the category for items placed via
`<dispatch>`/`<proxy>`, and it belongs on the `types.xml` side.

---

### `<tag>`

Placement surface. Exactly three exist, on all maps: `floor`, `shelves`,
`ground`. `[shipped]` Matched against `<tag>` in `types.xml`; an item with no
tag is unrestricted.

A container may carry several. 2,877 Livonia points sit in containers with
**no tag at all**.

---

### `<point>`

One possible loot position, in **coordinates relative to the structure**, not
world space.

| Attribute | Meaning |
|---|---|
| `pos` | X Y Z offset from the structure origin |
| `range` | A horizontal extent around `pos`. `[unverified]` |
| `height` | A vertical extent around `pos`. `[unverified]` |
| `flags` | `[unverified]` — see below |

**The shape is inferred, not established.** The two attributes are widely read
as describing a cylinder the item spawns within, and the fixed `height`/`range`
ratio below is consistent with that, but nothing in source or a shipped comment
says so. Treat "radius" and "spawn cylinder" as a working model, not a fact.

`range`/`height` are present on essentially every point (11,303 of 11,304 on
Livonia — one point at line 541 carries `pos` and `flags` only, which is
either an authoring slip or evidence both are optional `[unverified]`).

**Authoring convention:** `height` is **2.5 × `range`** on 5,843 of 11,304
Livonia points, and 1.667× on a further 1,278. If you hand-author points,
2.5× matches what Bohemia's tooling emits. `[shipped]`

#### `flags`

**`[unverified]`.** Only two values ever appear: `16` and `32`. Chernarus uses
only `32`. It is set on a small minority of points (428 / 535 / 591 of ~11–14k).

**It is not a restatement of `<tag>`.** Cross-tabulating flags against the
containing container's tags shows no correlation — `flags="32"` appears under
every tag combination including none, and both tagged and untagged containers
carry unflagged points.

No source, no wiki page, no reliable community reference. **Do not guess a
bitmask meaning.** If a task needs it, say it is unestablished.

---

### `<dispatch>` and `<proxy>`

Fixed placement of **named item classnames** at **exact offsets** — as opposed
to `<container>`, which places category-matched loot at random points. This is
what puts grenades in a grenade crate.

```xml
<dispatch dechance="1.000000">
    <proxy type="M67Grenade" pos="-3.30603 0.26218 -1.340943"
           rpy="0.000000 0.000000 0.000000" dechance="0.25" />
</dispatch>
```

| Element | Attribute | Meaning |
|---|---|---|
| `dispatch` | `dechance` | Group-level spawn chance. Optional — 31 of 87 Livonia dispatches omit it. `[shipped]` |
| `proxy` | `type` | **Item classname.** Not a group reference. |
| | `pos` / `rpy` | Offset and rotation relative to the structure |
| | `dechance` | Per-proxy spawn chance, `0.0`–`1.0`. Optional — 114 of 338 Livonia proxies omit it. |

`dechance` reads as a probability, but **Bohemia ships a value above 1.0** —
`StaticObj_Train_Wagon_Flat_Industrial_Planks_DE` carries `dechance="1.3"` on
Chernarus and Sakhal. `[shipped]` **[unverified]** whether values above 1 are
clamped, treated as a repeat count, or simply wrong. The validator reports
anything above 1.0 and tags that one as shipped; negative values are errors.

Whether an omitted `dechance` means `1.0` or defers to the parent is
`[unverified]`. Sakhal sets it on **every** dispatch and **every** proxy;
Chernarus sets it on 12 of 75 and 33 of 264. Bohemia is not consistent, so do
not infer a default from one map.

**Gated by `LootProxyPlacement` in `globals.xml`** — see `cross-file.md`.

**Every proxy `type` needs a `types.xml` entry**, at `nominal 0`. See
`cross-file.md` rule 4 for the pattern and for the five Bohemia ships
unregistered.

---

## mapgrouppos.xml

Flat list. One line per lootable structure standing on the map. Root `<map>`.

```xml
<map>
    <group name="Land_Wreck_hb02_aban1_red" pos="175.239578 196.972504 6863.169434"
           rpy="-0.000000 0.000000 -126.535629" a="-143.464355" />
</map>
```

| Attribute | Meaning |
|---|---|
| `name` | Prototype to use. Matched case-insensitively `[unverified]` |
| `pos` | **World** X Y Z |
| `rpy` | Roll / pitch / yaw of the structure `[unverified]` |
| `a` | **Rotation applied to the loot-point ring.** `[operator]` |

### `a` is the one that matters

`a` rotates the loot-point ring and must match the structure's physical
orientation. **The in-game verification and the misleading commit message are
in SKILL.md**; the pairing with object spawners is in `cross-file.md` rule 7.

What belongs here is the numbers: `rpy` and `a` are **not** redundant and are
not the same value — in the
example above `rpy` yaw is `-126.53` while `a` is `-143.46`. **[unverified]**
what `rpy` does independently; `a` is the one with a confirmed effect on loot.

### The file does not place buildings

Structures are in the terrain `.pbo`. A `mapgrouppos.xml` entry is purely a
central-economy registration: *"a lootable thing of this type stands here."*
Remove the line and the building remains, fully enterable, holding no loot.

### Per-map size

| | Chernarus | Livonia | Sakhal |
|---|---|---|---|
| Entries | 11,679 | 5,753 | 8,332 |
| Distinct names | 269 | 240 | 304 |
| Protos defined but never placed | 173 | 226 | 232 |

**An unplaced prototype is not dead config.** Proto is a shared library across
maps and DLC; roughly half of it going unused on any given map is normal.
