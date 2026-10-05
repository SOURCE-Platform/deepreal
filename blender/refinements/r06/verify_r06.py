#!/usr/bin/env python3
"""Verify the saved R06 model and its protected inputs."""

import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BLEND = HERE / "deepreal-exterior-refinement-r06.blend"
R05 = HERE.parent / "r05" / "deepreal-exterior-refinement-r05.blend"
DEEPREAL = REPO / "blender" / "deepreal.blend"
REPORT = HERE / "r06-verification.json"
EXPECTED = {
    str(R05): "f35eec8c33e1476d1a4a8d9cfc9c5197aa3c1f0843e10e874b817baf98a125f3",
    str(DEEPREAL): "4c65762f65d35f5345bb3ad601aafdb0ce2809681931aad480586cc5747d3412",
}


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def box_mm(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [[min(v[i] for v in corners) * 1000,
             max(v[i] for v in corners) * 1000] for i in range(3)]


def dimensions_mm(obj):
    box = box_mm(obj)
    return [round(high - low, 3) for low, high in box]


def check(rows, name, passed, evidence):
    rows.append({"check": name, "pass": bool(passed), "evidence": evidence})


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    rows = []

    housing = bpy.data.objects["Main_Housing"]
    toggle = bpy.data.collections["00 — HOUSING SHELL — CLICK EYE OR CAMERA"]
    check(rows, "housing has a one-collection visibility switch",
          list(toggle.objects) == [housing] and not toggle.hide_viewport,
          {"collection": toggle.name, "objects": [o.name for o in toggle.objects],
           "display_type": housing.display_type})

    unresolved = bpy.data.collections["98 — UNVERIFIED PCB BODY EVIDENCE — HIDDEN"]
    unresolved_names = sorted(o.name for o in unresolved.objects)
    check(rows, "unverified source bodies are retained but hidden",
          unresolved.hide_viewport and unresolved.hide_render and
          len(unresolved_names) == 5,
          {"objects": unresolved_names, "hidden_viewport": unresolved.hide_viewport,
           "hidden_render": unresolved.hide_render})

    proxy_rows = {}
    for ref, name in (
            ("J2", "J2_Face_Optical_Head_Connector_ENVELOPE"),
            ("J3", "J3_Interaction_Optical_Head_Connector_ENVELOPE")):
        obj = bpy.data.objects[name]
        proxy_rows[ref] = {
            "dimensions_mm": dimensions_mm(obj),
            "part": obj["Exact_Part"], "source": obj["Envelope_Source"],
            "bounds_mm": [[round(v, 3) for v in pair] for pair in box_mm(obj)],
        }
    check(rows, "J2 and J3 use manufacturer-dimensioned envelope proxies",
          all(item["dimensions_mm"] == [16.8, 1.0, 3.2]
              for item in proxy_rows.values()), proxy_rows)

    electronics = bpy.data.collections["02 — STATIONARY ELECTRONICS — PROVISIONAL"]
    housing_min_z = min(v.co.z for v in housing.data.vertices) * 1000
    below = {}
    for obj in electronics.all_objects:
        if obj.type != "MESH":
            continue
        minimum = box_mm(obj)[2][0]
        if minimum < housing_min_z - 0.01:
            below[obj.name] = round(minimum, 3)
    check(rows, "visible electronics do not extend below housing global envelope",
          not below, {"housing_min_z_mm": round(housing_min_z, 3),
                      "objects_below": below})

    overmold = bpy.data.objects["USB_C_Plug_Overmold"]
    overmold_box = box_mm(overmold)
    surface = float(housing["R06_USB_Surface_Z_mm"])
    insertion = round(overmold_box[2][1] - surface, 3)
    check(rows, "USB overmold enters its housing recess by at least 1 mm",
          insertion >= 1.0,
          {"surface_z_mm": surface, "overmold_bounds_mm": overmold_box,
           "axial_insertion_mm": insertion,
           "recess_mm": list(housing["R06_USB_Overmold_Recess_mm"])})

    source_results = {}
    for path_text, expected in EXPECTED.items():
        actual = sha256(Path(path_text))
        source_results[path_text] = {"actual": actual, "expected": expected,
                                     "match": actual == expected}
    check(rows, "R05 and authoritative DeepReal source hashes are unchanged",
          all(item["match"] for item in source_results.values()), source_results)

    result = "PASS" if all(row["pass"] for row in rows) else "FAIL"
    report = {
        "file": str(BLEND), "result": result, "checks": rows,
        "limitations": [
            "J2/J3 are dimensional envelope proxies, not detailed manufacturer STEP models.",
            "J4/J5 exact manufacturer parts remain unspecified and are a packaging blocker.",
            "The centered USB daughterboard, flex, pin mapping, SI, shielding, and thermal performance remain unverified."
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
