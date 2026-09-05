# Component source registry — retained drum-internals research

> **Legacy research, not current geometry.** This evidence was gathered for
> the earlier FreeCAD feasibility study. Datasheets and useful vendor geometry
> are retained, but all old FreeCAD models and scripts were removed after
> Blender became the design authority. Revalidate every candidate before a
> production selection.

Every dimension below comes from the manufacturer source linked in each
section. Nothing is estimated. Where sources disagree, both values are
listed and the envelope uses the conservative one. Machine-readable truth
The removed study used `registry.py` as its machine-readable envelope source;
this retained file is now the provenance record only.

Drum constraint used throughout: shell **Ø24 × 54 mm** per drum (positions
from the approved model `cad/deepreal.FCStd` @ dacd90c), assumed usable
interior **Ø21 × 51 mm** (wall 1.5 mm, end caps 1.5 mm — *assumption, not
a design decision*).

Evidence classification (Gate 1.5B):
- **OFFICIAL-VERIFIED** — full 3D dims from an official datasheet /
  drawing / STEP, in hand under `assets/`
- **OFFICIAL-INCOMPLETE** — official document in hand, some envelope dims
  missing from it (gap named)
- **ENGINEERING-ASSUMPTION** — assumed by this study, not sourced; always
  labelled
- **UNRESOLVED** — no official value obtainable (gated / 404);
  placeholder geometry is a lower bound only

Status legend: **candidate** = plausible in-drum · **candidate-borderline**
= only under orientations Gate 2 must verify · **candidate-external** =
cannot enter the drum, housing-mount only · **no-fit-reference** = exceeds
the drum shell, modelled for comparison only · **unresolved-reference** =
official dims unobtainable, lower-bound placeholder ·
**placeholder-assumption** = stand-in for a part class not yet selected.

---

## Gate 1 components (actuators + all-in-one sensors)

### 1. Orbbec Astra Mini Pro — no-fit-reference · OFFICIAL-VERIFIED

- **Function:** structured-light depth + RGB, all-in-one (MX6000 ASIC)
- **Envelope:** 84.90 × 20.00 × 19.92 mm (datasheet; drawing shows ±0.30 / ±0.35 tol)
- **Weight:** 34 g (datasheet v1.0) — web page says 35 g *(disagreement recorded)*
- **Electrical:** USB 2.0, DF13 5-pin (GND/GND/DP/DM/VDD 5 V); <2.4 W (web page)
- **Optical:** SL 855 nm (datasheet) / 850 nm (web page) *(disagreement recorded)*; depth 640×480@30, 0.6–6 m (datasheet) / 0.6–5 m (web); RGB 640×480
- **Sources:** product page https://orbbec3d.com/product-astra-mini-pro/ · datasheet `../../references/components/datasheets/orbbec-astra-mini-pro-datasheet.pdf` (product drawings p.5: LDM / RGB / IR layout, 2× M2 mounting)
- **CAD:** no official STEP obtained (datasheet drawing only)
- **Fit:** 84.9 mm width vs Ø24 mm drum — **cannot enter the drum.**

### 2. Orbbec Astra Embedded S — no-fit-reference · OFFICIAL-INCOMPLETE

- **Function:** structured-light depth + RGB, all-in-one
- **Envelope:** 69.0 × 22.9 × 15.0 mm (product page)
- **Weight:** 27 g
- **Electrical:** USB 3.0 Type-C, <2.2 W
- **Optical:** 940 nm; depth 1280×800@30, 0.25–1.5 m; RGB 1080p
- **Sources:** product page https://orbbec3d.com/product-astra-embedded-s/
- **CAD:** none downloaded
- **Fit:** 69 mm width vs Ø24 mm drum — **cannot enter the drum.**

### 3. Raspberry Pi Camera Module 3 (standard) — candidate-borderline · OFFICIAL-VERIFIED

