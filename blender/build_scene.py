#!/usr/bin/env python3
"""Build the Blender-native DeepReal reference scene from source.

The product dimensions live in design_spec.py.  No FreeCAD export or
generated manifest is required.  Everything is rebuilt from scratch so the
saved blend remains a generated, reproducible design artifact.

Usage (from the repository root):

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python blender/build_scene.py -- [--render]

    --render          also render the verification still to blender/renders/
    --camera NAME     hero (default) | front | device | laptop
    --samples N       Cycles samples (default 96)

"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import macbook        # noqa: E402
import materials      # noqa: E402
import mounting_stack # noqa: E402
import device         # noqa: E402
import design_spec    # noqa: E402
import electronics    # noqa: E402
import interconnect   # noqa: E402
import motion         # noqa: E402
import optics         # noqa: E402
import usb_port       # noqa: E402
import usb_cable      # noqa: E402

BLEND_PATH = os.path.join(HERE, "deepreal.blend")
RENDER_DIR = os.path.join(HERE, "renders")

OPEN_ANGLE_DEG = 105.0   # laptop opening angle (90 = lid vertical)

MM = 0.001


def _argv_flag(name, default=None):
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if name in args:
        return args[args.index(name) + 1] if default is not None else True
    return default


def _collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _aim(obj, target):
    constraint = obj.constraints.new('TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'


def _area_light(name, location, size, energy, color, target, col):
    light_data = bpy.data.lights.new(name, type='AREA')
    light_data.shape = 'DISK'
    light_data.size = size
    light_data.energy = energy
    light_data.color = color
    obj = bpy.data.objects.new(name, light_data)
    obj.location = location
    col.objects.link(obj)
    _aim(obj, target)
    return obj


def _set_default_viewport(target):
    """Save a useful close perspective instead of Blender's origin view."""
    focus = target.matrix_world.translation + Vector((0.0, 0.0, -0.010))
    eye = focus + Vector((0.13, -0.20, 0.075))
    rotation = (focus - eye).to_track_quat('-Z', 'Y')
    configured = 0
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = area.spaces.active
            region = space.region_3d
            space.lens = 50
            space.clip_start = 1 * MM
            space.clip_end = 10.0
            region.view_perspective = 'PERSP'
            region.view_location = focus
            region.view_rotation = rotation
            region.view_distance = (eye - focus).length
            configured += 1
    print("viewport: framed the complete device in {} 3D view(s)".format(
        configured))


