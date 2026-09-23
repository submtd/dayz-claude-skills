# CLAUDE.md

Working notes for building skills in this repo. `README.md` is for people
installing the plugin; this file is for whoever is authoring the next skill.

**Read this before starting a new skill.** It exists so each session does not
re-derive the same facts, re-trust the same bad sources, or repeat corrections
the operator has already made.

## The first rule: never assume

**If you think you know something, ask for confirmation before acting on it
or writing it down.** This applies to everything — DayZ mechanics, what a
live server does, operator intent, which skill to build next, what to name a
branch, whether to land a PR. A plausible belief is not a fact until source,
a shipped file, or the operator confirms it.

- **State your read, then ask.** "I believe X because Y — is that right?" is
  the shape. Do not present an inference as a finding, and do not quietly
  proceed on one.
- **An unconfirmed claim stays `[unverified]`.** Filling a gap with a good
  guess is the failure mode this repo exists to prevent.
- **This has already gone wrong.** "Tiers are unreachable on console" and
  "Clan Wars' contaminated-area loot is stranded" were both inference
  written up as findings, and both were wrong. See the `areaflags.map`
  constant below.

## What this repo is

A Claude Code plugin (`dayz`) holding skills for DayZ server development. Each
skill is `skills/<name>/` with `SKILL.md`, optional `references/` for heavy
lookup material, and optional `scripts/` for tooling.

**The goal is expertise at all things DayZ** — not support documentation for
any one server. A skill should make the reader expert on its subject in
general: the mechanism, its traps, what the documentation gets wrong, and how
PC and console differ. The point is not to summarise the DayZ wiki; it is to
capture **what the wiki gets wrong, what only the engine source settles, and
what only the operator knows.**

Two consequences that are easy to get backwards:

- **The live servers are evidence, not the subject.** They are how a claim
  gets verified and how Bohemia's own defects get caught. Operator intent goes
  in as an illustration of a general technique, not as a record of what one
  server happens to do. Write "here is how to disable loot at one location,
  and here is a server that did it," never "here is what Clan Wars does."
- **A console constraint is a consequence, not the universe.** Document the
  general mechanism first, then what it costs on Xbox/Nitrado. Saying
  something is impossible when it is merely awkward is the failure mode — see
  `areaflags.map` under the domain constants, where "tiers are unreachable on
  console" was wrong and the real answer is "you need a PC to author the
  file."

The scope runs past the CE mission tree: modding, Enforce script, map editing
and PC-side tooling are all in it, and the priority list below should grow in
that direction rather than stopping at the XML.

## The servers these skills serve

Two projects, four live mission configs, all **Xbox hosted on Nitrado**. They
are the verification corpus — diff against them, do not write *for* them.

| | One Life | Clan Wars |
|---|---|---|
| Repos | `../../dayz-one-life/{chernarus,livonia,sakhal}` | `../../dayz-clan-wars/livonia` |
| Philosophy | **Vanilla-as-possible.** Deviations are deliberate and few | **No survival attrition.** The game is faction warfare |
| Loot | Damaged (`0.25`–`0.82`), never pristine | Pristine (`0.0`–`0.0`) |
| Stamina | Vanilla | Effectively unlimited |
| Food decay | On | Off |
| Base decay | Vanilla 45-day lifetimes | 7-day lifetimes, flag-maintained |

Monorepos with the platform code: `../../dayz-one-life/one-life` and
`../../dayz-clan-wars/clan-wars` (Discord bots, ingest workers, ADM/RPT
parsers, web). Useful as worked examples — Clan Wars' bot is cited in two
skills already.

When a skill needs "what do the live servers actually do," diff those mission
folders against upstream vanilla **for the matching map**. Diffing Livonia
against Chernarus produces false positives every time.

## Domain constants — true for every skill

These have been confirmed by the operator. Do not re-derive or contradict them.

- **Console DayZ has no mod support.** The mission tree is the entire
  customization surface. "Use a mod" is never an answer.
- **`init.c` is inert.** Nitrado loads its own and never reads the one in the
  mission tree. Any advice routing through `init.c` is PC advice. Most DayZ
  documentation, Bohemia's included, assumes it works. **[unverified]** it is
  believed to be the only file Nitrado overrides this way — if some other
  file's settings mysteriously do nothing, retest that belief.
- **Live Xbox servers track `master`**, not a tagged release. Diff against
  `master`.
