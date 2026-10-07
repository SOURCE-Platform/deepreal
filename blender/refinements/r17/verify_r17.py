#!/usr/bin/env python3
"""Check R17's enclosed side modules against the R16 assembly."""

import bmesh
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "r16/deepreal-exterior-refinement-r16.blend"
MODEL = HERE / "deepreal-exterior-refinement-r17.blend"
REPORT = HERE / "r17-verification.json"
for path in (HERE.parent / "r08", HERE.parent / "r15"):
    sys.path.insert(0, str(path))
from verify_r08 import bounds_mm, signature, tree  # noqa: E402


def topology(obj):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    result = {"faces": len(mesh.faces),
              "non_manifold_edges": sum(not edge.is_manifold
                                        for edge in mesh.edges)}
    mesh.free()
    return result


def radial_max_mm(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return round(max(math.hypot(point.y * 1000 + 1.5,
                                point.z * 1000 - 20)
                     for point in points), 3)


def preserved_signatures():
    names = ["Thermal_Spreader", "Shield_Rear_Tray",
             "Face_Sensor_Head", "Interaction_Sensor_Head",
             "Face_Rear_Access_Cover_REMOVABLE_CONCEPT",
             "Interaction_Rear_Access_Cover_REMOVABLE_CONCEPT",
             "Face_Head_PCBA_Carrier_CONCEPT",
             "Interaction_Head_PCBA_Carrier_CONCEPT"]
    names += [side + "_Drum_Lens_" + aperture
              for side in ("Face", "Interaction")
              for aperture in ("Depth", "RGB", "ProjA", "ProjB", "Pinhole")]
    return {name: signature(bpy.data.objects[name]) for name in names}


def check_side(side, sign, base):
    cap_name = side + "_Sensor_Head_Flat_End_" + (
        "Left" if sign < 0 else "Right")
    cap = bpy.data.objects[cap_name]
    sleeve = bpy.data.objects[side + "_Fixed_End_Chamber_Sleeve_R17"]
    outer = bpy.data.objects[side + "_Smooth_Outer_End_Cap_R17"]
    shell = bpy.data.objects[side + "_Sensor_Head"]
    pigtail = bpy.data.objects[side + "_Head_Flex_Rotating_Pigtail_R17"]
    pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
    housing = bpy.data.objects["Main_Housing"]
    fixed_names = ("Axial_Motor_Stator_ENVELOPE_R17",
                   "Axial_Motor_Rotor_Hub_ENVELOPE_R17", "Encoder_Board",
                   "Encoder_Sensor_IC_PROXY_R17", "Encoder_Magnet",
                   "Stator_Mount_Top_R17", "Stator_Mount_Bottom_R17",
                   "Encoder_Board_Mount_A_R17",
                   "Encoder_Board_Mount_B_R17")
    radii = {name: radial_max_mm(bpy.data.objects[side + "_" + name])
             for name in fixed_names}
    fixed_fit = all(radius < 10.55 for radius in radii.values())
    blocked_side_rays = []
    for y, z in ((-1.5, 20), (-9, 20), (6, 20),
                 (-1.5, 12), (-1.5, 28)):
        origin = Vector((sign * .064, y * .001, z * .001))
        direction = Vector((-sign, 0, 0))
        if tree(outer).ray_cast(origin, direction, .015)[0] is None:
            blocked_side_rays.append([y, z])
    fixed_paths = {}
    for suffix in ("Head_Power_Data_Flex_ROUTE_CONCEPT",
                   "Motor_Power_Harness_ROUTE_CONCEPT",
                   "Encoder_Feedback_ROUTE_CONCEPT"):
        route = bpy.data.objects[side + "_" + suffix]
        route_tree = tree(route)
        fixed_paths[suffix] = {
            "inner_cap_hits": len(route_tree.overlap(tree(cap))),
            "sleeve_hits": len(route_tree.overlap(tree(sleeve))),
            "outer_cap_hits": len(route_tree.overlap(tree(outer))),
        }
    sampled_motion = {}
    for angle in range(-75, 76, 15):
        pivot.rotation_euler.x = math.radians(angle - base)
        bpy.context.view_layer.update()
        tail = tree(pigtail)
        body = tree(shell)
        sampled_motion[str(angle)] = {
            "pigtail_inner_cap_hits": len(tail.overlap(tree(cap))),
            "pigtail_sleeve_hits": len(tail.overlap(tree(sleeve))),
            "shell_sleeve_hits": len(body.overlap(tree(sleeve))),
            "shell_outer_cap_hits": len(body.overlap(tree(outer))),
        }
    pivot.rotation_euler.x = 0
    bpy.context.view_layer.update()
    boundaries = {name: topology(bpy.data.objects[name])
                  for name in (sleeve.name, outer.name, cap.name)}
    stationary = {
        "sleeve_housing_hits": len(tree(sleeve).overlap(tree(housing))),
        "outer_cap_housing_hits": len(tree(outer).overlap(tree(housing))),
    }
    evidence = {
        "drum_x_mm": bounds_mm(shell)[0],
        "sleeve_x_mm": bounds_mm(sleeve)[0],
        "outer_cap_x_mm": bounds_mm(outer)[0],
        "fixed_part_max_radii_mm": radii,
        "uncovered_side_ray_positions_mm": blocked_side_rays,
        "fixed_route_intersections": fixed_paths,
        "sampled_motion_intersections": sampled_motion,
        "stationary_intersections": stationary,
        "topology": boundaries,
    }
    passed = (fixed_fit and not blocked_side_rays
              and all(not any(row.values()) for row in fixed_paths.values())
              and all(not any(row.values())
                      for row in sampled_motion.values())
              and not any(stationary.values())
              and all(row["faces"] > 0 and row["non_manifold_edges"] == 0
                      for row in boundaries.values()))
    return passed, evidence


def moving_clearance():
    housing = tree(bpy.data.objects["Main_Housing"])
    result = {}
    for side, base in (("Face", 0), ("Interaction", 45)):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        cap_suffix = "Left" if side == "Face" else "Right"
        fixed_names = ("Axial_Motor_Stator_ENVELOPE_R17",
                       "Encoder_Board", "Encoder_Sensor_IC_PROXY_R17",
                       "Stator_Mount_Top_R17", "Stator_Mount_Bottom_R17",
                       "Sensor_Head_Flat_End_" + cap_suffix,
                       "Fixed_End_Chamber_Sleeve_R17",
                       "Smooth_Outer_End_Cap_R17",
                       "Bearing_Outer", "Bearing_Inner")
        fixed = [(name, tree(bpy.data.objects[side + "_" + name]))
                 for name in fixed_names]
        pigtail = bpy.data.objects[side +
                                   "_Head_Flex_Rotating_Pigtail_R17"]
        moving = [obj for obj in pivot.children if obj.type == "MESH"]
        for angle in range(-75, 76, 15):
            pivot.rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            hits = []
            for part in moving:
                part_tree = tree(part)
                for name, fixed_tree in fixed:
                    if part_tree.overlap(fixed_tree):
                        hits.append(part.name + " / " + name)
                if part.name.endswith(("Sensor_Head",
                                       "Rear_Access_Cover_REMOVABLE_CONCEPT")):
                    if part_tree.overlap(housing):
                        hits.append(part.name + " / Main_Housing")
            tail = tree(pigtail)
            for part in moving:
                if part.name != side + "_Head_Flex_Connector_PROXY":
                    if tail.overlap(tree(part)):
                        hits.append(pigtail.name + " / " + part.name)
            for name, fixed_tree in fixed:
                if tail.overlap(fixed_tree):
                    hits.append(pigtail.name + " / " + name)
            axis = Vector((0, -math.cos(math.radians(angle)),
                           -math.sin(math.radians(angle))))
            blocked_lenses = []
            for aperture in ("Depth", "RGB", "ProjA", "ProjB", "Pinhole"):
                lens = bpy.data.objects[side + "_Drum_Lens_" + aperture]
                center = sum((lens.matrix_world @ vertex.co
                              for vertex in lens.data.vertices), Vector())
                center /= len(lens.data.vertices)
                if housing.ray_cast(center + axis * .0005,
                                    axis, .080)[0] is not None:
                    blocked_lenses.append(aperture)
            result[f"{side}_{angle:+d}"] = {
                "part_intersections": hits,
                "housing_blocked_lenses": blocked_lenses}
        pivot.rotation_euler.x = 0
        bpy.context.view_layer.update()
    return result


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    original = preserved_signatures()
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    checks = []

    def record(label, passed, evidence):
        checks.append({"check": label, "pass": bool(passed),
                       "evidence": evidence})

    current = preserved_signatures()
    preserved = {name: original[name] == current[name] for name in original}
    record("R16 drums, optics, thermal stack and head boards preserved",
           all(preserved.values()), preserved)
    for side, sign, base in (("Face", -1, 0),
                            ("Interaction", 1, 45)):
        passed, evidence = check_side(side, sign, base)
        record(side + " drive and encoder are enclosed at sampled poses",
               passed, evidence)
    travel = moving_clearance()
    record("sampled movement retains fixed-part and lens-center clearance",
           all(not any(row.values()) for row in travel.values()), travel)
    record("R16 model file unchanged",
           hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash,
           {"sha256": source_hash})
    report = {
        "model": str(MODEL),
        "result": "PASS" if all(row["pass"] for row in checks) else "FAIL",
        "checks": checks,
        "engineering_readiness": "BLOCKED",
        "limits": [
            "Side-ray and triangle checks sample geometry, not manufacturing tolerances.",
            "The moving service-loop curve is a saved-pose illustration; full-angle deformation and cable fatigue are unverified.",
            "Encoder part, magnet specification, accuracy and calibration are unselected.",
            "Annular motor availability, torque, shaft coupling, fixed-cap attachment, sealing and housing strength are unverified.",
            "Interaction final travel range is still open; -75 to +75 degrees is a conservative visual study.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    for row in checks:
        print("PASS" if row["pass"] else "FAIL", row["check"])
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