def build():
    do_render = _argv_flag("--render")
    camera_name = _argv_flag("--camera", "hero")
    samples = int(_argv_flag("--samples", 256))

    manifest = design_spec.manifest()
    params = manifest["params"]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900 if camera_name == "front" else 1200
    scene.view_settings.view_transform = 'AgX'

    mats = materials.build_all()

    col_product = _collection("DeepReal Product")
    col_lid = _collection("MacBook Lid")
    col_deck = _collection("MacBook Deck")
    col_mount = _collection("Mounting (provisional)")
    col_rig = _collection("Render Rig (hidden)")
    col_rig.hide_viewport = True   # functional for renders, invisible in viewport

    product = device.build(manifest, mats, col_product)
    col_optics = _collection("Drum Optics")
    optics.apply_to_product(manifest, mats, col_optics)
    col_electronics = _collection("Electronics Assembly")
    product += electronics.build(col_electronics)
    col_motion = _collection("Drum Motion")
    product += motion.build(col_motion)
    col_interconnect = _collection("Interconnect Routing")
    product += interconnect.build(col_interconnect)
    lid, _deck = macbook.build(params, mats, col_lid, col_deck)
    mount = mounting_stack.build(params, mats, col_mount)
    col_usb = _collection("USB Port (provisional)")
    product += usb_port.build(manifest, mats, col_usb)
    product += usb_cable.build(manifest, mats, col_usb)

    # --- lid pivot: everything that swings with the lid -------------------
    # All product/MacBook vertices are baked in absolute product coordinates,
    # so children must be parented with matrix_parent_inverse = the pivot's
    # (translation-only) matrix at parenting time. The pivot's later
    # rotation then acts about the hinge point, T*R*T^-1, instead of about
    # the world origin.
    lid_h = params["DISPLAY_REFERENCE_HEIGHT"] * MM
    pivot = bpy.data.objects.new("Lid_Pivot", None)
    pivot.empty_display_size = 10 * MM
    pivot.location = Vector((0.0, 0.0, -lid_h))
    scene.collection.objects.link(pivot)
    bpy.context.view_layer.update()
    base = pivot.matrix_world.copy()          # rotation still zero
    base_inv = base.inverted()
    for obj in product + lid + mount:
        obj.parent = pivot
        obj.matrix_parent_inverse = base_inv

    # --- target + cameras + lights (all in the hidden rig collection) ----
    target = bpy.data.objects.new("Device_Target", None)
    target.empty_display_size = 5 * MM
    target.parent = pivot
    target.matrix_parent_inverse = base_inv
    target.location = (0.0, 0.0, 10 * MM)   # device centre, product frame
    col_rig.objects.link(target)

    pivot.rotation_euler.x = math.radians(90.0 - OPEN_ANGLE_DEG)

    cam_data = bpy.data.cameras.new("Camera_Hero")
    cam_data.lens = 60  # mm
    hero = bpy.data.objects.new("Camera_Hero", cam_data)
    hero.location = (0.13, -0.20, 0.055)   # front-right 3/4 of the device
    col_rig.objects.link(hero)
    _aim(hero, target)
    scene.camera = hero

    cam_data2 = bpy.data.cameras.new("Camera_Device")
    cam_data2.lens = 50
    device_cam = bpy.data.objects.new("Camera_Device", cam_data2)
    device_cam.location = (0.05, -0.14, 0.05)
    col_rig.objects.link(device_cam)
    _aim(device_cam, target)

    # Straight-on device study. The camera stays centered on the product
    # rather than favoring either drum, with enough margin to judge the
    # housing silhouette and optical layout.
    cam_data_front = bpy.data.cameras.new("Camera_Front")
    cam_data_front.lens = 55
    front_cam = bpy.data.objects.new("Camera_Front", cam_data_front)
    front_cam.location = (0.0, -0.18, 0.045)
    col_rig.objects.link(front_cam)
    _aim(front_cam, target)

    # whole-laptop view: aims at a fixed world point near the chassis
    # centre, not at the lid-mounted device
    laptop_target = bpy.data.objects.new("Laptop_Target", None)
    laptop_target.empty_display_size = 8 * MM
    laptop_target.location = (0.0, -0.03, -0.13)
    col_rig.objects.link(laptop_target)
    cam_data3 = bpy.data.cameras.new("Camera_Laptop")
    cam_data3.lens = 32
    laptop_cam = bpy.data.objects.new("Camera_Laptop", cam_data3)
    laptop_cam.location = (0.30, -0.44, 0.20)
    col_rig.objects.link(laptop_cam)
    _aim(laptop_cam, laptop_target)

    _area_light("Key", (-0.42, -0.20, 0.38), 0.7, 40, (1.0, 0.98, 0.95),
                target, col_rig)
    _area_light("Fill", (0.45, -0.10, 0.42), 0.8, 10, (0.85, 0.90, 1.0),
                target, col_rig)
    _area_light("Rim", (0.10, 0.45, 0.35), 0.4, 25, (1.0, 1.0, 1.0), target,
                col_rig)

    world = bpy.data.worlds.new("World")
    world.node_tree.nodes["Background"].inputs[0].default_value = \
        (0.02, 0.02, 0.022, 1.0)
    scene.world = world

    bpy.context.view_layer.update()
    _set_default_viewport(target)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("Scene built: {} objects, saved {}".format(
        len(scene.objects), BLEND_PATH))

    if do_render:
        names = {"hero": hero, "front": front_cam, "device": device_cam,
                 "laptop": laptop_cam}
        cam = names.get(camera_name, hero)
        scene.camera = cam
        os.makedirs(RENDER_DIR, exist_ok=True)
        scene.render.filepath = os.path.join(
            RENDER_DIR, "{}_001.png".format(camera_name))
        bpy.ops.render.render(write_still=True)
        print("Rendered:", scene.render.filepath)


if __name__ == "__main__":
    build()
