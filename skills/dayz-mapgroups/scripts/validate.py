#!/usr/bin/env python3
"""Validate a DayZ mission's mapgroupproto.xml and mapgrouppos.xml.

These two files are one mechanism: proto defines building types and where loot
may sit inside them, pos places instances of those types on the map. Every way
they can disagree fails silently -- the server boots clean, nothing reaches the
RPT, and the loot is simply absent. The cross-file checks are the point of this
script.

    validate.py /path/to/mission
    validate.py /path/to/mission --capacity   # loot capacity by usage
    validate.py /path/to/mission --verbose    # + findings that are normal in vanilla

Cross-file checks run when the sibling files are present:

  * cfglimitsdefinition.xml -- every usage/value/category/tag name must exist
  * db/types.xml            -- every <proxy type=...> needs a registration

What this script deliberately does NOT do:

  * flag a prototype that is never placed. Roughly half of proto goes unused on
    any given map; it is a shared library across maps and DLC, not a manifest.
  * compare group names case-sensitively. Bohemia's own files spell the same
    group two ways across the pair, and a case-sensitive check reports 6-11
    orphans on every untouched vanilla map.
  * guess at <point flags>. Only 16 and 32 are ever shipped and no source
    establishes what they mean; unknown values are reported, not interpreted.
  * claim a usage is unreachable because no placed group carries it. Loot
    routing has a second source this script cannot see: areaflags.map, a binary
    raster that carries usage areas as well as tiers. Polana on Livonia is
    mostly basic houses and spawns military loot because the area says so.
    Capacity computed here is a LOWER BOUND, never a total.

Exit status: 0 clean (warnings/notes allowed), 1 errors found, 2 could not run.
"""

import argparse
import collections
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Declared in mapgroupproto.xml's own <defaults> on every vanilla map. A third
# of groups and a quarter of containers carry no lootmax and rely on these.
FALLBACK_GROUP_LOOTMAX = 6
FALLBACK_CONTAINER_LOOTMAX = 4

# Bohemia references these from mapgroupproto.xml and ships no types.xml entry,
# on vanilla Chernarus and vanilla Livonia alike (Sakhal is clean). Real -- the
# CE logs them as unknown when the group builds -- but not local drift, and
# erroring on them would fail an untouched mission.
VANILLA_STRUCTURAL_ODDITIES = {
    # Sakhal ships <usage> inside <container>, where it cannot apply, and one
    # stray <category> directly under <group>. Chernarus and Livonia are clean.
    ("Land_Factory_Small", "usage-in-container"),
    ("Land_Geoplant_MaintenanceHall", "usage-in-container"),
    ("Land_Construction_Crane", "category-under-group"),
    # dechance above 1.0, on Chernarus and Sakhal.
    ("StaticObj_Train_Wagon_Flat_Industrial_Planks_DE", "dechance"),
}

VANILLA_UNREGISTERED_PROXIES = {
    "Offroad_02_Door_1_1_BeigeRust",
    "Offroad_02_Door_1_2_BeigeRust",
    "Offroad_02_Door_2_1_BeigeRust",
    "Offroad_02_Door_2_2_BeigeRust",
    "Offroad_02_Trunk_BeigeRust",
}

# The only <point flags> values Bohemia ships. Meaning unestablished.
KNOWN_POINT_FLAGS = {"16", "32"}


def structural(name, kind, message, errors, warnings):
    """Route a structural finding, downgrading Bohemia's own shipped oddities."""
    if (name, kind) in VANILLA_STRUCTURAL_ODDITIES:
        warnings.append(f"{message} [present in Bohemia's shipped file]")
    else:
        errors.append(message)


def load(path):
    return ET.parse(path).getroot()


def parse_proto(path):
    """Return (groups, defaults) from mapgroupproto.xml."""
    root = load(path)
    if root.tag != "prototype":
        raise ValueError(f"root element is <{root.tag}>, expected <prototype>")
    defaults = {}
    block = root.find("defaults")
    if block is not None:
        for entry in block.findall("default"):
            defaults[entry.get("name")] = entry.attrib
    return root.findall("group"), defaults


def group_lootmax(group, defaults):
    raw = group.get("lootmax")
    if raw is not None:
        return int(raw)
    return int(defaults.get("group", {}).get("lootmax", FALLBACK_GROUP_LOOTMAX))


def container_lootmax(container, defaults):
    raw = container.get("lootmax")
    if raw is not None:
        return int(raw)
    return int(defaults.get("container", {}).get("lootmax",
                                                 FALLBACK_CONTAINER_LOOTMAX))


