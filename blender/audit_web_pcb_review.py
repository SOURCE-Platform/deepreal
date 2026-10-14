#!/usr/bin/env python3
"""Check standalone PCB transport against the retained Blender snapshot."""

import hashlib
import json
import os
import struct
from pathlib import Path

import bpy
from mathutils.kdtree import KDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSET = Path(os.environ.get("DEEPREAL_WEB_PCB_REVIEW_OUT",
                            str(HERE / "review-output/web/main-pcba-review.glb"))).resolve()
REPORT = Path(os.environ["DEEPREAL_WEB_PCB_AUDIT_OUT"]).resolve()


def points(obj):
    return [obj.matrix_world @ vertex.co * 1000 for vertex in obj.data.vertices]


def maximum_gap(source, target):
    tree = KDTree(len(target))
    for index, point in enumerate(target):
        tree.insert(point, index)
    tree.balance()
    return max(tree.find(point)[2] for point in source)


def main():
    if not REPORT.is_relative_to(ROOT / "tmp") or REPORT.exists():
        raise ValueError("Choose a new internal tmp report path")
    manifest = json.loads(ASSET.with_suffix(".json").read_text())
    blob = ASSET.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == manifest["asset_sha256"]
    assert len(blob) == manifest["asset_bytes"]
    length, kind = struct.unpack_from("<II", blob, 12)
    assert kind == 0x4E4F534A
    gltf = json.loads(blob[20:20 + length])
    assert {node["name"] for node in gltf["nodes"]} == set(manifest["objects"])

    source = HERE / "deepreal.blend"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest["source_blend_sha256"]
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.window.scene = bpy.data.scenes["SOURCE - Canonical Assembly"]
    bpy.data.objects["Lid_Pivot"].rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    objects = [obj for obj in bpy.data.collections["Electronics Assembly"].objects
               if obj.get("PCBA_Component") or obj.get("PCBA_NativeSurface")]
    expected = {obj.name + "_WEB": points(obj) for obj in objects}
    assert set(expected) == set(manifest["objects"])

    # Compare real source shader values, not inferred chip colors.
    materials = {mat.name: mat for obj in objects for mat in obj.data.materials}
    for entry in gltf["materials"]:
        material = materials[entry["name"]]
        shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
        pbr = entry.get("pbrMetallicRoughness", {})
        assert abs(pbr.get("metallicFactor", 1) - shader.inputs["Metallic"].default_value) < 1e-6
        assert abs(pbr.get("roughnessFactor", 1) - shader.inputs["Roughness"].default_value) < 1e-6
        rgba = list(shader.inputs["Base Color"].default_value)
        rgba[3] = shader.inputs["Alpha"].default_value
        assert max(abs(a - b) for a, b in zip(pbr.get("baseColorFactor", [1, 1, 1, 1]), rgba)) < 1e-6

    # Import into an empty scene to avoid name suffixes and compare both directions.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(ASSET))
    bpy.context.view_layer.update()
    results = []
    for name, source_points in expected.items():
        obj = bpy.data.objects[name]
        assert obj.type == "MESH"
        target_points = points(obj)
        gap = max(maximum_gap(source_points, target_points),
                  maximum_gap(target_points, source_points))
        assert gap < 0.001, (name, gap)
        results.append({"object": name, "maximum_vertex_gap_mm": gap})
    report = {
        "asset_sha256": manifest["asset_sha256"],
        "source_blend_sha256": manifest["source_blend_sha256"],
        "object_count": len(results),
        "material_count": len(gltf["materials"]),
        "maximum_vertex_gap_mm": max(row["maximum_vertex_gap_mm"] for row in results),
        "checks": ["exact object inventory", "bidirectional world-space vertex comparison",
                   "source base color, alpha, metallic and roughness preservation"],
        "objects": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("x") as out:
        json.dump(report, out, indent=2)
        out.write("\n")
    print("PCB TRANSPORT PASS", report["object_count"], "objects;",
          report["maximum_vertex_gap_mm"], "mm maximum gap")


if __name__ == "__main__":
    main()
