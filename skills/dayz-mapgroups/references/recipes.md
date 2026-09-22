# mapgroupproto.xml / mapgrouppos.xml — recipes

Each recipe names the files it touches. **All of them fail silently if a step
is skipped**, so work the list rather than the gist.

---

## Disable loot at one specific place

*Files: `mapgrouppos.xml` only.*

The most common real request — a clan is farming military loot from the
compound they live in, a POI has become a magnet, one building is too rich.

Because `mapgroupproto.xml` describes a building **type**, editing it hits
every instance on the map. `mapgrouppos.xml` is per-instance, so it is the
right file.

1. **Find the entries by coordinate, not by name.** `pos` is world X Y Z; X
   and Z are the map grid, Y is altitude.
   ```sh
   python3 - <<'PY'
   import re, math, pathlib
   CX, CZ, R = 5520, 8775, 200          # centre and radius in metres
   for line in pathlib.Path("mapgrouppos.xml").read_text().splitlines():
       m = re.search(r'name="([^"]+)".*?pos="([\d.-]+) ([\d.-]+) ([\d.-]+)"', line)
       if not m: continue
       x, z = float(m.group(2)), float(m.group(4))
       if math.dist((x, z), (CX, CZ)) <= R:
           print(f"{math.dist((x,z),(CX,CZ)):7.1f}m  {m.group(1)}")
   PY
   ```
2. **Decide the edge deliberately.** Sort by distance and look at where the
   cluster stops. A roadside wreck 175 m out is not part of the compound;
   including it quietly removes loot players were not complaining about.
3. **Comment out, do not delete.** Prefix the reason so the change is
   greppable and reversible:
   ```xml
   <!-- Kopa prison (loot disabled): <group name="Land_Prison_Main" pos="..." rpy="..." a="..." /> -->
   ```
4. **Check what you removed** with `scripts/validate.py . --capacity` before
   and after. A compound usually spans several usages; confirm you cut the one
   you meant. Removing the map's only prison takes `Prison` capacity to zero,
   which strands any `Prison`-only type — see `capacity.md`.
5. **The buildings stay.** They remain in the terrain `.pbo`, enterable, with
   no loot. Say so when reporting the change; people expect the building to
   vanish and it does not.

---

## Concentrate loot at a POI without inflating the map

*Files: `cfglimitsdefinition.xml`, `db/types.xml`, `mapgroupproto.xml`,
`mapgrouppos.xml`.*

The problem: you want a bunker or a cache to hold strong loot, and raising an
item's `nominal` or widening its `usage` leaks it across the whole map. The CE
has no concept of "this one building."

The solution is a **custom usage flag** plus a type that carries only that
flag. The `dayz-types` skill covers the `types.xml` side; this is the half
that lives here, **including the trap that skill's version does not cover.**

### The trap

`<usage>` sits on a `<group>`, and a group is a **building type**. Tagging
`Land_Prison_Main` with a custom usage gives it to **every prison on the map**.
"Tag the POI's loot points" only works if the loot points belong to something
that exists exactly once.

So you need one of these to be true:

| Situation | What to do |
|---|---|
| The POI uses a classname placed **exactly once** | Tag that group. Verify the count first. |
| The classname is placed many times | **Author a new prototype** under a name of your own and place it once. |
| The POI is a custom object, not terrain | Author a new prototype; pair it with an `objectSpawnersArr` entry. |

Check the count before you touch anything:

```sh
grep -c 'name="Land_Prison_Main"' mapgrouppos.xml
```

### Steps

1. **Declare the usage** in `cfglimitsdefinition.xml`:
   ```xml
   <usageflags>
       …
       <usage name="Bunker"/>
   </usageflags>
   ```
2. **Add the types** in `db/types.xml` carrying **that usage and no other**. A
   second usage is what leaks the item back onto the map. Colour variants are
   ideal here — a CE-distinct type that is mechanically the same weapon; see
   `dayz-types/references/classnames.md`.
3. **Give them no `<value>`.** Tier does not work this way — see
   `cross-file.md` rule 6. Routing is by usage alone.
4. **Author the group** in `mapgroupproto.xml`:
   ```xml
   <group name="MyBunker_Cache" lootmax="9">
       <usage name="Bunker" />
       <container name="lootFloor" lootmax="9">
           <category name="weapons" />
           <tag name="floor" />
           <point pos="0.0 0.1 0.0" range="0.40" height="1.00" />
           <!-- …one <point> per slot, up to lootmax -->
       </container>
   </group>
   ```
   Keep `height ≈ 2.5 × range`; that is what Bohemia's tooling emits.