def check_proto_schema(groups, defaults, errors, warnings, notes, no_usage,
                       empty_containers, disabled_groups):
    seen = {}
    over_advertised = 0
    odd_flags = collections.Counter()
    for group in groups:
        name = group.get("name")
        if not name:
            errors.append("a <group> in mapgroupproto.xml has no name")
            continue
        key = name.lower()
        if key in seen:
            errors.append(f"mapgroupproto.xml: duplicate group {name!r} "
                          f"(also as {seen[key]!r}); the later one wins silently")
        seen[key] = name

        try:
            cap = group_lootmax(group, defaults)
        except ValueError:
            errors.append(f"{name}: lootmax {group.get('lootmax')!r} is not an integer")
            continue
        if cap <= 0:
            disabled_groups.append(name)

        containers = group.findall("container")
        if not containers:
            errors.append(f"{name}: no <container>, so the group has no loot points")
        if group.find("usage") is None:
            no_usage.append(name)
        if group.find("proxy") is not None:
            structural(name, "proxy-under-group",
                       f"{name}: <proxy> directly under <group>; proxies "
                       f"belong inside a <dispatch> and are ignored here",
                       errors, warnings)
        for stray in ("category", "tag", "point"):
            if group.find(stray) is not None:
                structural(name, f"{stray}-under-group",
                           f"{name}: <{stray}> directly under <group>; it "
                           f"belongs inside a <container> and is ignored here",
                           errors, warnings)

        total = 0
        for container in containers:
            for stray in ("usage", "value"):
                if container.find(stray) is not None:
                    structural(name, f"{stray}-in-container",
                               f"{name}: <{stray}> inside <container>; containers "
                               f"filter by category and tag only, and this is "
                               f"ignored", errors, warnings)
            try:
                total += container_lootmax(container, defaults)
            except ValueError:
                errors.append(f"{name}: container lootmax "
                              f"{container.get('lootmax')!r} is not an integer")
            points = container.findall("point")
            if not points:
                empty_containers.append(f"{name}/{container.get('name')}")
            for point in points:
                pos = (point.get("pos") or "").split()
                if len(pos) != 3:
                    errors.append(f"{name}: a <point> has pos={point.get('pos')!r}, "
                                  f"expected three numbers")
                flags = point.get("flags")
                if flags is not None and flags not in KNOWN_POINT_FLAGS:
                    odd_flags[flags] += 1
        if total > cap:
            over_advertised += 1

        for dispatch in group.findall("dispatch"):
            for proxy in dispatch.findall("proxy"):
                if not proxy.get("type"):
                    errors.append(f"{name}: a <proxy> has no type")
                chance = proxy.get("dechance")
                if chance is not None:
                    try:
                        value = float(chance)
                    except ValueError:
                        errors.append(f"{name}: proxy dechance {chance!r} is not a number")
                    else:
                        if value < 0.0:
                            errors.append(f"{name}: proxy dechance {value} "
                                          f"is negative")
                        elif value > 1.0:
                            structural(name, "dechance",
                                       f"{name}: proxy dechance {value} is above "
                                       f"1.0; dechance reads as a probability and "
                                       f"the effect of a value above 1 is "
                                       f"unestablished", errors, warnings)

    for flags, count in odd_flags.items():
        warnings.append(f"mapgroupproto.xml: {count} <point> carr(y) "
                        f"flags={flags!r}; vanilla ships only 16 and 32 and the "
                        f"meaning is unestablished")
    if disabled_groups:
        notes.append(f"{len(disabled_groups)} group(s) have lootmax 0 and hold "
                     f"nothing. Normal -- Bohemia uses it to retire a prototype "
                     f"in place: " + ", ".join(sorted(disabled_groups)))
    if empty_containers:
        notes.append(f"{len(empty_containers)} container(s) have no <point>, so "
                     f"they hold nothing. Normal -- vanilla ships 5 on Chernarus, "
                     f"2 on Livonia and 13 on Sakhal inside placed groups")
    if over_advertised:
        notes.append(f"{over_advertised} group(s) have containers summing above "
                     f"the group lootmax. Normal -- 130 of 240 placed groups on "
                     f"vanilla Livonia do. The group ceiling is what the engine "
                     f"enforces; reason with that, not the container sum")


