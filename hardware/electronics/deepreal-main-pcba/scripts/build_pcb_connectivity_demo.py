#!/usr/bin/env python3
"""Build a separate, non-native presentation graph with complete R/C accounting."""

import argparse
from collections import deque
import copy
import csv
import hashlib
import json
import math
from pathlib import Path

from presentation_pcb_connectivity import ConnectionRouter, GROUND, connection_plan, endpoint, pad_key

ROOT = Path(__file__).resolve().parents[4]
OLD = ROOT / "blender/review-output/web/pcb-visual-demo-02-r2/visual-routing-demo.json"
MANIFEST = ROOT / "blender/review-output/web/pcb-visual-05-aon01/main-pcba-review.json"


def write(path, data):
    if path.exists():
        raise ValueError("Refusing to overwrite " + str(path))
    path.write_text(json.dumps(data, separators=(",", ":")) + "\n")


def write_connection_csv(path, demo):
    if path.exists():
        raise ValueError("Refusing to overwrite a connection ledger")
    roots = {}
    for r in demo["connection_map"]["roots"]:
        roots.setdefault(r["net_id"], []).append(f'{r["ref"]}.{r["pad"]}')
    vias = {v["id"]: v for v in demo["vias"]}
    fields = ["reference", "kind", "proposed_role", "terminal", "side", "classification",
              "native_net", "proposed_net", "via_id", "via_span", "via_taps",
              "target_layer", "outer_connection", "inner_paths", "proposed_interface_pads",
              "native_track_evidence", "pin_functions_verified", "fabrication_allowed"]
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for part in demo["connection_map"]["parts"]:
            for t in part["terminals"]:
                native = t["mode"] == "engineering_reference"
                via = None if native else vias[t["via_id"]]
                writer.writerow({
                    "reference": part["ref"], "kind": part["kind"], "proposed_role": part["role"],
                    "terminal": t["pad"], "side": "front" if t["surface_layer"] == 0 else "back",
                    "classification": t["mode"], "native_net": t.get("native_net", ""),
                    "proposed_net": t.get("net_id", ""), "via_id": t.get("via_id", ""),
                    "via_span": "" if native else "1-10",
                    "via_taps": "" if native else ";".join(map(str, via["taps"])),
                    "target_layer": t.get("target_layer", ""), "outer_connection": t.get("connection_id", ""),
                    "inner_paths": ";".join(p["id"] for p in demo["inner_paths"]
                                           if not native and via["id"] in (p["from_via"], p["to_via"])),
                    "proposed_interface_pads": ";".join(roots.get(t.get("net_id"), [])),
                    "native_track_evidence": ";".join(t.get("native_track_ids", [])),
                    "pin_functions_verified": False, "fabrication_allowed": False,
                })