- **Function:** RGB camera (Sony IMX708, 11.9 MP, PDAF), CSI-2
- **Envelope:** 25.0 × 24.0 × 11.5 mm (official product page; Wide variant 12.4 mm thick)
- **Drawing detail:** board 25 × 23.862 mm; height stack 11.3 mm (lens 6.98 + 3.875 + FPC 1.12); mount holes 4× Ø2.2; lens Ø5.75; FOV 66°(D)/41°(H per drawing)
- **Electrical:** CSI-2, 15×1 mm FPC (22-pin 0.5 mm at Pi end)
- **Sources:** product page https://www.raspberrypi.com/products/camera-module-3/ · mech drawing `../../references/components/datasheets/rpi-camera-module-3-standard-mechanical-drawing.pdf` · official STEP `assets/rpi-camera-module-3-step.zip`
- **CAD verification (this study):** `Camera_module_3_std_model_simple.stp` measured **23.862 × 25.000 × 10.245 mm**; wide STEP 23.862 × 25.000 × 11.400 mm (STEPs omit the FPC tail; envelope uses the conservative published 11.5 mm)
- **Fit (Gate 1.5B, validator-verified):** minimum enclosing circle over all axis-aligned orientations = **Ø26.61 mm** (25 axial, 24×11.5 cross) — exceeds even the Ø24 mm shell, before any interior assumption. **No in-drum orientation exists.**

### 4. Pololu 75:1 Micro Metal Gearmotor MP 6V w/ 12 CPR encoder (item 5137) — candidate · OFFICIAL-VERIFIED

- **Function:** DC gearmotor actuator (direct drum drive candidate)
- **Envelope (official STEP, measured):** 41.6 × 14.9 × 13.6 mm — includes Ø3 mm D-shaft (~9.5 mm) and side-entry encoder connector
- **Published dimension PDF:** gearbox cross-section 10 × 12 mm, gearbox length 9 mm, overall length max 32.5 mm **excluding** the shaft
- **Electrical:** 6 V MP brushed motor; 12 CPR magnetic quadrature encoder, JST-SH side connector
- **Sources:** product page https://www.pololu.com/product/5137 · dimension diagram `../../references/components/datasheets/pololu-5137-dimensions.pdf` · official STEP zip `assets/pololu-micro-metal-gearmotor-step-models.zip` → extracted `assets/pololu-step/With Encoder, Side Connector/mmgm-pm-enc-side-con.step` (75:1 MP = `pm`, non-1000:1 gearbox, per zip README)
- **Fit:** cross-section needs a Ø20.2 mm circle → fits Ø21 mm assumed ID with ~0.4 mm radial margin; 41.6 mm length leaves 9.4 mm of the 51 mm interior for shaft support/wiring — **tight but plausible.**

### 5. T-Motor GB2208 KV128 — no-fit-reference · OFFICIAL-VERIFIED

- **Function:** brushless gimbal motor (direct-drive candidate)
- **Envelope:** Ø27.5 × 23 mm cylinder (spec table); centre hole Ø6 mm
- **Weight:** 39.5 g (incl. 20 cm cable)
- **Electrical:** 3–4S lipo, 12N14P, 14.4 Ω, 0.07 Nm, KV128
- **Sources:** product page https://store.tmotor.com/product/gb2208-gimbal-type.html · technical drawing `../../references/components/datasheets/tmotor-gb2208-drawing.jpg` (needed browser headers to download)
- **CAD:** no official STEP; a community GrabCAD model exists (third-party, **not used**)
- **Fit:** Ø27.5 mm > Ø24 mm drum shell — **cannot enter the drum.** (Would also need an external ESC + encoder.)

### 6. Robotis DYNAMIXEL XL330-M288-T — candidate-external · OFFICIAL-INCOMPLETE

- **Function:** smart servo (integrated driver + 4096-step absolute magnetic encoder)
- **Envelope:** 20 × 26 × 34 mm (official drawing: depth = 23 body + 3 horn flange)
- **Drawing detail:** horn P.C.D Ø12, 4× Ø1.6 holes (M2 tapping, DP 3.0 max), horn centre 9.5 mm from top edge
- **Weight:** 18 g
- **Electrical:** 5 V, TTL bus (3.3/5 V logic), stall 0.52 Nm, no-load 104 rpm
- **Sources:** eManual https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/ · store page https://www.robotis.us/dynamixel-xl330-m288-t/ · drawing `../../references/components/datasheets/robotis-xl330-m288-drawing.png`
- **CAD:** **UNRESOLVED** — official STEP/drawing links (download.php no=1985/1986/1987) 404 on both www.robotis.com and en.robotis.com; envelope is from the official drawing only
- **Fit:** smallest face (20×26) needs a Ø32.8 mm circle > Ø21 mm assumed ID — **cannot enter the drum**; external housing-mount drive only.

---

## Gate 1.5B components (discrete depth architecture)

### 7. Raspberry Pi CM3 Sensor Assembly (standard lens) — candidate · OFFICIAL-VERIFIED

**Replaces the full CM3 board as the in-drum RGB option.**

