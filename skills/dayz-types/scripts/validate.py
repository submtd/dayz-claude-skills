#!/usr/bin/env python3
"""Validate a DayZ db/types.xml, including its cross-file consistency.

Nothing in this file errors at runtime. An undefined tier, a craft-only item
with a population target, a name the ignore list despawns -- the server boots
clean and the item is quietly absent. The cross-file checks are the point of
this script; the schema checks are the easy half.

    validate.py /path/to/mission/db/types.xml
    validate.py --budget /path/to/mission/db/types.xml   # total nominal by category
    validate.py --verbose /path/to/mission/db/types.xml  # + normal-in-vanilla notes

Cross-file checks run when the sibling files are present:

  * cfglimitsdefinition.xml  -- every usage/value/tag/category name must exist
  * cfgignorelist.xml        -- listed types are despawned; the entry is dead
  * cfgspawnabletypes.xml    -- entries naming a type that is not defined
  * db/events.xml            -- <child type=...> naming a type that is not defined

What this script deliberately does NOT do:

  * flag a type name that vanilla does not ship. Many real classnames have no
    vanilla entry and work once added. Unknown != invalid.
  * treat vanilla as a schema reference. Bohemia ships min > nominal and a
    half-set quantity range of its own.

Exit status: 0 clean (warnings/notes allowed), 1 errors found, 2 could not run.
"""

import argparse
import collections
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCALARS = ("nominal", "lifetime", "restock", "min",
           "quantmin", "quantmax", "cost")

# Engine clamps lifetime to [3, 316224000] -- centraleconomy.c:314.
LIFETIME_MIN, LIFETIME_MAX = 3, 316224000

# Tiers each vanilla map declares. Livonia has no Tier4; copying a Chernarus
# entry across is the most common silent failure in this file.
MAP_TIERS = {
    "chernarusplus": {"Tier1", "Tier2", "Tier3", "Tier4", "Unique"},
    "enoch": {"Tier1", "Tier2", "Tier3", "Unique"},
    "sakhal": {"Tier1", "Tier2", "Tier3", "Tier4", "Unique"},
}

FLAG_ATTRS = ("count_in_cargo", "count_in_hoarder", "count_in_map",
              "count_in_player", "crafted", "deloot")

# Bohemia ships these defects in vanilla at master. They are real -- the items
# do not work -- but they are not local drift and reporting them as errors
# would fail an untouched mission. Downgraded to a tagged warning; the same
# shape on any other type still errors.
VANILLA_DEFECTS = {
    ("Crossbow_Black", "quant"),      # quantmin 80 / quantmax 0, Livonia + Sakhal
    ("BatteryCharger", "min"),        # min 18 > nominal 13, Sakhal
    ("Firewood", "crafted"),          # crafted="1" with nominal, Livonia
}


def report(name, kind, message, errors, warnings):
    """Route a finding, downgrading Bohemia's own shipped defects."""
    if (name, kind) in VANILLA_DEFECTS:
        warnings.append(f"{message} [present in Bohemia's shipped file]")
    else:
        errors.append(message)


def find_sibling(mission, *names):
    """Mission files are inconsistently cased across these repos."""
    for name in names:
        for candidate in (mission / name, mission / name.lower()):
            if candidate.is_file():
                return candidate
    return None


def parse_types(path):
    root = ET.parse(path).getroot()
    if root.tag != "types":
        raise ValueError(f"root element is <{root.tag}>, expected <types>")
    return root


def check_schema(root, errors, warnings, no_usage):
    seen = {}
    for entry in root.findall("type"):
        name = entry.get("name")
        if not name:
            errors.append("a <type> has no name attribute")
            continue
        if name in seen:
            errors.append(f"{name}: defined more than once")
        seen[name] = entry

        values = {}
        for field in SCALARS:
            text = entry.findtext(field)
            if text is None:
                errors.append(f"{name}: missing <{field}>")
                continue
            try:
                values[field] = int(text)
            except ValueError:
                errors.append(f"{name}: <{field}> is not an integer ({text!r})")

        flags = entry.find("flags")
        if flags is None:
            errors.append(f"{name}: missing <flags>")
        else:
            for attr in FLAG_ATTRS:
                if attr not in flags.attrib:
                    warnings.append(f"{name}: <flags> has no {attr}")

        if len(entry.findall("category")) > 1:
            errors.append(f"{name}: more than one <category>")

        nominal = values.get("nominal")
        minimum = values.get("min")
        lifetime = values.get("lifetime")
        qmin = values.get("quantmin")
        qmax = values.get("quantmax")

        # crafted="1" means craft-only: the CE will not place it at all, so a
        # population target is fiction. Vanilla Livonia ships one (Firewood).
        if flags is not None and flags.get("crafted") == "1" and nominal:
            report(name, "crafted",
                   f"{name}: crafted=\"1\" with nominal {nominal} -- craft-only "
                   f"types never spawn; set crafted=\"0\" or nominal to 0",
                   errors, warnings)

        if nominal is not None and minimum is not None:
            if nominal > 0 and minimum > nominal:
                report(name, "min",
                       f"{name}: min {minimum} > nominal {nominal}",
                       errors, warnings)

        if qmin is not None and qmax is not None:
            if (qmin == -1) != (qmax == -1):
                report(name, "quant",
                       f"{name}: quantmin/quantmax half-set ({qmin}/{qmax}) -- "
                       f"use -1 for both or a real range", errors, warnings)
            elif qmin != -1:
                if qmin > qmax:
                    report(name, "quant",
                           f"{name}: quantmin {qmin} > quantmax {qmax}",
                           errors, warnings)
                if not (0 <= qmin <= 100 and 0 <= qmax <= 100):
                    report(name, "quant",
                           f"{name}: quantmin/quantmax out of range ({qmin}/"
                           f"{qmax}) -- these are percentages, 0-100",
                           errors, warnings)

        if lifetime is not None and lifetime != 0:
            if not (LIFETIME_MIN <= lifetime <= LIFETIME_MAX):
                warnings.append(
                    f"{name}: lifetime {lifetime} outside the engine clamp "
                    f"[{LIFETIME_MIN}, {LIFETIME_MAX}]")

        # Not a defect by itself -- vanilla ships ~19 of these per map, all
        # cargo-spawned (Flashlight, SodaCan_*, wheels). Verbose only.
        if nominal and not entry.findall("usage"):
            no_usage.append(name)

    return seen


