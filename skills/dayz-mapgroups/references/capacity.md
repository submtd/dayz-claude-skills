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

## Saturation: capacity against `types.xml`

Divide a usage's `nominal` total in `types.xml` by its capacity here and you
get a rough pressure reading — how hard the CE is trying to fill those points.

```
vanilla Livonia            Clan Wars Livonia
usage          cap   nom  sat     cap   nom  sat
Village      13939  4807  34%   12944  2929  23%
Industrial    9204  3784  41%    8599  2160  25%
Farm          4694  2750  59%    4392  1954  44%
Military      1677  2559 153%    1658  3015 182%
Hunting       1256  1296 103%    1238  2007 162%
Police         333   636 191%     324   813 251%
Town           248  1666 672%     248   621 250%
Medic          429   617 144%     422   420 100%
```

**Saturation above 100% is normal and is not an error.** Both sides
over-attribute: a building with three usages is counted in three columns, and
an item with three usages is too. Military at 153% on untouched vanilla is the
baseline, not a defect.

What the number is good for:

- **Comparison against the same usage on vanilla.** Clan Wars' Police at 251%
  against vanilla's 191% says Police points are under materially more pressure
  than Bohemia intended — which is the intended effect of that server's
  retune, and worth knowing before adding more.
- **Spotting headroom.** Village at 23–34% and Office/School at 12–16% are
  where thinning costs least, because the CE was never filling those points.
- **Spotting the floor.** A usage whose capacity is small (Town at 248,
  Firefighter at 57) will swing wildly on small edits. Treat percentage
  changes there with suspicion.

## Zero capacity with non-zero nominal

**This is the check that finds real bugs.** If a usage has `nominal` allocated
in `types.xml` but no placed group carries that usage, those items have no
route into the world from building loot.

Two usages have **zero `mapgroupproto` capacity on every vanilla map** and are
fine: `ContaminatedArea` and `Special`. They are filled by the event system —
`cfgEffectArea.json` areas and the `StaticContaminatedArea` /
`ContaminatedArea_Dynamic` events — not by building loot points. Their items
are gas-zone exclusives by design.

**So zero capacity is only a fault when the event route is also gone.** The
check has to span four files:

| Usage has nominal but no group capacity | …and events off? | Verdict |
|---|---|---|
| `ContaminatedArea` | events active | normal — gas-zone loot |
| `ContaminatedArea` | `cfgEffectArea.json` `Areas: []` **and** `StaticContaminatedArea` `<active>0</active>` | **stranded — cannot spawn** |
| any building usage | n/a | **stranded** |

### Worked example — a live stranded population

Clan Wars Livonia removed all static and dynamic gas zones as a design
decision (no gas means no NBC gear, which means pox items serve no purpose).
`cfgEffectArea.json` is `{"Areas": [], "SafePositions": []}` and
`StaticContaminatedArea` carries `<nominal>0</nominal>` and `<active>0</active>`.

Eight `types.xml` entries still carry `ContaminatedArea` as their **only**
usage, totalling **63 nominal that cannot spawn anywhere**:

| Type | nominal | vanilla Livonia nominal |
|---|---|---|
| `M4A1` | **24** | 1 |
| `Mag_M14_10Rnd` | 16 | 16 |
| `Mag_M14_20Rnd` | 10 | 10 |
| `Attack2Bag_Green` / `_Ttsko` / `_Yeger` | 3 each | 3 each |
| `AK_Suppressor` | 2 | 2 |
| `M4_Suppressor` | 2 | 2 |

The `M4A1` line is the tell: vanilla ships it at nominal 1 as a gas-zone
exclusive, and it was deliberately raised to 24 — an intent to make the rifle
common that the usage flag silently defeats. The others are vanilla values
left in place after the areas went away.

**Fixes, in order of least surprise:**

1. **Give the type a real usage** — `Military` for the rifle and suppressors,
   `Military`/`Town` for the magazines. This is the only change that makes
   them spawn, and it costs real capacity, so budget the nominal (see the
   `dayz-types` skill).
2. **Or set `nominal` to 0** and leave the usage, if they were meant to go
   with the gas zones. Keeps the entry available for a later re-enable.
3. **Do not** add a `ContaminatedArea` group to `mapgroupproto.xml` to soak
   them up. That re-creates gas-zone loot in ordinary buildings and is not
   what the usage means.

`scripts/validate.py` reports this class of fault as
`stranded-usage`.
