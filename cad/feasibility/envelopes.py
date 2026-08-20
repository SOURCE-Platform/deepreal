"""Envelope builders for the drum-internals feasibility study.

Each component gets ONE envelope object in a "library row" behind the
model (+Y), spaced along X, NOT inside the drums (placement inside the
drums is layout work, see layouts.py). Gate 1 components are single
primitives (box or cylinder); Gate 1.5B multi-part components are
compounds of their registry "parts" (component-local frame: origin at
aperture centre, local +Z = depth into the component).

Every envelope object carries properties linking it back to the registry
so the document is self-describing and validate_feasibility.py can check
bounds against the published numbers.
"""

import FreeCAD as App
import Part

import registry


LIBRARY_ROW_Y = -60.0   # centre plane of the library row (user side, clear
                        # of the model which starts at Y=-13.5)
LIBRARY_ROW_Z = -40.0   # envelopes stand on this plane (below the model)
LIBRARY_START_X = -170.0
LIBRARY_GAP_X = 20.0


def _make_envelope_shape(entry):
    if entry["shape"] == "cylinder":
        diameter, length = entry["dims_mm"]
        return Part.makeCylinder(diameter / 2.0, length)
    x, y, z = entry["dims_mm"]
    return Part.makeBox(x, y, z)


def make_part_shape(part):
    """One registry part in the component-local frame (see registry.py)."""
    u_c, v_c, w0 = part.get("origin", (0.0, 0.0, 0.0))
    if part["shape"] == "cylinder":
        diameter, height = part["dims_mm"]
        sh = Part.makeCylinder(diameter / 2.0, height)
        sh.translate(App.Vector(u_c, v_c, w0))
    else:
        x, y, z = part["dims_mm"]
        sh = Part.makeBox(x, y, z)
        sh.translate(App.Vector(u_c - x / 2.0, v_c - y / 2.0, w0))
    return sh


def make_component_shape(key):
    """Full local-frame shape for a component (compound if multi-part)."""
    entry = registry.COMPONENTS[key]
    if entry["shape"] == "multipart":
        return Part.makeCompound(
            [make_part_shape(p) for p in entry["parts"]])
    return _make_envelope_shape(entry)


def expected_union_dims(key):
    """Sorted overall dims of a component from the registry (for checks)."""
    entry = registry.COMPONENTS[key]
    if entry["shape"] == "multipart":
        sh = make_component_shape(key)
        bb = sh.BoundBox
        return sorted([bb.XLength, bb.YLength, bb.ZLength])
    if entry["shape"] == "cylinder":
        d, length = entry["dims_mm"]
        return sorted([d, d, length])
    return sorted(entry["dims_mm"])


def build_all(doc):
    """Create one envelope object per component. Returns {key: object}."""
    objects = {}
    cursor_x = LIBRARY_START_X
    for key in registry.LIBRARY_ORDER:
        entry = registry.COMPONENTS[key]
        feat = doc.addObject("Part::Feature", "ENV_" + key)
        feat.Shape = make_component_shape(key)
        bb = feat.Shape.BoundBox
        # Stand the envelope on the library plane, centred in Y.
        feat.Placement = App.Placement(
            App.Vector(cursor_x - bb.XMin,
                       LIBRARY_ROW_Y - bb.YMin - bb.YLength / 2.0,
                       LIBRARY_ROW_Z - bb.ZMin),
            App.Rotation())
        cursor_x += bb.XLength + LIBRARY_GAP_X
        # Self-describing metadata for the document.
        feat.addProperty("App::PropertyString", "RegistryKey",
                         "Feasibility").RegistryKey = key
        feat.addProperty("App::PropertyString", "Manufacturer",
                         "Feasibility").Manufacturer = entry["manufacturer"]
        feat.addProperty("App::PropertyString", "Part",
                         "Feasibility").Part = entry["part"]
        feat.addProperty("App::PropertyString", "Function",
                         "Feasibility").Function = entry["function"]
        feat.addProperty("App::PropertyString", "PublishedDims",
                         "Feasibility").PublishedDims = str(entry["dims_mm"])
        feat.addProperty("App::PropertyString", "Evidence",
                         "Feasibility").Evidence = entry["evidence"]
        feat.addProperty("App::PropertyString", "FitStatus",
                         "Feasibility").FitStatus = entry["status"]
        feat.addProperty("App::PropertyString", "CadAsset",
                         "Feasibility").CadAsset = str(entry["cad_asset"])
        objects[key] = feat
    return objects
