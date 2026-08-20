"""Component registry for the drum-internals feasibility study (Gate 1).

This module is the single machine-readable source of truth for component
envelope dimensions. Every value is copied from the manufacturer source
listed in cad/feasibility/component_sources.md. Nothing is invented.
When sources disagree, both values are recorded in `notes` and the
envelope uses the conservative (larger) value.

Status values:
  "candidate"           : plausible for in-drum packaging (Gate 2 decides)
  "candidate-external"  : cannot fit inside the drum itself; could live in
                          the main housing and drive the drum indirectly
  "candidate-borderline": fits only under specific orientations/assumptions
                          that Gate 2 must verify
  "no-fit-reference"    : exceeds even the drum shell; modelled only so the
                          comparison is visible
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

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
# dims_mm are the envelope extents (x, y, z) in the orientation documented
# in component_sources.md, unless shape == "cylinder" (diameter x length).
COMPONENTS = {
    "orbbec_astra_mini_pro": {
        "manufacturer": "Orbbec",
        "part": "Astra Mini Pro",
        "function": "structured-light depth + RGB (all-in-one)",
        "shape": "box",
        "dims_mm": (84.90, 20.00, 19.92),
        "weight_g": 34.0,
        "electrical": "USB 2.0 (DF13 5-pin), 5 V, <2.4 W (web page)",
        "cad_asset": "assets/docs/orbbec-astra-mini-pro-datasheet.pdf",
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
        "status": "candidate-borderline",
        "notes": ("Official page rounds to 25x24x11.5 mm (Wide: 12.4 mm). "
                  "Mech drawing: board 25 x 23.862, stack 11.3. Official "
                  "STEP measured: 23.862 x 25.000 x 10.245 (std) / 11.400 "
                  "(wide); STEP omits the FPC tail. Board's minimum "
                  "enclosing circle ~34.7 mm > 21 mm assumed drum ID: only "
                  "fits across the drum axis, Gate 2 must verify."),
    },
    "rpi_cm3_sensor_assembly": {
        "manufacturer": "Raspberry Pi",
        "part": "Camera Module 3 Sensor Assembly (standard lens)",
        "function": "bare RGB sensor+lens sub-assembly (remote head)",
        "shape": "box",
        "dims_mm": (10.8, 10.8, 6.98),
        "weight_g": None,
        "electrical": "CSI-2 via board-to-flex connector (see brief)",
        "cad_asset": "assets/docs/rpi-camera-module-3-sensor-assembly-product-brief.pdf",
        "status": "candidate",
        "notes": ("Product brief physical spec p.4: 10.8 x 10.8 body, std "
                  "lens dia 5.75, depth 6.98 (wide: lens dia 6.95, depth "
                  "8.3). Fits the 21 mm assumed drum ID with margin. Flex "
                  "tail exit dims 8.9 / 7.3 / 3.3 / 4 recorded in the "
                  "brief; full tail geometry TBD in Gate 2."),
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
}

# Order used for the library row layout (left to right).
LIBRARY_ORDER = [
    "rpi_cm3_sensor_assembly",
    "rpi_camera_module_3",
    "pololu_5137",
    "robotis_xl330_m288",
    "tmotor_gb2208",
    "orbbec_astra_embedded_s",
    "orbbec_astra_mini_pro",
]
