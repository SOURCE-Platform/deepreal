#!/usr/bin/env python3
"""Verify the saved R04 geometry and write a machine-readable report."""

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUTPUT = HERE / "reports" / "r04-geometry-audit.json"
SOURCE_SHA256 = "4c65762f65d35f5345bb3ad601aafdb0ce2809681931aad480586cc5747d3412"
SOURCE_MTIME_EPOCH = 1789342681


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError("missing R04 object: " + name)
    return obj


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(p[i] for p in points) * 1000, 3) for i in range(3)],
        "max": [round(max(p[i] for p in points) * 1000, 3) for i in range(3)],
    }


def center(box, axis):
    return round((box["min"][axis] + box["max"][axis]) / 2.0, 3)


def overlaps(a, b):
    return all(min(a["max"][axis], b["max"][axis]) >
               max(a["min"][axis], b["min"][axis]) for axis in range(3))


def viewport_distances():
    values = []
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                values.append(round(area.spaces.active.region_3d.view_distance, 6))
    return values


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    bpy.context.view_layer.update()
    names = [
        "Face_Sensor_Head", "Interaction_Sensor_Head", "Main_PCBA",
        "Main_PCBA_Populated_Keepout", "Main_Housing_USB_Shell",
        "USB_C_Male_Metal_Shell", "USB_C_Plug_Overmold", "Thermal_Spreader",
        "Housing_Thermal_Pad_Left", "Housing_Thermal_Pad_Right",
        "Housing_Thermal_Boss_Left", "Housing_Thermal_Boss_Right",
    ]
    boxes = {name: bounds(required(name)) for name in names}
    face = boxes["Face_Sensor_Head"]
    interaction = boxes["Interaction_Sensor_Head"]
    panel = boxes["Main_Housing_USB_Shell"]
    plug = boxes["USB_C_Male_Metal_Shell"]
    overmold = boxes["USB_C_Plug_Overmold"]
    spreader = boxes["Thermal_Spreader"]
    left_pad = boxes["Housing_Thermal_Pad_Left"]
    right_pad = boxes["Housing_Thermal_Pad_Right"]
    left_boss = boxes["Housing_Thermal_Boss_Left"]
    right_boss = boxes["Housing_Thermal_Boss_Right"]
    drum_gap = abs(round(interaction["min"][0] - face["max"][0], 3))
    insertion = round(min(plug["max"][2], panel["max"][2]) -
                      max(plug["min"][2], panel["min"][2]), 3)
    metrics = {
        "drum_surface_gap_mm": drum_gap,
        "panel_usb_center_x_mm": center(panel, 0),
        "male_plug_center_x_mm": center(plug, 0),
        "overmold_center_x_mm": center(overmold, 0),
        "male_shell_insertion_overlap_z_mm": insertion,
        "overmold_to_housing_surface_z_gap_mm": round(
            -22.278 - overmold["max"][2], 3),
        "spreader_to_pad_contact_y_mm": round(
            left_pad["min"][1] - spreader["max"][1], 3),
        "pad_to_boss_contact_y_mm": round(
            left_boss["min"][1] - left_pad["max"][1], 3),
        "split_pad_center_channel_width_mm": round(
            right_pad["min"][0] - left_pad["max"][0], 3),
        "usb_shell_side_clearance_each_mm": round(
            panel["min"][0] - left_pad["max"][0], 3),
        "male_plug_side_clearance_each_mm": round(
            plug["min"][0] - left_pad["max"][0], 3),
        "saved_viewport_count": len(viewport_distances()),
    }
    thermal_parts = (left_pad, right_pad, left_boss, right_boss)
    checks = {
        "drums_touch_without_visible_gap": drum_gap == 0.0,
        "usb_assembly_is_centered": all(center(box, 0) == 0.0 for box in (
            panel, plug, overmold)),
        "male_shell_is_inserted": insertion >= 3.9,
        "overmold_is_seated_close_to_body": metrics[
            "overmold_to_housing_surface_z_gap_mm"] <= 0.25,
        "pad_touches_spreader": metrics["spreader_to_pad_contact_y_mm"] == 0.0,
        "boss_touches_pad": metrics["pad_to_boss_contact_y_mm"] == 0.0,
        "center_channel_clears_usb": not any(
            overlaps(panel, box) or overlaps(plug, box) for box in thermal_parts),
        "viewports_use_close_review_scale": all(
            value == 0.19 for value in viewport_distances()),
    }
    source = REPO / "blender" / "deepreal.blend"
    integrity = {
        "source_blend_sha256": sha256(source),
        "recorded_source_blend_sha256": SOURCE_SHA256,
        "source_blend_mtime_epoch": int(source.stat().st_mtime),
        "recorded_source_blend_mtime_epoch": SOURCE_MTIME_EPOCH,
        "note": "deepreal.blend is generated and Git-ignored; hash and pre-existing mtime are pinned here for repeat checks",
    }
    integrity["source_blend_matches_recorded_baseline"] = (
        integrity["source_blend_sha256"] == SOURCE_SHA256
        and integrity["source_blend_mtime_epoch"] == SOURCE_MTIME_EPOCH)
    checks["source_blend_unchanged"] = integrity[
        "source_blend_matches_recorded_baseline"]
    report = {
        "file": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "qualification": (
            "PASS verifies saved geometry and source-file integrity only. It does "
            "not approve thermal, electrical, tolerance, rotation, sealing, assembly, "
            "connector, or manufacturing performance."),
        "metrics": metrics,
        "checks": checks,
        "source_integrity": integrity,
        "bounds_mm": boxes,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"result": report["result"], "report": str(OUTPUT)}))
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
