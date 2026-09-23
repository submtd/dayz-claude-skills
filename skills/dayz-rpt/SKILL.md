---
name: dayz-rpt
description: Use when reading a DayZ server's .RPT or script_*.log — diagnosing why a mission edit did nothing, confirming a deploy loaded, invalid classnames or events, loot or vehicle spawn problems, crashes and unclean shutdowns, login and queue behaviour, console versus PC crossplay players, logout timers — or when told the RPT "shows an error" and asked what it means.
---

# DayZ .RPT and script log

The `.RPT` is the server process's own log. It's 0.5–2.6 MB per session, and
**about three-quarters of it is Bohemia asset noise.** Somewhere in the rest,
the central economy reports on the mission: how many types, events and map
groups it loaded, which classnames it rejected, which items it struggles to
place, which events cannot spawn. It is the closest thing to an error log the
mission XML has, and the only place to confirm a deploy took effect.

It also carries what the ADM does not: logins in progress, the platform
(console or PC crossplay) and the logout timer. `script_*.log` is the RPT's
`SCRIPT` lines again with no timestamps, so read the RPT.

Most of it is written by the **engine**, and the CE is `proto native`, so
**no source explains these messages.** The facts here come from 24 RPTs
(241,602 lines) from four Xbox servers on Nitrado, counted against the
mission files that produced them.

## Never answer from memory

Formats come from `references/format.md`, sessions from
`references/sessions.md`, and anything about the CE from
`references/ce-diagnostics.md`. Asked eight routine questions with no tools,
an agent hedged carefully and still got the basics wrong:

- It said RPT timestamps are **elapsed time since launch** ("a known
  annoyance"). They are **wall-clock `H:MM:SS.mmm`** in the host's local
  time. The header also carries the boot date.
- It gave connect lines as **`Player Bob connected (id=76561198…)`** and
  **`BattlEye Server: Player #3 … GUID`**. The real lines are `Player X
  (id=<40 hex>) connecting` and `… has connected.`, preceded by a
  `[StateMachine]` login sequence. No BattlEye line appears in 241k console
  lines.
- It did not know the platform is logged. `LOGINQUEUE : Player N updated
  with device type 'console'` or `'desktop'` is on every join, and
  **`desktop` is a PC crossplay player.**
- It invented mission-file errors: `Error reading types.xml`, `CE: UNKNOWN
  TYPE`, `Error: Json file cfggameplay.json could not be parsed`. The real
  one is `!!! [CE][offlineDB] :: Type 'X' will be ignored. (Type does not
  exist. (Typo?))`.
- It suggested grepping `SCRIPT (E)` as the first diagnostic. No `SCRIPT
  (E)` line appeared in 24 boots. The useful lines start with `!!! [CE]`.

## Things that are not what they look like

- **`Module: $CurrentDir:mpmissions\dayzOffline.<map>\init.c; loaded 1x
  files`** is Nitrado's `init.c` compiling, not yours. The deployed `init.c`
  stays inert `[operator]`. A Clan Wars investigation read this line the
  other way and lost a night to it.
- **`!!! [CE][offlineDB] :: No Shutdown message present.`** appears at every
  boot, after clean shutdowns too. It is not a crash. A crash is a completed
  file that lacks `--- Termination successfully completed ---`.
- **`.37` is 37 milliseconds.** Milliseconds are padded to two digits, not
  three, and hours below 10 are padded with a space. A parser that reads
  `.37` as 370 ms puts 1,477 of 18,719 same-second sequences out of order.
- **`has connected.` fires on every respawn**, exactly as the ADM's `is
  connected` does, and the counts match the ADM boot for boot. A join is a
  `connecting` followed by `has connected.` for the same player. Respawns
  run their own `…RespawnState` machine with an empty uid.
- **The login uid is empty for the first four states.** It appears at
  `DBGetLoginTimeLoginState` on every login (230 of 230).
- **Silence on a classname proves nothing, but a complaint proves a lot.**
  `Type does not exist. (Typo?)` names a `types.xml` classname the game does
  not know. That is a real, if one-sided, exception to "classnames have no
  authority below the operator".
- **Every load complaint on a vanilla-derived mission may be Bohemia's.**
  `Static_FrozenScientist_DE`, `ChristmasTree(_Green)`, two Sakhal police
  wrecks, `WinterMilitaryCoat_Greay` and `VehicleTransitBus` all come from
  Bohemia's own files. Check the list in `references/ce-diagnostics.md`
  before calling one local drift.
- **Loud repetition is not severity.** Clan Wars' admin vehicle events fail
  to spawn about 74 times a session each, and that is expected there. Among
  the loot warnings, `AK101` leads because its `nominal` went from 2 to 13,
  and vanilla prison clothing appears too. They are leads, not verdicts.
- **The header contains the server's public IP and Nitrado service path.**
  Anonymise before sharing any raw RPT.

## Confirming a deploy

After a restart, compare these RPT counts with the file you deployed. **All
five matched exactly on four live servers:**

| RPT line | Equals |
|---|---|
| `[CE][IgnoreList] … loaded N types` | `cfgignorelist.xml` entries |
| `[CE][LoadPrototype] :: loaded N prototypes` | uncommented `mapgroupproto.xml` groups |
| `[CE][LoadMap] "Group" :: loaded N groups` | uncommented `mapgrouppos.xml` groups |
| `[CE][DynamicEvent] Load Events:[N]` | `events.xml` events with `<active>1</active>` |
| `[CE][DE][SPAWNS] :: Total positions: N` | `<pos>` under active events in `cfgeventspawns.xml` |

Count **without comments**: a naive `grep -c` over-counts disabled entries.
`[CE][TypeSetup] N classes` is **not** the `types.xml` count.

- **Confirm the folder too.** The `Module: …mpmissions\<folder>\init.c`
  line names the mission folder the server actually uses, which is where the
  files must go. The `init.c` itself is Nitrado's.
- **The comparison is manual.** `triage.py` prints the RPT side. Counting
  the deployed file is on you.
- **JSON files cannot be confirmed this way.** `cfggameplay.json` loads
  silently.

## Build and platform

The player's device (console or PC crossplay) is in
`references/sessions.md`. This section is about the server build.

- **Verified here:** Xbox servers on Nitrado, 1.29. They are Windows
  processes (`PLATFORM_WINDOWS`) compiled with `SERVER_FOR_X1` and
  `SERVER_FOR_CONSOLE`, so engine code under either `#ifdef` applies.
- **Unverified off Xbox:** a PC server's RPT (paths, BattlEye lines, mod
  loading) and a PlayStation server's defines.
