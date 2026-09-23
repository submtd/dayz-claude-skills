#!/usr/bin/env python3
"""Triage a DayZ server .RPT: what does this boot say is wrong with the mission?

A healthy RPT is 5,000-15,000 lines of Bohemia's own asset warnings with a few
dozen lines that matter buried in them. This script throws the noise away and
reports what is left, grouped by the mission file it points at:

  * the central economy's load summary -- how many types, events, prototypes
    and map groups actually loaded, which is how you confirm an edit took
  * CE load problems: classnames the game does not know, events that do not
    exist, prototype parse errors
  * CE runtime pressure: items the loot respawner struggles to place, vehicle
    events that cannot spawn their nominal, event loot that overflows its wreck
  * the session: clean shutdown or not, joins versus respawns, device types

    triage.py FILE.RPT [FILE.RPT ...]
    triage.py DIR                 # every *.RPT inside, one report per boot
    triage.py DIR --top 20        # longer runtime lists (default 8)

Defects Bohemia ships in its own mission files are recognised by name and
tagged, so an untouched vanilla mission does not fail. See
references/ce-diagnostics.md for what each line is evidence of -- the CE is
engine-native and most of these messages are not explained by any source.

Exit status: 0 nothing the mission caused, 1 a CE load problem that is not a
known Bohemia defect or a file that did not end cleanly (and is not the newest,
still-running boot), 2 could not run.
"""

import argparse
import collections
import re
import sys
from pathlib import Path

# Classnames and event names Bohemia's own files reference but the game rejects.
# Present on untouched vanilla missions; reported, never failed. Verified against
# BohemiaInteractive/DayZ-Central-Economy@master for the map named.
VANILLA_DEFECTS = {
    "Static_FrozenScientist_DE": "in vanilla Chernarus/Livonia types.xml; no such class",
    "ChristmasTree": "vanilla Chernarus types.xml + events.xml; scope not public",
    "ChristmasTree_Green": "vanilla Livonia/Sakhal types.xml; scope not public",
    "Land_wreck_sed02_aban1_police": "vanilla Sakhal types.xml; scope not public",
    "Land_wreck_sed02_aban2_police": "vanilla Sakhal types.xml; scope not public",
    "WinterMilitaryCoat_Greay": "vanilla Livonia types.xml typo for ..._Grey",
    "VehicleTransitBus": "vanilla Chernarus/Livonia cfgeventspawns.xml; no such event",
}

TS = re.compile(r"^ ?(\d{1,2}):(\d{2}):(\d{2})\.(\d{2,3})\s+(.*)$")
R = {
    "version": re.compile(r"^Version (\S+)"),
    "mission": re.compile(r"Module: \$CurrentDir:mpmissions\\([^\\]+)\\init\.c"),
    "types": re.compile(r"\[CE\]\[TypeSetup\] :: (\d+) classes setuped"),
    "ignore": re.compile(r"\[CE\]\[IgnoreList\] \"[^\"]+\" :: loaded (\d+) types"),
    "events": re.compile(r"\[CE\]\[DynamicEvent\] Load\s+Events:\[(\d+)\] Primary spawners: (\d+) Secondary spawners: (\d+)"),
    "protos": re.compile(r"\[CE\]\[LoadPrototype\] :: loaded (\d+) prototypes"),
    "proto_bad": re.compile(r"!!! \[CE\]\[LoadPrototype\] (\d+) (groups have no points|groups have wrong points|Errors during XML parse)"),
    "mapload": re.compile(r"\[CE\]\[LoadMap\] \"(\w+)\" :: loaded (\d+) groups, groups failed: (\d+)"),
    "spawnpos": re.compile(r"\[CE\]\[DE\]\[SPAWNS\] :: Total positions: (\d+)"),
    "badtype": re.compile(r"!!! \[CE\]\[offlineDB\] :: Type '([^']+)' will be ignored\. \((.+)\)$"),
    "badevent": re.compile(r"!!! \[CE\]\[DE\]\[SPAWNS\] :: \[WARNING\] :: Skipping entry for non-existing event '([^']+)'"),
    "hard": re.compile(r"\[CE\]\[LootRespawner\] \(\w+\) :: Item \[\d+\] is hard to place, performance drops: \"([^\"]+)\""),
    "overtime": re.compile(r"\[CE\]\[LootRespawner\] \(\w+\) :: Item \[\d+\] causing search overtime: \"([^\"]+)\""),
    "vehfail": re.compile(r"!!! \[CE\]\[VehicleRespawner\] \((\w+)\) :: Respawning: \"([^\"]+)\" - Failed to spawn the requested amount \((\d+) < (\d+)\)"),
    "lootover": re.compile(r"\[CE\]\[SpawnRandomLoot\] \((\w+)\) :: Type: (\S+) :: !!! (Sum of container LootMax is lower than event child LootMax|Wanting to spawn more loot than possible)"),
    "pointrm": re.compile(r"!!! \[CE\]\[Point\] Removing [-\d.]+, [-\d.]+ from (\S+)"),
    "storage": re.compile(r"!!! (?:\[CE\]\[Storage\] )?Failed to (read|write) \[Storage\] data"),
    "connected": re.compile(r"^Player (.+) \(id=\w+ pos=<[^>]*>\) has connected\.$"),
    "connecting": re.compile(r"^Player (.+) \(id=\w+\) connecting$"),
    "device": re.compile(r"LOGINQUEUE\s+: Player \d+ updated with device type '(\w+)'"),
    "script_err": re.compile(r"SCRIPT\s+\(E\)"),
    "term": re.compile(r"--- Termination successfully completed ---"),
}
BOOT = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})\.RPT$")


