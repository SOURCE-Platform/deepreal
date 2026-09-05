# Depth architecture report — Gate 1.5B (legacy study)

> **Historical evidence only.** The original FreeCAD documents, build scripts,
> and validators referenced below were intentionally removed when the project
> moved to a Blender-first workflow. Component findings and vendor sources
> remain useful, but geometry claims must be revalidated in the current Blender
> model and later manufacturing CAD.

Drum-internals feasibility, discrete depth-sensing architectures for the
**unchanged** Ø24 × 54 mm sensor-head drums (`cad/deepreal.FCStd` @ main
dacd90c; sha1 guard `d27685ec2b35…` re-verified in this study).
Branch: `explore/drum-internals-feasibility`. All geometry lives in
`cad/feasibility/drum_internals.FCStd` (rebuild: `build.py`; checks:
`validate_feasibility.py`; schematics: `render_layouts.py`).

---

## 1. Scope and constraints

Gate 1.5B replaces the Gate 1 "all-in-one module" depth hypothesis
(Orbbec Astra Mini Pro / Embedded S — both no-fit at 84.9 / 69 mm width)
with **discrete architectures** assembled from bare components, and
evaluates them inside the current drum using only sourced data.

Hard constraints honoured:
- No exterior redesign: `deepreal.FCStd` untouched (checksum-guarded).
- No drum enlargement: all layouts inside the existing Ø24 × 54 shell,
  against the **assumed** usable interior Ø21 × 51 mm (wall 1.5 mm, end
  caps 1.5 mm — assumption, not a design decision).
- No actuator packaging (that is the next gate; the layouts only prove
  the optical stack leaves X-length for it).
- No conclusion that a larger drum (Ø35 …) is needed.
- STOP after this report.

Drum frame: axis along X at Y=−1.5 / Z=20; Face-drum interior
X −54.5 … −3.5. Optical axes are radial, user-facing (−Y) at the 0° rest
position; rotation travel ±75° (150° representative of 140–160°
required) sweeps the apertures through the window band.

## 2. Evidence classification

| Class | Meaning | Components |
|---|---|---|
| OFFICIAL-VERIFIED | Full dims from official docs/STEP in hand | CM3 Sensor Assembly · BELICE-850 · Belago1.2 · IRS2877A · (Gate 1: CM3 board, Pololu 5137, GB2208, Astra Mini Pro) |
| OFFICIAL-INCOMPLETE | Official doc in hand, some dims missing | OV9281 (package X/Y/Z absent from brief) · (Gate 1: Astra Embedded S, XL330 STEP 404) |
| ENGINEERING-ASSUMPTION | Assumed, labelled, never presented as fact | OV9281 die thickness + lens barrels · ToF illuminator placeholder · carrier-PCB keep-outs |
| UNRESOLVED | No official value obtainable | OV9281 package outline (NDA-gated) · IRS2976C die dims (MyInfineon-gated) · XL330 STEP (404) |

Every envelope object in the document carries its `Evidence` class as a
property; `registry.py` and `component_sources.md` carry the prose.

## 3. RGB architecture — both results

**Option 1 — full CM3 board: NO in-drum orientation exists.**
Envelope 25 × 24 × 11.5 mm (official page; STEP-verified
23.862 × 25 × 10.245). Best axis-aligned case (25 mm axial, 24 × 11.5
cross-section) needs a **Ø26.61 mm** enclosing circle — it exceeds the
Ø21 mm assumed interior *and even the Ø24 mm shell itself*. The board is
eliminated for in-drum RGB regardless of interior assumptions.
(Validator checks `RGB option 1 … NO in-drum orientation` /
`CM3 board exceeds even the drum shell`.)

**Option 2 — CM3 Sensor Assembly: fits with margin.**
10.8 × 10.8 mm footprint (TNBA1392 REV 0, key dims ±0.15, CPK ≥ 1.33);
optical stack depth **6.98 mm** (product brief p.4; TNBA1392 side view
shows 6.21 ±0.15 @ 10 cm focus / 5.97 ±0.15 @ ∞ — the AF moves the
lens; discrepancy recorded, envelope uses the conservative 6.98).
Multi-part envelope: lens Ø5.75 × 2.505 + body 10.8 × 10.8 × 4.025
(3.875 body + 0.15 AA glue) + PCB 0.45 + FPC-tail keep-out
(8.9 wide, 4.0 beyond body, 180° bend at R = 0.8 per TNBA1392 req. 3).
Best enclosing circle **Ø12.9 mm**; radial-optical placement verified in
both SL layouts. FOV 75° ±3 diag / 66° H / 41° V; EFL 4.74 F1.79;
image circle Ø8.4; IMX708-AAJH5-C; CSI-2 via 30-pin HLM-033M-3002-76.

