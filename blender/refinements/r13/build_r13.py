#!/usr/bin/env python3
"""Open a visible center seam between the two R12 drum bodies."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "r12" / "deepreal-exterior-refinement-r12.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r13.blend"
HALF_BODY_GAP = 0.5 / 1000  # mm to Blender meters, per drum
AXIAL_TOLERANCE = 0.00001 / 1000


def shorten_inner_end(name, new_end_x):
    drum = bpy.data.objects[name]
    drum.data = drum.data.copy()
    inverse = drum.matrix_world.inverted()
    edited = 0
    for vertex in drum.data.vertices:
        world = drum.matrix_world @ vertex.co
        if abs(world.x) < AXIAL_TOLERANCE:
            world.x = new_end_x
            vertex.co = inverse @ world
            edited += 1
    assert edited == 128, (name, edited)
    drum.data.update()
    drum["R13_Center_Seam"] = (
        "inner body end shortened 0.5 mm; nominal body gap 1.0 mm; "
        "mechanical running clearance unvalidated")
    return edited


def move_inner_face(name, new_anchor_x):
    obj = bpy.data.objects[name]
    world = obj.matrix_world.copy()
    world.translation = Vector((new_anchor_x,
                                world.translation.y,
                                world.translation.z))
    obj.matrix_world = world
    obj["R13_Center_Seam"] = (
        "flat visual end face now outside its shortened drum body; "
        "no overlap with opposing face")


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    shorten_inner_end("Face_Sensor_Head", -HALF_BODY_GAP)
    shorten_inner_end("Interaction_Sensor_Head", HALF_BODY_GAP)
    # Each presentation face is 0.24 mm thick. Keeping its inner side flush
    # with the new drum end leaves 0.52 mm between the two visible faces.
    move_inner_face("Face_Sensor_Head_Flat_End_Right", -HALF_BODY_GAP)
    move_inner_face("Interaction_Sensor_Head_Flat_End_Left", HALF_BODY_GAP)
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R13"
    scene["DeepReal_Status"] = (
        "1.0 mm nominal drum-body gap, 0.52 mm visible-face gap; "
        "engineering readiness BLOCKED")
    scene["R13_Center_Gap_mm"] = 1.0
    scene["R13_Visible_Face_Gap_mm"] = 0.52
    scene["R13_Limits"] = (
        "appearance study; bearing clearance, thermal expansion, runout, "
        "assembly tolerance and drum-end construction unverified")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R13 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