5. **Place it once** in `mapgrouppos.xml`, and set `a` to match the object's
   orientation:
   ```xml
   <group name="MyBunker_Cache" pos="11431.0 214.1 506.7" rpy="0 0 0" a="90" />
   ```
6. **Budget it.** The variant's `nominal` adds to the mission's total object
   count, which is a server performance budget. A POI concentrates loot; it is
   not free.
7. **Validate, restart, look.** `scripts/validate.py .`, then check in game —
   `a` in particular is a look-at-it setting, not a calculate-it one.

---

## Add a custom container and control its contents exactly

*Files: `cfggameplay.json`, `mapgrouppos.xml`, and deliberately **not**
`mapgroupproto.xml`.*

For an airdrop, a locked container, a staged cache — anything placed by an
object spawner rather than the terrain.

**Two routes, and the choice is the whole decision:**

| Want | Do |
|---|---|
| CE fills it from the loot economy | spawner JSON **+** a proto group **+** a pos entry |
| It holds exactly what you place, nothing else | spawner JSON **only** — **no proto group, no pos entry** |

The second is usually what people actually mean by "a custom loot container."
With no proto group there are no loot points, so the CE adds nothing — and
there is no unknown-type logging either, because no group ever builds.

If you take the first route:

1. Register the spawner JSON in `cfggameplay.json` →
   `WorldsData.objectSpawnersArr`.
2. Add the matching `mapgrouppos.xml` entry **at the same coordinates**.
   Either file alone gives you an empty object or orphaned loot.
3. Set `a` to match the spawner's yaw, then **confirm in game** — see
   `cross-file.md` rule 7.
4. Register every `<proxy>` classname in the proto in `db/types.xml` at
   `nominal 0`, or the RPT fills with unknown-type warnings on every build.
5. Moving it later means editing **both** files. Changing one is the classic
   way to get loot floating where the container used to be.

---

## Thin loot points for server performance

*Files: `mapgrouppos.xml` only.*

Dense towns are a known cause of stuttering: every loot point is an entity the
server maintains and streams. Removing pos entries reduces that load without
removing a single building.

**Set expectations honestly.** Clan Wars ran this at scale — 466 entries
removed across Nadbor and Topolin, roughly 3% of map-wide capacity — and the
operator's verdict was that **it helped a little**. `[operator]` It is a real
lever with a modest effect, not a fix. Say that rather than promising more.

1. **Target the densest clusters**, found by coordinate sweep, not by
   guesswork about which town "feels" busy.
2. **Take clutter before buildings.** Entries with `lootmax ≤ 2` that are not
   a house, barn or camp — sheds, vehicle wrecks, greenhouses, bus stops, dry
   toilets, well pumps, roadblock tables. Highest entity count per point of
   player-visible loot.
3. **If that is not enough, halve a category rather than emptying a street.**
   Sort the candidates by classname **then** position and drop every other
   one, so the cut spreads across variants and across the town. Emptying one
   street is noticeable; a diffuse 50% cut is not.
4. **Protect the usages that are already tight.** Run
   `scripts/validate.py . --capacity` first. Village/Office/School typically
   sit at 12–35% saturation and have room; Military and Police are often above
   100% and should be left alone. Report the per-usage delta in the commit.
5. **Deletions only, no line rewritten** — it keeps the diff readable and the
   re-merge tractable.
6. **Record the running fork size.** Bohemia ships terrain updates that
   rewrite `mapgrouppos.xml`; every deletion is a manual re-merge later. State
   the cumulative count in the commit message so the next person knows what
   they are taking on.

---

## Swap a proxy item across a whole map

*Files: `mapgroupproto.xml`, and check `db/types.xml`.*

To remove an item category from fixed placements — e.g. retiring gas-related
items along with the gas zones:

1. **Find every proxy of that type.**
   ```sh
   grep -n '<proxy type="Grenade_ChemGas"' mapgroupproto.xml
   ```
2. **Replace in place, preserving `pos`, `rpy` and `dechance`.** The offsets
   are authored against the model; changing the item does not change where it
   sits.
3. **Check the replacement is registered** in `db/types.xml`. If it is a real
   loot item it already is; if it is scenery, add it at `nominal 0`.
4. **Check the old type for orphans.** If nothing references it any more,
   decide whether its `types.xml` entry should go to `nominal 0` or stay.
5. **Then check the usage flags.** Retiring a mechanic usually strands types
   that carried its usage — `scripts/validate.py` reports these as
   `stranded-usage`, and `capacity.md` works through a live case where 63
   nominal was left with nowhere to spawn.
