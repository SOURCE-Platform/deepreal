"""Geometry helpers for the self-contained DeepReal R04 refinement."""

import copy
import math

import bpy
from mathutils import Matrix, Vector

import device
import macbook

MM = 0.001
OUTER_CENTER = (3.5, -10.0)
OUTER_RADIUS = 19.0
INNER_CENTER = (5.0, -10.0)
INNER_RADIUS = 16.0


def _quarter_arc(center, radius, steps=24):
    cy, cz = center
    return [
        (cy + radius * math.cos(math.radians(angle)),
         cz + radius * math.sin(math.radians(angle)))
        for angle in (-90.0 + 90.0 * i / steps for i in range(steps + 1))
    ]


def refinement_manifest(baseline):
    """Return the straight-back R04 housing with centered vertical USB."""
    result = copy.deepcopy(baseline)
    outer = [(-1.5, 35.0), (-1.5, 5.0), (3.5, 5.0)]
    outer += _quarter_arc(OUTER_CENTER, OUTER_RADIUS)
    outer += [(22.5, 35.0)]
    inner = [(5.0, 3.6)]
    inner += _quarter_arc(INNER_CENTER, INNER_RADIUS)
    inner += [(21.0, 3.6)]
    profile = result["profiles"]["Main_Housing"]
    profile["points_yz_mm"] = [list(point) for point in outer]
    profile["inner_points_yz_mm"] = [list(point) for point in inner]
    part = next(p for p in result["parts"] if p["name"] == "Main_Housing")
    part["bbox_mm"]["min"][1:] = [min(p[0] for p in outer), min(p[1] for p in outer)]
    part["bbox_mm"]["max"][1:] = [max(p[0] for p in outer), max(p[1] for p in outer)]
    exit_y = 18.0
    delta_y = exit_y - OUTER_CENTER[0]
    exit_z = OUTER_CENTER[1] - math.sqrt(OUTER_RADIUS ** 2 - delta_y ** 2)
    result["params"].update({
        "USB_EXIT_X": 0.0,
        "USB_EXIT_SURFACE_Y": exit_y,
        "USB_EXIT_SURFACE_Z": exit_z,
        "USB_EXIT_NORMAL_Y": 0.0,
        "USB_EXIT_NORMAL_Z": -1.0,
    })
    result["authority"] = "User-directed Blender refinement R04"
    return result


def hollow_housing(obj, manifest):
    """Apply source cavities using the refined quarter-round profile."""
    drum = macbook.cylinder(
        "_Drum_Channel_Cutter", Vector((0.0, -1.5 * MM, 20.0 * MM)),
        macbook.X, 13.2 * MM, 116.0 * MM, None, seg=96)
    bpy.context.scene.collection.objects.link(drum)
    device._difference(obj, drum, "Drum_Channel")
    motor = macbook.slab(
        "_Motor_Pocket_Cutter", Vector((0.0, 13.0 * MM, 20.0 * MM)),
        macbook.X, macbook.Z, (116.0 * MM, 23.0 * MM), 3.0 * MM,
        15.0 * MM, None)
    bpy.context.scene.collection.objects.link(motor)
    device._difference(obj, motor, "Motor_Pocket")
    for label, x in (("Face", -50.5), ("Interaction", 50.5)):
        cutter = macbook.slab(
            "_{}_Cable_Passage_Cutter".format(label),
            Vector((x * MM, 10.0 * MM, 6.5 * MM)), macbook.X, macbook.Z,
            (12.0 * MM, 10.0 * MM), 1.0 * MM, 7.0 * MM, None)
        bpy.context.scene.collection.objects.link(cutter)
        device._difference(obj, cutter, label + "_Cable_Passage")
    outline = [(y * MM, z * MM) for y, z in
               manifest["profiles"]["Main_Housing"]["inner_points_yz_mm"]]
    cavity = macbook.prism(
        "_Electronics_Cavity_Cutter", outline, Vector((0.0, 0.0, 0.0)),
        macbook.Y, macbook.Z, 116.0 * MM, None)
    bpy.context.scene.collection.objects.link(cavity)
    device._difference(obj, cavity, "Electronics_Cavity")


def usb_frame(params):
    surface = Vector((params["USB_EXIT_X"] * MM,
                      params["USB_EXIT_SURFACE_Y"] * MM,
                      params["USB_EXIT_SURFACE_Z"] * MM))
    normal = Vector((0.0, params["USB_EXIT_NORMAL_Y"],
                     params["USB_EXIT_NORMAL_Z"])).normalized()
    tangent = Vector((0.0, -normal.z, normal.y)).normalized()
    return surface, normal, tangent, -normal


