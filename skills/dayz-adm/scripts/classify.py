#!/usr/bin/env python3
"""Classify every line of a DayZ .ADM log and flag the ones a parser will get wrong.

The ADM never errors. A parser that misses a line shape drops the event
silently: a disconnect that never closes a session, a kill filed as an
environmental death, a respawn counted as a second death. This script sorts
every line into a known shape, lists the lines that match none, and reports
the shapes that are real but routinely mis-handled.

    classify.py FILE.ADM [FILE.ADM ...]
    classify.py DIR                      # every *.ADM inside, oldest name first
    classify.py FILE.ADM --unknown       # print each unmatched line
    classify.py FILE.ADM --verbose       # + per-shape counts and every trap hit

The shape catalogue was built from engine source (PluginAdminLog in
BohemiaInteractive/DayZ-Script-Diff) and checked against 146,308 production
lines from four Xbox servers on Nitrado. Every shape it knows was seen in that
corpus or is written by a source path; see references/lines.md.

What this script deliberately does NOT do:

  * attribute deaths. A bare "died." has several honest readings; see
    references/deaths.md. This reports the sequences, not a verdict.
  * convert times to UTC. The clock is host-local and the offset is per server,
    measured, not knowable from the file. See references/files-and-time.md.
  * treat a line it does not recognise as corrupt. An unknown shape usually
    means a game update added one -- read it, then extend SHAPES.

Exit status: 0 every line recognised, 1 unrecognised lines or a file-level
fault (no header, truncated tail), 2 could not run.
"""

import argparse
import collections
import re
import sys
from pathlib import Path

ID = r"(?:[0-9A-F]{40}|ERROR)"
NUM = r"-?[\d.]+(?:e[-+]?\d+)?"
VEC = rf"<{NUM}, {NUM}, {NUM}>"
# The identity block. Anchor on it, never on the gamertag: names are
# player-controlled and may contain spaces or any phrase a parser keys on.
WHO = rf'Player "(?P<name>.*?)" (?P<dead>\(DEAD\) )?\(id=(?P<id>{ID})(?: pos=(?P<pos>{VEC}))?\)'
WHO2 = rf'Player ".*?" (?:\(DEAD\) )?\(id={ID}(?: pos={VEC})?\)'
TIME = r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}) \| "

