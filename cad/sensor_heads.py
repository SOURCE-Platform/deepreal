"""
Phase 2 sensor-head builders.

Two horizontal cylindrical barrels whose axes run along X (left/right
across the display), per Reference A (Frame 2), mounted on the USER SIDE
(-Y) of the main housing -- the same side as the display's visible
screen/pixels and the seated user:

    front view (looking at the -Y user side of the housing):

    | margin | FACE HEAD | gap | INTERACTION HEAD | margin |

- Face_Sensor_Head        : left barrel  (face/presence subsystem)
- Interaction_Sensor_Head : right barrel (workspace-interaction subsystem)

The rear/mount side (+Y, the back of the laptop lid) stays clear for the
integrated arm and magnetic mounting system in later phases.

Each barrel gets a temporary orientation mark (debug geometry, not product
hardware): a thin strip lying almost flush with the barrel surface that
rotates with the barrel, so pitch rotation is visible even though a plain
cylinder is rotationally symmetric. The mark sits on the surface point
facing the user (-Y) at 0 deg -- the nominal direction the sensor faces.

Rotation convention (right-hand rule about +X): 0 deg = facing the user
(-Y); +90 deg = pitched down toward the keyboard (-Z); -90 deg = pitched
up (+Z).

Shape-level functions are pure geometry (no document needed, safe to fail
without side effects); builders create the named Part::Feature objects.

No lenses, apertures, motors, bearings, gears, or optical openings are
modelled in this phase. The barrels are mechanical envelopes that later
phases will populate.
"""

import FreeCAD as App
import Part

FACE_HEAD_NAME = "Face_Sensor_Head"
INTERACTION_HEAD_NAME = "Interaction_Sensor_Head"
FACE_ORIENTATION_NAME = "Face_Head_Orientation_Reference"
INTERACTION_ORIENTATION_NAME = "Interaction_Head_Orientation_Reference"

X_AXIS = App.Vector(1, 0, 0)


def sensor_head_shapes(params):
    """All four sensor-head shapes, without touching any document.

    Returns a dict: face, interaction, face_reference,
    interaction_reference (Part.Shape objects).
    """
    axis_y, axis_z = _axis_position(params)
    face_x0, interaction_x0 = _layout(params)
    return {
        "face": _barrel_shape(
            face_x0, params["FACE_HEAD_LENGTH"], params["FACE_HEAD_DIAMETER"],
            axis_y, axis_z, params["FACE_HEAD_ROTATION_DEG"]),
        "interaction": _barrel_shape(
            interaction_x0, params["INTERACTION_HEAD_LENGTH"],
            params["INTERACTION_HEAD_DIAMETER"],
            axis_y, axis_z, params["INTERACTION_HEAD_ROTATION_DEG"]),
        "face_reference": _orientation_mark_shape(
            params, face_x0, params["FACE_HEAD_LENGTH"],
            params["FACE_HEAD_DIAMETER"],
            axis_y, axis_z, params["FACE_HEAD_ROTATION_DEG"]),
        "interaction_reference": _orientation_mark_shape(
            params, interaction_x0, params["INTERACTION_HEAD_LENGTH"],
            params["INTERACTION_HEAD_DIAMETER"],
            axis_y, axis_z, params["INTERACTION_HEAD_ROTATION_DEG"]),
    }


def build_sensor_heads(doc, params):
    """Create the four sensor-head objects in doc.

    Group assignment is the caller's job (barrels -> Product, orientation
    marks -> References).
    """
    shapes = sensor_head_shapes(params)
    return {
        "face": _add_feature(doc, FACE_HEAD_NAME, shapes["face"]),
        "interaction": _add_feature(doc, INTERACTION_HEAD_NAME,
                                    shapes["interaction"]),
        "face_reference": _add_feature(doc, FACE_ORIENTATION_NAME,
                                       shapes["face_reference"]),
        "interaction_reference": _add_feature(doc, INTERACTION_ORIENTATION_NAME,
                                              shapes["interaction_reference"]),
    }


def _add_feature(doc, name, shape):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    return obj


def _layout(params):
    """X start positions of the two barrels, laid out left to right."""
    left = (-params["MAIN_BODY_WIDTH"] / 2.0
            + params["MAIN_BODY_DISPLAY_OFFSET_X"])
    face_x0 = left + params["SENSOR_HEAD_END_MARGIN"]
    interaction_x0 = (face_x0
                      + params["FACE_HEAD_LENGTH"]
                      + params["SENSOR_HEAD_CENTER_GAP"])
    return face_x0, interaction_x0


def _axis_position(params):
    """(Y, Z) of the barrel axes. Both heads share the same axis line
    placement; only their X ranges and rotations differ.

    Y is measured from the housing's user-side face (-Y): offset 0 puts
    the axis on that face plane (barrel half embedded in the housing, half
    protruding toward the user); positive offsets move the axis outward
    toward the user, negative offsets move it into the housing.
    """
    front_face_y = (params["MAIN_BODY_DISPLAY_OFFSET_Y"]
                    - params["MAIN_BODY_DEPTH"] / 2.0)
    axis_y = front_face_y - params["SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE"]
    body_center_z = (params["MAIN_BODY_DISPLAY_OFFSET_Z"]
                     + params["MAIN_BODY_HEIGHT"] / 2.0)
    axis_z = body_center_z + params["SENSOR_HEAD_AXIS_Z_OFFSET_FROM_BODY_CENTER"]
    return axis_y, axis_z


def _barrel_shape(x0, length, diameter, axis_y, axis_z, rotation_deg):
    """One horizontal cylindrical barrel, axis along X."""
    shape = Part.makeCylinder(diameter / 2.0, length,
                              App.Vector(x0, axis_y, axis_z), X_AXIS)
    _rotate_about_axis(shape, axis_y, axis_z, rotation_deg)
    return shape


def _orientation_mark_shape(params, x0, length, diameter,
                            axis_y, axis_z, rotation_deg):
    """Temporary debug mark rotating with a barrel.

    A thin flat strip lying almost flush with the barrel's user-facing
    surface (-Y at 0 deg), like a piece of tape: it marks the nominal
    direction the sensor faces without reading as product hardware.
    Clearly reference geometry, not part of DeepReal.
    """
    radius = diameter / 2.0
    mark_length = length * params["ORIENTATION_MARK_LENGTH_FRACTION"]
    width = params["ORIENTATION_MARK_WIDTH"]          # tangential (Z at 0 deg)
    thickness = params["ORIENTATION_MARK_THICKNESS"]  # radial (Y at 0 deg)
    embed = params["ORIENTATION_MARK_EMBED"]

    shape = Part.makeBox(mark_length, thickness, width)
    shape.translate(App.Vector(
        x0 + length / 2.0 - mark_length / 2.0,     # centred on the barrel
        axis_y - radius + embed - thickness,       # flush on the -Y surface
        axis_z - width / 2.0))                     # centred on the axis
    _rotate_about_axis(shape, axis_y, axis_z, rotation_deg)
    return shape


def _rotate_about_axis(shape, axis_y, axis_z, rotation_deg):
    """Rotate a shape in place about the X-parallel axis (axis_y, axis_z)."""
    if abs(rotation_deg) > 1e-12:
        shape.rotate(App.Vector(0, axis_y, axis_z), X_AXIS, rotation_deg)
    return shape
