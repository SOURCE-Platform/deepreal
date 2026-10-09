#!/usr/bin/env python3
"""Build a separate laptop-back study of the DeepReal magnetic target plate."""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

import design_spec  # noqa: E402
import macbook  # noqa: E402
import materials  # noqa: E402

MM = .001
SVG = HERE / "assets/deepreal-logo-v0.svg"
MODEL = HERE / "deepreal-logo-mount-plate-review-r31.blend"
PLATE_WIDTH = 110 * MM
PLATE_HEIGHT = 16 * MM
PLATE_Z = -10 * MM
LID_REAR_Y = 1.5 * MM
TAPE_THICKNESS = .4 * MM
PLATE_THICKNESS = .35 * MM
PLATE_FACE_Y = LID_REAR_Y + TAPE_THICKNESS + PLATE_THICKNESS


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def material(name, color, metallic, roughness):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return result


def dark_mark_material():
    result = bpy.data.materials.new("Dark_Laser_Logo")
    result.diffuse_color = (.008, .014, .018, 1)
    result.use_nodes = True
    nodes = result.node_tree.nodes
    nodes.clear()
    mark = nodes.new("ShaderNodeEmission")
    mark.inputs["Color"].default_value = (.008, .014, .018, 1)
    output = nodes.new("ShaderNodeOutputMaterial")
    result.node_tree.links.new(mark.outputs["Emission"],
                               output.inputs["Surface"])
    return result


def add_slab(name, center, size, radius, thickness, mat, col):
    obj = macbook.slab(name, Vector(center), macbook.X, macbook.Z,
                       size, radius, thickness, mat)
    col.objects.link(obj)
    return obj


def svg_strokes():
    """Sample this artwork's M/L/C open paths without changing its shape."""
    root = ET.parse(SVG).getroot()
    strokes = []
    token_pattern = r"[MLC]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
    for path in root.findall("{http://www.w3.org/2000/svg}path"):
        tokens = re.findall(token_pattern, path.attrib["d"])
        index, point, command, current = 0, None, None, []
        while index < len(tokens):
            if tokens[index] in "MLC":
                command = tokens[index]
                index += 1
            if command == "M":
                if current:
                    strokes.append(current)
                point = (float(tokens[index]), float(tokens[index + 1]))
                current = [point]
                index += 2
                command = "L"
            elif command == "L":
                point = (float(tokens[index]), float(tokens[index + 1]))
                current.append(point)
                index += 2
            elif command == "C":
                nums = tuple(float(v) for v in tokens[index:index + 6])
                control1, control2, end = nums[:2], nums[2:4], nums[4:]
                start = point
                for step in range(1, 19):
                    t = step / 18
                    s = 1 - t
                    current.append(tuple(s**3 * start[d] +
                                         3 * s*s*t * control1[d] +
                                         3 * s*t*t * control2[d] +
                                         t**3 * end[d] for d in (0, 1)))
                point = end
                index += 6
            else:
                raise ValueError("Unsupported SVG path command")
        if current:
            strokes.append(current)
    return strokes


def logo_curve(name, strokes, y, radius, mat, col):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    for stroke in strokes:
        spline = curve.splines.new("POLY")
        spline.points.add(len(stroke) - 1)
        for point, (sx, sy) in zip(spline.points, stroke):
            # SVG is 435 x 81. Preserve its aspect ratio on the plate.
            point.co = ((sx - 217.5) * .16 * MM, y,
                        PLATE_Z + (40.5 - sy) * .16 * MM, 1)
    obj = bpy.data.objects.new(name, curve)
    col.objects.link(obj)
    if mat:
        curve.materials.append(mat)
    return obj


def mark_logo(strokes, dark, col):
    # Laser-annealed appearance. Physical etch depth is intentionally absent
    # until the steel grade, thickness, and marking process are selected.
    logo = logo_curve("DeepReal_Logo_Laser_Mark_Concept", strokes,
                      PLATE_FACE_Y + .11 * MM, .11 * MM, dark, col)
    logo["Visual_Finish"] = "dark laser mark; physical etch depth unselected"
    return logo


def camera(name, location, target, scale, col):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    return obj


def area_light(name, location, energy, size, target, col):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()


