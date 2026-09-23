# Deaths, respawns and attribution

The ADM never says "X caused Y's death" in one reliable place. It writes the
death line the engine's `EEKilled` handler produced, plus whatever other
lines happened to fire around it. Attribution means reading a **sequence**.

Tags as in [lines.md](lines.md). Examples are real lines with names and ids
replaced. Counts are from 146,308 production lines. Quick reference:

| You see | It means | It is not |
|---|---|---|
| `(DEAD)` on the victim block | the player was not alive when the line was written | a death event by itself |
| `killed by Player "B" … with W` | PvP kill, killer named | the only PvP death shape |
| ` died. Stats> …` | the engine had no killer object | "unknown cause", necessarily |
| `is choosing to respawn`, alive | the player pressed Respawn while down; death follows | a respawn after death |
| `(DEAD) … is choosing to respawn` | the respawn button on an already-logged death | a second death |
| `is connected` right after a death | the respawn | a join |

---

## `(DEAD)` is state, not an event

`GetPlayerPrefix()` appends `(DEAD)` whenever `!player.IsAlive()` at write
time `[source]`. The consequences:

- **The death line itself carries it**, because `EEKilled` runs after health
  reaches zero.
- **Every later line about the corpse carries it:** hits on the body, a
  corpse `is unconscious`, a corpse in the PlayerList, and the
  `(DEAD) … is choosing to respawn` form.
- **A killer can carry it.** If the killer died first, even in the same
  second, the attacker block reads `Player "B" (DEAD) (id=…)`
  `[corpus: 27 lines]`. A kill pattern that does not allow `(DEAD)` on the
  attacker files the kill as environmental. One Life's `death.ts` has this
  defect; Clan Wars fixed it on 2026-09-10.

Count deaths from death **shapes**, never from the first `(DEAD)` you see.

## PvP: the normal sequence

```
11:44:24 | Player "Alpha" (id=AAAA… pos=<…>)[HP: 77.5] hit by Player "Bravo" (id=BBBB… pos=<…>) into LeftLeg(10) for 90 damage (Bullet_9x39AP) with VSS from 3.81352 meters 
11:44:24 | Player "Alpha" (id=AAAA… pos=<…>)[HP: 12.4754] hit by Player "Bravo" (id=BBBB… pos=<…>) into Torso(11) for 65.0246 damage (Bullet_9x39AP) with VSS from 3.81352 meters 
11:44:24 | Player "Alpha" (id=AAAA… pos=<…>) is unconscious
11:44:25 | Player "Alpha" (DEAD) (id=AAAA… pos=<…>)[HP: 0] hit by Player "Bravo" (id=BBBB… pos=<…>) into Torso(24) for 74.1546 damage (Bullet_9x39) with VSS from 4.6779 meters 
11:44:25 | Player "Alpha" (DEAD) (id=AAAA… pos=<…>) killed by Player "Bravo" (id=BBBB… pos=<…>) with VSS from 4.67798 meters 
11:44:33 | Player "Alpha" (DEAD) (id=AAAA… pos=<…>) is choosing to respawn
11:44:40 | Player "Alpha" (id=AAAA… pos=<10482.0, 13460.6, 3.5>) is connected
```

- **Within one second, order is not causal.** The kill line can come before
  the fatal hit. Several hits share a timestamp in a burst. Clan Wars' fix:
  among hits in the same second, **the lowest `[HP]` is the last hit**.
  Sorting by time alone missed two of four credits in their data
  `[project: CW death-verdict.ts]`.
- **Hits keep arriving after the kill** `[corpus: 908 PvP corpse hits]`,
  including from a **different** player:

  ```
  23:52:39 | Player "Alpha" (DEAD) (…) killed by Player "Bravo" (…) with Kolt 1911 from 2.2467 meters 
  23:52:39 | Player "Alpha" (DEAD) (…)[HP: 0] hit by Player "Charlie" (…) into Torso(24) for 75 damage (Bullet_9x39AP) with VSS from 2.86844 meters 
  ```

  Credit the kill line's killer. Charlie shot a corpse.
