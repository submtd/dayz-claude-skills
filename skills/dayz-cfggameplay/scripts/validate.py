#!/usr/bin/env python3
"""Validate a DayZ cfggameplay.json before releasing it.

Catches the failures the game server will not report: JSON that does not parse,
keys the engine silently ignores, arrays of the wrong length, and referenced
JSON files that are missing from the mission tree.

    validate.py /path/to/mission/cfggameplay.json [--map chernarusplus|enoch|sakhal]

The map is inferred from the mission directory name when not given. It matters
because Bohemia ships a different cold-area key name on Sakhal.

Exit status: 0 clean (warnings allowed), 1 errors found, 2 could not run.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = 123

# Keys shared by every map, as nested paths. Verified against
# BohemiaInteractive/DayZ-Central-Economy@master.
KNOWN = {
    "version",
    "GeneralData.disableBaseDamage",
    "GeneralData.disableContainerDamage",
    "GeneralData.disableRespawnDialog",
    "GeneralData.disableRespawnInUnconsciousness",
    "PlayerData.spawnGearPresetFiles",
    "PlayerData.disablePersonalLight",
    "PlayerData.StaminaData.sprintStaminaModifierErc",
    "PlayerData.StaminaData.sprintStaminaModifierCro",
    "PlayerData.StaminaData.staminaWeightLimitThreshold",
    "PlayerData.StaminaData.staminaMax",
    "PlayerData.StaminaData.staminaKgToStaminaPercentPenalty",
    "PlayerData.StaminaData.staminaMinCap",
    "PlayerData.StaminaData.sprintSwimmingStaminaModifier",
    "PlayerData.StaminaData.sprintLadderStaminaModifier",
    "PlayerData.StaminaData.meleeStaminaModifier",
    "PlayerData.StaminaData.obstacleTraversalStaminaModifier",
    "PlayerData.StaminaData.holdBreathStaminaModifier",
    "PlayerData.ShockHandlingData.shockRefillSpeedConscious",
    "PlayerData.ShockHandlingData.shockRefillSpeedUnconscious",
    "PlayerData.ShockHandlingData.allowRefillSpeedModifier",
    "PlayerData.MovementData.timeToStrafeJog",
    "PlayerData.MovementData.rotationSpeedJog",
    "PlayerData.MovementData.timeToSprint",
    "PlayerData.MovementData.timeToStrafeSprint",
    "PlayerData.MovementData.rotationSpeedSprint",
    "PlayerData.MovementData.allowStaminaAffectInertia",
    "PlayerData.DrowningData.staminaDepletionSpeed",
    "PlayerData.DrowningData.healthDepletionSpeed",
    "PlayerData.DrowningData.shockDepletionSpeed",
    "PlayerData.WeaponObstructionData.staticMode",
    "PlayerData.WeaponObstructionData.dynamicMode",
    "WorldsData.lightingConfig",
    "WorldsData.objectSpawnersArr",
    "WorldsData.environmentMinTemps",
    "WorldsData.environmentMaxTemps",
    "WorldsData.wetnessWeightModifiers",
    "WorldsData.playerRestrictedAreaFiles",
    "BaseBuildingData.HologramData.disableIsCollidingBBoxCheck",
    "BaseBuildingData.HologramData.disableIsCollidingPlayerCheck",
    "BaseBuildingData.HologramData.disableIsClippingRoofCheck",
    "BaseBuildingData.HologramData.disableIsBaseViableCheck",
    "BaseBuildingData.HologramData.disableIsCollidingGPlotCheck",
    "BaseBuildingData.HologramData.disableIsCollidingAngleCheck",
    "BaseBuildingData.HologramData.disableIsPlacementPermittedCheck",
    "BaseBuildingData.HologramData.disableHeightPlacementCheck",
    "BaseBuildingData.HologramData.disableIsUnderwaterCheck",
    "BaseBuildingData.HologramData.disableIsInTerrainCheck",
    "BaseBuildingData.HologramData.disallowedTypesInUnderground",
    "BaseBuildingData.ConstructionData.disablePerformRoofCheck",
    "BaseBuildingData.ConstructionData.disableIsCollidingCheck",
    "BaseBuildingData.ConstructionData.disableDistanceCheck",
    "UIData.use3DMap",
    "UIData.HitIndicationData.hitDirectionOverrideEnabled",
    "UIData.HitIndicationData.hitDirectionBehaviour",
    "UIData.HitIndicationData.hitDirectionStyle",
    "UIData.HitIndicationData.hitDirectionIndicatorColorStr",
    "UIData.HitIndicationData.hitDirectionMaxDuration",
    "UIData.HitIndicationData.hitDirectionBreakPointRelative",
    "UIData.HitIndicationData.hitDirectionScatter",
    "UIData.HitIndicationData.hitIndicationPostProcessEnabled",
    "MapData.ignoreMapOwnership",
    "MapData.ignoreNavItemsOwnership",
    "MapData.displayPlayerPosition",
    "MapData.displayNavInfo",
    "VehicleData.boatDecayMultiplier",
}

COLD_KEY = "BaseBuildingData.HologramData.disableColdArea{}Check"
# Bohemia's own shipped files disagree on this key's name.
COLD_BY_MAP = {"chernarusplus": "Building", "enoch": "Building", "sakhal": "Placement"}

# Arrays the engine reads positionally; a wrong length is a silent misread.
FIXED_LENGTH = {
    "WorldsData.environmentMinTemps": 12,
    "WorldsData.environmentMaxTemps": 12,
    "WorldsData.wetnessWeightModifiers": 5,
}

# Arrays whose entries are paths into the mission tree.
PATH_ARRAYS = (
    "PlayerData.spawnGearPresetFiles",
    "WorldsData.objectSpawnersArr",
    "WorldsData.playerRestrictedAreaFiles",
)

ENUMS = {
    "UIData.HitIndicationData.hitDirectionBehaviour": {0, 1, 2},
    "UIData.HitIndicationData.hitDirectionStyle": {0, 1, 2},
    "PlayerData.WeaponObstructionData.staticMode": {0, 1, 2},
    "PlayerData.WeaponObstructionData.dynamicMode": {0, 1, 2},
    "WorldsData.lightingConfig": {0, 1, 2},
}

# Values Bohemia documents as producing unexpected results.
NONZERO = (
    "PlayerData.StaminaData.staminaMax",
    "PlayerData.StaminaData.staminaMinCap",
)

ARGB_RE = re.compile(r"^0x[0-9a-fA-F]{8}$")


def flatten(node, prefix=""):
    """Yield (dotted path, value) for every leaf. Arrays are leaves."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from flatten(value, f"{prefix}.{key}" if prefix else key)
    else:
        yield prefix, node