**Verdict: the CM3 Sensor Assembly is the in-drum RGB camera.** The full
board remains modelled only as a no-fit reference.

## 4. SL IR camera grounding (OV9281)

The structured-light receiver is grounded in the official OmniVision
product brief (v1.4): 1280×800 @ 120 fps, **global shutter**
(OmniPixel3-GS, 3 µm), image area **3.896 × 2.453 mm**, CRA 9° linear,
1/4" format, 2-lane MIPI + DVP, 156 mW active, 64-pin CSP
(OV09281-H64A). The unsourced "8 × 8 × 5.8 mm" figure from earlier
discussion is **demoted** and removed from the envelopes. The Arducam
24 × 25 mm module alternative is ruled out (enclosing circle ≈ Ø34.7 mm
> Ø21 mm).

Honest gaps: the CSP **package outline is not in the brief** (full
datasheet is NDA-gated) → package X/Y/Z **UNRESOLVED**; die thickness
(1.5 mm) and the Ø6 × 4 mm lens barrel are labelled
ENGINEERING-ASSUMPTIONs. A bare sensor also needs a carrier PCB and an
NIR lens with CRA matched to 9° — both Gate 2 work.

## 5. Projector candidates (structured light)

| | **BELICE-850** | **Belago1.2** |
|---|---|---|
| Envelope (mm) | 3.50 ±0.15 × 3.40 ±0.15 × **3.56 ±0.1** | 4.200 ±0.075 × 3.900 ±0.050 × **3.325 ±0.050** |
| Wavelength / pattern | 850 nm, ~10k dots (pair) | 940 nm, ~15k pseudo-random dots |
| Aperture | 2.3 × 2.3, R0.1 | MLA active 2.0 ±0.1 sq, 4× R0.750 |
| Pads | 2.80 × 2.80 field, fiducials 2× Ø0.20 | Anode/Cathode/Sense1/Sense2 |
| Eye safety | (driver-side) | **integrated ITO interlock** (Sense1/2 open on fracture); 100% hotspot inspection |
| Notes | DS000618 v2-00 | DS001002 v1-00; pin-compatible w/ Belago1.1; MSL3; ordering AQAA-30 |
| Evidence | OFFICIAL-VERIFIED | OFFICIAL-VERIFIED |

Both are SMT modules needing a carrier PCB and VCSEL driver. BELICE-850
(850 nm) pairs slightly better with OV9281 NIR QE; Belago1.2 (940 nm)
brings the hardware interlock and 1.5× the dots. Both fit trivially
(Ø21 interior). The BELICE-850 height (3.56 ±0.1) was extracted from
the datasheet side view at 6× zoom after the 3× raster proved illegible.

## 6. ToF candidates

**IRS2877A / IRS2877AS (candidate, OFFICIAL-VERIFIED).** REAL3 iToF
imager, 640×480 (~307k px, upscaled), 940 nm, 4 mm image circle,
AEC-Q100 Gr2 (AS variant adds ISO 26262 ASIL-D), integrated eye-safety
logic, 1.8/3.3 V. Package PG-LFBGA-65-1: **9.0 ±0.1 × 9.0 ±0.1 ×
1.325 ±0.14 mm** (max 1.465); ball Ø0.42 / pitch 0.8 / 65 balls /
standoff ≥ 0.25; sensor-lens area 4.6 × 4.9 with centre offset. The
official STEP was probed: union bounds **9.000 × 9.000 × 1.465 mm** =
outline max exactly.

**Full-stack reservations (honest):** the verified envelope is the
imager die alone. A working ToF camera adds: receiving lens (unsourced —
Ø6 × 4 mm allowance modelled as assumption), **flood-illumination VCSEL
+ driver** (unsourced — BELICE-class placeholder modelled), **companion
controller IRS9103A** + passives + carrier PCB (keep-out modelled with
assumed dims), host interface and calibration. iToF also computes depth
on the companion/host — integration burden is higher than the SL path's
"camera + projector + host stereo/SL matching".