- **The respawn tail** (`is choosing to respawn`, `is connected`) is
  covered in [Respawns](#respawns) below.

## Deaths with no killer on the line

### Explosives and the 40mm grenade

- `killed by 6-M7 Frag Grenade`, `killed by Claymore`: the `ExplosivesBase`
  branch never names a thrower `[source]`.
- `killed by  with 40mm Explosive Grenade`, **two spaces**, comes from the
  melee branch with an empty killer prefix `[source + corpus: 13]`. The
  shooter is gone. Three M79 kills *do* name a killer (`… with M79 from
  15.3775 meters`, and two self-kills at 0 m). What decides which form a 40mm
  death gets is `[unverified]`. No source path explains the split. The
operator **believes** a direct hit with the grenade gives kill credit and a
splash kill does not `[operator: belief, not tested]`. That fits the named
kills, but no in-game test has confirmed it. Treat it as a lead: a staged test
(one direct hit, one splash) would settle it.
- A self-kill with your own M79 exists: `Player "A" (DEAD) … killed by
  Player "A" (DEAD) … with M79 from 0 meters` `[corpus: 2]`. Never credit
  a self-kill.

Recovering a thrower means correlating `placed …<LandMineTrap>` lines or
nearby players by position. That is inference; say so when you use it.

### ` died. Stats>`: the bare death

When `EEKilled`'s killer is the player itself, source writes
` died. Stats> Water: n Energy: n Bleed sources: n` (or ` drowned.`)
`[source]`. That happens far more often than "starved":

| What happened | What the log shows |
|---|---|
| Starvation / dehydration | `died.` with `Energy:` or `Water:` near 0 (the game reports 0) |
| Fall | `hit by FallDamageHealth` (HP ≤ 0) then `died.` |
| Bled out | `died. … Bleed sources: n` **and** a `bled out` line in the same second `[corpus: 13]` |
| Respawn while unconscious | `is choosing to respawn` then `died.` in the same second |
| Logged out while unconscious | `is disconnecting while being unconscious` then `died.` |
| Suicide | `died.` plus `committed suicide`, order depending on weapon (below) |
| Finished by a player, killed by bleed/shock tick | player hits, maybe `is unconscious`, then `died.` |
| Admin respawn / nothing visible | `died.` with nothing before it |

Of 515 bare `died.` lines in the corpus, 141 were suicides, 14 were
unconscious logouts, 11 were falls and 9 were unconscious respawns. **328
had nothing distinctive in the four lines before them.** Attribution for
those is inference from the recent hits.

**If `adminLogPlayerHitsOnly` is on** (Nitrado's "Log Damage"), infected and
animal hit lines are never written `[source]`. Every inference below that
reads infected hits (mauled, the knock-out corroboration) then has nothing to
read. It silently falls through to "died", with no error. Check the switch
before trusting a cause breakdown. All four servers studied here run it off.

**The worked solution** is Clan Wars'
`packages/domain/src/death-verdict.ts`, lifted from One Life's module and
checked against every bare death in One Life's production data
`[project]`. It infers a cause only for a bare `died.`, from the 120 s
before it:

1. A `FallDamage*` hit with HP ≤ 0 → fall.
2. Energy < 1 → starvation. Water < 1 → dehydration.
3. Infected hits **and** (bleeding, or knocked out, or minimum infected HP ≤ 1) → mauled.
4. Bleeding plus any hit → bled out.
5. Otherwise → died.

Its `finishedBy()` credits the **last player hitter** when the victim's HP
was ≤ 25 after that hit, or a knockout followed it, **and** nothing
non-player damaged the victim afterwards. It reports `cause = 'finished'`,
not a kill the log stated. **Keep that distinction in any tool you build:**
a credited kill that the log did not state is an inference, and the record
should say so.

### Infected knock-outs at high health

Infected deal **shock**, which never appears in `[HP: n]`. A player can go
`is unconscious` at HP 70+ and then die `[corpus + project: OL]`:

```
19:19:59 | Player "Alpha" (…)[HP: 83.3336] hit by Infected into RightLeg(3) for 5.85 damage (MeleeInfected)
19:19:59 | Player "Alpha" (…) is unconscious
19:20:01 | Player "Alpha" (…)[HP: 69.6836] hit by Infected into Torso(1) for 6.5 damage (MeleeInfected)
19:20:01 | Player "Alpha" (…) is choosing to respawn
19:20:01 | Player "Alpha" (DEAD) (…) died. Stats> Water: 728.293 Energy: 949.375 Bleed sources: 1
```

A rule of "HP near zero means the hits killed them" misses these.

## Respawns

### `is choosing to respawn` has two forms, and only one is a death

Source writes it from `OnClientRespawnEvent` only if the player
`IsUnconscious() || IsRestrained()`, then sets health to 0 `[source:
missionserver.c]`. The corpus shows two forms `[corpus: 52]`:

**Alive: the respawn causes the death.** 9 cases, all on One Life, and
none had a player hit in the 120 s before.

```
15:21:26 | Player "Alpha" (…) is unconscious
15:21:33 | Player "Alpha" (…) is choosing to respawn
15:21:33 | Player "Alpha" (DEAD) (…) died. Stats> Water: 664.646 Energy: 1044.27 Bleed sources: 2
15:21:38 | Player "Alpha" (…) is connected
```

The death line names no killer. Attribute it from the hits before the
knockout.

**`(DEAD)`: the death was already logged.** 43 cases, including PvP. 36 are
on Clan Wars and 7 on One Life. Clan Wars hides the Respawn button while
unconscious, so this form comes from the **death screen's** respawn, not the
unconscious menu.

```
15:28:30 | Player "Alpha" (DEAD) (…) died. Stats> … Bleed sources: 5
15:28:30 | Player "Alpha" (DEAD) (…) bled out
15:28:34 | Player "Alpha" (DEAD) (…) is choosing to respawn
15:28:39 | Player "Alpha" (…) is connected
```

The body still carries the unconscious flag, so pressing Respawn on the
death screen writes the line. **It is not a second death.** Neither the
Clan Wars nor the One Life parser matches this line at all today, which
happens to be safe. A parser that treats every `is choosing to respawn` as a
death double-counts.

### Only possible where the server allows it

`disableRespawnInUnconsciousness` hides the Respawn button while down
(`ingamemenuxbox.c: ShouldRestartBeVisible`) `[source]`. Script reads it
**only from `cfggameplay.json`**. When the JSON is enabled, Nitrado's panel
toggle "Disable respawning in unconsciousness" does nothing. Clan Wars'
panel shows it **off**, its JSON says `true`, and the button is gone in
game `[operator]`. So:

- A server running `true` in the JSON has written **zero** alive-form lines
  (Clan Wars: 0 of 36) `[corpus]`.
- It still writes the `(DEAD)` form. Setting `true` does not make the line
  disappear. A player the server killed while restrained would also write
  it `[source]`; none have been seen.

### Respawns write `is connected`

After any death, the new character arrives with `is connected` and no
disconnect, 5–15 s later `[corpus: 763 respawns]` `[operator]`. See
[lines.md](lines.md#sessions-exe).

**Plausible and wrong:** "that only happens when `economy.xml` has
`<player save="0">`." A deathmatch server with `save="0"` was the first place
this was noticed. The One Life servers run `save="1"` and do it on every
respawn.

## Unconscious logouts

```
09:25:31 | Player "Alpha" (…) is unconscious
09:25:44 | Player "Alpha" (…) has been disconnected
09:25:44 | Player "Alpha" (…)[HP: 99.3825] hit by Infected … (MeleeInfected)
09:25:58 | Player "Alpha" (…) is disconnecting while being unconscious
09:25:58 | Player "Alpha" (DEAD) (…) died. Stats> … Bleed sources: 0
```

When a client leaves while unconscious or restrained, the server kills the
body `[source: MissionServer.HandleBody]`.

- **`has been disconnected` often comes first** (8 of 14 cases `[corpus]`),
  and the body keeps taking hits after it. The death arrives seconds later,
  when the server handles the body. Do not require either order.
- **The death is the server's, not an attacker's.** Whether that counts as
  a combat log is a policy question. One Life decided not to label it
  publicly, because it reads as an accusation `[project: OL]`.

## Suicide

`committed suicide` comes from two source paths, and the corpus splits
exactly along them `[source + corpus: 439]`:

| Weapon | Count | Order | Victim block on the suicide line |
|---|---|---|---|
| Firearm or crossbow (Glock19 224, M14 5, …) | 291 | `committed suicide` **then** `died.` | alive |
| Blade or tool (SteakKnife 93, HuntingKnife 34, Hatchet 9, Pickaxe, Screwdriver, …) | 148 | `died.` **then** `committed suicide` | `(DEAD)` |

291 + 148 = 439, every suicide in the corpus, with no third order. Seven had
no `EmoteSuicide` line to name the item, and they split the same way.

- **Firearm:** `EmoteManager` logs `Suicide()` while `m_Player.IsAlive()`,
  and queues the kill.
- **Blade:** `LogSuicide()` fires from the animation event after death.

A parser that expects one order mis-files half of all suicides. Match on the
same id and the same second. The `performed EmoteSuicide with <item>` line
before either marks the start of the animation, not the death.