def append_and_shift_electronics(source_blend, target_collection):
    with bpy.data.libraries.load(str(source_blend), link=False) as (src, dst):
        if "Electronics Assembly" not in src.collections:
            raise RuntimeError("Electronics Assembly missing from source blend")
        dst.collections = ["Electronics Assembly"]
    imported = dst.collections[0]
    imported.name = target_collection.name
    bpy.context.scene.collection.children.unlink(target_collection)
    bpy.data.collections.remove(target_collection)
    bpy.context.scene.collection.children.link(imported)
    imported.hide_viewport = imported.hide_render = False
    for obj in imported.all_objects:
        obj.hide_viewport = obj.hide_render = False
        obj.hide_set(False)
        if obj.name == "Housing_Thermal_Pad":
            continue
        translation = Vector((0.0, -5.0 * MM, 0.0))
        obj.parent = None
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.location = translation
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.scale = (1.0, 1.0, 1.0)
        obj.matrix_world = Matrix.Translation(translation)
        obj["R04_Forward_Shift_mm"] = 5.0
    old_pad = bpy.data.objects.get("Housing_Thermal_Pad")
    if old_pad:
        bpy.data.objects.remove(old_pad, do_unlink=True)
    bpy.context.view_layer.update()
    return imported


def close_drum_gap(*collections):
    moved = []
    for target in collections:
        for obj in target.all_objects:
            shift = 0.0
            if obj.name.startswith("Face_"):
                shift = 2.0 * MM
            elif obj.name.startswith("Interaction_"):
                shift = -2.0 * MM
            if shift:
                obj.location.x += shift
                obj["R04_Drum_Inward_Shift_mm"] = 2.0
                moved.append(obj.name)
    return moved


def add_thermal_interface(target, materials):
    pad_material = bpy.data.materials.get("Thermal_Pad")
    if pad_material is None:
        pad_material = materials["Thermal_Pad"]
    housing_material = materials["Device_Housing_Anodized"]
    for side, x in (("Left", -18.75), ("Right", 18.75)):
        pad = macbook.slab(
            "Housing_Thermal_Pad_" + side,
            Vector((x * MM, 16.275 * MM, -11.5 * MM)), macbook.X,
            macbook.Z, (22.5 * MM, 18.0 * MM), 1.2 * MM, 1.4 * MM,
            pad_material)
        boss = macbook.slab(
            "Housing_Thermal_Boss_" + side,
            Vector((x * MM, 19.4375 * MM, -11.5 * MM)), macbook.X,
            macbook.Z, (22.5 * MM, 18.0 * MM), 1.2 * MM, 4.925 * MM,
            housing_material)
        target.objects.link(pad)
        target.objects.link(boss)
        pad["DeepReal_Status"] = "touches spreader; thermal properties unverified"
        boss["DeepReal_Status"] = "concept housing boss; manufacture unverified"


def add_usb_plug_and_cable(manifest, materials, target):
    surface, normal, tangent, _ = usb_frame(manifest["params"])
    overmold = macbook.prism(
        "USB_C_Plug_Overmold", macbook._rounded_rect_2d(9 * MM, 5 * MM, 2.2 * MM),
        surface + normal * 6.2 * MM, macbook.X, tangent, 12 * MM,
        materials["Cable_Overmold"])
    target.objects.link(overmold)
    shell = macbook.frame(
        "USB_C_Male_Metal_Shell", Vector((0.0, 18.0 * MM, -21.25 * MM)),
        macbook.X, macbook.Y, (8.35 * MM, 2.70 * MM), 1.30 * MM,
        (7.45 * MM, 1.80 * MM), 0.85 * MM, 7.50 * MM,
        materials["USB_Shell_Tin"])
    target.objects.link(shell)
    insert = macbook.slab(
        "USB_C_Male_Internal_Insert", Vector((0.0, 18.0 * MM, -21.05 * MM)),
        macbook.X, macbook.Y, (7.25 * MM, 1.68 * MM), 0.75 * MM,
        6.80 * MM, materials["Cable_Jacket"])
    target.objects.link(insert)
    tongue = macbook.slab(
        "USB_C_Male_Contact_Tongue", Vector((0.0, 17.52 * MM, -20.8 * MM)),
        macbook.X, macbook.Y, (3.6 * MM, 0.18 * MM), 0.05 * MM,
        5.8 * MM, materials["USB_Tongue_Gold"])
    target.objects.link(tongue)
    start = surface + normal * 12.2 * MM
    curve = bpy.data.curves.new("USB_C_Cable_Path", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 2.0 * MM
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    points = [start + normal * offset * MM for offset in (0, 18, 34, 52)]
    spline.bezier_points.add(len(points) - 1)
    for point, location in zip(spline.bezier_points, points):
        point.co = location
        point.handle_left_type = point.handle_right_type = "AUTO"
    curve.materials.append(materials["Cable_Jacket"])
    cable = bpy.data.objects.new("USB_C_Cable", curve)
    target.objects.link(cable)


def frame_viewports(target=(0.0, 0.004, 0.002), distance=0.19):
    front = (math.sqrt(0.5), math.sqrt(0.5), 0.0, 0.0)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            region = space.region_3d
            region.view_location = Vector(target)
            region.view_distance = distance
            region.view_rotation = front
            region.view_perspective = "PERSP"
            space.lens = 50.0
            space.overlay.show_relationship_lines = False