def revise_source_metadata(source_directory, output):
    """Correct D9's known intent without changing reviewed routing geometry."""
    if output.exists():
        raise ValueError("Choose a new metadata revision directory")
    original = (source_directory / "visual-routing-demo.json").read_bytes()
    demo = json.loads(original)
    if demo["schema"] != "deepreal.pcb-visual-demo.v3":
        raise ValueError("Metadata revision requires a v3 connection graph")
    with (ROOT / "hardware/electronics/deepreal-main-pcba/component-register.csv").open() as stream:
        source_row = next(row for row in csv.reader(stream) if row and row[0] == "D9")
    if source_row[1] != "VBUS TVS":
        raise ValueError("D9's source intent changed")
    geometry_keys = ("connections", "vias", "inner_paths", "return_planes", "endpoint_pads",
                     "native_evidence", "packages", "outlines_mm", "surface_z_m",
                     "pad_surface_z_m", "focus_bounds_mm", "silkscreen_exclusions")

    def geometry_sha(data):
        return hashlib.sha256(json.dumps({k: data[k] for k in geometry_keys},
                                        sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    before = geometry_sha(demo)
    part = next(p for p in demo["connection_map"]["parts"] if p["ref"] == "D9")
    part["role"] = "proposed_tvs_shunt"
    part["source_intent"] = "VBUS TVS, selection required. The proposed protected node is not a verified USB_VBUS connection."
    for root in demo["connection_map"]["roots"]:
        if root["net_id"] == "CONCEPT_NODE_D9":
            root["purpose"] = "proposed_unverified_protected_node"
    for net in demo["connection_map"]["nets"]:
        if net["id"] == "CONCEPT_NODE_D9":
            net["role"] = "proposed_unverified_protected_node"
    demo["visual_revision"] = "EXPLICIT_PASSIVE_CONNECTIONS_03_R2"
    demo["previous_presentation_data_sha256"] = hashlib.sha256(original).hexdigest()
    if "native_inferred_net_labels_not_verified" in demo:
        demo["historical_native_inferred_net_labels_not_verified"] = demo.pop("native_inferred_net_labels_not_verified")
    demo["limits"] = [s.replace("filter and indicator roles", "filter and TVS-shunt roles") for s in demo["limits"]]
    demo["geometry_projection_sha256"] = before
    assert geometry_sha(demo) == before, "Metadata correction changed reviewed geometry"
    output.mkdir()
    write(output / "visual-routing-demo.json", demo)
    write_connection_csv(output / "connection-map.csv", demo)
    report = json.loads((source_directory / "build-report.json").read_text())
    report.update({
        "status": "METADATA_REVISION_REQUIRES_FINAL_VALIDATION",
        "data_sha256": hashlib.sha256((output / "visual-routing-demo.json").read_bytes()).hexdigest(),
        "previous_data_sha256": hashlib.sha256(original).hexdigest(),
        "geometry_projection_sha256": before, "reviewed_geometry_unchanged": True,
        "metadata_correction": "D9 is the source register's VBUS TVS placeholder, not an indicator. Its actual protected rail/pin binding remains unverified.",
        "legacy_bus_connections_retained_after_envelope_check": 44,
        "legacy_bus_connections_retired_after_envelope_check": 29,
        "other_one_ended_local_routes_retired": 6,
    })
    write(output / "build-report.json", report)
    return report


def return_plane(router):
    """A connected raster region, with explicit clearance around other copper.

    Rectangles are presentation geometry, not a KiCad zone or fabrication fill.
    Keep only the connected main region and prove that every return barrel meets it.
    """
    space, step, origin = router.space, .10, [20, 20]
    nx = math.ceil((123-origin[0])/step)
    ny = math.ceil((48.5-origin[1])/step)
    cells = set()
    # Both planes must clear the native evidence on either reference layer.
    for y in range(ny):
        for x in range(nx):
            p = [origin[0]+(x+.5)*step, origin[1]+(y+.5)*step]
            if space.inside(p, .16) and all(space.clear(p, p, l, .075, GROUND) for l in (2, 9)):
                cells.add(y*nx+x)
    components = []
    unseen = set(cells)
    while unseen:
        start = unseen.pop()
        component, queue = {start}, deque([start])
        while queue:
            c = queue.popleft()
            for other in (c-1, c+1, c-nx, c+nx):
                if other in unseen and (other//nx == c//nx or other % nx == c % nx):
                    unseen.remove(other)
                    component.add(other)
                    queue.append(other)
        components.append(component)
    main = max(components, key=len)
    rectangles = []
    for y in range(ny):
        xs = sorted(c % nx for c in main if c//nx == y)
        if not xs:
            continue
        first = previous = xs[0]
        for x in xs[1:] + [nx+1]:
            if x != previous+1:
                rectangles.append([round(origin[0]+first*step, 6), round(origin[1]+y*step, 6),
                                   round(origin[0]+(previous+1)*step, 6), round(origin[1]+(y+1)*step, 6)])
                first = x
            previous = x
    for via in router.vias:
        if via["net_id"] != GROUND:
            continue
        p, radius = via["position_mm"], via["diameter_mm"]/2
        if not any(math.hypot(max(r[0]-p[0], 0, p[0]-r[2]), max(r[1]-p[1], 0, p[1]-r[3])) < radius
                   for r in rectangles):
            raise ValueError("Return via does not meet the connected reference region: " + via["id"])
        via["taps"] = sorted(set(via["taps"] + [2, 9]))
    return [{
        "id": f"RETURN_L{layer}", "net_id": GROUND, "layer": layer,
        "rectangles_mm": rectangles, "connected_region_count": 1,
        "raster_step_mm": step, "fabrication_fill": False,
    } for layer in (2, 9)]


def build_demo(geometry, old, plan, router, planes):
    demo = copy.deepcopy(old)
    demo.update({
        "schema": "deepreal.pcb-visual-demo.v3", "visual_revision": "EXPLICIT_PASSIVE_CONNECTIONS_03",
        "demo_board_sha256_is_historical": True, "native_export_matches_current_geometry": False,
        "connections": router.connections, "vias": router.vias, "connection_map": plan,
        "inner_paths": router.inner_paths, "return_planes": planes,
        "native_evidence": geometry["native_evidence"],
        "illustrative_connection_count": len(router.connections),
        "illustrative_segment_count": sum(len(p["points"])-1 for c in router.connections for p in c["paths"]),
        "illustrative_via_count": len(router.vias),
        "illustrative_inner_segment_count": sum(len(p["points"])-1 for p in router.inner_paths),
        "unrouted_visual_attempts": 0,
        "limits": [
            "Nonworking presentation geometry, not a verified circuit or a manufacturing design.",
            "Proposed bypass, bias, filter and TVS-shunt roles are placement-based templates. Actual IC pin functions, voltages, values and circuit feasibility are unresolved.",
            "Inner paths and connected return regions are explicit presentation geometry, not completed engineering routing or approved copper planes.",
            "Ten layer indices follow the unapproved preliminary intent. Layer spacing in the diagram is schematic; materials, dielectric thicknesses, via technology and impedance are unapproved.",
            "The native demo board hash identifies the historical v1 study only. No matching native export or fabrication files exist for this v3 graph.",
            "The 15 existing R/C circuits retain native pad and copper evidence. This does not qualify the whole board or resolve its inherited DRC findings.",
            "Complete two-terminal accounting does not establish complete chip, connector, protection-array, microphone or whole-board connectivity.",
            "Generic presentation packages follow existing envelopes and source pads, not manufacturer-qualified CAD.",
        ],
    })
    # Include every accounted terminal, plus the source-backed IC anchors and retained buses.
    wanted = {pad_key(t) for p in plan["parts"] for t in p["terminals"]}
    wanted.update(pad_key(t) for t in plan["roots"])
    wanted.update(pad_key(e) for c in router.connections for e in c["endpoints"] if e["ref"] != "VISUAL_VIA")
    source = {}
    for p in geometry["pads"]:
        if pad_key(p) in wanted:
            source[(p["ref"], p["pad"], *p["position"])] = {**endpoint(p), "layers": p["layers"]}
    demo["endpoint_pads"] = list(source.values())
    return demo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    geometry = json.loads(args.inputs.read_text())
    old = json.loads(OLD.read_text())
    manifest = json.loads(MANIFEST.read_text())
    source = ROOT / "tmp/usb-pd-interface-2026-10-16/mainboard-aon-07.kicad_pcb"
    glb = MANIFEST.with_suffix(".glb")
    if (geometry["native_evidence"]["source_sha256"] != old["source_board_sha256"]
            or hashlib.sha256(source.read_bytes()).hexdigest() != old["source_board_sha256"]
            or hashlib.sha256(glb.read_bytes()).hexdigest() != old["base_asset_sha256"]):
        raise ValueError("Source evidence changed")
    expected = connection_plan(geometry, old, {c["reference"] for c in manifest["components"]})
    if expected["rc_part_count"] != 199:
        raise ValueError("Displayed resistor/capacitor inventory changed")
    if not args.output:
        write(args.plan, expected)
        print(json.dumps({
            "status": "CONNECTION_PLAN_ONLY_NOT_ROUTED", "rc_parts": expected["rc_part_count"],
            "all_two_terminal_parts": expected["part_count"], "proposed_interfaces": len(expected["roots"]),
            "native_reference_parts": sum(p["role"] == "existing_partial_engineering" for p in expected["parts"]),
        }, indent=2))
        return
    plan = json.loads(args.plan.read_text())
    if plan != expected:
        raise ValueError("Plan differs from current source inventory")
    if args.output.exists():
        raise ValueError("Choose a new output directory")
    router = ConnectionRouter(geometry, old, plan).run(lambda text: print(text, flush=True))
    print("Building connected reference-region geometry", flush=True)
    planes = return_plane(router)
    demo = build_demo(geometry, old, plan, router, planes)
    args.output.mkdir()
    write(args.output / "visual-routing-demo.json", demo)
    write_connection_csv(args.output / "connection-map.csv", demo)
    report = {
        "status": "DRAFT_REQUIRES_INDEPENDENT_COVERAGE_AND_BROWSER_CHECKS",
        "source_board_sha256": old["source_board_sha256"], "base_asset_sha256": old["base_asset_sha256"],
        "data_sha256": hashlib.sha256((args.output / "visual-routing-demo.json").read_bytes()).hexdigest(),
        "rc_parts": 199, "all_two_terminal_parts": plan["part_count"],
        "native_reference_parts": 15, "surface_connections": len(router.connections),
        "vias": len(router.vias), "inner_paths": len(router.inner_paths),
        "reference_region_rectangles_per_layer": len(planes[0]["rectangles_mm"]),
        "old_one_ended_passive_routes_retired": 112, "old_unterminated_escape_stubs_retired": 81,
        "other_one_ended_local_routes_retired": 6,
        "legacy_bus_connections_retained_after_envelope_check": sum(c["purpose"].endswith(" bus") for c in router.connections),
        "legacy_bus_connections_retired_after_envelope_check": (
            sum(c["purpose"].endswith(" bus") for c in old["connections"])
            - sum(c["purpose"].endswith(" bus") for c in router.connections)),
        "engineering_files_modified": False, "electrical_qualification_claimed": False,
        "matching_native_export_exists": False,
    }
    write(args.output / "build-report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
