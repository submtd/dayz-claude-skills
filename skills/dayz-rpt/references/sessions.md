# Logins, devices and logouts in the RPT

The RPT is the only log that shows a login **in progress**. The ADM records
only that one happened. Tags as in [format.md](format.md). Examples are real
lines with names and ids replaced.

## A join, start to finish

```
 9:04:44.462 [StateMachine]: Player Alpha (dpnid 1234567890 uid ) Entering AuthPlayerLoginState
 9:04:44.743 [StateMachine]: Player Alpha (dpnid 1234567890 uid ) Entering WaitAuthPlayerLoginState
 9:04:47.430 Player Alpha (id=AAAA…) connecting
 9:04:47.445 [StateMachine]: Player Alpha (dpnid 1234567890 uid ) Entering WaitPlayerAssignedLoginState
 9:04:48.170 [StateMachine]: Player Alpha (dpnid 1234567890 uid ) Entering PlayerAssignedLoginState
 9:04:48.186 [StateMachine]: Player Alpha (dpnid 1234567890 uid AAAA…) Entering DBGetLoginTimeLoginState
 9:04:48.217 [StateMachine]: Player Alpha (dpnid 1234567890 uid AAAA…) Entering DBWaitLoginTimeLoginState
 9:04:53.223 [StateMachine]: Player Alpha (dpnid 1234567890 uid AAAA…) Entering DBGetCharacterLoginState
 9:04:53.254 [StateMachine]: Player Alpha (dpnid 1234567890 uid AAAA…) Entering CreateNetObjectsLoginState
 9:04:53.270 [StateMachine]: Player Alpha (dpnid 1234567890 uid AAAA…) Entering PreloadCamLoginState
 9:04:53.270  NETWORK      : Login: Player Alpha (1234567890) preloading at: 4100.500000 212.250000 7300.750000, yaw: 1.870095, new: 0
 9:04:53.270 [StateMachine]: Player Alpha (dpnid 1234567890 uid AAAA…) Entering WaitPreloadCamLoginState
 9:04:57.930 [StateMachine]: Player Alpha (dpnid 1234567890 uid AAAA…) Entering GetLoadedCharLoginState
 9:05:00.341 Player Alpha (id=AAAA… pos=<4100.5, 7300.7, 212.2>) has connected.
```

- **The `uid` is empty for the first four states**, until
  `DBGetLoginTimeLoginState`, on every login in the corpus (230 of 230). A parser that keys on the uid from the first
  line gets an empty string. Key on `dpnid` until the uid appears, or wait
  for `has connected.`.
- **`dpnid` is a per-connection number, not an identity.** Use the 40-hex
  `uid`/`id`, which is the same id the ADM prints.
- **The RPT says `connecting` and `has connected.`** The ADM says `is
  connecting` and `is connected`. Test fixtures that swap them test nothing.
- **Two coordinate orders in one login.** `preloading at: 4100.50 212.25
  7300.75` is the engine vector `x, altitude, z`. `has connected.` is `<x, z,
  altitude>`, the same as the ADM's player block.
- **Loaded versus new character.** A login ends in
  `GetLoadedCharLoginState` (202 in the corpus) or `GetNewCharLoginState`
  (25). Going by the state names, those are an existing character being
  loaded and a fresh spawn. What the preload line's `new: 0/1` flag
  tracks is `[unverified]`.
- **Queue entry** comes first: `[Login]: Adding player Alpha (N) to login
  queue at position N`, or `Adding prioritized player` for someone on the
  panel's prioritized list.
- **Login duration** from `AuthPlayerLoginState` to `has connected.` was
  16 s in this example. The `DBWaitLoginTime` state accounts for 5 s of it.

## Device: console or PC crossplay

```
 NETWORK      : Notified of player 987654321 using device 'console' (headless)
 LOGINQUEUE   : Player 987654321 updated with device type 'console'
```

- **The only place platform is logged.** The ADM does not carry it.
- **`'desktop'` is a PC crossplay player** `[operator]`. The Clan Wars Xbox
  server logged 1 and 2 `desktop` joins in two sessions, and `console` for
  everyone else `[corpus]`.