- **Function:** bare RGB sensor + lens sub-assembly (remote head off the CM3 board; IMX708, 11.9 MP, PDAF)
- **Footprint:** **10.8 × 10.8 mm ±0.15** (TNBA1392 REV 0 key dims, CPK ≥ 1.33)
- **Depth (optical stack):** **6.98 mm** per product brief p.4 — *discrepancy recorded:* TNBA1392 side view says **6.21 ±0.15 at 10 cm focus / 5.97 ±0.15 at infinity** (AF moves the lens); body height 3.875 ±0.15 matches both sources. Envelope uses the conservative brief value 6.98.
- **Side-view stack (TNBA1392):** 0.4 ±0.05 PCB + 0.15 AA glue + 3.875 ±0.15 body + lens protrusion; reinforcing glue max 0.8×0.8; FPC+EMI 0.13 ±0.05; tail PCB+ink 0.45 ±0.05
- **Lens:** Ø5.75 (std) / Ø6.95 (wide, depth 8.3); FOV 75° ±3 diagonal / 66° H / 41° V; EFL 4.74 mm F1.79 (brief rounds F1.8); image circle Ø8.4 mm; focus 10 cm–∞ (wide 5 cm–∞)
- **FPC tail:** 8.9 ±0.15 wide, extends 4.0 ±0.15 beyond body edge; bend area 7 ±0.15 wide; **bends 180° × 20 cycles at R = 0.8 mm** (TNBA1392 technical requirement 3); MIPI impedance 100 ±10 Ω; far-end connector HLM-033M-3002-76 (30-pin, 4.45 wide, 1.3 ref thick)
- **Electrical:** DVDD 1.1 V / AVDD 2.8 V / DOVDD 1.8 V; VCM driver DW9800W (I2C 0x18); EEPROM BL24SA64D-CS (0xA0); PWDN low-effective
- **Variants:** SA31VA30P std / SA31NA30P std-NoIR / SA36VA30P wide / SA36NA30P wide-NoIR, $15–25, in production until ≥ Jan 2030
- **Sources:** product brief `../../references/components/datasheets/rpi-camera-module-3-sensor-assembly-product-brief.pdf` (physical spec p.4, variants p.5) · standard datasheet `../../references/components/datasheets/rpi-camera-module-3-sensor-assembly-standard-datasheet.pdf` (TNBA1392 REV 0, TSP / Chongqing TS-Precision, single-page drawing)
- **CAD:** none published; multi-part envelope built from TNBA1392 by this study (lens / body / PCB / FPC-tail parts)
- **Fit (Gate 1.5B, validator-verified):** best enclosing circle **Ø12.9 mm** (10.8 axial) ≤ Ø21 assumed ID; radial-optical placement verified collision-free and contained in layouts SL-A / SL-B.

### 8. OmniVision OV9281 (OV09281-H64A) — candidate · OFFICIAL-INCOMPLETE

**Grounds the structured-light IR camera in a manufacturer document.**

- **Function:** global-shutter NIR camera die (structured-light receiver)
- **Official (product brief v1.4, May 2024):** 1280×800 @ 120 fps max; global shutter, OmniPixel3-GS, 3 µm pixel; **image area 3896 × 2453 µm**; CRA 9° linear; 1/4" optical format; 2-lane MIPI + DVP; 8/10-bit RAW; 2.8/1.2/1.8 V rails; 156 mW active; −30..+85 °C operating; **64-pin CSP** (ordering code OV09281-H64A)
- **UNRESOLVED:** CSP package body X/Y/Z — not in the product brief; the full OV9281 datasheet with the package outline is NDA-gated at OmniVision. Die thickness in the envelope (1.5 mm) is an **ENGINEERING-ASSUMPTION**; the Ø6 × 4 mm lens barrel is an **ENGINEERING-ASSUMPTION** allowance (no lens sourced; CRA 9° is the only official optical constraint)
- **DEMOTED (unsourced):** the earlier "8 × 8 × 5.8 mm" OV9281 module-class figure carried in discussion has no manufacturer source and is removed from the envelopes; the official anchor is the image area 3.896 × 2.453 mm + CSP package type
- **Module alternative ruled out:** Arducam OV9281 board 24 × 25 mm → minimum enclosing circle ≈ Ø34.7 mm > Ø21 mm assumed ID — cannot enter the drum; bare-sensor integration is the only in-drum path
- **Sources:** `../../references/components/datasheets/omnivision-ov9281-product-brief.pdf`
- **Fit:** modelled in layouts SL-A / SL-B (die + lens allowance); contained with margin.

