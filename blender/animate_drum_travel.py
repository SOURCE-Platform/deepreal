"""Render a looping clip of both drums sweeping their full travel.

The architecture locks useful drum rotation at roughly 140-160 deg total,
so this animates each drum pivot +/-80 deg about its centerline: one stop,
through center, to the other stop, and back.

Two staging notes, both applied in-memory only (the .blend is not saved):

- In the canonical scene the drum SHELL is the pivot's parent, so spinning
  the pivot would rotate only the optics and the bore cutters. The real
  device rotates the whole drum as one rigid body, so this script
  re-parents each shell under its pivot before keyframing.
- A perfectly smooth cylinder's rotation is invisible, so a small witness
  mark is added to each drum skin to make the sweep readable.

Run from the repository root:

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python blender/animate_drum_travel.py

Output: blender/renders/drum-travel-extremes.mp4 (4 s loop at 24 fps).
"""

import math
import os

import bpy
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "deepreal.blend")
OUTPUT = os.path.join(HERE, "renders", "drum-travel-extremes.mp4")

TRAVEL_DEG = 80.0       # each way from centre; ~160 deg total
FRAME_END = 97          # frame 49 is the far stop


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene

    pivots = [obj for obj in bpy.data.objects
              if obj.name.endswith("_Optics_Pivot")]
    if len(pivots) != 2:
        raise RuntimeError("Expected 2 optics pivots, found: "
                           + ", ".join(obj.name for obj in pivots))

    scene.frame_start = 1
    scene.frame_end = FRAME_END
    scene.render.fps = 24

    witness_mat = bpy.data.materials.new("Travel_Witness")
    witness_mat.use_nodes = True
    bsdf = witness_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 0.15, 0.05, 1.0)
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.15, 0.05, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 3.0

    for pivot in pivots:
        # Reparent the drum shell under the pivot so the whole drum spins
        # as one rigid body (shell, apertures, optics), like the hardware.
        shell = pivot.parent
        pivot_world = pivot.matrix_world.copy()
        if shell is not None:
            shell_world = shell.matrix_world.copy()
            pivot.parent = None
            pivot.matrix_world = pivot_world
            shell.parent = pivot
            shell.matrix_world = shell_world

        # Witness mark on the drum skin, near one end and clear of the
        # apertures, so the rotation is visible on the featureless skin.
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0015,
                                            depth=0.0008)
        mark = bpy.context.active_object
        mark.name = pivot.name.replace("_Optics_Pivot", "_Travel_Witness")
        mark.data.materials.append(witness_mat)
        mark.parent = pivot
        mark.matrix_parent_inverse = Matrix.Identity(4)
        mark.location = (0.024, -0.0118, 0.0)
        mark.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    for pivot in pivots:
        base = pivot.rotation_euler.x
        pivot.animation_data_clear()
        for frame, sign in ((1, -1.0), (49, 1.0), (FRAME_END, -1.0)):
            pivot.rotation_euler.x = base + math.radians(TRAVEL_DEG) * sign
            pivot.keyframe_insert("rotation_euler", index=0, frame=frame)
        pivot.rotation_euler.x = base

    cameras = [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    device_cam = next((cam for cam in cameras
                       if "device" in cam.name.lower()), scene.camera)
    scene.camera = device_cam

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = OUTPUT
    bpy.ops.render.render(animation=True)
    print("Saved animation:", OUTPUT)


if __name__ == "__main__":
    main()
