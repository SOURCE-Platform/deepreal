"""PROVISIONAL render-only magnetic mounting stack (Phase 4 preview).

The magnetic mounting stack is NOT modelled in the FreeCAD CAD yet
(cad/README.md lists it as intentionally absent until Phase 4). These
are render-side placeholder solids sized entirely from the exported CAD
manifest parameters, so they always sit in the right place relative to
the real geometry -- but their thicknesses/footprints are visual guesses,
not engineering. When CAD Phase 4 lands, delete this module and export
the real parts through cad/export_blender.py instead.

Stack layout across the laptop-lid pocket (all driven by manifest
params, nothing hand-placed):

    [arm mounting face  Y = REAR_ARM_MOUNT_FACE_Y]
      magnet plate      0.90 mm  (device side, nickel)
      air gap           0.35 mm
      steel plate       0.35 mm  (laptop side, keeper)
      foam tape         0.40 mm  (3M double-sided, on the lid rear face)
    [lid rear face      Y = DISPLAY_LID_THICKNESS / 2]

    0.90 + 0.35 + 0.35 + 0.40 = 2.00 mm = LAPTOP_LID_POCKET_CLEARANCE

The device-side magnet plate must be parented to the lid pivot along
with the CAD product (it rides the arm); the laptop-side plate + tape
glue to the lid rear face and follow the lid too. Everything this
module builds is therefore lid-side; build() returns one list.
"""

import bpy
from mathutils import Vector

import macbook

MM = 0.001

MAGNET_THICKNESS = 0.90 * MM
AIR_GAP = 0.35 * MM
STEEL_THICKNESS = 0.35 * MM
TAPE_THICKNESS = 0.40 * MM

PLATE_WIDTH = 40.0 * MM     # along X
PLATE_TOP_INSET = 1.0 * MM  # plate top below the lid top edge (Z = 0)
PLATE_HEIGHT = 12.0 * MM    # along Z, inside the pocket's contact band
PLATE_RADIUS = 0.8 * MM


def build(params, mats, col):
    """Build the mounting stack; returns the list of lid-side objects."""
    p = params
    lid_rear = p["DISPLAY_LID_THICKNESS"] / 2.0 * MM
    mount_face = p["REAR_ARM_MOUNT_FACE_Y"] * MM
    arm_bottom = p["REAR_ARM_BOTTOM_Z"] * MM   # pocket floor side (Z)

    z_top = -PLATE_TOP_INSET
    z_center = z_top - PLATE_HEIGHT / 2.0

    objs = []

    # Device side: magnet plate on the arm's vertical mounting face.
    magnet_center_y = mount_face - MAGNET_THICKNESS / 2.0
    objs.append(macbook.slab(
        "Mount_Magnet_Plate", Vector((0, magnet_center_y, z_center)),
        macbook.X, macbook.Z, (PLATE_WIDTH, PLATE_HEIGHT), PLATE_RADIUS,
        MAGNET_THICKNESS, mats["Mount_Magnet_Nickel"]))

    # Laptop side: foam tape on the lid rear face, steel plate on the tape.
    tape_center_y = lid_rear + TAPE_THICKNESS / 2.0
    objs.append(macbook.slab(
        "Mount_Foam_Tape", Vector((0, tape_center_y, z_center)),
        macbook.X, macbook.Z, (PLATE_WIDTH, PLATE_HEIGHT), PLATE_RADIUS,
        TAPE_THICKNESS, mats["Mount_Foam_Tape"]))
    steel_center_y = lid_rear + TAPE_THICKNESS + STEEL_THICKNESS / 2.0
    objs.append(macbook.slab(
        "Mount_Steel_Plate", Vector((0, steel_center_y, z_center)),
        macbook.X, macbook.Z, (PLATE_WIDTH, PLATE_HEIGHT), PLATE_RADIUS,
        STEEL_THICKNESS, mats["Mount_Steel_Plate"]))

    # Sanity: the full stack (magnet + air + steel + tape) must span
    # exactly the pocket between the lid rear face and the arm face.
    span = mount_face - lid_rear
    expected = (MAGNET_THICKNESS + AIR_GAP + STEEL_THICKNESS
                + TAPE_THICKNESS)
    if abs(span - expected) > 1e-6:
        print("mounting_stack: WARNING stack span {:.4f} m != expected "
              "{:.4f} m (params changed?)".format(span, expected))

    # The plate must stay inside the arm's mounting-face band.
    if z_top < arm_bottom + 0.5 * MM:
        print("mounting_stack: WARNING plate top Z {:.4f} dips below the "
              "arm tip Z {:.4f}".format(z_top, arm_bottom))

    for obj in objs:
        col.objects.link(obj)
    return objs
