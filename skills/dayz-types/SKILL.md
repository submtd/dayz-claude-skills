---
name: dayz-types
description: Use when working with a DayZ server's db/types.xml or per-item central economy tuning — how much of an item exists, how long it survives, where and in which tier it spawns, disabling or adding an item, base and storage decay, loot budget and server performance — or when an item does not spawn, will not stop spawning, or vanished from loot over time.
---

# DayZ db/types.xml

The per-item central economy table: one `<type>` entry per classname, ~1,970
of them per map. Vanilla source: `BohemiaInteractive/DayZ-Central-Economy`.

**Unlike `globals.xml`, this file is different on every map.** Chernarus,
Livonia and Sakhal ship different entries, different value tiers and different
nominals. Diff against the matching map or you will generate false positives
on every line.

**These servers are Xbox on Nitrado.** No mods; `init.c` is inert. See the
`dayz-cfggameplay` skill for what that rules out.

## Never answer from memory

Every element name, unit, default and tier list **must** come from
`references/keys.md`. An agent asked ten routine questions about this file
answered fluently and was wrong in ways that would have shipped:

- Asked which `value` tiers Livonia has, it said **"Tier1 through Tier4…
  possibly Tier5."** Livonia ships **Tier1–Tier3 only**. A `Tier4` copied from
  a Chernarus entry is silently ignored and the item never spawns.
- It invented a `vehiclesparts` category. The real one is `lootdispatch`.
- It described `cost` as spawn priority and omitted that the engine uses the
  same number for **cleanup** priority.
- It called `<category>` and `<usage>` effectively mandatory. **358 vanilla
  Livonia types have no `<category>` at all.**

The fluency is the problem. Nothing above reads as a guess.

## The rule that matters most

**Total `nominal` across the file is a server performance budget, not a loot
dial.** Every point of nominal is an object the server may have to track.

This is the operator's stated reason for how Clan Wars is tuned, and it is the
frame to bring to any "can we add more X" request. Clan Wars holds **26% fewer
objects than vanilla Livonia while carrying 26% more weapons**:

| | vanilla Livonia | Clan Wars | |
|---|---|---|---|
| **Total nominal** | 13,468 | **9,976** | **−26%** |
| Active types (nominal > 0) | 1,021 | 604 | −41% |
| weapons | 2,730 | **3,435** | **+26%** |
| clothes | 3,979 | 1,997 | −50% |
| food | 562 | 119 | −79% |
| tools | 4,156 | 3,078 | −26% |

> "The goal is for the server to feel like it has boosted loot, while actually
> having less total items than vanilla. This is strictly a server performance
> call." — operator

The move is **concentration, not addition**: fewer distinct types, higher
nominal each. Raising a weapon's nominal is paid for by cutting clothing
variants nobody looks at. `scripts/validate.py --budget` prints this table for
any mission; run it before and after any nominal change.

## Things that are not what they look like

- **`count_in_cargo="1"` will make an item stop spawning.** Hoarded copies
  count toward `nominal`, so once players stockpile it the CE sees the target
  met and places no more in the world. This is the real cause of "the item
  vanished from loot after a few weeks." **Operator-confirmed on these
  servers** — not folklore. Same applies to `count_in_hoarder` and
  `count_in_player`. See `references/keys.md`.
- **`crafted="1"` stops an item spawning entirely.** It marks the type
  craft-only and the CE will not place it, whatever `nominal` says.
  **Operator-confirmed.** Vanilla agrees: every Chernarus type carrying the
  flag sits at `nominal 0`. Livonia has one that does not — `Firewood`,
  `crafted="1"` with a non-zero nominal, so it never spawns. Counts in
  `references/keys.md`.
- **`quantmin`/`quantmax` are percentages, not counts.** `100` means a full
  magazine, not 100 rounds. **[source]** `CEItemProfile::GetQuantityMin()`
  returns a float `0.0`–`1.0`. `-1` on both means "no quantity roll."
- **`restock` is not a respawn timer, it is the opposite of `lifetime`** —
  the idle period before the type is *allowed* to respawn once needed.
  **[source]** `centraleconomy.c:762`.