**IRS2976C (unresolved-reference, UNRESOLVED).** 640×480, 940 nm, 4 mm
image circle, bare die, companion IRS9102C. Die dimensions are
MyInfineon-gated → **UNRESOLVED**; modelled only as a Ø4.0 × 0.5 mm
image-circle lower bound and **not carried into any layout**. Bare-die
integration (COB/WLO) would be an in-house packaging burden even if dims
were obtained.

## 7. Layout SL-A — axial line

RGB → IR → projector in one row along the drum axis; all apertures
flush at the user-facing wall plane (r = 9.5 mm, 1 mm clear of the
assumed interior).

| Station | Component | X centre (mm) | X span (mm) | Aperture |
|---|---|---|---|---|
| 1 | CM3 Sensor Assembly | −47.10 | −52.50 … −41.70 | lens Ø5.75, flush |
| 2 | OV9281 + lens allowance | −36.70 | −39.70 … −33.70 | Ø6 allowance, flush |
| 3 | BELICE-850 | −29.95 | −31.70 … −28.20 | 2.3 × 2.3, flush |

Carrier-PCB keep-out (assumption): 26.3 × 1.0 × 8.0 mm behind the back
planes (Y −3.9 … −2.9). The CM3 SA FPC tail exits tangentially (+Z) at
the back and folds 180° (R 0.8) along the carrier.

**Metrics (validator):** X span used **26.3 mm**, remaining **24.7 mm**
of 51 · worst corner radius 9.96 mm → **min radial clearance 0.54 mm** ·
collision-free (8 parts pairwise) · all parts inside Ø21.
Schematics: `legacy-layouts/layout_SLA_side.svg`,
`legacy-layouts/layout_SLA_cross.svg`.

## 8. Layout SL-B — mixed axial / cross-section

RGB axial at station 1 (as SL-A); OV9281 and **Belago1.2** share
station 2 (X centre −36.70), split tangentially: OV9281 at Z +2.7 mm,
Belago1.2 at Z −2.7 mm, both apertures **recessed to r = 8.5 mm**
(2.0 mm behind the interior wall).

| Station | Component | X centre (mm) | Z offset (mm) | Aperture |
|---|---|---|---|---|
| 1 | CM3 Sensor Assembly | −47.10 | 0 | flush |
| 2a | OV9281 + lens allowance | −36.70 | +2.7 | recessed 2.0 |
| 2b | Belago1.2 | −36.70 | −2.7 | recessed 2.0 |

**Metrics (validator):** X span used **20.8 mm**, remaining **30.2 mm**
(saves 5.5 mm vs SL-A) · worst corner radius 10.23 mm → **min radial
clearance 0.27 mm** · collision-free (station-2 Z gap between the OV9281
lens allowance and the Belago1.2 body ≈ **0.45 mm** — assembly-tolerance
risk, flagged) · all parts inside Ø21.
Trade-offs vs SL-A: shorter X, but recessed apertures need an oversized
window with a vignetting check, and the 0.45 mm Z gap plus 0.27 mm
radial clearance make SL-B strictly a "if X length runs out" fallback.
Schematics: `legacy-layouts/layout_SLB_side.svg`,
`legacy-layouts/layout_SLB_cross.svg`.

## 9. Layout ToF-A — iToF camera inside the current drum

IRS2877A (+ lens allowance) axial with a 940 nm flood-VCSEL placeholder
and a carrier-PCB keep-out holding the IRS9103A companion + driver +
passives:

| Station | Component | X centre (mm) | X span (mm) |
|---|---|---|---|
| 1 | IRS2877A BGA + lens allowance | −48.00 | −52.50 … −43.50 |
| 2 | ToF illuminator placeholder (BELICE-class) | −39.75 | −41.50 … −38.00 |
| — | carrier-PCB keep-out (assumption) | — | −53.50 … −37.00 |

