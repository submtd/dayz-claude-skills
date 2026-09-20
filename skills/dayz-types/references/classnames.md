# Adding types vanilla does not list

## The rule

**A classname missing from vanilla `types.xml` is not an invalid classname.**
Plenty of real, shipped items have no vanilla entry. Adding one makes it spawn.
**[operator]**

This cuts both ways, and the second half is the dangerous one:

- **Never delete or "correct" an unfamiliar type name.** It is probably
  deliberate, and it is probably working.
- **Never invent one.** A wrong classname fails exactly like a right one that
  is mis-tiered — silently. Nothing in the mission tree can tell you which
  you have.

**You cannot verify a classname from any source this repo has access to.**
Item classnames live in the game's `.cpp` configs, which are not in
`DayZ-Script-Diff` and not in `DayZ-Central-Economy`. Engine source settles
CE *behavior*, not the catalogue of items. Anything unverified here is settled
by one of two things only: a published list that is known to work, or the
operator testing it in game.

## Where the known-good names come from

**`github.com/scalespeeder`** — the operator's cited console-modding resource,
~251 repos of XML/JSON for PC *and console* servers, so it respects the
no-mods constraint these servers work under. **[operator]**

The relevant artefact is **`extra_types.xml`**, which appears in several
repos and is a ready-made list of valid classnames vanilla omits, e.g.
`scalespeeder/DayZ-112-LIVONIA-Trader-Store-and-Truck-XML-Files/extra_types.xml`.
Its 18 entries:

**Weapon colour variants**
`Winchester70_Green` `Winchester70_Black` `SKS_Black` `CZ527_Black`
`CZ527_Camo` `B95_Black`

**Magazine colour variants**
`Mag_AKM_Drum75Rnd_Green` `Mag_AKM_Drum75Rnd_Black`
`Mag_AK74_30Rnd_Green` `Mag_AK74_30Rnd_Black`
`Mag_AKM_Palm30Rnd_Black` `Mag_AKM_Palm30Rnd_Green`
`Mag_AK101_30Rnd_Green` `Mag_AK101_30Rnd_Black`
`Mag_CMAG_40Rnd_Green` `Mag_CMAG_30Rnd_Green`
`Mag_CMAG_40Rnd_Black` `Mag_CMAG_30Rnd_Black`

The repos are versioned by DayZ update (1.09 → 1.28). Prefer a recent one and
sanity-check against the live files rather than assuming an old snippet still
applies. The repo set is worth a dig for more than types — custom POIs, event
snippets, loadouts.

## Names in use on these servers

Clan Wars Livonia carries 11 types that exist in **no** vanilla file:

| Type | Provenance |
|---|---|
| `Winchester70_Black`, `Winchester70_Green` | scalespeeder `extra_types.xml` |
| `SKS_Black`, `CZ527_Black`, `CZ527_Camo`, `B95_Black` | scalespeeder `extra_types.xml` |
| `B95_Green`, `SKS_Green`, `CZ527_Green` | **operator-verified only** |
| `WinterMilitaryCoat_Grey` | **operator-verified only** (see below) |
| `ShippingContainerKeys_Red` | **operator-verified only** |

**All 11 spawn correctly in game.** **[operator]** The bottom five are not on
any published list — the operator's in-game confirmation is the whole of the
evidence, so do not "fix" them and do not cite them to someone else as
documented.

## The `WinterMilitaryCoat_Greay` trap

Vanilla **Livonia** `types.xml` spells it `WinterMilitaryCoat_Greay`.
Chernarus and Sakhal spell it `WinterMilitaryCoat_Grey`, and **all three
maps' `cfgspawnabletypes.xml` say `Grey`**. **[shipped]**

So Bohemia's Livonia entry is a typo against their own classname, and that
coat has never spawned on vanilla Livonia. Clan Wars renamed it to `Grey` and
it spawns. **[operator]**

Two lessons: Bohemia's shipped files are not a classname authority either, and
a one-letter difference is the entire failure.