# (key, pattern-after-timestamp). Order matters only where one shape is a
# prefix of another; the specific form comes first.
SHAPES = [
    # --- written by the executable, not by script (format not in source) ---
    ("connecting", rf"{WHO} is connecting$"),
    ("connected", rf"{WHO} is connected$"),
    ("disconnected", rf"{WHO} has been disconnected$"),
    # --- PlayerList block, every 300 s while anyone is on ---
    ("playerlist-header", r"##### PlayerList log: (?P<count>\d+) players?$"),
    ("playerlist-end", r"#####$"),
    ("playerlist-body", rf"{WHO}$"),
    # --- deaths (PluginAdminLog.PlayerKilled and friends) ---
    ("kill-fists", rf"{WHO} killed by {WHO2} with \(MeleeFist\)$"),
    ("kill-player", rf"{WHO} killed by {WHO2} with (?P<weapon>.+?)(?: from (?P<dist>{NUM}) meters)? ?$"),
    ("kill-no-killer", rf"{WHO} killed by  with (?P<weapon>.+)$"),
    ("kill-entity", rf"{WHO} killed by (?P<entity>.+)$"),
    ("died", rf"{WHO} (?P<how>died|drowned)\. Stats> Water: {NUM} Energy: {NUM} Bleed sources: \d+$"),
    ("bled-out", rf"{WHO} bled out$"),
    ("suicide", rf"{WHO} committed suicide$"),
    ("drowned-uncon", rf"{WHO} has drowned while unconscious$"),
    ("respawn", rf"{WHO} is choosing to respawn$"),
    ("disconnect-uncon", rf"{WHO} is disconnecting while being unconscious$"),
    ("disconnect-restrained", rf"{WHO} is disconnecting while being restrained$"),
    # --- consciousness ---
    ("unconscious", rf"{WHO} is unconscious$"),
    ("regained", rf"{WHO} regained consciousness$"),
    # --- hits (PlayerHitBy); [HP: n] is glued to the closing paren ---
    ("hit-player", rf"{WHO}\[HP: {NUM}\] hit by {WHO2} into \w*\(-?\d+\) for {NUM} damage \((?P<ammo>[^)]*)\)(?: with (?P<weapon>.+?)(?: from {NUM} meters)?)? ?$"),
    ("hit-block", rf"{WHO}\[HP: {NUM}\] hit by .+? into Block\(\d+\) for 0 damage ?.*$"),
    ("hit-creature", rf"{WHO}\[HP: {NUM}\] hit by (?P<src>[\w ]+?) into \w*\(-?\d+\) for {NUM} damage \((?P<ammo>[^)]*)\)$"),
    ("hit-explosion", rf"{WHO}\[HP: {NUM}\] hit by explosion \((?P<ammo>[^)]*)\)$"),
    ("hit-object", rf"{WHO}\[HP: {NUM}\] hit by (?P<src>\w+) with (?P<ammo>\w+)$"),
    ("hit-bare", rf"{WHO}\[HP: {NUM}\] hit by (?P<src>\w+)$"),
    ("stunned", rf"{WHO}\[HP: {NUM}\] stunned by .+$"),
    # --- building, placement, flags (adminLogPlacement / adminLogBuildActions) ---
    ("placed", rf"{WHO} placed (?P<display>.+?)<(?P<cls>\w+)>$"),
    ("built", rf"{WHO}Built (?P<part>\S+) on (?P<on>.+?) with (?P<tool>.+)$"),
    # Built names the part by its id (wall_base_down); Dismantled by its display
    # name (Lower Metal Wall). A single-token pattern drops every dismantle.
    ("dismantled", rf"{WHO}Dismantled (?P<part>.+?) from (?P<on>.+?) with (?P<tool>.+)$"),
    ("shelter", rf"{WHO} built (?P<what>\w+) with (?P<tool>.+?) ?$"),
    ("folded", rf"{WHO} folded (?P<what>.+)$"),
    ("packed", rf"{WHO} packed (?P<what>.+?) with (?P<tool>.+)$"),
    ("repaired", rf"{WHO} repaired (?P<what>.+?) with (?P<tool>.+)$"),
    ("flag", rf"{WHO} has (?P<dir>raised|lowered) (?P<flag>\w+) on (?P<pole>\w+) at {VEC}$"),
    # Bohemia's own bug: some action messages embed the player object's debug
    # string instead of prose. Seen for barbed wire and burying containers.
    ("debug-string", rf"{WHO}Player SurvivorBase<0x[0-9A-F]+> \w+:\d+ .+$"),
    # --- misc ---
    ("emote", rf"{WHO} performed (?P<emote>Emote\w+)(?: with (?P<item>\w+))?$"),
    ("teleported", rf"{WHO} was teleported from: {VEC} to: {VEC}\. Reason: (?P<reason>.+)$"),
]
COMPILED = [(k, re.compile(TIME + p)) for k, p in SHAPES]
HEADER = re.compile(r"AdminLog started on (\d{4})-(\d{2})-(\d{2}) at (\d{2}):(\d{2}):(\d{2})$")
STARS = re.compile(r"\*{20,}$")
FILENAME = re.compile(r"DayZServer_X1_x64_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})\.ADM$")
# FLT_MAX spelled out in full. It is what DayZ prints for "no position".
SENTINEL = "340282346638528859811704183484516925440"
# Past this the "backwards" step is a new day; below it, write-order jitter.
ROLLOVER_S = 12 * 3600


class Report:
    def __init__(self):
        self.shapes = collections.Counter()
        self.traps = collections.defaultdict(list)
        self.unknown = []
        self.errors = []
        self.files = 0
        self.lines = 0

    def trap(self, key, where, text):
        self.traps[key].append((where, text))


TRAP_TEXT = {
    "id-error": "id=ERROR on the identity block -- a parser requiring 40 hex drops "
                "the line; when it is a disconnect, that session never closes",
    "sentinel-pos": "position is FLT_MAX spelled out (no position) -- reject by bounds, "
                    "it can sit in any slot including altitude",
    "kill-no-killer": "'killed by  with X' (double space) -- a weapon kill whose killer "
                      "the game could not name; the shooter is not in the log",
    "respawn-dead": "'(DEAD) ... is choosing to respawn' -- the death is already logged "
                    "above; this is not a second death",
    "respawn-alive": "'is choosing to respawn' while alive -- the next line for this "
                     "player is a bare 'died.' naming no killer",
    "corpse-line": "(DEAD) on a hit/unconscious line -- a corpse taking damage, not an "
                   "event on a living player; can follow the kill line in the same second",
    "mutual-kill": "attacker block carries (DEAD) -- a parser whose pattern omits the "
                   "attacker's (DEAD) files a real PvP kill or hit as environmental",
    "debug-string": "action text replaced by an engine object dump (Bohemia bug) -- "
                    "the action is the words after the ':NNNNN'",
    "clock-jitter": "timestamp stepped backwards by less than 12h -- write-order jitter, "
                    "not midnight",
    "midnight": "timestamp stepped backwards by more than 12h -- the date rolled over; "
                "only the clock going backwards says so",
    "playerlist-count": "PlayerList header count differs from the body lines that followed",
    "odd-name": "gamertag contains text a whole-line parser keys on",
    "no-final-newline": "file does not end in a newline -- the last line may be cut short "
                        "even though it matched a shape (a cut distance still parses)",
}


