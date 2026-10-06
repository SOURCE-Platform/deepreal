#!/usr/bin/env python3
"""Check R14 assembly inventory, saved view and major hard-part clearances."""

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
sys.path.insert(0, str(HERE.parent / "r13"))
from verify_r13 import lens_results  # noqa: E402
sys.path.insert(0, str(HERE))
from r14_restore import donor_names  # noqa: E402

SOURCE = HERE.parent / "r13/deepreal-exterior-refinement-r13.blend"
BLEND = HERE / "deepreal-exterior-refinement-r14.blend"
REPORT = HERE / "r14-verification.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(label, passed, evidence):
    return {"check": label, "pass": bool(passed), "evidence": evidence}


def unchanged_source_geometry():
    names = (
        "Main_Housing", "Face_Sensor_Head", "Interaction_Sensor_Head",
        "Main_PCBA_Near_Full_Height_Right_Wing_PROPOSAL",
        "Thermal_Spreader", "Shield_Rear_Tray",
    )
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    before = {name: signature(bpy.data.objects[name]) for name in names}
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    return {name: signature(bpy.data.objects[name]) == original
            for name, original in before.items()}


def main():
    preserved = unchanged_source_geometry()
    checks = [check("R13 enclosure, PCB, drum and thermal meshes preserved",
                    all(preserved.values()), preserved)]

    restored = donor_names()
    missing = [name for name in restored if name not in bpy.data.objects]
    checks.append(check("44 motor and optical source parts restored",
                        len(restored) == 44 and not missing,
                        {"count": len(restored), "missing": missing}))

    created = []
    for side in ("Face", "Interaction"):
        created.extend((
            side + "_Head_PCBA_Carrier_CONCEPT",
            side + "_Head_Flex_Connector_PROXY",
            side + "_Head_Power_Data_Flex_ROUTE_CONCEPT",
            side + "_Motor_Power_Harness_ROUTE_CONCEPT",
            side + "_Encoder_Feedback_ROUTE_CONCEPT",
        ))
    checks.append(check("two head boards and both power/data/drive paths exist",
                        all(name in bpy.data.objects for name in created),
                        {name: name in bpy.data.objects for name in created}))
    obsolete = [side + "_Head_Flex_Interface_CONCEPT"
                for side in ("Face", "Interaction")]
    checks.append(check("obsolete unterminated flex proxies removed",
                        all(name not in bpy.data.objects for name in obsolete),
                        obsolete))

    route_ends = {}
    for side, sign, old_ref in (("Face", -1, "J2"),
                                ("Interaction", 1, "J3")):
        route = bpy.data.objects[
            side + "_Head_Power_Data_Flex_ROUTE_CONCEPT"]
        points = route.data.splines[0].points
        end = Vector(points[-1].co[:3]) * 1000
        target = Vector((sign * 22, 10.1, -23.5))
        route_ends[side] = {
            "last_point_mm": [round(v, 3) for v in end],
            "distance_to_nominal_J2_J3_mm": round((end - target).length, 4),
            "target": old_ref,
        }
    checks.append(check("head flex routes terminate at intended main-PCB area",
                        all(row["distance_to_nominal_J2_J3_mm"] < 0.01
                            for row in route_ends.values()), route_ends))

    hits = {}
    housing = tree(bpy.data.objects["Main_Housing"])
    for side in ("Face", "Interaction"):
        shell = tree(bpy.data.objects[side + "_Sensor_Head"])
        for name in restored:
            if not name.startswith(side + "_"):
                continue
            obj = bpy.data.objects[name]
            if obj.type != "MESH":
                continue
            part = tree(obj)
            shell_hits = len(part.overlap(shell))
            housing_hits = len(part.overlap(housing))
            if shell_hits or housing_hits:
                hits[name] = {"shell": shell_hits, "housing": housing_hits}
    checks.append(check("restored hard parts clear the drum shell and housing",
                        not hits, hits))

    left = bounds_mm(bpy.data.objects["Face_Sensor_Head"])[0][1]
    right = bounds_mm(bpy.data.objects["Interaction_Sensor_Head"])[0][0]
    checks.append(check("R13 one-millimeter center body gap retained",
                        abs(right - left - 1.0) < 0.001,
                        {"left_end_mm": left, "right_start_mm": right}))
    rays = lens_results()
    checks.append(check("all ten optical openings remain unobstructed by shells",
                        all(rays.values()), rays))

    housing_col = bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"]
    shell_col = bpy.data.collections[
        "01 — DRUM SHELLS — CLICK EYE FOR INTERNALS"]
    checks.append(check("saved file opens with housing and drum shells visible",
                        not housing_col.hide_viewport and not shell_col.hide_viewport
                        and not housing_col.hide_render
                        and not shell_col.hide_render,
                        {"housing": not housing_col.hide_viewport,
                         "drum_shells": not shell_col.hide_viewport}))
    distances = [area.spaces.active.region_3d.view_distance
                 for screen in bpy.data.screens for area in screen.areas
                 if area.type == "VIEW_3D"]
    checks.append(check("saved viewport remains close to the model",
                        bool(distances) and max(distances) <= 0.15,
                        [round(v, 5) for v in distances]))

    baseline = json.loads((HERE / "baseline.json").read_text())
    source_hashes = {rel: sha256(REPO / rel) == expected
                     for rel, expected in baseline["protected_sha256"].items()}
    checks.append(check("R13, donor and native PCB sources unchanged",
                        all(source_hashes.values()), source_hashes))
    status = subprocess.check_output(
        ["git", "status", "--short"], cwd=REPO, text=True).splitlines()
    unrelated = lambda rows: [row for row in rows
                              if not row[3:].startswith("blender/refinements/r14/")]
    checks.append(check("pre-existing unrelated edits remain untouched",
                        unrelated(status) == unrelated(baseline["git_status_before"]),
                        {"before": unrelated(baseline["git_status_before"]),
                         "after": unrelated(status)}))

    report = {"model": str(BLEND),
              "result": "PASS" if all(row["pass"] for row in checks) else "FAIL",
              "engineering_readiness": "BLOCKED", "checks": checks,
              "limits": [
                  "No verified head PCB schematic, copper, footprint or pinout.",
                  "Drum rotation feedthrough and flex fatigue are unresolved.",
                  "Drive torque, gearing, bearing fit, stop mounts and shell passages are unresolved.",
                  "Motor wiring and optical routes show intended paths, not routed nets.",
              ]}
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    for row in checks:
        print("PASS" if row["pass"] else "FAIL", row["check"])
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
