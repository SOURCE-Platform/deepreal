#!/usr/bin/env python3
"""Reserve a rear cable chamber and report conflicts; no route is approved."""

import json
import sys
from itertools import product
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(HERE.parent / "r08"))
from assembly_primitives import box, material  # noqa: E402
from verify_r08 import tree  # noqa: E402

SOURCE = HERE.parent / "r36/deepreal-inner-bearing-window-r36.blend"
MODEL = HERE / "deepreal-rear-cable-volume-r37.blend"
REPORT = HERE / "r37-volume-check.json"
MM = .001


def reserve(name, bounds, mat, collection):
    center = tuple((low + high) / 2 for low, high in bounds)
    size = tuple(high - low for low, high in bounds)
    obj = box(name, center, size, 0, mat, collection)
    obj["R37_Status"] = "space reservation only; not a cable or a cut"
    obj["R37_Bounds_mm"] = [list(pair) for pair in bounds]
    return obj


def overlap(a, b):
    return len(tree(a).overlap(tree(b)))


def point_inside(bvh, point):
    # Surface overlap misses one solid completely contained in another.
    origin = Vector(point)
    direction = Vector((.991, .107, .076)).normalized()
    count = 0
    for _ in range(100):
        hit, _, _, distance = bvh.ray_cast(origin, direction, 1.0)
        if hit is None:
            break
        count += 1
        origin = hit + direction * .00001
    return bool(count % 2)


def sample_points(volume):
    bounds = volume["R37_Bounds_mm"]
    return [tuple((pair[0] + (pair[1] - pair[0]) * fraction)
                    for pair, fraction in zip(bounds, fractions))
              for fractions in product((.2, .5, .8), repeat=3)]


def sampled_inside(volume, target):
    bvh = tree(target)
    return sum(point_inside(bvh, Vector(point) * MM)
               for point in sample_points(volume))


def render(scene, volumes):
    from mathutils import Vector

    cam_data = bpy.data.cameras.new("R37_Internal_Volume_View")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = .085
    cam = bpy.data.objects.new(cam_data.name, cam_data)
    scene.collection.objects.link(cam)
    cam.location = Vector((.055, -.075, .065))
    cam.rotation_euler = (Vector((-.010, .006, .020)) - cam.location).to_track_quat(
        "-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.show_shadows = True
    scene.display.shading.background_type = "WORLD"
    scene.world.color = (.12, .14, .16)
    shown = set(volumes) | {
        "Face_Inner_Bearing_Fixed_Race_ENV_R21",
        "R36_Face_Fixed_Bearing_Axial_Neck_ENV",
        "R36_Face_Inner_Race_Rear_Side_Web_ENV",
        "R36_Face_Inner_Race_Front_Side_Web_ENV",
        "R36_Face_Full_Width_Straight_Exit_ENV",
        "Face_Internal_Optical_Carrier",
        "Face_Head_PCBA_Carrier_CONCEPT",
        "Face_Center_Fed_Motor_Stator_ENV_R21",
    }
    for obj in bpy.data.objects:
        if obj.type != "CAMERA":
            obj.hide_render = obj.name not in shown
    scene.render.filepath = str(HERE / "r37-rear-volume-internal.png")
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    collection = bpy.data.collections.new("27 — R37 CABLE SPACE RESERVATION")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_05"
    passage = reserve("R37_Center_Divider_Passage_RESERVATION",
                      ((-.8, 1.2), (-1.7, 13.25), (11.5, 28.5)),
                      material("R37_Passage_Orange", (.9, .35, .07), .1, .4),
                      collection)
    chamber = reserve("R37_Rear_Service_Chamber_RESERVATION",
                      ((-26, -.2), (13, 20), (10.5, 28.5)),
                      material("R37_Chamber_Cyan", (.02, .55, .65), .1, .4),
                      collection)
    targets = (
        "R30_One_Piece_Enclosure",
        "R36_Face_Fixed_Bearing_Axial_Neck_ENV",
        "R36_Face_Inner_Race_Rear_Side_Web_ENV",
        "R36_Face_Inner_Race_Front_Side_Web_ENV",
        "Face_Internal_Optical_Carrier",
        "Face_Head_PCBA_Carrier_CONCEPT",
        "Face_Center_Fed_Motor_Stator_ENV_R21",
        "Face_Inner_Bearing_Fixed_Race_ENV_R21",
        "Face_Sensor_Head",
        "Interaction_Sensor_Head",
    )
    report = {
        "source": str(SOURCE),
        "model": str(MODEL),
        "units": "mm",
        "volumes": {},
        "status": "SPACE_RESERVATION_ONLY",
        "meaning": "Triangle intersections and 27 interior point samples identify occupied space; no boolean cut or dynamic flex is modeled.",
    }
    for volume in (passage, chamber):
        report["volumes"][volume.name] = {
            "bounds_xyz_mm": [list(pair) for pair in volume["R37_Bounds_mm"]],
            "triangle_hits": {name: overlap(volume, bpy.data.objects[name])
                              for name in targets},
            "sampled_inside_points_of_27": {
                name: sampled_inside(volume, bpy.data.objects[name])
                for name in targets},
        }
    shell_bvh = tree(bpy.data.objects["R30_One_Piece_Enclosure"])
    report["chamber_points_outside_visual_shell_mm"] = [
        list(point) for point in sample_points(chamber)
        if not point_inside(shell_bvh, Vector(point) * MM)]
    report["passage_chamber_triangle_hits"] = overlap(passage, chamber)
    report["supplier_example_not_design_limit"] = {
        "source": "https://www.we-online.com/files/pdf1/webinar-rigidflex-flexibility-cbt-en.pdf",
        "example_stack": "one flex layer, approximately 120 micrometres",
        "dynamic_inside_bend_radius_mm": ">12",
        "corresponding_180_degree_turn_diameter_mm": ">24",
        "chamber_depth_y_mm": 7,
        "chamber_height_z_mm": 18,
        "assessment": "A 180-degree rolling return cannot fit in the 7 mm depth or 18 mm height for this supplier example; actual stack and motion are undecided.",
    }
    report["notes"] = [
        "The center passage occupies the fixed divider and intersects the existing rear support web.",
        "The rear chamber mostly occupies the solid visual enclosure; a rear-upper sample lies outside its curved skin, so a rectangular cut would break through.",
        "The full-width exit strip runs along X with its width along Z. A turn toward rear Y would bend it edgewise unless a new cable topology reorients it.",
        "Mating-end thickness and width do not define the dynamic flex stack or bend radius.",
        "No load path, wall thickness, dust seal, dynamic deformation, electrical performance or fatigue has been validated.",
    ]
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    scene.name = "DeepReal Rear Cable Space Reservation R37"
    scene["R37_Engineering_Status"] = report["status"]
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
    render(scene, {passage.name, chamber.name})
    print("R37 SAVED", MODEL)
    print("R37 REPORT", REPORT)


if __name__ == "__main__":
    main()