- **Servers restart every 2 hours.** This caps session-scoped countdowns;
  persistent CE values are unaffected. **A deployed file plus the next
  restart is all it takes to go live** — no manual restart, no storage
  wipe. But CE *effects* settle asymmetrically: raising a `nominal` shows
  up fast, lowering one shows up slowly because the surplus must age out
  through each item's lifetime. Do not judge a reduction after one
  restart.
- **`areaflags.map` is a second loot router, and it is invisible from the
  XML.** A binary raster (~72–80 MB) shipped in the mission tree, carrying
  **map area properties: loot tiers *and* usage areas** — military, hunting,
  contaminated and others. A loot point's effective routing comes from **both**
  the building's `<usage>` in `mapgroupproto.xml` and the area flags where it
  stands. **The example to remember is Polana on Livonia**: mostly ordinary
  houses, spawns military loot, because the area says so.
  - `<value name="TierN">` on a surface building **does nothing**.
  - **A usage with no capacity in `mapgroupproto.xml` is not unreachable.**
    You cannot prove loot is stranded by reading the mission XML.
  - Authoring the raster needs **DayZ Tools, PC-only**, but **the edited file
    uploads to a console server and works** — the gate is the toolchain, not
    the platform. "No mods on console" does not extend to it.
  - **[unverified]** how the two sources combine. Polana rules out plain
    intersection. **Ask; do not infer.**

  **This constant has caught two wrong conclusions in one session** — "tiers
  are unreachable on console" (wrong: the raster deploys fine) and "Clan Wars'
  `ContaminatedArea` types are stranded because the gas zones are off" (wrong:
  those areas are still flagged contaminated in the raster, so the loot still
  spawns). Both were inference presented as a finding. **When a DayZ mechanism
  is not settled by source, a shipped file or the operator, ask.**
- **Silent failure is the norm.** Unknown keys, wrong nesting, missing
  referenced files, wrong-length arrays — none of these error. The server
  boots clean and the feature is quietly absent. This is why every skill ships
  a validator.

## Sources, in descending authority

**1. Engine source.** `BohemiaInteractive/DayZ-Script-Diff` publishes the game
scripts. This settles arguments.

```sh
gh api -X GET search/code -f q='GetDisableSomeCheck repo:BohemiaInteractive/DayZ-Script-Diff' \
  --jq '.items[]? | .path'
gh api "repos/BohemiaInteractive/DayZ-Script-Diff/contents/<path>" --jq '.content' | base64 -d
```

Config flags are read through `CfgGameplayHandler` accessors
(`scripts/3_game/cfggameplayhandler.c`) and CE globals through
`GetCEApi().GetCEGlobal*`. Searching the accessor name finds every consumer.
This is how `disableDistanceCheck` was found dead and
`disableIsPlacementPermittedCheck` was found to have nothing to do with
territory.

**Caveat:** much of the CE is `proto native` — engine-side C++ — and is *not*
in the script repo. When a lookup turns up only a `proto native` declaration,
say the claim is unverifiable rather than falling back to the wiki.

**2. Shipped vanilla files.** `BohemiaInteractive/DayZ-Central-Economy@master`.
Authoritative for defaults.

```sh
gh api "repos/BohemiaInteractive/DayZ-Central-Economy/contents/dayzOffline.<map>/<file>?ref=master" \
  --jq '.content' | base64 -d
```

Maps are `chernarusplus`, `enoch` (Livonia), `sakhal`.

**3. The Bohemia wiki.** Useful for semantics, unreliable for facts. **It has
been wrong or inverted in seven documented places across two files so far** —
wrong defaults, inverted descriptions, and key names that only exist on one
map. Where it disagrees with source or a shipped file, it loses, and the skill
says so explicitly.

The wiki is behind Cloudflare. `WebFetch` and curl get 403; use the
`claude-in-chrome` tools, and expect the first read to return the challenge
page — wait a few seconds and read again.

**Coverage is thinner than it looks.** `DayZ:Central_Economy_Configuration`
documents `globals.xml` and `cfgEconomyCore.xml` and stops — **there is no
wiki page for `types.xml` at all**, and `Central_Economy_Tweaking` /
`Central_Economy_Mission_Files` are both empty. Every per-element `types.xml`
reference online is community-written. Do not spend a session hunting for the
official one.

**3b. Community console resources.** `github.com/scalespeeder` — ~251 repos of
XML/JSON for DayZ servers, explicitly **PC and console**, so it respects the
no-mods constraint. Cited by the operator as a good resource. The
`extra_types.xml` files are the known-good list of valid classnames vanilla
omits. Below shipped files in authority but above the wiki for anything
console-specific.