def infer_map(path):
    """Guess the map from the mission directory name, or None."""
    for part in reversed(path.resolve().parts):
        lowered = part.lower()
        for name in ("chernarusplus", "enoch", "sakhal"):
            if name in lowered:
                return name
        if "chernarus" in lowered:
            return "chernarusplus"
        if "livonia" in lowered:
            return "enoch"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="path to cfggameplay.json")
    parser.add_argument("--map", choices=sorted(COLD_BY_MAP), help="mission map")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"error: {args.file}: no such file", file=sys.stderr)
        return 2

    raw = args.file.read_text(encoding="utf-8-sig")
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR  does not parse: {exc}")
        print("       The server would silently fall back to vanilla defaults.")
        return 1

    mission = args.file.parent
    mapname = args.map or infer_map(args.file)
    errors, warnings, notes = [], [], []

    if mapname:
        known = KNOWN | {COLD_KEY.format(COLD_BY_MAP[mapname])}
        wrong = COLD_KEY.format(
            "Placement" if COLD_BY_MAP[mapname] == "Building" else "Building"
        )
    else:
        # Map unknown: accept either spelling, but say so.
        known = KNOWN | {COLD_KEY.format("Building"), COLD_KEY.format("Placement")}
        wrong = None
        notes.append(
            "map not given and not inferable from the path; "
            "cold-area key spelling not checked (pass --map)"
        )

    flat = dict(flatten(doc))

    if "version" not in flat:
        errors.append('"version" is missing')
    elif flat["version"] != SCHEMA_VERSION:
        warnings.append(
            f'"version" is {flat["version"]}, this reference documents {SCHEMA_VERSION} '
            "— confirm against upstream for your build"
        )

    for path, value in flat.items():
        if path not in known:
            if wrong and path == wrong:
                errors.append(
                    f"{path}: wrong spelling for {mapname} — the engine ignores it. "
                    f"Use {COLD_KEY.format(COLD_BY_MAP[mapname])}"
                )
            else:
                errors.append(f"{path}: unknown key — the engine ignores it silently")
            continue

        want = FIXED_LENGTH.get(path)
        if want is not None:
            if not isinstance(value, list):
                errors.append(f"{path}: expected an array of {want} values")
            elif len(value) != want:
                errors.append(f"{path}: has {len(value)} values, needs exactly {want}")

        if path in ENUMS and value not in ENUMS[path]:
            warnings.append(
                f"{path}: {value} is outside the documented set "
                f"{sorted(ENUMS[path])}"
            )

        if path in NONZERO and value == 0:
            warnings.append(
                f"{path}: 0 is documented as producing unexpected results; use 100.0"
            )

        if path == "UIData.HitIndicationData.hitDirectionIndicatorColorStr":
            if not (isinstance(value, str) and ARGB_RE.match(value)):
                errors.append(f'{path}: expected an ARGB string like "0xffbb0a1e"')

    referenced = set()
    for path in PATH_ARRAYS:
        entries = flat.get(path)
        if entries is None:
            continue
        if not isinstance(entries, list):
            errors.append(f"{path}: expected an array of paths")
            continue
        for entry in entries:
            if not isinstance(entry, str):
                errors.append(f"{path}: {entry!r} is not a path string")
                continue
            target = (mission / entry.lstrip("./")).resolve()
            referenced.add(target)
            if not target.is_file():
                errors.append(
                    f"{path}: {entry} does not exist — the server fails at boot"
                )
            else:
                try:
                    json.loads(target.read_text(encoding="utf-8-sig"))
                except json.JSONDecodeError as exc:
                    errors.append(f"{entry}: does not parse: {exc}")

    # A file sitting in custom/ that nothing references spawns nothing. Common
    # enough to be worth saying out loud.
    custom = mission / "custom"
    if custom.is_dir():
        orphans = sorted(
            p.name
            for p in custom.glob("*.json")
            if p.resolve() not in referenced
        )
        if orphans:
            notes.append(
                "custom/ files referenced by nothing (they do nothing): "
                + ", ".join(orphans)
            )

    if flat.get("BaseBuildingData.HologramData.disableIsPlacementPermittedCheck"):
        notes.append(
            "disableIsPlacementPermittedCheck is true — territory permission "
            "enforcement is off, anyone can build in anyone's territory"
        )

    label = f"{args.file}" + (f" (map: {mapname})" if mapname else "")
    print(label)
    for message in errors:
        print(f"  ERROR    {message}")
    for message in warnings:
        print(f"  WARNING  {message}")
    for message in notes:
        print(f"  NOTE     {message}")
    if not (errors or warnings or notes):
        print("  OK       no problems found")

    print(
        "\nReminder: none of this is read unless server.cfg has "
        "enableCfgGameplayFile = 1;"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
