# mapgroupproto.xml / mapgrouppos.xml — the cross-file rules

Neither file does anything alone. Every rule below fails **silently**: the
server boots clean, no line appears in the RPT, and the loot is simply absent.

---

## 1. pos → proto: the name must resolve

Every `<group name>` in `mapgrouppos.xml` must match a `<group name>` in
`mapgroupproto.xml`. A pos entry naming a prototype that does not exist places
nothing.

**The match is case-insensitive.** `[unverified]`, but see SKILL.md — Bohemia's
own files rely on it, and a case-sensitive check produces 6–11 false positives
on every untouched vanilla map. **Compare lowercased.**

The reverse is **not** a rule. 173–232 prototypes per map are never placed;
proto is a shared library across maps and DLC. An unplaced proto is not dead
config and must not be reported as one.

---

## 2. proto → cfglimitsdefinition.xml: the vocabulary

`<usage>`, `<value>`, `<category>` and `<tag>` names in `mapgroupproto.xml`
are only legal if declared in **the same mission's**
`cfglimitsdefinition.xml`. An undeclared name is silently ignored, taking its
whole filter with it.

```xml
<lists>
    <categories>  <category name="tools"/> …          </categories>
    <tags>        <tag name="floor"/> …               </tags>
    <usageflags>  <usage name="Military"/> …          </usageflags>
    <valueflags>  <value name="Tier1"/> …             </valueflags>
</lists>
```

**This file differs per map.** Livonia declares `Tier1`–`Tier3` and `Unique`;
Chernarus and Sakhal add `Tier4`. A `Tier4` copied from a Chernarus file into
a Livonia mission is ignored.

**Custom names work** — add them here first and they become legal in both
`mapgroupproto.xml` and `types.xml`. This is what makes the POI recipe in
`recipes.md` possible.

`cfglimitsdefinitionuser.xml` exists alongside it and defines *user*-facing
limit groupings; it is not the registry proto validates against.

---

## 3. proto ↔ types.xml: the four-way match

An item spawns at a loot point only if **all** of these intersect:

| `mapgroupproto.xml` | `db/types.xml` | Effect if they do not overlap |
|---|---|---|
| `<group><usage>` | `<type><usage>` | item never appears in that building type |
| `<group><value>` | `<type><value>` | see the tier caveat below |
| `<container><category>` | `<type><category>` | item never appears in that container |
| `<container><tag>` | `<type><tag>` | item never appears at those points |

An item with **no** `<category>`, `<tag>` or `<value>` is unrestricted on that
axis — 358 vanilla Livonia types have no `<category>` at all. Absence is not
the same as an empty match.

**The tier caveat:** `<value>` on a proto group does not control tier for
ordinary surface buildings — tiers come from `areaflags.map`. See rule 6.

### Zero capacity with non-zero nominal

If a usage carries `nominal` in `types.xml` but no *placed* group carries that
usage, those items cannot spawn from building loot. `ContaminatedArea` and
`Special` are the legitimate exceptions — they are event-fed. See
`capacity.md`, which works the check through a live example.

---

## 4. proxy types → types.xml: registration at nominal 0

Every `<proxy type="...">` classname needs a `types.xml` entry — **not to make
it spawn** (dispatch places it regardless) but so the CE has a registration
for the classname. Without one it logs the type as unknown each time the group
builds. `[operator]`

The pattern is a registration that stays out of the loot economy:

```xml
<type name="StaticObj_Furniture_metalcrate_02">
    <nominal>0</nominal>
    <lifetime>7200</lifetime>
    <restock>0</restock>
    <min>0</min>
    <quantmin>-1</quantmin>
    <quantmax>-1</quantmax>
    <cost>100</cost>
    <flags count_in_cargo="0" count_in_hoarder="0" count_in_map="1"
           count_in_player="0" crafted="0" deloot="0"/>
</type>
```

`nominal 0` / `min 0` keeps it off the loot economy; `count_in_map="1"`
registers it as a world object. This is the **reverse** of the intuitive
reading, in which a proxy would be drawn from the nominal pool.

### Five ship unregistered in vanilla

