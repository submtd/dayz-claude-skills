---
name: dayz-mapgroups
description: Use when working with a DayZ server's mapgroupproto.xml or mapgrouppos.xml — where loot can spawn inside a building, how much fits, which buildings on the map are lootable, loot tiers and usage flags on spawn points, static props and fixed item placement inside structures, custom POIs and loot concentration, disabling loot at one location, or loot-point thinning for server performance — or when loot appears in the wrong place, in the wrong quantity, or not at all in a specific building.
---

# DayZ mapgroupproto.xml and mapgrouppos.xml

Two files, one mechanism. **`mapgroupproto.xml` defines building types**: for
each structure classname, where loot may appear inside it, what kinds, and how
much. **`mapgrouppos.xml` places instances**: every lootable structure standing
on the map, one line each, naming a prototype.

Change one without the other and you get silence — no error, no log line, no
loot. That is the characteristic failure of this pair and the reason they are
one skill.

Vanilla source: `BohemiaInteractive/DayZ-Central-Economy@master`, per map
(`dayzOffline.chernarusplus`, `dayzOffline.enoch`, `dayzOffline.sakhal`).
Both files are large — 18k–22k lines for proto, 5k–12k for pos — and both are
**different on every map**. Diff against the matching map.

## Never answer from memory

Every element name, attribute, default and valid value **must** come from
`references/schema.md`. This file is undocumented: there is no Bohemia wiki
page for `mapgroupproto.xml`, and community write-ups disagree with the
shipped files. An agent asked eight routine questions about it answered
fluently and was wrong six times:

- It gave the root element as **`<proto>`**. It is **`<prototype>`**.
- It **missed the `<defaults>` block entirely** and then said `lootmax` has
  no default. The file declares its own: **`group` 6, `container` 4**. On
  Livonia 137 of 456 groups and 243 of 852 containers rely on it, so "no
  default" mis-reads a third of the file.