- **The CE lines come from the same engine everywhere.** Their meaning
  should carry across platforms; their counts belong to the mission.

## Routing

| Question | Go to |
|---|---|
| Header, timestamps, file naming and retention, clean shutdown, script log, what to ignore | `references/format.md` |
| Login states, uid timing, console or PC, joins versus respawns, logout timer | `references/sessions.md` |
| Did my edit load? Invalid classnames or events, loot and vehicle spawn warnings, storage | `references/ce-diagnostics.md` |
| Triage a boot or a directory of them | `scripts/triage.py` |
| The same events from the gameplay side | `dayz-adm` |
| Acting on a CE finding | `dayz-types`, `dayz-mapgroups`, `dayz-globals` |

## scripts/triage.py

```sh
python3 scripts/triage.py DayZServer_X1_x64_2026-09-22_12-02-02.RPT
python3 scripts/triage.py /path/to/rpt-dir            # one report per boot
python3 scripts/triage.py /path/to/rpt-dir --top 20   # longer runtime lists
```

Per boot it reports:
- version and mission folder
- clean shutdown or not (the newest file is treated as still running)
- the load-summary counts
- load complaints, with Bohemia's shipped defects tagged by name
- the top loot, vehicle and event-loot warnings
- storage failures
- joins, respawns and devices, paired per player

**Exit 0** means nothing the mission caused. **Exit 1** means a load
complaint not on Bohemia's list, failed map groups, or a completed file with
no clean shutdown. **Exit 2** means it could not run. On all 24 production
files it exits 0, because every load complaint on the live servers is
Bohemia's.

It does **not** interpret runtime warnings or judge severity. That needs the
mission files and the operator's intent.
