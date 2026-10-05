#!/usr/bin/env python3
"""Check saved R09 packaging geometry and protected source files."""

import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import bounds_mm, tree  # noqa: E402

R08 = HERE.parent / "r08" / "deepreal-exterior-refinement-r08.blend"
R09 = HERE / "deepreal-exterior-refinement-r09.blend"
REPORT = HERE / "r09-verification.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collision(a, b):
    return len(tree(bpy.data.objects[a]).overlap(tree(bpy.data.objects[b])))


def record(checks, label, okay, evidence):
    checks.append({"check": label, "pass": bool(okay), "evidence": evidence})


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R08))
    old_overlap = collision("USB_C_Plug_Overmold", "Thermal_Spreader")
    bpy.ops.wm.open_mainfile(filepath=str(R09))
    checks = []
    removed = ("Centered_USB_Daughterboard", "USB_Power_Data_Side_Route_CONCEPT",
               "Mainboard_USB_Flex_Connector_CONCEPT", "Main_Housing_USB_Back",
               "Main_Housing_USB_Cutter", "Main_Housing_USB_Shell",
               "Main_Housing_USB_Tongue")
    record(checks, "centered daughterboard and flex study removed",
           all(bpy.data.objects.get(name) is None for name in removed), list(removed))

    tab = "Main_PCBA_Right_USB_Tab_GEOMETRY_PROPOSAL"
    socket = "USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED"
    spreader = "Thermal_Spreader"
    socket_box, spreader_box = (bounds_mm(bpy.data.objects[name])
                                for name in (socket, spreader))
    lateral_gap = round(socket_box[0][0] - spreader_box[0][1], 3)
    record(checks, "socket is outside spreader footprint",
           lateral_gap > 0 and collision(socket, spreader) == 0,
           {"socket_to_spreader_lateral_mm": lateral_gap,
            "physical_temperature_verified": False})

    contacts = {"tab_to_source_board": collision(tab, "Main_PCBA"),
                "socket_to_tab": collision(socket, tab)}
    record(checks, "conceptual tab touches original board and socket",
           all(value > 0 for value in contacts.values()), contacts)

    blocked_pairs = (
        (tab, "Shield_Rear_Tray"), (tab, "Main_Housing"),
        (tab, spreader), (tab, "Shield_Front_Lid"),
        (socket, "Shield_Rear_Tray"),
        (socket, "Shield_Front_Lid"), (socket, "Main_Housing"),
        ("USB_C_Plug_Overmold", spreader),
        ("USB_C_Plug_Overmold", "Shield_Rear_Tray"),
        ("USB_C_Plug_Overmold", "Main_Housing"),
        ("USB_C_Plug_Overmold", "Housing_Thermal_Pad_Right"),
        ("USB_C_Plug_Overmold", "Thermal_Link_Right"),
        ("USB_C_Male_Metal_Shell", spreader),
        ("USB_C_Male_Metal_Shell", "Shield_Rear_Tray"),
        ("USB_C_Male_Metal_Shell", "Main_Housing"),
        ("USB_C_Cable", "Shield_Rear_Tray"),
        ("USB_C_Cable", "Main_Housing"),
    )
    overlaps = {f"{a} <> {b}": collision(a, b) for a, b in blocked_pairs}
    record(checks, "listed unintended mesh intersections are absent",
           all(count == 0 for count in overlaps.values()), overlaps)

    shield_ray = tree(bpy.data.objects["Shield_Rear_Tray"]).ray_cast(
        Vector((0.043, 0.01135, -0.01625)), Vector((1, 0, 0)), 0.006)[0]
    center_ray = tree(bpy.data.objects["Main_Housing"]).ray_cast(
        Vector((0, 0.018, -0.035)), Vector((0, 0, 1)), 0.03)[0]
    right_ray = tree(bpy.data.objects["Main_Housing"]).ray_cast(
        Vector((0.0515, 0.01415, -0.035)), Vector((0, 0, 1)), 0.03)[0]
    record(checks, "side shield and housing entry open; center housing closed",
           shield_ray is None and center_ray is not None and right_ray is None,
           {"side_shield_ray_hit": shield_ray is not None,
            "center_housing_ray_hit": center_ray is not None,
            "right_housing_ray_hit": right_ray is not None,
            "shield_wall_faces_removed": bpy.data.objects[
                "Shield_Rear_Tray"]["R09_Removed_Side_Wall_Faces"]})

    views = [area.spaces.active.region_3d.view_distance
             for screen in bpy.data.screens for area in screen.areas
             if area.type == "VIEW_3D"]
    record(checks, "saved model opens at close review scale",
           bool(views) and all(distance <= 0.15 for distance in views), views)

    baseline = json.loads((HERE / "baseline.json").read_text())
    protected = {name: {"expected": expected,
                        "actual": sha256(REPO / name)}
                 for name, expected in baseline["protected_files_sha256"].items()}
    record(checks, "protected R08 and KiCad files unchanged",
           all(v["expected"] == v["actual"] for v in protected.values()), protected)

    report = {
        "file": str(R09), "result": "PASS" if all(c["pass"] for c in checks)
        else "FAIL", "checks": checks,
        "r08_plug_spreader_triangle_intersections": old_overlap,
        "r09_plug_spreader_triangle_intersections": collision(
            "USB_C_Plug_Overmold", spreader),
        "engineering_readiness": "BLOCKED",
        "limits": [
            "Board tab and socket are Blender geometry only; KiCad board unchanged.",
            "Exact USB-C receptacle, mating cable, pads and solder joints unverified.",
            "No USB power/data routing, SI, thermal, shield/EMI or retention approval.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
