#!/usr/bin/env python3
"""Verify the saved R05 review model without modifying it."""

import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BLEND = HERE / "deepreal-exterior-refinement-r05.blend"
SOURCE = REPO / "blender" / "deepreal.blend"
REPORT = HERE / "r05-verification.json"
EXPECTED_SOURCE_SHA256 = (
    "4c65762f65d35f5345bb3ad601aafdb0ce2809681931aad480586cc5747d3412")


def bounds_mm(obj):
    corners = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return {
        axis: [round(min(v[i] for v in corners) * 1000, 4),
               round(max(v[i] for v in corners) * 1000, 4)]
        for i, axis in enumerate(("x", "y", "z"))
    }


def object_box_mm(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [[min(v[i] for v in corners) * 1000,
             max(v[i] for v in corners) * 1000] for i in range(3)]


def contains(box, point, tolerance=0.05):
    return all(low - tolerance <= value <= high + tolerance
               for (low, high), value in zip(box, point))


def route_ends_mm(obj):
    points = obj.data.splines[0].points
    world = [obj.matrix_world @ Vector(point.co[:3]) for point in points]
    return [[coordinate * 1000 for coordinate in world[index]]
            for index in (0, -1)]


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require(checks, name, condition, evidence):
    checks.append({"check": name, "pass": bool(condition), "evidence": evidence})


def ray_hits_y(obj, x_mm, z_mm):
    inverse = obj.matrix_world.inverted()
    origin = inverse @ Vector((x_mm / 1000, -0.1, z_mm / 1000))
    direction = (inverse.to_3x3() @ Vector((0, 1, 0))).normalized()
    return bool(obj.ray_cast(origin, direction, distance=0.2)[0])


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    checks = []

    board = bpy.data.objects["Main_PCBA"]
    c101 = bpy.data.objects["PCBA_C101"]
    c107 = bpy.data.objects["PCBA_C107"]
    board_box = bounds_mm(board)
    c101_box = bounds_mm(c101)
    c107_box = bounds_mm(c107)
    cap_gap_101 = round(c101_box["y"][0] - board_box["y"][1], 4)
    cap_gap_107 = round(c107_box["y"][0] - board_box["y"][1], 4)
    require(checks, "imported capacitors follow shifted board",
            0.0 <= cap_gap_101 <= 0.2 and 0.0 <= cap_gap_107 <= 0.2,
            {"board": board_box, "C101": c101_box, "C107": c107_box,
             "rear_face_gaps_mm": [cap_gap_101, cap_gap_107]})

    bosses = sorted(name for name in bpy.data.objects if "Thermal_Boss" in name)
    require(checks, "artificial housing bosses removed", not bosses, bosses)

    housing = bpy.data.objects["Main_Housing"]
    wire = bpy.data.objects["Main_Housing_Inspection_Wireframe"]
    require(checks, "housing defaults to solid", housing.display_type == "SOLID",
            housing.display_type)
    require(checks, "inspection wire is optional and hidden",
            wire.display_type == "WIRE" and wire.hide_viewport and wire.hide_render,
            {"display": wire.display_type, "hide_viewport": wire.hide_viewport,
             "hide_render": wire.hide_render})

    legacy = bpy.data.objects["USB_C_Receptacle_J1_LEGACY_LOCATION"]
    require(checks, "legacy right-edge J1 is hidden",
            legacy.hide_viewport and legacy.hide_render,
            {"hide_viewport": legacy.hide_viewport,
             "hide_render": legacy.hide_render})

    slot_data = {}
    for name in ("Thermal_Spreader", "Shield_Rear_Tray", "Shield_Front_Lid"):
        obj = bpy.data.objects[name]
        slot_data[name] = {
            "width_mm": obj.get("R05_Service_Slot_Width_mm"),
            "z_mm": list(obj.get("R05_Service_Slot_Z_mm", [])),
        }
    require(checks, "USB path is recorded through spreader and shields",
            all(v == {"width_mm": 15.0, "z_mm": [-24.0, -13.5]}
                for v in slot_data.values()), slot_data)
    center_hits = {name: ray_hits_y(bpy.data.objects[name], 0.0, -18.75)
                   for name in slot_data}
    require(checks, "USB service openings exist in native geometry",
            not any(center_hits.values()), center_hits)

    required_routes = (
        "Centered_USB_Daughterboard", "Mainboard_USB_Flex_Connector_CONCEPT",
        "USB3_PD_Internal_Flex_CONCEPT", "Face_Head_Power_Data_Flex_CONCEPT",
        "Interaction_Head_Power_Data_Flex_CONCEPT",
        "Face_Head_Flex_Interface_CONCEPT",
        "Interaction_Head_Flex_Interface_CONCEPT")
    require(checks, "proposed board and routes are present",
            all(name in bpy.data.objects for name in required_routes),
            list(required_routes))

    routed_connections = {}
    for route_name, start_name, end_name in (
            ("USB3_PD_Internal_Flex_CONCEPT", "Centered_USB_Daughterboard",
             "Mainboard_USB_Flex_Connector_CONCEPT"),
            ("Face_Head_Power_Data_Flex_CONCEPT",
             "Face_Optical_Head_Connector", "Face_Head_Flex_Interface_CONCEPT"),
            ("Interaction_Head_Power_Data_Flex_CONCEPT",
             "Interaction_Optical_Head_Connector",
             "Interaction_Head_Flex_Interface_CONCEPT")):
        start, end = route_ends_mm(bpy.data.objects[route_name])
        start_box = object_box_mm(bpy.data.objects[start_name])
        end_box = object_box_mm(bpy.data.objects[end_name])
        routed_connections[route_name] = {
            "start_inside": contains(start_box, start),
            "end_inside": contains(end_box, end),
            "start_mm": [round(v, 3) for v in start],
            "end_mm": [round(v, 3) for v in end],
        }
    require(checks, "route centerlines terminate in their modeled interfaces",
            all(item["start_inside"] and item["end_inside"]
                for item in routed_connections.values()), routed_connections)

    thermal_names = tuple(
        f"{kind}_{side}" for kind in ("Thermal_Link", "Housing_Thermal_Pad")
        for side in ("Left", "Right"))
    thermal_boxes = {name: bounds_mm(bpy.data.objects[name]) for name in thermal_names}
    require(checks, "bounded thermal links are inside nominal housing width",
            all(box["x"][0] >= -54 and box["x"][1] <= 54
                for box in thermal_boxes.values()), thermal_boxes)

    port_parts = [bpy.data.objects[name] for name in (
        "Main_Housing_USB_Back", "Main_Housing_USB_Shell",
        "Main_Housing_USB_Tongue")]
    port_x = [round(obj.location.x * 1000, 6) for obj in port_parts]
    require(checks, "external USB port is centered",
            all(abs(value) < 1e-6 for value in port_x),
            {obj.name: value for obj, value in zip(port_parts, port_x)})

    source_hash = sha256(SOURCE)
    require(checks, "authoritative source blend hash unchanged",
            source_hash == EXPECTED_SOURCE_SHA256,
            {"actual": source_hash, "expected": EXPECTED_SOURCE_SHA256})

    report = {
        "file": str(BLEND),
        "source": str(SOURCE),
        "result": "PASS" if all(c["pass"] for c in checks) else "FAIL",
        "checks": checks,
        "limitations": [
            "No electrical continuity or pin mapping is established by this model.",
            "Daughterboard, flex, connector, shielding, SI, thermal, and fit details remain unverified.",
            "The existing main-board J1 location cannot serve the centered-port concept without redesign."
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
