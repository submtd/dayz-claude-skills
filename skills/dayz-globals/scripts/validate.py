#!/usr/bin/env python3
"""Validate a DayZ db/globals.xml, including its cross-file pairs.

Most variables in globals.xml only work in concert with another mission file.
Changing one side and not the other produces no error and no result, so the
cross-file checks below are the point of this script — the schema checks are
the easy half.

    validate.py /path/to/mission/db/globals.xml

Cross-file checks run when the sibling files are present:

  * cfgspawnabletypes.xml  — <damage> entries override LootDamage* per item
  * db/types.xml           — the lifetimes FlagRefresh* postpones
  * env/zombie_territories.xml — the zone counts ZombieMaxCount caps

Exit status: 0 clean (warnings/notes allowed), 1 errors found, 2 could not run.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DAY = 86400

# name -> (type, vanilla value). Identical across all three vanilla maps.
VANILLA = {
    "AnimalMaxCount": ("0", "200"),
    "CleanupAvoidance": ("0", "100"),
    "CleanupLifetimeDeadAnimal": ("0", "1200"),
    "CleanupLifetimeDeadInfected": ("0", "330"),
    "CleanupLifetimeDeadPlayer": ("0", "3600"),
    "CleanupLifetimeDefault": ("0", "45"),
    "CleanupLifetimeLimit": ("0", "50"),
    "CleanupLifetimeRuined": ("0", "330"),
    "FlagRefreshFrequency": ("0", "432000"),
    "FlagRefreshMaxDuration": ("0", "3456000"),
    "FoodDecay": ("0", "1"),
    "IdleModeCountdown": ("0", "60"),
    "IdleModeStartup": ("0", "1"),
    "InitialSpawn": ("0", "100"),
    "LootDamageMax": ("1", "0.82"),
    "LootDamageMin": ("1", "0.0"),
    "LootProxyPlacement": ("0", "1"),
    "LootSpawnAvoidance": ("0", "100"),
    "RespawnAttempt": ("0", "2"),
    "RespawnLimit": ("0", "20"),
    "RespawnTypes": ("0", "12"),
    "RestartSpawn": ("0", "0"),
    "SpawnInitial": ("0", "1200"),
    "TimeHopping": ("0", "60"),
    "TimeLogin": ("0", "15"),
    "TimeLogout": ("0", "15"),
    "TimePenalty": ("0", "20"),
    "WorldWetTempUpdate": ("0", "1"),
    "ZombieMaxCount": ("0", "1000"),
    "ZoneSpawnDist": ("0", "300"),
}

# Base-building parts whose types.xml lifetimes FlagRefresh* acts on.
BASE_PARTS = (
    "Fence", "Watchtower", "TerritoryFlag", "SeaChest", "WoodenCrate",
    "Barrel_Blue", "MediumTent", "LargeTent", "CarTent",
)

# TimeLogin/TimeLogout are documented with this ceiling.
TIME_MAX = 65536


def parse_globals(path):
    """Return {name: (type, value)} or raise ET.ParseError."""
    root = ET.parse(path).getroot()
    out = {}
    for var in root.findall("var"):
        name = var.get("name")
        if name:
            out[name] = (var.get("type"), var.get("value"))
    return out


def as_number(raw):
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def check_schema(found, errors, warnings):
    for name, (vtype, value) in sorted(found.items()):
        if name not in VANILLA:
            errors.append(f"{name}: unknown variable — the engine ignores it")
            continue
        want_type, _ = VANILLA[name]
        if vtype != want_type:
            kind = {"0": "integer", "1": "float", "2": "string"}
            errors.append(
                f'{name}: type="{vtype}" but vanilla ships type="{want_type}" '
                f"({kind.get(want_type, '?')})"
            )
        num = as_number(value)
        if num is None:
            errors.append(f"{name}: value {value!r} is not a number")
            continue
        # A float under type="0" is truncated silently rather than erroring.
        if want_type == "0" and num != int(num):
            errors.append(
                f'{name}: {value} is a float under type="0" — silently truncated'
            )

    for name in sorted(set(VANILLA) - set(found)):
        warnings.append(f"{name}: missing — the engine falls back to its default")

    for name in ("TimeLogin", "TimeLogout"):
        num = as_number(found.get(name, (None, None))[1])
        if num is not None and num > TIME_MAX:
            errors.append(f"{name}: {int(num)} exceeds the documented max {TIME_MAX}")

    lo = as_number(found.get("LootDamageMin", (None, None))[1])
    hi = as_number(found.get("LootDamageMax", (None, None))[1])
    for label, val in (("LootDamageMin", lo), ("LootDamageMax", hi)):
        if val is not None and not 0.0 <= val <= 1.0:
            errors.append(f"{label}: {val} is outside the 0..1 range")
    if lo is not None and hi is not None and lo > hi:
        errors.append(f"LootDamageMin ({lo}) is greater than LootDamageMax ({hi})")


def check_food_decay(found, errors):
    """FoodDecay requires WorldWetTempUpdate=1 — both live in this file."""
    food = as_number(found.get("FoodDecay", (None, None))[1])
    wet = as_number(found.get("WorldWetTempUpdate", (None, None))[1])
    if food and not wet:
        errors.append(
            "FoodDecay is on but WorldWetTempUpdate is off — food decay "
            "requires WorldWetTempUpdate=1, so it is silently disabled"
        )


def check_loot_damage(found, mission, notes):
    """<damage> in cfgspawnabletypes.xml overrides LootDamage* per item."""
    spawnable = mission / "cfgspawnabletypes.xml"
    if not spawnable.is_file():
        return
    text = spawnable.read_text(encoding="utf-8-sig", errors="replace")
    entries = []
    for m in re.finditer(r"<damage[^/>]*/>", text):
        start = text.rfind("<type ", 0, m.start())
        name = "?"
        if start != -1:
            hit = re.search(r'name="([^"]+)"', text[start:start + 300])
            if hit:
                name = hit.group(1)
        entries.append((name, m.group(0)))
    if not entries:
        return

    lo = as_number(found.get("LootDamageMin", (None, None))[1])
    hi = as_number(found.get("LootDamageMax", (None, None))[1])
    shown = ", ".join(sorted({n for n, _ in entries})[:6])
    more = "" if len(entries) <= 6 else f" (+{len(entries) - 6} more)"
    notes.append(
        f"cfgspawnabletypes.xml has {len(entries)} <damage> entr"
        f"{'y' if len(entries) == 1 else 'ies'} — those items ignore "
        f"LootDamageMin/Max entirely: {shown}{more}"
    )
    if lo == 0.0 and hi == 0.0:
        notes.append(
            "globals.xml asks for pristine loot (0.0/0.0) but the entries "
            "above override it — strip them to make globals.xml the single "
            "control point, unless they are deliberate (e.g. single-use keys)"
        )


def check_flag_refresh(found, mission, notes):
    """FlagRefresh* only postpones the lifetimes in types.xml."""
    types_xml = mission / "db" / "types.xml"
    if not types_xml.is_file():
        types_xml = mission / "types.xml"
    max_dur = as_number(found.get("FlagRefreshMaxDuration", (None, None))[1])
    if not types_xml.is_file() or max_dur is None:
        return
    text = types_xml.read_text(encoding="utf-8-sig", errors="replace")
    lifetimes = {}
    for name in BASE_PARTS:
        m = re.search(rf'<type name="{name}">(.*?)</type>', text, re.S)
        if m:
            lt = re.search(r"<lifetime>(\d+)</lifetime>", m.group(1))
            if lt:
                lifetimes[name] = int(lt.group(1))
    if not lifetimes:
        return

    # TerritoryFlag is the flag itself, not a thing the flag protects.
    protected = {k: v for k, v in lifetimes.items() if k != "TerritoryFlag"}
    if not protected:
        return
    worst = max(protected.values())
    if worst > max_dur * 2:
        names = sorted(k for k, v in protected.items() if v == worst)
        notes.append(
            f"FlagRefreshMaxDuration is {max_dur / DAY:.1f}d but base parts "
            f"live {worst / DAY:.1f}d in types.xml ({', '.join(names[:3])}) — "
            "the flag only postpones those lifetimes, so a short flag "
            "duration on long lifetimes does almost nothing. Shorten the "
            "lifetimes if the goal is faster cleanup of abandoned bases."
        )


def check_infected_cap(found, mission, notes):
    """ZombieMaxCount caps what zombie_territories.xml asks for."""
    zones = mission / "env" / "zombie_territories.xml"
    cap = as_number(found.get("ZombieMaxCount", (None, None))[1])
    if not zones.is_file() or cap is None:
        return
    text = zones.read_text(encoding="utf-8-sig", errors="replace")
    dmax = [int(x) for x in re.findall(r'dmax="(\d+)"', text)]
    if not dmax:
        return
    total = sum(dmax)
    if total > cap:
        notes.append(
            f"env/zombie_territories.xml asks for up to {total} infected across "
            f"{len(dmax)} zones but ZombieMaxCount is {int(cap)} — the cap "
            "decides density once players are spread out, and zone edits will "
            "not show up until it is raised"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="path to db/globals.xml")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"error: {args.file}: no such file", file=sys.stderr)
        return 2

    try:
        found = parse_globals(args.file)
    except ET.ParseError as exc:
        print(f"ERROR  does not parse: {exc}")
        return 1

    # db/globals.xml -> mission root is two levels up; tolerate a flat layout.
    mission = args.file.parent
    if mission.name == "db":
        mission = mission.parent

    errors, warnings, notes = [], [], []
    check_schema(found, errors, warnings)
    check_food_decay(found, errors)
    check_loot_damage(found, mission, notes)
    check_flag_refresh(found, mission, notes)
    check_infected_cap(found, mission, notes)

    print(args.file)
    for message in errors:
        print(f"  ERROR    {message}")
    for message in warnings:
        print(f"  WARNING  {message}")
    for message in notes:
        print(f"  NOTE     {message}")
    if not (errors or warnings or notes):
        print("  OK       no problems found")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
