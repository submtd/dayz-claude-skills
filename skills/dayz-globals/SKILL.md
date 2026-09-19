---
name: dayz-globals
description: Use when working with a DayZ server's db/globals.xml or central economy tuning — loot damage and item condition, cleanup and corpse lifetimes, loot respawn rates, initial and restart spawn percentages, territory flag refresh, idle mode, login/logout/hopping timers, zombie and animal population caps, food decay — or when a globals.xml change did not take effect.
---

# DayZ db/globals.xml

Thirty central-economy tuning variables, read from `db/globals.xml` in the
mission folder. Vanilla source: `BohemiaInteractive/DayZ-Central-Economy`.

**Vanilla `globals.xml` is identical across Chernarus, Livonia and Sakhal.**
Unlike `cfggameplay.json`, there is no per-map variance to reconcile.

**These servers are Xbox on Nitrado.** No mods; `init.c` is inert. See the
`dayz-cfggameplay` skill for what that rules out.

## Never answer from memory

Every variable name, default and unit **must** come from `references/vars.md`.
An agent asked eight routine questions about this file said `ZombieMaxCount`
does not exist ("that's not in globals.xml"), put `CleanupLifetimeDefault` at
~14 days when it is **45 seconds**, inverted `FlagRefreshMaxDuration`, read
`IdleModeStartup` as a duration when it is a 0/1 flag, and invented an
elaborate wrong story for `InitialSpawn` / `SpawnInitial` / `RestartSpawn`.
Only the `type` attribute came back right.

**The wiki is also wrong twice** — `LootDamageMax` and `LootSpawnAvoidance`
defaults disagree with every shipped file. `references/vars.md` marks each
claim **[source]**, **[wiki]** or **[unverified]**. Do not promote an
`[unverified]` claim to fact.

## The rule that matters most

**Almost nothing in this file works alone.** Every variable here that has real
gameplay effect is half of a pair with another file. Changing one side and not
the other is the characteristic failure — it produces no error and no result.

| To change | You must also touch | Why |
|---|---|---|
| Loot condition (`LootDamage*`) | `cfgspawnabletypes.xml` | **Any `<damage>` entry there wins**, including `0.0/0.0` |
| Base cleanup speed (`FlagRefresh*`) | `db/types.xml` lifetimes | The flag only postpones those lifetimes |
| Infected density (`ZombieMaxCount`) | `env/zombie_territories.xml` | The cap does not spawn anything |
| Animal density (`AnimalMaxCount`) | `env/*_territories.xml` | Same |
| `FoodDecay` | `WorldWetTempUpdate` **in this file** | Food decay requires it set to `1` |

Details and worked examples in `references/cross-file.md`. **Read it before
changing loot condition, base decay or infected counts.**

## Things that are not what they look like

- **`CleanupLifetimeDefault` is not a `types.xml` fallback.** It is **45
  seconds**, for entities with no economy setup **and damage ≥ 1.0** — a
  sweeper for untracked dead or ruined things.
- **`ZombieMaxCount` is a ceiling, not a lever.** Raising it spawns nothing on
  its own; lowering it silently clips your zone definitions.
- **`FlagRefreshMaxDuration` is how long the flag keeps refreshing**, not a
  grace period before decay. **[source]** `totem.c:12`.
- **`IdleModeStartup` is a 0/1 flag**, not a duration.
- **`InitialSpawn` and `RestartSpawn` are percentages; `SpawnInitial` is a
  retry count.** Different things despite the near-identical names.
- **`RestartSpawn` defaults to `0`** — restarting does *not* top loot up.
- **Damage is a durability budget, not just condition.** An item at `0.8`
  ruins after one use, which makes it a single-use key. See `cross-file.md`.
- **`TimeHopping` penalises your incoming players.** It is added to the login
  timer for anyone arriving from another server — i.e. every new player.

## Diagnosing "I changed it and nothing happened"

1. **Is it half of a cross-file pair?** Check the table above first. This is
   the most common cause by a wide margin.
2. **Did the server restart?** These are read at startup.
3. **Does the `type` attribute match the value?** A float written under
   `type="0"` is truncated silently. Only `LootDamage*` are floats.
4. **Is it session-scoped, and does your restart interval outlive it?** A
   2-hour restart cycle means any session countdown longer than 7200s never
   elapses — that is why One Life's `IdleModeCountdown: 21600` is effectively
   "never". Lifetimes and flag refresh are persistent in CE storage and are
   *not* reset by restarts.
