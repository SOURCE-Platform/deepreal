#!/usr/bin/env python3
"""Measure retained mechanical interfaces, without saving either Blender input."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_fit_geometry import section_loops, to_kicad

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "r36": ROOT / "blender/refinements/r36/deepreal-inner-bearing-window-r36.blend",
    "r38": ROOT / "blender/refinements/r38/deepreal-exterior-mount-r38.blend",
}
NATIVE_SOURCE = ROOT / "blender/deepreal.blend"
BOARD_NAME = "Main_PCBA_Near_Full_Height_Right_Wing_PROPOSAL"
INTERFACES = {
    "J1": "USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED",
    "J2": "J2_Face_Optical_Head_Connector_ENVELOPE",
    "J3": "J3_Interaction_Optical_Head_Connector_ENVELOPE",
    "J4": "J4_Face_Motor_Encoder_Connector_PROXY",
    "J5": "J5_Interaction_Motor_Encoder_Connector_PROXY",
    "usb_plug_shell": "USB_C_Male_Metal_Shell",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry(obj):
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    try:
        matrix = obj.matrix_world
        vertices = [list(matrix @ vertex.co * 1000) for vertex in mesh.vertices]
        mesh.calc_loop_triangles()
        triangles = [list(triangle.vertices) for triangle in mesh.loop_triangles]
        return vertices, triangles
    finally:
        obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()


def bounds(obj):
    vertices, _ = geometry(obj)
    # Web X/height/depth = Blender X/Z/-Y, all measured in millimetres.
    points = [[v[0], v[2], -v[1]] for v in vertices]
    lo = [round(min(v[i] for v in points), 6) for i in range(3)]
    hi = [round(max(v[i] for v in points), 6) for i in range(3)]
    return {"object": obj.name, "min_mm": lo, "max_mm": hi,
            "center_mm": [round((a + b) / 2, 6) for a, b in zip(lo, hi)],
            "size_mm": [round(b - a, 6) for a, b in zip(lo, hi)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if not args.output.is_absolute() or args.output.exists():
        parser.error("use a new absolute output path")
    project = ROOT / "hardware/electronics/deepreal-main-pcba"
    data = json.loads((project / "engineering-layout-export.json").read_text())
    x0, y0, x1, y1 = data["board"]["bounds_mm"]
    origin = [(x0 + x1) / 2, (y0 + y1) / 2]
    hashes = {str(path.relative_to(ROOT)): digest(path)
              for path in list(SOURCES.values()) + [NATIVE_SOURCE]}
    measurements = {}
    for label, path in SOURCES.items():
        bpy.ops.wm.open_mainfile(filepath=str(path))
        if "Lid_Pivot" in bpy.data.objects:
            bpy.data.objects["Lid_Pivot"].rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        board = bpy.data.objects[BOARD_NAME]
        box = bounds(board)
        vertices, triangles = geometry(board)
        loops = section_loops(vertices, triangles, -box["center_mm"][2])
        measurements[label] = {
            "board": box, "profile_loops_web_mm": loops,
            "interfaces": {ref: bounds(bpy.data.objects[name])
                           for ref, name in INTERFACES.items()},
        }
    if measurements["r36"] != measurements["r38"]:
        raise ValueError("R36/R38 PCB interfaces differ; do not merge silently")
    current = measurements["r36"]
    center_height = current["board"]["center_mm"][1]
    for item in current["interfaces"].values():
        item["body_center_kicad_mm"] = to_kicad(
            item["center_mm"][:2], origin, center_height)
        item["anchor_status"] = "BODY_CENTRE_ONLY_NOT_A_FOOTPRINT_ANCHOR"
    # Inventory every retained native body, not the website's sparse selection.
    # Register the board plane once; never move individual viewer components.
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE_SOURCE))
    bpy.context.window.scene = bpy.data.scenes["SOURCE - Canonical Assembly"]
    bpy.data.objects["Lid_Pivot"].rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    native_plane = bounds(bpy.data.objects["Main_PCBA"])["center_mm"][2]
    depth_offset = current["board"]["center_mm"][2] - native_plane
    bodies = {}
    for obj in bpy.data.collections["Electronics Assembly"].objects:
        if not obj.get("PCBA_Component"):
            continue
        if obj.get("PCBA_SourceBoardHash") != digest(project / "deepreal-main-pcba.kicad_pcb"):
            raise ValueError("native body source board mismatch: " + obj.name)
        item = bounds(obj)
        for key in ("min_mm", "max_mm", "center_mm"):
            item[key][2] = round(item[key][2] + depth_offset, 6)
        item["model_status"] = obj["PCBA_ModelStatus"]
        item["side"] = obj["PCBA_Side"]
        bodies[obj["PCBA_Ref"]] = item
    expected = {c["ref"] for c in data["components"] if c["models"]}
    if set(bodies) != expected:
        raise ValueError("incomplete native component-body inventory")
    payload = {
        "schema": "deepreal.pcb-mechanical-interface.v1",
        "revision": "MECH-FIT-01",
        "status": "MEASURED_PRESENTATION_TARGET_NOT_APPROVED_INTERFACES",
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
        "sources_sha256": hashes,
        "source_board_sha256": digest(project / "deepreal-main-pcba.kicad_pcb"),
        "source_export_sha256": digest(project / "engineering-layout-export.json"),
        "source_status_sha256": digest(project / "design-status.json"),
        "coordinate_system": {
            "web_xyz_from_blender_xyz": ["X", "Z", "-Y"],
            "units": "mm", "kicad_origin_mm": origin,
            "board_center_height_mm": center_height,
            "board_center_web_depth_mm": current["board"]["center_mm"][2],
            "origin_policy": "KEEP_CORE_DATUM_NOT_EXTENDED_OUTLINE_CENTRE",
        },
        "board": current["board"],
        "profile_loops_web_mm": current["profile_loops_web_mm"],
        "profile_quantization_mm": 0.0001,
        "profile_loops_kicad_mm": [
            [to_kicad(p, origin, center_height) for p in loop]
            for loop in current["profile_loops_web_mm"]],
        "interfaces": current["interfaces"],
        "retained_component_bodies": bodies,
        "native_board_plane_registration_web_mm": [0, 0, round(depth_offset, 6)],
        "open": [
            "J1 unselected socket envelope; its body centre is not a land-pattern datum",
            "Hirose CX90M3-24P maximum recommended PCB thickness 0.8 mm conflicts with both 1.5 mm mechanical and 1.6 mm KiCad candidates",
            "J2/J3 envelopes do not establish latch, contact-side or numbered-pin orientation",
            "J4/J5 have no selected low-profile part or verified land pattern",
            "Profile cutouts are mechanical mesh sections, not approved plated mounting holes",
            "Full component, housing, flex and plug-insertion clearances are unvalidated",
            "Actual circuitry, final placements and all routing remain incomplete",
        ],
    }
    if any(digest(ROOT / path) != value for path, value in hashes.items()):
        raise ValueError("source changed during measurement")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
    print("MEASURED", args.output, "profile loops:", len(payload["profile_loops_web_mm"]))


if __name__ == "__main__":
    main()
