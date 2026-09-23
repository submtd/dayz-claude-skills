# RPT format, files and noise

**Tags:**
- `[corpus]`: seen in 24 RPTs (241,602 lines) and 24 script logs from four
  Xbox/Nitrado servers on DayZ 1.29.163709, 2026-09-22.
- `[source]`: `BohemiaInteractive/DayZ-Script-Diff`.
- `[operator]`: confirmed by the server operator.

Most RPT content is written by the engine, not by script. Its format is known
only from real files.

## Files

```
DayZServer_X1_x64_2026-09-22_12-02-02.RPT
script_2026-09-22_12-02-06.log
DayZServer_X1_x64_2026-09-22_12-02-03.ADM
```

- **One RPT per boot**, named with the boot time in the **host's local
  clock**, the same clock as the ADM. The ADM from the same boot is named
  within a second or two of it. Pair the two by nearest name, not by exact
  match.
- **Size:** 0.5–2.6 MB per 2-hour session `[corpus]`. It grows with player
  count, because a quarter of the file is per-player debug. The ADM for the
  same session is around 100 KB.
- **Nitrado kept 37–39 of each** (RPT, ADM, script log) on all four
  servers when listed on 2026-09-22 `[corpus: one listing]`. At a 2-hour
  restart that is about three days. Whether that is a count, an age or a
  disk limit is `[unverified]`. Fetch what you need before it goes.
- **They sit in `config/`** beside the ADM, not in the mission folder. Fetch
  them the way `dayz-adm`'s `references/files-and-time.md` describes.
- **The live file is readable and grows.** The same session's RPT went from
  926,207 to 1,024,960 bytes between two fetches `[corpus]`. A Clan Wars doc
  says RPTs are invisible until the session ends; that is wrong.

## The header

```
=====================================================================
== C:\SERVICES\<nitrado-id>_local\dayzxb\DayZServer_X1_x64.exe
== "C:\SERVICES\…\DayZServer_X1_x64.exe" -ip=<PUBLIC IP> -port=<PORT> -config=serverDZ_Private.cfg -limitFPS=100 -profiles=C:\SERVICES\…\dayzxb/config -dologs …
=====================================================================
Exe timestamp: 2026/08/11 11:20:42
Current time:  2026/09/22 12:02:02
Version 1.29.163709
=====================================================================
```

- **The header contains the server's public IP, port and Nitrado service
  path.** Never paste a raw RPT anywhere public. Anonymise first.
- `Current time` is the boot instant in the host clock, and the only full
  date in the file. `Version` is the exact build, which is the fastest way
  to tell whether a server has taken a game update.
- The server is started with `-config=serverDZ_Private.cfg`, not
  `serverDZ.cfg`. How that file relates to the Nitrado panel is
  `[unverified]`.

## Timestamps

```
12:02:02.780 String "STR_server_shutdown" listed twice in "Global"
 9:02:10.422 String "STR_server_shutdown" listed twice in "Global"
10:59:37.32  Saved 0 players ...
10:59:37.251 !!! [CE][Point] Removing …
```

- **Wall-clock `H:MM:SS.mmm` in the host's local time,** not time since
  launch. There is no date; roll the header date forward when the clock
  goes backwards, as the ADM requires.
- **Hours below 10 are padded with a space** (` 9:02:10.422`), not a zero.
  18,479 lines start with a space `[corpus]`. The ADM zero-pads, so a shared
  regex fails on one of the two.
- **Milliseconds are zero-padded to two digits, not three.** 0–99 ms print as
  `.07` or `.37` followed by an extra space, which keeps the column aligned.
  100–999 ms print as `.251`. **`.37` means 37 ms, not 370.** Checked against
  line order: reading it as 37 keeps 18,719 of 18,719 same-second sequences in
  order, and reading it as 370 breaks 1,477 of them `[corpus]`.
- **Component tags carry a severity**: `ENTITY (W)`, `ENTITY (E)`,
  `ANIMATION (E)`, `MATERIAL (E)`. By use, W is a warning and E an error.
  **No `SCRIPT (E)` or `SCRIPT (W)` line appears in 24 boots** `[corpus]`,
  so their format and meaning are `[unverified]`. Every `(E)` that does
  appear is in the noise table below.