5. **Is a player standing there?** `CleanupAvoidance` and `LootSpawnAvoidance`
   are both 100m, so nothing spawns or is deleted inside a 100m bubble around
   any player.
6. **Run the validator** — it checks the cross-file pairs.

```sh
python3 skills/dayz-globals/scripts/validate.py /path/to/mission/db/globals.xml
```

## Item condition scale

Damage runs `0.0` (pristine) to `1.0` (ruined). Confirmed boundaries:

| Damage | Condition |
|---|---|
| `0.0` | Pristine |
| `0.25` | Worn |
| `0.8` | Badly damaged |
| `1.0` | Ruined |

**[unverified]** Where badly-damaged becomes ruined is not established. Do not
state a cutoff.

## House conventions (One Life / Clan Wars)

One Life keeps all three maps in sync — the same seven deviations everywhere,
maintained from `../globals.xml` in the parent folder. Clan Wars has nine.

| Variable | Vanilla | One Life | Clan Wars |
|---|---|---|---|
| `LootDamageMin` | `0.0` | **`0.25`** | `0.0` |
| `LootDamageMax` | `0.82` | `0.82` | **`0.0`** |
| `FoodDecay` | `1` | `1` | **`0`** |
| `RespawnTypes` | `12` | `12` | **`25`** |
| `FlagRefreshMaxDuration` | `3456000` | **`604800`** | **`1209600`** |
| `IdleModeStartup` | `1` | **`0`** | **`0`** |
| `IdleModeCountdown` | `60` | **`21600`** | **`0`** |
| `TimeHopping` | `60` | **`0`** | **`0`** |
| `TimeLogin` | `15` | **`5`** | **`5`** |
| `TimePenalty` | `20` | **`0`** | **`0`** |

**The loot damage rows are a deliberate philosophical split.** One Life spawns
loot damaged (`0.25`–`0.82`, never pristine) — degraded gear is a decision and
repair matters. Clan Wars spawns everything pristine (`0.0`–`0.0`) — item
condition is friction between players and the fight, and an unequal random roll
is unfair rather than interesting.

**Clan Wars is a coherent base-decay system**, and this is the reference
example: base parts at `604800` (7 days) in `types.xml`, flag refreshing every
5 days for up to 14. Stop maintaining a base and it is gone in a week. That is
the intent, and it works.

**⚠ One Life's `FlagRefreshMaxDuration: 604800` is a known-broken artifact.**
It was shortened from 40 days to 7 to clean up abandoned bases faster, before
the mechanic was fully understood — but base part lifetimes were left at
vanilla `3888000` (45 days). Since the flag only postpones those lifetimes, a
7-day refresher on a 45-day lifetime does almost nothing.

- **Do not "normalise" it back to vanilla** as though it were drift. It is
  there on purpose, aiming at a real goal.
- **The actual fix is `types.xml`**: shorten lifetimes on `Fence`,
  `Watchtower`, tents and containers, then set `FlagRefreshMaxDuration` to a
  sensible multiple of `FlagRefreshFrequency`.
- The operator intends to revisit this. Offer the fix; do not apply it unasked.

**Both servers zero the hopping penalties** — `TimeHopping` and `TimePenalty`
to `0`, `TimeLogin` to `5`, `TimeLogout` left at vanilla `15`. The reasoning is
player retention, not fast travel: the penalty is added to the login timer for
players arriving from another server, so it punishes exactly the people you are
trying to attract. Leaving `TimeLogout` at 15 keeps the combat-logging
deterrent — *leaving* stays costly, *arriving* does not.

**Both disable idle mode.** On Nitrado you pay for the box regardless, so there
is no saving to capture, and a frozen economy overnight means the first player
on in the morning finds a stale world. Clan Wars does it with `0`/`0`; One Life
with `0`/`21600`, which its 2-hour restart cycle makes equivalent.

**Clan Wars leaves two `<damage>` entries in `cfgspawnabletypes.xml`** —
`PunchedCard` and `ShippingContainerKeys_Red`, both at `0.8/0.8`. These are
deliberate single-use keys, not a missed strip. See `cross-file.md`.

## Editing

Same discipline as `cfggameplay.json`: **splice, do not reserialize.** Change
the bytes you mean to change; leave the rest byte-identical so the diff is
reviewable. Commit messages should name the gameplay effect and give
before/after values, since these are numbers someone will want to diff later.

A deploy is not a live change — the server reads this at startup.