- It said `<container>` carries `usage` and `value` filters. **Containers
  carry neither**; they carry `category` and `tag`. (Sakhal ships two that do
  anyway — Bohemia's bug, not a counter-example. See `references/schema.md`.)
- It described `<proxy type="...">` as **a reference to another `<group>`**
  that "does not itself spawn loot" and is "fully subject to nominal/min."
  `type` is an **item classname**, and the relationship to `nominal` is the
  reverse of what it said. See the trap below.
- It described `<dispatch>` as a **random pick among alternative prototypes
  for visual variety**. It is a fixed-offset placement list for named items.
- It listed usage flags including **`City`**, which does not exist, while
  omitting `Office`, `Lunapark`, `Underground` and `Special`. It gave the
  tiers as "Tier1 through Tier4" and **omitted `Unique`** — on Livonia,
  which has no `Tier4` at all.

To its credit it refused to invent numeric `flags` values and flagged its own
uncertainty on `a`. The rest read as fact. That fluency is the problem.

## The two files, concretely

```xml
<!-- mapgroupproto.xml — the building TYPE. One entry per classname. -->
<group name="Land_Garage_Row_Small" lootmax="6">
    <usage name="Village" />
    <container name="lootFloor" lootmax="4">
        <category name="tools" />
        <tag name="floor" />
        <point pos="1.02 -1.17 -0.89" range="0.49" height="1.24" />
    </container>
</group>
```
```xml
<!-- mapgrouppos.xml — the INSTANCES. One line per building on the map. -->
<group name="Land_Garage_Row_Small" pos="5488.47 308.85 8693.53"
       rpy="-0.0 0.0 1.15" a="88.84" />
```

`pos` is world X/Y/Z. `rpy`/`a` are orientation — **see the `a` trap below,
they are not interchangeable**. A pos line carries no loot information at all;
it is a pointer to a prototype.

## Things that are not what they look like

- **`mapgrouppos.xml` does not place buildings.** The meshes and collision
  live in the terrain `.pbo`. A pos entry only tells the central economy
  *"a lootable thing of this type stands here."* Delete a line and the
  building is still there, still enterable — it just holds no loot. This is
  the single most useful property of the file and the basis of every recipe
  in `references/recipes.md`.

- **`a` is not a duplicate of `rpy`, and it is the one that matters for
  loot.** `a` rotates the loot-point ring around the structure. Set it wrong
  and points land outside or inside the mesh. **[operator]** Verified in
  game: a container placed by an object spawner with `a="0"` spawned its loot
  *perpendicular to the container*; `a="90"` fixed it. **Note the commit
  history on this is misleading** — `dayz-clan-wars/livonia@8dafd08` records
  the 90° value as introducing a mismatch to be fixed later. The opposite is
  true; 90° was the fix. Do not trust that commit message over this line.

- **`<proxy>` is a named item at a fixed offset, not a sub-building.**
  `<proxy type="M67Grenade" pos="..." rpy="..." dechance="0.25"/>` places
  *that classname* at *that exact spot*, rolling `dechance` to decide whether
  it appears. It is how a crate modelled to hold grenades actually holds
  grenades. Proxies only ever appear inside `<dispatch>`.

- **Proxy items still need a `types.xml` entry, at `nominal 0`.** Not to make
  them spawn — dispatch places them regardless — but so the CE has a
  registration for the classname. Without one it logs the type as unknown
  every time the group builds. **[operator]** The pattern is `nominal 0`,
  `min 0`, `count_in_map="1"`, short lifetime: registered, but outside the
  loot economy. This is the reverse of the intuitive reading, where a proxy
  would be *drawn from* the nominal pool.

- **Five proxy types ship unregistered in Bohemia's own files.**
  `Offroad_02_Door_1_1_BeigeRust`, `_1_2_`, `_2_1_`, `_2_2_` and
  `Offroad_02_Trunk_BeigeRust` are referenced by `mapgroupproto.xml` and
  absent from `types.xml` on **vanilla Chernarus and vanilla Livonia**
  (Sakhal is clean). **This is not local drift** — `scripts/validate.py`
  knows them by name and downgrades them to a tagged warning so an untouched
  mission still exits 0. Do not "fix" them in a mission tree.

- **`<value name="TierN">` on a surface building does nothing.**
  **[operator]** Loot tiers are not in the mission XML at all — they live in
  **`areaflags.map`**, a ~72–80 MB binary raster that ships in the mission
  tree beside these files. Tier is therefore a property of *where a building
  stands*, not of the building. This is why `<value>` appears on only 2 of
  446 Chernarus groups, 14 of 456 Livonia and 5 of 525 Sakhal — and only on
  interiors (the Livonia underground bunker, Sakhal's warhead facility) and
  dynamically-spawned containers, none of which the area raster covers.
  **[unverified]** that `<value>` acts as the fallback where the raster does
  not reach; the shipped pattern fits, but the CE is `proto native` and not
  in the script repo.

- **Tiers *are* editable on console — the constraint is the toolchain, not
  the platform.** `areaflags.map` is authored with **DayZ Tools, which is
  PC-only**, but the resulting file deploys to a console server like any
  other mission file and works. **[operator]** Do not tell a console operator
  that loot tiers are out of reach; tell them they need a PC to author the
  raster. "No mods on console" does **not** extend to this.

- **A group's `lootmax` and its containers' `lootmax` disagree, usually.**
  The group value is the ceiling the engine enforces; containers routinely
  advertise more. On Clan Wars Livonia **129 of 237 placed building types**
  have containers summing above the group cap, and the two rollups differ by
  39% map-wide. Always reason with the **group ceiling** — see
  `references/capacity.md`.

- **Group names match case-insensitively.** **[unverified]**, but the
  evidence is strong: Bohemia's own files spell the same group
  `Land_Wreck_truck01_aban1_green` in proto and `Land_wreck_truck01_aban1_green`
  in pos, and `Land_Mil_Guardhouse3` vs `Land_Mil_GuardHouse3`. A
  case-sensitive check reports 6 orphans on vanilla Chernarus, 10 on Livonia
  and 11 on Sakhal; case-insensitively all three, and all four live configs,
  report **zero**. Three independently-authored maps landing on exactly zero
  is not coincidence. **A case-sensitive validator is wrong**, and this is
  the single easiest way to generate a page of false positives here.

- **Empty containers, `lootmax="0"` groups and a `dechance` of `1.3` are all
  shipped by Bohemia.** A validator that errors on any of them fails an
  untouched vanilla mission. `scripts/validate.py` reports each as a note or a
  tagged warning; vanilla Chernarus, Livonia and Sakhal all exit 0.

- **Most prototypes are never placed.** Livonia defines 456 groups and places
  240 distinct names; 226 protos have no pos entry at all. That is normal —
  proto is a shared library across maps and DLC, not a manifest. **An unplaced
  proto is not dead config** and must not be reported as one.

- **Usage, value, category and tag names are declared per mission, not
  global.** Every one must appear in that mission's
  `cfglimitsdefinition.xml`; an undeclared name is silently dropped along with
  the whole filter. There is no fixed list to memorise — read the mission's
  file. This is also what makes **custom** usage flags possible, and it is the
  mechanism the POI recipe depends on. See `references/cross-file.md` rule 2.

- **A usage can carry `nominal` in `types.xml` with nowhere to spawn.** If no
  *placed* group carries that usage, those items simply never appear — no
  error, no log line. Removing the map's only prison, or switching off the
  contaminated-area events while types still route through
  `ContaminatedArea`, both do this. `scripts/validate.py` reports it as
  `stranded-usage`; `references/capacity.md` works a live case where 63
  nominal was stranded, including a rifle whose nominal had been deliberately
  raised to 24. **Check this after any change that removes capacity.**

- **`<usage>` is on the `<group>`, so it is a property of the building type,
  not the location.** Tagging `Land_Prison_Main` with a custom usage gives it
  to every prison on the map. This is the trap in the POI recipe in
  `dayz-types/references/classnames.md`, which says only "tag the POI's loot
  points" — see `references/recipes.md` for the version that works.

- **Two groups ship with no `<usage>` at all** on vanilla Livonia —
  `Land_Mil_Airfield_HQ` and `Land_Airfield_Radar_Tall`. Neither is placed in
  `mapgrouppos.xml`, so neither matters, but a validator that flags
  usage-less groups will hit them. **[unverified]** what a placed usage-less
  group would actually draw.

## Routing

| Question | Go to |
|---|---|
| What does this element/attribute mean? Valid values? | `references/schema.md` |
| How much loot can spawn here? Is my change safe? | `references/capacity.md` |
| How do these files interact with types.xml, cfglimitsdefinition, object spawners? | `references/cross-file.md` |
| Concentrate loot at a POI, disable loot at one place, thin for performance, add a custom container | `references/recipes.md` |

## House conventions

- **Splice, never parse-and-reserialize.** Both files carry meaningful
  formatting; `mapgrouppos.xml` is one element per line by design, which is
  what makes it greppable and line-diffable. A round trip through an XML
  library destroys the indentation (proto uses tabs at irregular depths) and
  makes the diff unreviewable.
- **Disable by commenting out, not deleting**, when the change is a policy
  choice you may reverse. Prefix the reason so it stays greppable:
  `<!-- Kopa prison (loot disabled): <group name="..." ... /> -->`. Reserve
  deletion for bulk passes where the volume makes comments unreadable, and
  say in the commit how many lines went.
- **Editing `mapgrouppos.xml` forks it from upstream.** Bohemia ships terrain
  updates that rewrite this file; every deletion needs a manual re-merge
  afterwards. Record the running deletion count in the commit message so the
  next person knows the size of the re-merge before they start.
- **Read the value back after editing.** A `<point>` at the wrong nesting
  depth — inside `<group>` rather than `<container>` — still parses as valid
  XML and is silently ignored.
- **Run `scripts/validate.py <mission-dir>`** before shipping, and confirm in
  game after a restart. It works on any DayZ mission tree.
