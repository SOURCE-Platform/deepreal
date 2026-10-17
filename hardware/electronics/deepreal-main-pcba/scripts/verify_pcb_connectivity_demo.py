#!/usr/bin/env python3
"""Independent source-inventory and presentation-envelope audit, not KiCad DRC."""

from collections import Counter, defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
import sys

from presentation_pcb_connectivity import pad_key, source_space


def audit(demo, geometry):
    native = geometry["native_evidence"]
    assert demo["native_evidence"] == native, "Native evidence was changed"
    source = defaultdict(dict)
    for p in geometry["pads"]:
        if p["pad"]:
            source[p["ref"]][p["pad"]] = p
    expected_rc = {r for r in source if r.startswith(("C", "R"))}
    parts = demo["connection_map"]["parts"]
    actual_rc = {p["ref"] for p in parts if p["kind"] in ("capacitor", "resistor")}
    assert expected_rc == actual_rc and len(expected_rc) == 199, "Incomplete source R/C inventory"
    native_pads = {pad_key(p): p for p in native["pads"]}
    reference_parts, proposed_terminals = 0, 0
    for part in parts:
        terminals = part["terminals"]
        assert set(t["pad"] for t in terminals) == set(source[part["ref"]]), "Missing source terminal"
        assert len(terminals) == 2
        for terminal in terminals:
            p = source[part["ref"]][terminal["pad"]]
            assert terminal["position"] == p["position"] and terminal["surface_layer"] in p["layers"]
            if terminal["mode"] == "engineering_reference":
                observed = native_pads[pad_key(terminal)]
                assert terminal["native_net"] == observed["net"]
                assert terminal["native_track_ids"] == observed["connected_track_uuids"]
            else:
                assert not p["net"], "A proposal overwrote a source-assigned terminal"
                proposed_terminals += 1
        reference_parts += part["role"] == "existing_partial_engineering"
    assert reference_parts == 15 and proposed_terminals == 388

    # First compare every added barrel against the source and every other barrel.
    space = source_space(geometry)
    for via in demo["vias"]:
        p = via["position_mm"]
        assert space.inside(p, via["diameter_mm"]/2+.045), "Via leaves native outline"
        assert all(space.clear(p, p, layer, via["diameter_mm"]/2, via=True)
                   for layer in range(1, 11)), "Via contacts another source pad/barrel"
        space.via(via, via["net_id"])
    segments = 0
    all_paths = []
    for connection in demo["connections"]:
        exempt = frozenset(pad_key(e) for e in connection["endpoints"] if e["ref"] != "VISUAL_VIA")
        for path in connection["paths"]:
            all_paths.append((path["points"], 1 if path["layer"] == 0 else 10,
                              connection["width_mm"], connection["net_id"], exempt))
    for path in demo["inner_paths"]:
        all_paths.append((path["points"], path["layer"], path["width_mm"], path["net_id"], frozenset()))
    for points, layer, width, net, exempt in all_paths:
        for a, b in zip(points, points[1:]):
            assert space.clear(a, b, layer, width/2, net, exempt), (
                "Presentation envelope contact", layer, net, a, b)
            count = max(1, math.ceil(math.dist(a, b)/.1))
            assert all(space.inside([a[i]+(b[i]-a[i])*j/count for i in (0, 1)])
                       for j in range(count+1)), "A segment crosses the board cutout"
            space.line(layer, a, b, width, net)
            segments += 1

    # The graph is reconstructed from the actual terminal/via/path records.
    vias = {v["id"]: v for v in demo["vias"]}
    connections = {c["id"]: c for c in demo["connections"]}
    graph = defaultdict(set)

    def join(a, b):
        graph[a].add(b)
        graph[b].add(a)

    for path in demo["inner_paths"]:
        a, b = vias[path["from_via"]], vias[path["to_via"]]
        assert a["position_mm"] == path["points"][0] and b["position_mm"] == path["points"][-1]
        assert a["net_id"] == path["net_id"] == b["net_id"]
        assert path["layer"] in a["taps"] and path["layer"] in b["taps"]
        join(a["id"], b["id"])
    for plane in demo["return_planes"]:
        for via in vias.values():
            if via["net_id"] != plane["net_id"] or plane["layer"] not in via["taps"]:
                continue
            x, y = via["position_mm"]
            assert any(math.hypot(max(x0-x, 0, x-x1), max(y0-y, 0, y-y1)) < via["diameter_mm"]/2
                       for x0, y0, x1, y1 in plane["rectangles_mm"])
            join(via["id"], plane["id"])
    roots = {r["via_id"] for r in demo["connection_map"]["roots"]}
    seen, queue = set(roots), deque(roots)
    while queue:
        for other in graph[queue.popleft()]:
            if other not in seen:
                seen.add(other)
                queue.append(other)
    for part in parts:
        for terminal in part["terminals"]:
            if terminal["mode"] == "engineering_reference":
                continue
            via = vias[terminal["via_id"]]
            c = connections[terminal["connection_id"]]
            assert c["endpoints"][0]["ref"] == part["ref"] and c["endpoints"][0]["pad"] == terminal["pad"]
            assert c["endpoints"][0]["position"] == terminal["position"]
            assert c["endpoints"][1]["position"] == via["position_mm"]
            assert via["net_id"] == c["net_id"] == terminal["net_id"] and via["id"] in seen
            assert terminal["target_layer"] in via["taps"]
    return {
        "status": "SOURCE_INVENTORY_GRAPH_AND_PRESENTATION_ENVELOPES_PASS_NOT_ELECTRICAL_DRC",
        "rc_parts": len(expected_rc), "rc_terminals": len(expected_rc)*2,
        "all_two_terminal_parts": len(parts), "all_terminals": len(parts)*2,
        "native_reference_parts": reference_parts, "native_reference_terminals": reference_parts*2,
        "proposed_part_terminals": proposed_terminals,
        "proposed_ic_interfaces": len(roots), "outer_connections": len(demo["connections"]),
        "inner_paths": len(demo["inner_paths"]), "audited_trace_segments": segments, "vias": len(vias),
        "inner_layer_path_counts": dict(Counter(p["layer"] for p in demo["inner_paths"])),
        "minimum_presentation_envelope_gap_mm": .045,
        "real_pin_functions_verified": False, "fabrication_rules_verified": False,
        "matching_native_export_exists": False,
    }


def main():
    inputs, data, output = map(Path, sys.argv[1:])
    if output.exists():
        raise ValueError("Choose a new evidence report")
    report = audit(json.loads(data.read_text()), json.loads(inputs.read_text()))
    report["data_sha256"] = hashlib.sha256(data.read_bytes()).hexdigest()
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
