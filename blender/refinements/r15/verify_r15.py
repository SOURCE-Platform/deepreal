#!/usr/bin/env python3
"""Check the R15 drum study at neutral and sampled travel positions."""

import bmesh
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import bounds_mm, signature, tree  # noqa: E402

SOURCE = HERE.parent / "r14/deepreal-exterior-refinement-r14.blend"
BLEND = HERE / "deepreal-exterior-refinement-r15.blend"
REPORT = HERE / "r15-verification.json"


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def record(checks, name, passed, evidence):
    checks.append({"check": name, "pass": bool(passed), "evidence": evidence})


def topology(obj):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    evidence = {"vertices": len(mesh.verts), "faces": len(mesh.faces),
                "non_manifold_edges": sum(not edge.is_manifold
                                          for edge in mesh.edges)}
    mesh.free()
    return evidence


def fixed_parts(side):
    names = [side + "_" + name for name in (
        "Geared_Motor", "Motor_Pinion", "Motor_Bracket",
        "Motor_Mount_Arm_Low_CONCEPT", "Motor_Mount_Arm_High_CONCEPT",
        "Encoder_Board", "Bearing_Outer", "Bearing_Inner")]
    names += [side + "_Sensor_Head_Flat_End_"
              + ("Left" if side == "Face" else "Right")]
    return [bpy.data.objects[name] for name in names]


def moving_parts(side):
    pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
    return [obj for obj in pivot.children if obj.type == "MESH"]


def bounds(obj):
    corners = [obj.matrix_world @ Vector(vertex)
               for vertex in obj.bound_box]
    return [(min(point[i] for point in corners),
             max(point[i] for point in corners)) for i in range(3)]


def boxes_overlap(first, second):
    return all(first[i][0] < second[i][1]
               and second[i][0] < first[i][1] for i in range(3))


def travel_check():
    housing = tree(bpy.data.objects["Main_Housing"])
    detail = {}
    for side, base in (("Face", 0), ("Interaction", 45)):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        moving = moving_parts(side)
        fixed = fixed_parts(side)
        fixed_boxes = {obj.name: bounds(obj) for obj in fixed}
        fixed_trees = {obj.name: tree(obj) for obj in fixed}
        for angle in range(-75, 76, 15):
            pivot.rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            hits = []
            for item in moving:
                item_box = bounds(item)
                overlaps = [obj for obj in fixed
                            if boxes_overlap(item_box, fixed_boxes[obj.name])]
                if not overlaps and item.name not in (
                        side + "_Sensor_Head",
                        side + "_Rear_Access_Cover_REMOVABLE_CONCEPT"):
                    continue
                item_tree = tree(item)
                for obj in overlaps:
                    if item_tree.overlap(fixed_trees[obj.name]):
                        hits.append(item.name + " / " + obj.name)
                if item.name in (side + "_Sensor_Head",
                                 side + "_Rear_Access_Cover_REMOVABLE_CONCEPT"):
                    if item_tree.overlap(housing):
                        hits.append(item.name + " / Main_Housing")
            view_blocked = []
            axis = Vector((0, -math.cos(math.radians(angle)),
                           -math.sin(math.radians(angle))))
            for aperture in ("Depth", "RGB", "ProjA", "ProjB", "Pinhole"):
                lens = bpy.data.objects[side + "_Drum_Lens_" + aperture]
                center = sum((lens.matrix_world @ vertex.co
                              for vertex in lens.data.vertices), Vector())
                center /= len(lens.data.vertices)
                if housing.ray_cast(center + axis * .0005,
                                    axis, .080)[0] is not None:
                    view_blocked.append(aperture)
            detail[side + "_%+d" % angle] = {
                "fixed_part_or_housing_intersections": hits,
                "housing_blocked_lens_center_rays": view_blocked}
        pivot.rotation_euler.x = 0
        bpy.context.view_layer.update()
    return detail


