#!/usr/bin/env python3
"""Validate Condor .fpl files against FPL-format-spec.md.

Checks: C3 key inventory, indexed-key completeness, numeric types, and
AATTime/DesignatedTime pairing. Condor 1 keys are accepted only on non-C3 files.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Known keys from FPL-format-spec.md (normalized base names without numeric suffixes)
SPEC_SECTIONS = {
    "Version",
    "Task",
    "Weather",
    "Plane",
    "GameOptions",
    "Description",
}

SPEC_KEYS: dict[str, set[str]] = {
    "Version": {"Condor version"},
    "Task": {
        "Landscape",
        "Count",
        "PZCount",
        "DisabledAirspaces",
        "TaskVersion",
        "TaskID",
        "TaskName",
        "DesignatedTime",
    },
    "Weather": {"WZCount", "RandomizeWeatherOnEachFlight"},
    "Plane": {
        "Class",
        "Name",
        "Skin",
        "Water",
        "FixedMass",
        "CGBias",
        "Seat",
        "Bugwipers",
    },
    "GameOptions": {
        "TaskDate",
        "StartTime",
        "StartTimeWindow",
        "RaceStartDelay",
        "AATTime",
        "IconsVisibleRange",
        "ThermalHelpersRange",
        "TurnpointHelpersRange",
        "AAT",
        "AllowBugwipers",
        "AllowPDA",
        "AllowRealtimeScoring",
        "AllowExternalView",
        "AllowPadlockView",
        "AllowSmoke",
        "AllowPlaneRecovery",
        "AllowHeightRecovery",
        "AllowMidairCollisionRecovery",
        "AllowInstructorActions",
        "PenaltyCloudFlying",
        "PenaltyPlaneRecovery",
        "PenaltyHeightRecovery",
        "PenaltyWrongWindowEnterance",
        "PenaltyWindowCollision",
        "PenaltyAirspaceEnterance",
        "PenaltyPenaltyZoneEnterance",
        "PenaltyThermalHelpers",
        "MaxStartGroundSpeed",
        "PenaltyStartSpeed",
        "PenaltyHighStart",
        "PenaltyLowFinish",
        "RandSeed",
        "StartType",
        "StartHeight",
        "BreakProb",
        "RopeLength",
        "MaxWingLoading",
        "MaxTeams",
        "AcroFlight",
    },
    "Description": {"Text"},
}

# C1/C2 GameOptions — not part of the C3 spec (Appendix C)
LEGACY_GAMEOPTIONS_KEYS = {
    "PenaltyLostKnuckle",
    "MaxTowplanes",
    "TailHunting",
    "TailKnucklesNum",
    "TailKnucklesSize",
    "TailKnucklesDensity",
}

# Indexed / patterned keys (base regex -> section)
INDEXED_KEY_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("TPName", re.compile(r"^TPName(\d+)$"), "Task"),
    ("TPPosX", re.compile(r"^TPPosX(\d+)$"), "Task"),
    ("TPPosY", re.compile(r"^TPPosY(\d+)$"), "Task"),
    ("TPPosZ", re.compile(r"^TPPosZ(\d+)$"), "Task"),
    ("TPAirport", re.compile(r"^TPAirport(\d+)$"), "Task"),
    ("TPSectorType", re.compile(r"^TPSectorType(\d+)$"), "Task"),
    ("TPSectorDirection", re.compile(r"^TPSectorDirection(\d+)$"), "Task"),
    ("TPRadius", re.compile(r"^TPRadius(\d+)$"), "Task"),
    ("TPAngle", re.compile(r"^TPAngle(\d+)$"), "Task"),
    ("TPAltitude", re.compile(r"^TPAltitude(\d+)$"), "Task"),
    ("TPWidth", re.compile(r"^TPWidth(\d+)$"), "Task"),
    ("TPHeight", re.compile(r"^TPHeight(\d+)$"), "Task"),
    ("TPAzimuth", re.compile(r"^TPAzimuth(\d+)$"), "Task"),
    ("PZPos0X", re.compile(r"^PZPos0X(\d+)$"), "Task"),
    ("PZPos0Y", re.compile(r"^PZPos0Y(\d+)$"), "Task"),
    ("PZPos1X", re.compile(r"^PZPos1X(\d+)$"), "Task"),
    ("PZPos1Y", re.compile(r"^PZPos1Y(\d+)$"), "Task"),
    ("PZPos2X", re.compile(r"^PZPos2X(\d+)$"), "Task"),
    ("PZPos2Y", re.compile(r"^PZPos2Y(\d+)$"), "Task"),
    ("PZPos3X", re.compile(r"^PZPos3X(\d+)$"), "Task"),
    ("PZPos3Y", re.compile(r"^PZPos3Y(\d+)$"), "Task"),
    ("PZBase", re.compile(r"^PZBase(\d+)$"), "Task"),
    ("PZTop", re.compile(r"^PZTop(\d+)$"), "Task"),
    ("PZPenaltyTimeFactor", re.compile(r"^PZPenaltyTimeFactor(\d+)$"), "Task"),
    ("PolygonX", re.compile(r"^Polygon(\d+)X$"), "WeatherZone"),
    ("PolygonY", re.compile(r"^Polygon(\d+)Y$"), "WeatherZone"),
]

C3_TP_KEYS = (
    "TPName",
    "TPPosX",
    "TPPosY",
    "TPPosZ",
    "TPAirport",
    "TPSectorType",
    "TPSectorDirection",
    "TPRadius",
    "TPAngle",
    "TPAltitude",
    "TPWidth",
    "TPHeight",
    "TPAzimuth",
)

PZ_KEYS = (
    "PZPos0X",
    "PZPos0Y",
    "PZPos1X",
    "PZPos1Y",
    "PZPos2X",
    "PZPos2Y",
    "PZPos3X",
    "PZPos3Y",
    "PZBase",
    "PZTop",
    "PZPenaltyTimeFactor",
)

WEATHER_ZONE_KEYS = {
    "Name",
    "PointCount",
    "MoveDir",
    "MoveSpeed",
    "BorderWidth",
    "WindDir",
    "WindSpeed",
    "WindUpperSpeed",
    "WindDirVariation",
    "WindSpeedVariation",
    "WindTurbulence",
    "ThermalsTemp",
    "ThermalsTempVariation",
    "ThermalsDew",
    "ThermalsStrength",
    "ThermalsStrengthVariation",
    "ThermalsInversionheight",
    "ThermalsOverdevelopment",
    "ThermalsWidth",
    "ThermalsWidthVariation",
    "ThermalsActivity",
    "ThermalsActivityVariation",
    "ThermalsTurbulence",
    "ThermalsFlatsActivity",
    "ThermalsStreeting",
    "ThermalsBugs",
    "WavesStability",
    "WavesMoisture",
    "HighCloudsCoverage",
}

# Legacy flat weather keys (C1/C2)
LEGACY_WEATHER_KEYS = {
    "WindDir",
    "WindSpeed",
    "WindDirVariation",
    "WindSpeedVariation",
    "WindTurbulence",
    "ThermalsTemp",
    "ThermalsTempVariation",
    "ThermalsDew",
    "ThermalsStrength",
    "ThermalsStrengthVariation",
    "ThermalsInversionheight",
    "ThermalsWidth",
    "ThermalsWidthVariation",
    "ThermalsActivity",
    "ThermalsTurbulence",
    "Pressure",
    "WeatherPreset",
}

# Classified (section, base-name) pairs that are not numeric
STRING_CLASSIFICATIONS = {
    ("Task", "Landscape"),
    ("Task", "TaskName"),
    ("Task", "DisabledAirspaces"),
    ("Task", "TPName"),
    ("Plane", "Class"),
    ("Plane", "Name"),
    ("Plane", "Skin"),
    ("WeatherZone", "Name"),
    ("Description", "Text"),
}

C3_VERSIONS = frozenset({"3000", "3050", "3100"})
TWO_PI = 2.0 * math.pi
AAT_TIME_TOLERANCE_MIN = 0.05
# Window azimuth: radians in [0, 2π], or UI compass in 45° steps (club files mix both).
COMPASS_DEGREE_STEPS = {0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 360.0}


@dataclass
class FileReport:
    path: str
    sections: list[str] = field(default_factory=list)
    version: str | None = None
    landscape: str | None = None
    count: int | None = None
    pz_count: int | None = None
    wz_count: int | None = None
    aat: str | None = None
    start_type: str | None = None
    unknown_keys: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def is_c3_version(version: str | None) -> bool:
    """C3 build codes 3000–3999 (3.0.0=3000, 3.0.5=3050, 3.1.0=3100)."""
    if not version or not version.isdigit():
        return False
    return 3000 <= int(version) < 4000


def normalize_section(name: str) -> str:
    if re.fullmatch(r"WeatherZone\d+", name):
        return "WeatherZone"
    return name


def classify_key(section: str, key: str, *, version: str | None = None) -> str | None:
    """Return the spec base name for a key, or None if unknown for this version."""
    norm = normalize_section(section)
    c3 = is_c3_version(version)
    if norm in SPEC_KEYS and key in SPEC_KEYS[norm]:
        return key
    if norm == "WeatherZone" and key in WEATHER_ZONE_KEYS:
        return key
    if not c3:
        if norm == "Weather" and key in LEGACY_WEATHER_KEYS:
            return key
        if norm == "GameOptions" and key in LEGACY_GAMEOPTIONS_KEYS:
            return key
    for base, pattern, expected in INDEXED_KEY_PATTERNS:
        if pattern.match(key):
            if expected == "WeatherZone" and norm == "WeatherZone":
                return base
            if expected == "Task" and norm == "Task":
                return base
    return None


def _parse_number(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _is_int_csv(value: str) -> bool:
    if value == "":
        return True
    parts = value.split(",")
    return all(part.strip().lstrip("-").isdigit() and part.strip() != "" for part in parts)


def _indexed_match(key: str) -> tuple[str, int] | None:
    for base, pattern, _expected in INDEXED_KEY_PATTERNS:
        matched = pattern.match(key)
        if matched:
            return base, int(matched.group(1))
    return None


def _check_value_type(section: str, key: str, value: str, classified: str) -> str | None:
    norm = normalize_section(section)
    if (norm, classified) == ("Task", "DisabledAirspaces"):
        if not _is_int_csv(value):
            return f"Non-integer CSV [{section}] {key}={value!r}"
        return None
    if (norm, classified) in STRING_CLASSIFICATIONS:
        return None
    if _parse_number(value) is None:
        return f"Non-numeric [{section}] {key}={value!r}"
    return None


def _check_completeness(sections: dict[str, dict[str, str]], report: FileReport) -> None:
    task = sections.get("Task", {})
    if report.count is not None:
        for i in range(report.count):
            for base in C3_TP_KEYS:
                if f"{base}{i}" not in task:
                    report.warnings.append(f"Missing {base}{i} for Count={report.count}")
        for key in task:
            matched = _indexed_match(key)
            if matched is None:
                continue
            base, idx = matched
            if base.startswith("TP") and idx >= report.count:
                report.warnings.append(f"Extra {key} beyond Count={report.count}")

    if report.pz_count is not None:
        for z in range(report.pz_count):
            for base in PZ_KEYS:
                if f"{base}{z}" not in task:
                    report.warnings.append(f"Missing {base}{z} for PZCount={report.pz_count}")
        for key in task:
            matched = _indexed_match(key)
            if matched is None:
                continue
            base, idx = matched
            if base.startswith("PZ") and idx >= report.pz_count:
                report.warnings.append(f"Extra {key} beyond PZCount={report.pz_count}")

    for section, kv in sections.items():
        if not re.fullmatch(r"WeatherZone\d+", section):
            continue
        raw_count = kv.get("PointCount")
        if raw_count is None:
            report.warnings.append(f"Missing PointCount in [{section}]")
            continue
        point_count = int(raw_count) if raw_count.isdigit() else None
        if point_count is None:
            continue
        for j in range(point_count):
            if f"Polygon{j}X" not in kv:
                report.warnings.append(f"Missing Polygon{j}X in [{section}] for PointCount={point_count}")
            if f"Polygon{j}Y" not in kv:
                report.warnings.append(f"Missing Polygon{j}Y in [{section}] for PointCount={point_count}")
        for key in kv:
            matched = _indexed_match(key)
            if matched is None:
                continue
            base, idx = matched
            if base in {"PolygonX", "PolygonY"} and idx >= point_count:
                report.warnings.append(f"Extra {key} in [{section}] beyond PointCount={point_count}")


def _check_semantic(sections: dict[str, dict[str, str]], report: FileReport) -> None:
    task = sections.get("Task", {})
    game = sections.get("GameOptions", {})
    designated = task.get("DesignatedTime")
    aat_time = game.get("AATTime")
    if designated is not None and aat_time is not None:
        minutes = _parse_number(designated)
        hours = _parse_number(aat_time)
        if minutes is not None and hours is not None:
            if abs(minutes - hours * 60.0) > AAT_TIME_TOLERANCE_MIN:
                report.warnings.append(
                    f"DesignatedTime={designated} min is not AATTime={aat_time} h "
                    f"(expected {hours * 60.0:g} min)"
                )

    if report.count is None:
        return
    for i in range(report.count):
        raw_az = task.get(f"TPAzimuth{i}")
        if raw_az is None:
            continue
        azimuth = _parse_number(raw_az)
        if azimuth is not None:
            as_degrees = abs(azimuth - round(azimuth)) < 1e-6 and float(round(azimuth)) in COMPASS_DEGREE_STEPS
            as_radians = abs(azimuth) <= TWO_PI + 1e-6
            if not (as_degrees or as_radians):
                report.warnings.append(
                    f"TPAzimuth{i}={raw_az} is neither radians (0–2π) nor a 45° compass step"
                )


def parse_fpl(path: Path) -> tuple[dict[str, dict[str, str]], FileReport]:
    report = FileReport(path=str(path))
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None

    text = path.read_text(encoding="utf-8", errors="replace")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, {})
            report.sections.append(current)
            continue
        if current is None or "=" not in line:
            report.warnings.append(f"Unparsed line outside section: {raw_line!r}")
            continue
        key, value = line.split("=", 1)
        sections[current][key] = value

    task = sections.get("Task", {})
    weather = sections.get("Weather", {})
    game = sections.get("GameOptions", {})
    version = sections.get("Version", {})

    report.version = version.get("Condor version")
    report.landscape = task.get("Landscape")
    report.count = int(task["Count"]) if task.get("Count", "").isdigit() else None
    report.pz_count = int(task["PZCount"]) if task.get("PZCount", "").isdigit() else None
    report.wz_count = int(weather["WZCount"]) if weather.get("WZCount", "").isdigit() else None
    report.aat = game.get("AAT")
    report.start_type = game.get("StartType")

    weather_zones = [s for s in sections if re.fullmatch(r"WeatherZone\d+", s)]
    if report.wz_count is not None and len(weather_zones) != report.wz_count:
        report.warnings.append(
            f"WZCount={report.wz_count} but found {len(weather_zones)} WeatherZone sections"
        )

    for section, keys in sections.items():
        for key, value in keys.items():
            classified = classify_key(section, key, version=report.version)
            if classified is None:
                report.unknown_keys.setdefault(section, []).append(key)
                continue
            type_error = _check_value_type(section, key, value, classified)
            if type_error:
                report.warnings.append(type_error)

    if is_c3_version(report.version):
        _check_completeness(sections, report)
        _check_semantic(sections, report)

    return sections, report


def aggregate_reports(reports: list[FileReport]) -> dict:
    all_sections: set[str] = set()
    all_keys_by_section: dict[str, set[str]] = defaultdict(set)
    all_unknown: dict[str, set[str]] = defaultdict(set)
    versions: set[str] = set()
    landscapes: set[str] = set()
    tp_counts: set[int] = set()
    airport_angles: list[float] = []
    tp_radii: list[float] = []
    tp_angles: list[float] = []
    sector_types: set[str] = set()

    for rep in reports:
        all_sections.update(rep.sections)
        if rep.version:
            versions.add(rep.version)
        if rep.landscape:
            landscapes.add(rep.landscape)
        if rep.count is not None:
            tp_counts.add(rep.count)
        for section, keys in rep.unknown_keys.items():
            for key in keys:
                all_unknown[section].add(key)
        sections_data, _ = parse_fpl(Path(rep.path))
        task = sections_data.get("Task", {})
        count = rep.count or 0
        for i in range(count):
            st = task.get(f"TPSectorType{i}")
            if st is not None:
                sector_types.add(st)
            r = task.get(f"TPRadius{i}")
            if r:
                try:
                    tp_radii.append(float(r))
                except ValueError:
                    pass
            a = task.get(f"TPAngle{i}")
            if a:
                try:
                    val = float(a)
                    tp_angles.append(val)
                    if task.get(f"TPAirport{i}") == "1":
                        airport_angles.append(val)
                except ValueError:
                    pass
        for section, kv in sections_data.items():
            for key in kv:
                all_keys_by_section[normalize_section(section)].add(key)

    return {
        "file_count": len(reports),
        "sections": sorted(all_sections),
        "normalized_sections": sorted({normalize_section(s) for s in all_sections}),
        "versions": sorted(versions),
        "landscapes": sorted(landscapes),
        "tp_counts": sorted(tp_counts),
        "sector_types": sorted(sector_types),
        "tp_radius_min": min(tp_radii) if tp_radii else None,
        "tp_radius_max": max(tp_radii) if tp_radii else None,
        "tp_angle_values": sorted(set(tp_angles)),
        "airport_tp_angles": sorted(set(airport_angles)),
        "unknown_keys": {k: sorted(v) for k, v in sorted(all_unknown.items())},
        "keys_by_section": {k: sorted(v) for k, v in sorted(all_keys_by_section.items())},
        "warnings": [w for rep in reports for w in rep.warnings],
        "files": [
            {
                "path": Path(rep.path).name,
                "version": rep.version,
                "landscape": rep.landscape,
                "count": rep.count,
                "pz_count": rep.pz_count,
                "wz_count": rep.wz_count,
                "aat": rep.aat,
                "start_type": rep.start_type,
                "unknown_key_count": sum(len(v) for v in rep.unknown_keys.values()),
                "warnings": rep.warnings,
            }
            for rep in reports
        ],
    }


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent
    sample_dir = root / "samples"
    c3_only = "--c3-only" in argv
    paths = sorted(sample_dir.rglob("*.fpl"))
    if not paths:
        print(f"No .fpl files in {sample_dir}", file=sys.stderr)
        return 1

    reports: list[FileReport] = []
    for path in paths:
        _, report = parse_fpl(path)
        if c3_only and not is_c3_version(report.version):
            continue
        reports.append(report)

    if not reports:
        print("No samples matched filter.", file=sys.stderr)
        return 1

    summary = aggregate_reports(reports)
    summary["c3_only"] = c3_only
    out_json = root / "validation_report.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    label = "C3 " if c3_only else ""
    print(f"Validated {summary['file_count']} {label}samples in {sample_dir}")
    print(f"Condor versions: {', '.join(summary['versions'])}")
    print(f"Landscapes: {', '.join(summary['landscapes'])}")
    print(f"TP counts: {summary['tp_counts']}")
    print(f"Sections seen: {', '.join(summary['normalized_sections'])}")
    unknown_count = sum(len(v) for v in summary["unknown_keys"].values())
    if summary["unknown_keys"]:
        print("Unknown keys (not in spec inventory):")
        for section, keys in summary["unknown_keys"].items():
            print(f"  [{section}] {', '.join(keys)}")
    else:
        print("No unknown keys vs spec inventory.")
    if summary["warnings"]:
        print(f"Warnings ({len(summary['warnings'])}):")
        for w in summary["warnings"][:20]:
            print(f"  - {w}")
        if len(summary["warnings"]) > 20:
            print(f"  … {len(summary['warnings']) - 20} more")
    else:
        print("No structure/type warnings.")
    print(f"Full report: {out_json}")

    if c3_only and (unknown_count or summary["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