### 9. ams OSRAM BELICE-850 — candidate · OFFICIAL-VERIFIED

- **Function:** 850 nm dot-projector VCSEL module for structured light (~10k dots per emitter pair)
- **Envelope:** **3.50 ±0.15 × 3.40 ±0.15 × 3.56 ±0.1 mm** (datasheet fig. 11 top view, fig. 12 side view incl. 0.25 mm step feature)
- **Optical aperture:** 2.3 × 2.3 mm, corner R0.1 (fig. 13)
- **Bottom pads:** 2.80 ±0.1 × 2.80 ±0.1 mm field; pads 0.50 / 2.05 / 0.25 / 0.30 ±0.1; fiducials 2× Ø0.20; corner radii 4× R0.70
- **Sources:** `../../references/components/datasheets/ams-belice-850-datasheet.pdf` (DS000618 v2-00, 2019-May-15, 23 pp)
- **CAD:** none published; envelope from the datasheet drawings
- **Integration:** SMT module — needs carrier PCB + VCSEL driver (not included); used as the projector in layout **SL-A**
- **Fit:** contained in layouts with large margin.

### 10. ams OSRAM Belago1.2 — candidate · OFFICIAL-VERIFIED

- **Function:** 940 nm pseudo-random dot projector, ~15k dots, with resistive-ITO eye-safety interlock
- **Envelope:** **4.200 ±0.075 × 3.900 ±0.050 × 3.325 ±0.050 mm** (datasheet fig. 6: top view / front view height)
- **Optical aperture / MLA active area:** 2.0 ±0.1 square, corner radii 4× R0.750; FOI orientation marked on package (fig. 11)
- **Pads (bottom view):** Anode(+) / Cathode / Sense1 / Sense2; pad dims 0.550 / 0.950 / 2.050 / 0.250 ±0.100 etc.; pin-compatible with Belago1.1
- **Drive:** ~0.7 A pulse class (fig. 4 @ 25 °C, Ti = 1 ms, 30 fps); MSL3, peak reflow 250 °C; ventilation hole present; **must not be ultrasonically cleaned**
- **Eye safety:** every emitter hotspot-inspected in production; Sense1/Sense2 open on ITO fracture → driver must cut power (needs driver-side support)
- **Ordering:** AQAA-30 / Q65114A0198
- **Sources:** `../../references/components/datasheets/ams-belago1-2-datasheet.pdf` (DS001002 v1-00, 2025-Apr-22, 19 pp)
- **CAD:** none published; envelope from the datasheet drawings
- **Fit:** modelled as the projector in layout **SL-B**; contained (station-2 Z stack gap to the OV9281 lens allowance ≈ 0.45 mm — flagged).

### 11. Infineon IRS2877A / IRS2877AS — candidate · OFFICIAL-VERIFIED