- **The component tag's indentation varies** (`NETWORK`, ` NETWORK`,
  `  NETWORK`). It is nesting, not a new field. Match with `\s+`.
- **1,243 lines have no timestamp:** the header block and multi-line
  continuations.

## Clean shutdown

```
11:00:19.799 ENGINE       : Destroying game
11:00:19.799  SCRIPT       : ~DayZGame()
11:00:23.588  --- Termination successfully completed ---
```

Every completed session ended with this line: 20 of 20 `[corpus]`. **A
finished file without it means the process died.** The only other case is the
newest file, whose session is still running.

**`!!! [CE][offlineDB] :: No Shutdown message present.` appears at every
boot** (24 of 24), including after clean terminations. It is not evidence of
a crash.

## The script log is a subset

`script_YYYY-MM-DD_HH-MM-SS.log` holds the RPT's `SCRIPT` lines with no
timestamps. Its header gives the date as **day.month.**:

```
Log C:\SERVICES\…\config\script_2026-09-22_17-02-15.log started at 22.09. 17:02:15
```

Of 1,135 script-log lines, 1,014 appear verbatim in the same boot's RPT. The
other 121 differ only because **the RPT strips `%`**: `(8%)` becomes `(8)`.
One line was missing from the RPT. Nothing else is unique to the script log
`[corpus]`. **Read the RPT.** The script log adds nothing except an exact
percentage.

## Script defines: these servers are Windows builds of the console server

```
SCRIPT : Module: Game; … defines: "DAYZ_1_29,SERVER_FOR_X1,SERVER_FOR_CONSOLE,SERVER,PLATFORM_WINDOWS,RELEASE,NO_GUI,…"
```

Every module compiles with `SERVER_FOR_X1`, `SERVER_FOR_CONSOLE` **and**
`PLATFORM_WINDOWS` `[corpus]`. When reading engine source for console
behaviour, code under `#ifdef SERVER_FOR_CONSOLE` applies, and so does code
under `#ifdef PLATFORM_WINDOWS`.

## `Module: …\init.c` is not your init.c

```
SCRIPT : Module: $CurrentDir:mpmissions\dayzOffline.chernarusplus\init.c; loaded 1x files; 1x classes; …
```

This line is written at every boot. It reads as proof that the mission's
`init.c` compiled. **It is Nitrado's own `init.c`.** The one you deploy is not
the one that runs `[operator]`, and the domain constant that `init.c` is inert
stands. A Clan Wars investigation read this line as its deployed file
executing, and spent a night on it.

The same line tells you the **mission folder name** the server actually uses
(`dayzOffline.chernarusplus`, `dayzOffline.enoch`, `dayzOffline.sakhal`),
which is where the deployed files must go.

## Noise: three-quarters of the file

| Family | Share | Examples |
|---|---|---|
| Model and geometry warnings | 32% | `Convex "…" selection faces are less then 4 in dz\…p3d`, `Warning: No components in …`, `ENTITY (W): Unknown object class 'pond'`, `Door '…' is missing geometry components` |
| Per-player simulation debug | 27% | `NETWORK : Simulate networked players`, `PLAYER : Player Simulation entity SurvivorM_Niki:…`, `ANIMATION : Start Weapon command`, `DEFAULT : Sliding pose with …` |
| Config and localization | 9% | `Localization not present: STR_…`, `Updating base class …`, `Warning Message: No entry 'bin\config.bin/CfgVehicles/….ClothingTypes'`, `ENTITY (E): Type '…' must be inherited from class '…'` |
| Server-query protocol | 6% | `[A2S] received data`, `[A2S] A2S_INFO` |

All of it appears on every server regardless of mission content, and none of
it is caused by anything an operator can change `[corpus]`. The
per-player debug scales with population: empty sessions have none. **Filter
it before reading the rest.** `scripts/triage.py` does this.

Two lines from Bohemia's data look alarming and are baseline: `ANIMATION (E):
Can't load sakhal/Anims/cfg/skeletons.anim.xml` and `MATERIAL (E): Object
dz\characters\zombies\z_hermit_m.xob - cannot load material …`. Both appear on
all four servers at every boot, Chernarus and Livonia included.
