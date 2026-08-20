# Component source registry — drum-internals feasibility (Gate 1)

Every dimension below comes from the manufacturer source linked in each
section. Nothing is estimated. Where sources disagree, both values are
listed and the envelope uses the conservative one. Machine-readable truth
for the envelope dims lives in `registry.py`; this file is the provenance
record.

Drum constraint used throughout: shell **Ø24 × 54 mm** per drum (positions
from the approved model `cad/deepreal.FCStd` @ dacd90c), assumed usable
interior **Ø21 × 51 mm** (wall 1.5 mm, end caps 1.5 mm — *assumption, not
a design decision*).

Status legend: **candidate** = plausible in-drum · **candidate-borderline**
= only under orientations Gate 2 must verify · **candidate-external** =
cannot enter the drum, housing-mount only · **no-fit-reference** = exceeds
the drum shell, modelled for comparison only.

---

## 1. Orbbec Astra Mini Pro — no-fit-reference

- **Function:** structured-light depth + RGB, all-in-one (MX6000 ASIC)
- **Envelope:** 84.90 × 20.00 × 19.92 mm (datasheet; drawing shows ±0.30 / ±0.35 tol)
- **Weight:** 34 g (datasheet v1.0) — web page says 35 g *(disagreement recorded)*
- **Electrical:** USB 2.0, DF13 5-pin (GND/GND/DP/DM/VDD 5 V); <2.4 W (web page)
- **Optical:** SL 855 nm (datasheet) / 850 nm (web page) *(disagreement recorded)*; depth 640×480@30, 0.6–6 m (datasheet) / 0.6–5 m (web); RGB 640×480
- **Sources:** product page https://orbbec3d.com/product-astra-mini-pro/ · datasheet `assets/docs/orbbec-astra-mini-pro-datasheet.pdf` (product drawings p.5: LDM / RGB / IR layout, 2× M2 mounting)
- **CAD:** no official STEP obtained (datasheet drawing only)
- **Fit:** 84.9 mm width vs Ø24 mm drum — **cannot enter the drum.**

## 2. Orbbec Astra Embedded S — no-fit-reference

- **Function:** structured-light depth + RGB, all-in-one
- **Envelope:** 69.0 × 22.9 × 15.0 mm (product page)
- **Weight:** 27 g
- **Electrical:** USB 3.0 Type-C, <2.2 W
- **Optical:** 940 nm; depth 1280×800@30, 0.25–1.5 m; RGB 1080p
- **Sources:** product page https://orbbec3d.com/product-astra-embedded-s/
- **CAD:** none downloaded
- **Fit:** 69 mm width vs Ø24 mm drum — **cannot enter the drum.**

## 3. Raspberry Pi Camera Module 3 (standard) — candidate-borderline

- **Function:** RGB camera (Sony IMX708, 11.9 MP, PDAF), CSI-2
- **Envelope:** 25.0 × 24.0 × 11.5 mm (official product page; Wide variant 12.4 mm thick)
- **Drawing detail:** board 25 × 23.862 mm; height stack 11.3 mm (lens 6.98 + 3.875 + FPC 1.12); mount holes 4× Ø2.2; lens Ø5.75; FOV 66°(D)/41°(H per drawing)
- **Electrical:** CSI-2, 15×1 mm FPC (22-pin 0.5 mm at Pi end)
- **Sources:** product page https://www.raspberrypi.com/products/camera-module-3/ · mech drawing `assets/docs/rpi-camera-module-3-standard-mechanical-drawing.pdf` · official STEP `assets/rpi-camera-module-3-step.zip`
- **CAD verification (this study):** `Camera_module_3_std_model_simple.stp` measured **23.862 × 25.000 × 10.245 mm**; wide STEP 23.862 × 25.000 × 11.400 mm (STEPs omit the FPC tail; envelope uses the conservative published 11.5 mm)
- **Fit:** board minimum enclosing circle ≈34.7 mm > Ø21 mm assumed ID — **cannot lie flat inside the drum**; only across-axis orientations possible (Gate 2).

## 4. Raspberry Pi CM3 Sensor Assembly (standard lens) — candidate

- **Function:** bare RGB sensor + lens sub-assembly (remote head off the CM3 board)
- **Envelope:** 10.8 × 10.8 × 6.98 mm (product brief p.4, standard lens Ø5.75); Wide lens variant Ø6.95 × 8.3 mm deep
- **Flex tail exit geometry:** 8.9 / 7.3 / 3.3 / 4 mm (brief p.4); FOV 66° std / 102° wide (diagonal)
- **Sources:** product brief `assets/docs/rpi-camera-module-3-sensor-assembly-product-brief.pdf` · standard-NFOV datasheet `assets/docs/rpi-camera-module-3-sensor-assembly-standard-datasheet.pdf`
- **CAD:** none published
- **Fit:** fits the Ø21 mm assumed ID with large margin. This is currently the **only RGB option that fits in-drum.**

