#!/usr/bin/env python3
"""Replace the R22 canopy with a single flat-roof enclosure concept."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21"):
    sys.path.insert(0, str(path))

import macbook  # noqa: E402
from r21_chassis import material, yz_prism  # noqa: E402

SOURCE = HERE.parent / "r21/deepreal-side-supported-drums-r21.blend"
OUTPUT = HERE / "deepreal-integrated-flat-roof-r23.blend"
OLD_HOUSING = ("R21_Lower_Housing_And_Rear_Spine",
               "R21_Support_Left_Outer", "R21_Support_Center",
               "R21_Support_Right_Outer", "R21_Center_Gap_Fairing")


def ccw(outline):
    area = sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(outline, outline[1:] + outline[:1]))
    return outline if area > 0 else list(reversed(outline))


def roof_profile():
    # Flat top from front lip to rear tangent; only the back corner rounds.
    outer = [(-6.0, 34.2), (11.0, 34.2)]
    for i in range(1, 25):
        angle = math.radians(90 - i * 90 / 24)
        outer.append((11 + 11.5 * math.cos(angle),
                      22.7 + 11.5 * math.sin(angle)))
    inner = [(22.5, 13), (21.1, 13), (21.1, 22.7)]
    for i in range(1, 25):
        angle = math.radians(i * 90 / 24)
        inner.append((11 + 10.1 * math.cos(angle),
                      22.7 + 10.1 * math.sin(angle)))
    return ccw(outer + inner + [(-6.0, 32.8)])


def union_into(base, part):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = base
    base.select_set(True)
    modifier = base.modifiers.new("R23_Union_" + part.name, "BOOLEAN")
    modifier.operation = "UNION"
    modifier.solver = "EXACT"
    modifier.object = part
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    base.select_set(False)
    bpy.data.objects.remove(part, do_unlink=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    for name in OLD_HOUSING:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    collection = bpy.data.collections.new("14 — R23 UNIFIED ENCLOSURE")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    shell_mat = material("R23_Enclosure_Satin_Graphite",
                         (.12, .15, .17, 1), .2, .46)
    base_profile = [(-1.5, -29), (10, -29), (14, -28), (18, -25),
                    (21, -21), (22.5, -16), (22.5, 25), (21, 28),
                    (18, 31), (12, 32), (11.7, 32), (11.7, 6.8),
                    (-1.5, 6.8)]
    base = yz_prism("R23_Unified_Enclosure", ccw(base_profile),
                    0, 120, shell_mat, collection)
    support_profile = [(-4.2, 17), (-4.2, 23), (-5.5, 32.6),
                       (-5.5, 34.2), (11.5, 34.2), (18, 31),
                       (22.5, 22.7), (22.5, 5.5), (6, 5.5),
                       (6, 10), (2, 14)]
    for label, x, thickness in (("Left", -58.3, 2.2),
                                ("Center", 0, 3.0),
                                ("Right", 58.3, 2.2)):
        support = yz_prism("R23_Temporary_" + label, ccw(support_profile),
                           x, thickness, shell_mat, collection)
        union_into(base, support)
    roof = yz_prism("R23_Temporary_Flat_Roof", roof_profile(),
                    0, 120, shell_mat, collection)
    union_into(base, roof)
    fairing = macbook.cylinder(
        "R23_Temporary_Center_Fairing", Vector((0, -.0015, .020)),
        macbook.X, .012, .003, shell_mat, seg=96)
    collection.objects.link(fairing)
    union_into(base, fairing)
    base["R23_Design_Intent"] = (
        "single continuous enclosure mesh: flat top, rounded rear corner, "
        "vertical back, left/center/right supports and lower body")
    base["R23_Status"] = (
        "concept shell; wall thickness, bearing bores, assembly access, "
        "fasteners, molding split and dust sealing unverified")
    scene.name = "DeepReal Integrated Flat-Roof Enclosure R23"
    scene["R23_Assembly_Risk"] = (
        "one-piece supports may trap drums; installation path and removable "
        "bearing hardware are not yet resolved")
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {"source": str(SOURCE), "model": str(OUTPUT),
                "enclosure": base.name, "mesh_vertices": len(base.data.vertices),
                "flat_roof_top_mm": 34.2, "flat_roof_underside_mm": 32.8,
                "front_roof_edge_y_mm": -6.0,
                "rear_corner_radius_mm": 11.5,
                "readiness": "appearance and packaging concept only"}
    (HERE / "r23-enclosure-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R23 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
