# ADM files, timestamps and fetching from Nitrado

Tags as in [lines.md](lines.md). `[project]` = measured by one of the
operator's production ingest workers and recorded in its repo.

## Files

**One file per server boot.** A restart never appends to the old file
`[corpus: 3,018 files]`.

```
DayZServer_X1_x64_2026-09-01_22-01-00.ADM
```

- **The name carries the boot time** in the **host's local clock**. `X1` is
  the Xbox build. The PC and PlayStation names are `[unverified]`; do not
  assume the same pattern.
- **The header repeats the boot time:**
  ```
  ******************************************************************************
  AdminLog started on 2026-09-01 at 22:01:00
  ```
  The header time equals the name's in 3,015 of 3,018 files; the other three
  are 1 s later `[corpus]`. It is the **only date in the file**.
- **42% of files are header-only** (1,282 of 3,018): a boot with nobody
  on, or an empty server between restarts. They are small and are
  never appended to, so their Nitrado `modified_at` **is** their creation
  instant. That makes them the cleanest clock-offset evidence (below).
- **A file with no header** is a crash-truncated boot or not an ADM at all
  (Nitrado can return an HTML error page with HTTP 200) `[project: CW]`.
  Its lines cannot be dated from the file. Quarantine it.
- **Restart cadence is the operator's, not DayZ's.** The live servers
  restart every 2 h. A deathmatch server on the same host restarts every
  30 min. The file count follows.

## Timestamps

```
23:59:58 | ##### PlayerList log: 2 players
00:00:02 | Player "Alpha" (…)
```

- **`HH:MM:SS | ` only.** No date and no timezone, and hours are
  zero-padded `[corpus: every line]`. The RPT pads hours with a *space*
  (`  9:55:02.719`); the ADM does not. Don't share a regex between them.
- **Date = header date, rolled forward each time the clock goes backwards by
  more than 12 h.** That is the only midnight signal. A single file can span
  midnight `[corpus: 57 rollovers]`.
- **Small backward steps happen** (write-order jitter) and are **not**
  midnight. All three production parsers use the 12 h threshold. The RPT
  parser in One Life used 20 h. Either works; a threshold of 0 does not.
- **Walk every file from line 0**, even when resuming mid-file. Midnight is a
  property of the sequence, so starting at line 400 loses any rollover
  before it `[project: CW ingest.ts]`.

## The clock offset, and its sign

The file's clock is the **host's wall clock**. It is not UTC and not
necessarily the server's in-game time. The offset differs per server and
has to be **measured**:

These are **examples, not defaults**. Measure any other server.

| Server | Server clock | Add this to get UTC |
|---|---|---|
| One Life Chernarus | UTC−4 | +4 h |
| One Life Livonia, Sakhal; Clan Wars | UTC−7 | +7 h |
| Deathmatch (same operator) | UTC−7 | +7 h |

`[project: each ingest worker's servers.clock_offset_ms as of 2026-09-22,
stored as "UTC = local + offset": 14400000 and 25200000. Chernarus
confirmed by a known event, 19:42:19 local = 23:42:19Z]`

**The sign is a trap, and the operator's own code states it both ways.**
Clan Wars' schema comment says "Chernarus **UTC+4**", meaning the value to
add. The server's clock is UTC**−4**. An agent that reads "UTC+4" as the
server's zone gets every timestamp wrong by 8 hours. Always write it as
"add +4 h to get UTC".

**How to measure it** `[project: CW derive-clock-offset.ts, bloodbag
admPoller.js]`:

> offset = min over files of (Nitrado `modified_at` − time in filename),
> snapped to a 15-minute grid.

`modified_at` is true UTC epoch seconds. `created_at` reflects when the
listing was made and is useless. A `modified_at` of `0` means missing and
must be excluded, or the offset comes out wrong by decades. Header-only
files give the tightest bound.

**Daylight saving `[unverified]`:** −4 and −7 look like North American
summer time. If the hosts observe DST, every offset moves by an hour in
November, and a parser that stored one offset will be off by 1 h. Clan
Wars knowingly leaves a DST hazard unfixed: it picks the "newest" file by
its local-time name, so a backwards clock step can stall ingest. Re-measure
after each DST change. Do not assume it.

## Reading the live file

- **The current session's `.ADM` is visible and grows** while the server
  runs `[operator]`. A Clan Wars doc that says logs are invisible until the
  session ends is right for the RPT and `script_*.log` and wrong for the ADM.
- **Lines reach the file late.** Around 10 minutes of lag was measured
  between an event and its ADM line appearing through the API
  `[project: bloodbag]`. Anything "real-time" is not.
- **A download can end mid-line.** The last line of the live file may be
  cut, and a cut line can still match a pattern (`… with VSS from 4.67`
  loses digits, and `… with VSS ` loses the distance entirely). Drop the
  trailing fragment of the live file every time. Re-read it on the next
  poll. `classify.py` reports this as `no-final-newline`.
- **Files never shrink legitimately.** Keep a cursor per file and never let
  it move backwards. Treat a shorter download as a failed fetch, not a
  rewrite.

## Fetching from Nitrado

`[project: all three ingest workers]`. All calls use `Authorization: Bearer
<token>` against `https://api.nitrado.net`.

1. `GET /services/{id}/gameservers` → `data.gameserver.game_specific.path`.
2. `GET /services/{id}/gameservers/file_server/list?dir=<path>config` →
   `data.entries[]` with `name`, `path`, `size`, `modified_at`.
3. `GET /services/{id}/gameservers/file_server/download?file=<path>` →
   `data.token.url`, then a plain GET of that URL with no auth header.

Traps:

- **`game_specific.log_files` is capped.** The deathmatch bot saw about 4 of
  148 files through it and lost kills `[project: bloodbag]`. Use the
  directory listing.
- **Errors arrive as HTTP 200** with `status: "error"`. Check the body, not
  the status code.
- **Whole-file downloads only.** There are no byte ranges, so re-download
  and skip to the cursor.
- **The path on disk** looks like
  `/games/<id>/noftp/dayzxb/config/DayZServer_X1_x64_….ADM` `[project]`.
  The ADM sits beside the RPT in `config/`, not in the mission folder.
