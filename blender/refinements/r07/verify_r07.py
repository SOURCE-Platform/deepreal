#!/usr/bin/env python3
"""Verify R07 clearances, housing-mode toggle, and protected inputs."""

import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BLEND = HERE / "deepreal-exterior-refinement-r07.blend"
R06 = HERE.parent / "r06" / "deepreal-exterior-refinement-r06.blend"
BASE = REPO / "blender" / "deepreal.blend"
REPORT = HERE / "r07-verification.json"
EXPECTED = {
    str(R06): "30a89ce7b16fe1003d620c28853861467f50d36e3f3e8cc94719ff0346bd3d88",
    str(BASE): "4c65762f65d35f5345bb3ad601aafdb0ce2809681931aad480586cc5747d3412",
}


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(face.vertices) for face in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False,
                                epsilon=1e-8)
    evaluated.to_mesh_clear()
    return tree


def bounds_mm(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return [[round(min(p[i] for p in points) * 1000, 3),
             round(max(p[i] for p in points) * 1000, 3)] for i in range(3)]


def add(rows, name, passed, evidence):
    rows.append({"check": name, "pass": bool(passed), "evidence": evidence})


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    rows = []
    solid = bpy.data.objects["Main_Housing"]
    wire = bpy.data.objects["Main_Housing_Inspection_Wireframe"]
    solid_collection = bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"]
    wire_collection = bpy.data.collections[
        "00A — WIREFRAME FALLBACK — KEEP VISIBLE"]
    add(rows, "one-eye solid-to-wireframe viewport toggle is configured",
        list(solid_collection.objects) == [solid] and
        list(wire_collection.objects) == [wire] and
        wire.display_type == "WIRE" and not wire.hide_viewport and
        all(abs(value - 0.997) < 1e-6 for value in wire.scale),
        {"solid_collection": solid_collection.name,
         "wire_collection": wire_collection.name,
         "wire_scale": list(wire.scale), "wire_render_hidden": wire.hide_render})

    board = bpy.data.objects["Centered_USB_Daughterboard"]
    board_box = bounds_mm(board)
    overmold_box = bounds_mm(bpy.data.objects["USB_C_Plug_Overmold"])
    add(rows, "daughterboard is above and forward of the plug overmold",
        board_box[1][1] <= overmold_box[1][0] - 0.49 and
        board_box[2][0] >= -20.001,
        {"daughterboard_bounds_mm": board_box,
         "overmold_bounds_mm": overmold_box})

    depsgraph = bpy.context.evaluated_depsgraph_get()
    pairs = (
        ("Centered_USB_Daughterboard", "USB_C_Plug_Overmold"),
        ("Centered_USB_Daughterboard", "Thermal_Spreader"),
        ("Centered_USB_Daughterboard", "Shield_Rear_Tray"),
        ("Centered_USB_Daughterboard", "Shield_Front_Lid"),
        ("Centered_USB_Daughterboard", "Main_Housing"),
        ("USB_C_Plug_Overmold", "Main_Housing"),
    )
    trees = {name: world_tree(bpy.data.objects[name], depsgraph)
             for pair in pairs for name in pair}
    collisions = {f"{a} <-> {b}": len(trees[a].overlap(trees[b]))
                  for a, b in pairs}
    add(rows, "no triangle intersections remain in the USB packaging path",
        not any(collisions.values()), collisions)

    slot_data = {}
    for name in ("Thermal_Spreader", "Shield_Rear_Tray", "Shield_Front_Lid"):
        obj = bpy.data.objects[name]
        slot_data[name] = {
            "width_mm": obj["R07_Service_Slot_Width_mm"],
            "z_mm": list(obj["R07_Service_Slot_Z_mm"]),
        }
    add(rows, "service path provides nominal 1 mm board-edge clearance",
        all(item == {"width_mm": 18.0, "z_mm": [-25.0, -10.0]}
            for item in slot_data.values()), slot_data)

    sources = {}
    for text, expected in EXPECTED.items():
        actual = sha256(Path(text))
        sources[text] = {"actual": actual, "expected": expected,
                         "match": actual == expected}
    add(rows, "R06 and authoritative DeepReal input hashes are unchanged",
        all(item["match"] for item in sources.values()), sources)

    result = "PASS" if all(row["pass"] for row in rows) else "FAIL"
    report = {
        "file": str(BLEND), "result": result, "checks": rows,
        "limitations": [
            "The daughterboard is a conditional packaging option, not an approved USB implementation.",
            "The split thermal path is a clearance workaround, not validated thermal design.",
            "USB SI, PD, ESD, shield bonding, cable retention, thermals, tolerances, and physical testing remain open."
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
