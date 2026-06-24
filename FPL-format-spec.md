# Condor Soaring Simulator — `.fpl` Flight Plan Format

**Status:** Unofficial, reverse-engineered community specification  
**Scope:** **Condor 3 only** (version codes `3000`, `3100`) — Condor 1/2 are out of scope (see Appendix C)  
**Last updated:** 2026-06-24 (32 C3 samples validated; unit encoding cross-checked via `winch.fpl` UI export)  
**Authors:** Synthesized from Condor 3 samples, the C3 user guide, CondorUTill tools, and forum reports

---

## 1. Disclaimer

This document is **not** published or endorsed by Condor Soaring Ltd. The `.fpl` format is an internal configuration format read and written by the Condor Flight Planner. Field semantics were inferred from:

- Local `.fpl` samples (Condor 3 installs and user flight plans)
- [Condor 3 User Guide](https://downloads3.condorsoaring.com/manuals/Condor%203%20manual_en.pdf) (UI semantics)
- [Condor Orientation](https://www.cumulus-soaring.com/condor2/Condor_Orientation.pdf) (sector types, penalties)
- [FPLCheck README](http://condorutill.fr/FPLCheck/FPLCheck_README.txt) (validation aliases)
- [CoTaCo manual](https://condorutill.fr/CoTaCo/CoTaCo_Manual_EN.pdf) (AAT, penalty zones, CUP import)
- [pycondor](https://github.com/s-celles/pycondor) (ConfigParser parsing, turnpoint field list)
- [Condor Landscape Guide](https://www.condorsoaring.com/wp-content/downloads/clt/Condor%20Landscape%20Guide%20ENGLISH%20rev2.pdf) (UTM/WGS 84 projection, scenery tile grid)
- Condor forums (penalty zone fields, coordinate origin, UI round-trip quirks)
- [condor.club](https://www.condor.club) (task distribution; **not** a format spec)

Fields marked **confirmed (UI docs)** come from official or community UI documentation. Fields marked **observed** were seen in files but lack official documentation. Fields marked **inferred** are reasonable guesses.

Hand-editing `[Task]` geometry is discouraged by FPL2V3 maintainers and may produce unpredictable behaviour in-game.

---

## 2. File format basics

| Property | Value |
|----------|-------|
| Extension | `.fpl` |
| Structure | INI-style: `[Section]` headers, `Key=Value` lines |
| Line endings | CRLF typical on Windows; LF may work |
| Encoding | **Observed:** Windows-1252 (`cp1252`) for non-ASCII names; pycondor supports `--fixencoding --encoding_in cp1252`. UTF-8 not guaranteed. |
| Comments | **Not observed** in saved files; do not assume `#` or `;` comments are preserved |
| Boolean values | `0` = false/off, `1` = true/on |
| Numeric values | Integer or floating-point decimal; no units suffix in file |
| Key case | Case-sensitive as written below |
| Parser | Standard INI parsers work (Python `configparser`, etc.) if they tolerate duplicate section names — **Condor uses unique section names** |

### Typical file locations

| Path | Purpose |
|------|---------|
| `Documents\Condor3\FlightPlans\` | User-saved flight plans |
| `Documents\Condor3\Pilots\<PilotName>\Flightplan.fpl` | Auto-saved last flight plan per pilot |
| `Documents\Condor3\RaceResults\` | Race replay copies |
| `<CondorInstall>\FlightPlans\Default\` | Shipped defaults |

Related formats: `.sfl` (flight plan **list** — stores references to `.fpl` files only), `.ftr` (flight track, embeds a copy of the flight plan).

---

## 3. Condor 3 version codes

`[Version]` → `Condor version=<code>`

| Code | Release | Notes |
|------|---------|-------|
| `3000` | 3.0.0 | Observed on early C3 install defaults (Slovenia3) |
| `3100` | 3.1.0 | Most C3 samples (local saves, race replays, condor.club exports) |

Encoding: **inferred** — `major * 1000 + minor * 100 + patch * 10` (e.g. 3.1.0 → 3100).

### Condor 3 section layout

| Section | Purpose |
|---------|---------|
| `[Version]` | Simulator build code |
| `[Task]` | Landscape, turnpoints, penalty zones, disabled airspaces |
| `[Weather]` | Zone count header only (`WZCount`, `RandomizeWeatherOnEachFlight`) |
| `[WeatherZoneN]` | Per-zone weather (0 = base; 1–7 = optional moving polygons, up to 8 **confirmed UI**) |
| `[Plane]` | Glider class, type, ballast, seat, bug wipers |
| `[GameOptions]` | Timing, AAT, penalties, helpers, recoveries, start type |
| `[Description]` | Free-text task notes (often condor.club task ID) |

There is **no separate `[NOTAM]` section** in any Condor 3 sample examined. Ghost/helper/penalty settings that lived on the C1/C2 NOTAM tab appear under `[GameOptions]` in C3.

### C3-specific notes

| Topic | Condor 3 behaviour |
|-------|-------------------|
| `ThermalsInversionheight` | AMSL in weather zones **confirmed (FPL2V3 vs C2)** |
| Weather model | Base zone + up to 7 overlay zones with moving polygons |
| Airspace | `DisabledAirspaces` CSV exported with task (CoTaCo can emit OpenAir) |
| Task metadata | `TaskVersion`, `TaskID`, `TaskName` optional — common in condor.club exports, rare in local saves |

---

## 4. Document structure (Condor 3)

A complete Condor 3 flight plan typically contains, in order:

```
[Version]
[Task]
[Weather]
[WeatherZone0]
[WeatherZone1]
...
[WeatherZone(WZCount-1)]
[Plane]
[GameOptions]
[Description]
```

`WZCount` in `[Weather]` must equal the number of `[WeatherZoneN]` sections (including zone 0 = base).

---

## 5. Section reference

### 5.1 `[Version]`

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `Condor version` | integer | Simulator build code (see §3) | observed |

---

### 5.2 `[Task]`

Defines landscape, turnpoints, penalty zones, and disabled airspace regions.

#### 5.2.1 Task-level keys

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `Landscape` | string | Landscape folder / `.trn` basename (e.g. `AA3`, `CW-Swiss`, `Slovenia3`) | confirmed |
| `Count` | integer | Number of turnpoints (indices `0` … `Count-1`) | confirmed |
| `PZCount` | integer | Number of penalty zones (indices `0` … `PZCount-1`) | confirmed |
| `DisabledAirspaces` | CSV integers | IDs of airspace volumes disabled for this task | observed |
| `TaskVersion` | integer | Task schema version | observed (condor.club exports) |
| `TaskID` | integer | Online task ID (condor.club network ID) | observed (condor.club exports) |
| `TaskName` | string | Human-readable task name | observed (condor.club exports) |
| `DesignatedTime` | float | AAT designated task time in minutes | observed (Sierradlv AAT) |

**DisabledAirspaces:** Comma-separated list with no spaces in samples. Empty list = all airspaces active. A long list of all IDs (0…1317) = all airspaces disabled (common for online/club tasks). **Validated:** partial lists also occur — e.g. `1082,1194,1208,1209,1235,1310,1311,1337,1338` in a condor.club race replay with one penalty zone, disabling only selected volumes rather than all airspaces.

#### 5.2.2 Turnpoint keys (indexed)

For each index `i` where `0 ≤ i < Count`, the following keys exist:

| Key | Type | Units | Description | Source |
|-----|------|-------|-------------|--------|
| `TPName{i}` | string | — | Display name (may differ from landscape `.cup` DB name) | confirmed |
| `TPPosX{i}` | float | m | Landscape X (Condor grid metres; see §8) | confirmed |
| `TPPosY{i}` | float | m | Landscape Y (Condor grid metres; see §8) | confirmed |
| `TPPosZ{i}` | float | m | Ground elevation MSL at point | observed |
| `TPAirport{i}` | 0\|1 | — | `1` = co-located with airport (takeoff/finish airfield) | confirmed |
| `TPSectorType{i}` | integer | — | Sector geometry type (see §6) | confirmed |
| `TPSectorDirection{i}` | integer | — | Always `0` in all C3 samples examined | observed |
| `TPRadius{i}` | float | m | Classic sector: cylinder radius (0–5000) | confirmed |
| `TPAngle{i}` | float | deg | Classic sector: arc angle (90, 180, 270, 360) | confirmed |
| `TPAltitude{i}` | float | m MSL | Window sector: vertical centre; also stored for Classic | confirmed |
| `TPWidth{i}` | float | m | Classic: min altitude MSL **or** Window: horizontal width | confirmed |
| `TPHeight{i}` | float | m | Classic: max altitude MSL **or** Window: vertical height | confirmed |
| `TPAzimuth{i}` | float/enum | deg | Window sector: entry direction (N=0, NE, E, …) | confirmed |

**FPLCheck altitude aliases** (Classic sectors only):

| Alias | Maps to | Role |
|-------|---------|------|
| `StartMinAlt` | `TPWidth1` | Start gate floor MSL |
| `StartMaxAlt` | `TPHeight1` | Start gate ceiling MSL |
| `FinishMinAlt` | `TPWidth{Count-1}` | Finish floor MSL |
| `FinishMaxAlt` | `TPHeight{Count-1}` | Finish ceiling MSL |

#### 5.2.3 Penalty zone keys (indexed)

When `PZCount > 0`, for each zone index `z`:

| Key | Type | Units | Description | Source |
|-----|------|-------|-------------|--------|
| `PZPos0X{z}` | float | m | Corner 0 X | forum |
| `PZPos0Y{z}` | float | m | Corner 0 Y | forum |
| `PZPos1X{z}` | float | m | Corner 1 X | forum |
| `PZPos1Y{z}` | float | m | Corner 1 Y | forum |
| `PZPos2X{z}` | float | m | Corner 2 X | forum |
| `PZPos2Y{z}` | float | m | Corner 2 Y | forum |
| `PZPos3X{z}` | float | m | Corner 3 X | forum |
| `PZPos3Y{z}` | float | m | Corner 3 Y | forum |
| `PZBase{z}` | float | m MSL | Floor altitude (0–10000) | forum |
| `PZTop{z}` | float | m MSL | Ceiling altitude | forum |
| `PZPenaltyTimeFactor{z}` | integer | pts/min | Extra scoring penalty per minute inside zone | forum |

Quadrilateral corners define horizontal extent. UI default vertical span: ground to 5000 m MSL **confirmed (Orientation)**. UI allows 2–1000 pts/min for this factor.

**Limitation (forum):** Flight Planner UI may only honour ~8 penalty zones; higher `PZCount` values in hand-edited files may not work in sim.

---

### 5.3 `[Weather]` (Condor 3)

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `WZCount` | integer | Number of `[WeatherZoneN]` sections (1–8 **confirmed UI**) | confirmed |
| `RandomizeWeatherOnEachFlight` | 0\|1 | Re-roll thermals/wind each flight using `RandSeed` | observed |

Condor 3 moves all atmospheric parameters into `[WeatherZoneN]`. The `[Weather]` section is only a zone count header.

---

### 5.4 `[WeatherZoneN]` (Condor 3)

`N` ranges from `0` to `WZCount - 1`. Zone 0 is typically the **base** weather covering the whole landscape. Higher-index zones override base weather inside their polygon. Overlapping zones: **lower index wins** **confirmed (C3 manual)**.

#### Zone geometry

| Key | Type | Units | Description | Source |
|-----|------|-------|-------------|--------|
| `Name` | string | — | Display name (`Base`, `Weather zone 1`, …) | observed |
| `PointCount` | integer | — | `0` = entire landscape; `>0` = polygon vertex count | confirmed |
| `Polygon{j}X` | float | m | Vertex j X (landscape coords), `j = 0 … PointCount-1` | observed |
| `Polygon{j}Y` | float | m | Vertex j Y | observed |
| `MoveDir` | float | deg | Direction zone drifts (0=N, 90=E, …) | confirmed |
| `MoveSpeed` | float | m/s | Zone translation speed (`2.222…` ≈ 8 km/h observed) | confirmed |
| `BorderWidth` | float | m | Transition blend width at zone boundary | confirmed |

Zones begin moving when the server/flight starts **confirmed (forum)**.

#### Zone atmosphere (same keys in every zone)

| Key | Type | Units | Description | Source |
|-----|------|-------|-------------|--------|
| `WindDir` | float | deg | Surface wind **from** direction | confirmed |
| `WindSpeed` | float | m/s | Surface wind speed | confirmed |
| `WindUpperSpeed` | float | m/s | Wind at altitude (`13.889…` ≈ 50 km/h observed) | observed |
| `WindDirVariation` | integer | — | UI slider level (1–3 typical) | observed |
| `WindSpeedVariation` | integer | — | UI slider level | observed |
| `WindTurbulence` | integer | — | UI slider level | observed |
| `ThermalsTemp` | float | °C | Target surface / thermal top temperature | confirmed |
| `ThermalsTempVariation` | integer | — | Randomness slider | observed |
| `ThermalsDew` | float | °C | Dew point | confirmed |
| `ThermalsStrength` | integer | — | Thermal strength slider (1–5) | confirmed |
| `ThermalsStrengthVariation` | integer | — | Randomness slider | observed |
| `ThermalsInversionheight` | float | m AMSL (C3) | Inversion / cloud base reference height | confirmed (FPL2V3) |
| `ThermalsOverdevelopment` | 0\|1+ | — | `0` = none; `1`+ enables CB development **confirmed (C3 manual)** | confirmed |
| `ThermalsWidth` | integer | — | Thermal diameter slider | observed |
| `ThermalsWidthVariation` | integer | — | Randomness slider | observed |
| `ThermalsActivity` | integer | — | Thermal density slider | observed |
| `ThermalsActivityVariation` | integer | — | Randomness slider | observed |
| `ThermalsTurbulence` | integer | — | In-thermal turbulence slider | observed |
| `ThermalsFlatsActivity` | integer | — | Flatland thermal activity | observed |
| `ThermalsStreeting` | integer | — | Cloud/thermal streeting | observed |
| `ThermalsBugs` | integer | — | Bug accumulation rate (XC option) | observed |
| `WavesStability` | integer | — | Mountain wave stability | observed |
| `WavesMoisture` | integer | 0–10 | Wave moisture slider; UI displays as **percent** (`8` → 80%) | observed |
| `HighCloudsCoverage` | integer | 0–8 | High cloud slider; UI displays as **octas** (`2` → 2/8) | observed |

FPLCheck can compute cloud base from `[WeatherZone0]` thermal data and departure airfield elevation for validation rules.

---

### 5.5 `[Plane]`

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `Class` | string | Competition class (`Standard`, `18-meter`, `Club`, `All`, …) | confirmed |
| `Name` | string | Glider type ID (e.g. `Antares18S`, `LS8neo`) | confirmed |
| `Skin` | string | Livery name (`Default`, …) | confirmed |
| `Water` | float/int | Water ballast amount | confirmed |
| `FixedMass` | float/int | Fixed ballast | confirmed |
| `CGBias` | float | CG trim bias | confirmed |
| `Seat` | integer | `1` = front, `2` = rear (two-seaters) | observed |
| `Bugwipers` | 0\|1 | Bug wiper option enabled | observed (C3 XC) |

**Round-trip quirk (forum):** `Water`, `FixedMass`, `CGBias`, and `Seat` are saved in `.fpl` but may be **reset to hangar defaults** when loading via Free Flight UI. `Class`, `Name`, and `Skin` load correctly. Refly/restart may preserve values.

---

### 5.6 `[GameOptions]`

Race timing, realism, penalties, and feature toggles.

#### Date and time

| Key | Type | Units | Description | Source |
|-----|------|-------|-------------|--------|
| `TaskDate` | integer | — | Days since **1899-12-30** (Delphi/Excel-style serial; `46194` = 2026-06-21 **validated**) | observed |
| `StartTime` | float | hours | Local task start time (e.g. `13`, `12.5` = 12:30) **validated:** `12.5` in condor.club race replay | confirmed |
| `StartTimeWindow` | float | hours | Start gate open duration (`0` = instant close **observed**) | confirmed |
| `RaceStartDelay` | float | hours | Delay before race timing starts; stored as **decimal hours** (`0.01666…` ≈ 1 min; `0.16666…` ≈ 10 min **validated**) | observed |

#### Task type

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `AAT` | 0\|1 | `1` = Assigned Area Task | confirmed |
| `AATTime` | float | hours | AAT minimum time (e.g. `1.25` = 1 h 15 min) | confirmed |

When `AAT=1`, intermediate turnpoints typically use large `TPRadius` (e.g. 15000 m) **validated** in `Lesce AAT task.fpl` (zones 2–3 at 15000 m, finish at 1000 m). `PenaltyLowFinish=0` also observed in that AAT sample.

#### Launch / start

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `StartType` | integer | Launch/start mode (see §7) | observed |
| `StartHeight` | float | m | Start gate reference height (AGL **inferred**) | confirmed |
| `MaxStartGroundSpeed` | float | km/h | Maximum ground speed crossing start | observed |
| `RopeLength` | float | m | Aero-tow rope length | observed |
| `BreakProb` | float | % | Winch cable break probability; stored as **whole-number percent** (`44` = 44%; not `0.44`) | observed |

#### Helpers and visibility

| Key | Type | Units | Description | Source |
|-----|------|-------|-------------|--------|
| `IconsVisibleRange` | float | nm | Other glider icon visibility | confirmed |
| `ThermalHelpersRange` | float | nm | Thermal helper visibility (`0` = off) | confirmed |
| `TurnpointHelpersRange` | float | nm | Turnpoint helper visibility | confirmed |

#### Feature allows (competition host locks)

| Key | Type | Description |
|-----|------|-------------|
| `AllowBugwipers` | 0\|1 | Bug wipers permitted |
| `AllowPDA` | 0\|1 | PDA / flight computer |
| `AllowRealtimeScoring` | 0\|1 | Live scoring |
| `AllowExternalView` | 0\|1 | External camera |
| `AllowPadlockView` | 0\|1 | Padlock chase cam |
| `AllowSmoke` | 0\|1 | Smoke trail |
| `AllowPlaneRecovery` | 0\|1 | Mid-air reposition recovery |
| `AllowHeightRecovery` | 0\|1 | Altitude recovery |
| `AllowMidairCollisionRecovery` | 0\|1 | Collision recovery |
| `AllowInstructorActions` | 0\|1 | Instructor controls |

#### Penalties (seconds added to task time)

| Key | Type | Trigger |
|-----|------|---------|
| `PenaltyCloudFlying` | integer | Flying in clouds |
| `PenaltyPlaneRecovery` | integer | Using plane recovery |
| `PenaltyHeightRecovery` | integer | Using height recovery |
| `PenaltyWrongWindowEnterance` | integer | Window sector wrong direction |
| `PenaltyWindowCollision` | integer | Hitting window frame |
| `PenaltyAirspaceEnterance` | integer | Entering restricted airspace |
| `PenaltyPenaltyZoneEnterance` | integer | Entering penalty zone |
| `PenaltyThermalHelpers` | integer | Using thermal helper (H key) |
| `PenaltyStartSpeed` | integer | Exceeding max start ground speed |
| `PenaltyHighStart` | integer | Starting above max altitude |
| `PenaltyLowFinish` | integer | Finishing below min altitude |

#### Other

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `RandSeed` | integer | Weather/thermal RNG seed | observed |
| `MaxWingLoading` | float | kg/m² limit (`0` = none) | observed |
| `MaxTeams` | integer | Multiplayer team limit | observed |
| `AcroFlight` | integer | Aerobatic mode (`0` = off) | observed |

---

### 5.7 `[Description]`

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `Text` | string | Freeform notes; condor.club tasks often embed `Task #XXXX found on www.condor.club` | observed |

May be empty: `Text=` with no value.

---

## 6. Turnpoint conventions and sector geometry

### 6.1 Typical index roles (racing task)

| Index | Role | Typical flags |
|-------|------|---------------|
| `0` | Takeoff / airfield | `TPAirport0=1`, special `TPAngle0` (see below) |
| `1` | Start gate | `TPAngle1=180` (line sector), `TPHeight1` = start max alt |
| `2 … Count-2` | Turnpoints | Various `TPAngle` (90° common) |
| `Count-1` | Finish | Small radius (500 m) or line (`TPAngle=180`, `TPWidth>0` for line finish **observed**) |

Tasks may omit separate takeoff if using non-airport starts **inferred**. AAT tasks may use fewer distinct points with large cylinders.

### 6.2 `TPSectorType` values

| File value | UI name | Geometry keys used |
|------------|---------|-------------------|
| `0` | Classic | `TPRadius`, `TPAngle`, `TPWidth` (min MSL), `TPHeight` (max MSL) |
| `1` | Window | `TPAltitude` (centre MSL), `TPWidth` (width m), `TPHeight` (height m), `TPAzimuth` |

UI documentation labels Classic=1, Window=2 (1-based); **file format is 0-based observed**.

### 6.3 Classic sector parameters (confirmed UI)

- **Radius:** 0–5000 m (default 3000)
- **Angle:** 90, 180, 270, or 360° (full cylinder)
- **Min altitude (`TPWidth`):** MSL metres; default 0 (ground)
- **Max altitude (`TPHeight`):** MSL metres; default 5000; min sector height 100 m

### 6.4 Window sector parameters (confirmed UI)

- **Altitude:** Vertical centre MSL (default 1500)
- **Width:** Horizontal width m (default 100)
- **Height:** Vertical extent m (default 100)
- **Azimuth:** Entry heading (N, NE, E, SE, S, SW, W, NW)

### 6.5 Airport `TPAngle` encoding (observed, not documented)

Takeoff points (`TPAirport=1`) often carry large `TPAngle` values unrelated to standard sector angles:

```
TPAngle0=29098   (UFYBEC / Turtmann, AA3)
TPAngle0=29080   (Samedan, AA3 race replay)
TPAngle0=29060   (Interlaken / ARUBEC, AA3)
TPAngle0=90      (some hand-built AA3 tasks — may differ from condor.club exports)
```

**Validated radius range across samples:** 500, 1000, 1500, 3000, 15000 m. **Validated TPAngle values (non-airport):** 90, 180, 360.

**Hypothesis (inferred):** Encodes runway heading or airport start cylinder orientation in an internal unit (possibly centidegrees or packed integer). Treat as opaque unless reverse-engineered via `NaviCon.dll`.

### 6.6 Line finish (observed)

```
TPRadius8=500
TPAngle8=180
TPWidth8=800      ← line length (m) inferred
TPHeight8=10000
```

CoTaCo converts Window sectors to XCSoar “line” types; 180° Classic sectors with `TPWidth>0` may represent line finishes.

---

## 7. Start and launch types

`StartType` in `[GameOptions]` selects the launch method **confirmed (C3 manual §4.5 NOTAM / Flight settings)**:

| Value | Meaning | Evidence |
|-------|---------|----------|
| `0` | **Aerotow** start | Most install defaults and condor.club tasks; uses `RopeLength` for tow-rope length |
| `1` | **Winch** start | `FlightPlans\winch.fpl` (user-named); `BreakProb` = rope-break probability on winch launch |
| `2` | **Airborne / airstart** | Tasks with in-air start gate (`StartHeight` 700–1500 m); no ground launch |

UI labels (Condor 3 manual): *“Choose from aerotow start, winch start or airborne start.”*

### Winch-specific keys

When `StartType=1`:

| Key | Role |
|-----|------|
| `BreakProb` | Winch cable break probability as **whole-number percent** (`44` = 44%; `0` = never, **confirmed UI**) |
| `RopeLength` | Still present in `winch.fpl` (`50` m) — may mirror aerotow rope UI field or be unused for winch |

### Example: winch launch (`winch.fpl`)

```
Landscape=Slovenia3
Count=8                   ← 8-TP task (triangle with return)
PZCount=3                 ← three penalty zones (indices 0–2)
WZCount=3                 ← base + two moving weather zones
StartType=1               ← winch
StartHeight=700
BreakProb=44
RopeLength=50
RandomizeWeatherOnEachFlight=1
RaceStartDelay=0.16666667163372   ← 10 min (hours)
```

Penalty zones use default vertical span `PZBase=0`, `PZTop=10000`, `PZPenaltyTimeFactor=5` per zone. Weather zone 2 has `ThermalsOverdevelopment=1`.

---

## 8. Coordinate systems

All horizontal positions in a `.fpl` file use **Condor landscape coordinates**: distances in **metres** on a flat, landscape-local grid. They are **not** WGS84 latitude/longitude and **not** raw UTM easting/northing values you can pass directly to a generic GIS library without landscape bounds.

The same grid is used everywhere geometry appears in the file: turnpoints, penalty-zone corners, and weather-zone polygon vertices.

### 8.1 Horizontal axes (`TPPosX`, `TPPosY`, …)

| Field pattern | Unit | Meaning |
|---------------|------|---------|
| `TPPosX{i}`, `TPPosY{i}` | m | Turnpoint centre (or sector anchor) |
| `PZPos{corner}X{z}`, `PZPos{corner}Y{z}` | m | Penalty-zone quadrilateral corners (`corner` 0–3) |
| `Polygon{j}X`, `Polygon{j}Y` | m | Weather-zone polygon vertices |

**Typical magnitudes:** Values are often in the **10⁴–10⁵ m** range (e.g. `TPPosX0=337211`, `TPPosY0=266724` on Slovenia3 in `winch.fpl`). Relative distances within one landscape are always meaningful; absolute numbers are only comparable across files that share the same `Landscape=` value.

### 8.2 Vertical axis (`TPPosZ`, `PZBase`, `PZTop`, …)

| Field | Unit | Meaning |
|-------|------|---------|
| `TPPosZ{i}` | m | **Terrain elevation MSL** at the turnpoint XY **observed** |
| `PZBase{z}`, `PZTop{z}` | m | Penalty-zone floor/ceiling altitude MSL |
| `TPAltitude{i}` | m | Window sector: vertical centre MSL; also stored on Classic sectors (default 1500) — **altitude band on Classic is `TPWidth`/`TPHeight`, not `TPAltitude`** |

`TPPosZ` is stored in the file and matches ground height at the XY location; it is not a pilot-selected value.

### 8.3 Underlying map projection

Condor landscapes are built on a **UTM projection with WGS 84 datum** **confirmed (Landscape Guide)**.

| Rule | Detail |
|------|--------|
| One zone per landscape | Each scenery uses a **single UTM zone**; Condor cannot mix zones in one landscape **confirmed (Landscape Guide)** |
| Large sceneries | Areas spanning zone boundaries should stay mostly inside the chosen zone; cross-zone edges accumulate projection error **confirmed (Landscape Guide)** |
| `.fpl` values vs UTM | Saved XY values are **Condor landscape metres** on an internal grid aligned with that projection — **not** zone easting/northing read from an online UTM converter **inferred (NaviCon required for lat/lon)** |

Scenery authors convert real-world lat/lon to UTM when building terrain; the Flight Planner then reads/writes the Condor grid. External tools must use landscape-aware conversion (below), not a bare lat/lon → UTM step.

### 8.4 Landscape grid layout

Condor uses a **fixed origin and extent per landscape** **confirmed (NaviCon.dll, forums)**:

```
(MaxX, MaxY)  ───────────  top-left corner of landscape
      │                           ▲ +Y
      │                           │
      │         task geometry     │
      │                           │
      └──────────────────────────► +X
(0, 0)  bottom-right corner of landscape
```

| Concept | Value |
|---------|-------|
| Origin | **`(0, 0)` = bottom-right corner** of the landscape |
| Opposite corner | **`(GetMaxX(), GetMaxY())` = top-left corner** |
| Valid range | `0 ≤ X ≤ MaxX`, `0 ≤ Y ≤ MaxY` (points outside may still appear in hand-edited files) |
| +X direction | From the **right edge toward the left edge** (horizontal toward top-left) |
| +Y direction | From the **bottom edge toward the top edge** (vertical toward top-left) |

Compass bearing of +X/+Y depends on how the real terrain sits in the UTM zone; the grid convention itself is landscape-relative, not “east/north UTM axes.”

**Terrain bitmap note (scenery authors):** Condor terrain tiles use a **90 m/pixel** raster in classic (V1) documentation **confirmed (Landscape Guide, forums)**. Bitmap pixel `(0, 0)` is the **top-left** of the tile, whereas Condor `(0, 0)` is the **bottom-right** of the full landscape — the two origins differ. For a bitmap `M × N` pixels:

```
PosX = (M - pixelX) × 90
PosY = (N - pixelY) × 90
```

**inferred (forum)** — use `NaviCon.dll` or current scenery tools rather than hand-applying this for Condor 3 landscapes (30 m terrain mesh in V2/C3 sceneries).

### 8.5 Converting between Condor XY and WGS84

**Authoritative path:** Condor installs **`NaviCon.dll`** (Condor 2 patch 9 onward) **confirmed (forums, pycondor)**. Initialise with the landscape `.trn` file, then convert:

| DLL export | Purpose |
|------------|---------|
| `NaviConInit(trnPath)` | Load landscape; returns success flag |
| `GetMaxX()`, `GetMaxY()` | Landscape extent (top-left corner coords) |
| `XYToLat(x, y)`, `XYToLon(x, y)` | Condor XY → WGS84 decimal degrees |
| Reverse functions | Lat/lon → XY exist in community wrappers **inferred (pycondor, CoCoCo)** |

Example using [pycondor](https://github.com/s-celles/pycondor):

```python
navicon_dll.init(landscape_name)  # loads <Landscape>.trn from Condor install
lat = navicon_dll.xy_to_lat(pos_x, pos_y)
lon = navicon_dll.xy_to_lon(pos_x, pos_y)
```

**Without `NaviCon.dll`:**

| Tool | Role |
|------|------|
| [CoCoCo](https://condorutill.fr/) (CondorUTill) | Lat/lon ↔ Condor XY for a named landscape |
| [CoTaCo](https://condorutill.fr/CoTaCo.html) | Builds `.fpl` from `.cup` waypoints + template; matches CUP names to landscape DB |
| Condor Flight Planner | GUI authoritative writer — drag/drop or import |
| [condor.club](https://www.condor.club) briefings | Publish **lat/lon only** (degrees/minutes); must be converted separately (see Appendix B) |

There is **no portable formula** in this spec to derive XY from lat/lon using only the landscape name; you need `NaviCon.dll`, CoCoCo, or the in-game planner.

### 8.6 Practical guidance

1. **Same landscape only** — Never copy `TPPosX/Y` from an AA3 task into a Slovenia3 file; coordinates are landscape-specific.
2. **Relative geometry is safe to analyse** — Leg distances, polygon areas, and TP ordering can be computed from XY alone within one file.
3. **Hand-editing XY is discouraged** — See §10; FPL2V3 and forum reports warn of unpredictable in-game behaviour without planner calibration.
4. **`TPPosZ` sanity check** — If Z disagrees sharply with known terrain, the XY pair is likely wrong or from another landscape.
5. **CUP vs FPL** — Landscape `.cup` files store waypoints as **lat/lon** (SeeYou format); only `.fpl` `[Task]` stores Condor XY.

---

## 9. FPLCheck validation conventions

FPLCheck rule files use the same INI structure with extended operators: `=`, `!=`, `<`, `<=`, `>`, `>=`, `[]` (string contains).

**Wildcards for turnpoint rules:**

| Pattern | Meaning |
|---------|---------|
| `TPRadius*` | All turnpoints |
| `TPAngle\|` | Finish turnpoint (`Count-1`) |
| `TPAngle$` | All except TP0, TP1, and finish |
| `TPAngle?` | All except TP0, TP1, penultimate, and finish |
| `TPAngle%` | Penultimate turnpoint (before finish) |

Section-qualified keys: `[Plane]Name=ASW19`

---

## 10. Known quirks and limitations

1. **No official schema** — new Condor versions may add keys without notice.
2. **UI vs file** — Some `[Plane]` ballast fields do not round-trip through Free Flight load.
3. **Hand-edit `[Task]`** — Coordinate changes require landscape calibration; FPL2V3 warns of unpredictable results.
4. **Penalty zones** — UI limit ~8 active zones; manual `PZCount` may not all work.
5. **Encoding** — Non-ASCII turnpoint names may need cp1252.
6. **Condor.club** — Distributes tasks and briefings (lat/lon text); does not document `.fpl` keys.
7. **Ghosts** — Ghost flight tracks (`.ftr`) are configured in the Flight Planner UI; no ghost keys appear in saved C3 `.fpl` files examined.

---

## 11. Minimal valid Condor 3 example

```ini
[Version]
Condor version=3100

[Task]
Landscape=AA3
Count=3
TPName0=NewTP
TPPosX0=671736.25
TPPosY0=468687
TPPosZ0=400
TPAirport0=1
TPSectorType0=0
TPSectorDirection0=0
TPRadius0=3000
TPAngle0=90
TPAltitude0=1500
TPWidth0=0
TPHeight0=10000
TPAzimuth0=0
TPName1=NewTP
TPPosX1=668469.125
TPPosY1=457633.25
TPPosZ1=908
TPAirport1=0
TPSectorType1=0
TPSectorDirection1=0
TPRadius1=3000
TPAngle1=180
TPAltitude1=1500
TPWidth1=0
TPHeight1=10000
TPAzimuth1=0
TPName2=Courtelary
TPPosX2=704488.625
TPPosY2=440753.03125
TPPosZ2=686
TPAirport2=0
TPSectorType2=0
TPSectorDirection2=0
TPRadius2=3000
TPAngle2=180
TPAltitude2=1500
TPWidth2=0
TPHeight2=10000
TPAzimuth2=0
PZCount=0
DisabledAirspaces=

[Weather]
RandomizeWeatherOnEachFlight=0
WZCount=1

[WeatherZone0]
Name=Base
PointCount=0
MoveDir=0
MoveSpeed=0
BorderWidth=0
WindDir=0
WindSpeed=0
WindUpperSpeed=0
WindDirVariation=1
WindSpeedVariation=1
WindTurbulence=1
ThermalsTemp=22
ThermalsTempVariation=1
ThermalsDew=10
ThermalsStrength=2
ThermalsStrengthVariation=1
ThermalsInversionheight=2500
ThermalsOverdevelopment=0
ThermalsWidth=2
ThermalsWidthVariation=1
ThermalsActivity=3
ThermalsActivityVariation=1
ThermalsTurbulence=1
ThermalsFlatsActivity=2
ThermalsStreeting=0
ThermalsBugs=0
WavesStability=5
WavesMoisture=8
HighCloudsCoverage=2

[Plane]
Class=All
Name=LS8neo
Skin=Default
Water=0
FixedMass=0
CGBias=0
Seat=1
Bugwipers=1

[GameOptions]
TaskDate=46194
StartTime=12
StartTimeWindow=0
RaceStartDelay=0.16666667163372
AATTime=3
IconsVisibleRange=20
ThermalHelpersRange=11
TurnpointHelpersRange=30
AAT=0
AllowBugwipers=1
AllowPDA=1
AllowRealtimeScoring=1
AllowExternalView=1
AllowPadlockView=1
AllowSmoke=1
AllowPlaneRecovery=1
AllowHeightRecovery=1
AllowMidairCollisionRecovery=1
AllowInstructorActions=0
PenaltyCloudFlying=100
PenaltyPlaneRecovery=100
PenaltyHeightRecovery=100
PenaltyWrongWindowEnterance=100
PenaltyWindowCollision=100
PenaltyAirspaceEnterance=100
PenaltyPenaltyZoneEnterance=100
PenaltyThermalHelpers=60
MaxStartGroundSpeed=150
PenaltyStartSpeed=1
PenaltyHighStart=1
PenaltyLowFinish=1
RandSeed=1991769747
StartType=2
StartHeight=1500
BreakProb=0
RopeLength=50
MaxWingLoading=0
MaxTeams=0
AcroFlight=0

[Description]
Text=
```

Derived from `Documents\Condor3\FlightPlans\c3sim.fpl`.

---

## 12. Tooling cross-reference

| Tool | Read FPL | Write FPL | Notes |
|------|----------|-----------|-------|
| Condor 3 Flight Planner | Yes | Yes | Authoritative writer |
| [CoTaCo](https://condorutill.fr/CoTaCo.html) | Yes | Yes (from `.cup` + Template.fpl) | C3; exports TSK/LKT/CUP/JSON |
| [FPLCheck](https://condorutill.fr/FPLCheck/FPLCheck_README.txt) | Validate | No | Rule files use FPL syntax |
| `validate_fpl.py` (this repo) | Validate | No | C3-focused key inventory check |

---

## 13. References

1. Condor 3 User Guide — https://downloads3.condorsoaring.com/manuals/Condor%203%20manual_en.pdf  
2. Condor Orientation (Roger Thoman) — https://www.cumulus-soaring.com/condor2/Condor_Orientation.pdf  
3. CondorUTill — https://condorutill.fr/  
4. FPLCheck README — http://condorutill.fr/FPLCheck/FPLCheck_README.txt  
5. CoTaCo Manual — https://condorutill.fr/CoTaCo/CoTaCo_Manual_EN.pdf  
6. pycondor — https://github.com/s-celles/pycondor  
7. Penalty zone FPL fields — https://www.condorsoaring.com/forums/viewtopic.php?t=18631  
8. Plane settings round-trip — https://www.condorsoaring.com/forums/viewtopic.php?f=32&p=194375  
9. FPL2V3 / C3 weather — https://www.condorsoaring.com/forums/viewtopic.php?t=22322  
10. condor.club — https://www.condor.club  
11. Condor Landscape Guide (UTM, scenery tiles) — https://www.condorsoaring.com/wp-content/downloads/clt/Condor%20Landscape%20Guide%20ENGLISH%20rev2.pdf  
12. NaviCon / bitmap ↔ Condor XY — https://www.condorsoaring.com/forums/viewtopic.php?t=17062  
13. Condor XY corner calibration (GIS) — https://gis.stackexchange.com/questions/143104/  

---

## Appendix A: Sample file index

### Validation corpus (`spec-validation\samples\`)

See §14 for the full 12-file inventory used in the 2026-06-24 validation pass (expanded from FlightPlans and Downloads).

### Additional local files (not copied to validation set)

| File | Notes |
|------|-------|
| `Pilots\Wollschlegel_Philipp\Flightplan.fpl` | Same as `condorclub_UFYBEC_AA3_race_5tp.fpl` |
| `FlightPlans\matterhorn.fpl` | Same as `local_AA3_race_3tp.fpl` |
| `FlightPlans\jura run.fpl` | Same as `local_AA3_race_5tp.fpl` |
| `FlightPlans\c3sim.fpl` | Same as `samples\local\local_AA3_c3sim_3tp.fpl` (helpers on, named finish TP) |
| `FlightPlans\Jungfrau.fpl` | Same as `samples\local\local_AA3_Jungfrau_3tp.fpl` (`StartHeight=700`, helpers off) |
| `FlightPlans\winch.fpl` | Same as `samples\local\local_Slovenia3_winch_8tp.fpl` (winch, 8 TP, PZ×3, WZ×3) |
| `FlightPlans\Lesce AAT task.fpl` | Same as `local_Slovenia3_AAT_6tp.fpl` |
| `RaceResults\Race 729773665 on 2026.06.10.fpl` | Same as `condorclub_race_AA3_9tp.fpl` |
| `RaceResults\Race 157438007 on 2026.06.10.fpl` | Same as `condorclub_race_AA3_pz1_6tp.fpl` |
| pycondor `samples/default.fpl` | Same as `reference_pycondor_C1_default.fpl` |

---

## Appendix B: Condor.club task briefing (related, not FPL)

Online task pages expose human-readable turnpoint blocks:

```
Start (2,434 ft)
Heading: 115° for 3.9 NM,
Coords: 46.31.377N / 6.42.372E
Classic turnpoint,
min. height: 0 ft, max.: 6,234 ft
angle: 180°, radius: 13,123 ft
```

These coordinates are WGS84 degrees/minutes; convert separately to `.fpl` landscape XY via Flight Planner, CoCoCo, or CoTaCo (see §8.5).

---

## 14. Validated against 32 Condor 3 samples

**Scope:** Condor 3 only (`3000`, `3100`). One Condor 1 reference file (`1150`) is kept in the corpus for regression but excluded from C3 statistics below.  
**Validation date:** 2026-06-24 (32 C3 samples after `winch.fpl`)  
**Sample directory:** `Documents\Condor3\spec-validation\samples\`  
**Validation script:** `python spec-validation\validate_fpl.py --c3-only`

### 14.1 Sample inventory

| File | Source | Version | Landscape | TPs | AAT | WZ | Notes |
|------|--------|---------|-----------|-----|-----|----|-------|
| `condorclub_UFYBEC_AA3_race_5tp.fpl` | condor.club task #UFYBEC (local pilot save) | 3100 | AA3 | 5 | 0 | 2 | Moving weather zone |
| `condorclub_race_AA3_9tp.fpl` | condor.club task #ARUBEC (race replay) | 3100 | AA3 | 9 | 0 | 1 | Line finish `TPWidth8=800` |
| `condorclub_race_AA3_pz1_6tp.fpl` | condor.club race replay | 3100 | AA3 | 6 | 0 | 1 | **PZCount=1** with all `PZ*` keys |
| `local_AA3_race_3tp.fpl` | Local FlightPlans (`matterhorn.fpl`) | 3100 | AA3 | 3 | 0 | 1 | Minimal triangle; helpers off |
| `local_AA3_race_5tp.fpl` | Local FlightPlans (`jura run.fpl`) | 3100 | AA3 | 5 | 0 | 1 | Non-zero wind; `StartHeight=700`; `AllowInstructorActions=1` |
| `local\local_AA3_c3sim_3tp.fpl` | Local FlightPlans (`c3sim.fpl`) | 3100 | AA3 | 3 | 0 | 1 | Named finish `Courtelary`; helpers on; `StartHeight=1500` |
| `local\local_AA3_Jungfrau_3tp.fpl` | Local FlightPlans (`Jungfrau.fpl`) | 3100 | AA3 | 3 | 0 | 1 | `StartHeight=700`; helpers/recovery off |
| `local\local_Slovenia3_winch_8tp.fpl` | Local FlightPlans (`winch.fpl`) | 3100 | Slovenia3 | 8 | 0 | **3** | **`StartType=1` winch**; **`PZCount=3`**; **`WZCount=3`**; moving zones; `ThermalsOverdevelopment=1` in zone 2 |
| `local_Slovenia3_AAT_6tp.fpl` | Condor install defaults (prior pass) | 3000 | Slovenia3 | 6 | **1** | 2 | 15000 m AAT cylinders |
| `local_Slovenia3_race_5tp.fpl` | Condor install defaults (prior pass) | 3100 | Slovenia3 | 5 | 0 | 1 | |
| `local_Slovenia3_triangle_5tp.fpl` | Condor install defaults (prior pass) | 3100 | Slovenia3 | 5 | 0 | 1 | |
| `downloads\downloads_CW-Swiss_Marcuss_8tp.fpl` | Downloads (`Swiss - Marcuss_CC.fpl`) | 3100 | **CW-Swiss** | 8 | 0 | 1 | condor.club #AQYBEC; **StartType=0** tow |
| `condor3_install\install_Slovenia3_Ajdovscina_ridge_6tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 6 | 0 | 1 | Ridge task; `StartType=0` |
| `condor3_install\install_Slovenia3_Austrian300_triangle_5tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 5 | 0 | 1 | |
| `condor3_install\install_Slovenia3_Bovec_free_6tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 6 | 0 | 1 | `StartType=2` on install default |
| `condor3_install\install_Slovenia3_Celje250_triangle_5tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 5 | 0 | 1 | |
| `condor3_install\install_Slovenia3_Lesce100_triangle_5tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 5 | 0 | 1 | |
| `condor3_install\install_Slovenia3_MurskaSobota_open_6tp.fpl` | `C:\Condor3\FlightPlans\` | **3100** | Slovenia3 | 6 | 0 | 1 | v3.1.0 install default; `StartType=2` |
| `condor3_install\install_Slovenia3_NovoMesto_triangle_5tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 5 | 0 | 1 | |
| `condor3_install\install_Slovenia3_Postonja_free_6tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 6 | 0 | 1 | **TPSectorType4=1** Window sector (`TPWidth4=100`, `TPHeight4=100`, `TPAzimuth4≈π/4`) |
| `condor3_install\install_Slovenia3_Ptuj_free_6tp.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 6 | 0 | 1 | |
| `condor3_install\install_Slovenia3_Slo300_triangle_6tp_wz2.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 6 | 0 | 2 | Moving weather zone |
| `condor3_install\install_Slovenia3_Slo400_triangle_5tp_wz2.fpl` | `C:\Condor3\FlightPlans\` | 3000 | Slovenia3 | 5 | 0 | 2 | Moving weather zone |
| `pilots\pilots_Slovenia3_PilotNew_2tp.fpl` | `C:\Condor3\Pilots\Pilot_New\` | 3000 | Slovenia3 | 2 | 0 | 1 | Minimal auto-save (2 TPs) |
| `race\race_AA3_9tp_starttype0.fpl` | RaceResults replay | 3100 | AA3 | 9 | 0 | 1 | Distinct 9-TP race; `StartType=0` |
| `race\race_AA3_5tp_starttype1.fpl` | RaceResults replay | 3100 | AA3 | 5 | 0 | 1 | **`StartType=1`** (winch — same value as `winch.fpl`) |
| `race\race_AA3_8tp.fpl` | RaceResults replay | 3100 | AA3 | 8 | 0 | 1 | |
| `race\race_Slovenia3_6tp.fpl` | RaceResults replay | 3100 | Slovenia3 | 6 | 0 | 1 | |
| `downloads\downloads_LakeKeepitC3_213km_6tp.fpl` | Downloads (condor.club #28125) | 3100 | **LakeKeepitC3** | 6 | 0 | **3** | `TaskVersion`/`TaskID`/`TaskName` in C3; `TPRadius` 1000 m |
| `downloads\downloads_Japan-Shikoku3_18m_6tp.fpl` | Downloads (condor.club #28126) | 3100 | **Japan-Shikoku3** | 6 | 0 | 2 | Small cylinders (`TPRadius=500` m) |
| `downloads\downloads_Sierradlv_AAT_6tp.fpl` | Downloads (CIAC day #6) | 3100 | **Sierradlv** | 6 | **1** | 1 | **`DesignatedTime=90`**; `AATTime=1.5` |
| `downloads\downloads_AA3_MontBlanc_7tp.fpl` | Downloads (condor.club) | 3100 | AA3 | 7 | 0 | 1 | Tour du Mont Blanc; `StartType=0` |

**Disk scan (2026-06-24):** Searched `Documents\Condor3\`, `C:\Condor3\`, `Downloads\`, and `Documents\Condor\` (C2 — not present). Found 46 non-corpus `.fpl` files; **12 byte-identical** to existing samples (skipped); **2 empty** condor.club stubs in `Downloads\` (0 bytes — skipped); **20 new unique** copied.

**Duplicates skipped:** `FlightPlans\` matterhorn/jura/c3sim/Jungfrau; `Pilots\Wollschlegel_Philipp\Flightplan.fpl`; 3 of 7 `RaceResults\` replays; 3 of 15 `C:\Condor3\FlightPlans\` (Lesce AAT, Austrian 200 km, Slovenj Gradec); `Swiss - Marcuss_CC.fpl`.

**Empty downloads skipped:** `Flying Gliders Virtual Championship-Competition day #10-_CC.fpl`, `VG3021_Pumalin Park_200km_20m_CC.fpl` (login required or failed download).

### 14.2 Sections observed (C3)

Across all 31 Condor 3 samples:

`[Version]`, `[Task]`, `[Weather]`, `[WeatherZone0]` … `[WeatherZone2]` (when `WZCount≥3`), `[Plane]`, `[GameOptions]`, `[Description]`

No unexpected top-level sections. No `[NOTAM]` section.

### 14.3 Key coverage vs this spec

All keys in C3 samples match §5 or indexed patterns. **`DesignatedTime`** documented in §5.2.1.

| Finding | Result |
|---------|--------|
| `TPSectorType` | `0` (Classic) and **`1` (Window)** observed |
| `TPSectorDirection` | Always `0` in C3 |
| Penalty zones | **`PZCount=1`** in race replay; **`PZCount=3`** in `winch.fpl` — full `PZPos*`/`PZBase`/`PZTop`/`PZPenaltyTimeFactor` for indices 0–2 |
| `PZPenaltyTimeFactor` | **5** (default UI) in `winch.fpl`; other samples use task-level penalties |
| `RandSeed` | Positive integers in all C3 samples |
| `PenaltyAirspaceEnterance` | Values 100, 120, 200, 210 observed |
| `WindUpperSpeed` | `0` in some zones; up to `16.667` m/s in AA3 |
| `ThermalsOverdevelopment` | `0` and `1` observed (`winch.fpl` zone 2) |
| `ThermalsInversionheight` | `2200`–`4425` m AMSL observed |
| `HighCloudsCoverage` | Range 1–5 |
| `Polygon{N}X/Y` | Up to **12** vertices (`PointCount=12`, LakeKeepitC3) |
| `[Task]` metadata | `TaskVersion`/`TaskID`/`TaskName` on condor.club exports |
| `StartType` | **`0`** aerotow, **`1`** winch, **`2`** airborne/airstart **confirmed** |
| `StartHeight` | **410**, 680, 700, **1000**, **1400**, 1500 observed |
| Landscapes | **AA3**, **CW-Swiss**, **Japan-Shikoku3**, **LakeKeepitC3**, **Sierradlv**, **Slovenia3** |
| Turnpoint count | **2**–**9** |
| `TPRadius` | **500**–**15000** m |
| AAT | **Slovenia3** and **Sierradlv** (`DesignatedTime` on Sierradlv) |
| `WZCount` | **1**, **2**, and **3** observed; `BorderWidth` up to **12000** m (`winch.fpl` zone 1) |
| `MoveSpeed` | Up to **13.889** m/s (~50 km/h) in `winch.fpl` weather zone 1 |

### 14.4 Spec claims confirmed

- INI structure with indexed turnpoint keys (`TPName0`…`TPName{N-1}`)
- Version code mapping (`3000`, `3100`)
- C3 weather zone model with `WZCount` matching zone section count (up to 3 zones validated)
- Airport `TPAngle` opaque encoding (large values on takeoff points)
- AAT large-radius turnpoints and **`DesignatedTime`** on club AAT tasks
- Window sector geometry (`TPSectorType=1`, `TPWidth`, `TPHeight`, `TPAzimuth`)
- Penalty zone quadrilateral + altitude + factor fields (**multi-zone `PZCount=3` validated in `winch.fpl`**)
- Multi-zone weather with moving polygons and overdevelopment (`winch.fpl`)
- condor.club task references in `[Description] Text` and `TaskID`/`TaskName`

### 14.5 Open questions (Condor 3)

| Item | Status |
|------|--------|
| **Airport `TPAngle` encoding** | Opaque (~29098, etc.) — not plain degrees |
| **`DesignatedTime` vs `AATTime`** | Both present on Sierradlv AAT; relationship unclear |
| **Ghost / `.ftr` settings** | Not stored in `.fpl` files examined |
| **Landscapes not in corpus** | Pumalin Park (empty download stub), others |
| **Plane ballast round-trip** | Forum reports UI may ignore `Water`/`FixedMass`/`CGBias`/`Seat` on load |
| **`PZCount > 8` in-game** | Forum warns hand-edited values above UI limit may not work (3 zones validated in `winch.fpl`) |

### 14.6 Recommended follow-up (C3)

1. Re-download failed condor.club stubs (Pumalin Park, FGVC day #10) while logged in.
2. Save the same task from Flight Planner before/after changing ballast to confirm round-trip behaviour.
3. Run `python validate_fpl.py --c3-only` after adding samples.

---

## Appendix C: Out of scope (Condor 1 / 2)

This spec targets **Condor 3 only**. The following are documented elsewhere or differ materially:

| Topic | C1/C2 behaviour (not covered here) |
|-------|-------------------------------------|
| Version codes | `1150` (C1), `2000`–`2200` (C2) |
| `[Weather]` | Flat wind/thermal keys (no `[WeatherZoneN]`) |
| `[NOTAM]` section | Ghosts, launch filters in C1/C2 UI — absent from C3 `.fpl` |
| `ThermalsInversionheight` | AGL in C2, AMSL in C3 (FPL2V3 converts) |
| Extra `[GameOptions]` | `PenaltyLostKnuckle`, `MaxTowplanes`, tail-hunt keys (C1) |
| Migration | Use [FPL2V3](https://condorutill.fr/FPL2V3/) for C2→C3 conversion |

One C1 reference file (`reference_pycondor_C1_default.fpl`, version `1150`) remains in the validation corpus for regression only.
