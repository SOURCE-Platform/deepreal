"""
DeepReal CAD parameters -- single source of truth.

All dimensions are in millimetres.

Coordinate system
-----------------
- X : left/right across the laptop display (+X to the user's right)
- Y : front/back depth, defined physically rather than abstractly:
      -Y = FRONT / USER SIDE -- the side of the display with the visible
           screen/pixels, where the seated user sits. The sensor heads
           live on this side.
      +Y = REAR / MOUNT SIDE -- the back of the laptop lid. The integrated
           arm and magnetic mounting system will live on this side.
      This matches FreeCAD's viewing convention: the standard front view
      and the generated isometric review camera both look at the -Y face.
- Z : vertical (+Z up)

Origin
------
The origin sits at the centre of the top edge of the display lid, on the
lid's mid-plane:

- X = 0 : horizontal centre of the display
- Y = 0 : mid-plane of the lid thickness (screen/pixels face at
          Y = -thickness/2, rear lid face at Y = +thickness/2)
- Z = 0 : top edge of the display lid; the lid extends downward (-Z)

The laptop is reference geometry only. It is NOT part of the DeepReal
product; it exists so DeepReal parts can be positioned against the top edge
of a display. Its dimensions are independently adjustable so thicker laptops
and desktop monitors can be simulated later.

To change the model, edit the values below and rerun build.py. No dimension
should be hard-coded anywhere else.
"""

# ---------------------------------------------------------------------------
# Display reference (MacBook Air M2, the current physical reference laptop)
# ---------------------------------------------------------------------------

# Measured lid thickness of the reference MacBook Air M2.
DISPLAY_LID_THICKNESS = 3.0

# Overall lid width/height. Approximate published chassis dimensions, used
# only to make the reference slab large enough to visualise against.
# TEMPORARY visualisation parameters, not measured values.
DISPLAY_REFERENCE_WIDTH = 304.0
DISPLAY_REFERENCE_HEIGHT = 215.0

# ---------------------------------------------------------------------------
# DeepReal main housing (concept design envelope)
# ---------------------------------------------------------------------------

MAIN_BODY_WIDTH = 120.0   # X extent
MAIN_BODY_HEIGHT = 30.0   # Z extent
MAIN_BODY_DEPTH = 24.0    # Y extent

# Placement of the housing relative to the display top edge / origin.
# These are uncertain concept-stage values, exposed as parameters rather
# than guessed permanently:
#   X : horizontal offset of the housing centre from the display centre
#   Y : offset of the housing depth-centre from the lid mid-plane
#       (0 = housing straddles the lid symmetrically)
#   Z : height of the housing bottom face above the display top edge
#       (0 = bottom face flush with the top edge)
MAIN_BODY_DISPLAY_OFFSET_X = 0.0
MAIN_BODY_DISPLAY_OFFSET_Y = 0.0
MAIN_BODY_DISPLAY_OFFSET_Z = 0.0

# ---------------------------------------------------------------------------
# Sensor heads (Phase 2): two horizontal cylindrical barrels along X,
# mounted on the user side (-Y) of the main housing
# ---------------------------------------------------------------------------

# Mechanical placeholder envelopes only. Sensor hardware is not yet
# selected; these diameters are NOT engineering specifications.
FACE_HEAD_DIAMETER = 24.0
INTERACTION_HEAD_DIAMETER = 24.0

# Layout across the main housing (front view, looking at the -Y user side):
#   | margin | FACE HEAD | gap | INTERACTION HEAD | margin |
SENSOR_HEAD_END_MARGIN = 4.0
SENSOR_HEAD_CENTER_GAP = 4.0

# Optional explicit barrel lengths (mm). None derives a symmetric 50/50
# split of the available width (MAIN_BODY_WIDTH - 2*margin - gap) in
# resolve(). Set explicit values when the two subsystems need different
# internal volumes.
FACE_HEAD_LENGTH = None
INTERACTION_HEAD_LENGTH = None

# Independent pitch rotation of each barrel about its own X-parallel axis
# (right-hand rule about +X). 0 deg = sensor faces the user (-Y);
# +90 deg = sensor face pitched down toward the keyboard (-Z);
# -90 deg = pitched up (+Z).
FACE_HEAD_ROTATION_DEG = 0.0
INTERACTION_HEAD_ROTATION_DEG = 0.0

