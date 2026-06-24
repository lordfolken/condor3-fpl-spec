# GitHub issue draft — XCSoar/XCSoar

**Title:** Feature request: per-turnpoint altitude limits (Condor / CoTaCo import gap)

**Labels (suggested):** enhancement, task

---

## Summary

XCSoar task altitude rules are limited to **start max height** and **finish min height** at task level. **Observation zones are 2D only** (no min/max altitude per turnpoint).

This is a practical gap when flying Condor 3 tasks converted with [CoTaCo](https://condorutill.fr/CoTaCo.html): Condor Classic sectors store an **MSL floor and ceiling on every turnpoint** (`TPWidth` / `TPHeight`), but those limits cannot be represented faithfully in `.tsk`.

## Condor semantics (source of the gap)

On Condor **Classic** sectors (`TPSectorType=0`):

| Field | Meaning |
|-------|---------|
| `TPWidth` | Min altitude MSL (floor) |
| `TPHeight` | Max altitude MSL (ceiling) |

Every turnpoint can have its own band. Start/finish also have FPLCheck aliases (`StartMinAlt` → `TPWidth1`, `StartMaxAlt` → `TPHeight1`, etc.).

Example (condor.club task #UFYBEC, airstart at Turtmann):

```
TPWidth1=0
TPHeight1=1829    # start ceiling 1829 m MSL
```

Intermediate turnpoints may carry non-default bands; finish may specify min arrival / max arrival separately.

## Current XCSoar behaviour

### Task-level only

`StartConstraints` exposes **max height only** (no min):

```cpp
// src/Engine/Task/Ordered/StartConstraints.hpp
unsigned max_height;
AltitudeReference max_height_ref;
```

`FinishConstraints` exposes **min height only** (no max):

```cpp
// src/Engine/Task/Ordered/FinishConstraints.hpp
unsigned min_height;
AltitudeReference min_height_ref;
```

Enforcement matches that asymmetry — `CheckHeight` on start checks `altitude <= max_height`; on finish checks `altitude >= min_height` (`StartConstraints.cpp`, `FinishConstraints.cpp`).

`.tsk` deserialisation reads only those four attributes (`Deserialiser.cpp`: `start_max_height`, `start_max_height_ref`, `finish_min_height`, `finish_min_height_ref`).

### Observation zones are 2D

`ObservationZone` defines horizontal geometry only (cylinder, sector, line, keyhole, …). There is no min/max altitude on OZ types.

## CoTaCo workaround (fragile, not enforced)

CoTaCo maps Condor → `.tsk` as follows:

| Condor | CoTaCo → XCSoar |
|--------|-----------------|
| Intermediate `TPWidth` / `TPHeight` | Appended to **waypoint name**, e.g. `Megeve[1500-4000]` — **display only** |
| Start max (`TPHeight1`, etc.) | `start_max_height` in task header — **enforced** |
| Finish min (`TPWidth` on finish) | `finish_min_height` in task header — **enforced** |
| Start min, finish max | **No native `.tsk` fields** — dropped or name suffix only |

Known fragility (CoTaCo manual / xcsoar-user list):

- If the waypoint already exists in `.cup` / `.xcm`, the **database name wins** and the `[min-max]` suffix is lost.
- Default 5-character map labels truncate the suffix unless full-name label format is enabled.

## What is lost in practice

1. **Intermediate altitude bands** — not enforceable; at best a label hack.
2. **Start floor** — Condor `TPWidth1` has no XCSoar equivalent.
3. **Finish ceiling** — Condor `TPHeight` on finish has no XCSoar equivalent.
4. **Sector-volume semantics** — Condor limits apply inside the cylinder volume; XCSoar start/finish checks apply at the start/finish event, not as a per-OZ altitude shell.

Pilots using XCSoar + CoTaCo for Condor online tasks should treat altitude limits as **briefing / Condor scoring**, not as fully modelled task rules in XCSoar.

## Possible directions (for discussion)

Not prescribing a design — options maintainers might consider:

1. **Per-OZ min/max altitude** on turnpoint observation zones (MSL/AGL ref), checked when the turnpoint is scored.
2. **Task-level extensions:** `start_min_height`, `finish_max_height` (mirroring Condor start/finish bands).
3. **Import path:** document the limitation in SeeYou/CUP/Condor import docs; or preserve limits in waypoint `comment` when name suffix would be overwritten.

## References

- CoTaCo manual: https://condorutill.fr/CoTaCo/CoTaCo_Manual_EN.pdf
- Condor `.fpl` Classic sector fields: `TPWidth` (floor MSL), `TPHeight` (ceiling MSL)
- Related: CUP `MaxAlt=` is start-only on import (`TaskFileSeeYou.cpp`); SeeYou task options `NearAlt` noted missing in #2031

## Environment

- XCSoar: current `master` (verified against source tree, 2025-06)
- Workflow: Condor 3 `.fpl` → CoTaCo → `.tsk` + `.prf` (not a native `.fpl` loader in XCSoar)
