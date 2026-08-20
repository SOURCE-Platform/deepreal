"""Review presets for the feasibility document (Gate 1).

Ten non-destructive presets: each sets group visibility and a camera
view. NOTHING in the document is moved, resized, deleted, or saved by a
preset; in a headless console the preset prints what it would show.

Usage (FreeCAD GUI Python console, with drum_internals.FCStd active):
    import sys; sys.path.insert(0, "<repo>/cad/feasibility")
    import review_presets
    review_presets.apply_preset(1)
    review_presets.list_presets()
"""

PRESETS = [
    {"id": 1, "name": "Overview_All",
     "camera": "iso",
     "visible": ["G00_Exterior_Reference", "G01_Drum_Shells_Context",
                  "G04_Sensors_RGB", "G05_Sensors_Depth_StructuredLight",
                  "G06_Actuators_SmartServo", "G07_Actuators_DCGearmotor",
                  "G08_Actuators_GimbalBLDC"],
     "purpose": "Everything except assumptions/no-fit duplicates."},
    {"id": 2, "name": "Exterior_Only",
     "camera": "iso",
     "visible": ["G00_Exterior_Reference"],
     "purpose": "Approved exterior context alone."},
    {"id": 3, "name": "Drums_Context",
     "camera": "front",
     "visible": ["G00_Exterior_Reference", "G01_Drum_Shells_Context",
                  "G02_Drum_Interior_Assumed"],
     "purpose": "Drum shells + assumed interior against the housing."},
    {"id": 4, "name": "Travel_Sectors",
     "camera": "right",
     "visible": ["G01_Drum_Shells_Context", "G03_Drum_Travel_Markers"],
     "purpose": "150 deg representative travel markers from the side."},
    {"id": 5, "name": "Library_Row",
     "camera": "front",
     "visible": ["G04_Sensors_RGB", "G05_Sensors_Depth_StructuredLight",
                  "G06_Actuators_SmartServo", "G07_Actuators_DCGearmotor",
                  "G08_Actuators_GimbalBLDC"],
     "purpose": "All component envelopes side by side, true size."},
    {"id": 6, "name": "RGB_Candidates",
     "camera": "iso",
     "visible": ["G04_Sensors_RGB", "G02_Drum_Interior_Assumed"],
     "purpose": "RGB options against the assumed interior volume."},
    {"id": 7, "name": "Depth_Candidates",
     "camera": "iso",
     "visible": ["G05_Sensors_Depth_StructuredLight",
                  "G02_Drum_Interior_Assumed"],
     "purpose": "Structured-light modules against the interior volume "
                 "(the no-fit is visible at a glance)."},
    {"id": 8, "name": "Actuator_Candidates",
     "camera": "iso",
     "visible": ["G06_Actuators_SmartServo", "G07_Actuators_DCGearmotor",
                  "G08_Actuators_GimbalBLDC",
                  "G02_Drum_Interior_Assumed"],
     "purpose": "All three actuator architectures vs interior volume."},
    {"id": 9, "name": "NoFit_Reference",
     "camera": "iso",
     "visible": ["G11_NoFit_Reference", "G01_Drum_Shells_Context"],
     "purpose": "No-fit components next to the drum shell for scale."},
    {"id": 10, "name": "Empty_Placeholders",
     "camera": "iso",
     "visible": ["G09_Bearings_Supports", "G10_Wiring_Harness",
                  "G12_Review_Preset_Notes"],
     "purpose": "Shows the not-yet-researched categories (empty groups)."},
]

from groups import GROUP_DEFS

_ALL_GROUPS = [name for name, _d in GROUP_DEFS]


def list_presets():
    for p in PRESETS:
        print("%2d  %-22s %s" % (p["id"], p["name"], p["purpose"]))


def _set_camera(view, name):
    if name == "front":
        view.viewFront()
    elif name == "right":
        view.viewRight()
    elif name == "top":
        view.viewTop()
    else:
        view.viewAxonometric()
    view.fitAll()


def apply_preset(preset_id):
    preset = next(p for p in PRESETS if p["id"] == preset_id)
    try:
        import FreeCADGui as Gui
    except ImportError:
        print("headless: preset %d (%s) would show %s, camera=%s"
              % (preset["id"], preset["name"], preset["visible"],
                 preset["camera"]))
        return
    doc = Gui.ActiveDocument
    if doc is None:
        raise RuntimeError("no active GUI document")
    visible = set(preset["visible"])
    for name in _ALL_GROUPS:
        obj = doc.Document.getObject(name)
        if obj is not None:
            gui_obj = doc.getObject(name)
            gui_obj.Visibility = name in visible
    _set_camera(doc.ActiveView, preset["camera"])
    print("preset %d (%s) applied" % (preset["id"], preset["name"]))