# Barrel axis placement relative to the main housing:
#   Y : offset of the barrel axis from the housing's user-side face (-Y).
#       0 = axis on the front face plane (barrel half embedded, half
#       protruding toward the user). Positive = outward toward the user,
#       negative = into the housing. Coarse concept-stage placement.
#   Z : offset of the barrel axis from the housing vertical centre.
SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE = 0.0
SENSOR_HEAD_AXIS_Z_OFFSET_FROM_BODY_CENTER = 0.0

# Temporary rotation-orientation marks (debug geometry, NOT product
# hardware): thin strips lying almost flush with each barrel's surface
# that rotate with the barrel, so pitch rotation is visible even though a
# plain cylinder is rotationally symmetric. The mark sits on the surface
# point facing the user (-Y) at 0 deg -- the nominal sensor facing
# direction.
ORIENTATION_MARK_LENGTH_FRACTION = 0.5   # fraction of barrel length
ORIENTATION_MARK_WIDTH = 2.0             # tangential width on the surface
ORIENTATION_MARK_THICKNESS = 0.5         # radial thickness
ORIENTATION_MARK_EMBED = 0.1             # sunk into the barrel surface


def get_params():
    """Return all build parameters as a dict of name -> value (mm)."""
    return {
        "DISPLAY_LID_THICKNESS": DISPLAY_LID_THICKNESS,
        "DISPLAY_REFERENCE_WIDTH": DISPLAY_REFERENCE_WIDTH,
        "DISPLAY_REFERENCE_HEIGHT": DISPLAY_REFERENCE_HEIGHT,
        "MAIN_BODY_WIDTH": MAIN_BODY_WIDTH,
        "MAIN_BODY_HEIGHT": MAIN_BODY_HEIGHT,
        "MAIN_BODY_DEPTH": MAIN_BODY_DEPTH,
        "MAIN_BODY_DISPLAY_OFFSET_X": MAIN_BODY_DISPLAY_OFFSET_X,
        "MAIN_BODY_DISPLAY_OFFSET_Y": MAIN_BODY_DISPLAY_OFFSET_Y,
        "MAIN_BODY_DISPLAY_OFFSET_Z": MAIN_BODY_DISPLAY_OFFSET_Z,
        "FACE_HEAD_DIAMETER": FACE_HEAD_DIAMETER,
        "INTERACTION_HEAD_DIAMETER": INTERACTION_HEAD_DIAMETER,
        "SENSOR_HEAD_END_MARGIN": SENSOR_HEAD_END_MARGIN,
        "SENSOR_HEAD_CENTER_GAP": SENSOR_HEAD_CENTER_GAP,
        "FACE_HEAD_LENGTH": FACE_HEAD_LENGTH,
        "INTERACTION_HEAD_LENGTH": INTERACTION_HEAD_LENGTH,
        "FACE_HEAD_ROTATION_DEG": FACE_HEAD_ROTATION_DEG,
        "INTERACTION_HEAD_ROTATION_DEG": INTERACTION_HEAD_ROTATION_DEG,
        "SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE":
            SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE,
        "SENSOR_HEAD_AXIS_Z_OFFSET_FROM_BODY_CENTER":
            SENSOR_HEAD_AXIS_Z_OFFSET_FROM_BODY_CENTER,
        "ORIENTATION_MARK_LENGTH_FRACTION": ORIENTATION_MARK_LENGTH_FRACTION,
        "ORIENTATION_MARK_WIDTH": ORIENTATION_MARK_WIDTH,
        "ORIENTATION_MARK_THICKNESS": ORIENTATION_MARK_THICKNESS,
        "ORIENTATION_MARK_EMBED": ORIENTATION_MARK_EMBED,
    }


def resolve(params):
    """Return a copy of `params` with derived values filled in.

    Derived today:
    - FACE_HEAD_LENGTH / INTERACTION_HEAD_LENGTH when left as None:
      a symmetric split of the width available between end margins and the
      centre gap.
    """
    p = dict(params)
    available = (p["MAIN_BODY_WIDTH"]
                 - 2.0 * p["SENSOR_HEAD_END_MARGIN"]
                 - p["SENSOR_HEAD_CENTER_GAP"])
    if p["FACE_HEAD_LENGTH"] is None:
        p["FACE_HEAD_LENGTH"] = available / 2.0
    if p["INTERACTION_HEAD_LENGTH"] is None:
        p["INTERACTION_HEAD_LENGTH"] = available / 2.0
    return p
