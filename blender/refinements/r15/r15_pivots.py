"""Parent each drum's rotating assembly to an inspectable travel pivot."""

import bpy

MM = 0.001


def rotating_parts(side):
    prefix = side + "_"
    named = {side + "_Sensor_Head",
             side + "_Rear_Access_Cover_REMOVABLE_CONCEPT",
             side + "_Head_PCBA_Carrier_CONCEPT",
             side + "_Head_Flex_Connector_PROXY",
             side + "_Ring_Gear", side + "_Drum_Axle",
             side + "_Encoder_Magnet",
             side + "_Sensor_Head_Flat_End_"
             + ("Right" if side == "Face" else "Left")}
    return [obj for obj in bpy.data.objects
            if obj.name.startswith(prefix)
            and (obj.name in named
                 or obj.name.startswith(prefix + "Drum_Lens_")
                 or obj.get("R14_Assembly") ==
                 side + " rotating drum assembly")]


def build(scene):
    collection = bpy.data.collections.new(
        "08 — DRUM TRAVEL PIVOTS — 150 DEGREE STUDY")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    pivots = []
    for side, sign, base in (("Face", -1, 0.0),
                             ("Interaction", 1, 45.0)):
        pivot = bpy.data.objects.new(
            side + "_Rotating_Drum_Pivot_R15", None)
        collection.objects.link(pivot)
        pivot.empty_display_type = "CIRCLE"
        pivot.empty_display_size = 3.0 * MM
        pivot.location = (sign * 26.75 * MM, -1.5 * MM, 20 * MM)
        pivot.rotation_mode = "XYZ"
        pivot.lock_rotation[1] = True
        pivot.lock_rotation[2] = True
        pivot["R15_Current_Optical_Direction_deg"] = base
        pivot["R15_Allowed_Optical_Direction_deg"] = [-75.0, 75.0]
        pivot["R15_Pivot_X_Range_deg"] = [-75.0 - base, 75.0 - base]
        pivot["R15_Status"] = (
            "kinematic limit for review; physical hard-stop design open")
        bpy.context.view_layer.update()
        for obj in rotating_parts(side):
            obj.parent = pivot
            obj.matrix_parent_inverse = pivot.matrix_world.inverted()
        bpy.context.view_layer.update()
        pivots.append(pivot)
    return pivots
