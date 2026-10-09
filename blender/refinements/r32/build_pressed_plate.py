#!/usr/bin/env python3
"""Build the taller DeepReal laptop target plate with a softly pressed logo."""

import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "r31"))
sys.path.insert(0, str(HERE.parents[1]))

import build_mount_plate as base  # noqa: E402
import design_spec  # noqa: E402
import macbook  # noqa: E402
import materials  # noqa: E402
import pressed_plate_mesh as pressed  # noqa: E402

MM = .001
MODEL = HERE / "deepreal-pressed-logo-plate-review-r32.blend"
RENDER_PREFIX = "r32"


def render(scene, cam, name, width, height):
    scene.camera = cam
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = str(HERE / name)
    bpy.ops.render.render(write_still=True)
    print(RENDER_PREFIX.upper(), "RENDER", scene.render.filepath)


def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = f"DeepReal Pressed Laptop Target Plate {RENDER_PREFIX.upper()}"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 192
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "AgX"
    scene.world = bpy.data.worlds.new("Charcoal Product Studio")
    scene.world.color = (.085, .105, .125)
    scene.render.resolution_percentage = 100
    return scene


def create_product():
    mats = materials.build_all()
    laptop_col = base.collection("01 — LAPTOP REAR VIEW")
    hidden_col = base.collection("02 — ORIGINAL INTERIOR (HIDDEN)")
    mount_col = base.collection("03 — TALL PLATE AND FOAM")
    studio_col = base.collection("04 — PRODUCT CAMERAS AND LIGHTS")
    params = design_spec.manifest()["params"]
    old_lid, _deck = macbook.build(params, mats, hidden_col, laptop_col)
    for obj in old_lid:
        obj.hide_render = True
        obj.hide_set(True)
    lid = base.add_slab("Laptop_Continuous_Aluminium_Back",
                        (0, 0, -107.5 * MM), (304.1 * MM, 215 * MM),
                        10 * MM, 3 * MM, mats["MacBook_Aluminium"],
                        laptop_col)
    lid["Reference"] = "3 mm visual laptop proxy"
    foam = base.add_slab("Replaceable_Foam_Adhesive_Sticker",
                         (0, 1.7 * MM, pressed.Z_CENTER * MM),
                         (109 * MM, 23 * MM), 1.3 * MM, .4 * MM,
                         base.material("Warm_Grey_Foam", (.07, .075, .08),
                                       0, .9), mount_col)
    steel = base.material("Pressed_Satin_Ferritic_Steel",
                          (.14, .17, .19), .58, .42)
    plate, logo_height = pressed.build(base.svg_strokes(), steel, mount_col)
    plate["Art_Source"] = str(base.SVG)
    foam["Concept_Only"] = True
    print(RENDER_PREFIX.upper(), "PLATE", pressed.WIDTH, pressed.HEIGHT,
          "LOGO", pressed.LOGO_WIDTH, round(logo_height, 2))
    return studio_col


def setup_studio(col):
    target = (0, pressed.FACE_Y * MM, pressed.Z_CENTER * MM)
    base.area_light("Broad_Upper_Softbox", (-.16, .18, .11),
                    2.0, .22, target, col)
    base.area_light("Opposite_Fill", (.19, .14, -.04),
                    1.0, .16, target, col)
    base.area_light("Low_Left_Grazing_Strip", (-.10, .018, -.013),
                    1.15, .023, target, col)
    base.area_light("High_Right_Raking_Strip", (.075, .014, .012),
                    .7, .018, target, col)
    hero = base.camera("Camera_Laptop_Back_Opens_Here",
                       (0, .45, -.103), (0, 0, -.106), .34, col)
    detail = base.camera("Camera_Tall_Plate_And_Logo",
                         (.012, .13, .013), target, .14, col)
    macro = base.camera("Camera_Groove_Shadow_Graze",
                        (.009, .075, .029),
                        (0, pressed.FACE_Y * MM, -.015),
                        .083, col)
    for cam in (hero, detail, macro):
        cam.data.clip_start = .001
    return hero, detail, macro


def main():
    scene = setup_scene()
    studio = create_product()
    hero, detail, macro = setup_studio(studio)
    scene.camera = detail
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1000
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.overlay.show_overlays = False
                area.spaces.active.shading.type = "MATERIAL"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
    render(scene, detail, f"{RENDER_PREFIX}-tall-pressed-plate.png",
           1800, 1050)
    render(scene, macro, f"{RENDER_PREFIX}-groove-shadow-detail.png",
           1800, 1000)
    render(scene, hero, f"{RENDER_PREFIX}-laptop-back.png", 1600, 1200)


if __name__ == "__main__":
    main()