**Metrics (validator):** X span used **16.5 mm**, remaining **34.5 mm**
of 51 · worst corner radius 9.96 mm → **min radial clearance 0.54 mm** ·
collision-free · all parts inside Ø21.
The X budget proves a ToF camera fits the current drum with room to
spare for the actuator (Pololu 5137 needs 41.6 of 51 mm when axial —
see §11 note). Reservations from §6 stand: only the imager die is
OFFICIAL-VERIFIED; illuminator, lens, companion board are placeholders/
assumptions.
Schematics: `legacy-layouts/layout_ToFA_side.svg`,
`legacy-layouts/layout_ToFA_cross.svg`.

## 10. Validation results

`validate_feasibility.py` — **ALL PASS** (71 objects, 19 groups):

- 13/13 library envelopes match registry dims (multi-part entries
  compared against their parts union) — incl. CM3 SA
  10.8 × 14.8 × 6.98 (with tail), OV9281 Ø6 × 5.5 stack, IRS2877A
  9 × 9 × 5.465 stack.
- Drum context matches the approved model (shells X −56…−2 / 2…56,
  Ø24 at Y −1.5 / Z 20; interiors Ø21 × 51; 4 travel plates ±75°).
- Exterior reference bounds match the approved Main_Housing.
- **Layout checks:** every LA_* part matches its registry part dims;
  per-layout pairwise boolean collision ≈ 0 mm³; full containment in
  the Ø21 × 51 assumed interior; aperture markers inside the drum X
  span.
- **Both RGB results:** CM3 board — no in-drum orientation (min
  enclosing Ø26.61 > Ø24 shell); CM3 Sensor Assembly — fits (Ø12.9 best
  circle; radial-optical placements verified).
- **Guard:** `cad/deepreal.FCStd` sha1 equals the main-branch blob
  (`d27685ec2b35…`) — the approved exterior was not touched.

| Layout | X used / remaining (mm) | Min radial clearance (mm) | Collision |
|---|---|---|---|
| SL-A | 26.3 / 24.7 | 0.54 | none (8 parts) |
| SL-B | 20.8 / 30.2 | 0.27 | none (8 parts; 0.45 mm Z gap flagged) |
| ToF-A | 16.5 / 34.5 | 0.54 | none (4 parts) |

## 11. Open items and Gate 2 recommendations

**UNRESOLVED (do not design against until cleared):**
1. OV9281 CSP package outline (NDA-gated) — envelope uses image area +
   assumptions.
2. IRS2976C die dims (MyInfineon-gated) — lower-bound placeholder only.
3. XL330-M288 official STEP (links 404) — drawing-derived envelope only.
4. No lens sourced for OV9281 / IRS2877A (Ø6 × 4 mm allowances are
   assumptions; CRA 9° / 4 mm image circle are the official anchors).
5. No 940 nm flood illuminator selected for ToF-A (placeholder is
   BELICE-class geometry).

**Assumptions to retire next gate:** interior Ø21 × 51 (wall/end-cap
1.5 mm); carrier-PCB keep-out dims; die thicknesses.

**Plausibility verdict (against the CURRENT Ø24 / assumed-Ø21 drums):**
- **Structured light (SL-A): PLAUSIBLE.** Entirely official-verified
  core (CM3 SA + BELICE-850) plus one OFFICIAL-INCOMPLETE die (OV9281);
  24.7 mm of the 51 mm interior remains for actuator/bearings/wiring.
- **Structured light (SL-B): PLAUSIBLE but tighter** — only if the
  5.5 mm X saving is needed; accept 0.27 mm radial clearance, 0.45 mm
  station-2 gap, recessed-window vignetting work.
- **ToF (ToF-A): GEOMETRICALLY EASY, STACK RISK HIGH** — 34.5 mm
  remaining, but illuminator/companion/lens are unsourced and iToF bring
  -up (calibration, eye-safety drive, host compute) is heavier than SL.
- **Actuator coexistence note:** Pololu 5137 (41.6 mm axial) does NOT
  fit alongside SL-A (26.3 mm) in one 51 mm drum interior; Gate 2 must
  place the actuator off-axis, in the opposite drum, in the housing
  (XL330 external drive), or revisit drive concepts. This study makes
  no actuator decision.
- **RGB:** CM3 Sensor Assembly is the only viable in-drum RGB; the full
  CM3 board is geometrically excluded (Ø26.6 > Ø24 shell).

**STOP** — per the Gate 1.5B spec this report ends the phase. No
actuator packaging, no drum-resize conclusion, no exterior change was
made or proposed.
