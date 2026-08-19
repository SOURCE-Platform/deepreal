#!/usr/bin/env python3
"""
Phase 1 + Phase 2 validation.

Rebuilds the geometry in memory with perturbed parameters and checks that
the resulting bounding boxes respond correctly, then reopens the saved
deepreal.FCStd and verifies its structure and injected view state.

Coordinate convention under test: -Y = FRONT/USER side (screen/pixels,
seated user, sensor heads); +Y = REAR/MOUNT side (back of lid; future arm
and magnetic mount).

Run headless from the repository root (after cad/build.py):

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cad/validate.py

Exits non-zero if any check fails.

Note: freecadcmd executes this file with __name__ set to the module name,
not "__main__", so main() is invoked unconditionally at import time. Do not
import this module.
"""

import importlib
import os
import shutil
import sys
import tempfile
import time
import zipfile

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
    if not os.path.exists(os.path.join(HERE, "parameters.py")):
        HERE = os.path.join(HERE, "cad")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402

import document  # noqa: E402
import parameters  # noqa: E402
import parts  # noqa: E402
import sensor_heads  # noqa: E402

FAILURES = []

HOUSING = parts.MAIN_HOUSING_NAME
DISPLAY = parts.DISPLAY_REFERENCE_NAME
FACE = sensor_heads.FACE_HEAD_NAME
INTERACTION = sensor_heads.INTERACTION_HEAD_NAME
FACE_MARK = sensor_heads.FACE_ORIENTATION_NAME
INTERACTION_MARK = sensor_heads.INTERACTION_ORIENTATION_NAME


def check(label, actual, expected, tol=1e-6):
    ok = abs(actual - expected) <= tol
    print("[{}] {}: expected {}, got {}".format(
        "PASS" if ok else "FAIL", label, expected, actual))
    if not ok:
        FAILURES.append(label)


def check_true(label, condition):
    print("[{}] {}".format("PASS" if condition else "FAIL", label))
    if not condition:
        FAILURES.append(label)


def extents(obj):
    bb = obj.Shape.BoundBox
    return bb.XLength, bb.YLength, bb.ZLength


def axis_center_y(obj):
    bb = obj.Shape.BoundBox
    return (bb.YMin + bb.YMax) / 2.0


def axis_center_z(obj):
    bb = obj.Shape.BoundBox
    return (bb.ZMin + bb.ZMax) / 2.0


def build_with(**overrides):
    params = parameters.get_params()
    params.update(overrides)
    doc = document.build_document(params)
    objects = {obj.Name: obj for obj in doc.Objects}
    return doc, objects


def cylinder_axis_along_x(obj):
    """True if the solid has a cylindrical face whose axis is parallel to X."""
    x_axis = App.Vector(1, 0, 0)
    for face in obj.Shape.Faces:
        surface = face.Surface
        if surface.TypeId == "Part::GeomCylinder":
            if abs(abs(surface.Axis * x_axis) - 1.0) < 1e-9:
                return True
    return False


