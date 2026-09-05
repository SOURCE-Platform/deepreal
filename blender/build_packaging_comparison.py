#!/usr/bin/env python3
"""Build a side-by-side DeepReal electronics packaging study.

This is deliberately separate from build_scene.py. It compares three
architecture-stage packaging envelopes without changing the canonical product
scene or pretending that open PCB, motor, shielding, and thermal decisions are
production geometry.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import macbook  # noqa: E402


MM = 0.001
SOURCE_BLEND = os.path.join(HERE, "deepreal.blend")
OUTPUT_BLEND = os.path.join(HERE, "renders",
                            "packaging-comparison.blend")
CUTAWAY_BLEND = os.path.join(HERE, "renders",
                             "packaging-comparison-cutaway.blend")
EXTERIOR_RENDER = os.path.join(HERE, "renders",
                               "packaging-comparison-exterior.png")
CUTAWAY_RENDER = os.path.join(HERE, "renders",
                              "packaging-comparison-cutaway.png")
GEAR_DETAIL_RENDER = os.path.join(HERE, "renders",
                                  "packaging-comparison-drive-gear.png")

# All three variants use the selected gear drive: an offset
# micro-gearmotor behind each drum drives a gear ring on the drum's
# outboard end. (Coaxial end-pod drive was evaluated in an earlier pass
# of this study and rejected for its ~32 mm width cost.)
# Variants are staggered diagonally (behind and to the right) so that a
# side view of one variant is never blocked by another.
VARIANTS = (
    {
        "id": "Current",
        "label": "CURRENT 120 x 30 x 24 mm\nCOMPONENT COLLISIONS",
        "offset_x": -0.20,
        "offset_y": 0.0,
        "body_mm": (120.0, 30.0, 24.0),
        "board_y": 14.0,
        "status": "collision",
    },
    {
        "id": "Compact",
        "label": "COMPACT 120 x 34 x 18 mm\nSAME WIDTH, TIGHT VERTICAL DECK",
        "offset_x": 0.20,
        "offset_y": 0.33,
        "body_mm": (120.0, 34.0, 18.0),
        "board_y": 13.5,
        "stack": "top",
        "status": "tight",
    },
)


def material(name, color, metallic=0.0, roughness=0.45, alpha=1.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if alpha < 1.0:
        mat.diffuse_color = (*color, alpha)
        try:
            mat.surface_render_method = 'DITHERED'
        except AttributeError:
            pass
    return mat


def child_collection(parent, name):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def link_only(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def transform_for(offset_x, offset_y, cad_pose):
    return Matrix.Translation((offset_x, offset_y, 0.0)) @ cad_pose


def make_box(name, center_mm, dimensions_mm, radius_mm, mat, collection,
             variant_transform):
    center = Vector(tuple(value * MM for value in center_mm))
    dx, dy, dz = (value * MM for value in dimensions_mm)
    obj = macbook.slab(name, center, macbook.X, macbook.Z, (dx, dz),
                       radius_mm * MM, dy, mat)
    link_only(obj, collection)
    obj.matrix_world = variant_transform
    return obj


def make_cylinder(name, center_mm, axis, radius_mm, length_mm, mat,
                  collection, variant_transform, segments=48):
    center = Vector(tuple(value * MM for value in center_mm))
    obj = macbook.cylinder(name, center, axis, radius_mm * MM,
                           length_mm * MM, mat, seg=segments)
    link_only(obj, collection)
    obj.matrix_world = variant_transform
    return obj


def make_wire(name, points_mm, radius_mm, mat, collection,
              variant_transform):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = radius_mm * MM
    curve.bevel_resolution = 3
    curve.materials.append(mat)
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points_mm) - 1)
    for point, coordinates in zip(spline.bezier_points, points_mm):
        local = Vector(tuple(value * MM for value in coordinates))
        point.co = variant_transform @ local
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    return obj


def duplicate_flat(original, name, collection, offset_x, offset_y):
    duplicate = original.copy()
    if original.data is not None:
        duplicate.data = original.data.copy()
    duplicate.animation_data_clear()
    duplicate.parent = None
    duplicate.matrix_parent_inverse = Matrix.Identity(4)
    duplicate.matrix_world = (
        Matrix.Translation((offset_x, offset_y, 0.0))
        @ original.matrix_world
    )
    duplicate.name = name
    collection.objects.link(duplicate)
    return duplicate


def build_variant(variant, templates, cad_pose, materials):
    root = bpy.data.collections.new("Variant_" + variant["id"])
    bpy.context.scene.collection.children.link(root)
    exterior = child_collection(root, variant["id"] + "_Exterior")
    # The enclosure gets its own collection so the whole shell (housing +
    # both drums) can be toggled with one click in the outliner.
    enclosure = child_collection(root, variant["id"] + "_Enclosure")
    internals = child_collection(root, variant["id"] + "_Internals")

    shell_names = {
        "Main_Housing",
        "Face_Sensor_Head",
        "Interaction_Sensor_Head",
    }
    shells = []
    laptop_objects = []
    for original in templates:
        target = enclosure if original.name in shell_names else exterior
        copy = duplicate_flat(
            original, variant["id"] + "_" + original.name,
            target, variant["offset_x"], variant["offset_y"])
        if not original.name.startswith(
                ("Main_Housing", "Face_", "Interaction_", "Mount_")):
            laptop_objects.append(copy)
        if original.name in shell_names:
            shells.append(copy)

    variant_transform = transform_for(
        variant["offset_x"], variant["offset_y"], cad_pose)
    width, height, depth = variant["body_mm"]
    expansion = None
    # Board level: the Current variant keeps electronics at drum height to
    # expose the collisions; expanded variants drop them into the downward
    # extension behind the laptop lid.
    board_z = 20.0
    if variant["id"] != "Current":
        # Growth goes downward behind the laptop lid, never upward. Local
        # CAD frame: lid mid-plane y=0 with the rear face at +Y, lid top
        # edge at z=0 extending downward (-Z).
        front_y = 2.0                      # clear the lid rear face (+Y)
        rear_y = front_y + depth
        top_z = 5.0                        # merges into the housing rear
        bottom_z = top_z - height          # extension hangs down behind lid
        expansion = make_box(
            variant["id"] + "_Expanded_Housing",
            (0.0, (front_y + rear_y) / 2.0,
             (bottom_z + top_z) / 2.0),
            (width, rear_y - front_y, top_z - bottom_z),
            4.0, materials["housing"], exterior, variant_transform)
        # Fuse the extension and the original bar into ONE housing solid so
        # the growth reads as part of the device, not a tacked-on box.
        housing_copy = bpy.data.objects[variant["id"] + "_Main_Housing"]
        union = housing_copy.modifiers.new("Union_Expansion", "BOOLEAN")
        union.operation = "UNION"
        union.solver = "EXACT"
        union.object = expansion
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = housing_copy
        housing_copy.select_set(True)
        bpy.ops.object.modifier_apply(modifier=union.name)
        housing_copy.select_set(False)
        bpy.data.objects.remove(expansion)
        # Deck level: Compact hugs the belly top so the wire drops from
        # the drums stay short; Reference centers the stack in its much
        # larger reserve volume.
        board_z = (top_z - 16.5 if variant["stack"] == "top"
                   else (top_z + bottom_z) / 2.0)

    status_mat = materials[variant["status"]]
    board_y = variant["board_y"]

    keepout = make_box(
        variant["id"] + "_PCBA_KeepOut_90x28x15",
        (0.0, board_y - 2.45, board_z), (90.0, 15.0, 28.0), 1.0,
        status_mat, internals, variant_transform)

    # Vertical deck, tightly sandwiched toward the drums: EMI shield |
    # chips | PCBA | heat spreader, with sub-mm gaps. The same stack is
    # used in every variant; only its placement differs (Current leaves it
    # at drum height so the collisions stay visible; the expanded variants
    # drop it into the belly behind the lid).
    board = make_box(
        variant["id"] + "_Main_PCBA",
        (0.0, board_y, board_z), (90.0, 1.6, 28.0), 0.8,
        materials["board"], internals, variant_transform)

    soc = make_box(
        variant["id"] + "_NXP_iMX95_15mm",
        (-3.0, board_y - 2.3, board_z + 1.0), (15.0, 3.0, 15.0), 0.8,
        materials["soc"], internals, variant_transform)
    fpga = make_box(
        variant["id"] + "_CrossLink_NX_FPGA",
        (-28.0, board_y - 2.1, board_z + 1.0), (13.0, 2.6, 13.0), 0.6,
        materials["fpga"], internals, variant_transform)

    for index, (x, z) in enumerate(((12.0, board_z - 4.0),
                                    (12.0, board_z + 6.0))):
        make_box(
            "{}_LPDDR_{}".format(variant["id"], index + 1),
            (x, board_y - 1.9, z), (8.0, 2.2, 6.0), 0.5,
            materials["memory"], internals, variant_transform)
    make_box(
        variant["id"] + "_eMMC",
        (27.0, board_y - 1.9, board_z - 3.0), (10.0, 2.2, 8.0), 0.5,
        materials["memory"], internals, variant_transform)
    for index, x in enumerate((27.0, 38.0)):
        make_box(
            "{}_PMIC_{}".format(variant["id"], index + 1),
            (x, board_y - 1.9, board_z + 8.0), (7.0, 2.2, 7.0), 0.4,
            materials["power"], internals, variant_transform)

    shield = make_box(
        variant["id"] + "_EMI_Shield",
        (-6.0, board_y - 5.95, board_z + 1.0), (55.0, 3.5, 24.0), 1.2,
        materials["shield"], internals, variant_transform)
    spreader = make_box(
        variant["id"] + "_Heat_Spreader",
        (0.0, board_y + 2.05, board_z), (76.0, 1.5, 30.0), 1.0,
        materials["spreader"], internals, variant_transform)

    mipi_end_y = board_y - 3.8
    if variant["id"] == "Current":
        motor_end_z = 20.0  # board at drum height: short straight run
        motor_mid_yz = (15.5, 20.0)
    else:
        motor_end_z = board_z + 13.5  # top edge of the dropped deck
        motor_mid_yz = (15.0, (20.0 + motor_end_z) / 2.0)

    # Drum drive (selected concept): an offset micro-gearmotor sits behind
    # each drum; a pinion on its shaft meshes a gear ring on the drum's
    # outboard end. The drum rotates about its own centerline on its
    # bearings; the gears only deliver torque. (Coaxial end-pod motors were
    # rejected: ~32 mm wider device and larger direct-drive motors.)
    drum_axis_y = -1.45
    drum_axis_z = 20.0
    gear_motor_y = drum_axis_y + 17.0  # pinion r4 + ring r13 mesh
    motors = []
    for side, sign in (("L", -1.0), ("R", 1.0)):
        motor = make_cylinder(
            "{}_GearDrive_Motor_{}".format(variant["id"], side),
            (sign * 46.0, gear_motor_y, drum_axis_z), macbook.X,
            4.0, 12.0, materials["motor"], internals, variant_transform)
        make_cylinder(
            "{}_GearDrive_Pinion_{}".format(variant["id"], side),
            (sign * 53.5, gear_motor_y, drum_axis_z), macbook.X,
            4.0, 3.0, materials["gearbox"], internals, variant_transform)
        make_cylinder(
            "{}_GearDrive_RingGear_{}".format(variant["id"], side),
            (sign * 53.5, drum_axis_y, drum_axis_z), macbook.X,
            13.0, 3.0, materials["gearbox"], internals, variant_transform)
        keep = make_box(
            "{}_GearDrive_Motor_KeepOut_{}".format(variant["id"], side),
            (sign * 45.0, gear_motor_y, drum_axis_z),
            (22.0, 10.0, 22.0), 1.5, status_mat, internals,
            variant_transform)
        keep.display_type = "WIRE"
        motors += [motor, keep]
        make_wire(
            "{}_Motor_Wiring_{}".format(variant["id"], side),
            ((sign * 46.0, gear_motor_y, drum_axis_z),
             (sign * 39.0, motor_mid_yz[0], motor_mid_yz[1]),
             (sign * 34.0, board_y + 0.5, motor_end_z)),
            0.55, materials["motor_wire"], internals, variant_transform)

    # Keep-out envelopes reserve space; wireframe in the viewport so they
    # never hide the parts inside them. Renders still show them translucent.
    keepout.display_type = "WIRE"

    # Four camera links converge near the capture FPGA. Motor/power wiring
    # runs separately to avoid implying a finalized harness topology.
    wire_specs = (
        ("Face_RGB", (-10.0, -5.0, 20.0),
         (-26.0, mipi_end_y, board_z + 1.6)),
        ("Face_IR", (-48.0, -5.0, 20.0),
         (-31.0, mipi_end_y, board_z + 1.6)),
        ("Interaction_RGB", (48.0, -5.0, 20.0),
         (-22.0, mipi_end_y, board_z + 1.6)),
        ("Interaction_IR", (10.0, -5.0, 20.0),
         (-25.0, mipi_end_y, board_z + 1.6)),
    )
    for name, start, end in wire_specs:
        mid = ((start[0] + end[0]) / 2.0,
               8.0, start[2] + (end[2] - start[2]) / 2.0)
        make_wire(
            "{}_MIPI_{}".format(variant["id"], name),
            (start, mid, end), 0.45, materials["mipi"], internals,
            variant_transform)

    return {
        "id": variant["id"],
        "root": root,
        "exterior": exterior,
        "internals": internals,
        "shells": shells,
        "laptop_objects": laptop_objects,
        "internal_objects": [keepout, board, soc, fpga, shield, spreader]
                            + motors,
    }


def make_label(variant, camera, mat):
    curve = bpy.data.curves.new(variant["id"] + "_Label", "FONT")
    curve.body = variant["label"]
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 10 * MM
    curve.space_line = 0.92
    curve.extrude = 0.18 * MM
    curve.bevel_depth = 0.04 * MM
    curve.materials.append(mat)
    obj = bpy.data.objects.new(variant["id"] + "_Label", curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (variant["offset_x"], variant["offset_y"] - 0.04, 0.095)
    obj.rotation_euler = (
        camera.location - obj.location
    ).to_track_quat("Z", "Y").to_euler()
    return obj


def aim(obj, point):
    obj.rotation_euler = (point - obj.location).to_track_quat("-Z", "Y").to_euler()


def set_collection_render(collection, hidden):
    for obj in list(collection.all_objects):
        obj.hide_render = hidden


def main():
    os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=SOURCE_BLEND)
    scene = bpy.context.scene
    bpy.context.view_layer.update()

    source_housing = bpy.data.objects["Main_Housing"]
    cad_pose = source_housing.matrix_world.copy()
    source_objects = list(scene.objects)
    templates = [
        obj for obj in scene.objects
        if obj.type in {"MESH", "CURVE"}
        and not obj.hide_render
        and not obj.name.startswith("USB_Plug")
        and obj.name not in {"USB_Cable", "USB_Cable_Path"}
    ]

    mats = {
        "housing": bpy.data.materials["Device_Housing_Anodized"],
        "board": material("Study_PCBA", (0.035, 0.22, 0.08), roughness=0.62),
        "soc": material("Study_iMX95", (0.92, 0.55, 0.08),
                        metallic=0.25, roughness=0.34),
        "fpga": material("Study_FPGA", (0.02, 0.48, 0.68),
                         metallic=0.15, roughness=0.36),
        "memory": material("Study_Memory", (0.035, 0.055, 0.09),
                           roughness=0.35),
        "power": material("Study_Power", (0.42, 0.17, 0.55),
                          roughness=0.42),
        "shield": material("Study_EMI_Shield", (0.55, 0.58, 0.62),
                           metallic=0.9, roughness=0.25),
        "spreader": material("Study_Heat_Spreader", (0.62, 0.22, 0.07),
                             metallic=0.9, roughness=0.28),
        "motor": material("Study_Motor", (0.58, 0.035, 0.025),
                          metallic=0.55, roughness=0.34),
        "gearbox": material("Study_Gearbox", (0.20, 0.21, 0.23),
                            metallic=0.8, roughness=0.32),
        "mipi": material("Study_MIPI", (0.95, 0.56, 0.08),
                         roughness=0.45),
        "motor_wire": material("Study_Motor_Wire", (0.72, 0.08, 0.03),
                               roughness=0.50),
        "collision": material("Study_Collision", (0.80, 0.025, 0.018),
                              roughness=0.42, alpha=0.16),
        "tight": material("Study_Tight", (0.92, 0.52, 0.02),
                          roughness=0.42, alpha=0.12),
        "reserve": material("Study_Reserve", (0.04, 0.62, 0.22),
                            roughness=0.42, alpha=0.08),
        "ghost": material("Study_Ghost_Shell", (0.10, 0.13, 0.17),
                          metallic=0.35, roughness=0.28, alpha=0.04),
        "label_current": material("Study_Label_Current",
                                  (0.95, 0.18, 0.10), roughness=0.40),
        "label_compact": material("Study_Label_Compact",
                                  (1.0, 0.62, 0.08), roughness=0.40),
        "label_reference": material("Study_Label_Reference",
                                    (0.10, 0.86, 0.34), roughness=0.40),
    }
    # Smooth transparency for the ghost shells; the dithered default reads
    # as heavy grain in close-ups.
    mats["ghost"].surface_render_method = "BLENDED"
    # In the viewport the ghost should read as a faint tinted shell rather
    # than an almost invisible outline (render alpha stays as-is).
    mats["ghost"].diffuse_color = (0.10, 0.13, 0.17, 0.22)

    variants = [
        build_variant(variant, templates, cad_pose, mats)
        for variant in VARIANTS
    ]

    for original in source_objects:
        if original.type in {"MESH", "CURVE", "CAMERA", "LIGHT"}:
            original.hide_render = True
            original.hide_set(True)

    camera_data = bpy.data.cameras.new("Packaging_Comparison_Camera")
    camera_data.lens = 50
    camera = bpy.data.objects.new("Packaging_Comparison_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (-0.45, -1.20, 0.35)
    aim(camera, Vector((0.0, 0.16, -0.03)))
    scene.camera = camera

    labels = [
        make_label(
            variant, camera,
            mats["label_" + variant["id"].lower()])
        for variant in VARIANTS
    ]

    world = scene.world or bpy.data.worlds.new("Packaging_Comparison_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (
        0.012, 0.014, 0.019, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.10
    scene.world = world

    study_lights = []
    for name, location, energy, size, color in (
        ("Study_Key", (-0.50, -0.55, 0.65), 180, 0.9,
         (1.0, 0.94, 0.86)),
        ("Study_Fill", (0.58, -0.25, 0.40), 90, 0.8,
         (0.74, 0.84, 1.0)),
        ("Study_Rim", (0.0, 0.42, 0.55), 220, 0.7,
         (0.72, 0.82, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        light = bpy.data.objects.new(name, data)
        light.location = location
        aim(light, Vector((0.0, 0.0, -0.07)))
        scene.collection.objects.link(light)
        study_lights.append(light)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 2400
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.render.film_transparent = False

    # Exterior comparison: packaging internals are hidden.
    for built in variants:
        set_collection_render(built["internals"], True)
    scene.render.filepath = EXTERIOR_RENDER
    bpy.ops.render.render(write_still=True)

    # Technical comparison: ghost the housing/drums and reveal all reserves.
    for built in variants:
        set_collection_render(built["internals"], False)
        for laptop_obj in built["laptop_objects"]:
            laptop_obj.hide_render = True
        for shell in built["shells"]:
            shell["Study_Original_Materials"] = ",".join(
                material.name for material in shell.data.materials
                if material is not None)
            shell.data.materials.clear()
            shell.data.materials.append(mats["ghost"])
    camera_data.lens = 43
    camera.location = (-0.01, -0.85, 0.22)
    aim(camera, Vector((-0.02, 0.22, 0.02)))
    scene.render.resolution_y = 1000
    scene.render.filepath = CUTAWAY_RENDER
    bpy.ops.render.render(write_still=True)

    # Gear-drive close-up: one drum end with ghosted shells, so the torque
    # path into the drum (motor -> pinion -> ring gear) is unambiguous.
    for label in labels:
        label.hide_render = True
    by_id = {built["id"]: built for built in variants}

    def show_only(subject):
        for built in variants:
            set_collection_render(built["root"], True)
        set_collection_render(subject["root"], False)
        for laptop_obj in subject["laptop_objects"]:
            laptop_obj.hide_render = True
        # Keep-out envelopes clutter close-ups; they reserve space but hide
        # no real part, so drop them from the detail view.
        keepout_names = [o.name for o in subject["root"].all_objects
                         if "KeepOut" in o.name]
        for obj_name in keepout_names:
            bpy.data.objects[obj_name].hide_render = True
        print("Detail {}: hid {} keep-outs".format(
            subject["id"], len(keepout_names)))

    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    # An orthographic engineering-section view reads more clearly than
    # perspective for explaining the torque path.
    camera_data.type = "ORTHO"

    show_only(by_id["Compact"])
    # Oblique engineering view from outboard and the user side, framed in
    # the device's own upright frame: the ring gear reads as a disc fixed
    # to the drum end, with the pinion and the red motor body beside it.
    def world_center(obj):
        local = sum((Vector(corner) for corner in obj.bound_box),
                    Vector()) / 8.0
        return obj.matrix_world @ local

    ring_center = world_center(
        bpy.data.objects["Compact_GearDrive_RingGear_L"])
    motor_center = world_center(
        bpy.data.objects["Compact_GearDrive_Motor_L"])
    target = ring_center * 0.6 + motor_center * 0.4
    # Nearly axial with a slight user-side offset: the ring gear reads as
    # a disc (its band and annulus show past the drum rim), while the
    # parallax separates the red motor body from the pinion in front of it.
    cam_pos = target + Vector((-0.09, -0.025, 0.008))
    back = (cam_pos - target).normalized()
    up_hint = (cad_pose.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    right = up_hint.cross(back).normalized()
    cam_up = back.cross(right)
    camera.matrix_world = Matrix.Translation(cam_pos) @ Matrix(
        (right, cam_up, back)).transposed().to_4x4()
    camera_data.ortho_scale = 0.08
    scene.render.filepath = GEAR_DETAIL_RENDER
    bpy.ops.render.render(write_still=True)
    camera_data.type = "PERSP"

    # Save an inspection file in the cutaway state: ghosted see-through
    # shells, internals visible, laptops and keep-outs tucked away.
    for built in variants:
        set_collection_render(built["root"], False)
        for laptop_obj in built["laptop_objects"]:
            laptop_obj.hide_render = True
            laptop_obj.hide_set(True)
        for obj in list(built["root"].all_objects):
            if "KeepOut" in obj.name:
                obj.hide_render = True
                obj.hide_set(True)
    for label in labels:
        label.hide_render = False
    # The camera and studio lights only exist to make the PNG renders;
    # their gizmos clutter interactive inspection, so hide them in the
    # viewport in both saved files (renders are unaffected).
    for rig_obj in study_lights + [camera]:
        rig_obj.hide_set(True)
    camera_data.lens = 43
    camera.location = (-0.01, -0.85, 0.22)
    aim(camera, Vector((-0.02, 0.22, 0.02)))
    scene.render.resolution_x = 2400
    scene.render.resolution_y = 1000
    bpy.ops.wm.save_as_mainfile(filepath=CUTAWAY_BLEND)

    # Save the main file in the easier-to-understand exterior state. The
    # named per-variant collections still allow the internals to be shown.
    for built in variants:
        for obj in list(built["root"].all_objects):
            obj.hide_set(False)
        set_collection_render(built["internals"], True)
        for laptop_obj in built["laptop_objects"]:
            laptop_obj.hide_render = False
        for shell in built["shells"]:
            material_names = shell.get("Study_Original_Materials", "").split(",")
            shell.data.materials.clear()
            for material_name in material_names:
                if material_name:
                    shell.data.materials.append(bpy.data.materials[material_name])
    camera_data.lens = 50
    camera.location = (-0.45, -1.20, 0.35)
    aim(camera, Vector((0.0, 0.16, -0.03)))
    scene.render.resolution_x = 2400
    scene.render.resolution_y = 1200
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print("Saved comparison blend:", OUTPUT_BLEND)
    print("Saved cutaway blend:", CUTAWAY_BLEND)
    print("Saved exterior render:", EXTERIOR_RENDER)
    print("Saved cutaway render:", CUTAWAY_RENDER)


if __name__ == "__main__":
    main()
