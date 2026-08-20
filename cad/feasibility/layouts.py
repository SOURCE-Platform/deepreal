"""In-drum layout studies (Gate 1.5B): SL-A, SL-B, ToF-A.

All layouts live inside the CURRENT Face drum: shell dia 24 x 54 mm,
assumed usable interior dia 21 x 51 mm (X -54.5 .. -3.5), axis along X at
Y=-1.5 / Z=20 (registry.py). No drum enlargement, no exterior change.

Component orientation: optical axes are RADIAL, pointing at the
user-facing (-Y) rest direction; component local +Z (depth from the
aperture plane, see registry.py) maps to drum +Y (inward), local X (u)
maps to drum +X, local Y (v) maps to drum -Z. "r_ap" is the radial
position of the aperture plane from the drum axis: 9.5 mm = flush
(1.0 mm clear of the assumed 10.5 mm interior radius); smaller values
are recessed (window/vignetting reservation, recorded per layout).

Geometry transforms are BAKED into the shapes (Placement left identity)
so BoundBox and boolean checks in validate_feasibility.py operate in
global coordinates directly.
"""

import FreeCAD as App
import Part

import registry
from envelopes import make_part_shape

# Assumed-interior radius / aperture placement constants.
R_INTERIOR = registry.ASSUMED_INNER_DIAMETER / 2.0          # 10.5
APERTURE_WALL_CLEARANCE = 1.0                                # mm
R_AP_FLUSH = R_INTERIOR - APERTURE_WALL_CLEARANCE            # 9.5
R_AP_RECESSED = R_INTERIOR - 2.0                             # 8.5 (SL-B st-2)

X_MIN = registry.FACE_INTERIOR_X_MIN   # -54.5
X_MAX = registry.FACE_INTERIOR_X_MAX   #  -3.5
AXIS_Y = registry.DRUM_AXIS_Y
AXIS_Z = registry.DRUM_AXIS_Z

# ---------------------------------------------------------------------------
# Layout definitions
# ---------------------------------------------------------------------------
LAYOUTS = {
    "SL-A": {
        "title": "Structured-light A: pure axial line",
        "description": (
            "RGB (CM3 Sensor Assembly) -> IR camera (OV9281 bare sensor "
            "+ lens allowance) -> dot projector (BELICE-850), in one row "
            "along the drum axis; all apertures flush at the user-facing "
            "wall plane (r = 9.5 mm). Simplest window, longest X span."),
        "projector": "ams_belice_850",
        "placements": [
            {"component": "rpi_cm3_sensor_assembly",
             "x_c": -47.10, "z_c": 20.0, "r_ap": R_AP_FLUSH},
            {"component": "ov9281_ir_camera",
             "x_c": -36.70, "z_c": 20.0, "r_ap": R_AP_FLUSH},
            {"component": "ams_belice_850",
             "x_c": -29.95, "z_c": 20.0, "r_ap": R_AP_FLUSH},
        ],
        "keepouts": [
            {"name": "carrier_pcb", "kind": "box",
             "min": (-53.5, -3.9, 16.0), "max": (-27.2, -2.9, 24.0),
             "note": ("ENGINEERING-ASSUMPTION: stationary carrier PCB + "
                      "passives strip (26.3 x 1.0 x 8.0 mm) behind the "
                      "deepest component back plane; no board is "
                      "designed yet.")},
        ],
        "notes": [
            "All apertures coplanar (r = 9.5): single flat window band.",
            "CM3 SA FPC tail exits tangentially (+Z) at the back plane; "
            "180 deg bend at R=0.8 per TNBA1392 must route along the "
            "carrier PCB (Gate 2 routing).",
            "OV9281 lens is an allowance, not a sourced part.",
            "BELICE-850 needs a carrier + VCSEL driver on the PCB strip.",
        ],
    },
    "SL-B": {
        "title": "Structured-light B: mixed axial / cross-section",
        "description": (
            "RGB (CM3 SA) axial at station 1; IR camera (OV9281) and dot "
            "projector (Belago1.2, 940 nm) SHARE station 2, split "
            "tangentially (+/-Z offsets) with apertures recessed to "
            "r = 8.5 mm. Shortens the X span at the cost of a recessed "
            "window and a tighter Z stack."),
        "projector": "ams_belago1_2",
        "placements": [
            {"component": "rpi_cm3_sensor_assembly",
             "x_c": -47.10, "z_c": 20.0, "r_ap": R_AP_FLUSH},
            {"component": "ov9281_ir_camera",
             "x_c": -36.70, "z_c": 22.7, "r_ap": R_AP_RECESSED},
            {"component": "ams_belago1_2",
             "x_c": -36.70, "z_c": 17.3, "r_ap": R_AP_RECESSED},
        ],
        "keepouts": [
            {"name": "carrier_pcb", "kind": "box",
             "min": (-53.5, -3.9, 16.0), "max": (-32.7, -2.9, 24.0),
             "note": ("ENGINEERING-ASSUMPTION: stationary carrier PCB + "
                      "passives strip (20.8 x 1.0 x 8.0 mm).")},
        ],
        "notes": [
            "Station-2 apertures recessed 2.0 mm from the interior wall: "
            "the drum window must be oversized and vignetting checked "
            "(Gate 2 reservation).",
            "Z gap between OV9281 lens allowance and Belago1.2 body at "
            "station 2 is ~0.45 mm: assembly tolerance risk, flagged.",
            "Belago1.2 Sense1/Sense2 eye-safety interlock pins must "
            "reach the driver (datasheet requirement).",
            "OV9281 lens is an allowance, not a sourced part.",
        ],
    },
    "ToF-A": {
        "title": "Time-of-flight A: IRS2877A camera + flood illuminator",
        "description": (
            "Infineon IRS2877A(S) ToF imager (PG-LFBGA-65-1, 9.0 x 9.0 x "
            "1.465 mm STEP-verified) + lens allowance, axial with a "
            "940 nm flood-VCSEL PLACEHOLDER and a carrier-PCB keep-out "
            "(companion IRS9103A + passives live in the keep-out). "
            "Honest full-stack reservations: illuminator unselected, "
            "companion/controller/passives not dimensioned."),
        "projector": None,
        "placements": [
            {"component": "infineon_irs2877a",
             "x_c": -48.00, "z_c": 20.0, "r_ap": R_AP_FLUSH},
            {"component": "tof_illuminator_placeholder",
             "x_c": -39.75, "z_c": 20.0, "r_ap": R_AP_FLUSH},
        ],
        "keepouts": [
            {"name": "carrier_pcb", "kind": "box",
             "min": (-53.5, -5.3, 15.5), "max": (-37.0, -3.8, 24.5),
             "note": ("ENGINEERING-ASSUMPTION: carrier PCB + companion "
                      "IRS9103A + VCSEL driver + passives keep-out "
                      "(16.5 x 1.5 x 9.0 mm). Full ToF stack: imager + "
                      "lens + illuminator + companion + passives + host "
                      "interface; only the imager is OFFICIAL-VERIFIED.")},
        ],
        "notes": [
            "IRS2877A die envelope is official (package outline + STEP); "
            "the 4 mm lens allowance is an assumption.",
            "Illuminator is a BELICE-class placeholder: a real 940 nm "
            "flood VCSEL (e.g. TARA2000-AUT class) must be selected.",
            "Eye-safety: IRS2877A family integrates eye-safety logic but "
            "the illuminator drive must implement it (Gate 2).",
            "IRS2976C (bare die) deliberately NOT laid out: die dims "
            "UNRESOLVED (MyInfineon-gated).",
        ],
    },
}


