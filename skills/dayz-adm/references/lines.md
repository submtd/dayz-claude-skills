# ADM line catalogue

Every line shape DayZ writes to the `.ADM`, with where it comes from, what
gates it, and what it looks like. Examples are real production lines with the
gamertag and id replaced (`Alpha`/`Bravo`, `AAAA…`/`BBBB…` = 40 hex).

**Tags:** `[source]` = `scripts/4_world/plugins/pluginbase/pluginadminlog.c`
or a named caller in `BohemiaInteractive/DayZ-Script-Diff`. `[corpus]` = seen
in 146,308 production lines from four Xbox/Nitrado servers (July–Sept 2026),
count given. `[exe]` = written by the executable, not script. Its format is
*only* known from the corpus, and no source settles it. `[operator]` =
confirmed by the server operator.

## Contents

- [The identity block](#the-identity-block) — shared by almost every line
- [File header](#file-header)
- [Sessions](#sessions-exe)
- [PlayerList](#playerlist)
- [Deaths](#deaths)
- [Consciousness](#consciousness)
- [Hits](#hits)
- [Building and placement](#building-and-placement)
- [Other](#other)
- [Never seen on console](#never-seen-on-console)
- [Gating switches](#gating-switches)

---

## The identity block

```
Player "Alpha" (id=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA pos=<7508.3, 8821.6, 34.1>)
Player "Alpha" (DEAD) (id=AAAA… pos=<…>)
```

Built by `GetPlayerPrefix()` `[source]`.

- **`(DEAD)`** is inserted between the name and `(id=` whenever the player is
  not alive **at the moment the line is written** `[source]`. It is not a
  death event. It marks the killed player on the death line, the corpse on
  every line after it, and a killer who died first. See
  [deaths.md](deaths.md).
- **`id=`** is 40 uppercase hex characters `[corpus: 107,084 of 107,096]`.
  It is the same id the RPT logs and `GetIdentity().GetId()` returns: a
  console session's RPT `[Logout]: New player AAAA…` matched the ADM's
  `(id=AAAA…)` `[project: clan-wars docs/direction/2026-09-13-console-init-c-findings.md]`. Nitrado's ban list accepts it
  `[project: OL, verified empirically]`. Nothing in any source says what it
  is a hash of, and it is **not** a gamertag, XUID or Steam64.
- **`id=ERROR`** occurs `[corpus: 12]`, always on a `has been disconnected`
  line and always with a sentinel position. A parser that requires 40 hex
  drops those lines, and that player's session never closes.
- **`pos=<x, z, y>`**: easting, northing, **altitude last** `[source]`. The
  engine vector is `(x, height, z)`, but the prefix prints `[0], [2], [1]`.
  - Each value is **truncated** to one decimal, not rounded `[source]`.
  - A value with no fractional part prints as an integer (`12836`, not
    `12836.0`) `[source + corpus]`.
- **Sentinel position.** `-340282346638528859811704183484516925440.0` is
  FLT_MAX spelled out in full, never in `e` notation `[corpus: 242 lines]`.
  It can appear in any slot, altitude included. Reject by map bounds. A
  "position" of −3.4e38 poisons any distance or zone calculation.
- **`pos=` is absent** only on `is connecting` `[corpus]`. Every other line
  carries it, including both blocks on hit and kill lines.
- **No `id=` at all never occurs** in the corpus. A test fixture in One
  Life's parser shows `(DEAD) (pos=<…>)` with no id; treat it as synthetic.
- **Gamertags contain spaces** (`Some Name 42`) and are player-chosen.
  Anchor every pattern on `(id=<40 hex>` and parse right of it. A pattern
  that keys on `hit by` or `killed by` anywhere in the line can be spoofed by
  a gamertag. None in the corpus do, but nothing prevents it.

## File header

```
******************************************************************************
AdminLog started on 2026-09-01 at 22:01:00
```

`[exe]` `[corpus: 3,018 files, every one]`. The only line with a date. It has
no timestamp column and no timezone, and the time is the host's local clock.
See [files-and-time.md](files-and-time.md).

## Sessions `[exe]`

| Shape | Count | Example |
|---|---|---|
| connecting | 6,230 | `23:10:00 \| Player "Alpha" (id=AAAA…) is connecting` |
| connected | 6,791 | `23:10:13 \| Player "Alpha" (id=AAAA… pos=<1000.0, 2000.0, 50.1>) is connected` |
| disconnected | 6,286 | `… (id=AAAA… pos=<…>) has been disconnected` |

- **`is connecting` has no `pos=`.** The character is not loaded yet.
- **`is connected` fires on every respawn**, at the new spawn point, with
  **no** `has been disconnected` before it `[corpus]` `[operator]`. It is not
  a join. Counting connects counts lives, and pairing connect with disconnect
  to build sessions over-counts.
- **The split is exact.** Of 6,791 `is connected` lines, 6,028 follow an
  `is connecting` (a join) and 763 follow a death of that id (a respawn).
  There are zero of anything else `[corpus]`. Only 52 of the 763 respawns
  have an `is choosing to respawn` line, so detect a respawn by the
  preceding death, not by that line.
- **The RPT says `has connected.`**, not `is connected`. Test fixtures that
  use the RPT wording on ADM lines test nothing.

## PlayerList

```
13:00:07 | ##### PlayerList log: 2 players
13:00:07 | Player "Alpha" (id=AAAA… pos=<5001.0, 3001.0, 6.0>)
13:00:07 | Player "Bravo" (DEAD) (id=BBBB… pos=<1003.0, 2003.0, 50.2>)
13:00:07 | #####
```

- **Written every 300 s** by a script timer `[source: TIMER_PLAYERLIST = 300]`.
  The interval is a constant, not configurable. `adminLogPlayerList` only
  turns it on or off.
- **Skipped entirely while the server is empty** `[source]`.
- The header and the terminator carry timestamps. Body lines end at the
  closing paren. In 18,385 blocks, the header count always matched the body
  `[corpus]`.
- Body lines include corpses as `(DEAD)` `[corpus: 49]`. A corpse in the list
  is not a death event.

## Deaths

All from `PlayerKilled()` and its callers `[source]`. Attribution rules are in
[deaths.md](deaths.md).

| Shape | Count | Written as |
|---|---|---|
| PvP, firearm | 251 | `P (DEAD) (id=…) killed by Player "Bravo" (id=… pos=…) with M4-A1 from 5.72301 meters ` |
| PvP, melee | 58 | `… killed by Player "Bravo" (…) with Combat Knife` (no distance) |
| PvP, fists | 12 | `… killed by Player "Bravo" (…) with (MeleeFist)` (parentheses literal) |
| Killer not named | 13 | `… killed by  with 40mm Explosive Grenade` (**two spaces**) |
| Entity | 41 | `… killed by ZmbM_PatrolNormal_Autumn` / `Animal_CanisLupus_Grey` / `6-M7 Frag Grenade` / `Claymore` |
| Self-caused | 515 | `… died. Stats> Water: 594.976 Energy: 594.976 Bleed sources: 1` |
| Drowning | 2 | `… drowned. Stats> Water: … Energy: … Bleed sources: …` |
| Bled out | 13 | `… bled out` |
| Suicide | 439 | `… committed suicide` |
| Respawn | 52 | `… is choosing to respawn` |
| Logout while down | 14 | `… is disconnecting while being unconscious` |
| Logout while restrained | 0 | `… is disconnecting while being restrained` `[source only]` |
| Drowned while down | 0 | `… has drowned while unconscious` `[source only]` |

- **The firearm line ends in a trailing space**: `" meters "` `[source]`.
  Distance is a raw float with up to six decimals.
- **The weapon is the display name** (`M4-A1`, `CR-550 Savanna`,
  `Engraved Kolt 1911`), not the classname. Entity kills print the
  **classname** (`ZmbM_…`) via `GetType()`. Explosives print the display name.
- **`killed by  with X`**, with two spaces, comes from source's melee branch.
  It runs when the killing object is a melee-capable item with no player in
  its hierarchy, so the killer prefix is empty `[source + corpus]`. The 40mm
  grenade from an M79 and a `Fireplace` both land here. **The shooter is not
  in the log.**
- **`killed by <explosive>` never names a thrower** `[source: ExplosivesBase branch]`.
- **Starvation, dehydration, falls and "unknown" all print the same line:**
  ` died. Stats>`. The cause has to be inferred from the Stats values and
  the lines before it. Phrases like "died of hunger" or "fell to death" do not
  exist.
- **`Stats>` is followed by the literal words `Water:` and `Energy:`**, and
  those are the only vitals ever logged.

## Consciousness

```
… (id=AAAA… pos=<…>) is unconscious
… (id=AAAA… pos=<…>) regained consciousness
```

`[source: UnconStart / UnconStop]` `[corpus: 430 / 361]`.

- `regained consciousness` is suppressed if the player is dead `[source]`.
- `(DEAD) … is unconscious` occurs `[corpus: 8]`. It is a corpse, written
  after the kill in the same second. It is not a knockout.
- **Infected deal shock, which never shows in `[HP: n]`.** A player can be
  knocked out at HP 70+ by infected `[corpus + project: OL]`.

## Hits

From `PlayerHitBy()` `[source]`. **`[HP: n]` is glued to the closing paren**,
with no space, and is the victim's health **after** the hit.

| Shape | Count | Example |
|---|---|---|
| Player, firearm | 3,273 (all three player rows; includes 908 hits on corpses) | `P (…)[HP: 12.4754] hit by Player "Bravo" (…) into Torso(11) for 65.0246 damage (Bullet_9x39AP) with VSS from 3.81352 meters ` |
| Player, melee | ″ | `… hit by Player "Bravo" (…) into Head(0) for 25 damage (MeleeSharpHeavy_1) with Machete` |
| Player, fists | ″ | `… hit by Player "Bravo" (…) into Torso(1) for 10 damage (MeleeFist_Heavy)` (no `with`) |
| Infected / animal | 26,699 | `… hit by Infected into LeftLeg(8) for 5.85 damage (MeleeInfected)` / `hit by Wolf into Head(0) for 10 damage (MeleeWolf)` |
| Trap, no zone | 15 | `… hit by TripwireTrap into (-1) for 0 damage (TripWireHit)` |
| Explosion | 231 | `… hit by explosion (LandMineExplosion)` (no source named) |
| Object | 1,630 | `… hit by Fence with BarbedWireHit` / `hit by Hatchback_02_Black with TransportHit` / `hit by Fireplace with FireDamage` |
| Fall | 144 | `… hit by FallDamageHealth` (only when health damage > 0) |
| Block | 0 | `… hit by … into Block(n) for 0 damage ` `[source only]` |
| Stun | 0 | `… stunned by <ammo>` (`[source]`: "unused atm") |

- **Infected and animal hits use the display name**: `Infected`, `Wolf`.
  Traps and objects use the classname via `GetType()`.
- **`Dummy_Light` 0-damage infected hits are the single largest hit class**
  (12,676 of 26,699) `[corpus]`. They are infected swings that connected for
  no health damage. They are hits, not noise to drop blindly, but they carry
  no damage.
- **Zone and component:** `into Torso(11)`. The number is the hit component.
  A trap with no zone prints `into (-1)`, with an empty zone and component
  −1 `[corpus]`. A pattern of `\w+\(\d+\)` drops it.
- **Corpse hits.** `(DEAD)[HP: 0] hit by …` lines follow a kill in the same
  second, including hits from a different player `[corpus: 908 PvP corpse
  hits]`. **Order within a second is not causal.** The kill line can come
  before the hit that caused it.
- **Dead attackers:** the attacker block can carry `(DEAD)` too, on kills
  and on hits against a living victim `[corpus: 27 lines]`.
- **Vehicle hits name the vehicle, not the driver.** `hit by Offroad_02 with
  TransportHit` identifies no one.

## Building and placement

Gated by `adminLogPlacement` and `adminLogBuildActions` `[source]`.

| Shape | Count | Example |
|---|---|---|
| Placed | 3,228 | `… placed Fence Kit<FenceKit>` / `placed Nameless Object<GardenPlot>` |
| Built | 5,785 | `…)Built wall_base_down on Fence with Hammer` |
| Dismantled | 663 | `…)Dismantled Lower Frame from Fence with Hatchet` |
| Shelter | 33 | `… built ShelterStick with Hands ` (lowercase, trailing space, **ungated**) |
| Folded | 166 | `… folded Fence` |
| Packed | 154 | `… packed Large Tent with Hands` |
| Repaired | 32 | `… repaired Gate with Hammer` |
| Flag | 113 | `… has raised Flag_Livonia on TerritoryFlag at <4512.250000, 221.500000, 8034.750000>` |
| Debug string | 268 | `…)Player SurvivorBase<0x0000024…> SurvivorM_Lewis:20305 Mounted BarbedWire on Fence` |

- **`Built` and `Dismantled` have no space after the paren.** `placed`,
  `built`, `folded`, `packed` and `repaired` do.
- **`Built` names the part by its id; `Dismantled` by its display name.**
  `Built wall_base_down`, but `Dismantled Lower Frame`. 471 of 663 dismantle
  lines have a multi-word part `[corpus]`. A `Dismantled (\S+) from` pattern
  drops 71% of them. The 29% it keeps (`Base`) still do not match the `base`
  the build line recorded, so the two cannot be joined on part name.
- **`placed` shows `display<classname>`**, and the display name can be the
  literal `Nameless Object` `[source]`.
- **The flag position is `<x, altitude, z>`, altitude in the middle.** It
  is the object's raw vector, not the player prefix's `x, z, y`. **Two
  orderings in one line** `[source: totem.GetPosition() + corpus]`.
- **Debug-string lines are a Bohemia bug.** An action's admin message embeds
  the player object's debug name (`Player SurvivorBase<0x…> SurvivorM_Lewis:NNNNN`)
  instead of prose. The verb follows: `Mounted BarbedWire on`,
  `Unmounted BarbedWire from`, `Dug in SeaChest<0x…> SeaChest:NNN at position <…>`,
  `Dug out UndergroundStash<…>`. The hex address and number vary from line to
  line.

## Other

| Shape | Count | Example |
|---|---|---|
| Emote | 6,100 | `… performed EmoteSitA` / `performed EmoteSuicide with SteakKnife` |
| Teleported | 1,331 | `… was teleported from: <4767.481934, 339.441010, 10376.478516> to: <5154.072754, 56.397713, 1075.143311>. Reason: Spawning in Player Restricted Area: RestrictedAreaBunkerEntrance` |

- **Teleport `from:`/`to:` values are `<x, altitude, z>`**, altitude in the
  middle, with six decimals. The same line's `pos=` is `x, z, y`. Getting
  this backwards swaps a horizontal axis with the vertical.
- The reasons in source are `Spawning in Player Restricted Area: <areaName>`
  and `Unwillingly spawning in contaminated area.` `[source + corpus]`. PRA
  teleports only fire at spawn and login. See `dayz-cfggameplay` for PRAs.
- `EmoteSuicide with <item>` is the start of the animation. It is not the death.

## Never seen on console

These shapes are in source (or are claimed for PC) and have **zero** lines in
146k console lines:

- **Chat and `#toadmin` reports.** Source lists them as exe-side. Their format
  is `[unverified]`, and none appear on Xbox.
- `stunned by`, `into Block(…)`, `has drowned while unconscious`,
  `is disconnecting while being restrained`.

A parser may include them. A skill may not quote a format for them.

## Gating switches

`serverDZ.cfg` keys, read in `PluginAdminLog()` `[source]`. On Nitrado they
are panel toggles `[operator]`:

| Key | Nitrado toggle | Effect |
|---|---|---|
| `adminLogPlayerHitsOnly` | **Log Damage** | `1` **drops** infected and animal hit lines. Traps, objects, falls and explosions still log. |
| `adminLogPlacement` | Log Placement | `placed …` lines |
| `adminLogBuildActions` | Log Basebuilding | Built, Dismantled, folded, packed, repaired, flag raise/lower, debug-string lines |
| `adminLogPlayerList` | Log Playerlist | The 300 s PlayerList block |

**"Log Damage" is inverted from its label** `[operator]`: turning it **on**
logs **less**. It is the hits-*only* filter. Nitrado's help text says so
("select to log only damage done by players"), but the name reads the
other way.

Connect, disconnect, deaths, consciousness, emotes, teleports and the
shelter `built` line are not gated (`sheltersite.c` calls
`DirectAdminLogPrint`, which skips the filter). The panel's "Admin Log" toggle turns the whole file on or off.
