"""
DeepReal document assembly (Phase 2 + Phase 2.5 live-reload support).

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
        |-- Main_Housing
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
import sensor_heads

DOC_NAME = "deepreal"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "deepreal.FCStd")

GROUP_REFERENCES = "References"
GROUP_PRODUCT = "Product"

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
            (parts.main_housing_shape(params), GROUP_PRODUCT),
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
    accumulate duplicates. Non-generated objects in the document are left
    untouched.
    """
    shapes = generated_shape_map(params)  # may raise; doc stays untouched

    # Remove previous generated objects (parts first, then empty groups).
    for name in list(shapes.keys()) + [GROUP_REFERENCES, GROUP_PRODUCT]:
        existing = doc.getObject(name)
        if existing is not None:
            doc.removeObject(name)

    groups = {}
    for group_name in (GROUP_REFERENCES, GROUP_PRODUCT):
        groups[group_name] = doc.addObject("App::DocumentObjectGroup",
                                           group_name)

    created = []
    for name, (shape, group_name) in shapes.items():
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
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
    doc.Comment = ("DeepReal Phase 2: display reference, main housing "
                   "envelope, two cylindrical sensor heads. Generated by "
                   "cad/build.py; do not edit generated geometry manually.")
    doc.recompute()  # explicit: the saved file must be fully recomputed
    doc.saveAs(OUTPUT_PATH)
    summarise(doc)
    print("Saved:", OUTPUT_PATH)
    print("Headless save: no GUI view state embedded. For interactive "
          "development, start the live-reload session with cad/dev.sh")