## 5. Pololu 75:1 Micro Metal Gearmotor MP 6V w/ 12 CPR encoder (item 5137) — candidate

- **Function:** DC gearmotor actuator (direct drum drive candidate)
- **Envelope (official STEP, measured):** 41.6 × 14.9 × 13.6 mm — includes Ø3 mm D-shaft (~9.5 mm) and side-entry encoder connector
- **Published dimension PDF:** gearbox cross-section 10 × 12 mm, gearbox length 9 mm, overall length max 32.5 mm **excluding** the shaft
- **Electrical:** 6 V MP brushed motor; 12 CPR magnetic quadrature encoder, JST-SH side connector
- **Sources:** product page https://www.pololu.com/product/5137 · dimension diagram `assets/docs/pololu-5137-dimensions.pdf` · official STEP zip `assets/pololu-micro-metal-gearmotor-step-models.zip` → extracted `assets/pololu-step/With Encoder, Side Connector/mmgm-pm-enc-side-con.step` (75:1 MP = `pm`, non-1000:1 gearbox, per zip README)
- **Fit:** cross-section needs a Ø20.2 mm circle → fits Ø21 mm assumed ID with ~0.4 mm radial margin; 41.6 mm length leaves 9.4 mm of the 51 mm interior for shaft support/wiring — **tight but plausible.**

## 6. T-Motor GB2208 KV128 — no-fit-reference

- **Function:** brushless gimbal motor (direct-drive candidate)
- **Envelope:** Ø27.5 × 23 mm cylinder (spec table); centre hole Ø6 mm
- **Weight:** 39.5 g (incl. 20 cm cable)
- **Electrical:** 3–4S lipo, 12N14P, 14.4 Ω, 0.07 Nm, KV128
- **Sources:** product page https://store.tmotor.com/product/gb2208-gimbal-type.html · technical drawing `assets/docs/tmotor-gb2208-drawing.jpg` (needed browser headers to download)
- **CAD:** no official STEP; a community GrabCAD model exists (third-party, **not used**)
- **Fit:** Ø27.5 mm > Ø24 mm drum shell — **cannot enter the drum.** (Would also need an external ESC + encoder.)

## 7. Robotis DYNAMIXEL XL330-M288-T — candidate-external

- **Function:** smart servo (integrated driver + 4096-step absolute magnetic encoder)
- **Envelope:** 20 × 26 × 34 mm (official drawing: depth = 23 body + 3 horn flange)
- **Drawing detail:** horn P.C.D Ø12, 4× Ø1.6 holes (M2 tapping, DP 3.0 max), horn centre 9.5 mm from top edge
- **Weight:** 18 g
- **Electrical:** 5 V, TTL bus (3.3/5 V logic), stall 0.52 Nm, no-load 104 rpm
- **Sources:** eManual https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/ · store page https://www.robotis.us/dynamixel-xl330-m288-t/ · drawing `assets/docs/robotis-xl330-m288-drawing.png`
- **CAD:** **UNRESOLVED** — official STEP/drawing links (download.php no=1985/1986/1987) 404 on both www.robotis.com and en.robotis.com; envelope is from the official drawing only
- **Fit:** smallest face (20×26) needs a Ø32.8 mm circle > Ø21 mm assumed ID — **cannot enter the drum**; external housing-mount drive only.

---

## Preliminary no-fit / fit summary (Gate 1)

| Component | Envelope (mm) | vs Ø24 drum (Ø21 assumed ID) | Status |
|---|---|---|---|
| RPi CM3 Sensor Assembly | 10.8×10.8×6.98 | fits with margin | candidate |
| Pololu 5137 gearmotor | 41.6×14.9×13.6 | cross-section Ø20.2 fits; length tight | candidate |
| RPi Camera Module 3 (board) | 25×24×11.5 | flat-face circle Ø34.7 — no flat fit | candidate-borderline |
| DYNAMIXEL XL330-M288 | 20×26×34 | min circle Ø32.8 — cannot enter | candidate-external |
| Orbbec Astra Mini Pro | 84.9×20×19.92 | exceeds shell outright | no-fit-reference |
| Orbbec Astra Embedded S | 69×22.9×15 | exceeds shell outright | no-fit-reference |
| T-Motor GB2208 | Ø27.5×23 | exceeds shell outright | no-fit-reference |

**Structured-light depth:** no commercial all-in-one SL module (Orbbec
84.9/69 mm wide) fits a Ø24 mm drum. An in-drum depth capability would
need a discrete architecture (separate IR projector + IR camera, e.g. two
CM3 sensor assemblies + projector) — flagged for Gate 2, no components
researched yet.

**Wiring across the rotating joint** (140–160° travel): unresolved —
capsule slip ring vs flex loop trade-off not yet researched (G10 group
empty).

**Bearings/supports:** not yet researched (G09 group empty).
