"""One-shot viewport setup for deepreal.blend.

Run it when opening the generated scene (needs a window, so not usable
from --background builds):

    /Applications/Blender.app/Contents/MacOS/Blender \
        blender/deepreal.blend --python blender/view_setup.py

Sets every 3D viewport to the hero camera's view in SOLID shading
(bright studio viewport light, no render wait; press Z for wireframe or
rendered anytime) with camera/light gizmo overlays off, then saves once
so the layout persists for future plain opens. Re-run any time after a
pipeline rebuild (headless rebuilds cannot save viewport state).
"""

import bpy


def _setup():
    scene = bpy.context.scene
    hero = bpy.data.objects.get("Camera_Hero")
    if hero is not None:
        scene.camera = hero
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.region_3d.view_perspective = 'CAMERA'
                space.shading.type = 'SOLID'
                overlay = space.overlay
                for attr in ("show_cameras", "show_lights", "show_extras"):
                    if hasattr(overlay, attr):
                        setattr(overlay, attr, False)
    bpy.ops.wm.save_mainfile()
    print("view_setup: camera view + solid shading set and saved")


_setup()
