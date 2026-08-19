"""
Phase 1 part builders.

Each part has a shape-level function (pure geometry, no document needed,
safe to fail without side effects) and a thin builder that creates the
named Part::Feature in a document. Every dimension comes from the params
dict produced by parameters.get_params(); nothing is hard-coded here, so
editing parameters.py and rerunning build.py regenerates the geometry
predictably.

Only the display reference slab lives here: since Phase 3 the
Main_Housing solid (rectangular body + quarter-circle rear arm +
laptop-lid pocket) is built as one extruded side profile in
rear_arm.py.

Translations are baked into the shapes (object placements stay at the
origin) so that Shape.BoundBox is always in global coordinates.
"""

import FreeCAD as App
import Part

# Canonical object names (also used by document.py and validate.py).
DISPLAY_REFERENCE_NAME = "MacBook_Air_M2_Display_Reference"
MAIN_HOUSING_NAME = "Main_Housing"


def display_reference_shape(params):
    """
    Simplified MacBook Air M2 lid: a plain slab.

    - X width     = DISPLAY_REFERENCE_WIDTH   (visualisation only)
    - Y thickness = DISPLAY_LID_THICKNESS     (measured: 3.0 mm)
    - Z height    = DISPLAY_REFERENCE_HEIGHT  (visualisation only)

    Positioned with its top edge at Z = 0, centred on X = 0, and centred on
    the lid mid-plane Y = 0. The screen/pixels face points toward the user
    at -Y; the rear lid face (mount side) is at +Y.

    Reference geometry only: no keyboard, glass, logo, or electronics.
    """
    width = params["DISPLAY_REFERENCE_WIDTH"]
    thickness = params["DISPLAY_LID_THICKNESS"]
    height = params["DISPLAY_REFERENCE_HEIGHT"]

    shape = Part.makeBox(width, thickness, height)
    shape.translate(App.Vector(-width / 2.0, -thickness / 2.0, -height))
    return shape


def build_display_reference(doc, params):
    """Create the display-reference object in doc."""
    obj = doc.addObject("Part::Feature", DISPLAY_REFERENCE_NAME)
    obj.Shape = display_reference_shape(params)
    return obj