- **`cost` is priority for cleanup as well as respawn.** **[source]**
  `centraleconomy.c:764`. Vanilla leaves it at `100` on nearly everything and
  the operator has never moved it. Treat it as leave-alone.
- **A type name absent from vanilla `types.xml` is not invalid.** Many real
  classnames ship with no vanilla entry and work once added. Do not "correct"
  or delete an unfamiliar name. See `references/classnames.md`.
- **`cfgspawnabletypes.xml` is not required for an item to spawn.** It only
  controls attachments and cargo. **Operator-confirmed.** An item with no
  entry there still spawns, bare.
- **A type in `cfgignorelist.xml` is despawned, not merely untracked.** Its
  `types.xml` entry is dead weight whatever the values say. Clan Wars ignores
  all four `PartyTent*` deliberately — **they are a known source of server
  lag and are not allowed to exist** — while `types.xml` still carries entries
  for them. That overlap is intentional; leave it.
- **`lifetime` is clamped to `[3, 316224000]`** (3 seconds to 10 years).
  **[source]** `centraleconomy.c:314`. `lifetime 0` appears only on static map
  objects — `Land_*_DE` and `StaticObj_*_DE` wrecks, containers and
  roadblocks. Per-map counts in `references/keys.md`.
- **`lootdispatch` is a category, not a mechanism you configure here.** 174
  vanilla Livonia types use it, all vehicle doors and panels. It is how parts
  reach `<dispatch>` proxies on wrecks — see
  `dayz-globals/references/cross-file.md`.
- **Vanilla violates its own invariants.** `Crossbow_Black` ships
  `quantmin 80` / `quantmax 0` on Livonia and Sakhal; `BatteryCharger` ships
  `min 18` > `nominal 13` on Sakhal. These are Bohemia's bugs, present
  upstream. Never treat a shipped vanilla file as a schema reference.

## Routing

| Task | Read |
|---|---|
| What an element means, its unit, its default | `references/keys.md` |
| Which files a change here also touches | `references/cross-file.md` |
| Adding an item vanilla does not list | `references/classnames.md` |
| Checking a file before shipping | `scripts/validate.py` |

```sh
scripts/validate.py <mission>/db/types.xml            # errors, warnings, notes
scripts/validate.py --budget  <mission>/db/types.xml  # total nominal by category
scripts/validate.py --verbose <mission>/db/types.xml  # + normal-in-vanilla notes
```

It checks, in this order: XML parse and root element; the seven required
scalars, `<flags>` attributes and duplicate names; `crafted` vs `nominal`,
`min` vs `nominal`, the quantity pair, the lifetime clamp; every
`usage`/`value`/`tag`/`category` name against `cfglimitsdefinition.xml`; and
then `cfgignorelist.xml`, `cfgspawnabletypes.xml` and `db/events.xml`. It does
**not** check anything in `mapgroupproto.xml`, so it cannot tell you a
declared usage matches no real loot point — and it cannot check a classname.

It stays silent on a coherent config: vanilla Chernarus reports `OK` and
nothing else. It **does not** flag a type name vanilla omits, because unknown
is not invalid, and it downgrades Bohemia's three shipped defects to a tagged
warning so an untouched mission still exits 0.

Paths are relative to this skill's directory; run it from there or use an
absolute path.

## Diagnosing "the item does not spawn"

In the order these actually bite, not the order they seem likely:

1. **Wrong tier for the map.** `Tier4` on Livonia is the single most common
   silent kill. Livonia is Tier1–3; Chernarus and Sakhal are Tier1–4.
2. **`nominal` is 0.** The standard way to disable an item — check it was not
   already disabled on purpose.
3. **A `usage`, `value`, `tag` or `category` name not in
   `cfglimitsdefinition.xml`** for that map. Silently dropped.
4. **`crafted="1"`.** Craft-only; the CE will not place it at all.
5. **The type is in `cfgignorelist.xml`.** It will be despawned on sight.
6. **No `<usage>` at all**, on an item you expect in building loot. It can
   then only arrive as cargo, via an event, or from `cfgspawnabletypes.xml`.
7. **`count_in_*` satisfaction** — see the trap above. Suspect this when the
   item *used to* spawn.
8. **Classname is genuinely wrong.** Real, but rarer than it feels, and you
   cannot confirm it from any file in the tree — see
   `references/classnames.md`.

