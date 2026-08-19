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
#   X : horizontal offset of the housing centre from the display centre
#   Y/Z : None = derived from the laptop-lid pocket relationships below:
#       Y : the housing's front (user-side) face sits
#           MAIN_BODY_LID_FRONT_OFFSET behind the lid's front face
#           (0 = flush; the housing extends rearward from there and is
#           NOT centred on the lid thickness)
#       Z : the housing bottom face sits MAIN_BODY_LID_TOP_CLEARANCE
#           above the lid top edge (the lid never supports the body by
#           simple contact)
# Set explicit numbers only to detach the housing from the pocket
# relationships (not recommended).
MAIN_BODY_DISPLAY_OFFSET_X = 0.0
MAIN_BODY_DISPLAY_OFFSET_Y = None
MAIN_BODY_DISPLAY_OFFSET_Z = None

# ---------------------------------------------------------------------------
# Laptop-lid pocket (Phase 3): the fused housing + rear arm forms a
# receiving pocket that captures the top edge of the laptop lid
# ---------------------------------------------------------------------------
# The lid's top edge slides UP into the slot bounded above by the housing
# bottom face and at the rear by the arm's vertical mounting face. The
# future magnetic mounting stack (Phase 4) will secure the device in this
# region. All values provisional; tuned visually.
MAIN_BODY_LID_TOP_CLEARANCE = 5.0   # housing bottom sits this far above the
                                    # lid top edge (= lid insertion depth)
MAIN_BODY_LID_FRONT_OFFSET = 0.0    # housing front face sits this far behind
                                    # the lid's front face (0 = planes flush)
LAPTOP_LID_POCKET_CLEARANCE = 2.0   # gap between the lid rear face and the
                                    # arm's vertical mounting face

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
# Nominal orientations per the geometry specification: the face drum looks
# forward at the user; the interaction drum is pitched downward (the
# original 3/4 concept sketch is the authority). 45 deg is a PROVISIONAL
# angle, not a locked design value.
FACE_HEAD_ROTATION_DEG = 0.0
INTERACTION_HEAD_ROTATION_DEG = 45.0

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

# ---------------------------------------------------------------------------
# Rear arm (Phase 3): the rectangular body + quarter-circle mounting arm
# + laptop-lid pocket are ONE coherent Y-Z side profile, extruded along X
# across the full device width into the single Main_Housing solid
# ---------------------------------------------------------------------------
# Per the annotated review screenshots, the arm hangs BELOW the
# rectangular body: its true quarter-circle arc meets the housing exactly
# at the bottom-rear corner, TANGENT to the rear face, so the silhouette
# is one continuous enclosure -- no embedded arm top edge, no crossover
# point on the rear face, no horizontal splitter seam, no boolean
# artifacts. The vertical flat mounting face (facing the lid) forms the
# rear wall of the laptop-lid pocket; the Phase 4 magnet/plate/foam-tape
# stack will sit on it. The long thin line descending from the arm in the
# original sketches is the USB-C cable -- it is NOT part of the arm and
# is not modelled yet.
#
# The arm position is DERIVED, never placed independently: the mounting
# face sits LAPTOP_LID_POCKET_CLEARANCE behind the lid rear face and the
# arc centre sits exactly on the housing bottom plane at that Y, so
# moving the housing or the lid reference carries the arm along.
#
# ALL values below are PROVISIONAL concept proportions; none are
# production dimensions.

REAR_ARM_RADIUS = None         # None = derived: the arc meets the housing
                               # exactly at its bottom-rear corner (radius
                               # = the housing depth behind the mounting
                               # face). Set a number to override: a
                               # smaller arc tucks under the housing and
                               # leaves a flat bottom strip behind it.


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
        "MAIN_BODY_LID_TOP_CLEARANCE": MAIN_BODY_LID_TOP_CLEARANCE,
        "MAIN_BODY_LID_FRONT_OFFSET": MAIN_BODY_LID_FRONT_OFFSET,
        "LAPTOP_LID_POCKET_CLEARANCE": LAPTOP_LID_POCKET_CLEARANCE,
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
        "REAR_ARM_RADIUS": REAR_ARM_RADIUS,
    }


def _derive_housing_offsets(p):
    """Fill in None housing offsets from the lid-pocket relationships."""
    if p["MAIN_BODY_DISPLAY_OFFSET_Y"] is None:
        # Front faces flush: the housing's front (user-side) face sits on
        # the lid's front plane plus MAIN_BODY_LID_FRONT_OFFSET; the
        # housing extends rearward from there.
        lid_front_y = -p["DISPLAY_LID_THICKNESS"] / 2.0
        p["MAIN_BODY_DISPLAY_OFFSET_Y"] = (
            lid_front_y
            + p["MAIN_BODY_LID_FRONT_OFFSET"]
            + p["MAIN_BODY_DEPTH"] / 2.0)
    if p["MAIN_BODY_DISPLAY_OFFSET_Z"] is None:
        # The housing bottom floats MAIN_BODY_LID_TOP_CLEARANCE above the
        # lid top edge (Z=0): the lid enters the pocket and never
        # supports the body by simple contact.
        p["MAIN_BODY_DISPLAY_OFFSET_Z"] = p["MAIN_BODY_LID_TOP_CLEARANCE"]
    return p


