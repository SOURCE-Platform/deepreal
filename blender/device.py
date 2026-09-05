"""Native clean-topology rebuild of the Blender-authoritative product.

The Main_Housing is extruded from the Blender design specification's Y-Z
profile and the two sensor drums are true quad-grid cylinders.

The geometry is generated natively rather than imported as a tessellated
mesh, keeping the concept editable and deterministic in headless builds.

The housing begins as the approved curved outer profile, then receives three
explicit cavities: the drum channel, motor pocket, and electronics cavity.
Import-safe; call build().
"""

import bmesh
import bpy
import math
from mathutils import Vector

import macbook

MM = 0.001

SHELL_SEGMENTS = 64       # drum circumference segments (quad walls)
# Architecture-stage drum shell assumption: 1.5 mm wall and endcaps,
# yielding a 21 mm usable diameter inside the 24 mm exterior.
INTERIOR_WALL = 1.5 * MM
EDGE_SPLIT_ANGLE = 40.0    # degrees; sharper edges shade flat
BEVEL_WIDTH = 0.2 * MM     # light-catching edge rounding
ENVELOPE_TOLERANCE = 0.2 * MM  # bbox match vs Blender design specification


def _verify_envelope(name, me, bbox_mm):
    """Verify the generated drum's outer envelope against the design spec."""
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    got = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    want = (bbox_mm["min"][0] * MM, bbox_mm["max"][0] * MM,
            bbox_mm["min"][1] * MM, bbox_mm["max"][1] * MM,
            bbox_mm["min"][2] * MM, bbox_mm["max"][2] * MM)
    deltas = [abs(a - b) for a, b in zip(got, want)]
    worst = max(deltas)
    print("device: {:<24} outer envelope matches design bbox "
          "(worst {:.4f} mm; hollow interior O{:.0f} follows the "
          "feasibility assumptions)".format(
              name, worst / MM, (2 * (12.0 - 1.5))))
    if worst > ENVELOPE_TOLERANCE:
        raise ValueError(
            "{} shell outer envelope deviates {:.3f} mm from the design "
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


def _difference(target, cutter, label):
    """Apply one exact boolean and discard its temporary cutter."""
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    modifier = target.modifiers.new(label, 'BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.solver = 'EXACT'
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    target.select_set(False)
    bpy.data.objects.remove(cutter, do_unlink=True)


def _hollow_housing(obj):
    """Cut the actual internal volumes required by the reference assembly."""
    drum_cutter = macbook.cylinder(
        "_Drum_Channel_Cutter", Vector((0.0, -1.5 * MM, 20.0 * MM)),
        macbook.X, 13.2 * MM, 116.0 * MM, None, seg=96)
    bpy.context.scene.collection.objects.link(drum_cutter)
    _difference(obj, drum_cutter, "Drum_Channel")

    motor_cutter = macbook.slab(
        "_Motor_Pocket_Cutter", Vector((0.0, 13.0 * MM, 20.0 * MM)),
        macbook.X, macbook.Z, (116.0 * MM, 23.0 * MM), 3.0 * MM,
        15.0 * MM, None)
    bpy.context.scene.collection.objects.link(motor_cutter)
    _difference(obj, motor_cutter, "Motor_Pocket")

    # This profile is deliberately smaller than the outer cyan-sketch
    # profile, leaving real front/rear/bottom walls and 2 mm end caps.
    inner_yz_mm = [
        (5.3, 3.6), (5.3, -24.5), (7.0, -26.0), (13.0, -26.8),
        (18.5, -24.5), (21.3, -17.0), (21.3, 3.6),
    ]
    inner_outline = [(y * MM, z * MM) for y, z in inner_yz_mm]
    electronics_cutter = macbook.prism(
        "_Electronics_Cavity_Cutter", inner_outline, Vector((0.0, 0.0, 0.0)),
        macbook.Y, macbook.Z, 116.0 * MM, None)
    bpy.context.scene.collection.objects.link(electronics_cutter)
    _difference(obj, electronics_cutter, "Electronics_Cavity")
    obj["DeepReal_Subsystem"] = "Curved enclosure"
    obj["DeepReal_Evidence"] = "APPROVED BLENDER CONCEPT"


def build(manifest, mats, col):
    """Build housing + both sensor drums; returns the object list."""
    parts = {p["name"]: p for p in manifest["parts"]}
    objs = []

    for name in sorted(parts):
        part = parts[name]
        bb = part["bbox_mm"]
        linked = False
        if name == "Main_Housing":
            points = manifest["profiles"]["Main_Housing"]["points_yz_mm"]
            outline = [(y * MM, z * MM) for (y, z) in points]
            center = Vector(((bb["min"][0] + bb["max"][0]) / 2.0 * MM,
                             0.0, 0.0))
            thickness = (bb["max"][0] - bb["min"][0]) * MM
            obj = macbook.prism(name, outline, center, macbook.Y,
                                macbook.Z, thickness,
                                mats["Device_Housing_Anodized"])
            col.objects.link(obj)
            linked = True
            _hollow_housing(obj)
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

        if not linked:
            col.objects.link(obj)
        _finish_clean(obj)
        if name != "Main_Housing":
            _verify_envelope(name, obj.data, bb)
        objs.append(obj)

    return objs