def main():
    base = parameters.resolve(parameters.get_params())

    print("--- Phase 1 regression: baseline dimensions ---")
    doc, o = build_with()
    check("housing width == MAIN_BODY_WIDTH",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])
    check("housing depth == MAIN_BODY_DEPTH",
          extents(o[HOUSING])[1], base["MAIN_BODY_DEPTH"])
    check("housing height == MAIN_BODY_HEIGHT",
          extents(o[HOUSING])[2], base["MAIN_BODY_HEIGHT"])
    check("display thickness == DISPLAY_LID_THICKNESS",
          extents(o[DISPLAY])[1], base["DISPLAY_LID_THICKNESS"])
    check("housing bottom flush with display top edge (Z=0)",
          o[HOUSING].Shape.BoundBox.ZMin, base["MAIN_BODY_DISPLAY_OFFSET_Z"])
    check("display top edge at Z=0", o[DISPLAY].Shape.BoundBox.ZMax, 0.0)

    print("--- Phase 1 regression: MAIN_BODY_WIDTH regenerates ---")
    _, o = build_with(MAIN_BODY_WIDTH=base["MAIN_BODY_WIDTH"] + 20.0)
    check("housing width follows MAIN_BODY_WIDTH",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"] + 20.0)
    check("display width unaffected",
          extents(o[DISPLAY])[0], base["DISPLAY_REFERENCE_WIDTH"])

    print("--- Phase 1 regression: MAIN_BODY_HEIGHT regenerates ---")
    _, o = build_with(MAIN_BODY_HEIGHT=base["MAIN_BODY_HEIGHT"] + 10.0)
    check("housing height follows MAIN_BODY_HEIGHT",
          extents(o[HOUSING])[2], base["MAIN_BODY_HEIGHT"] + 10.0)

    print("--- Phase 1 regression: MAIN_BODY_DEPTH regenerates ---")
    _, o = build_with(MAIN_BODY_DEPTH=base["MAIN_BODY_DEPTH"] + 3.0)
    check("housing depth follows MAIN_BODY_DEPTH",
          extents(o[HOUSING])[1], base["MAIN_BODY_DEPTH"] + 3.0)

    print("--- Phase 1 regression: DISPLAY_LID_THICKNESS touches only the reference ---")
    _, o = build_with(DISPLAY_LID_THICKNESS=base["DISPLAY_LID_THICKNESS"] + 2.0)
    check("display thickness follows DISPLAY_LID_THICKNESS",
          extents(o[DISPLAY])[1], base["DISPLAY_LID_THICKNESS"] + 2.0)
    check("housing depth unaffected by DISPLAY_LID_THICKNESS",
          extents(o[HOUSING])[1], base["MAIN_BODY_DEPTH"])
    check("housing width unaffected by DISPLAY_LID_THICKNESS",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])

    print("--- Phase 2: sensor-head geometry (user side = -Y) ---")
    doc, o = build_with()
    front_face_y = (base["MAIN_BODY_DISPLAY_OFFSET_Y"]
                    - base["MAIN_BODY_DEPTH"] / 2.0)
    rear_face_y = (base["MAIN_BODY_DISPLAY_OFFSET_Y"]
                   + base["MAIN_BODY_DEPTH"] / 2.0)
    check_true("face and interaction heads are distinct objects",
               o[FACE] is not o[INTERACTION])
    check_true("face head is separate from Main_Housing",
               o[FACE] is not o[HOUSING])
    check_true("interaction head is separate from Main_Housing",
               o[INTERACTION] is not o[HOUSING])
    check("face head length == derived symmetric length",
          extents(o[FACE])[0], base["FACE_HEAD_LENGTH"])
    check("interaction head length == derived symmetric length",
          extents(o[INTERACTION])[0], base["INTERACTION_HEAD_LENGTH"])
    check("face head Y extent == FACE_HEAD_DIAMETER",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])
    check("face head Z extent == FACE_HEAD_DIAMETER",
          extents(o[FACE])[2], base["FACE_HEAD_DIAMETER"])
    check("interaction head Y extent == INTERACTION_HEAD_DIAMETER",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    check("interaction head Z extent == INTERACTION_HEAD_DIAMETER",
          extents(o[INTERACTION])[2], base["INTERACTION_HEAD_DIAMETER"])
    check_true("face head cylinder axis along X",
               cylinder_axis_along_x(o[FACE]))
    check_true("interaction head cylinder axis along X",
               cylinder_axis_along_x(o[INTERACTION]))
    check("face head starts after the left end margin",
          o[FACE].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"])
    check("interaction head starts after the centre gap",
          o[INTERACTION].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"]
          + base["FACE_HEAD_LENGTH"] + base["SENSOR_HEAD_CENTER_GAP"])
    check("interaction head leaves the right end margin",
          base["MAIN_BODY_WIDTH"] / 2.0 - o[INTERACTION].Shape.BoundBox.XMax,
          base["SENSOR_HEAD_END_MARGIN"])
    check("face head axis on the housing user-side face (Y)",
          axis_center_y(o[FACE]),
          front_face_y - base["SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE"])
    check("face head axis at housing vertical centre (Z)",
          axis_center_z(o[FACE]), base["MAIN_BODY_HEIGHT"] / 2.0)
    check("face head protrudes toward the user past the front face",
          front_face_y - o[FACE].Shape.BoundBox.YMin,
          base["SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE"]
          + base["FACE_HEAD_DIAMETER"] / 2.0)
    check("interaction head protrudes toward the user past the front face",
          front_face_y - o[INTERACTION].Shape.BoundBox.YMin,
          base["SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE"]
          + base["INTERACTION_HEAD_DIAMETER"] / 2.0)
    check_true("face head does not protrude past the rear (mount) face",
               o[FACE].Shape.BoundBox.YMax <= rear_face_y + 1e-6)
    check_true("interaction head does not protrude past the rear (mount) face",
               o[INTERACTION].Shape.BoundBox.YMax <= rear_face_y + 1e-6)

    print("--- Phase 2: FACE_HEAD_DIAMETER touches only the face head ---")
    _, o = build_with(FACE_HEAD_DIAMETER=base["FACE_HEAD_DIAMETER"] + 6.0)
    check("face head Y extent follows FACE_HEAD_DIAMETER",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"] + 6.0)
    check("face head Z extent follows FACE_HEAD_DIAMETER",
          extents(o[FACE])[2], base["FACE_HEAD_DIAMETER"] + 6.0)
    check("interaction head diameter unaffected",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    check("housing width unaffected by FACE_HEAD_DIAMETER",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])

    print("--- Phase 2: INTERACTION_HEAD_DIAMETER touches only the interaction head ---")
    _, o = build_with(INTERACTION_HEAD_DIAMETER=base["INTERACTION_HEAD_DIAMETER"] + 6.0)
    check("interaction head Y extent follows INTERACTION_HEAD_DIAMETER",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"] + 6.0)
    check("face head diameter unaffected",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])

    print("--- Phase 2: margins, gap, explicit lengths ---")
    _, o = build_with(SENSOR_HEAD_END_MARGIN=base["SENSOR_HEAD_END_MARGIN"] + 2.0)
    check("face head start follows SENSOR_HEAD_END_MARGIN",
          o[FACE].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"] + 2.0)
    check("derived head length shrinks with larger margins",
          extents(o[FACE])[0],
          (base["MAIN_BODY_WIDTH"] - 2.0 * (base["SENSOR_HEAD_END_MARGIN"] + 2.0)
           - base["SENSOR_HEAD_CENTER_GAP"]) / 2.0)
    _, o = build_with(SENSOR_HEAD_CENTER_GAP=base["SENSOR_HEAD_CENTER_GAP"] + 4.0)
    check("interaction head start follows SENSOR_HEAD_CENTER_GAP",
          o[INTERACTION].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"]
          + (base["MAIN_BODY_WIDTH"] - 2.0 * base["SENSOR_HEAD_END_MARGIN"]
             - base["SENSOR_HEAD_CENTER_GAP"] - 4.0) / 2.0
          + base["SENSOR_HEAD_CENTER_GAP"] + 4.0)
    _, o = build_with(FACE_HEAD_LENGTH=40.0)
    check("explicit FACE_HEAD_LENGTH honoured",
          extents(o[FACE])[0], 40.0)
    check("interaction head keeps derived length when face is explicit",
          extents(o[INTERACTION])[0], base["INTERACTION_HEAD_LENGTH"])

    print("--- Phase 2: orientation marks (flush debug strips) ---")
    mark_t = base["ORIENTATION_MARK_THICKNESS"]
    mark_w = base["ORIENTATION_MARK_WIDTH"]
    _, o = build_with()
    check("baseline face mark thin in Y (flush strip)",
          extents(o[FACE_MARK])[1], mark_t)
    check("baseline face mark width in Z",
          extents(o[FACE_MARK])[2], mark_w)
    check("face mark nearly flush with the barrel surface",
          (axis_center_y(o[FACE]) - base["FACE_HEAD_DIAMETER"] / 2.0)
          - o[FACE_MARK].Shape.BoundBox.YMin,
          mark_t - base["ORIENTATION_MARK_EMBED"])
    check_true("face mark sits on the user side of the housing front face",
               o[FACE_MARK].Shape.BoundBox.YMax <= front_face_y + 1e-6)
    check_true("interaction mark sits on the user side of the housing front face",
               o[INTERACTION_MARK].Shape.BoundBox.YMax <= front_face_y + 1e-6)

    print("--- Phase 2: independent rotation about X ---")
    _, o = build_with(FACE_HEAD_ROTATION_DEG=90.0)
    check("rotated face mark Y extent grows to mark width",
          extents(o[FACE_MARK])[1], mark_w)
    check("rotated face mark Z extent collapses to thickness",
          extents(o[FACE_MARK])[2], mark_t)
    check("face mark X extent unchanged (rotation about X)",
          extents(o[FACE_MARK])[0],
          base["FACE_HEAD_LENGTH"] * base["ORIENTATION_MARK_LENGTH_FRACTION"])
    check("interaction mark unaffected by face rotation (Y)",
          extents(o[INTERACTION_MARK])[1], mark_t)
    check("interaction mark unaffected by face rotation (Z)",
          extents(o[INTERACTION_MARK])[2], mark_w)
    check("face barrel envelope unchanged by its own rotation (Y)",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])
    check("interaction barrel envelope unchanged by face rotation (Y)",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    check("housing unaffected by face rotation",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])

    _, o = build_with(INTERACTION_HEAD_ROTATION_DEG=90.0)
    check("rotated interaction mark Y extent grows to mark width",
          extents(o[INTERACTION_MARK])[1], mark_w)
    check("rotated interaction mark Z extent collapses to thickness",
          extents(o[INTERACTION_MARK])[2], mark_t)
    check("face mark unaffected by interaction rotation (Y)",
          extents(o[FACE_MARK])[1], mark_t)
    check("face mark unaffected by interaction rotation (Z)",
          extents(o[FACE_MARK])[2], mark_w)

    print("--- Phase 2: model structure / no later-phase geometry ---")
    doc, o = build_with()
    part_features = [obj for obj in doc.Objects if obj.TypeId == "Part::Feature"]
    check("exactly six Part::Feature solids", len(part_features), 6)
    check("exactly eight document objects (2 groups + 6 parts)",
          len(doc.Objects), 8)
    references = doc.getObject(document.GROUP_REFERENCES)
    product = doc.getObject(document.GROUP_PRODUCT)
    check_true("References group exists", references is not None)
    check_true("Product group exists", product is not None)
    check_true("display reference is in References group",
               references is not None and o[DISPLAY] in references.Group)
    check_true("face mark is in References group",
               references is not None and o[FACE_MARK] in references.Group)
    check_true("interaction mark is in References group",
               references is not None and o[INTERACTION_MARK] in references.Group)
    check_true("main housing is in Product group",
               product is not None and o[HOUSING] in product.Group)
    check_true("face head is in Product group",
               product is not None and o[FACE] in product.Group)
    check_true("interaction head is in Product group",
               product is not None and o[INTERACTION] in product.Group)

    print("--- Phase 2.5: live-reload architecture ---")
    import live_reload
    import review_camera

    watched = {os.path.basename(p) for p in live_reload.watched_files()}
    for required in ("parameters.py", "parts.py", "sensor_heads.py",
                     "document.py"):
        check_true("watched: " + required, required in watched)
    for excluded in ("build.py", "validate.py", "live_reload.py",
                     "start_dev.py", "review_camera.py", "review_view.py",
                     "capture_review_view.py", "review_view_preset.py"):
        check_true("not watched: " + excluded, excluded not in watched)
    check_true("deepreal.FCStd is not a watch trigger",
               not any(p.endswith(".FCStd") for p in live_reload.watched_files()))

    deb = live_reload.Debouncer(0.4)
    deb.note_change(0.0)
    deb.note_change(0.1)
    deb.note_change(0.2)
    check_true("debouncer suppresses rapid burst", not deb.due(0.5))
    check_true("debouncer fires once burst is quiet", deb.due(0.61))
    deb.fire()
    check_true("debouncer resets after firing", not deb.due(1.0))

    fd, tmp_file = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    try:
        snap = live_reload.snapshot([tmp_file])
        changed, snap = live_reload.detect_changes([tmp_file], snap)
        check_true("no change detected without edits", not changed)
        later_ns = int((time.time() + 5.0) * 1e9)
        os.utime(tmp_file, ns=(later_ns, later_ns))
        changed, snap = live_reload.detect_changes([tmp_file], snap)
        check_true("mtime change detected", changed)
    finally:
        os.remove(tmp_file)

    tmp_dir = tempfile.mkdtemp()
    sys.path.insert(0, tmp_dir)
    probe_mod = "deepreal_reload_probe"
    try:
        with open(os.path.join(tmp_dir, probe_mod + ".py"), "w") as fh:
            fh.write("VALUE = 1\n")
        importlib.import_module(probe_mod)
        check("probe module initial value", sys.modules[probe_mod].VALUE, 1)

        with open(os.path.join(tmp_dir, probe_mod + ".py"), "w") as fh:
            fh.write("def broken(:\n")
        try:
            live_reload.reload_modules([probe_mod])
            raised = False
        except Exception:
            raised = True
        check_true("broken module reload raises (session catches it)", raised)
        check("module keeps last good state after failed reload",
              sys.modules[probe_mod].VALUE, 1)

        with open(os.path.join(tmp_dir, probe_mod + ".py"), "w") as fh:
            fh.write("VALUE = 2\n")
        live_reload.reload_modules([probe_mod])
        check("module recovers with new value", sys.modules[probe_mod].VALUE, 2)
    finally:
        sys.path.remove(tmp_dir)
        sys.modules.pop(probe_mod, None)

    try:
        reloaded = live_reload.reload_geometry_modules()
        check_true("geometry modules reload without error (reloaded: {})"
                   .format(", ".join(reloaded)), True)
    except Exception:
        check_true("geometry modules reload without error", False)

    print("--- Phase 2.5: in-place rebuild without duplication ---")
    doc, o = build_with()
    for _ in range(20):
        document.rebuild_in_place(doc)
    names = sorted(obj.Name for obj in doc.Objects)
    check("object count stable after 20 in-place rebuilds",
          len(doc.Objects), 8)
    check_true("no duplicate object names after 20 rebuilds",
               len(names) == len(set(names)))
    o = {obj.Name: obj for obj in doc.Objects}
    check_true("sensor heads still separate after rebuilds",
               o[FACE] is not o[INTERACTION])
    check_true("heads still in Product group after rebuilds",
               o[FACE] in doc.getObject(document.GROUP_PRODUCT).Group
               and o[INTERACTION] in doc.getObject(document.GROUP_PRODUCT).Group)
    check("face head diameter intact after rebuilds",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])

    p27 = parameters.resolve(dict(parameters.get_params(),
                                  FACE_HEAD_DIAMETER=27.0))
    document.rebuild_in_place(doc, p27)
    o = {obj.Name: obj for obj in doc.Objects}
    check("in-place rebuild applies FACE_HEAD_DIAMETER=27",
          extents(o[FACE])[1], 27.0)
    check("interaction head unchanged by face-only edit",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    document.rebuild_in_place(doc)
    o = {obj.Name: obj for obj in doc.Objects}
    check("in-place rebuild returns to default diameter",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])

    print("--- Phase 2.5: failed reload keeps the last valid model ---")
    bad = parameters.resolve(dict(parameters.get_params(),
                                  FACE_HEAD_DIAMETER=-5.0))
    try:
        document.rebuild_in_place(doc, bad)
        raised = False
    except Exception:
        raised = True
    check_true("invalid geometry raises during staging", raised)
    check("model intact after failed rebuild (object count)",
          len(doc.Objects), 8)
    o = {obj.Name: obj for obj in doc.Objects}
    check("face head intact after failed rebuild",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])
    document.rebuild_in_place(doc)
    check("rebuild succeeds again after failure",
          extents({obj.Name: obj for obj in doc.Objects}[FACE])[1],
          base["FACE_HEAD_DIAMETER"])

    print("--- Phase 2.5: orphan cleanup / generated-object ownership ---")
    import Part
    doc, o = build_with()
    check_true("all generated objects carry the ownership stamp",
               all(getattr(obj, "DeepRealGenerated", False)
                   for obj in doc.Objects))
    orphan = doc.addObject("Part::Feature", "Orphan_Probe")
    orphan.Shape = Part.makeSphere(5.0, App.Vector(0.0, 0.0, 15.0))
    document._mark_generated(orphan)  # as if a previous build created it
    doc.getObject(document.GROUP_REFERENCES).addObject(orphan)
    manual = doc.addObject("Part::Feature", "Manual_Notes")
    manual.Shape = Part.makeBox(1.0, 1.0, 1.0)
    doc.getObject(document.GROUP_REFERENCES).addObject(manual)
    doc.recompute()
    check("object count with probe objects", len(doc.Objects), 10)
    document.rebuild_in_place(doc)
    check("stamped orphan removed on rebuild", len(doc.Objects), 9)
    check_true("orphan name gone from the document",
               doc.getObject("Orphan_Probe") is None)
    check_true("manual (unstamped) object survives rebuild",
               doc.getObject("Manual_Notes") is not None)
    check_true("standard generated set intact after cleanup",
               all(doc.getObject(n) is not None for n in (
                   DISPLAY, HOUSING, FACE, INTERACTION,
                   FACE_MARK, INTERACTION_MARK)))
    check_true("groups still exist after cleanup",
               doc.getObject(document.GROUP_REFERENCES) is not None
               and doc.getObject(document.GROUP_PRODUCT) is not None)

    print("--- Phase 2.5: review camera preset ---")
    check_true("missing preset -> None (fallback to iso+fitAll)",
               review_camera.load_preset(
                   os.path.join(tempfile.gettempdir(),
                                "deepreal_no_such_preset.py")) is None)
    preset_probe = os.path.join(tmp_dir, "preset_probe.py")
    with open(preset_probe, "w") as fh:
        fh.write('CAMERA_SETTINGS = "#Inventor V2.1 ascii\\n\\n'
                 'OrthographicCamera { }\\n"\n')
    loaded = review_camera.load_preset(preset_probe)
    check_true("preset file loads as a camera string",
               isinstance(loaded, str) and "OrthographicCamera" in loaded)
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print("--- Phase 2.5: no GUI XML injection anywhere ---")
    # Needles are built dynamically so this file's own source stays clean.
    needle_zip_write = "write" + "str"
    needle_module = "view" + "state"
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(HERE, name)) as fh:
            src = fh.read()
        check_true("{}: no archive-injection code".format(name),
                   needle_zip_write not in src and needle_module not in src)

    print("--- document presentation ---")
    doc, o = build_with()
    check_true("no touched/invalid objects after build recompute",
               all(not ({"Touched", "Invalid"} & set(obj.State))
                   for obj in doc.Objects))

    if os.path.exists(document.OUTPUT_PATH):
        if document.DOC_NAME in App.listDocuments():
            App.closeDocument(document.DOC_NAME)
        saved = App.openDocument(document.OUTPUT_PATH)
        names = sorted(obj.Name for obj in saved.Objects)
        print("  saved objects:", ", ".join(names))
        check("saved document object count", len(saved.Objects), 8)
        for name in (DISPLAY, HOUSING, FACE, INTERACTION, FACE_MARK,
                     INTERACTION_MARK):
            check_true("saved document contains " + name,
                       saved.getObject(name) is not None)
        check_true("saved document fully recomputed (no touched/invalid)",
                   all(not ({"Touched", "Invalid"} & set(obj.State))
                       for obj in saved.Objects))
        App.closeDocument(saved.Name)

        with zipfile.ZipFile(document.OUTPUT_PATH) as zf:
            zip_members = zf.namelist()
        print("  archive members:", ", ".join(zip_members))
        check_true("no GuiDocument.xml in freshly built file (GUI XML "
                   "injection removed; view state stays GUI-side)",
                   "GuiDocument.xml" not in zip_members)
    else:
        check_true("deepreal.FCStd exists (run build.py first)", False)

    print()
    if FAILURES:
        print("VALIDATION FAILED ({} check(s)):".format(len(FAILURES)))
        for label in FAILURES:
            print("  -", label)
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(1)
    print("All Phase 1 + Phase 2 validation checks passed.")
    sys.stdout.flush()


# freecadcmd quirks: an unhandled exception makes it run the script a
# second time and still exit 0, and sys.exit() drops buffered stdout.
# Catch everything, flush explicitly, and exit with a real status code.
try:
    main()
except SystemExit:
    raise
except Exception:
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(1)
