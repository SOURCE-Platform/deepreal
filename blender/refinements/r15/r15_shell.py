"""Cut removable rear service panels from the two R14 drum shells."""

import math

import bpy
from mathutils import Vector

import macbook

MM = 0.001
AXIS_Y_MM = -1.5
AXIS_Z_MM = 20.0


def _bake(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = bpy.data.meshes.new_from_object(evaluated)
    obj.modifiers.clear()
    obj.data = mesh


def _wedge(name, side, angle_deg, width_deg, inset_mm):
    # Rear quarter of the rotating body. Interaction's optical front already
    # points 45 degrees down, so its opposite rear is rotated with it.
    half = width_deg / 2.0
    outline = [(0.0, 0.0)]
    for index in range(33):
        theta = math.radians(180.0 - half + width_deg * index / 32.0)
        y = -20.0 * math.cos(theta)
        z = 20.0 * math.sin(theta)
        turn = math.radians(angle_deg)
        outline.append((y * math.cos(turn) - z * math.sin(turn),
                        y * math.sin(turn) + z * math.cos(turn)))
    x_center = -26.75 if side == "Face" else 26.75
    length = 48.5 - 2.0 * inset_mm
    obj = macbook.prism(name,
                        [(y * MM, z * MM) for y, z in outline],
                        Vector((x_center * MM, AXIS_Y_MM * MM,
                                AXIS_Z_MM * MM)),
                        macbook.Y, macbook.Z, length * MM)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _boolean(target, cutter, operation):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    modifier = target.modifiers.new("R15_Rear_Access", "BOOLEAN")
    modifier.operation = operation
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    target.select_set(False)
    bpy.data.objects.remove(cutter, do_unlink=True)


def build(scene, interaction_opening_deg=45.0):
    covers = bpy.data.collections.new(
        "01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS")
    scene.collection.children.link(covers)
    covers.color_tag = "COLOR_05"
    created = []
    for side, base_angle in (("Face", 0.0),
                             ("Interaction", interaction_opening_deg)):
        shell = bpy.data.objects[side + "_Sensor_Head"]
        _bake(shell)
        cover = shell.copy()
        cover.data = shell.data.copy()
        cover.name = side + "_Rear_Access_Cover_REMOVABLE_CONCEPT"
        covers.objects.link(cover)
        cut = _wedge(side + "_Opening_Cutter", side, base_angle, 90.0, 0)
        _boolean(shell, cut, "DIFFERENCE")
        panel_cut = _wedge(side + "_Cover_Cutter", side,
                           base_angle, 88.4, 0.24)
        _boolean(cover, panel_cut, "INTERSECT")
        shell["R15_Rear_Opening"] = (
            "90-degree rear quarter aperture, 48.5 mm nominal axial length; "
            "removable cover fitted in normal use")
        shell["R15_Opening_Angle_At_Saved_Pose_deg"] = base_angle
        cover["R15_Access_Status"] = (
            "visual removable shell section; seam, seal, fasteners and "
            "structural stiffness unverified")
        cover["R15_Rotating_Assembly"] = side
        created.append(cover)
    return covers, created
