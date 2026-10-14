"""Material-aware candidate review, never a live viewer or engineering signoff.

Run in an empty Blender process with DEEPREAL_WEB_ASSEMBLY_OUT pointing to
an isolated GLB. JPEG views are saved beside it without editing the source.
"""

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_camera_mount import camera_frame

asset = Path(os.environ["DEEPREAL_WEB_ASSEMBLY_OUT"])
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(asset))
objects = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH"}
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 95
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.035, .035, .035, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .4
scene.view_settings.view_transform = "AgX"
camera_data = bpy.data.cameras.new("Optical_Support_Review")
camera = bpy.data.objects.new(camera_data.name, camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = "ORTHO"
camera_data.clip_start = .0001
camera_data.clip_end = 2
lights = []
for index in range(3):
    data = bpy.data.lights.new(f"Support_Light_{index}", "AREA")
    data.energy = .15
    data.shape = "DISK"
    data.size = .05
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    lights.append(obj)

for side in ("Face", "Interaction"):
    for name, obj in objects.items():
        obj.hide_render = not (
            name.startswith((f"WEB_{side}_RGB_", f"WEB_{side}_Head_Board_Spacer_",
                             f"WEB_{side}_Optics_"))
            or name.startswith(side + "_") and any(token in name for token in (
                "Head_PCBA_", "Head_Flex_Connector", "Internal_Optical_Carrier",
                "RGB_Module", "RGB_Wide", "IR_Depth", "SL_Projector")))
    frame = camera_frame(objects, side)
    for view, eye in (("front", (-24, 5, 65)), ("oblique", (-30, 28, 35))):
        focus = frame @ (Vector((-23, 0, 0)) * .001)
        camera.location = frame @ (Vector(eye) * .001)
        camera.rotation_euler = (focus - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.ortho_scale = .061
        for light, local in zip(lights, ((-20, 25, 50), (15, 30, -45), (-45, -20, -30))):
            light.location = frame @ (Vector(local) * .001)
            light.rotation_euler = (focus - light.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(asset.parent / f"{side.lower()}-support-{view}.jpg")
        bpy.ops.render.render(write_still=True)