**4. The operator.** The only source for intent, live behavior, and anything
Nitrado-specific. Ask rather than infer.

**Item classnames have no authority below the operator.** They live in the
game's `.cpp` configs, which are in neither GitHub repo. Engine source settles
CE *behavior*, not the catalogue of items. A classname is confirmed by a
published working list or an in-game test, and by nothing else — and a wrong
one fails exactly like a right one that is mis-tiered.

## How to build a skill

The process that produced the existing three. Follow it.

**1. Gather.** Read the live mission files, pull upstream vanilla for the
matching map, and diff per map. Note which deviations are shared across servers
and which are one project's.

**2. RED — baseline before writing anything.** Dispatch a subagent with no
tools and no skill, and ask it 6–8 routine questions about the file. Record
what it gets wrong **verbatim**. Every baseline so far produced confident
fabrication rather than admitted gaps: invented sections and key names, denied
that a real variable exists, defaults off by four orders of magnitude,
descriptions inverted. That failure mode is what `SKILL.md` must counter, and
it is why every skill opens with a "never answer from memory" rule rather than
a summary.

**3. Walk it through with the operator, one setting at a time.** State your
read, say plainly what you are unsure of, and ask. This is where the highest
value comes from — single-use keys via damage, login-only PRA triggers, the
`init.c` inversion, and the `TimeHopping` retention problem all came out of
this step and none were derivable from any document.

Do not batch settings unless they are genuinely one mechanism, and say so when
you do. When the operator corrects you, take it and move on — do not defend
the earlier reading.

**4. Write.** Mark every claim `[source]`, `[wiki]` or `[unverified]`. An
`[unverified]` gap is not an invitation to fill it in. Where you had a claim
wrong, the correction goes in as a named trap, because the wrong version is
what the next agent will also guess.

**5. Ship a validator.** Its distinctive job is the checks the game will not do
— cross-file consistency above all. `dayz-globals/scripts/validate.py` is the
reference: it checks four cross-file pairs and correctly stays silent on a
coherent config while flagging a broken one. Verify it against every live file,
the upstream vanilla files, and deliberately broken fixtures covering each
failure path.

**6. GREEN — re-run the baseline questions with the skill present.** Ask the
subagent for blunt feedback on gaps and ambiguity as well as answers. Act on
the feedback; it has caught real holes both times.

**7. Ship it through the workflow.** `main` is protected — keel blocks direct
commits and pushes. Use `keel:start-work` to cut a `feature/*` branch, add an
entry under `## [Unreleased]` in `CHANGELOG.md` (the gate checks the
*committed* state, not the working tree), then `keel:finish-work` to open the
PR, `keel:review`, and `keel:land`. Land with a **merge commit**, not a squash:
`.keel.json` is `trunk` topology, so `main` is the production branch and
keel blocks any other strategy (`[merge-strategy]`).

Write the commit message so it says what was **wrong** and why, not just what
changed — the existing history is the model. CI runs `scripts/ci_check.py`,
which will fail the PR if a skill's frontmatter `name` stops matching its
directory or a validator stops running.

## Skill conventions

- **Frontmatter `description` states only *when* to use the skill**, never what
  it does or how it works. A description that summarises the workflow gets
  followed instead of the skill body.
- **`SKILL.md` carries the traps, the routing table, and the house
  conventions.** Heavy per-key lookup goes in `references/`.
- **Every skill needs a "Things that are not what they look like" section.**
  This is where the value concentrates.
- **Cross-file rules deserve their own reference file** when there are more
  than two. See `dayz-globals/references/cross-file.md`.
- **Record operator intent, not just values.** "Clan Wars sets X" is weak;
  "Clan Wars sets X because raids are scheduled" survives contact with a change
  request.
- **Editing discipline, in every skill:** splice, never parse-and-reserialize.
  The live files have meaningful formatting and key order, and a round trip
  makes the diff unreviewable. Read the value back after editing — a key at the
  wrong nesting depth still parses.

## Known issues in the live servers

Recorded so they are not "fixed" by accident or repeated.

- **One Life `FlagRefreshMaxDuration: 604800`** — shortened from 40 days to 7
  to clean up abandoned bases, before the mechanic was understood. Base part
  lifetimes were left at vanilla 45 days, and the flag only postpones those, so
  it is close to inert. The fix is `db/types.xml` lifetimes. **Offer it; do not
  apply it unasked, and do not revert the setting to vanilla as though it were
  drift.** The operator intends to revisit.