- The number is the `dpnid`, so join it to the state-machine lines to get a
  name and uid.

## Joins versus respawns

**Respawns run their own state machine**, with an **empty uid** throughout
`[corpus: 36]`:

```
[StateMachine]: Player Alpha (dpnid N uid ) Entering GetCharacterRespawnState
[StateMachine]: Player Alpha (dpnid N uid ) Entering GetNewCharRespawnState
[StateMachine]: Player Alpha (dpnid N uid ) Entering PreloadCamRespawnState
[StateMachine]: Player Alpha (dpnid N uid ) Entering WaitPreloadCamRespawnState
```

**Every respawn writes `has connected.`**, just as the ADM writes `is
connected`. The RPT and ADM counts from the same boot match exactly:

| Boot | RPT `connecting` / `has connected.` | ADM `is connecting` / `is connected` |
|---|---|---|
| 09:02 | 17 / 18 | 17 / 18 |
| 11:01 | 33 / 42 | 33 / 42 |
| 13:02 | 49 / 53 | 49 / 53 |
| 15:02 | 77 / 96 | 77 / 96 |

A `has connected.` with a `connecting` before it (for that player) is a
join. Without one, it's a respawn. Pair them **per player**. A login that
never completes has a `connecting` and no connect, so subtracting totals
produces negative respawns.

## Disconnects

The engine writes its own sequence, keyed by `dpnid` `[corpus]`:

```
[Disconnect]: Start script disconnect 1234567890 (dbCharacterId N dbPlayerId N) logoutTime 15
[Disconnect]: Finish script disconnect 1234567890 (AAAA…)
[Disconnect]: DisconnectPlayerFinish 1234567890
[Disconnect]: Remove player info 1234567890
[Disconnect]: Player destroy 1234567890
```

| Line | Count | Note |
|---|---|---|
| `Start script disconnect` | 236 | carries `logoutTime`, the same value as `[Logout]` below |
| `Finish script disconnect` | 185 | 41 more carry a **negative** dpnid, meaning is `[unverified]` |
| `Cancel script disconnect` | 9 | the logout was cancelled |
| `Client N early disconnect` | 66 | left before the login finished, `[unverified]` beyond the name |
| `No packets from N`, then `Player X (N) kicked from server: N (Connection with host has been lost.)` | 9 | a network timeout, not an admin kick |

The ADM's `has been disconnected` is the gameplay-side record of the same
event.

## Logouts

From `MissionServer.OnClientDisconnectedEvent` and its timer `[source:
missionserver.c]`:

```
SCRIPT : [Logout]: New player AAAA… with logout time 15
SCRIPT : [Logout]: Player AAAA… finished
SCRIPT : [Logout]: New player AAAA… with instant logout
SCRIPT : [Logout]: Player AAAA… cancelled
```

- **`logout time N`** is a value the engine passes in. The character stays
  in the world for N seconds after the player leaves `[source: LogoutInfo
  timer]`. It was 15 in 186 cases and 0 in 43, and there were 6 `instant
  logout` lines `[corpus]`. Which config key sets it, and what decides 0
  versus 15, is not in script `[unverified]`.
- **`cancelled`** means the player cancelled the logout countdown
  (`LogoutCancelEvent`) `[source]`.
- **`finished`** means the timer ran out. The logout can no longer be
  cancelled, and the disconnect handlers run `[source: PlayerDisconnected]`.
- **`Print()` from mission script reaches the RPT.** These lines prove it.
  A Clan Wars finding that `Print` is silent applies to `init.c`, not to
  mission script generally.

## Periodic lines that look like events

- `Saved N players ...`: written periodically. It is not a logout. It
  printed `Saved 0 players` on empty servers `[corpus]`; exactly what
  triggers it is `[unverified]`.
- `SCRIPT : ---- PlayerBase OnStoreLoad SUCCESS ----`: printed at the end
  of `PlayerBase.OnStoreLoad`, when a character is restored from storage
  `[source: playerbase.c]`. It carries no name, so correlate by time.
