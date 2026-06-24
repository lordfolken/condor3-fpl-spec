#!/usr/bin/env python3
"""Validate Condor .fpl flight plan files against FPL-format-spec.md key inventory."""

from __future__ import annotations

import json
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
        "PenaltyLostKnuckle",
        "MaxTowplanes",
        "TailHunting",
        "TailKnucklesNum",
        "TailKnucklesSize",
        "TailKnucklesDensity",
    },
    "Description": {"Text"},
}

# Indexed / patterned keys (base regex -> section)
INDEXED_KEY_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("TPName", re.compile(r"^TPName\d+$"), "Task"),
    ("TPPosX", re.compile(r"^TPPosX\d+$"), "Task"),
    ("TPPosY", re.compile(r"^TPPosY\d+$"), "Task"),
    ("TPPosZ", re.compile(r"^TPPosZ\d+$"), "Task"),
    ("TPAirport", re.compile(r"^TPAirport\d+$"), "Task"),
    ("TPSectorType", re.compile(r"^TPSectorType\d+$"), "Task"),
    ("TPSectorDirection", re.compile(r"^TPSectorDirection\d+$"), "Task"),
    ("TPRadius", re.compile(r"^TPRadius\d+$"), "Task"),
    ("TPAngle", re.compile(r"^TPAngle\d+$"), "Task"),
    ("TPAltitude", re.compile(r"^TPAltitude\d+$"), "Task"),
    ("TPWidth", re.compile(r"^TPWidth\d+$"), "Task"),
    ("TPHeight", re.compile(r"^TPHeight\d+$"), "Task"),
    ("TPAzimuth", re.compile(r"^TPAzimuth\d+$"), "Task"),
    ("PZPos0X", re.compile(r"^PZPos0X\d+$"), "Task"),
    ("PZPos0Y", re.compile(r"^PZPos0Y\d+$"), "Task"),
    ("PZPos1X", re.compile(r"^PZPos1X\d+$"), "Task"),
    ("PZPos1Y", re.compile(r"^PZPos1Y\d+$"), "Task"),
    ("PZPos2X", re.compile(r"^PZPos2X\d+$"), "Task"),
    ("PZPos2Y", re.compile(r"^PZPos2Y\d+$"), "Task"),
    ("PZPos3X", re.compile(r"^PZPos3X\d+$"), "Task"),
    ("PZPos3Y", re.compile(r"^PZPos3Y\d+$"), "Task"),
    ("PZBase", re.compile(r"^PZBase\d+$"), "Task"),
    ("PZTop", re.compile(r"^PZTop\d+$"), "Task"),
    ("PZPenaltyTimeFactor", re.compile(r"^PZPenaltyTimeFactor\d+$"), "Task"),
    ("PolygonX", re.compile(r"^Polygon\d+X$"), "WeatherZone"),
    ("PolygonY", re.compile(r"^Polygon\d+Y$"), "WeatherZone"),
]

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


def normalize_section(name: str) -> str:
    if re.fullmatch(r"WeatherZone\d+", name):
        return "WeatherZone"
    return name


def classify_key(section: str, key: str) -> str | None:
    norm = normalize_section(section)
    if norm in SPEC_KEYS and key in SPEC_KEYS[norm]:
        return key
    if norm == "WeatherZone" and key in WEATHER_ZONE_KEYS:
        return key
    if norm == "Weather" and key in LEGACY_WEATHER_KEYS:
        return key
    for base, pattern, expected in INDEXED_KEY_PATTERNS:
        if pattern.match(key):
            if expected == "WeatherZone" and norm == "WeatherZone":
                return base
            if expected == "Task" and norm == "Task":
                return base
    return None


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

    if report.count is not None:
        for i in range(report.count):
            if f"TPName{i}" not in task:
                report.warnings.append(f"Missing TPName{i} for Count={report.count}")

    for section, keys in sections.items():
        for key in keys:
            if classify_key(section, key) is None:
                report.unknown_keys.setdefault(section, []).append(key)

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


C3_VERSIONS = frozenset({"3000", "3100"})


def is_c3_version(version: str | None) -> bool:
    return version in C3_VERSIONS if version else False


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
    print(f"Full report: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