def _place_part(component_key, part, x_c, z_c, r_ap):
    """Registry part shape transformed into drum-global coordinates."""
    sh = make_part_shape(part)
    # local +Z (depth) -> drum +Y (inward); local +Y (v) -> drum -Z.
    sh.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90.0)
    sh.translate(App.Vector(x_c, AXIS_Y - r_ap, z_c))
    return sh


def build(doc):
    """Create LA_/AP_/KO_ objects for every layout. Returns {layout: objs}."""
    created = {}
    for lname, ldef in LAYOUTS.items():
        objs = []
        ltag = lname.replace("-", "")
        for pl in ldef["placements"]:
            ckey = pl["component"]
            entry = registry.COMPONENTS[ckey]
            parts = (entry["parts"] if entry["shape"] == "multipart"
                     else [{"name": "body", "shape": entry["shape"],
                            "dims_mm": entry["dims_mm"],
                            "origin": (0.0, 0.0, 0.0),
                            "note": "single-part envelope"}])
            for part in parts:
                feat = doc.addObject(
                    "Part::Feature",
                    "LA_%s_%s_%s" % (ltag, ckey, part["name"]))
                feat.Shape = _place_part(ckey, part, pl["x_c"], pl["z_c"],
                                         pl["r_ap"])
                feat.addProperty("App::PropertyString", "Layout",
                                 "Feasibility").Layout = lname
                feat.addProperty("App::PropertyString", "Component",
                                 "Feasibility").Component = ckey
                feat.addProperty("App::PropertyString", "PartName",
                                 "Feasibility").PartName = part["name"]
                feat.addProperty("App::PropertyString", "Evidence",
                                 "Feasibility").Evidence = entry["evidence"]
                feat.addProperty("App::PropertyString", "PartNote",
                                 "Feasibility").PartNote = part["note"]
                feat.addProperty("App::PropertyFloat", "ApertureRadiusMm",
                                 "Feasibility").ApertureRadiusMm = pl["r_ap"]
                objs.append(feat)
            # Aperture marker at the component's aperture plane.
            ap = entry.get("aperture")
            if ap is not None:
                mk = doc.addObject("Part::Feature",
                                   "AP_%s_%s" % (ltag, ckey))
                y0 = AXIS_Y - pl["r_ap"]
                if ap["shape"] == "circle":
                    r = ap["diameter_mm"] / 2.0
                    mk.Shape = Part.makeCylinder(
                        r, 0.3, App.Vector(pl["x_c"], y0, pl["z_c"]),
                        App.Vector(0, -1, 0))
                else:
                    ax, az = ap["dims_mm"]
                    mk.Shape = Part.makeBox(
                        ax, 0.3, az,
                        App.Vector(pl["x_c"] - ax / 2.0, y0 - 0.3,
                                   pl["z_c"] - az / 2.0))
                mk.addProperty("App::PropertyString", "Layout",
                               "Feasibility").Layout = lname
                mk.addProperty("App::PropertyString", "Component",
                               "Feasibility").Component = ckey
                mk.addProperty("App::PropertyString", "ApertureNote",
                               "Feasibility").ApertureNote = ap["note"]
                objs.append(mk)
        for ko in ldef.get("keepouts", []):
            lo, hi = ko["min"], ko["max"]
            feat = doc.addObject("Part::Feature",
                                 "KO_%s_%s" % (ltag, ko["name"]))
            feat.Shape = Part.makeBox(
                hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2],
                App.Vector(*lo))
            feat.addProperty("App::PropertyString", "Layout",
                             "Feasibility").Layout = lname
            feat.addProperty("App::PropertyString", "KeepoutNote",
                             "Feasibility").KeepoutNote = ko["note"]
            feat.addProperty("App::PropertyString", "Evidence",
                             "Feasibility").Evidence = \
                "ENGINEERING-ASSUMPTION"
            objs.append(feat)
        created[lname] = objs
    return created
