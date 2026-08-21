"""Parametric MacBook Air (M2-generation 13.6" chassis, silver) for the
DeepReal render scene.

Built entirely in bpy in METERS, in the CAD's world coordinate system:
origin at the centre of the lid's top edge on the lid mid-plane, lid
extending downward (-Z), screen facing the user (-Y), +X to the user's
right. The lid cross-section is LOCKED to the exported CAD reference
slab (width/height/thickness from the manifest params) so the DeepReal
device's laptop-lid pocket visually captures this lid exactly.

Dimensions follow the published Apple chassis numbers (304.1 x 215 mm,
11.3 mm closed), except the lid thickness which follows the CAD
reference (3.0 mm measured) so the pocket fit reads correctly; the deck
thickness absorbs the difference (11.3 - 3.0).

Everything is simple analytic geometry (rounded-rect slabs, frames,
cylinders) via bmesh -- no modifiers left live on objects except where
applied during construction. The module is import-safe; call build().

Constant-ish dimensions that are internal to the MacBook (not shared
with the CAD) are normalised to meters here.
"""

import math

import bmesh
import bpy
from mathutils import Vector

MM = 0.001

# --- chassis (m); lid W/H/T come from manifest params in build() -------
DECK_THICKNESS = 11.3 * MM - 3.0 * MM   # closed total minus lid thickness
CORNER_RADIUS = 10.0 * MM               # chassis corner radius
EDGE_BEVEL = 1.4 * MM                   # visible edge rounding

# --- screen assembly ----------------------------------------------------
GLASS_INSET = 4.5 * MM        # black glass inset from the lid edge
GLASS_RADIUS = 8.0 * MM
ACTIVE_INSET = 10.5 * MM      # lit area inset from the lid edge
ACTIVE_RADIUS = 5.0 * MM
GLASS_FRONT_RECESS = 0.3 * MM  # glass sits this far behind the lid front
NOTCH_SIZE = (18.0 * MM, 4.5 * MM)

# --- keyboard (unit = key pitch) ---------------------------------------
KEY_PITCH = 19.0 * MM
CAP_SIZE = 17.1 * MM          # 0.9 u keycap
CAP_HEIGHT = 1.3 * MM
FN_ROW_H = 0.6                # function-row key height in units
WELL_MARGIN = 3.0 * MM
KB_BACK_GAP = 10.0 * MM       # keyboard well to deck rear edge

# rows of (width in units); heights: row 0 is FN_ROW_H, others 1 u.
# Each row sums to 14.5 u (standard ANSI/MacBook width).
KEY_ROWS = (
    [1.0] * 13 + [1.5],                       # ` 1..0 - =  delete
    [1.5] + [1.0] * 12 + [1.0],               # tab  q..]  \
    [1.75] + [1.0] * 11 + [1.75],             # caps  a..'  return
    [2.25] + [1.0] * 10 + [2.25],             # shift  z../  shift
    [1.0, 1.0, 1.0, 1.0, 4.5, 1.0, 1.0,       # fn ctrl opt cmd space cmd opt
     1.0, 1.0, 1.0, 1.0],                     # arrows
)

# --- trackpad -----------------------------------------------------------
TRACKPAD_SIZE = (120.0 * MM, 80.0 * MM)
TRACKPAD_GAP = 8.0 * MM        # gap from keyboard well front edge
TRACKPAD_RADIUS = 6.0 * MM

# --- misc ---------------------------------------------------------------
HINGE_RADIUS = 2.8 * MM
HINGE_LENGTH = 272.0 * MM
FOOT_RADIUS = 4.8 * MM
FOOT_HEIGHT = 1.2 * MM

X = Vector((1.0, 0.0, 0.0))
Y = Vector((0.0, 1.0, 0.0))
Z = Vector((0.0, 0.0, 1.0))


