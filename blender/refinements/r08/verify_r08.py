#!/usr/bin/env python3
"""Check R08 native geometry and protected source hashes."""

import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BLEND = HERE / "deepreal-exterior-refinement-r08.blend"
REPORT = HERE / "r08-verification.json"
EXPECTED = {
    "blender/refinements/r07/deepreal-exterior-refinement-r07.blend":
        "1e31502e0f7e859d0513d891fa6c9db259c285e856b085de1e3cc253ccb6234a",
    "blender/refinements/r06/deepreal-exterior-refinement-r06.blend":
        "30a89ce7b16fe1003d620c28853861467f50d36e3f3e8cc94719ff0346bd3d88",
    "blender/refinements/r04/deepreal-exterior-refinement-r04.blend":
        "0a8599a3b38f938fa9c68352d40226961f56a7c25272acd8831dddf51444c78a",
    "blender/deepreal.blend":
        "4c65762f65d35f5345bb3ad601aafdb0ce2809681931aad480586cc5747d3412",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def signature(obj):
    mesh = obj.data
    return {
        "vertices": [tuple(round(x, 9) for x in point.co) for point in mesh.vertices],
        "faces": [tuple(face.vertices) for face in mesh.polygons],
    }


def bounds_mm(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    box = [[round(min(v[i] for v in points) * 1000, 3),
            round(max(v[i] for v in points) * 1000, 3)] for i in range(3)]
    evaluated.to_mesh_clear()
    return box


def tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(face.vertices) for face in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False,
                                  epsilon=1e-8)
    evaluated.to_mesh_clear()
    return result


def add(checks, name, passed, evidence):
    checks.append({"check": name, "pass": bool(passed), "evidence": evidence})


def rear_surface_hit(obj, x_mm, z_mm, start_y_mm, depth_mm):
    location, _, _, _ = tree(obj).ray_cast(
        Vector((x_mm, start_y_mm, z_mm)) * 0.001,
        Vector((0.0, -1.0, 0.0)), depth_mm * 0.001)
    return location is not None


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    checks = []
    with bpy.data.libraries.load(
            str(HERE.parent / "r04" / "deepreal-exterior-refinement-r04.blend"),
            link=False) as (src, dst):
        dst.objects = ["Thermal_Spreader", "Shield_Front_Lid"]
    unchanged = {}
    for name, donor in zip(("Thermal_Spreader", "Shield_Front_Lid"), dst.objects):
        unchanged[name] = signature(bpy.data.objects[name]) == signature(donor)
        bpy.data.objects.remove(donor, do_unlink=True)
    add(checks, "spreader and front shield have their original uncut mesh",
        all(unchanged.values()), unchanged)

    surface = {
        "spreader_center_closed": rear_surface_hit(
            bpy.data.objects["Thermal_Spreader"], 0, -17.5, 16, 3),
        "front_lid_center_closed": rear_surface_hit(
            bpy.data.objects["Shield_Front_Lid"], 0, -17.5, 8, 2),
        "rear_tray_center_closed": rear_surface_hit(
            bpy.data.objects["Shield_Rear_Tray"], 0, -17.5, 16, 3),
        "rear_tray_side_open": not rear_surface_hit(
            bpy.data.objects["Shield_Rear_Tray"], 39, -17.5, 16, 3),
    }
    add(checks, "center layers are closed and only side tray feedthrough is open",
        all(surface.values()), surface)

    board = bounds_mm(bpy.data.objects["Centered_USB_Daughterboard"])
    socket = bounds_mm(bpy.data.objects[
        "USB_C_Female_Socket_ENVELOPE_NOT_PART_SELECTED"])
    plug = bounds_mm(bpy.data.objects["USB_C_Plug_Overmold"])
    add(checks, "external USB and proposed daughterboard are centered",
        all(abs(box[0][0] + box[0][1]) < 0.01
            for box in (board, socket, plug)),
        {"board": board, "socket_envelope": socket, "plug_overmold": plug})

    pairs = (
        ("Centered_USB_Daughterboard", "Thermal_Spreader"),
        ("Centered_USB_Daughterboard", "Shield_Rear_Tray"),
        ("Centered_USB_Daughterboard", "Shield_Front_Lid"),
        ("Centered_USB_Daughterboard", "Main_Housing"),
        ("Centered_USB_Daughterboard", "Thermal_Link_Left"),
        ("Centered_USB_Daughterboard", "Thermal_Link_Right"),
        ("USB_C_Plug_Overmold", "Main_Housing"),
        ("USB_C_Male_Metal_Shell", "Main_Housing"),
        ("USB_C_Female_Socket_ENVELOPE_NOT_PART_SELECTED", "Thermal_Spreader"),
        ("USB_C_Female_Socket_ENVELOPE_NOT_PART_SELECTED", "Main_Housing"),
        ("Mainboard_USB_Flex_Connector_CONCEPT", "Main_Housing"),
        ("Mainboard_USB_Flex_Connector_CONCEPT", "Shield_Rear_Tray"),
        ("USB_Power_Data_Side_Route_CONCEPT", "Thermal_Spreader"),
        ("USB_Power_Data_Side_Route_CONCEPT", "Shield_Rear_Tray"),
        ("USB_Power_Data_Side_Route_CONCEPT", "Shield_Front_Lid"),
        ("USB_Power_Data_Side_Route_CONCEPT", "Main_Housing"),
        ("USB_Power_Data_Side_Route_CONCEPT", "Thermal_Link_Right"),
        ("USB_Power_Data_Side_Route_CONCEPT", "Housing_Thermal_Pad_Right"),
    )
    trees = {name: tree(bpy.data.objects[name])
             for pair in pairs for name in pair}
    collisions = {f"{a} <> {b}": len(trees[a].overlap(trees[b]))
                  for a, b in pairs}
    add(checks, "no unintended mesh intersections along new USB path",
        not any(collisions.values()), collisions)

    route = bpy.data.objects["USB_Power_Data_Side_Route_CONCEPT"]
    points = list(route["R08_Route_Points_mm"])
    xs = points[0::3]
    ys = points[1::3]
    tray = bpy.data.objects["Shield_Rear_Tray"]
    lid = bpy.data.objects["Shield_Front_Lid"]
    add(checks, "route goes to right of spreader with a small rear feedthrough",
        max(xs) >= 39 and max(ys) >= 18 and
        list(tray["R08_Feedthrough_Envelope_mm"]) == [5.0, 4.0] and
        "R08_Feedthrough_Envelope_mm" not in lid,
        {"max_route_x_mm": max(xs), "max_route_y_mm": max(ys),
         "spreader_max_x_mm": bounds_mm(bpy.data.objects["Thermal_Spreader"])[0][1],
         "rear_feedthrough_mm": list(tray["R08_Feedthrough_Envelope_mm"])})

    scene = bpy.context.scene
    add(checks, "unverified electrical and thermal status remains explicit",
        "no electrical or thermal approval" in scene["DeepReal_Status"] and
        "unverified" in scene["R08_Thermal_Status"] and
        "not selected" in bpy.data.objects[
            "USB_C_Female_Socket_ENVELOPE_NOT_PART_SELECTED"]["DeepReal_Status"],
        {"scene": scene["DeepReal_Status"],
         "thermal": scene["R08_Thermal_Status"]})

    viewport_distances = [round(area.spaces.active.region_3d.view_distance, 4)
                          for screen in bpy.data.screens for area in screen.areas
                          if area.type == "VIEW_3D"]
    add(checks, "saved viewport framing is close",
        bool(viewport_distances) and max(viewport_distances) <= 0.145,
        viewport_distances)

    hashes = {rel: {"expected": expected, "actual": sha256(REPO / rel)}
              for rel, expected in EXPECTED.items()}
    add(checks, "protected Blender sources retain baseline hashes",
        all(row["actual"] == row["expected"] for row in hashes.values()), hashes)
    status = "PASS" if all(row["pass"] for row in checks) else "FAIL"
    report = {
        "file": str(BLEND), "result": status, "checks": checks,
        "engineering_readiness": "BLOCKED",
        "limits": [
            "USB-C socket is a visual envelope, not an exact selected part.",
            "Internal flex route is diagrammatic; no real PCB, pin mapping, power, or SI design exists.",
            "Thermal path, vent decision, shield bonding, and EMI require engineering and measurement.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
