#!/usr/bin/env python3
"""Check transport fidelity separately from engineering readiness.

Run in the generated Blender file. A transport PASS never closes a design
gate. Projected model near-contacts are review candidates, not DRC verdicts.
"""

import itertools
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pcba_native_import import checked_inputs
from pcba_bom import ALL_PARTS


def bounds(obj):
    points = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    return [[min(p[i] for p in points)*1000 for i in range(3)],
            [max(p[i] for p in points)*1000 for i in range(3)]]


def inspect():
    data, manifest = checked_inputs()
    assembly = bpy.data.collections["Electronics Assembly"]
    objects = [o for o in assembly.objects if o.get("PCBA_Component")]
    refs = [o["PCBA_Ref"] for o in objects]
    by_ref = {c["ref"]: c for c in data["components"]}
    expected = set(by_ref)-set(manifest["pad_or_hole_only_refs"])
    failures = []
    if len(refs) != len(set(refs)) or set(refs) != expected:
        failures.append("component population differs from the full KiCad inventory")
    for obj in assembly.objects:
        if obj.name.startswith(("PCBA_Ground_Via_", "PCB_Ground_Ring_",
                                "Shield_Ground_Via_")) or obj.get("PCBA_Visual_Copper"):
            failures.append("handmade copper is active: " + obj.name)
    for obj in objects:
        ref = obj["PCBA_Ref"]
        if obj.get("PCBA_SourceBoardHash") != manifest["source_board_sha256"]:
            failures.append(ref + " has stale provenance")
        if obj.get("PCBA_Side") != by_ref[ref]["side"]:
            failures.append(ref + " has the wrong board side")
        if obj.get("PCBA_RotationDeg") != by_ref[ref]["rotation_deg"]:
            failures.append(ref + " has the wrong source orientation")
    board = bpy.data.objects["Main_PCBA"]
    report = json.loads(board["PCBA_ImportReport"])
    if report["max_anchor_error_mm"] > .1:
        failures.append("footprint anchor transfer exceeds 0.1 mm")
    envelope_refs = sorted(o["PCBA_Ref"] for o in objects
                           if o["PCBA_ModelStatus"].startswith("REPRESENTATIVE"))
    if envelope_refs != sorted(manifest["missing_model_refs"]):
        failures.append("missing model accounting is inconsistent")
    lo, hi = bounds(board)
    span = [hi[i]-lo[i] for i in range(3)]
    x0, y0, x1, y1 = data["board"]["bounds_mm"]
    if abs(span[0]-(x1-x0)) > .1 or abs(span[2]-(y1-y0)) > .1:
        failures.append("rendered substrate does not match the KiCad outline bounds")
    boxes = {o["PCBA_Ref"]: bounds(o) for o in objects}
    candidates = []
    for a, b in itertools.combinations(objects, 2):
        if a["PCBA_Side"] != b["PCBA_Side"]:
            continue
        a0, a1 = boxes[a["PCBA_Ref"]]
        b0, b1 = boxes[b["PCBA_Ref"]]
        gaps = [max(b0[i]-a1[i], a0[i]-b1[i]) for i in (0, 2)]
        if max(gaps) <= .05:
            candidates.append({"refs": [a["PCBA_Ref"], b["PCBA_Ref"]],
                "projected_axis_gaps_mm": [round(v, 5) for v in gaps],
                "status": "REVIEW_CANDIDATE_MODEL_BOUNDS_NOT_COURTYARD_DRC"})
    views = {}
    for name in ("06 PCBA Top", "07 PCBA Bottom", "08 PCBA Dimensioned",
                 "04 Electronics Exploded", "05 Shield Cutaway"):
        scene = bpy.data.scenes.get(name)
        if not scene:
            failures.append("missing view: " + name)
            continue
        scene_refs = [o["PCBA_Ref"] for o in scene.objects if o.get("PCBA_Component")]
        views[name] = len(scene_refs)
        if set(scene_refs) != expected:
            failures.append("view loses components: " + name)
        for clone in scene.objects:
            source_name = clone.get("Linked_Source_Object")
            if source_name and clone.data is not bpy.data.objects[source_name].data:
                failures.append("view has independent geometry: " + clone.name)
        if name in {"06 PCBA Top", "07 PCBA Bottom", "08 PCBA Dimensioned"}:
            # Evaluating each scene matters: stale matrices can conceal a
            # carried-over laptop hinge rotation until rendering starts.
            previous_scene = bpy.context.window.scene
            bpy.context.window.scene = scene
            bpy.context.view_layer.update()
            for clone in scene.objects:
                if not (clone.get("PCBA_Component") or clone.get("PCBA_NativeSurface")):
                    continue
                source = bpy.data.objects[clone["Linked_Source_Object"]]
                error = max((clone.matrix_world @ Vector(p) -
                             source.matrix_world @ Vector(p)).length*1000
                            for p in clone.bound_box)
                if error > .1:
                    failures.append("presentation moves geometry: " + clone.name)
            bpy.context.window.scene = previous_scene
            bpy.context.view_layer.update()
    report.update({"schema": "deepreal.native-import-check.v1",
        "source_board_sha256": manifest["source_board_sha256"],
        "transport_status": "FAIL" if failures else "PASS",
        "transport_failures": failures, "view_component_counts": views,
        "projected_near_contact_candidates": candidates,
        "missing_required_metadata_refs": sorted({p["ref"] for p in ALL_PARTS}-set(by_ref)),
        "pads_in_canonical_export": len(data["pads"]),
        "named_pad_nets": sorted({p["net"] for p in data["pads"] if p["net"]}),
        "warning": "Footprints, circuits, routing, mechanics and head interfaces are NOT approved."})
    destination = HERE / "review-output"
    destination.mkdir(exist_ok=True)
    (destination / "native-import-check.json").write_text(json.dumps(report, indent=2)+"\n")
    print("TRANSPORT:", report["transport_status"], "| ENGINEERING: BLOCKED | PUBLICATION: BLOCKED")
    print("Native models / envelopes / holes:", len(manifest["native_model_refs"]),
          len(envelope_refs), len(manifest["pad_or_hole_only_refs"]))
    print("Projected near-contact review candidates:", len(candidates))
    if failures:
        raise RuntimeError("\n".join(failures))


def main():
    scene = bpy.data.scenes["SOURCE - Canonical Assembly"]
    bpy.context.window.scene = scene
    pivot = bpy.data.objects.get("Lid_Pivot")
    original = pivot.rotation_euler.copy() if pivot else None
    try:
        if pivot:
            pivot.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        inspect()
    finally:
        if pivot:
            pivot.rotation_euler = original
        bpy.context.view_layer.update()


if __name__ == "__main__":
    main()