- **`disableDistanceCheck: true` on all four servers** does nothing — dead
  config in Bohemia's source. Harmless; flagged by the validator.
- **Clan Wars has three orphaned files in `custom/`**
  (`admin-castle-explosives.json`, `admin-castle-flag-kit.json`,
  `flag-supplies.json`) that no array references, so they spawn nothing. May be
  staging; flagged by the validator.
- **`dayz-one-life/chernarus/CLAUDE.md:51`** says spawns use "vanilla gear plus
  `StartingEquipSetup` in `init.c`" — misleading, since `init.c` is inert. That
  repo has not been touched.
- **Three defects ship in Bohemia's own `types.xml`** and are therefore
  present on our servers too: `Crossbow_Black` has `quantmin 80`/`quantmax 0`
  (Livonia, Sakhal); `BatteryCharger` has `min 18` > `nominal 13` (Sakhal);
  `Firewood` has `crafted="1"` with a non-zero nominal, so it cannot spawn
  (Livonia, inherited by Clan Wars). `dayz-types/scripts/validate.py` knows
  these three by name and downgrades them to a tagged warning so an untouched
  mission still exits 0. **Do not treat them as local drift.**
- **Five `<proxy>` types ship unregistered in `mapgroupproto.xml`** —
  `Offroad_02_Door_{1_1,1_2,2_1,2_2}_BeigeRust` and
  `Offroad_02_Trunk_BeigeRust` are referenced by proto and absent from
  `types.xml` on **vanilla Chernarus and vanilla Livonia** (Sakhal is clean),
  so three of the four live configs inherit it. The CE logs each as an unknown
  type when the group builds. `dayz-mapgroups/scripts/validate.py` knows them
  by name and downgrades them to a tagged warning. **Not local drift.**
- **Sakhal's `mapgroupproto.xml` breaks Bohemia's own schema** — two
  containers carry a `<usage>` where it cannot apply (`Land_Factory_Small`,
  `Land_Geoplant_MaintenanceHall`) and `Land_Construction_Crane` has a
  `<category>` directly under `<group>`. Also shipped, also downgraded by the
  validator. Do not copy the shape.
- **Vanilla Livonia's `WinterMilitaryCoat_Greay` is a Bohemia typo.** All
  three maps' `cfgspawnabletypes.xml` say `Grey`, as do Chernarus and Sakhal
  `types.xml`. The coat has never spawned on vanilla Livonia. Clan Wars fixed
  it; One Life still carries the typo.
- **Clan Wars' `PartyTent*` ignore-list / `types.xml` overlap is intentional.**
  Party tents are a known source of server lag and are not allowed to exist.
  Flagged as a note by the validator; do not "resolve" it.
- **One Life's `types.xml` is deliberately frozen** at the vanilla reset while
  upstream `master` has moved on (mossy ghillies, `Tier4` on `PoliceVest`,
  `deloot` changes). **Flag the gap; never auto-apply it.**

## Status

**Done:** `dayz-cfggameplay`, `dayz-globals`, `dayz-types`, `dayz-mapgroups`.

**Next, in rough priority order:**

1. **ADM/RPT parsing** — the unattributed-death trap is already recorded in
   `dayz-cfggameplay`. Clan Wars' `packages/adm-parser` and
   `packages/domain/src/death-verdict.ts` are worked solutions worth
   generalising.
2. **Release and FTP deploy workflow** — `../../dayz-clan-wars/livonia/CLAUDE.md`
   has real scar tissue in it: publishing a Release is what deploys, a tag
   alone ships nothing, and an undeployed tag is invisible without an audit.
3. **`env/*_territories.xml`** — infected and animal zone tuning, the lever
   behind `ZombieMaxCount`.
4. **`cfgspawnabletypes.xml` and `cfgrandompresets.xml`** — attachment and
   cargo presets. Clan Wars adds 136 lines of weapon `<attachments>` presets
   that no existing skill covers, and `dayz-globals` already leans on the
   `<damage>` side of `cfgspawnabletypes.xml`.
5. **`db/events.xml` and `cfgeventspawns.xml`** — dynamic events, helicopter
   crashes, contaminated areas. `dayz-mapgroups` already depends on reading
   whether the contaminated-area events are live.
6. **Beyond the mission tree**, per the broadened scope: `areaflags.map` and
   DayZ Tools, Enforce script and modding for PC servers, and map editing.
   None of these are started.
