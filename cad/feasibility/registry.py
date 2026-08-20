"""Component registry for the drum-internals feasibility study.

Gate 1: sourced actuator / all-in-one sensor envelopes.
Gate 1.5B: discrete depth-sensing architecture components (RGB sensor
assembly, IR camera, structured-light projectors, ToF imagers) with a
formal evidence classification, plus multi-part envelope data used by the
layout studies (layouts.py).

This module is the single machine-readable source of truth for component
envelope dimensions. Every value is copied from the manufacturer source
listed in cad/feasibility/component_sources.md. Nothing is invented.
When sources disagree, both values are recorded in `notes` and the
envelope uses the conservative (larger) value.

Evidence classification (Gate 1.5B):
  "OFFICIAL-VERIFIED"      : full 3D dims from an official datasheet /
                             drawing / STEP, in hand under assets/
  "OFFICIAL-INCOMPLETE"    : official document in hand, but some envelope
                             dims are missing from it (gap named in notes)
  "ENGINEERING-ASSUMPTION" : value assumed by this study, NOT sourced;
                             always labelled, never presented as fact
  "UNRESOLVED"             : no official value obtainable (gated/404);
                             placeholder geometry is a lower bound only

Status values:
  "candidate"              : plausible for in-drum packaging (Gate 2 decides)
  "candidate-external"     : cannot fit inside the drum itself
  "candidate-borderline"   : fits only under specific orientations/assumptions
  "no-fit-reference"       : exceeds even the drum shell; modelled for
                             comparison only
  "unresolved-reference"   : official dims unobtainable; lower-bound
                             placeholder modelled
  "placeholder-assumption" : stand-in for a part class not yet selected

Multi-part envelopes (Gate 1.5B):
  Entries may carry a "parts" list. Parts are defined in a component-local
  frame: origin at the APERTURE centre on the optical-axis/front plane,
  local +Z (w) pointing INTO the component (depth), local X (u) / local
  Y (v) spanning the footprint. Each part: {"name", "shape", "dims_mm",
  "origin" (u_c, v_c, w_start), "note"}. layouts.py places these; the
  library row shows the compound. "dims_mm" on the entry remains the
  overall envelope (sorted-compare target for the validator).
"""

# ---------------------------------------------------------------------------
# Drum context (from the APPROVED model, cad/deepreal.FCStd @ main dacd90c)
# ---------------------------------------------------------------------------
# The two sensor-head barrels already exist in the approved design:
#   Face_Sensor_Head        X -56..-2  (54 mm long)
#   Interaction_Sensor_Head X   2..56  (54 mm long)
#   both: diameter 24, axis along X at Y=-1.5, Z=20
DRUM_SHELL_DIAMETER = 24.0
DRUM_SHELL_LENGTH = 54.0
DRUM_FACE_X_MIN = -56.0
DRUM_FACE_X_MAX = -2.0
DRUM_INTERACTION_X_MIN = 2.0
DRUM_INTERACTION_X_MAX = 56.0
DRUM_AXIS_Y = -1.5
DRUM_AXIS_Z = 20.0

# Required rotation travel per the study brief.
TRAVEL_MIN_DEG = 140.0
TRAVEL_MAX_DEG = 160.0
TRAVEL_MARK_DEG = 150.0   # single representative sector drawn in context

# ASSUMPTIONS (not design decisions): shell wall and end-cap thickness used
# only to draw the "assumed usable interior" context volume.
ASSUMED_WALL_MM = 1.5
ASSUMED_END_CAP_MM = 1.5
ASSUMED_INNER_DIAMETER = DRUM_SHELL_DIAMETER - 2.0 * ASSUMED_WALL_MM   # 21.0
ASSUMED_INNER_LENGTH = DRUM_SHELL_LENGTH - 2.0 * ASSUMED_END_CAP_MM    # 51.0

