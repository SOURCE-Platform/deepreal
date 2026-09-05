"""USB-C female port on the arm's curved underside.

This is a PROVISIONAL Blender concept sized and placed from the Blender-native
design specification. A later manufacturing-CAD phase must reconstruct the
selected connector, retention, sealing, and wall details.

Integration language (same as the drum optics): the curved arm surface
is NOT flattened -- the panel opening is a rounded-rectangle bore cut
along the LOCAL surface normal, so the opening is slightly elliptical
on the curve and the housing's existing edge-bevel chamfers the cut.

Placement: centred horizontally (X = 0) on the quarter-circle arm's
outer (under) surface, PORT_ANGLE_DEG around the arc from the arm tip
(0 deg = tip, pointing down; 90 deg = rear corner). 30 deg is the
steepest downward-facing part of the curve, so a plugged cable drapes
straight down, clearing the laptop lid.

Anatomy (separate objects, parented to Main_Housing):
    Main_Housing_USB_Cutter   hidden boolean cutter (rounded-rect bore)
    Main_Housing_USB_Shell    recessed metal receptacle shell
    Main_Housing_USB_Cavity   dark interior behind the shell mouth
    Main_Housing_USB_Tongue   the centre tongue in the slot
"""

import math

import bpy
from mathutils import Vector

import macbook

MM = 0.001

PORT_ANGLE_DEG = 45.0   # around the arm arc from the tip (0) to rear (90);
                        # per the annotated reference: exit axis ~30 deg
                        # from vertical, tilted rearward, with the laptop
                        # open at 105 deg (was 30 -> ~15 deg from vertical)
OPENING_W = 9.2 * MM    # rounded-rect panel cut, USB-C proportions
OPENING_H = 3.4 * MM
OPENING_R = 1.6 * MM
BORE_DEPTH = 7.0 * MM

SHELL_W = 8.9 * MM      # receptacle shell (slightly inside the cut)
SHELL_H = 3.3 * MM
SHELL_R = 1.62 * MM
SHELL_IN_W = 8.3 * MM   # hollow: the slot you see into
SHELL_IN_H = 2.7 * MM
SHELL_IN_R = 1.3 * MM
SHELL_LEN = 6.0 * MM
SHELL_RECESS = 0.8 * MM

TONGUE_W = 3.6 * MM     # centre contact tongue in the slot
TONGUE_H = 0.9 * MM
TONGUE_LEN = 4.2 * MM
TONGUE_RECESS = 1.8 * MM

BACK_W = 8.5 * MM       # dark end plate at the back of the socket
BACK_H = 3.0 * MM
BACK_R = 1.4 * MM
BACK_LEN = 0.6 * MM
BACK_RECESS = 6.2 * MM


def port_frame(p):
    """Shared placement math: returns (surface_point, normal, tangent,
    inward) of the port opening, derived from the resolved arm params."""
    centre = Vector((0.0, p["REAR_ARM_MOUNT_FACE_Y"] * MM,
                     p["REAR_ARM_ARC_CENTER_Z"] * MM))
    radius = p["REAR_ARM_RADIUS"] * MM
    theta = math.radians(PORT_ANGLE_DEG)
    normal = Vector((0.0, math.sin(theta), -math.cos(theta)))
    surface = centre + radius * normal
    tangent = Vector((0.0, math.cos(theta), math.sin(theta))
                     ).normalized()
    return surface, normal, tangent, -normal


def build(manifest, mats, col):
    p = manifest["params"]
    housing = bpy.data.objects["Main_Housing"]
    surface, normal, tangent, inward = port_frame(p)

    def port_prism(name, w, h, r, depth, mouth_recess, material):
        return macbook.prism(
            name, macbook._rounded_rect_2d(w, h, r),
            surface + inward * (mouth_recess + depth / 2.0),
            macbook.X, tangent, depth, material)

    cutter = port_prism("Main_Housing_USB_Cutter", OPENING_W, OPENING_H,
                        OPENING_R, BORE_DEPTH + 1.0 * MM, -1.0 * MM, None)
    cutter.hide_viewport = True
    cutter.hide_render = True
    col.objects.link(cutter)
    cutter.parent = housing            # housing basis is identity

    mod = housing.modifiers.new("Bore_USB_C", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    mod.solver = 'EXACT'
    housing.modifiers.move(len(housing.modifiers) - 1, 0)

    # hollow stamped shell: the rounded-rect rim you see into (frame =
    # outer wall + inner wall + end rings), tin-plated so it reads as a
    # connector, not a hole
    shell = macbook.frame(
        "Main_Housing_USB_Shell",
        surface + inward * (SHELL_RECESS + SHELL_LEN / 2.0),
        macbook.X, tangent,
        (SHELL_W, SHELL_H), SHELL_R, (SHELL_IN_W, SHELL_IN_H), SHELL_IN_R,
        SHELL_LEN, mats["USB_Shell_Tin"])
    for poly in shell.data.polygons:
        poly.use_smooth = True
    col.objects.link(shell)
    shell.parent = housing

    # centre contact tongue reaching toward the mouth, gold contacts
    tongue = port_prism("Main_Housing_USB_Tongue", TONGUE_W, TONGUE_H,
                        0.0, TONGUE_LEN, TONGUE_RECESS,
                        mats["USB_Tongue_Gold"])
    col.objects.link(tongue)
    tongue.parent = housing

    # dark end plate so the socket's back reads as depth, not nylon
    back = port_prism("Main_Housing_USB_Back", BACK_W, BACK_H,
                      BACK_R, BACK_LEN, BACK_RECESS,
                      mats["Optic_Projector_Inset"])
    col.objects.link(back)
    back.parent = housing

    print("usb_port: opening on arm underside at X=0, {:.0f} deg around "
          "the arc (surface y={:.4f} z={:.4f} m, normal tilt "
          "{:.0f} deg from vertical)".format(
              PORT_ANGLE_DEG, surface.y, surface.z, 90 - PORT_ANGLE_DEG))
    return [shell, tongue, back]