def main():
    preserved_names = ("Main_Housing", "Thermal_Spreader",
                       "Shield_Rear_Tray",
                       "Main_PCBA_Near_Full_Height_Right_Wing_PROPOSAL")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    originals = {name: signature(bpy.data.objects[name])
                 for name in preserved_names}
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    checks = []
    preserved = {name: signature(bpy.data.objects[name]) == original
                 for name, original in originals.items()}
    record(checks, "enclosure, thermal and main-PCB meshes retained",
           all(preserved.values()), preserved)

    topo = {}
    ring_dimensions = {}
    pivot_parts = {}
    for side in ("Face", "Interaction"):
        for name in (side + "_Sensor_Head",
                     side + "_Rear_Access_Cover_REMOVABLE_CONCEPT"):
            topo[name] = topology(bpy.data.objects[name])
        ring = bpy.data.objects[side + "_Ring_Gear"]
        ring_x = bounds_mm(ring)[0]
        ring_dimensions[side] = {
            "radial_outer_diameter_mm": 20.9,
            "drum_inner_diameter_mm": 21.0,
            "ring_x_mm": ring_x,
            "shell_x_mm": bounds_mm(bpy.data.objects[side + "_Sensor_Head"])[0]}
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        pivot_parts[side] = {"ring_parent": ring.parent == pivot,
                             "cover_parent": bpy.data.objects[
                                 side + "_Rear_Access_Cover_REMOVABLE_CONCEPT"
                             ].parent == pivot}
    record(checks, "shell and removable covers are closed meshes",
           all(row["non_manifold_edges"] == 0 and row["faces"] > 0
               for row in topo.values()), topo)
    inside = all(row["ring_x_mm"][0] >= row["shell_x_mm"][0]
                 and row["ring_x_mm"][1] <= row["shell_x_mm"][1]
                 and row["radial_outer_diameter_mm"] <
                 row["drum_inner_diameter_mm"]
                 for row in ring_dimensions.values())
    record(checks, "gear envelopes lie inside the drum shells",
           inside and all(all(row.values()) for row in pivot_parts.values()),
           {"dimensions": ring_dimensions, "pivot_links": pivot_parts})

    left = bounds_mm(bpy.data.objects["Face_Sensor_Head"])[0][1]
    right = bounds_mm(bpy.data.objects["Interaction_Sensor_Head"])[0][0]
    record(checks, "one-millimeter center drum gap retained",
           abs(right - left - 1.0) < .001,
           {"left_end_mm": left, "right_start_mm": right})

    travel = travel_check()
    record(checks, "sampled 150-degree travel clears fixed parts and housing",
           all(not row["fixed_part_or_housing_intersections"] and
               not row["housing_blocked_lens_center_rays"]
               for row in travel.values()), travel)

    collections = {name: bpy.data.collections[name]
                   for name in (
                       "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME",
                       "01 — DRUM SHELLS — CLICK EYE FOR INTERNALS",
                       "01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS")}
    visible = {name: not col.hide_viewport and not col.hide_render
               for name, col in collections.items()}
    record(checks, "normal saved view has housing, shells and covers visible",
           all(visible.values()), visible)
    distances = [area.spaces.active.region_3d.view_distance
                 for screen in bpy.data.screens for area in screen.areas
                 if area.type == "VIEW_3D"]
    record(checks, "saved viewport is framed near the model",
           bool(distances) and max(distances) <= .15,
           [round(value, 4) for value in distances])

    baseline = json.loads((HERE / "baseline.json").read_text())
    source_hashes = {rel: digest(REPO / rel) == expected
                     for rel, expected in baseline["protected_sha256"].items()}
    record(checks, "R14, R13 and native PCB sources unchanged",
           all(source_hashes.values()), source_hashes)
    current = subprocess.check_output(
        ["git", "status", "--short"], cwd=REPO, text=True).splitlines()
    def unrelated(rows):
        return [row for row in rows if not row[3:].startswith(
            ("blender/refinements/r14/", "blender/refinements/r15/"))]
    record(checks, "unrelated pre-existing work remains untouched",
           unrelated(current) == unrelated(baseline["git_status_before"]),
           {"before": unrelated(baseline["git_status_before"]),
            "after": unrelated(current)})

    report = {"model": str(BLEND), "result": "PASS" if all(
        check["pass"] for check in checks) else "FAIL",
        "engineering_readiness": "BLOCKED", "checks": checks,
        "limitations": [
            "Sampled triangle intersections and lens center rays do not establish full mechanical or optical clearance.",
            "Gear teeth, coupling, torque, tolerances, hard stops and retention are not designed.",
            "The rear access cover requires real fasteners, sealing and structural validation.",
            "The head flex is shown only at neutral pose; dynamic service loop and cable life are unresolved.",
        ]}
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    for row in checks:
        print("PASS" if row["pass"] else "FAIL", row["check"])
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
