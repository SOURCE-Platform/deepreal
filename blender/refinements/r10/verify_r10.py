#!/usr/bin/env python3
"""Check continuity, seating, clearances, outline copy and protected files."""

import bmesh
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import bounds_mm, tree  # noqa: E402

BLEND = HERE / "deepreal-exterior-refinement-r10.blend"
OUTLINE = HERE / "native-outline-study-NOT-FOR-FAB.kicad_pcb"
REPORT = HERE / "r10-verification.json"
BOARD = "Main_PCBA_Continuous_Right_USB_Tab_PROPOSAL"
SOCKET = "USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED"


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def overlap(a, b):
    return len(tree(bpy.data.objects[a]).overlap(tree(bpy.data.objects[b])))


def mesh_stats(obj):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    vertices = set(mesh.verts)
    parts = 0
    while vertices:
        parts += 1
        stack = [vertices.pop()]
        while stack:
            for edge in stack.pop().link_edges:
                for neighbor in edge.verts:
                    if neighbor in vertices:
                        vertices.remove(neighbor)
                        stack.append(neighbor)
    stats = {"connected_components": parts,
             "nonmanifold_edges": sum(not e.is_manifold for e in mesh.edges),
             "faces": len(mesh.faces)}
    mesh.free()
    return stats


def outline_edges(text):
    blocks = re.findall(r'\t\(gr_line\n.*?\n\t\)', text, re.S)
    edges = []
    for block in blocks:
        if '(layer "Edge.Cuts")' not in block:
            continue
        start = re.search(r'\(start ([\d.]+) ([\d.]+)\)', block)
        end = re.search(r'\(end ([\d.]+) ([\d.]+)\)', block)
        edges.append(((float(start[1]), float(start[2])),
                      (float(end[1]), float(end[2]))))
    return edges


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    checks = []

    def record(label, okay, evidence):
        checks.append({"check": label, "pass": bool(okay),
                       "evidence": evidence})

    board = bpy.data.objects[BOARD]
    stats = mesh_stats(board)
    box = bounds_mm(board)
    record("one continuous manifold board with integral right tab",
           stats["connected_components"] == 1
           and stats["nonmanifold_edges"] == 0
           and round(box[0][0], 1) == -45
           and round(box[0][1], 1) == 57.5
           and bpy.data.objects.get(
               "Main_PCBA_Right_USB_Tab_GEOMETRY_PROPOSAL") is None,
           {**stats, "bounds_mm": box, "separate_tab_present": False})

    old = bpy.data.objects["Main_PCBA_Imported_Artwork_HIDDEN_REFERENCE"]
    record("unaltered imported board visual hidden as reference",
           old.hide_render and old.hide_get(),
           {"hide_render": old.hide_render, "hide_viewport": old.hide_get()})

    socket_stats = mesh_stats(bpy.data.objects[SOCKET])
    socket_board_overlap = overlap(SOCKET, BOARD)
    feet = [o.name for o in bpy.data.objects
            if o.name.startswith("USB_Socket_Illustrative_Seat_")]
    record("socket seating geometry is one manifold object on board",
           socket_stats["connected_components"] == 1
           and socket_stats["nonmanifold_edges"] == 0
           and socket_board_overlap > 0 and not feet,
           {**socket_stats, "socket_board_triangle_intersections":
            socket_board_overlap, "loose_seating_objects": feet,
            "electrical_attachment_verified": False})

    spreader = bounds_mm(bpy.data.objects["Thermal_Spreader"])
    socket = bounds_mm(bpy.data.objects[SOCKET])
    gap = round(socket[0][0] - spreader[0][1], 3)
    record("socket envelope separated laterally from spreader",
           gap > 0 and overlap(SOCKET, "Thermal_Spreader") == 0,
           {"gap_mm": gap, "thermal_safety_established": False})

    pairs = ((SOCKET, "Main_Housing"), (SOCKET, "Shield_Rear_Tray"),
             ("USB_C_Plug_Overmold", "Main_Housing"),
             ("USB_C_Plug_Overmold", "Thermal_Spreader"))
    collisions = {a + " <> " + b: overlap(a, b) for a, b in pairs}
    record("listed housing, shield and spreader clashes absent",
           all(count == 0 for count in collisions.values()), collisions)

    source_pcb = (REPO / "hardware/electronics/deepreal-main-pcba/"
                  "deepreal-main-pcba.kicad_pcb")
    original = source_pcb.read_text()
    proposal = OUTLINE.read_text()
    edges = outline_edges(proposal)
    expected = [(20, 20), (110, 20), (110, 32.5), (122.5, 32.5),
                (122.5, 45), (110, 45), (110, 48), (20, 48)]
    record("native outline study has one closed integral extension",
           len(edges) == 8
           and [a for a, _ in edges] == expected
           and [b for _, b in edges] == expected[1:] + expected[:1],
           {"edges": edges, "closed": bool(edges and edges[-1][1] == edges[0][0])})
    record("outline study retains all original footprints and J1 placement",
           proposal.count("\t(footprint ") == original.count("\t(footprint ")
           and '(at 106.075 34)' in proposal,
           {"original_footprints": original.count("\t(footprint "),
            "proposal_footprints": proposal.count("\t(footprint "),
            "J1_not_relocated": True})

    baseline = json.loads((HERE.parent / "r09" / "baseline.json").read_text())
    protected = {name: hash_file(REPO / name) == expected_hash
                 for name, expected_hash in baseline[
                     "protected_files_sha256"].items()}
    record("protected KiCad and R08 files match baseline hashes",
           all(protected.values()), protected)

    report = {"file": str(BLEND), "result": "PASS" if all(
        check["pass"] for check in checks) else "FAIL", "checks": checks,
        "engineering_readiness": "BLOCKED",
        "limitations": [
            "Blender mesh continuity does not validate PCB fabrication or routing.",
            "KiCad copy changes only Edge.Cuts; original J1 is still misplaced and "
            "has an unresolved part/footprint mismatch.",
            "Socket feet are illustrative, not a verified connector footprint.",
            "No thermal, USB signal, electrical or insertion-force validation."],
        "protected_hashes": {name: hash_file(REPO / name) for name in protected}}
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