def triage(path):
    f = collections.Counter()
    info = {"file": path.name, "term": False, "lines": 0}
    lists = collections.defaultdict(collections.Counter)
    bad = []
    pending = set()  # players seen "connecting" whose "has connected." has not arrived
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        info["lines"] += 1
        m = TS.match(raw)
        body = m.group(5) if m else raw.strip()
        mm = R["version"].match(raw)
        if mm and "version" not in info:
            info["version"] = mm.group(1)
        if R["term"].search(body):
            info["term"] = True
        mm = R["mission"].search(body)
        if mm:
            info["mission"] = mm.group(1)
        for key in ("types", "ignore", "protos", "spawnpos"):
            mm = R[key].search(body)
            if mm:
                info.setdefault(key, []).append(int(mm.group(1)))
        mm = R["events"].search(body)
        if mm:
            info["events"] = tuple(int(x) for x in mm.groups())
        mm = R["mapload"].search(body)
        if mm:
            info.setdefault("mapload", []).append((mm.group(1), int(mm.group(2)), int(mm.group(3))))
            if int(mm.group(3)):
                bad.append(f"[CE][LoadMap] \"{mm.group(1)}\": {mm.group(3)} groups failed")
        mm = R["proto_bad"].search(body)
        if mm:
            lists["proto_bad"][mm.group(2)] += int(mm.group(1))
        mm = R["badtype"].search(body)
        if mm:
            lists["badtype"][(mm.group(1), mm.group(2))] += 1
        mm = R["badevent"].search(body)
        if mm:
            lists["badevent"][mm.group(1)] += 1
        for key in ("hard", "overtime", "pointrm"):
            mm = R[key].search(body)
            if mm:
                lists[key][mm.group(1)] += 1
        mm = R["vehfail"].search(body)
        if mm:
            lists["vehfail"][f"{mm.group(2)} ({mm.group(1)}) got {mm.group(3)} of {mm.group(4)}"] += 1
        mm = R["lootover"].search(body)
        if mm:
            lists["lootover"][f"{mm.group(2)} ({mm.group(1)})"] += 1
        mm = R["storage"].search(body)
        if mm:
            f["storage_" + mm.group(1)] += 1
        # A join is "connecting" then "has connected."; a respawn is a bare
        # "has connected." (every respawn writes one). Pair per player, not by
        # subtracting totals: a login that never completes has no connect.
        mm = R["connecting"].match(body)
        if mm:
            pending.add(mm.group(1))
        mm = R["connected"].match(body)
        if mm:
            f["joins" if mm.group(1) in pending else "respawns"] += 1
            pending.discard(mm.group(1))
        mm = R["device"].search(body)
        if mm:
            lists["device"][mm.group(1)] += 1
        if R["script_err"].search(body):
            lists["script_err"][body[:160]] += 1
    return info, f, lists, bad