## Recipe: adding a type

1. **Get the classname from a source that is known to work** — a published
   list, or a variant already proven on one of these servers. If neither, say
   plainly that it needs an in-game test; do not present a guess as a fact.
2. **Add the `<type>` block**, matching vanilla's element order and
   indentation. Splice it in; do not reserialize the file. Put it in
   alphabetical position — that is a **house convention for reviewable
   diffs**, not an engine requirement; nothing suggests the CE cares about
   order.

   **Starting values.** Vanilla medians for an *enabled* Chernarus type, as a
   sane default to adjust from rather than a number to copy **[shipped]**:

   | category | nominal | min | lifetime |
   |---|---|---|---|
   | clothes | 12 | 8 | 14400 |
   | weapons | 10 | 5 | 14400 |
   | tools | 40 | 24 | 14400 |
   | containers | 8 | 5 | 28800 |
   | food | 20 | 15 | 14400 |
   | explosives | 10 | 5 | 14400 |

   `min` at roughly 60% of `nominal` is the vanilla habit. `restock 0`,
   `cost 100`, and `quantmin`/`quantmax` `-1`/`-1` unless the item has a real
   quantity — except on Clan Wars, which uses `100`/`100` throughout.
3. **`crafted="0"`**, or it will not spawn at all.
4. **Use only tiers and flags that map declares** —
   `cfglimitsdefinition.xml`. Remember Livonia has no `Tier4`.
5. **Budget the `nominal`.** Every point is an object the server tracks. If
   this is an addition rather than a replacement, say what it costs and what
   could be cut — see the budget table in `SKILL.md`.
6. **`cfgspawnabletypes.xml` is optional** — add an entry only if the item
   should arrive with attachments, cargo or a specific damage range. Without
   one it spawns bare. It is **not** needed for the item to appear.
7. **Run `scripts/validate.py`**, then confirm in game after a restart.

## Recipe: high-value loot at a custom POI

**This is the main reason the colour variants matter.** **[operator]**

The problem: you build a custom bunker, or swap train containers for locked
containers, and want strong loot inside without inflating that loot everywhere
else on the map. Raising a weapon's `nominal` or widening its `usage` leaks it
across the whole map — the CE has no concept of "this one building."

The solution: **a colour variant is a CE-distinct type that is mechanically
the same weapon.** Give the variant its own custom usage flag and tag the POI's
loot points with it. The variant then spawns *only* there, and the base
weapon's economy is untouched.

1. **Declare a custom usage flag** in `cfglimitsdefinition.xml`:
   ```xml
   <usage name="Bunker"/>
   ```
2. **Add the variant to `types.xml`** with that usage and nothing else:
   ```xml
   <type name="SKS_Black">
       <nominal>6</nominal>
       <lifetime>10800</lifetime>
       <restock>0</restock>
       <min>4</min>
       <quantmin>-1</quantmin>
       <quantmax>-1</quantmax>
       <cost>100</cost>
       <flags count_in_cargo="0" count_in_hoarder="0" count_in_map="1"
              count_in_player="0" crafted="0" deloot="0"/>
       <category name="weapons"/>
       <usage name="Bunker"/>
   </type>
   ```
   Give it **no `<value>`** unless the POI's points carry a tier, and no
   second usage — a single extra usage is what leaks it back onto the map.
3. **Tag the POI's loot points** with the same usage in `mapgroupproto.xml`.
4. **Keep the base type alone.** `SKS` keeps its vanilla `Military` usage and
   its own nominal; the variant is a separate population.

Why it works: the two are separate CE types with separate targets, so the
variant's nominal is spent entirely inside the POI. Players get a distinctly
better container without the map-wide inflation.

The cost is still real — the variant's `nominal` adds to the file's total
object budget. A POI is a place to *concentrate* loot, not a free extra.

The magazine variants in `extra_types.xml` work the same way and pair
naturally with the weapon variants for a themed cache. Clan Wars does not
currently use any of the 12; they are available if a POI wants them.