`scripts/validate.py` catches 1–6 mechanically.

## Deploying and verifying a change

**Deploying the file and waiting for the next restart is enough.**
**[operator]** No manual restart, no storage wipe. Servers restart every 2
hours, so that is the worst-case wait before a change is live. (On Clan Wars
the deploy trigger is *publishing a GitHub Release* — a tag alone ships
nothing.)

**How fast it becomes visible depends on which way you moved the number.**
**[operator]**

- **Raising `nominal` shows up quickly.** The CE has a deficit to fill and
  spawns into it.
- **Lowering `nominal` shows up slowly.** It stops new placement; the surplus
  has to age out through each copy's `lifetime` first, and anything in
  persistent storage never ages out at all. Same mechanism as `nominal 0`.

**So do not judge a reduction after one restart.** An agent that checks too
early will conclude the edit failed and start "fixing" a config that is
working. If a cut must take effect now, the lever is `cfgignorelist.xml`,
not a smaller nominal.

## Diagnosing "the item will not go away"

Setting `nominal 0` stops *new* placement. It does not remove what already
exists — those copies run out their `lifetime` first, and persistent storage
does not expire on a restart. To remove an item now, add it to
`cfgignorelist.xml`; that despawns it.

## House conventions

- **Splice, never parse-and-reserialize.** These files have meaningful key
  order and indentation, and Clan Wars' was hand-edited item by item through
  Claude Code — **there is no generator to re-run and the file is the source
  of truth**. A round trip makes the diff unreviewable and destroys the only
  record of intent.

  For one or a few types, edit the `<type>` block in place with a targeted
  string replacement. For a bulk change across many types — the realistic
  case, e.g. the 22 base-part lifetimes — scope the edit to the types you
  mean by name, rather than pattern-matching a value across the file:

  ```python
  import re, pathlib
  BASE = ["Barrel_Blue", "CarTent", "Fence", "LargeTent", "Watchtower"]  # etc.
  p = pathlib.Path("db/types.xml"); s = p.read_text()
  for name in BASE:
      block = re.search(rf'(<type name="{re.escape(name)}">.*?</type>)', s, re.S)
      assert block, name                      # fail loudly on a typo'd name
      new = re.sub(r"<lifetime>\d+</lifetime>",
                   "<lifetime>604800</lifetime>", block.group(1))
      s = s.replace(block.group(1), new)
  p.write_text(s)
  ```

  A blind `sed s/3888000/604800/g` would also hit any unrelated type that
  happens to share the value. **Then read the values back** and diff — a key
  at the wrong nesting depth still parses, and `git diff --stat` should show
  exactly the line count you intended.
- **Keep the element order** vanilla uses: `nominal`, `lifetime`, `restock`,
  `min`, `quantmin`, `quantmax`, `cost`, `flags`, then `category`, `usage`,
  `value`, `tag`.
- **One Life tracks upstream `master` but is deliberately frozen** at the
  vanilla reset. Upstream has since moved (mossy ghillies enabled, `Tier4`
  added to `PoliceVest`, `deloot` flag changes). **Flag the gap so it is
  visible; never auto-apply it.** Adopting an upstream value is an operator
  decision each time.
- **State the before and after in the commit body**, per value. These are
  economy numbers someone will diff later.

## Known live-server state

Recorded so it is not "fixed" by accident. See also the root `CLAUDE.md`.

- **One Life base part lifetimes are vanilla `3888000` (45 days)** on all
  three maps, while `globals.xml` sets `FlagRefreshMaxDuration` to 7 days.
  The flag only postpones these lifetimes, so the shortened refresh is close
  to inert. **The fix lives in this file.** Offer it; do not apply it unasked.
  Clan Wars already did exactly this — 35 types at `604800`.
- **Clan Wars' broad `7200` lifetime is not tied to the 2-hour restart
  cadence.** It looks like it is and it is not — the operator confirmed there
  is no such rationale. Do not repeat that story.
- **Clan Wars sets `quantmin`/`quantmax` to `100`/`100` on all 1,979 types**,
  including items with no quantity at all, where vanilla uses `-1`. This is a
  deliberate blanket pass and has caused no problems. Do not "clean it up."