def report(path, info, f, lists, bad, newest, top):
    problems = list(bad)
    print(f"=== {info['file']}")
    boot = BOOT.search(info["file"])
    print(f"  boot {boot.group(1)} {boot.group(2)}:{boot.group(3)}:{boot.group(4)} (host clock)" if boot
          else f"  (name carries no boot time)")
    print(f"  version {info.get('version', '?')}  mission {info.get('mission', '?')}  "
          f"{info['lines']} lines")
    if info["term"]:
        print("  shutdown: clean ('Termination successfully completed')")
    elif newest:
        print("  shutdown: none yet -- newest file, assumed still running")
    else:
        print("  shutdown: MISSING -- crashed, killed, or a download cut short")
        problems.append("file did not end with a clean termination")

    def first(key):
        v = info.get(key)
        return v[0] if v else "?"
    ev = info.get("events", ("?", "?", "?"))
    maps = ", ".join(f"{k} {n} (failed {x})" for k, n, x in info.get("mapload", [])) or "?"
    print(f"  CE loaded: {first('types')} types, {first('ignore')} ignore-list, {ev[0]} events "
          f"({ev[1]} primary, {ev[2]} secondary spawners), {first('protos')} prototypes, "
          f"{first('spawnpos')} event positions")
    print(f"  map groups: {maps}")

    for (name, why), n in sorted(lists["badtype"].items()):
        tag = VANILLA_DEFECTS.get(name)
        print(f"  {'note ' if tag else 'ERROR'} type '{name}' ignored: {why}"
              + (f"  [Bohemia: {tag}]" if tag else ""))
        if not tag:
            problems.append(f"type {name}")
    for name, n in sorted(lists["badevent"].items()):
        tag = VANILLA_DEFECTS.get(name)
        print(f"  {'note ' if tag else 'ERROR'} cfgeventspawns.xml names event '{name}', which "
              f"events.xml does not define" + (f"  [Bohemia: {tag}]" if tag else ""))
        if not tag:
            problems.append(f"event {name}")
    for what, n in sorted(lists["proto_bad"].items()):
        print(f"  note  [CE][LoadPrototype] {n} {what} (mapgroupproto.xml; vanilla has these too)")

    def show(key, label):
        c = lists[key]
        if not c:
            return
        print(f"  {label}: {sum(c.values())} lines, {len(c)} distinct")
        for name, n in c.most_common(top):
            print(f"      {n:6d}  {name}")

    show("overtime", "LootRespawner 'causing search overtime'")
    show("hard", "LootRespawner 'hard to place, performance drops'")
    show("vehfail", "VehicleRespawner 'failed to spawn the requested amount'")
    show("lootover", "SpawnRandomLoot event loot exceeds its containers")
    show("pointrm", "'[CE][Point] Removing' (spawn point dropped)")
    if f["storage_read"] or f["storage_write"]:
        print(f"  storage: {f['storage_read']} failed reads, {f['storage_write']} failed writes")
    dev = ", ".join(f"{k} {v}" for k, v in lists["device"].items()) or "none"
    print(f"  players: {f['joins']} joins, {f['respawns']} respawns, devices: {dev}")
    show("script_err", "SCRIPT (E)")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", type=Path, help=".RPT files or directories of them")
    ap.add_argument("--top", type=int, default=8, help="entries per runtime list")
    args = ap.parse_args()
    files = []
    for p in args.paths:
        if p.is_dir():
            files += sorted(p.glob("*.RPT"))
        elif p.is_file():
            files.append(p)
        else:
            print(f"error: {p} does not exist", file=sys.stderr)
            return 2
    if not files:
        print("error: no .RPT files found", file=sys.stderr)
        return 2
    newest = {}
    for p in files:
        newest[p.parent] = max(newest.get(p.parent, p.name), p.name)
    failed = []
    for p in files:
        problems = report(p, *triage(p), newest=(newest[p.parent] == p.name), top=args.top)
        failed += [f"{p.name}: {x}" for x in problems]
    if failed:
        print(f"\n{len(failed)} problem(s) the mission or the server caused:")
        for x in failed:
            print(f"  {x}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
