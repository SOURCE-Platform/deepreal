#!/usr/bin/env python3
"""Finish the visible DeepReal enclosure silhouette for product renders."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21", HERE.parent / "r23"):
    sys.path.insert(0, str(path))

import macbook  # noqa: E402
from build_r23 import OLD_HOUSING, ccw, roof_profile, union_into  # noqa: E402
from r21_chassis import material, yz_prism  # noqa: E402

SOURCE = HERE.parent / "r21/deepreal-side-supported-drums-r21.blend"
OUTPUT = HERE / "deepreal-finished-exterior-r24.blend"


def lower_profile():
    # A true quarter curve replaces the coarse four-edge rear lower corner.
    outline = [(-1.5, -29), (10, -29)]
    for i in range(1, 25):
        angle = math.radians(-90 + 90 * i / 24)
        outline.append((10 + 12.5 * math.cos(angle),
                        -16 + 13 * math.sin(angle)))
    outline += [(22.5, 20), (11.7, 20), (11.7, 6.8), (-1.5, 6.8)]
    return ccw(outline)


def add_finish(obj):
    bevel = obj.modifiers.new("R24_Soft_Enclosure_Edges", "BEVEL")
    bevel.width = .00035
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(36)
    bevel.harden_normals = True
    normals = obj.modifiers.new("R24_Weighted_Normals", "WEIGHTED_NORMAL")
    normals.keep_sharp = True
    normals.weight = 50


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    for name in OLD_HOUSING:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    collection = bpy.data.collections.new("15 — R24 FINISHED EXTERIOR SHELL")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    housing_mat = material("R24_Satin_Mineral_Housing",
                           (.115, .14, .155, 1), .12, .52)
    drum_mat = bpy.data.materials["Device_Sensor_Drum.001"]
    drum_mat.node_tree.nodes["Principled BSDF"].inputs[
        "Base Color"].default_value = (.047, .055, .066, 1)
    shell = yz_prism("R24_One_Piece_Enclosure", lower_profile(),
                     0, 120, housing_mat, collection)
    support_profile = [(-4.2, 17), (-4.2, 23), (-5.5, 32.6),
                       (-5.5, 34.2), (11.5, 34.2), (18, 31),
                       (22.5, 22.7), (22.5, 5.5), (6, 5.5),
                       (6, 10), (2, 14)]
    for label, x, width in (("Left", -58.3, 2.2),
                            ("Center", 0, 3.0),
                            ("Right", 58.3, 2.2)):
        cheek = yz_prism("R24_Temporary_" + label, ccw(support_profile),
                         x, width, housing_mat, collection)
        union_into(shell, cheek)
    top = yz_prism("R24_Temporary_Flat_Top", roof_profile(),
                   0, 120, housing_mat, collection)
    union_into(shell, top)
    center = macbook.cylinder(
        "R24_Temporary_Center_Island", Vector((0, -.0015, .020)),
        macbook.X, .012, .003, housing_mat, seg=96)
    collection.objects.link(center)
    union_into(shell, center)
    add_finish(shell)
    shell["R24_Form"] = (
        "one connected enclosure: flat roof, rounded back, smooth lower "
        "rear corner, center island and two outer supports")
    shell["R24_Scope"] = "exterior appearance; parting seams added later"
    # A middle interaction pose keeps both optical heads readable in a hero.
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    interaction.rotation_euler.x = -math.radians(22.5)
    scene.name = "DeepReal Finished Exterior Study R24"
    scene["R24_Render_Intent"] = (
        "website exterior study; appearance is intentional, mechanical "
        "assembly and internal clearances are not certified")
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {
        "source": str(SOURCE), "model": str(OUTPUT),
        "enclosure": shell.name,
        "flat_top_mm": 34.2, "top_underside_mm": 32.8,
        "lower_rear_corner_radius_y_mm": 12.5,
        "lower_rear_corner_radius_z_mm": 13.0,
        "edge_bevel_mm": .35,
        "saved_optical_pose_deg": {"face": 0, "interaction": 22.5},
        "scope": "exterior visual study",
    }
    (HERE / "r24-exterior-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R24 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
