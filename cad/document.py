"""
DeepReal document assembly (Phases 1-3 + Phase 2.5 live-reload support).

Builds the FreeCAD document from parameters.py. This module is import-safe
(no side effects at import time); the runnable entry points are build.py
(rebuild + save, headless/CI) and validate.py (regeneration checks). The
interactive live reload (live_reload.py) reuses the exact same geometry
code through rebuild_in_place().

Resulting model tree:

    deepreal
    |-- References
    |   |-- MacBook_Air_M2_Display_Reference
    |   |-- Face_Head_Orientation_Reference         (debug mark)
    |   `-- Interaction_Head_Orientation_Reference  (debug mark)
    `-- Product
        |-- Main_Housing  (one extruded Y-Z side profile: rectangular
        |                  body + quarter-circle rear arm + laptop-lid
        |                  pocket, a single connected solid)
        |-- Face_Sensor_Head          (user side, -Y)
        `-- Interaction_Sensor_Head

The document is saved only through FreeCAD's normal save API. Headless
saves contain no GUI view state; view/camera setup is a GUI-side concern
(review_view.py / review_camera.py / the live-reload session).
"""

import os

import FreeCAD as App

import parameters
import parts
import rear_arm
import sensor_heads

DOC_NAME = "deepreal"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "deepreal.FCStd")

GROUP_REFERENCES = "References"
GROUP_PRODUCT = "Product"

# Name of the dynamic property stamped onto every object the build system
# creates. The stamp is stored in the document, so ownership survives
# save/reload cycles: populate_document only ever deletes stamped objects
# (plus the two reserved group names) and never touches objects the user
# created manually.
GENERATED_MARK = "DeepRealGenerated"


def _mark_generated(obj):
    """Stamp `obj` as owned by the DeepReal build system."""
    if not hasattr(obj, GENERATED_MARK):
        obj.addProperty("App::PropertyBool", GENERATED_MARK, "DeepReal",
                        "Owned by the DeepReal build system; do not edit.")
    setattr(obj, GENERATED_MARK, True)

# Review colours as (r, g, b) floats in 0..1, plus optional transparency
# (0..100). Cosmetic only; geometry never depends on these. Applied through
# the normal view-provider API and only when a build runs with the FreeCAD
# GUI up -- headless saves carry no view state at all.
OBJECT_STYLES = {
    "MacBook_Air_M2_Display_Reference": {
        "color": (0.60, 0.60, 0.65), "transparency": 70},
    "Main_Housing": {"color": (0.15, 0.45, 0.80)},
    "Face_Sensor_Head": {"color": (0.85, 0.55, 0.20)},
    "Interaction_Sensor_Head": {"color": (0.20, 0.65, 0.55)},
    "Face_Head_Orientation_Reference": {"color": (0.90, 0.10, 0.10)},
    "Interaction_Head_Orientation_Reference": {"color": (0.90, 0.10, 0.10)},
}


def generated_shape_map(params):
    """Build every generated shape WITHOUT touching any document.

    Returns {object_name: (shape, group_name)}. Building all shapes first
    means a failure (invalid parameter, half-saved edit) raises before any
    existing document object is modified, so the displayed model stays
    intact. Later phases register their parts here; group membership in
    this map is what drives automatic visibility handling.
    """
    heads = sensor_heads.sensor_head_shapes(params)
    return {
        parts.DISPLAY_REFERENCE_NAME:
            (parts.display_reference_shape(params), GROUP_REFERENCES),
        parts.MAIN_HOUSING_NAME:
            (rear_arm.main_housing_with_arm_shape(params), GROUP_PRODUCT),
        sensor_heads.FACE_HEAD_NAME:
            (heads["face"], GROUP_PRODUCT),
        sensor_heads.INTERACTION_HEAD_NAME:
            (heads["interaction"], GROUP_PRODUCT),
        sensor_heads.FACE_ORIENTATION_NAME:
            (heads["face_reference"], GROUP_REFERENCES),
        sensor_heads.INTERACTION_ORIENTATION_NAME:
            (heads["interaction_reference"], GROUP_REFERENCES),
    }


