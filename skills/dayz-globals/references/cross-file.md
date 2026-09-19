# globals.xml — the cross-file pairs

Almost nothing in `globals.xml` works alone. Each section below is a pair:
changing one side without the other produces **no error and no result**, which
is the characteristic way time gets lost here.

---

## Loot condition: `cfgspawnabletypes.xml` wins

`LootDamageMin` / `LootDamageMax` set the damage roll for every item the CE
spawns — **unless that item has a `<damage>` entry in
`cfgspawnabletypes.xml`.**

**Any `<damage>` entry wins, including `0.0/0.0`.** There is no "zero means
fall through." A per-item entry takes that item out of `globals.xml` control
permanently.

That gives three usable configurations:

| Goal | How |
|---|---|
| Uniform condition, one control point | **Strip all `<damage>` entries** from `cfgspawnabletypes.xml`, set `LootDamage*` in `globals.xml` |
| Worn loot generally, specific items pristine | Leave `globals.xml` at your worn range; give the exceptions a `0.0/0.0` entry |
| Pristine everywhere | Either strip the entries, or set them all to `0.0/0.0` |

**Prefer stripping over zeroing.** Setting every entry to `0.0/0.0` produces
pristine loot today but permanently removes those items from `globals.xml`
control — you lose the single knob. Stripping keeps `globals.xml` as the one
place condition is decided.

### Damage as a single-use gate

Item damage is also a **durability budget**. An item spawned at `0.8` (badly
damaged) ruins after one use. That makes damage a way to build single-use
items out of ordinary ones.

Clan Wars uses this deliberately. Its `cfgspawnabletypes.xml` has had 64 of
Livonia's 66 `<damage>` entries stripped, leaving exactly two:

```xml
<damage min="0.8" max="0.8" />   <!-- PunchedCard -->
<damage min="0.8" max="0.8" />   <!-- ShippingContainerKeys_Red -->
```

Both are Livonia bunker puzzle items. A punched card opens the bunker **once**;
a red key opens the shipping container **once**. They spawn badly damaged so
that using them destroys them.

Vanilla Livonia ships `ShippingContainerKeys_Red` at `0.0/0.0`, so this is a
deliberate change, not a missed strip. **Do not "clean up" those two entries** —
they are the mechanic.

### Condition scale

| Damage | Condition |
|---|---|
| `0.0` | Pristine |
| `0.25` | Worn |
| `0.8` | Badly damaged |
| `1.0` | Ruined |

**[unverified]** The badly-damaged → ruined boundary is not established.

---

## Base decay: `FlagRefresh*` needs `types.xml` lifetimes

A territory flag's only job is to **postpone the lifetimes set in
`db/types.xml`**. So `FlagRefreshFrequency` and `FlagRefreshMaxDuration` mean
nothing until you know what lifetimes they are acting on.

- `FlagRefreshFrequency` — how often the flag bumps nearby item lifetimes.
- `FlagRefreshMaxDuration` — how long the refresher runs before stopping.
- **Re-raising the flag resets the full `MaxDuration` clock.**

**Fast cleanup of abandoned bases needs both:** short lifetimes on base parts
*and* a short flag duration. Short lifetimes alone means active players lose
their bases; a short flag duration alone does nothing.

### Worked example — Clan Wars, which is coherent

| | Value | |
|---|---|---|
| `types.xml` lifetime, `Fence` / `Watchtower` / tents / containers | `604800` | 7 days |
| `FlagRefreshFrequency` | `432000` | 5 days |
| `FlagRefreshMaxDuration` | `1209600` | 14 days |

Untended, a base part dies in a week. A raised flag bumps it at day 5 and day
10, and the refresher stops at day 14. Stop showing up and the base is gone
inside a week; maintain the flag and it persists. That is the intended
mechanic on a server built around base raiding.

### Counter-example — One Life, which is not

| | Value | |
|---|---|---|
| `types.xml` lifetime, base parts | `3888000` | **45 days** (vanilla) |
| `FlagRefreshMaxDuration` | `604800` | 7 days |

`FlagRefreshMaxDuration` was shortened from vanilla's 40 days to 7 to clean up
abandoned bases faster — but the 45-day lifetimes it acts on were left at
vanilla. A 7-day refresher on a 45-day lifetime is close to inert; bases
persist roughly 45 days either way.

