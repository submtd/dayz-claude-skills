---
name: dayz-adm
description: Use when reading, parsing or ingesting a DayZ server's .ADM admin log — kill feeds, death causes, who killed whom, session and playtime tracking, player ids and bans, PlayerList positions, base-building or flag activity, timestamps and timezones, fetching logs from Nitrado — or when a log-driven bot, leaderboard or stat looks wrong, double-counts, or misses events.
---

# DayZ .ADM admin log

The `.ADM` is the server's event log: sessions, hits, deaths, consciousness,
building, placement, emotes, teleports, and a PlayerList every five minutes.
One line per event, one file per server boot. Every Discord kill feed,
leaderboard and death-cause tool on a DayZ server is a parser over this file.

**It never errors.** A line shape the parser misses is an event that silently
did not happen: a disconnect that never closes a session, a kill filed as a
bleed-out, a respawn counted as a second death. This skill exists because
the format looks obvious and isn't.

Engine source: `scripts/4_world/plugins/pluginbase/pluginadminlog.c` in
`BohemiaInteractive/DayZ-Script-Diff` writes most lines. Connect, disconnect,
chat and the header are written by the executable, and their format is known
**only** from real files. The facts here were checked against 146,308
production lines from four Xbox servers on Nitrado.

## Never answer from memory

Every line format, field order and count **must** come from
`references/lines.md`, and every death sequence from `references/deaths.md`.
An agent asked eight routine questions about the ADM, with no tools, hedged
carefully and was still wrong wherever it committed:

- It said positions are **`<X, Y, Z>` with altitude in the middle**, with
  "moderate-high confidence". The player position is **`<x, z, altitude>`**:
  source prints `[0], [2], [1]`. Two other positions in the same file (flag
  poles, teleports) **do** put altitude in the middle, so both answers are
  somewhere in the log, and a parser needs to know which is which.
- It invented **`died of hunger`** and **`died of a broken leg / fall
  damage`**. Neither exists. Starvation, dehydration, falls and more all
  print one line: ` died. Stats> Water: n Energy: n Bleed sources: n`.
- It gave the PlayerList header as **`Player List (N players):`**. It is
  **`##### PlayerList log: N players`**, closed by a bare `#####`.
- It said the PlayerList interval "may be configurable". It is a **300 s
  constant**. The config key only turns it on or off.
- It **did not know `is choosing to respawn` exists**. That line is the whole
  unconscious-respawn problem.
- It did not know about the **`(DEAD)`** marker, the **`[HP: n]`** field,
  or the four `serverDZ.cfg` switches that decide which lines exist at all.

## Things that are not what they look like

- **`(DEAD)` is state, not an event.** It is added to the name whenever the
  player is not alive at write time. It marks the death line, every corpse
  line after it (908 PvP hits on corpses in the corpus), and **a killer who
  died first**. Count deaths from death shapes, never from `(DEAD)`.
- **`is connected` is not a join.** Every respawn writes one, 5–15 s after
  the death, with no disconnect before it. Of 6,791 connects, 6,028 were
  joins (preceded by `is connecting`) and 763 were respawns (preceded by a
  death), with **zero** exceptions. A tempting explanation, that this only
  happens with `economy.xml` `<player save="0">`, is **wrong**: `save="1"`
  servers do it on every respawn.
- **`is choosing to respawn` is only sometimes a death.** Alive, it causes
  the death, and a bare `died.` follows in the same second. With `(DEAD)`,
  the death was already logged and this is the death-screen button. 43 of
  52 were the `(DEAD)` form. Treat every one as a death and you
  double-count.
- **` died.` does not mean "unknown".** It means the engine had no killer
  object. That covers starvation, falls, bleed-outs, unconscious respawns
  and logouts, blade suicides, and a player finished off by a bleed tick
  after being shot. The cause is in the lines **before** it
  (`references/deaths.md`).
- **`killed by  with 40mm Explosive Grenade`**, with **two spaces**, is a
  kill whose killer the game lost. Grenades, claymores and mines never name a
  thrower either. Nothing in the log recovers them.
- **Line order within one second is not causal.** A kill line can come
  before the hit that caused it, and a different player can hit the corpse
  after it. Clan Wars resolves same-second hits by **lowest HP = last hit**.
- **`id=` is not always 40 hex.** `id=ERROR`, with an all-sentinel
  position, appears on disconnects. A strict id pattern drops the line, and
  that session never closes.