def check_file(path, rep, want_unknown):
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lines = text.split("\n")
    trailing_partial = not text.endswith("\n") and lines and lines[-1] != ""
    if text.endswith("\n"):
        lines = lines[:-1]
    rep.files += 1

    if not FILENAME.search(path.name):
        rep.errors.append(f"{path.name}: name is not DayZServer_X1_x64_YYYY-MM-DD_HH-MM-SS.ADM "
                          "(fine for an extract; a real file's name carries the boot time)")

    header_seen = False
    last_s = None
    pl_expect = None
    pl_seen = 0
    for n, line in enumerate(lines, 1):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        rep.lines += 1
        where = f"{path.name}:{n}"
        if STARS.match(line):
            rep.shapes["header-stars"] += 1
            continue
        if HEADER.match(line):
            rep.shapes["header"] += 1
            header_seen = True
            last_s = None
            continue
        key = None
        m = None
        for k, rx in COMPILED:
            m = rx.match(line)
            if m:
                key = k
                break
        if key is None:
            if n == len(lines) and trailing_partial:
                rep.errors.append(f"{where}: last line has no newline and matches no shape -- "
                                  "a download that ended mid-line; drop it, never parse it")
            else:
                rep.unknown.append((where, line))
            continue
        rep.shapes[key] += 1
        g = m.groupdict()
        if n == len(lines) and trailing_partial:
            rep.trap("no-final-newline", where, line)

        s = int(g["h"]) * 3600 + int(g["m"]) * 60 + int(g["s"])
        if last_s is not None and s < last_s:
            rep.trap("midnight" if last_s - s > ROLLOVER_S else "clock-jitter", where, line)
        last_s = s

        if key == "playerlist-header":
            pl_expect, pl_seen = int(g["count"]), 0
        elif key == "playerlist-body":
            pl_seen += 1
        elif key == "playerlist-end" and pl_expect is not None:
            if pl_seen != pl_expect:
                rep.trap("playerlist-count", where, f"header said {pl_expect}, saw {pl_seen}")
            pl_expect = None

        if "id=ERROR" in line:
            rep.trap("id-error", where, line)
        if SENTINEL in line:
            rep.trap("sentinel-pos", where, line)
        if key == "kill-no-killer":
            rep.trap("kill-no-killer", where, line)
        if key == "respawn":
            rep.trap("respawn-dead" if g.get("dead") else "respawn-alive", where, line)
        if key in ("hit-player", "hit-creature", "hit-explosion", "hit-object", "hit-bare",
                   "unconscious") and g.get("dead"):
            rep.trap("corpse-line", where, line)
        # The attacker's block, not the count: a dead attacker can hit a living victim.
        if key in ("kill-player", "kill-fists", "hit-player") and re.search(r' by Player ".*?" \(DEAD\) \(id=', line):
            rep.trap("mutual-kill", where, line)
        if key == "debug-string":
            rep.trap("debug-string", where, line)
        name = g.get("name") or ""
        if re.search(r'"|\||hit by|killed by|\(DEAD\)|\(id=', name):
            rep.trap("odd-name", where, line)

    if not header_seen:
        rep.errors.append(f"{path.name}: no 'AdminLog started on' header -- the date of every "
                          "line in this file is unknowable from the file alone")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", type=Path, help=".ADM files or directories of them")
    ap.add_argument("--unknown", action="store_true", help="print every unrecognised line")
    ap.add_argument("--verbose", action="store_true", help="per-shape counts and every trap hit")
    args = ap.parse_args()

    files = []
    for p in args.paths:
        if p.is_dir():
            files += sorted(p.glob("*.ADM"))
        elif p.is_file():
            files.append(p)
        else:
            print(f"error: {p} does not exist", file=sys.stderr)
            return 2
    if not files:
        print("error: no .ADM files found", file=sys.stderr)
        return 2

    rep = Report()
    for f in files:
        check_file(f, rep, args.unknown)

    print(f"{rep.files} file(s), {rep.lines} non-empty lines, "
          f"{sum(rep.shapes.values())} recognised, {len(rep.unknown)} unrecognised")
    for e in rep.errors:
        print(f"ERROR  {e}")
    if rep.unknown:
        print(f"ERROR  {len(rep.unknown)} line(s) match no known shape -- a parser built on "
              "this catalogue drops them silently")
        for where, line in rep.unknown if args.unknown else rep.unknown[:5]:
            print(f"         {where}: {line[:220]}")
        if not args.unknown and len(rep.unknown) > 5:
            print("         ... --unknown for all")
    for key, hits in sorted(rep.traps.items()):
        print(f"trap   {key} x{len(hits)}: {TRAP_TEXT[key]}")
        for where, line in hits[: (len(hits) if args.verbose else 1)]:
            print(f"         {where}: {line[:220]}")
    if args.verbose:
        print("\nshapes:")
        for k, v in rep.shapes.most_common():
            print(f"  {v:8d}  {k}")
    return 1 if rep.errors or rep.unknown else 0


if __name__ == "__main__":
    sys.exit(main())