- **Function:** indirect-ToF depth imager die (REAL3), 640×480 (~307k px, upscaled output), 940 nm
- **Package (PG-LFBGA-65-1):** body **9.0 ±0.1 × 9.0 ±0.1 mm**, height **1.325 ±0.14 (max 1.465)**; ball Ø0.42, pitch 0.8, 65 balls, standoff min 0.25; sensor/lens area 4.6 ±0.05 × 4.9 ±0.05 with centre offset; 4 mm image circle (1/4" class)
- **STEP verification (this study):** official STEP `../../references/components/cad/infineon-pg-lfbga-65-1-3d.stp` probed — union bounds **9.000 × 9.000 × 1.465 mm** = outline max tolerance exactly; 168 solids (body 9×9×0.915 cap + substrate + balls)
- **Variants:** IRS2877A (AEC-Q100 grade 2) / IRS2877AS (adds ISO 26262 ASIL-D)
- **Electrical:** 1.8 V / 3.3 V rails; **companion controller IRS9103A mandatory**
- **FULL-STACK RESERVATION:** the envelope is the imager die (+ Ø6 × 4 mm lens allowance, ENGINEERING-ASSUMPTION). A working ToF camera additionally needs: receiving lens (unsourced), flood-illumination VCSEL + driver (unsourced — placeholder modelled), IRS9103A companion + passives + carrier PCB (keep-out modelled, dims assumed), host interface. iToF at 940 nm gives depth + active-amplitude simultaneously; sunlight robustness per brief.
- **Sources:** `../../references/components/datasheets/infineon-irs2877as-product-brief.pdf` · `../../references/components/datasheets/infineon-pg-lfbga-65-1-package-outline.pdf` · `../../references/components/cad/infineon-pg-lfbga-65-1-3d.stp`
- **Fit:** modelled in layout **ToF-A**; contained with margin.

### 12. Infineon IRS2976C — unresolved-reference · UNRESOLVED

- **Function:** indirect-ToF depth imager bare die, 640×480, 940 nm, 1/4" (4 mm) image circle; companion IRS9102C
- **UNRESOLVED:** die dimensions are behind the MyInfineon portal (gated) — not obtained. Modelled geometry = Ø4.0 × 0.5 mm disc = **the official 4 mm image circle as a lower-bound footprint only**; a real die + WLO/wire-bond stack is larger
- **Not carried into layouts.** Same full-stack reservations as IRS2877A, plus chip-on-board handling would be an in-house packaging burden
- **Sources:** family reference `../../references/components/datasheets/infineon-irs2877as-product-brief.pdf`

### 13. ToF flood-illuminator placeholder — placeholder-assumption · ENGINEERING-ASSUMPTION

- **Function:** stand-in for the 940 nm flood VCSEL every iToF camera needs
- **Envelope:** 3.50 × 3.40 × 3.56 mm, borrowed from BELICE-850 (OFFICIAL for BELICE-850) as representative of the SMT VCSEL module class
- **No part selected.** Gate 2 candidates: ams OSRAM TARA2000-AUT class flood illuminators; must pair with the eye-safety drive scheme.

---

## Preliminary no-fit / fit summary

| Component | Envelope (mm) | vs Ø24 drum (Ø21 assumed ID) | Evidence | Status |
|---|---|---|---|---|
| RPi CM3 Sensor Assembly | 10.8×10.8×6.98 (+FPC tail) | fits; layouts SL-A/SL-B verified | OFFICIAL-VERIFIED | candidate |
| OmniVision OV9281 (bare) | die 3.9×2.5 (+lens allowance Ø6×4) | fits; pkg dims UNRESOLVED | OFFICIAL-INCOMPLETE | candidate |
| ams BELICE-850 | 3.50×3.40×3.56 | fits | OFFICIAL-VERIFIED | candidate |
| ams Belago1.2 | 4.20×3.90×3.325 | fits (SL-B station-2 gap 0.45 mm) | OFFICIAL-VERIFIED | candidate |
| Infineon IRS2877A(S) | 9.0×9.0×1.465 (+lens allowance) | fits; full-stack reservations | OFFICIAL-VERIFIED | candidate |
| Infineon IRS2976C | Ø4.0 lower bound only | die dims UNRESOLVED (gated) | UNRESOLVED | unresolved-reference |
| ToF illuminator placeholder | 3.50×3.40×3.56 (borrowed) | fits | ENGINEERING-ASSUMPTION | placeholder-assumption |
| Pololu 5137 gearmotor | 41.6×14.9×13.6 | cross-section Ø20.2 fits; length tight | OFFICIAL-VERIFIED | candidate |
| RPi Camera Module 3 (board) | 25×24×11.5 | min enclosing Ø26.6 > Ø24 shell — **no in-drum orientation** | OFFICIAL-VERIFIED | candidate-borderline |
| DYNAMIXEL XL330-M288 | 20×26×34 | min circle Ø32.8 — cannot enter | OFFICIAL-INCOMPLETE | candidate-external |
| Orbbec Astra Mini Pro | 84.9×20×19.92 | exceeds shell outright | OFFICIAL-VERIFIED | no-fit-reference |
| Orbbec Astra Embedded S | 69×22.9×15 | exceeds shell outright | OFFICIAL-INCOMPLETE | no-fit-reference |
| T-Motor GB2208 | Ø27.5×23 | exceeds shell outright | OFFICIAL-VERIFIED | no-fit-reference |

**Structured-light depth:** no commercial all-in-one SL module (Orbbec
84.9/69 mm wide) fits a Ø24 mm drum. The discrete architecture
(CM3 Sensor Assembly + OV9281 bare sensor + BELICE-850/Belago1.2
projector) is modelled and validated in layouts SL-A / SL-B
(`depth_architecture_report.md`).

**Time-of-flight depth:** IRS2877A + illuminator placeholder + carrier
keep-out fit easily (ToF-A), but the full stack has unsourced elements
(lens, illuminator, companion board) — see the report's reservation list.

**Wiring across the rotating joint** (140–160° travel): unresolved —
capsule slip ring vs flex loop trade-off not yet researched (G10 group
empty).

**Bearings/supports:** not yet researched (G09 group empty).
