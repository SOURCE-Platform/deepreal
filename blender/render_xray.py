#!/usr/bin/env python3
"""Acceptance render: oblique WIREFRAME view of the drum packaging.

Renders deepreal.blend with the Workbench engine in wireframe shading
from an oblique three-quarter angle, so the hollow drum shells, internal
optical carriers, module bodies, PCBs and through-wall barrels are all
visible for the spec's acceptance check (run after build_scene.py):

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python blender/render_xray.py
"""

import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "deepreal.blend")
OUT = os.path.join(HERE, "renders", "xray_check.png")


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene

    # oblique 3/4 angle on the device (aimed at the tracked device target)
    target = bpy.data.objects["Device_Target"]
    cam_data = bpy.data.cameras.new("Camera_Xray")
    cam_data.lens = 60
    cam = bpy.data.objects.new("Camera_Xray", cam_data)
    cam.location = (0.16, -0.24, 0.09)
    scene.collection.objects.link(cam)
    constraint = cam.constraints.new('TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    bpy.context.view_layer.update()

    scene.camera = cam
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1440
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.type = 'WIREFRAME'
    scene.display.shading.show_object_outline = False
    scene.render.film_transparent = False
    scene.world = None if scene.world is None else scene.world

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("X-ray acceptance render:", OUT)


main()