def check_pos(groups, pos_path, errors, notes):
    """pos -> proto name resolution. Case-insensitive, deliberately."""
    defined = {g.get("name", "").lower() for g in groups}
    placed = collections.Counter()
    malformed = 0
    no_rotation = 0
    for entry in load(pos_path).findall("group"):
        name = entry.get("name")
        if not name:
            errors.append("a <group> in mapgrouppos.xml has no name")
            continue
        placed[name.lower()] += 1
        if len((entry.get("pos") or "").split()) != 3:
            malformed += 1
        if entry.get("a") is None:
            no_rotation += 1

    if malformed:
        errors.append(f"mapgrouppos.xml: {malformed} entr(ies) have a pos that "
                      f"is not three numbers")
    if no_rotation:
        notes.append(f"mapgrouppos.xml: {no_rotation} entr(ies) have no 'a' "
                     f"attribute, so the loot-point ring is unrotated")

    orphans = {name: count for name, count in placed.items() if name not in defined}
    for name, count in sorted(orphans.items(), key=lambda kv: -kv[1]):
        errors.append(f"mapgrouppos.xml places {name!r} {count} time(s) but "
                      f"mapgroupproto.xml defines no such group -- these spawn "
                      f"nothing")

    unplaced = len(defined - set(placed))
    if unplaced:
        notes.append(f"{unplaced} prototype(s) are never placed. Normal -- proto "
                     f"is a shared library across maps and DLC, not a manifest")
    return placed


def check_limits(groups, mission, errors):
    """Every usage/value/category/tag must be declared for THIS mission."""
    path = mission / "cfglimitsdefinition.xml"
    if not path.is_file():
        return
    root = load(path)
    declared = {
        "usage": {u.get("name") for u in root.iter("usage")},
        "value": {v.get("name") for v in root.iter("value")},
        "category": {c.get("name") for c in root.iter("category")},
        "tag": {t.get("name") for t in root.iter("tag")},
    }
    missing = collections.defaultdict(set)
    for group in groups:
        for kind in ("usage", "value"):
            for node in group.findall(kind):
                if node.get("name") not in declared[kind]:
                    missing[kind].add(node.get("name"))
        for container in group.findall("container"):
            for kind in ("category", "tag"):
                for node in container.findall(kind):
                    if node.get("name") not in declared[kind]:
                        missing[kind].add(node.get("name"))
    for kind, names in sorted(missing.items()):
        errors.append(f"mapgroupproto.xml uses {kind} name(s) not declared in "
                      f"cfglimitsdefinition.xml, so the filter is silently "
                      f"dropped: {', '.join(sorted(names))}")


def check_proxy_registration(groups, mission, errors, warnings):
    path = mission / "db" / "types.xml"
    if not path.is_file():
        return
    registered = {t.get("name") for t in load(path).findall("type")}
    referenced = {p.get("type") for g in groups for p in g.iter("proxy") if p.get("type")}
    unregistered = sorted(referenced - registered)
    shipped = [n for n in unregistered if n in VANILLA_UNREGISTERED_PROXIES]
    local = [n for n in unregistered if n not in VANILLA_UNREGISTERED_PROXIES]
    if local:
        errors.append(f"proxy type(s) with no db/types.xml entry -- the CE logs "
                      f"each as unknown every time the group builds. Register at "
                      f"nominal 0 / min 0 / count_in_map=\"1\": {', '.join(local)}")
    if shipped:
        warnings.append(f"{len(shipped)} proxy type(s) have no db/types.xml entry "
                        f"[present in Bohemia's shipped file]: {', '.join(shipped)}")


def capacity_by_usage(groups, defaults, placed):
    """Capacity = group lootmax (the engine's ceiling) x instances placed.

    Two reasons this is not a total. A group with several usages contributes
    its full capacity to each, so the columns over-attribute. And areaflags.map
    grants usage by map area, independently of any building's <usage>, so real
    capacity for a usage is at least this and often more. Use for before/after
    deltas, never as an absolute.
    """
    info = {}
    for group in groups:
        try:
            cap = group_lootmax(group, defaults)
        except ValueError:
            cap = 0
        info[group.get("name", "").lower()] = (
            cap, [u.get("name") for u in group.findall("usage")])
    per_usage = collections.Counter()
    total = 0
    for name, count in placed.items():
        if name not in info:
            continue
        cap, usages = info[name]
        total += cap * count
        for usage in usages:
            per_usage[usage] += cap * count
    return per_usage, total


def note_zero_capacity(groups, defaults, placed, mission, notes):
    """Usages that types.xml allocates nominal to but no placed group carries.

    Reported as information only. It is NOT evidence the loot is unreachable:
    areaflags.map carries usage areas as well as tiers and grants them by map
    position, independently of any building's <usage>. Polana on Livonia is
    mostly basic houses and spawns military loot for exactly that reason. This
    script cannot read the raster, so it can never prove the negative.
    """
    types_path = mission / "db" / "types.xml"
    if not types_path.is_file():
        return
    per_usage, _ = capacity_by_usage(groups, defaults, placed)
    wanted = collections.Counter()
    for entry in load(types_path).findall("type"):
        try:
            count = int(entry.findtext("nominal", "0").strip() or "0")
        except ValueError:
            continue
        if count <= 0:
            continue
        for usage in entry.findall("usage"):
            wanted[usage.get("name")] += count
    zero = {u: n for u, n in wanted.items() if per_usage.get(u, 0) == 0}
    if not zero:
        return
    listed = ", ".join(f"{u} ({n} nominal)" for u, n in
                       sorted(zero.items(), key=lambda kv: -kv[1]))
    notes.append(
        f"usage(s) carrying nominal with no mapgroupproto capacity: {listed}. "
        f"NOT evidence the loot is stranded -- areaflags.map carries usage "
        f"areas (military, hunting, contaminated and others) and grants them "
        f"by map position, independently of any building's <usage>. This "
        f"script cannot read that raster. Verify in game before acting")