# Face-drum assumed-interior X span (layouts live here).
FACE_INTERIOR_X_MIN = DRUM_FACE_X_MIN + ASSUMED_END_CAP_MM   # -54.5
FACE_INTERIOR_X_MAX = DRUM_FACE_X_MAX - ASSUMED_END_CAP_MM   #  -3.5

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
# dims_mm are the envelope extents (x, y, z) in the orientation documented
# in component_sources.md, unless shape == "cylinder" (diameter x length).
COMPONENTS = {
    # ------------------------------------------------------------ Gate 1
    "orbbec_astra_mini_pro": {
        "manufacturer": "Orbbec",
        "part": "Astra Mini Pro",
        "function": "structured-light depth + RGB (all-in-one)",
        "shape": "box",
        "dims_mm": (84.90, 20.00, 19.92),
        "weight_g": 34.0,
        "electrical": "USB 2.0 (DF13 5-pin), 5 V, <2.4 W (web page)",
        "cad_asset": "assets/docs/orbbec-astra-mini-pro-datasheet.pdf",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "no-fit-reference",
        "notes": ("Datasheet v1.0 says 34 g and 855 nm; web page says 35 g "
                  "and 850 nm. 84.9 mm width vs 24 mm drum shell: cannot "
                  "enter the drum. No official STEP obtained."),
    },
    "orbbec_astra_embedded_s": {
        "manufacturer": "Orbbec",
        "part": "Astra Embedded S",
        "function": "structured-light depth + RGB (all-in-one)",
        "shape": "box",
        "dims_mm": (69.0, 22.9, 15.0),
        "weight_g": 27.0,
        "electrical": "USB 3.0 Type-C, <2.2 W (web page)",
        "cad_asset": None,
        "evidence": "OFFICIAL-INCOMPLETE",
        "status": "no-fit-reference",
        "notes": ("Product-page dims only; no datasheet/CAD downloaded. "
                  "69 mm width vs 24 mm drum shell: cannot enter the drum."),
    },
    "rpi_camera_module_3": {
        "manufacturer": "Raspberry Pi",
        "part": "Camera Module 3 (standard)",
        "function": "RGB camera (IMX708, 11.9 MP, CSI-2)",
        "shape": "box",
        "dims_mm": (25.0, 24.0, 11.5),
        "weight_g": None,
        "electrical": "CSI-2, 15x1 mm FPC",
        "cad_asset": "assets/rpi-camera-module-3-step.zip "
                     "(Camera_module_3_std_model_simple.stp)",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "candidate-borderline",
        "notes": ("Official page rounds to 25x24x11.5 mm (Wide: 12.4 mm). "
                  "Mech drawing: board 25 x 23.862, stack 11.3. Official "
                  "STEP measured: 23.862 x 25.000 x 10.245 (std) / 11.400 "
                  "(wide); STEP omits the FPC tail. Board's minimum "
                  "enclosing circle ~34.7 mm > 21 mm assumed drum ID: only "
                  "fits across the drum axis, Gate 2 must verify."),
    },
    "pololu_5137": {
        "manufacturer": "Pololu",
        "part": "75:1 Micro Metal Gearmotor MP 6V with 12 CPR encoder, "
                "side connector (item 5137)",
        "function": "DC gearmotor actuator (direct drum drive candidate)",
        "shape": "box",
        "dims_mm": (41.6, 14.9, 13.6),
        "weight_g": None,
        "electrical": "6 V MP motor + 12 CPR magnetic encoder (JST SH side)",
        "cad_asset": "assets/pololu-step/With Encoder, Side Connector/"
                     "mmgm-pm-enc-side-con.step",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "candidate",
        "notes": ("Envelope measured from the OFFICIAL STEP (includes the "
                  "~9.5 mm D-shaft and the side-entry encoder connector). "
                  "Published dimension PDF: gearbox 10x12 mm, length 9 mm, "
                  "overall length max 32.5 mm EXCLUDING the dia 3 mm "
                  "D-shaft. Cross-section needs a ~20.2 mm circle: fits the "
                  "21 mm assumed drum ID with ~0.4 mm radial margin."),
    },
    "tmotor_gb2208": {
        "manufacturer": "T-Motor",
        "part": "GB2208 KV128 gimbal motor",
        "function": "brushless gimbal motor (direct-drive candidate)",
        "shape": "cylinder",
        "dims_mm": (27.5, 23.0),   # diameter, length
        "weight_g": 39.5,
        "electrical": "3-4S lipo, 12N14P, 14.4 ohm, 0.07 Nm, 20 cm cable",
        "cad_asset": "assets/docs/tmotor-gb2208-drawing.jpg",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "no-fit-reference",
        "notes": ("Spec table: dia 27.5 x 23 mm, centre hole dia 6 mm. "
                  "27.5 mm diameter exceeds the 24 mm drum shell: cannot "
                  "enter the drum. Technical drawing JPG saved; no official "
                  "STEP (a community GrabCAD model exists, not used)."),
    },
    "robotis_xl330_m288": {
        "manufacturer": "Robotis",
        "part": "DYNAMIXEL XL330-M288-T",
        "function": "smart servo actuator (integrated controller + "
                    "absolute encoder)",
        "shape": "box",
        "dims_mm": (20.0, 26.0, 34.0),
        "weight_g": 18.0,
        "electrical": "5 V, TTL (3.3/5 V logic), stall 0.52 Nm, "
                      "4096-step absolute encoder",
        "cad_asset": "assets/docs/robotis-xl330-m288-drawing.png",
        "evidence": "OFFICIAL-INCOMPLETE",
        "status": "candidate-external",
        "notes": ("Official dimension drawing (robotis.us): 20 x 34 front, "
                  "depth 23 body + 3 horn flange = 26; horn PCD dia 12, "
                  "4x dia 1.6 holes, horn centre 9.5 mm from top edge. "
                  "Smallest face needs a 32.8 mm circle > 21 mm assumed "
                  "drum ID: cannot enter the drum; external-mount drive "
                  "only. Official STEP links (download.php no=1985/1986/"
                  "1987) return 404 on both www.robotis.com and "
                  "en.robotis.com: CAD UNRESOLVED."),
    },
    # ---------------------------------------------------- Gate 1.5B: RGB
    "rpi_cm3_sensor_assembly": {
        "manufacturer": "Raspberry Pi",
        "part": "Camera Module 3 Sensor Assembly (standard lens)",
        "function": "bare RGB sensor+lens sub-assembly (remote head; "
                    "replaces the full CM3 board as the in-drum RGB option)",
        "shape": "multipart",
        "dims_mm": (10.8, 10.8, 6.98),
        "weight_g": None,
        "electrical": ("CSI-2 (2-lane MIPI per TNBA1392 pinout) via 30-pin "
                       "board-to-flex connector HLM-033M-3002-76; DVDD 1.1 V "
                       "/ AVDD 2.8 V / DOVDD 1.8 V; VCM driver DW9800W; "
                       "EEPROM BL24SA64D-CS"),
        "cad_asset": "assets/docs/rpi-camera-module-3-sensor-assembly-"
                     "product-brief.pdf; assets/docs/rpi-camera-module-3-"
                     "sensor-assembly-standard-datasheet.pdf (TNBA1392 REV 0)",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "candidate",
        "aperture": {"shape": "circle", "diameter_mm": 5.75,
                     "note": "lens front face"},
        "parts": [
            {"name": "lens", "shape": "cylinder", "dims_mm": (5.75, 2.505),
             "origin": (0.0, 0.0, 0.0),
             "note": ("lens barrel protrusion above body top: 6.98 total - "
                      "0.45 PCB - 4.025 body+glue = 2.505; lens dia 5.75 "
                      "(brief p.4 + TNBA1392 top view)")},
            {"name": "body", "shape": "box", "dims_mm": (10.8, 10.8, 4.025),
             "origin": (0.0, 0.0, 2.505),
             "note": ("body 3.875 +/-0.15 (TNBA1392 side view) + 0.15 AA "
                      "glue; footprint 10.8x10.8 key-dim CPK>=1.33")},
            {"name": "pcb", "shape": "box", "dims_mm": (10.8, 10.8, 0.45),
             "origin": (0.0, 0.0, 6.530),
             "note": ("0.4 +/-0.05 PCB (TNBA1392) + ink, conservative "
                      "0.45; total stack 6.98 matches brief p.4")},
            {"name": "fpc_tail", "shape": "box",
             "dims_mm": (8.9, 4.0, 0.45),
             "origin": (0.0, -7.4, 6.530),
             "note": ("FPC exit keepout: tail 8.9 +/-0.15 wide, 4.0 +/-0.15 "
                      "visible beyond body edge, bend area 7 +/-0.15 wide; "
                      "bends 180 deg at R=0.8 mm (TNBA1392 technical "
                      "requirement 3); exits to local -v at the back "
                      "plane")},
        ],
        "notes": ("Footprint 10.8x10.8 +/-0.15 (TNBA1392 key dims, "
                  "CPK>=1.33). DEPTH DISCREPANCY recorded: brief p.4 says "
                  "6.98 mm (std) / 8.3 (wide); TNBA1392 side view says "
                  "6.21 +/-0.15 at 10 cm focus and 5.97 +/-0.15 at infinity "
                  "(AF moves the lens; body itself 3.875 +/-0.15, matching "
                  "the brief's 3.875). Envelope uses the conservative "
                  "brief value 6.98. Optics: EFL 4.74 mm F1.79 (brief "
                  "rounds F1.8), FOV 75 deg +/-3 diagonal / 66 H / 41 V, "
                  "image circle dia 8.4 mm, focus 10 cm-inf, sensor "
                  "IMX708-AAJH5-C (CRA 35.3 deg). Fits the 21 mm assumed "
                  "drum ID with margin. FPC connector at far end of tail "
                  "not modelled (HLM-033M-3002-76, 30-pin)."),
    },
    # ------------------------------------------- Gate 1.5B: SL IR camera
    "ov9281_ir_camera": {
        "manufacturer": "OmniVision",
        "part": "OV9281 (OV09281-H64A, b&w, 64-pin CSP)",
        "function": "global-shutter NIR camera die for structured-light "
                    "depth (bare sensor; needs lens + carrier PCB)",
        "shape": "multipart",
        "dims_mm": (6.0, 6.0, 5.5),
        "weight_g": None,
        "electrical": ("analog 2.8 V / core 1.2 V / I/O 1.8 V; active "
                       "156 mW; 2-lane MIPI + DVP; SCCB"),
        "cad_asset": "assets/docs/omnivision-ov9281-product-brief.pdf",
        "evidence": "OFFICIAL-INCOMPLETE",
        "status": "candidate",
        "aperture": {"shape": "circle", "diameter_mm": 6.0,
                     "note": ("lens allowance outline (assumption); the die "
                              "itself has no aperture")},
        "parts": [
            {"name": "lens_allowance", "shape": "cylinder",
             "dims_mm": (6.0, 4.0), "origin": (0.0, 0.0, 0.0),
             "note": ("ENGINEERING-ASSUMPTION: compact board-lens class "
                      "barrel (dia 6 x 4 mm). The brief specifies only "
                      "CRA 9 deg linear + 1/4 in lens size; no lens is "
                      "sourced. Gate 2 must select a real NIR lens.")},
            {"name": "die", "shape": "box",
             "dims_mm": (3.896, 2.453, 1.5), "origin": (0.0, 0.0, 4.0),
             "note": ("footprint = OFFICIAL image area 3896 x 2453 um "
                      "(brief, product features); THICKNESS 1.5 mm is an "
                      "ENGINEERING-ASSUMPTION (CSP die + margins): the "
                      "64-pin CSP package outline is NOT in the product "
                      "brief (full datasheet is NDA-gated): package X/Y/Z "
                      "UNRESOLVED.")},
        ],
        "notes": ("OFFICIAL (brief v1.4, May 2024): 1280x800 @ 120 fps "
                  "max, global shutter (OmniPixel3-GS, 3 um pixel), image "
                  "area 3896 x 2453 um, CRA 9 deg linear, 1/4 in optical "
                  "format, 2-lane MIPI + DVP, 8/10-bit RAW, -30..+85 C "
                  "operating, 64-pin CSP (ordering code OV09281-H64A). "
                  "Package body dims UNRESOLVED from available documents. "
                  "The earlier 8x8x5.8 mm module-class claim is DEMOTED "
                  "(unsourced; see component_sources.md). Arducam "
                  "24x25 mm module ruled out: board circle dia 34.7 mm > "
                  "21 mm assumed drum ID."),
    },
    # -------------------------------------------- Gate 1.5B: SL projectors
    "ams_belice_850": {
        "manufacturer": "ams OSRAM",
        "part": "BELICE-850 (DS000618 v2-00)",
        "function": "850 nm dot-projector VCSEL module for structured "
                    "light (~10k dots per emitter pair)",
        "shape": "box",
        "dims_mm": (3.50, 3.40, 3.56),
        "weight_g": None,
        "electrical": ("VCSEL array, pads on 2.80 x 2.80 mm bottom field "
                       "(datasheet fig. 12); drive per datasheet"),
        "cad_asset": "assets/docs/ams-belice-850-datasheet.pdf",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "candidate",
        "aperture": {"shape": "box", "dims_mm": (2.3, 2.3),
                     "note": "optical aperture 2.3x2.3, corner R0.1 (fig. 13)"},
        "notes": ("Datasheet DS000618 v2-00 (2019-May-15): top view "
                  "3.50 +/-0.15 x 3.40 +/-0.15; side view HEIGHT "
                  "3.56 +/-0.1 with a 0.25 mm step feature; bottom pad "
                  "field 2.80 +/-0.1 x 2.80 +/-0.1 (pads 0.50/2.05/0.25/"
                  "0.30 +/-0.1); fiducials 2x dia 0.20; corner radii "
                  "4x R0.70; optical aperture 2.3x2.3 R0.1. SMT module, "
                  "needs carrier PCB + driver (not included)."),
    },
    "ams_belago1_2": {
        "manufacturer": "ams OSRAM",
        "part": "Belago1.2 (DS001002 v1-00, ordering AQAA-30 / Q65114A0198)",
        "function": "940 nm pseudo-random dot projector, ~15k dots, with "
                    "resistive-ITO eye-safety interlock",
        "shape": "box",
        "dims_mm": (4.200, 3.900, 3.325),
        "weight_g": None,
        "electrical": ("Anode(+)/Cathode/Sense1/Sense2 pads (datasheet "
                       "fig. 6 bottom view); ~0.7 A pulse class (fig. 4: "
                       "Ti=1 ms, 30 fps); MSL3, peak reflow 250 C"),
        "cad_asset": "assets/docs/ams-belago1-2-datasheet.pdf",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "candidate",
        "aperture": {"shape": "box", "dims_mm": (2.0, 2.0),
                     "note": ("MLA active area 2.0 +/-0.1 square; aperture "
                              "corners 4x R0.750 (fig. 6)")},
        "notes": ("Datasheet DS001002 v1-00 (2025-Apr-22): top view "
                  "4.200 +/-0.075 x 3.900 +/-0.050; front view HEIGHT "
                  "3.325 +/-0.050; MLA active area 2 +/-0.100; corner "
                  "radii 4x R0.750; pads 0.550/0.950/2.050/0.250 +/-0.100 "
                  "etc. Pin-compatible with Belago1.1. Eye-safety "
                  "interlock: fracture of the resistive ITO layer opens "
                  "Sense1/Sense2 -> driver must cut power (hotspot "
                  "protection, every emitter inspected in production). "
                  "Module contains a ventilation hole; must NOT be "
                  "ultrasonically cleaned."),
    },
    # --------------------------------------------------- Gate 1.5B: ToF
    "infineon_irs2877a": {
        "manufacturer": "Infineon",
        "part": "IRS2877A / IRS2877AS (REAL3 ToF imager, PG-LFBGA-65-1)",
        "function": "indirect-ToF depth imager die, 640x480 (~307k px, "
                    "upscaled), 940 nm, integrated eye-safety logic",
        "shape": "multipart",
        "dims_mm": (9.0, 9.0, 5.465),
        "weight_g": None,
        "electrical": ("1.8 V / 3.3 V rails (brief); companion imager-"
                       "controller IRS9103A required; illumination VCSEL + "
                       "driver NOT included"),
        "cad_asset": "assets/docs/infineon-irs2877as-product-brief.pdf; "
                     "assets/docs/infineon-pg-lfbga-65-1-package-outline.pdf; "
                     "assets/step/infineon-pg-lfbga-65-1-3d.stp",
        "evidence": "OFFICIAL-VERIFIED",
        "status": "candidate",
        "aperture": {"shape": "circle", "diameter_mm": 6.0,
                     "note": ("lens allowance outline (assumption); die "
                              "itself: sensor/lens area 4.6x4.9 mm")},
        "parts": [
            {"name": "lens_allowance", "shape": "cylinder",
             "dims_mm": (6.0, 4.0), "origin": (0.0, 0.0, 0.0),
             "note": ("ENGINEERING-ASSUMPTION: compact lens barrel "
                      "(dia 6 x 4 mm) for the 4 mm image circle; no lens "
                      "sourced. Gate 2 must select a real 940 nm lens.")},
            {"name": "sensor_bga", "shape": "box",
             "dims_mm": (9.0, 9.0, 1.465), "origin": (0.0, 0.0, 4.0),
             "note": ("OFFICIAL: PG-LFBGA-65-1 body 9.0 +/-0.1 x 9.0 "
                      "+/-0.1, height 1.325 +/-0.14 (max 1.465); ball "
                      "dia 0.42, pitch 0.8, 65 balls, standoff min 0.25; "
                      "sensor/lens area 4.6 +/-0.05 x 4.9 +/-0.05 with "
                      "centre offset. OFFICIAL STEP probed by this study: "
                      "union bounds 9.000 x 9.000 x 1.465 = outline max.")},
        ],
        "notes": ("Product brief: 640x480 (~307k px, upscaled output), "
                  "940 nm operation, 4 mm image circle (1/4 in class), "
                  "AEC-Q100 grade 2; IRS2877AS adds ISO 26262 (ASIL-D). "
                  "Companion chip IRS9103A mandatory; an illumination "
                  "VCSEL + its driver + receiving lens + host interface "
                  "complete the camera: FULL-STACK RESERVATION - the "
                  "envelope here is the imager die + lens allowance only; "
                  "a working ToF camera adds illuminator, controller, "
                  "passives and PCB (see ToF-A layout keepouts)."),
    },
    "infineon_irs2976c": {
        "manufacturer": "Infineon",
        "part": "IRS2976C (REAL3 ToF imager, bare die)",
        "function": "indirect-ToF depth imager die, 640x480, 940 nm "
                    "(higher-voltage companion IRS9102C)",
        "shape": "cylinder",
        "dims_mm": (4.0, 0.5),   # dia = official 4 mm image circle; thin disc
        "weight_g": None,
        "electrical": "companion IRS9102C required; illumination separate",
        "cad_asset": "assets/docs/infineon-irs2877as-product-brief.pdf "
                     "(family reference only)",
        "evidence": "UNRESOLVED",
        "status": "unresolved-reference",
        "notes": ("Bare-die product: die dimensions are behind the "
                  "MyInfineon portal (gated) - UNRESOLVED, not obtained. "
                  "Modelled geometry is a dia 4.0 mm x 0.5 mm disc = the "
                  "OFFICIAL 4 mm image circle (1/4 in class) as a "
                  "LOWER-BOUND footprint only; a real die + wire-bond/"
                  "WLO stack is larger. Not carried into the layouts: "
                  "kept as a reference row. Same full-stack reservations "
                  "as IRS2877A apply, plus die-level handling/COB "
                  "packaging would be an in-house burden."),
    },
    "tof_illuminator_placeholder": {
        "manufacturer": "unselected (placeholder class: ams OSRAM flood "
                        "VCSEL, BELICE/TARA class)",
        "part": "ToF flood-illumination placeholder (940 nm class)",
        "function": "flood IR illuminator stand-in for the ToF-A layout",
        "shape": "box",
        "dims_mm": (3.50, 3.40, 3.56),
        "weight_g": None,
        "electrical": "VCSEL + driver (unselected)",
        "cad_asset": None,
        "evidence": "ENGINEERING-ASSUMPTION",
        "status": "placeholder-assumption",
        "notes": ("ENGINEERING-ASSUMPTION: no 940 nm flood illuminator has "
                  "been selected. Envelope borrows the BELICE-850 package "
                  "dims (3.50 x 3.40 x 3.56, OFFICIAL for BELICE-850) as "
                  "a representative of the SMT VCSEL module class. Gate 2 "
                  "must select a real illuminator (e.g. ams TARA2000-AUT "
                  "class) and re-check."),
    },
}

# Order used for the library row layout (left to right).
LIBRARY_ORDER = [
    "rpi_cm3_sensor_assembly",
    "ov9281_ir_camera",
    "ams_belice_850",
    "ams_belago1_2",
    "infineon_irs2877a",
    "infineon_irs2976c",
    "tof_illuminator_placeholder",
    "rpi_camera_module_3",
    "pololu_5137",
    "robotis_xl330_m288",
    "tmotor_gb2208",
    "orbbec_astra_embedded_s",
    "orbbec_astra_mini_pro",
]