def render(scene, cam, name, width, height):
    scene.camera = cam
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = str(HERE / name)
    bpy.ops.render.render(write_still=True)
    print("R31 RENDER", scene.render.filepath)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "DeepReal Laptop Target Plate R31"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 128
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "AgX"
    scene.world = bpy.data.worlds.new("Charcoal Studio")
    scene.world.color = (.12, .15, .18)
    mats = materials.build_all()
    laptop_col = collection("01 — LAPTOP REAR VIEW")
    hidden_col = collection("02 — ORIGINAL LAPTOP INTERIOR (HIDDEN)")
    mount_col = collection("03 — REPLACEABLE FOAM AND STEEL TARGET")
    studio_col = collection("04 — REVIEW CAMERAS AND LIGHTS")
    params = design_spec.manifest()["params"]
    old_lid, deck = macbook.build(params, mats, hidden_col, laptop_col)
    for obj in old_lid:
        obj.hide_render = True
        obj.hide_set(True)
    lid = add_slab("Laptop_Continuous_Aluminium_Back",
                   (0, 0, -107.5 * MM), (304.1 * MM, 215 * MM),
                   10 * MM, 3 * MM, mats["MacBook_Aluminium"], laptop_col)
    lid["Reference"] = "3 mm visual lid proxy, not a universal laptop fit"
    foam = add_slab("Replaceable_Foam_Adhesive_Sticker",
                    (0, LID_REAR_Y + .2 * MM, PLATE_Z),
                    (106 * MM, 14 * MM), 1.2 * MM, TAPE_THICKNESS,
                    material("Warm_Grey_Foam", (.075, .08, .085), 0, .86),
                    mount_col)
    plate = add_slab("DeepReal_Full_Width_430_Steel_Target_Concept",
                     (0, LID_REAR_Y + TAPE_THICKNESS + .175 * MM,
                      PLATE_Z), (PLATE_WIDTH, PLATE_HEIGHT), 1.5 * MM,
                     PLATE_THICKNESS,
                     material("Satin_Brushed_Steel", (.075, .092, .105), .45,
                              .49), mount_col)
    plate["Concept_Material"] = "magnetic 430 ferritic stainless candidate"
    plate["Provisional"] = True
    foam["Provisional"] = True
    strokes = svg_strokes()
    logo = mark_logo(strokes, dark_mark_material(), mount_col)
    plate["Logo_Source"] = str(SVG.relative_to(HERE))
    plate["Logo_Stroke_Count"] = len(strokes)
    print("R31 LOGO STROKES", len(strokes))
    area_light("Large_Left_Softbox", (-.20, .23, .12), 5.0, .22,
               (0, 0, -.10), studio_col)
    area_light("Right_Rim", (.19, .16, -.03), 3.0, .16,
               (0, 0, -.09), studio_col)
    area_light("Plate_Graze", (.02, .10, .04), 1.5, .09,
               (0, PLATE_FACE_Y, PLATE_Z), studio_col)
    hero = camera("Camera_Back_Lid_Opens_Here", (0, .45, -.103),
                  (0, 0, -.106), .34, studio_col)
    detail = camera("Camera_Full_Width_Plate_Detail", (.01, .18, .035),
                    (0, PLATE_FACE_Y, -.023), .16, studio_col)
    macro = camera("Camera_Logo_And_Foam_Edge", (.065, .115, .025),
                   (0, PLATE_FACE_Y, PLATE_Z), .135, studio_col)
    exploded = camera("Camera_Adhesive_Layers_Exploded", (.095, .145, .035),
                      (0, PLATE_FACE_Y, .001), .22, studio_col)
    scene.camera = hero
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.overlay.show_overlays = False
                area.spaces.active.shading.type = "MATERIAL"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
    render(scene, hero, "r31-laptop-back.png", 1600, 1200)
    render(scene, detail, "r31-full-width-plate.png", 1800, 1000)
    render(scene, macro, "r31-logo-and-foam-detail.png", 1800, 1100)
    plate.location.y += 6 * MM
    plate.location.z += 20 * MM
    logo.location.y += 6 * MM
    logo.location.z += 20 * MM
    render(scene, exploded, "r31-attachment-layers-exploded.png", 1800, 1100)
    plate.location.y = 0
    plate.location.z = 0
    logo.location.y = 0
    logo.location.z = 0


if __name__ == "__main__":
    main()
