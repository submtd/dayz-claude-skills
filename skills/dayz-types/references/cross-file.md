# What `types.xml` depends on, and what depends on it

`types.xml` is the common dependency of the mission tree. More files point at
it than at anything else, and none of the links error when broken.

Quick map:

| The other file | Direction | What breaks silently |
|---|---|---|
| `cfglimitsdefinition.xml` | types → it | An undefined `usage`/`value`/`tag`/`category` is dropped |
| `cfgignorelist.xml` | it → types | Listed types are **despawned**; their entry is dead |
| `db/globals.xml` | pairs | `FlagRefresh*` only postpones lifetimes set here |
| `cfgspawnabletypes.xml` | it → types | Attachments only — **not** required to spawn |
| `db/events.xml` | it → types | `<child type=...>` naming a missing type |
| `mapgroupproto.xml` | types → it | `usage`/`value`/`tag`/`category` must match real loot points |
| `cfgeconomycore.xml` | registers | A custom types file not registered is never read |

---

## `cfglimitsdefinition.xml` — the name registry

Every `<category>`, `<usage>`, `<value>` and `<tag>` name used in `types.xml`
must be declared in that map's `cfglimitsdefinition.xml`. An undeclared name
is dropped with no error, and if it was the type's only usage or value, the
item stops spawning.

**The tier lists differ by map — Livonia has no `Tier4`.** See
`keys.md`. This is the single most common silent failure in the file and the
reason cross-map copy-paste is dangerous.

`cfglimitsdefinitionuser.xml` defines *shorthand groups* (`Tier123`,
`TownVillage`) for use in `mapgroupproto.xml`. **Those group names are not
valid inside `types.xml`** — a type uses the individual flags. Do not "tidy"
three `<value>` lines into a `Tier123`.

Adding a new flag is legitimate and is the basis of the POI technique in
`classnames.md`: declare it in `cfglimitsdefinition.xml`, then use it on both
the type and the loot point.

## `cfgignorelist.xml` — despawns, and wins

**Types on the ignore list are despawned from the game**, not merely left
untracked by the CE. **[operator]** A `types.xml` entry for an ignored type
has no effect whatever its values say.

This makes the ignore list the tool for **removing an item that already
exists**. Setting `nominal 0` stops new placement but leaves current copies to
run out their lifetime, and persistent copies never expire.

Clan Wars ignores all four `PartyTent*` while `types.xml` still carries
entries for them at the 7-day lifetime. **That overlap is intentional — party
tents are a known source of server lag and are not allowed to exist.**
**[operator]** Do not "resolve" it by deleting either side.

The validator reports the overlap as a note, because the same shape can also
mean someone disabled an item in one file and forgot the other.

## `db/globals.xml` — base decay is a pair

`FlagRefreshFrequency` and `FlagRefreshMaxDuration` **only postpone the
lifetimes set in this file.** A flag cannot make a base part live longer than
its `types.xml` lifetime allows; it only keeps resetting the clock, and only
for as long as `FlagRefreshMaxDuration`.

So base decay speed is set here, in the ~22 vanilla types at `3888000`
(45 days), not in `globals.xml`.

**One Life's live state:** `FlagRefreshMaxDuration` was shortened to 7 days to
clear abandoned bases, but the part lifetimes were left at vanilla 45 days, so
the change is close to inert. **The fix belongs in this file.** Offer it; do
not apply it unasked, and do not revert the `globals.xml` value as though it
were drift. Clan Wars shows the working version — 35 types at `604800`.

See `dayz-globals/references/cross-file.md` for the `globals.xml` side.

## `cfgspawnabletypes.xml` — attachments only

**Not required for an item to spawn.** **[operator]** It controls what a
spawned item comes with: attachments, cargo, and `<damage>`.

Two consequences:

- A new type with no entry here still spawns — just bare. Adding a type is one
  edit, not two. Clan Wars happens to have entries for all 11 of its added
  types, which makes the files look like they require each other.
- **Any `<damage>` entry here overrides `LootDamageMin`/`LootDamageMax`** from
  `globals.xml`, including `0.0/0.0`. That is how Clan Wars gets pristine loot
  while One Life gets damaged. See `dayz-globals`.

An entry here naming a type with no `types.xml` entry is harmless but dead —
vanilla ships 10–14 of them per map (`AugOptic`, `Glowplug`, `ZmbM_Mummy`).
The validator notes them without complaint.

## `db/events.xml` — event children

Dynamic events spawn named types via `<child type="...">`. A child naming a
type with no `types.xml` entry spawns nothing. All four live missions are
clean here.

Event-spawned items bypass `nominal` placement but **not** `lifetime` — an
event item still despawns on the clock set here.

## `mapgroupproto.xml` — where loot points live

The other half of `usage`, `value`, `tag` and `category`. A type can only
appear in a building whose loot points carry matching flags, so a type's flags
are only meaningful relative to what the map actually has. A valid,
declared usage that no building on the map uses produces exactly the same
silence as an undeclared one.

The `<dispatch>`/`<container>` split is documented in
`dayz-globals/references/cross-file.md`. The `lootdispatch` **category** in
this file is the type-side of the dispatch mechanism.

## `cfgeconomycore.xml` — registration

`types.xml` is registered here, and so is any additional types file. A custom
file that is not registered is never read and produces no error.

The registration is a `<ce folder="...">` block, sibling to `<classes>` and
`<defaults>`, listing each extra file and its kind. A working console example
from `scalespeeder/DayZ-112-LIVONIA-Trader-Store-and-Truck-XML-Files`:

```xml
<ce folder="db"><!-- extra types files that are added for trader -->
    <file name="extra_types.xml" type="types" />
    <file name="colour_Spawnabletypes.xml" type="spawnabletypes" />
    <file name="trader-truck-spawnabletype.xml" type="spawnabletypes" />
    <file name="trader-truck-event.xml" type="events" />
</ce>
```

`folder` is the directory the listed files sit in, relative to the mission
root (`db` above, since that is where the snippets were dropped). `type` is
the CE file kind — `types`, `spawnabletypes`, `events`.

**None of these four missions has a `<ce>` block** — everything lives in the
single `db/types.xml`. So this is the shape to write if a snippet ever calls
for one, not a pattern already in use here.

**[unverified]** what happens when a registered extra file repeats a `<type
name=...>` that `db/types.xml` already defines — whether it overrides, merges
or duplicates. Published snippets are written as though it overrides, but
nobody has confirmed it on these servers. Prefer editing `db/types.xml`
directly, which is what both projects do.

These missions keep everything in the single `db/types.xml`. Splitting into a
`custom/` types file is possible but adds a registration step and a second
place to look — Clan Wars already has three orphaned `custom/` JSON files that
nothing references, so the failure mode is live in this codebase.
