# Loot capacity — the number to reason with

"How much loot can spawn in this building?" has two plausible answers in
`mapgroupproto.xml` and they disagree badly. Picking the wrong one produces
confident, wrong reassurance about whether a change is safe.

```xml
<group name="Land_Garage_Row_Small" lootmax="6">   ← 6
    <container name="lootFloor"   lootmax="4">    ┐
    <container name="lootshelves" lootmax="4">    ┘ ← 12
```

**The group `lootmax` is the ceiling the engine enforces. Use it.** The
container sum describes a capacity the engine never allows.

This is not an edge case. Containers exceed the group cap on:

| | over-advertising groups | group ceiling | container sum | gap |
|---|---|---|---|---|
| vanilla Chernarus | 160 of 269 placed | 46,143 | 67,062 | +45% |
| vanilla Livonia | 130 of 240 | 24,079 | 33,277 | +38% |
| vanilla Sakhal | 167 of 304 | 37,292 | 53,119 | +42% |
| Clan Wars Livonia | 129 of 237 | 22,645 | 31,563 | +39% |

**Historical note.** Two Clan Wars commits quote per-usage capacity using
different rollups and one warns against diffing them
(`8873406` "loot slots" vs `fbbcf66` "loot capacity"). Neither is the group
ceiling throughout. **Numbers quoted in commits before this skill are not
reproducible with `scripts/validate.py --capacity` and should not be treated
as a baseline.** Re-measure rather than diffing against them.

## Computing it

```
capacity(map) = Σ over mapgrouppos entries:
                  group.lootmax  if set, else <defaults> group lootmax (6)
```

`scripts/validate.py <mission> --capacity` prints this, per usage and in
total, for any mission tree.

## Per-usage capacity over-attributes — use it for deltas only

A group with three `<usage>` tags contributes its **full** capacity to all
three, because any of the three pools may fill those same points. So per-usage
figures sum to far more than the map's real capacity and are **not** absolute
counts.

They are still the right tool for before/after comparison, which is what you
actually need when thinning or retuning: *"this change costs Village 995 and
leaves Military untouched"* is a sound claim from these numbers.

## Capacity from these files is a lower bound, never a total

**`areaflags.map` grants usage by map area, independently of any building's
`<usage>`.** `[operator]` It carries military, hunting, contaminated and other
area flags alongside the loot tiers. Polana on Livonia is mostly ordinary
houses and spawns military loot because the area says so — none of which is
visible in `mapgroupproto.xml` or `mapgrouppos.xml`.

So every figure in this file is **at least** the real capacity and usually
less. Two independent reasons it is not a total:

1. **The raster adds usage** that these files never mention, and it is binary
   — nothing here can read it.
2. **Per-usage columns over-attribute**: a group with three `<usage>` tags
   contributes its full capacity to all three, because any of the three pools
   may fill those same points.

**What that rules out.** You cannot use these numbers to prove that a usage
has nowhere to spawn, however tempting the arithmetic looks. A usage carrying
`nominal` in `types.xml` with zero capacity here is **not** evidence its loot
is stranded; the raster may be granting it across half the map.
`scripts/validate.py` reports the situation as a note and says so explicitly.
Confirm in game before acting on it.

**What they are still good for.** Before/after comparison of a change you made
to these files. The raster contribution is a constant across such a
comparison, so *"this thinning pass costs Village 995 and leaves Military
untouched"* is a sound claim even though "Village capacity is 12,944" is not a
complete one.

## Saturation: a pressure reading, not a measurement

Dividing a usage's `nominal` total in `types.xml` by its capacity here gives a
rough sense of how hard the CE is pushing against the points these files
define.

```
vanilla Livonia            Clan Wars Livonia
usage          cap   nom  sat     cap   nom  sat
Village      13939  4807  34%   12944  2929  23%
Industrial    9204  3784  41%    8599  2160  25%
Military      1677  2559 153%    1658  3015 182%
Police         333   636 191%     324   813 251%
Town           248  1666 672%     248   621 250%
```

**Saturation above 100% is normal and is not an error.** Both sides
over-attribute, and the capacity side is a lower bound besides. Military at
153% on untouched vanilla is the baseline, not a defect.

Use it for two things only:

- **Comparison against the same usage on vanilla.** Clan Wars' Police at 251%
  against vanilla's 191% says Police points are under more pressure than
  Bohemia intended — worth knowing before adding more.
- **Spotting headroom.** Village at 23–34% and Office/School at 12–16% are
  where thinning costs least.

Treat small-capacity usages (Town at 248, Firefighter at 57) with suspicion:
percentages swing wildly and the raster's unseen contribution is
proportionally largest there.
