"""
Phase 3 part builder: Main_Housing as ONE coherent Y-Z side profile.

Per the geometry specification and the annotated review screenshots, the
Main_Housing solid -- rectangular sensor body + full-width quarter-circle
rear arm + laptop-lid pocket -- is built from a SINGLE closed 2D side
profile extruded along X across the full device width. No boolean union
is involved, so there are no splitter seams, no internal faces, and no
crossover artifacts: body and arm are one enclosure by construction.

The arm hangs BELOW the rectangular body (the corrected lower position
from the review annotations): its true quarter-circle arc meets the
housing exactly at the bottom-rear corner, tangent to the rear face, so
the silhouette runs rear face -> arc -> mounting face -> pocket ceiling
as one continuous outline.

Side profile (Y-Z plane; -Y = front/user side):

    Z
    ^
    |   (front)                  (rear)
    |   +----------------------+   top face (housing_top_z)
    |   |                      |
    |   |   rectangular body   |
    |   |                      |
    |   +-------+              |   pocket ceiling (housing_bot_z)
    |  pocket   | mount face    |
    |   mouth   | (faces lid)    )  quarter-circle arc: centre C =
    |           |                )  (MOUNT_FACE_Y, housing_bot_z),
    |           |               |   radius REAR_ARM_RADIUS; tangent
    |           +  bottom tip --+   to the rear face at the corner
    +--------------------------------> Y

The laptop lid's top edge rises into the pocket mouth (between the lid
rear face and the mounting face) without touching anything; the Phase 4
magnet/plate/foam-tape stack will secure the device there. The long thin
line leaving the arm in the original sketches is the USB-C cable and is
deliberately NOT modelled.

resolve() derives all profile points and rejects colliding/impossible
parameter sets, so this builder only reads derived REAR_ARM_* values.
Translations are baked into the shape (object placement stays at the
origin) so Shape.BoundBox is global.
"""

import math

import FreeCAD as App
import Part


def main_housing_with_arm_shape(params):
    """Build the Main_Housing product solid from resolved parameters.

    One closed Y-Z wire (pocket ceiling -> mounting face -> arc -> rear
    face -> top -> front face) extruded along X across MAIN_BODY_WIDTH.
    Pure geometry: touches no document, so invalid parameters raise before
    any existing document object is modified. Raises unless the result is
    exactly one valid connected solid -- anything less is a build error,
    never a product.
    """
    width = params["MAIN_BODY_WIDTH"]
    x0 = params["MAIN_BODY_DISPLAY_OFFSET_X"] - width / 2.0
    front_y = (params["MAIN_BODY_DISPLAY_OFFSET_Y"]
               - params["MAIN_BODY_DEPTH"] / 2.0)
    rear_y = (params["MAIN_BODY_DISPLAY_OFFSET_Y"]
              + params["MAIN_BODY_DEPTH"] / 2.0)
    bot_z = params["REAR_ARM_HOUSING_BOTTOM_Z"]
    top_z = bot_z + params["MAIN_BODY_HEIGHT"]
    face_y = params["REAR_ARM_MOUNT_FACE_Y"]
    arc_top_y = params["REAR_ARM_REAR_Y"]   # arc's upper endpoint
    tip_z = params["REAR_ARM_BOTTOM_Z"]     # mounting-face bottom tip
    r = params["REAR_ARM_RADIUS"]

    # Arc midpoint, exactly 45 deg around the quarter circle.
    mid = (face_y + r * math.sqrt(0.5), bot_z - r * math.sqrt(0.5))

    def p(y, z):
        return App.Vector(x0, y, z)

    edges = [
        # pocket ceiling: front-bottom corner -> mounting face top
        Part.makeLine(p(front_y, bot_z), p(face_y, bot_z)),
        # mounting face: down to the arm tip
        Part.makeLine(p(face_y, bot_z), p(face_y, tip_z)),
        # quarter-circle arc: tip -> up/rear toward the bottom-rear corner
        Part.Arc(p(face_y, tip_z), p(*mid), p(arc_top_y, bot_z)).toShape(),
    ]
    if arc_top_y < rear_y - 1e-9:
        # An explicit smaller radius leaves the arc short of the rear
        # face: close the gap with a flat bottom strip.
        edges.append(Part.makeLine(p(arc_top_y, bot_z), p(rear_y, bot_z)))
    edges.extend([
        # rear face, top face, front face (closes the profile)
        Part.makeLine(p(rear_y, bot_z), p(rear_y, top_z)),
        Part.makeLine(p(rear_y, top_z), p(front_y, top_z)),
        Part.makeLine(p(front_y, top_z), p(front_y, bot_z)),
    ])
    face = Part.Face(Part.Wire(edges))  # Wire sorts connected edges
    solid = face.extrude(App.Vector(width, 0.0, 0.0))
    if len(solid.Solids) != 1:
        raise ValueError("single-profile housing produced {} solid(s); "
                         "expected exactly 1".format(len(solid.Solids)))
    if not solid.isValid():
        raise ValueError("single-profile housing produced an invalid "
                         "solid")
    return solid