- **`Built` and `Dismantled` name parts differently.** `Built
  wall_base_down` uses the part's id; `Dismantled Lower Frame` uses its
  display name. A `Dismantled (\S+)` pattern drops 71% of dismantles, and
  the ones it catches still don't match their build lines.
- **"Log Damage" on Nitrado is inverted from its label.** Turning it **on**
  sets `adminLogPlayerHitsOnly`, which **removes** infected and animal hit
  lines.
- **The clock is local and the sign is a trap.** The live servers run at
  UTC−4 and UTC−7. Their ingest code stores "+4"/"+7", the amount to add,
  and one schema comment calls that "UTC+4". Read the wrong way, every
  timestamp is off by 8 hours (`references/files-and-time.md`).
- **Suicide lines come in two orders.** A firearm suicide logs `committed
  suicide` while alive, then `died.`. A blade suicide logs `died.` first,
  then `(DEAD) … committed suicide`.
- **Infected knock people out at high HP.** Shock never shows in `[HP: n]`,
  so a player can be knocked out at HP 83 with no player involved. A rule
  of "low HP means the hits killed them" misses these deaths.

## Console and PC

Everything verified here is **Xbox on Nitrado**, filename
`DayZServer_X1_x64_…`. The script-written lines come from shared engine
source and should read identically on PC. The executable-written lines
(connect, disconnect, header), the PC and PlayStation file names and
locations, and chat are `[unverified]` off Xbox. **No chat or `#toadmin`
line appears in 146k console lines.** Do not quote a chat format.

On console the log is the only telemetry there is. Without mods, nothing
can add a line, so everything a bot knows comes from these shapes. On PC,
a mod can call `PluginAdminLog.DirectAdminLogPrint()` or write its own file.
That changes what is possible, not what vanilla writes.

## Routing

| Question | Go to |
|---|---|
| What does line X look like? What gates it? How common is it? | `references/lines.md` |
| Who killed whom? Why a bare `died.`? Respawns, unconscious logouts, suicides | `references/deaths.md` |
| File names, headers, dates, midnight, UTC offset, fetching from Nitrado, partial reads | `references/files-and-time.md` |
| Does my parser handle every real shape? | `scripts/classify.py` (below) |
| Should the Respawn button show while unconscious? | `dayz-cfggameplay`, `disableRespawnInUnconsciousness` |

## House conventions for parsers

- **Anchor on the identity block**, `(id=<40 hex or ERROR>…)`, and parse
  right of it. Gamertags are player-chosen and may contain spaces or any
  phrase a whole-line search keys on.
- **Key players on the id, never the gamertag.** Players rename, and a name
  is a label. Accept `ERROR` and decide deliberately what it means.
- **Make every `(DEAD)` optional on both blocks** of kill and hit lines.
- **Reject positions by map bounds.** The FLT_MAX sentinel can sit in any
  slot. Know which ordering each position uses: the player block is `x, z,
  altitude`; flag poles and teleports are `x, altitude, z`.
- **Drop the trailing fragment of the live file** every poll. A cut line can
  still match a pattern with a truncated value.
- **Store what the log stated separately from what you inferred.** A kill
  credited from preceding hits (Clan Wars' `finishedBy`) is an inference,
  and the record should say so. Public-facing labels such as "combat logged"
  are policy, not log facts.
- **Store every raw line losslessly**, keyed by file and line number. Both
  production ingest workers do. When a new shape turns up, you can re-parse
  history instead of losing it.
- **Run `scripts/classify.py` over real files** before trusting a parser,
  and again after every game update.

## scripts/classify.py

```sh
python3 scripts/classify.py DayZServer_X1_x64_2026-09-01_22-01-00.ADM
python3 scripts/classify.py /path/to/adm-dir            # every *.ADM
python3 scripts/classify.py /path/to/adm-dir --unknown  # list unmatched lines
python3 scripts/classify.py /path/to/adm-dir --verbose  # per-shape counts, every trap hit
```

It sorts every line into a known shape. **Any line it cannot place is an
error**: a parser built on this catalogue drops it. It also flags missing
headers and cut tails, and reports every trap it sees (`id-error`,
`sentinel-pos`, `kill-no-killer`, both respawn forms, corpse lines, dead
attackers, debug-string lines, midnight and jitter, PlayerList count
mismatches). Exit 0 means every line was recognised, 1 means unrecognised
lines or a file fault, 2 means it could not run.

On the 3,018 production files it recognises all 146,308 lines. It does
**not** attribute deaths or convert to UTC; both need judgment the file
cannot supply.
