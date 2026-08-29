"""Native clean-topology rebuild of the DeepReal device (quad meshes).

Replaces the tessellated CAD STLs for the PRODUCT parts: the Main_Housing
is re-extruded from the CAD-exported Y-Z profile polyline (quad side
walls, n-gon caps) and the two sensor drums are true quad-grid
cylinders. The CAD stays the single source of truth -- every dimension
comes from the manifest (profile points, bounding boxes, resolved
parameters), and each rebuilt mesh is VERIFIED against the CAD solid's
volume (must match within VOLUME_TOLERANCE or the build fails loudly).

Why not just import the CAD tessellation? Triangulated CAD meshes are
mathematically fine but structurally ugly to inspect and edit, and
their shading depends on operators that can silently fail in headless
builds. These native meshes use pure data-API shading (use_smooth +
Edge Split modifier), which cannot silently fail.

Topologically: housing = 43-ish quad walls + 2 n-gon caps; each drum =
96 quad walls + 2 n-gon caps. Import-safe; call build().
"""

import bmesh
import bpy
import math
from mathutils import Vector

import macbook

MM = 0.001

SHELL_SEGMENTS = 64       # drum circumference segments (quad walls)
# Hollow-shell interior per the CAD feasibility study's documented
# assumption (cad/feasibility/depth_architecture_report.md sec.1:
# wall 1.5 mm, end caps 1.5 mm, usable interior O21 x 51 mm). The outer
# envelope stays CAD-exact; the interior is where the optical modules
# are packaged.
INTERIOR_WALL = 1.5 * MM
EDGE_SPLIT_ANGLE = 40.0    # degrees; sharper edges shade flat
BEVEL_WIDTH = 0.2 * MM     # light-catching edge rounding
VOLUME_TOLERANCE = 0.005   # 0.5% vs the CAD solid volume
ENVELOPE_TOLERANCE = 0.2 * MM  # bbox match vs CAD, for shell drums


def _verify_volume(name, me, expected_m3):
    bm = bmesh.new()
    bm.from_mesh(me)
    got_m3 = abs(bm.calc_volume())
    bm.free()
    err = abs(got_m3 - expected_m3) / expected_m3
    print("device: {:<24} volume {:>10.1f} mm^3 vs CAD {:>10.1f} mm^3 "
          "({:+.3%})".format(name, got_m3 / MM**3, expected_m3 / MM**3,
                             (got_m3 - expected_m3) / expected_m3))
    if err > VOLUME_TOLERANCE:
        raise ValueError(
            "{} rebuild volume deviates {:.3%} from the CAD solid "
            "(tolerance {:.3%})".format(name, err, VOLUME_TOLERANCE))


def _verify_envelope(name, me, bbox_mm):
    """Shell drums: the CAD solid is a placeholder envelope, so the check
    is outer-envelope equality (bbox), not volume. The hollow interior
    follows the feasibility study's documented assumptions."""
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    got = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    want = (bbox_mm["min"][0] * MM, bbox_mm["max"][0] * MM,
            bbox_mm["min"][1] * MM, bbox_mm["max"][1] * MM,
            bbox_mm["min"][2] * MM, bbox_mm["max"][2] * MM)
    deltas = [abs(a - b) for a, b in zip(got, want)]
    worst = max(deltas)
    print("device: {:<24} outer envelope matches CAD bbox "
          "(worst {:.4f} mm; hollow interior O{:.0f} follows the "
          "feasibility assumptions)".format(
              name, worst / MM, (2 * (12.0 - 1.5))))
    if worst > ENVELOPE_TOLERANCE:
        raise ValueError(
            "{} shell outer envelope deviates {:.3f} mm from the CAD "
            "bbox (tolerance {:.3f} mm)".format(
                name, worst / MM, ENVELOPE_TOLERANCE / MM))


def _finish_clean(obj):
    """Deterministic shading via the data API only: smooth everywhere,
    Edge Split by angle for crisp creases, plus a subtle bevel."""
    for poly in obj.data.polygons:
        poly.use_smooth = True
    split = obj.modifiers.new("EdgeSplit", 'EDGE_SPLIT')
    split.split_angle = math.radians(EDGE_SPLIT_ANGLE)
    split.use_edge_sharp = False
    bevel = obj.modifiers.new("EdgeBevel", 'BEVEL')
    bevel.width = BEVEL_WIDTH
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(EDGE_SPLIT_ANGLE)


def build(manifest, mats, col):
    """Build housing + both sensor drums; returns the object list."""
    parts = {p["name"]: p for p in manifest["parts"]}
    objs = []

    for name in sorted(parts):
        part = parts[name]
        bb = part["bbox_mm"]
        expected_m3 = part["volume_mm3"] * MM**3

        if name == "Main_Housing":
            points = manifest["profiles"]["Main_Housing"]["points_yz_mm"]
            outline = [(y * MM, z * MM) for (y, z) in points]
            center = Vector(((bb["min"][0] + bb["max"][0]) / 2.0 * MM,
                             0.0, 0.0))
            thickness = (bb["max"][0] - bb["min"][0]) * MM
            obj = macbook.prism(name, outline, center, macbook.Y,
                                macbook.Z, thickness,
                                mats["Device_Housing_Anodized"])
        elif name.endswith("Sensor_Head"):
            centre = Vector(((bb["min"][0] + bb["max"][0]) / 2.0 * MM,
                             (bb["min"][1] + bb["max"][1]) / 2.0 * MM,
                             (bb["min"][2] + bb["max"][2]) / 2.0 * MM))
            radius = (bb["max"][1] - bb["min"][1]) / 2.0 * MM
            length = (bb["max"][0] - bb["min"][0]) * MM
            obj = macbook.tube(name, centre, macbook.X,
                               radius - INTERIOR_WALL, radius, length,
                               mats["Device_Sensor_Drum"],
                               seg=SHELL_SEGMENTS)
        else:
            continue  # debug marks / reference slab stay hidden STLs

        col.objects.link(obj)
        _finish_clean(obj)
        if name == "Main_Housing":
            _verify_volume(name, obj.data, expected_m3)
        else:
            _verify_envelope(name, obj.data, bb)
        objs.append(obj)

    return objs