def print_capacity(groups, defaults, placed, mission):
    per_usage, total = capacity_by_usage(groups, defaults, placed)
    nominal = collections.Counter()
    types_path = mission / "db" / "types.xml"
    if types_path.is_file():
        for entry in load(types_path).findall("type"):
            try:
                count = int(entry.findtext("nominal", "0").strip() or "0")
            except ValueError:
                continue
            if count <= 0:
                continue
            for usage in entry.findall("usage"):
                nominal[usage.get("name")] += count

    print("  loot capacity (group lootmax x instances placed)")
    print(f"    {'total':<18}{total:>10}")
    print(f"    {'pos entries':<18}{sum(placed.values()):>10}")
    print()
    print(f"    {'usage':<18}{'capacity':>10}{'nominal':>10}{'saturation':>12}")
    for usage in sorted(set(per_usage) | set(nominal), key=lambda u: -per_usage.get(u, 0)):
        cap = per_usage.get(usage, 0)
        nom = nominal.get(usage, 0)
        sat = f"{nom / cap * 100:.0f}%" if cap else "-"
        print(f"    {usage:<18}{cap:>10}{nom:>10}{sat:>12}")
    print()
    print("    LOWER BOUND, not a total. areaflags.map grants usage by map area")
    print("    as well -- Polana on Livonia is basic houses spawning military")
    print("    loot -- and this script cannot read that raster. Both columns also")
    print("    over-attribute, since a group or type with three usages counts in")
    print("    all three. Use for before/after deltas, never as absolutes.")
    print("    Saturation above 100% is normal: vanilla Livonia ships Military at")
    print("    153% and Town at 672%.")


def resolve_mission(given):
    """Accept a mission dir, or either of the two files inside one."""
    if given.is_file():
        given = given.parent
    if (given / "mapgroupproto.xml").is_file():
        return given
    if given.name == "db" and (given.parent / "mapgroupproto.xml").is_file():
        return given.parent
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mission", type=Path,
                        help="mission directory containing mapgroupproto.xml")
    parser.add_argument("--capacity", action="store_true",
                        help="also print loot capacity by usage")
    parser.add_argument("--verbose", action="store_true",
                        help="also list findings that are normal in vanilla")
    args = parser.parse_args()

    mission = resolve_mission(args.mission)
    if mission is None:
        print(f"error: {args.mission}: no mapgroupproto.xml here", file=sys.stderr)
        return 2
    proto_path = mission / "mapgroupproto.xml"
    pos_path = mission / "mapgrouppos.xml"
    if not pos_path.is_file():
        print(f"error: {mission}: mapgroupproto.xml without mapgrouppos.xml",
              file=sys.stderr)
        return 2

    try:
        groups, defaults = parse_proto(proto_path)
    except ET.ParseError as exc:
        print(f"{mission}\n  ERROR    mapgroupproto.xml does not parse: {exc}")
        return 1
    except ValueError as exc:
        print(f"{mission}\n  ERROR    mapgroupproto.xml: {exc}")
        return 1

    errors, warnings, notes = [], [], []
    no_usage, empty_containers, disabled_groups = [], [], []
    check_proto_schema(groups, defaults, errors, warnings, notes, no_usage,
                       empty_containers, disabled_groups)
    try:
        placed = check_pos(groups, pos_path, errors, notes)
    except ET.ParseError as exc:
        print(f"{mission}\n  ERROR    mapgrouppos.xml does not parse: {exc}")
        return 1
    check_limits(groups, mission, errors)
    check_proxy_registration(groups, mission, errors, warnings)

    note_zero_capacity(groups, defaults, placed, mission, notes)
    if args.verbose:
        if no_usage:
            notes.append(f"{len(no_usage)} group(s) carry no <usage>: "
                         + ", ".join(sorted(no_usage)))
        if empty_containers:
            notes.append("containers with no <point>: "
                         + ", ".join(sorted(empty_containers)))

    print(mission)
    for message in errors:
        print(f"  ERROR    {message}")
    for message in warnings:
        print(f"  WARNING  {message}")
    for message in notes:
        print(f"  NOTE     {message}")
    if not (errors or warnings or notes):
        print("  OK       no problems found")
    if args.capacity:
        print()
        print_capacity(groups, defaults, placed, mission)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