def populate_document(doc, params):
    """Replace all generated objects inside `doc` with geometry from params.

    Shared by the headless build and the interactive live reload, so both
    workflows run exactly the same geometry code. Generated objects are
    deleted and recreated deterministically by name; repeated calls never
    accumulate duplicates. An object whose registration is removed from
    the source disappears from the document on the next rebuild: every
    generated object carries the DeepRealGenerated stamp, and every
    stamped object that is no longer in the registry is deleted. Manually
    created (unstamped) objects are never deleted, even if the user put
    them inside one of the generated groups.
    """
    shapes = generated_shape_map(params)  # may raise; doc stays untouched

    # Remove everything the build system owns: objects in the new registry
    # (recreated below), objects stamped by previous builds (including any
    # whose registration was since removed from the source), and the two
    # generated groups (recreated below). Unstamped manual objects survive.
    doomed = set(shapes.keys()) | {GROUP_REFERENCES, GROUP_PRODUCT}
    doomed.update(obj.Name for obj in doc.Objects
                  if getattr(obj, GENERATED_MARK, False))
    for name in sorted(doomed):
        existing = doc.getObject(name)
        if existing is not None:
            doc.removeObject(name)

    groups = {}
    for group_name in (GROUP_REFERENCES, GROUP_PRODUCT):
        group = doc.addObject("App::DocumentObjectGroup", group_name)
        _mark_generated(group)
        groups[group_name] = group

    created = []
    for name, (shape, group_name) in shapes.items():
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        _mark_generated(obj)
        groups[group_name].addObject(obj)
        created.append(obj)

    doc.recompute()
    _style(doc)
    return created


def build_document(params=None):
    """Headless/CI path: create a fresh document with all generated geometry.

    The document is regenerated from scratch on every call: all objects
    are derived from parameters.py, so the generated FCStd is a disposable
    artifact and the Python source remains the single source of truth.
    """
    if params is None:
        params = parameters.get_params()
    params = parameters.resolve(params)

    if DOC_NAME in App.listDocuments():
        App.closeDocument(DOC_NAME)
    doc = App.newDocument(DOC_NAME)
    populate_document(doc, params)
    return doc


def rebuild_in_place(doc, params=None):
    """Interactive path: rebuild generated geometry inside an open document.

    The document identity and GUI session are preserved; only the
    generated objects are swapped. Raises (leaving the document untouched)
    if the parameters produce invalid geometry.
    """
    if params is None:
        params = parameters.get_params()
    params = parameters.resolve(params)
    populate_document(doc, params)
    return doc


def _style(doc):
    """Apply review colours when a GUI is present (headless builds skip
    this entirely; their saved files carry no view state).

    Group separation and naming keep every object distinguishable in the
    tree regardless; colours are a bonus for interactive sessions.
    """
    if not App.GuiUp:
        return
    try:
        for name, style in OBJECT_STYLES.items():
            obj = doc.getObject(name)
            if obj is None:
                continue
            if "color" in style:
                obj.ViewObject.ShapeColor = style["color"]
            if "transparency" in style:
                obj.ViewObject.Transparency = style["transparency"]
    except Exception as exc:  # appearance must never break a build
        print("warning: could not set appearance:", exc)


def summarise(doc):
    """Print the model tree with overall dimensions."""
    print("Model tree:")
    for group_name in (GROUP_REFERENCES, GROUP_PRODUCT):
        group = doc.getObject(group_name)
        print("  " + group.Name)
        for obj in group.Group:
            bb = obj.Shape.BoundBox
            print("    {}  [{:.1f} x {:.1f} x {:.1f}] mm (X x Y x Z)".format(
                obj.Name, bb.XLength, bb.YLength, bb.ZLength))


def main():
    """Rebuild and save deepreal.FCStd from the current parameters."""
    doc = build_document()
    doc.Comment = ("DeepReal Phases 1-3: display reference, main housing "
                   "envelope built as a single extruded side profile "
                   "with the full-width quarter-circle rear arm "
                   "(forming the laptop-lid pocket), two "
                   "cylindrical sensor heads (interaction drum pitched "
                   "down). Generated by cad/build.py; do not edit "
                   "generated geometry manually.")
    doc.recompute()  # explicit: the saved file must be fully recomputed
    doc.saveAs(OUTPUT_PATH)
    summarise(doc)
    print("Saved:", OUTPUT_PATH)
    print("Headless save: no GUI view state embedded. For interactive "
          "development, start the live-reload session with cad/dev.sh")