def _rounded_rect_2d(w, h, r, seg=12):
    """CCW outline of a w x h rounded rectangle, centred, in 2D."""
    hw, hh = w / 2.0, h / 2.0
    r = max(0.0, min(r, hw, hh))
    if r < 1e-9:
        return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    pts = []
    for cx, cy, a0 in ((hw - r, hh - r, 0.0),
                       (-hw + r, hh - r, 90.0),
                       (-hw + r, -hh + r, 180.0),
                       (hw - r, -hh + r, 270.0)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90.0 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _mesh_from_bmesh(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _recalc(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def _extrude_outline(bm, center, u, v, outline, thickness):
    """Vertices of an outline extruded +/- thickness/2 along u x v.

    Returns (top_ring, bottom_ring); +n = u.cross(v) side is 'top'.
    """
    n = u.cross(v)
    top, bot = [], []
    half = thickness / 2.0
    for (x, y) in outline:
        base = center + u * x + v * y
        top.append(bm.verts.new(base + n * half))
        bot.append(bm.verts.new(base - n * half))
    return top, bot


def prism(name, outline, center, u, v, thickness, material=None):
    """Extrude an arbitrary CCW 2D outline [(x, y), ...] into a closed
    prism: quad side walls, n-gon caps. Outline lives in the (u, v)
    plane; thickness along u x v. Shared by slab() and by device.py
    (which feeds it the CAD Main_Housing profile)."""
    bm = bmesh.new()
    top, bot = _extrude_outline(bm, center, u, v, outline, thickness)
    count = len(outline)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    _recalc(bm)
    return _finish_object(name, _mesh_from_bmesh(name, bm), material)


def slab(name, center, u, v, size, radius, thickness, material=None):
    """Rounded-rectangle slab centred at `center`, size (along u, v),
    thickness along u x v."""
    outline = _rounded_rect_2d(size[0], size[1], radius)
    return prism(name, outline, center, u, v, thickness, material)


def frame(name, center, u, v, outer, outer_r, inner, inner_r, thickness,
          material=None):
    """Slab with a rounded-rect through-hole: outer (w,h), inner (w,h)."""
    bm = bmesh.new()
    o_out = _rounded_rect_2d(outer[0], outer[1], outer_r)
    o_in = _rounded_rect_2d(inner[0], inner[1], inner_r)
    ot, ob = _extrude_outline(bm, center, u, v, o_out, thickness)
    it, ib = _extrude_outline(bm, center, u, v, o_in, thickness)
    count = len(o_out)
    assert count == len(o_in), "outline segment counts must match"
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((ot[i], ob[i], ob[j], ot[j]))      # outer wall
        bm.faces.new((it[i], it[j], ib[j], ib[i]))      # inner wall
        bm.faces.new((ot[i], ot[j], it[j], it[i]))      # top annulus
        bm.faces.new((ob[i], ib[i], ib[j], ob[j]))      # bottom annulus
    _recalc(bm)
    return _finish_object(name, _mesh_from_bmesh(name, bm), material)


def cylinder(name, center, axis, radius, length, material=None, seg=48):
    bm = bmesh.new()
    ref = X if abs(axis.dot(X)) < 0.9 else Y
    u = ref.cross(axis).normalized()
    v = axis.cross(u).normalized()
    half = length / 2.0
    top, bot = [], []
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        p = center + u * (radius * math.cos(a)) + v * (radius * math.sin(a))
        top.append(bm.verts.new(p + axis * half))
        bot.append(bm.verts.new(p - axis * half))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    _recalc(bm)
    return _finish_object(name, _mesh_from_bmesh(name, bm), material)


def _finish_object(name, me, material):
    obj = bpy.data.objects.new(name, me)
    if material is not None:
        me.materials.append(material)
    return obj


def _apply_bevel(obj, width, segments=4, angle_limit=40.0):
    """Apply a bevel modifier in place (headless-safe). Non-fatal on
    failure: the object simply keeps sharp edges."""
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(angle_limit)
    # modifier_apply needs the object in the scene and active; link it
    # to the master collection temporarily if it is not linked anywhere.
    temp_linked = False
    if obj.name not in bpy.context.scene.collection.all_objects:
        bpy.context.scene.collection.objects.link(obj)
        temp_linked = True
    try:
        bpy.context.view_layer.objects.active = obj
        with bpy.context.temp_override(object=obj, active_object=obj,
                                       selected_objects=[obj]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as exc:
        print("macbook: bevel failed on {} ({}), keeping sharp edges".format(
            obj.name, exc))
        try:
            obj.modifiers.remove(mod)
        except Exception:
            pass
    finally:
        if temp_linked:
            bpy.context.scene.collection.objects.unlink(obj)


def build(params, mats, col_lid, col_deck):
    """Build the MacBook. Returns (lid_objects, deck_objects): everything
    in lid_objects must follow the lid when it swings (parent them to the
    scene's lid pivot); deck_objects stay with the chassis."""
    p = params
    lid_w = p["DISPLAY_REFERENCE_WIDTH"] * MM
    lid_h = p["DISPLAY_REFERENCE_HEIGHT"] * MM
    lid_t = p["DISPLAY_LID_THICKNESS"] * MM
    alu = mats["MacBook_Aluminium"]

    lid, deck = [], []

    # ---- lid: aluminium frame + recessed black glass + active screen ----
    lid_frame = frame("MacBook_Lid", Vector((0, 0, -lid_h / 2)), X, Z,
                      (lid_w, lid_h), CORNER_RADIUS,
                      (lid_w - 2 * GLASS_INSET, lid_h - 2 * GLASS_INSET),
                      GLASS_RADIUS, lid_t, alu)
    lid_front = -lid_t / 2.0
    glass_front = lid_front + GLASS_FRONT_RECESS  # behind the alu bezel
    glass_t = lid_t + 2 * GLASS_FRONT_RECESS  # fills the hole completely
    glass = slab("MacBook_Screen_Glass",
                 Vector((0, glass_front + glass_t / 2.0, -lid_h / 2)), X, Z,
                 (lid_w - 2 * GLASS_INSET, lid_h - 2 * GLASS_INSET),
                 GLASS_RADIUS, glass_t, mats["MacBook_Screen_Glass"])
    # The lid's front face is the -Y side, so a slab's -Y face sits at
    # center - t/2: place centres at (target_front + t/2).
    active_t = 0.2 * MM
    active = slab("MacBook_Screen_Active",
                  Vector((0, glass_front - 0.05 * MM + active_t / 2.0,
                          -lid_h / 2)), X, Z,
                  (lid_w - 2 * ACTIVE_INSET, lid_h - 2 * ACTIVE_INSET),
                  ACTIVE_RADIUS, active_t, mats["MacBook_Screen_Active"])
    notch_t = 0.2 * MM
    notch = slab("MacBook_Notch",
                 Vector((0, glass_front - 0.02 * MM + notch_t / 2.0,
                         -lid_h / 2 + (lid_h - 2 * ACTIVE_INSET) / 2
                         - NOTCH_SIZE[1] / 2)), X, Z,
                 NOTCH_SIZE, 1.2 * MM, notch_t, mats["MacBook_Keyboard_Well"])
    lid += [lid_frame, glass, active, notch]

    # ---- deck: aluminium slab, keyboard well, keycaps, trackpad ---------
    deck_top = -lid_h                      # flush with the lid bottom edge
    deck_rear = lid_t / 2.0                # closed lid sits exactly on deck
    deck_c = Vector((0, deck_rear - 215.0 * MM / 2.0,
                     deck_top - DECK_THICKNESS / 2.0))
    deck_obj = slab("MacBook_Deck", deck_c, X, Y,
                    (lid_w, 215.0 * MM), CORNER_RADIUS, DECK_THICKNESS, alu)
    deck.append(deck_obj)

    total_units = sum(KEY_ROWS[0])
    kb_w = total_units * KEY_PITCH
    rows_h = [FN_ROW_H] + [1.0] * (len(KEY_ROWS) - 1)
    kb_h = sum(rows_h) * KEY_PITCH
    well = slab("MacBook_Keyboard_Well",
                Vector((0, deck_rear - KB_BACK_GAP - kb_h / 2.0,
                        deck_top + 0.08 * MM / 2.0)), X, Y,
                (kb_w + 2 * WELL_MARGIN, kb_h + 2 * WELL_MARGIN),
                2.0 * MM, 0.08 * MM, mats["MacBook_Keyboard_Well"])
    deck.append(well)

    # one shared keycap mesh, scaled per key
    cap_tpl = slab("KeycapTemplate", Vector((0, 0, 0)), X, Y,
                   (CAP_SIZE, CAP_SIZE), 1.2 * MM, CAP_HEIGHT,
                   mats["MacBook_Keycap"])
    _apply_bevel(cap_tpl, 0.45 * MM, segments=3)
    cap_mesh = cap_tpl.data
    bpy.data.objects.remove(cap_tpl, do_unlink=True)

    y_back = deck_rear - KB_BACK_GAP
    for r, (row, rh) in enumerate(zip(KEY_ROWS, rows_h)):
        cursor = -kb_w / 2.0
        for k, units in enumerate(row):
            width = units * KEY_PITCH - 1.9 * MM
            obj = bpy.data.objects.new("Key_r{}c{}".format(r, k), cap_mesh)
            obj.location = (cursor + units * KEY_PITCH / 2.0,
                            y_back - (sum(rows_h[:r]) + rh / 2.0) * KEY_PITCH,
                            deck_top + 0.08 * MM + CAP_HEIGHT / 2.0)
            obj.scale = (width / CAP_SIZE,
                         (rh * KEY_PITCH - 1.9 * MM) / CAP_SIZE, 1.0)
            deck.append(obj)
            cursor += units * KEY_PITCH

    well_front = deck_rear - KB_BACK_GAP - kb_h - WELL_MARGIN
    tp_c = Vector((0, well_front - TRACKPAD_GAP - TRACKPAD_SIZE[1] / 2.0,
                   deck_top + 0.1 * MM / 2.0))
    deck.append(slab("MacBook_Trackpad", tp_c, X, Y, TRACKPAD_SIZE,
                     TRACKPAD_RADIUS, 0.1 * MM, mats["MacBook_Trackpad"]))

    # ---- hinge + feet ----------------------------------------------------
    deck.append(cylinder("MacBook_Hinge", Vector((0, 1.2 * MM,
                                                  deck_top - 0.5 * MM)),
                         X, HINGE_RADIUS, HINGE_LENGTH,
                         mats["MacBook_Hinge"]))
    deck_cy = deck_rear - 215.0 * MM / 2.0
    deck_bot = deck_top - DECK_THICKNESS
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            deck.append(cylinder(
                "MacBook_Foot{}{}".format(int(sx), int(sy)),
                Vector((sx * 128.0 * MM, deck_cy + sy * 86.0 * MM,
                        deck_bot - FOOT_HEIGHT / 2.0)),
                Z, FOOT_RADIUS, FOOT_HEIGHT, mats["MacBook_Foot"], seg=24))

    # ---- finish: bevel the large slabs, link to collections --------------
    for obj in (lid_frame, deck_obj):
        _apply_bevel(obj, EDGE_BEVEL)

    for obj in lid:
        col_lid.objects.link(obj)
    for obj in deck:
        col_deck.objects.link(obj)
    return lid, deck