def resolve(params):
    """Return a copy of `params` with derived values filled in.

    Derived today:
    - FACE_HEAD_LENGTH / INTERACTION_HEAD_LENGTH when left as None:
      a symmetric split of the width available between end margins and the
      centre gap.
    - MAIN_BODY_DISPLAY_OFFSET_Y/Z when left as None: the housing front
      face flushes with the lid's front plane and the housing bottom
      floats MAIN_BODY_LID_TOP_CLEARANCE above the lid top edge.
    - REAR_ARM_* quarter-disk profile points (Y-Z plane) from the pocket,
      housing and arm parameters, with guardrails that reject impossible
      or pocket-breaking geometry.
    """
    p = dict(params)
    available = (p["MAIN_BODY_WIDTH"]
                 - 2.0 * p["SENSOR_HEAD_END_MARGIN"]
                 - p["SENSOR_HEAD_CENTER_GAP"])
    if p["FACE_HEAD_LENGTH"] is None:
        p["FACE_HEAD_LENGTH"] = available / 2.0
    if p["INTERACTION_HEAD_LENGTH"] is None:
        p["INTERACTION_HEAD_LENGTH"] = available / 2.0

    # --- Phase 3: housing placement derives from the lid pocket ---
    p = _derive_housing_offsets(p)
    housing_front_y = (p["MAIN_BODY_DISPLAY_OFFSET_Y"]
                       - p["MAIN_BODY_DEPTH"] / 2.0)
    housing_rear_y = (p["MAIN_BODY_DISPLAY_OFFSET_Y"]
                      + p["MAIN_BODY_DEPTH"] / 2.0)
    housing_bot_z = p["MAIN_BODY_DISPLAY_OFFSET_Z"]
    housing_top_z = housing_bot_z + p["MAIN_BODY_HEIGHT"]
    lid_rear_y = p["DISPLAY_LID_THICKNESS"] / 2.0

    # --- Phase 3: derived rear-arm quarter-circle profile (Y-Z plane) ---
    # The arm hangs below the body. The arc centre C sits exactly ON the
    # housing bottom plane, LAPTOP_LID_POCKET_CLEARANCE behind the lid's
    # rear face. From C, one straight radius edge runs toward -Z (the
    # vertical mounting face, ending at the arm's bottom tip) and the
    # circular arc of REAR_ARM_RADIUS sweeps from that tip up/rearward to
    # the profile's rear-bottom corner, meeting the housing rear face
    # tangentially at the corner -- the corrected lower connection from
    # the annotated review screenshots.
    p["REAR_ARM_MOUNT_FACE_Y"] = (lid_rear_y
                                  + p["LAPTOP_LID_POCKET_CLEARANCE"])
    if p["REAR_ARM_RADIUS"] is None:
        # The arc meets the housing exactly at its bottom-rear corner:
        # radius = the housing depth behind the mounting face.
        p["REAR_ARM_RADIUS"] = (housing_rear_y
                                - p["REAR_ARM_MOUNT_FACE_Y"])
    p["REAR_ARM_ARC_CENTER_Z"] = housing_bot_z
    p["REAR_ARM_REAR_Y"] = (p["REAR_ARM_MOUNT_FACE_Y"]
                            + p["REAR_ARM_RADIUS"])
    p["REAR_ARM_BOTTOM_Z"] = (p["REAR_ARM_ARC_CENTER_Z"]
                              - p["REAR_ARM_RADIUS"])
    p["REAR_ARM_HOUSING_BOTTOM_Z"] = housing_bot_z

    # Guardrails: reject impossible or pocket-breaking geometry loudly
    # instead of building a broken shape.
    if p["MAIN_BODY_LID_TOP_CLEARANCE"] < 0.5:
        raise ValueError("MAIN_BODY_LID_TOP_CLEARANCE must be >= 0.5 mm "
                         "(the housing must float above the lid top edge)")
    if p["LAPTOP_LID_POCKET_CLEARANCE"] < 0.5:
        raise ValueError("LAPTOP_LID_POCKET_CLEARANCE must be >= 0.5 mm")
    if p["REAR_ARM_MOUNT_FACE_Y"] < housing_front_y + 1.0:
        raise ValueError("no room for the pocket: the arm's mounting face "
                         "must sit at least 1 mm behind the housing front "
                         "face (check MAIN_BODY_DEPTH / "
                         "MAIN_BODY_LID_FRONT_OFFSET / lid thickness)")
    if p["REAR_ARM_RADIUS"] < 2.0:
        raise ValueError("REAR_ARM_RADIUS must be >= 2 mm")
    if p["REAR_ARM_REAR_Y"] > housing_rear_y + 1e-9:
        raise ValueError("REAR_ARM_RADIUS too large: the arc would pass "
                         "the housing rear face (max radius = housing "
                         "rear Y - mounting face Y)")
    if p["REAR_ARM_BOTTOM_Z"] > -1.0:
        raise ValueError("REAR_ARM_RADIUS too small: the arm tip must sit "
                         "at least 1 mm below the lid top edge to capture "
                         "it (radius must exceed MAIN_BODY_LID_TOP_"
                         "CLEARANCE + 1 mm)")
    if p["REAR_ARM_BOTTOM_Z"] <= -p["DISPLAY_REFERENCE_HEIGHT"]:
        raise ValueError("REAR_ARM_RADIUS too large: the arm would reach "
                         "past the bottom of the display reference")
    # The pocket must stay clear: sensor head barrels may not dip below
    # the housing bottom face (the pocket's ceiling).
    head_axis_z = (housing_bot_z + p["MAIN_BODY_HEIGHT"] / 2.0
                   + p["SENSOR_HEAD_AXIS_Z_OFFSET_FROM_BODY_CENTER"])
    head_r = (max(p["FACE_HEAD_DIAMETER"], p["INTERACTION_HEAD_DIAMETER"])
              / 2.0)
    if head_axis_z - head_r < housing_bot_z:
        raise ValueError("sensor heads would break through the pocket "
                         "ceiling (head barrels must stay at/above the "
                         "housing bottom face)")
    return p
