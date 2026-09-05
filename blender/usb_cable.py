"""USB-C cable assembly (render-side, provisional).

Plugged male USB-C connector in the arm's receptacle -> 0.5 m cable
that drapes down behind the lid, swings left under the deck and rises
to the MacBook's left-side USB-C port, where the second male connector
hovers PORT_GAP short of it (aimed at the port, deliberately NOT
plugged in, per spec).

Everything is parented to Main_Housing with baked CAD-world
coordinates, so the assembly follows the device; the drape shape is
authored for the current 105 deg laptop opening (a big lid-angle change
would want the path regenerated).

Shares the port placement math with usb_port.py; run after it.
"""

import bpy
from mathutils import Vector

import macbook
import usb_port

MM = 0.001

CABLE_OD = 4.0 * MM
CABLE_LENGTH = 0.5           # m, nominal (checked at build, +/- 3 cm)

PLUG_SHELL_W = 8.2 * MM      # male shell (slides into the receptacle)
PLUG_SHELL_H = 2.5 * MM
PLUG_SHELL_R = 1.2 * MM
OVERMOLD_W = 9.0 * MM        # strain-relief boot
OVERMOLD_H = 5.0 * MM
OVERMOLD_LEN = 12.0 * MM

PORT_GAP = 30.0 * MM         # hover distance: plug tip to laptop port

# drape control points (world m), excluding the start point. The first
# points continue the plug axis (~30 deg from vertical, rearward, per
# the annotated reference: yellow lines) before a large-radius sweep
# down-left behind the deck to the laptop's left-side port.
_DRAPE = [
    (0.000, 0.1013, -0.0744),
    (0.006, 0.1160, -0.1080),
    (-0.025, 0.0880, -0.1630),
    (-0.085, 0.0350, -0.2200),
    (-0.160, -0.0200, -0.2470),
    (-0.220, -0.0580, -0.2330),
]


def _prism_along(name, w, h, r, length, center, direction, material):
    """Rounded-rect prism extruded along `direction` (any axis)."""
    ref = macbook.X if abs(direction.dot(macbook.X)) < 0.9 else macbook.Y
    u = ref
    v = direction.cross(ref).normalized()
    return macbook.prism(name, macbook._rounded_rect_2d(w, h, r),
                         center, u, v, length, material)


def build(manifest, mats, col):
    p = manifest["params"]
    surface, normal, tangent, _inward = usb_port.port_frame(p)
    housing = bpy.data.objects["Main_Housing"]

    def add(obj):
        col.objects.link(obj)
        obj.parent = housing           # identity basis: follows the device
        return obj

    # ---- connector A: plugged into the receptacle ------------------------
    shell_a = macbook.prism(
        "USB_Plug_A_Shell", macbook._rounded_rect_2d(PLUG_SHELL_W,
                                                     PLUG_SHELL_H,
                                                     PLUG_SHELL_R),
        surface + normal * (1.0 * MM - 5.5 * MM / 2.0),
        macbook.X, tangent, 5.5 * MM, mats["USB_Shell_Tin"])
    for poly in shell_a.data.polygons:
        poly.use_smooth = True
    add(shell_a)

    overmold_a = _prism_along(
        "USB_Plug_A_Overmold", OVERMOLD_W, OVERMOLD_H, 2.2 * MM,
        OVERMOLD_LEN, surface + normal * (1.0 * MM + OVERMOLD_LEN / 2.0),
        normal, mats["Cable_Overmold"])
    for poly in overmold_a.data.polygons:
        poly.use_smooth = True
    add(overmold_a)

    # ---- cable: beveled curve, draped to the laptop's left-side port -----
    # laptop port anchor from the manifest params + macbook constants
    lid_w = p["DISPLAY_REFERENCE_WIDTH"] * MM
    port_face_x = -lid_w / 2.0
    port_y = macbook.SIDE_PORT_Y[0]
    port_z = -p["DISPLAY_REFERENCE_HEIGHT"] * MM - macbook.DECK_THICKNESS / 2.0

    start = surface + normal * (1.0 * MM + OVERMOLD_LEN)
    plug_total = OVERMOLD_LEN + 6.5 * MM + PORT_GAP
    end = Vector((port_face_x - plug_total, port_y, port_z))
    points = ([tuple(start)] + _DRAPE
              + [tuple(end - Vector((35.0 * MM, 0.0, 0.0))), tuple(end)])

    curve = bpy.data.curves.new("USB_Cable_Path", 'CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)

    def fill(coords):
        for bp, pt in zip(spline.bezier_points, coords):
            bp.co = pt
            bp.handle_left_type = bp.handle_right_type = 'AUTO'

    def lateral_shrink(coords, f):
        """Pull interior points (except the axis-critical first one)
        toward the start->end chord by factor f -- shortens the path
        while keeping both anchors and the exit angle."""
        a, b = Vector(coords[0]), Vector(coords[-1])
        chord = b - a
        out = [coords[0], coords[1]]
        for pt in coords[2:-1]:
            p = Vector(pt)
            t = (p - a).dot(chord) / chord.length_squared
            foot = a + t * chord
            out.append(tuple(foot + (p - foot) * f))
        out.append(coords[-1])
        return out

    fill(points)
    for f in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4):
        if f < 1.0:
            fill(lateral_shrink(points, f))
        length = spline.calc_length()
        if abs(length - CABLE_LENGTH) <= 0.02:
            break
    if abs(length - CABLE_LENGTH) > 0.03:
        raise ValueError(
            "USB cable drape measures {:.3f} m, off target {:.3f} m by "
            "{:+.0f} mm -- tune _DRAPE midpoints".format(
                length, CABLE_LENGTH, (length - CABLE_LENGTH) / MM))
    curve.bevel_depth = CABLE_OD / 2.0
    curve.bevel_resolution = 4
    curve.resolution_u = 16
    curve.materials.append(mats["Cable_Jacket"])
    cable = bpy.data.objects.new("USB_Cable", curve)
    add(cable)

    # ---- connector B: hovering at the laptop port, aimed at it -----------
    end_dir = Vector((1.0, 0.0, 0.0))   # final approach runs along +X

    overmold_b = _prism_along(
        "USB_Plug_B_Overmold", OVERMOLD_W, OVERMOLD_H, 2.2 * MM,
        OVERMOLD_LEN, end + end_dir * (OVERMOLD_LEN / 2.0), end_dir,
        mats["Cable_Overmold"])
    for poly in overmold_b.data.polygons:
        poly.use_smooth = True
    add(overmold_b)

    shell_b = _prism_along(
        "USB_Plug_B_Shell", PLUG_SHELL_W, PLUG_SHELL_H, PLUG_SHELL_R,
        6.5 * MM, end + end_dir * (OVERMOLD_LEN + 3.25 * MM), end_dir,
        mats["USB_Shell_Tin"])
    for poly in shell_b.data.polygons:
        poly.use_smooth = True
    add(shell_b)

    tip_x = end.x + OVERMOLD_LEN + 6.5 * MM
    print("usb_cable: {:.0f} mm curve (target {:.2f} m), plug B tip "
          "{:.1f} mm from the laptop port face (gap spec {:.0f} mm)".format(
              length / MM, CABLE_LENGTH, (port_face_x - tip_x) / MM,
              PORT_GAP / MM))
    return [shell_a, overmold_a, cable, overmold_b, shell_b]