`Offroad_02_Door_1_1_BeigeRust`, `_1_2_`, `_2_1_`, `_2_2_` and
`Offroad_02_Trunk_BeigeRust` are referenced by `mapgroupproto.xml` and absent
from `types.xml` on **vanilla Chernarus and vanilla Livonia**. Sakhal is
clean. **This is a Bohemia defect inherited by every mission built on those
maps, not local drift** — `scripts/validate.py` knows them by name and
downgrades them to a tagged warning so an untouched mission exits 0.

### Deleting a proto removes its registrations' purpose

If you delete a group, re-check whether its proxy types are still referenced
elsewhere before dropping their `types.xml` entries. A proxy classname is
usually used by several prototypes.

---

## 5. `<dispatch>` ← `LootProxyPlacement` in `db/globals.xml`

`LootProxyPlacement` gates the dispatch mechanism. It is `1` on all three
vanilla maps. Setting it to `0` kills themed fixed placement server-wide,
leaving only category loot on random `<point>`s — so the crate modelled to
hold grenades holds whatever the category roll produces.

**[unverified]** whether `0` disables `<dispatch>` outright or merely skips
the proxies. Either way it is a server-wide switch and almost never the right
lever for a single building; delete or edit the `<dispatch>` block instead.

See the `dayz-globals` skill for the variable itself.

---

## 6. Tiers ← `areaflags.map`, not the XML

Loot tier is a property of **where a building stands**, not of the building.
It lives in `areaflags.map`, a binary raster shipped in the mission tree
(~72–80 MB).

- Setting `<value name="TierN">` on an ordinary surface building **does
  nothing**. `[operator]`
- `<value>` appears in vanilla only on interiors and dynamically-spawned
  containers, which the surface raster does not cover. `[shipped]`
- Editing the raster needs **DayZ Tools, which is PC-only** — but the result
  **deploys to a console server and works**. `[operator]` The constraint is
  the authoring toolchain, not the platform.

So on a console mission tree with no PC available, **`<usage>` is the only
loot-routing lever you have.** Design around usage flags, not tiers.

---

## 7. pos ↔ `cfggameplay.json` → `objectSpawnersArr`

For a structure that is **not** part of the terrain — a container, a custom
POI, an airdrop — two independent things must happen:

| | File | Effect if missing |
|---|---|---|
| the physical object | a JSON in `objectSpawnersArr` | loot points with nothing around them |
| the loot registration | a `mapgrouppos.xml` entry | an empty object |

**They must move together.** Change the position in one and not the other and
the object and its loot land in different places.

**And the rotations must agree.** `mapgrouppos.xml`'s `a` rotates the
loot-point ring; the spawner JSON carries the object's own yaw. These are
different numbers in different frames, so **matching digits does not mean
matching orientation** — the verified case in SKILL.md needed `a="90"` against
a container the spawner placed at yaw 0. Set `a`, look at it in game, adjust.

To furnish such an object **exactly**, with no CE loot layered on top, give it
**no `mapgroupproto.xml` group at all** and place its contents from the
spawner JSON. No group means no loot points, which also means no unknown-type
logging, because no group builds.

---

## 8. Filenames are fixed

`cfgeconomycore.xml` registers `<ce folder>` sources for `types`, `events` and
`spawnabletypes`, which is how those can be split across extra files.
**`mapgroupproto.xml` and `mapgrouppos.xml` are loaded by fixed filename** and
have no equivalent — neither appears in `cfgeconomycore.xml` on any vanilla
map. `[unverified]` that no mechanism exists, but none is documented and none
is used in any shipped mission. **Do not split these files.**

---

## 9. Diagnostics

`cfgeconomycore.xml` ships with CE logging off. Two defaults are the ones that
matter here:

```xml
<default name="log_ce_lootspawn" value="false"/>
<default name="log_ce_lootcleanup" value="false"/>
```

Setting `log_ce_lootspawn` to `true` logs what the CE actually places and is
the only direct way to confirm a loot point is live. It is verbose — turn it
on, take one restart, turn it off.

`log_missionfilewarning` defaults to `true`, which is what surfaces unknown
proxy types and other mission-file faults in the RPT. Leave it on.
