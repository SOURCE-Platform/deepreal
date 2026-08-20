"""Envelope builders for the drum-internals feasibility study (Gate 1).

Each component gets ONE primitive envelope (box or cylinder) sized exactly
to the registry dimensions (registry.py). Envelopes are placed in a
"library row" behind the model (+Y), spaced along X, NOT inside the drums:
placement inside the drums is Gate 2 packaging work.

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
LIBRARY_START_X = -150.0
LIBRARY_GAP_X = 20.0


def _make_envelope_shape(entry):
    if entry["shape"] == "cylinder":
        diameter, length = entry["dims_mm"]
        return Part.makeCylinder(diameter / 2.0, length)
    x, y, z = entry["dims_mm"]
    return Part.makeBox(x, y, z)


def build_all(doc):
    """Create one envelope object per component. Returns {key: object}."""
    objects = {}
    cursor_x = LIBRARY_START_X
    for key in registry.LIBRARY_ORDER:
        entry = registry.COMPONENTS[key]
        feat = doc.addObject("Part::Feature", "ENV_" + key)
        feat.Shape = _make_envelope_shape(entry)
        dims = entry["dims_mm"]
        if entry["shape"] == "cylinder":
            # Stand the cylinder on the library plane, centred in Y.
            feat.Placement = App.Placement(
                App.Vector(cursor_x, LIBRARY_ROW_Y, LIBRARY_ROW_Z),
                App.Rotation())
            cursor_x += dims[0] + LIBRARY_GAP_X
        else:
            feat.Placement = App.Placement(
                App.Vector(cursor_x,
                           LIBRARY_ROW_Y - dims[1] / 2.0,
                           LIBRARY_ROW_Z),
                App.Rotation())
            cursor_x += dims[0] + LIBRARY_GAP_X
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
        feat.addProperty("App::PropertyString", "FitStatus",
                         "Feasibility").FitStatus = entry["status"]
        feat.addProperty("App::PropertyString", "CadAsset",
                         "Feasibility").CadAsset = str(entry["cad_asset"])
        objects[key] = feat
    return objects
