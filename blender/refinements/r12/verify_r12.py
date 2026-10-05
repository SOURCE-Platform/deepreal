#!/usr/bin/env python3
"""Check R12 review geometry and preserve its native source files."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import bounds_mm, tree  # noqa: E402

BLEND = HERE / "deepreal-exterior-refinement-r12.blend"
NATIVE = REPO / "hardware/electronics/deepreal-main-pcba/deepreal-main-pcba.kicad_pcb"
STUDY = HERE / "native-outline-H5-study-NOT-FOR-FAB.kicad_pcb"
REPORT = HERE / "r12-verification.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def geometry(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bad = sum(not edge.is_manifold for edge in bm.edges)
    visited = set()
    count = 0
    for vertex in bm.verts:
        if vertex in visited:
            continue
        count += 1
        stack = [vertex]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(edge.other_vert(current) for edge in current.link_edges)
    bm.free()
    return {"nonmanifold_edges": bad, "connected_components": count}


def hit(name, x, y, z, direction, distance_mm):
    location, _, _, _ = tree(bpy.data.objects[name]).ray_cast(
        Vector((x, y, z)) * 0.001, Vector(direction), distance_mm * 0.001)
    return location is not None


def check_native_copy():
    original = NATIVE.read_text()
    study = STUDY.read_text()
    edges = re.findall(r'\t\(gr_line\n.*?\n\t\)', study, re.S)
    edges = [e for e in edges if '(layer "Edge.Cuts")' in e]
    points = [(20, 20), (122.5, 20), (122.5, 46.5),
              (110, 46.5), (110, 48), (20, 48)]
    expected = set(zip(points, points[1:] + points[:1]))

    def xy(raw):
        return tuple(float(n) for n in raw.split())

    actual = {(xy(re.search(r'\(start ([^)]+)\)', edge).group(1)),
               xy(re.search(r'\(end ([^)]+)\)', edge).group(1)))
              for edge in edges}
    original_footprints = re.findall(r'\t\(footprint .*?\n\t\)', original, re.S)
    study_footprints = re.findall(r'\t\(footprint .*?\n\t\)', study, re.S)
    h5 = [f for f in study_footprints if '(property "Reference" "H5"' in f]
    original_j1 = [f for f in original_footprints
                   if '(property "Reference" "J1"' in f]
    study_j1 = [f for f in study_footprints
                if '(property "Reference" "J1"' in f]
    ids = re.findall(r'\(uuid "([0-9a-f-]{36})"\)', study)
    evidence = {
        "edge_count": len(edges), "expected_outline": actual == expected,
        "H5_count": len(h5),
        "H5_position": '(at 117 27.5)' in h5[0] if h5 else False,
        "H5_drill_2_7_mm": '(drill 2.7)' in h5[0] if h5 else False,
        "footprints_added": study.count('\t(footprint ') -
                            original.count('\t(footprint '),
        "uuid_duplicates": len(ids) - len(set(ids)),
        "native_J1_unchanged": len(original_j1) == len(study_j1) == 1
        and original_j1[0] == study_j1[0],
    }
    return evidence


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    checks = []

    def record(label, okay, evidence):
        checks.append({"check": label, "pass": bool(okay),
                       "evidence": evidence})

    board = bpy.data.objects["Main_PCBA_Near_Full_Height_Right_Wing_PROPOSAL"]
    bb = bounds_mm(board)
    shape = geometry(board)
    record("one connected board with near-full-height wing and H5 opening",
           shape == {"nonmanifold_edges": 0, "connected_components": 1}
           and bb[0] == [-45, 57.5] and bb[2] == [-25.5, 2.5]
           and not hit(board.name, 52, 15, -5, (0, -1, 0), 8)
           and hit(board.name, 55, 15, -5, (0, -1, 0), 8),
           {"bounds_mm": bb, "geometry": shape})

    socket_name = "USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED"
    socket = bpy.data.objects[socket_name]
    seated = len(tree(socket).overlap(tree(board)))
    socket_shape = geometry(socket)
    record("illustrative USB socket sits on the one-piece board",
           seated > 0 and socket_shape == {
               "nonmanifold_edges": 0, "connected_components": 1},
           {"triangle_intersections": seated, "socket_geometry": socket_shape,
            "actual_footprint_and_solder_joints_verified": False})

    surface = {name: bounds_mm(bpy.data.objects[name])[0]
               for name in ("PCBA_Native_Surface_03", "PCBA_Native_Surface_04")}
    record("native board finish spans the new wing on both faces",
           all(box[1] >= 57.499 for box in surface.values()), surface)

    support = {
        "pilot_axis_open": not hit("Main_Housing", 52, 11, -5,
                                   (0, -1, 0), 2),
        "boss_shoulders_present": all(
            hit("Main_Housing", x, 11, -5, (0, -1, 0), 1)
            for x in (50.2, 53.8)),
        "housing_status": bpy.data.objects["Main_Housing"].get(
            "R12_H5_Support", ""),
    }
    record("candidate housing support sits beneath H5, with blind pilot",
           support["pilot_axis_open"] and support["boss_shoulders_present"]
           and "unverified" in support["housing_status"], support)

    ends = {}
    for drum_name in ("Face_Sensor_Head", "Interaction_Sensor_Head"):
        drum_x = bounds_mm(bpy.data.objects[drum_name])[0]
        for side, edge, direction in (("Left", drum_x[0], 1),
                                      ("Right", drum_x[1], -1)):
            name = drum_name + "_Flat_End_" + side
            obj = bpy.data.objects[name]
            face_x = bounds_mm(obj)[0]
            ends[name] = {
                "flat_disk_manifold": geometry(obj)["nonmanifold_edges"] == 0,
                "covers_tube_radius_mm": round((bounds_mm(obj)[1][1] -
                                                  bounds_mm(obj)[1][0]) / 2, 2),
                "outside_shell_mm": round(
                    edge - face_x[0] if side == "Left" else face_x[1] - edge, 3),
                "center_ray_hits": hit(name, edge - direction, -1.5, 20,
                                       (direction, 0, 0), 3),
            }
    record("four flat end skins cover the drum rims",
           len(ends) == 4 and all(
               v["flat_disk_manifold"] and
               abs(v["covers_tube_radius_mm"] - 12) < 0.02 and
               0.2 <= v["outside_shell_mm"] <= 0.3 and
               v["center_ray_hits"] for v in ends.values()), ends)

    native = check_native_copy()
    record("separate native outline and H5 study is internally consistent",
           native["edge_count"] == 6 and native["expected_outline"]
           and native["H5_count"] == 1 and native["H5_position"]
           and native["H5_drill_2_7_mm"] and native["footprints_added"] == 1
           and native["uuid_duplicates"] == 0 and native["native_J1_unchanged"],
           native)

    baseline = json.loads((HERE / "baseline.json").read_text())
    hashes = {name: sha256(REPO / name) == old
              for name, old in baseline["protected_files_sha256"].items()}
    record("R11 and native PCB sources are unchanged", all(hashes.values()), hashes)
    status = subprocess.check_output(
        ["git", "status", "--short"], cwd=REPO, text=True).splitlines()
    # Committing this refinement removes its old untracked-directory entry.
    unrelated = lambda rows: [row for row in rows
                              if not row[3:].startswith("blender/refinements/")]
    record("unrelated prework Git changes are preserved",
           unrelated(status) == unrelated(baseline["git_status_before"]),
           {"before": unrelated(baseline["git_status_before"]),
            "after": unrelated(status)})

    report = {
        "file": str(BLEND),
        "result": "PASS" if all(c["pass"] for c in checks) else "FAIL",
        "checks": checks, "engineering_readiness": "BLOCKED",
        "limits": [
            "The new PCB outline and H5 support are layout concepts, not strength or fabrication validation.",
            "The separate native copy has no connector footprint/routing update and has not passed KiCad DRC.",
            "The drum end disks are presentation skins, not validated closures or bearing designs.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    for check in checks:
        print("PASS" if check["pass"] else "FAIL", check["check"])
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