def check_limits(root, mission, errors, notes):
    """Every usage/value/tag/category name must be declared for this map."""
    path = find_sibling(mission, "cfglimitsdefinition.xml")
    if path is None:
        notes.append("cfglimitsdefinition.xml not found -- name checks skipped")
        return
    limits_root = ET.parse(path).getroot()
    declared = {}
    for child, key in (("categories", "category"), ("tags", "tag"),
                       ("usageflags", "usage"), ("valueflags", "value")):
        section = limits_root.find(child)
        declared[key] = ({e.get("name") for e in section}
                         if section is not None else set())

    undefined = collections.defaultdict(list)
    for entry in root.findall("type"):
        for key in ("category", "tag", "usage", "value"):
            for element in entry.findall(key):
                if element.get("name") not in declared[key]:
                    undefined[(key, element.get("name"))].append(entry.get("name"))

    for (key, value), users in sorted(undefined.items()):
        errors.append(
            f"<{key} name=\"{value}\"> is not declared in "
            f"{path.name} -- silently dropped on {len(users)} type(s), "
            f"e.g. {', '.join(users[:3])}")



def check_ignorelist(root, mission, notes):
    path = find_sibling(mission, "cfgIgnoreList.xml", "cfgignorelist.xml")
    if path is None:
        return
    ignored = {e.get("name") for e in ET.parse(path).getroot().iter("type")}
    defined = {e.get("name") for e in root.findall("type")}
    overlap = sorted(ignored & defined)
    if overlap:
        notes.append(
            f"{len(overlap)} type(s) are in {path.name} and so are despawned "
            f"regardless of their entry here: {', '.join(overlap[:6])}"
            + (" ..." if len(overlap) > 6 else ""))


def check_spawnabletypes(root, mission):
    path = find_sibling(mission, "cfgspawnabletypes.xml")
    if path is None:
        return []
    defined = {e.get("name") for e in root.findall("type")}
    missing = sorted({e.get("name") for e in ET.parse(path).getroot().findall("type")
                      if e.get("name") not in defined})
    return missing


def check_events(root, mission, errors):
    path = mission / "db" / "events.xml"
    if not path.is_file():
        return
    defined = {e.get("name") for e in root.findall("type")}
    missing = sorted({c.get("type") for c in ET.parse(path).getroot().iter("child")
                      if c.get("type") and c.get("type") not in defined})
    if missing:
        errors.append(
            f"{len(missing)} event child type(s) in db/events.xml have no "
            f"entry here and spawn nothing: {', '.join(missing[:6])}")


def print_budget(root):
    """Total nominal is a server performance budget, not a loot dial."""
    per_category = collections.Counter()
    total = active = 0
    for entry in root.findall("type"):
        try:
            nominal = int(entry.findtext("nominal") or 0)
        except ValueError:
            continue
        category = entry.find("category")
        per_category[category.get("name") if category is not None else "(none)"] += nominal
        total += nominal
        active += 1 if nominal else 0

    print("  loot budget")
    print(f"    {'total nominal':<16}{total:>8}")
    print(f"    {'active types':<16}{active:>8}")
    for name, value in per_category.most_common():
        print(f"    {name:<16}{value:>8}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="path to db/types.xml")
    parser.add_argument("--budget", action="store_true",
                        help="also print the total nominal budget by category")
    parser.add_argument("--verbose", action="store_true",
                        help="also list informational findings that are normal "
                             "in vanilla (no-usage types, dead spawnable entries)")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"error: {args.file}: no such file", file=sys.stderr)
        return 2

    try:
        root = parse_types(args.file)
    except ET.ParseError as exc:
        print(f"{args.file}\n  ERROR    does not parse: {exc}")
        return 1
    except ValueError as exc:
        print(f"{args.file}\n  ERROR    {exc}")
        return 1

    mission = args.file.parent
    if mission.name == "db":
        mission = mission.parent

    errors, warnings, notes, no_usage = [], [], [], []
    check_schema(root, errors, warnings, no_usage)
    check_limits(root, mission, errors, notes)
    check_ignorelist(root, mission, notes)
    dead_spawnable = check_spawnabletypes(root, mission)
    check_events(root, mission, errors)

    if args.verbose:
        if no_usage:
            notes.append(
                f"{len(no_usage)} type(s) have nominal > 0 and no <usage>, so "
                f"they reach the world only as cargo, event or spawnable type: "
                + ", ".join(no_usage))
        if dead_spawnable:
            notes.append(
                f"{len(dead_spawnable)} entr(ies) in cfgspawnabletypes.xml name "
                f"a type with no entry here -- harmless but dead: "
                + ", ".join(dead_spawnable))

    print(args.file)
    for message in errors:
        print(f"  ERROR    {message}")
    for message in warnings:
        print(f"  WARNING  {message}")
    for message in notes:
        print(f"  NOTE     {message}")
    if not (errors or warnings or notes):
        print("  OK       no problems found")
    if args.budget:
        print_budget(root)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