**This is a known artifact, not drift.** The goal was real and the lever was
wrong. Do not silently revert it to vanilla, and do not repeat the shape of the
mistake. The fix is to shorten the `types.xml` lifetimes and then set
`FlagRefreshMaxDuration` to a sensible multiple of `FlagRefreshFrequency`. The
operator intends to revisit it — offer, do not apply unasked.

### Checking the pair

```sh
python3 - <<'EOF'
import re, pathlib
t = pathlib.Path("db/types.xml").read_text()
for name in ("Fence", "Watchtower", "TerritoryFlag", "SeaChest",
             "WoodenCrate", "Barrel_Blue", "MediumTent", "LargeTent", "CarTent"):
    m = re.search(rf'<type name="{name}">(.*?)</type>', t, re.S)
    if m:
        lt = re.search(r'<lifetime>(\d+)</lifetime>', m.group(1))
        if lt:
            s = int(lt.group(1))
            print(f"{name:<16} {s:>9} = {s/86400:.1f} days")
EOF
```

Compare the result against `FlagRefreshMaxDuration`. If the lifetimes are much
larger than the flag duration, the flag setting is doing nothing.

---

## Infected density: the cap is not the lever

`ZombieMaxCount` is a **map-wide ceiling**. It spawns nothing. Density comes
from `env/zombie_territories.xml`, where each zone carries:

- `smin` / `smax` — static infected count range
- `dmin` / `dmax` — dynamic infected count range

`AnimalMaxCount` works the same way against the animal territory files.

**Because infected only populate near players, an empty region has none**, so
the cap rarely binds at low population. It bites when players are spread widely
enough to have many zones live at once — and then it clips zones silently, with
no log line and no error.

### The diagnostic

Sum `dmax` across all zones and compare to `ZombieMaxCount`:

```sh
python3 - <<'EOF'
import re, pathlib
t = pathlib.Path("env/zombie_territories.xml").read_text()
d = [int(x) for x in re.findall(r'dmax="(\d+)"', t)]
print(f"zones: {len(d)}   sum(dmax): {sum(d)}")
EOF
```

Measured on live servers:

| Server | Zones | Σ `dmax` | `ZombieMaxCount` |
|---|---|---|---|
| Clan Wars Livonia | 328 | 2,582 | 1000 |
| One Life Chernarus | 768 | 5,205 | 1000 |

Both define 2.5–5× more infected than the cap allows. **If the sum is far above
the cap, the cap is deciding your density at high population, not your zone
tuning** — and edits to zone values will not show up until you raise it.

Raise the cap only with server performance in mind; infected are the usual
cause of server FPS loss. **[unverified]** What a Nitrado Xbox instance can
actually carry has not been measured.

---

## `LootProxyPlacement` and `mapgroupproto.xml`

`LootProxyPlacement: 1` enables the `<dispatch>` mechanism in
`mapgroupproto.xml`. It is narrower than "let containers hold loot."

A building group can carry two independent loot systems:

```xml
<group name="Land_Underground_Storage_POX" lootmax="10">
    <container name="lootFloor" lootmax="10">
        <category name="weapons" />
        <point pos="-2.667725 0.745178 0.938353" range="0.34" height="0.85" />
    </container>
    <dispatch dechance="1.000000">
        <proxy type="M67Grenade" pos="-3.30603 0.26218 -1.340943"
               rpy="0 0 0" dechance="0.25" />
    </dispatch>
</group>
```

- **`<container>`** — general loot, chosen by *category*, placed at random
  `<point>`s within a radius.
- **`<dispatch>`** — a **named item type at a fixed offset** from the parent
  object. The group carries a `dechance`, and each `<proxy>` rolls its own.

This is what makes a crate modelled to hold grenades actually contain grenades.
Setting `LootProxyPlacement: 0` kills themed placement server-wide, leaving
only category loot on random points.

**[unverified]** Whether `0` disables `<dispatch>` outright or merely skips the
proxies has not been confirmed from source.

---

## `FoodDecay` needs `WorldWetTempUpdate`

Both live in `globals.xml`, but the dependency is easy to miss:
**`FoodDecay` requires `WorldWetTempUpdate: 1`.** Turning off the parent
silently disables food decay too.

`WorldWetTempUpdate` drives the whole survival layer around clothing — gear
getting wet, drying by a fire, warming and cooling. Disabling it is far more
drastic than disabling food decay alone, and is rarely what anyone means.

To stop food rotting, set `FoodDecay: 0` and leave `WorldWetTempUpdate` at `1`.
