#!/usr/bin/env python3
"""Replace U1/U6/U7 and source-defined local alias nets, preserving the fixed datum."""

import argparse
import copy
import json
import re
import subprocess
import uuid
from pathlib import Path

from build_pcb_fit_candidate import digest, top_level_blocks
from build_pcb_connector_candidate import child, replace_ranges
from build_pcb_model_candidate import merge_footprints, reference
from export_native_review import read_glb


REVISION = "MECH-FIT-05"
PREDECESSOR_HASH = "69332669aec680c6d2a9765ef0b695776f9646421717596a9bd78c99a0661d6e"
PACKAGES = {
    "U1": "NXP_IMX95_SOT2251-1",
    "U6": "NXP_PF53B_SOT2283-1",
    "U7": "NXP_PF53B_SOT2283-1",
}
ALIASES = {"PGND": {1, 2, 3, 17, 18, 19, 20, 24}, "LX": {21, 22, 23}}


def expected_net(ref, number):
    if ref in ("U6", "U7") and number.isdigit():
        for function, numbers in ALIASES.items():
            if int(number) in numbers:
                return f"PACKAGE_{ref}_{function}"
    return ""


def deterministic_blocks(text, components):
    edits = []
    for a, b, block in top_level_blocks(text)[0]:
        if not block.startswith("(footprint "):
            continue
        ref = reference(block)
        if ref not in PACKAGES:
            raise ValueError("unexpected replacement reference")
        root_uuid = child(block, "footprint", "uuid")[2]
        index = 0

        def identity(match):
            nonlocal index
            if match[0] == root_uuid:
                return '(uuid "{}")'.format(components[ref]["uuid"])
            index += 1
            return '(uuid "{}")'.format(uuid.uuid5(
                uuid.NAMESPACE_URL, f"deepreal:{REVISION}:{ref}:child:{index}"))

        block = re.sub(r'^\(footprint "[^"]+"',
                       f'(footprint "DeepReal_Evidence:{PACKAGES[ref]}"', block)
        edits.append((a, b, re.sub(r'\(uuid "[^"]+"\)', identity, block)))
    if len(edits) != 3:
        raise ValueError("three replacement footprints required")
    return replace_ranges(text, edits)


def verify_scope(before, after):
    old = {c["ref"]: c for c in before["components"]}
    new = {c["ref"]: c for c in after["components"]}
    if old.keys() != new.keys() or len(new) != 238:
        raise ValueError("component population changed")
    for ref in old:
        keys = ("uuid", "ref", "value", "position_mm", "rotation_deg", "side") \
            if ref in PACKAGES else tuple(old[ref])
        if any(old[ref][k] != new[ref][k] for k in keys):
            raise ValueError("unscoped component change: " + ref)
    for key in ("board", "holes", "tracks", "vias", "zones"):
        if before[key] != after[key]:
            raise ValueError("unscoped source section: " + key)
    if [p for p in before["pads"] if p["ref"] not in PACKAGES] != \
            [p for p in after["pads"] if p["ref"] not in PACKAGES]:
        raise ValueError("unscoped pad change")
    for ref, count in (("U1", 548), ("U6", 24), ("U7", 24)):
        pads = [p for p in after["pads"] if p["ref"] == ref]
        if len(pads) != count or len({p["number"] for p in pads}) != count:
            raise ValueError("unexpected package pad count: " + ref)
    if len(after["pads"]) != 2626 or after["tracks"] or after["vias"] or after["zones"]:
        raise ValueError("unrouted package-study classification changed")
    for pad in after["pads"]:
        expected = expected_net(pad["ref"], pad["number"])
        if pad["net"] != expected or bool(pad["net_code"]) != bool(expected):
            raise ValueError("unapproved external or invented net assignment")


def build(args):
    import pcbnew
    import export_kicad_design as cad

    source_layout = args.predecessor / "engineering-layout-export.json"
    before = json.loads(source_layout.read_text())
    source = args.predecessor / before["metadata"]["source_board"]
    if before["metadata"]["design_revision"] != "MECH-FIT-04" or digest(source) != PREDECESSOR_HASH:
        raise ValueError("unexpected predecessor")
    for flag in ("is_canonical", "fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed"):
        if before["metadata"].get(flag) is not False:
            raise ValueError("predecessor release locks required")
    evidence = json.loads((args.proposal / "nxp-package-evidence.json").read_text())
    for relative, sha in evidence["artifacts_sha256"].items():
        path = (args.proposal / relative).resolve()
        if not path.is_relative_to(args.proposal.resolve()) or digest(path) != sha:
            raise ValueError("changed evidence artifact: " + relative)
    if evidence["U1"]["ball_count"] != 548 or \
            evidence["U6_U7"]["package"] != "SOT2283-1" or \
            evidence["U1"]["land_proposal"]["vendor_land_definition_verified"] is not False:
        raise ValueError("missing private proposal limits")
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    (output / "fp-lib-table").write_text(
        '(fp_lib_table\n  (lib (name "DeepReal_Evidence") (type "KiCad") '
        f'(uri {json.dumps(str(args.proposal / "DeepReal_Evidence.pretty"))}) '
        '(options "") (descr "Private unqualified NXP package proposals"))\n)\n')
    components = {c["ref"]: c for c in before["components"]}
    scratch = pcbnew.BOARD()
    nets = {}
    for ref in ("U6", "U7"):
        for function in ALIASES:
            name = f"PACKAGE_{ref}_{function}"
            net = pcbnew.NETINFO_ITEM(scratch, name, len(nets) + 1)
            scratch.Add(net)
            nets[name] = net
    for ref, name in PACKAGES.items():
        part = components[ref]
        if part["side"] != "TOP":
            raise ValueError("unexpected package face")
        footprint = pcbnew.FootprintLoad(str(args.proposal / "DeepReal_Evidence.pretty"), name)
        if not footprint:
            raise ValueError("cannot load evidence footprint")
        scratch.Add(footprint)
        footprint.SetReference(ref)
        footprint.SetValue(part["value"])
        footprint.SetOrientationDegrees(part["rotation_deg"])
        footprint.SetPosition(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in part["position_mm"]]))
        for pad in footprint.Pads():
            name = expected_net(ref, pad.GetNumber())
            if name:
                pad.SetNet(nets[name])
    temporary = output / "serialization-inspection.kicad_pcb"
    pcbnew.SaveBoard(str(temporary), scratch)
    replacements = deterministic_blocks(temporary.read_text(), components)
    target = output / "deepreal-main-pcba-mech-fit-05.kicad_pcb"
    original = source.read_text()
    merged = merge_footprints(original, replacements, set(PACKAGES))
    # Serialize only replacement footprints. Every other root block, including
    # outline, design rules, source text and inherited ignored checks, stays raw.
    unchanged = lambda text: [b for _, _, b in top_level_blocks(text)[0]
                              if not b.startswith("(footprint ") or reference(b) not in PACKAGES]
    if unchanged(original) != unchanged(merged):
        raise ValueError("unscoped serialized root change")
    target.write_text(merged)
    board = pcbnew.LoadBoard(str(target))
    tracks, vias = cad.copper(board)
    layout = {
        "metadata": {
            **copy.deepcopy(before["metadata"]), "design_revision": REVISION,
            "design_status": "PRIVATE_UNROUTED_NXP_PACKAGE_PROPOSAL",
            "source_board": target.name, "source_board_sha256": digest(target),
            "predecessor_board_sha256": PREDECESSOR_HASH,
            "package_evidence_sha256": digest(args.proposal / "nxp-package-evidence.json"),
            "package_land_and_stencil_release": False,
            "external_netlist_complete": False, "local_package_alias_nets_only": True,
        },
        "board": cad.board_outline(board), "components": cad.components(board),
        "pads": cad.pads(board), "holes": cad.holes(board),
        "tracks": tracks, "vias": vias, "zones": cad.zones(board),
        "validation_status": before["validation_status"],
    }
    verify_scope(before, layout)
    for ref in PACKAGES:
        pads = {p["number"]: p for p in layout["pads"] if p["ref"] == ref}
        expected = {r["number"]: r["position_mm"] for r in evidence["U1"]["balls"]} \
            if ref == "U1" else evidence["U6_U7"]["positions_mm"]
        origin = components[ref]["position_mm"]
        for number, local in expected.items():
            if any(abs(pads[number]["position_mm"][i] - origin[i] - local[i]) > 0.000002
                   for i in (0, 1)):
                raise ValueError("registered pad differs from vendor source: " + ref + "." + number)
    (output / "engineering-layout-export.json").write_text(json.dumps(layout, indent=2) + "\n")
    report = {
        "schema": "deepreal.pcb-nxp-candidate.v1", "revision": REVISION,
        "builder_sha256": digest(Path(__file__)),
        "source_board_sha256": digest(target), "predecessor_board_sha256": PREDECESSOR_HASH,
        "changed_footprint_refs": sorted(PACKAGES), "population": 238,
        "pad_primitives": 2626, "unchanged_pad_primitives": 2030,
        "fixed_origin_mm": [65, 34], "source_root_scope_verified": True,
        "local_package_alias_nets": sorted(nets),
        "alias_net_basis": "PF53 Rev 7 pages 8-9 PGND/LX functions; same-function pins only, no external or inter-package assignments",
        "evidence_sha256": digest(args.proposal / "nxp-package-evidence.json"),
        "limits": evidence["common_limits"],
        "U1_AF22": evidence["U1"]["function_conflicts"],
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
    }
    (output / "package-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    glb = output / "main-pcba-native.glb"
    command = [
        str(args.kicad_cli), "pcb", "export", "glb", "--output", str(glb),
        "--define-var", "KICAD10_3DMODEL_DIR=" + str(args.model_dir),
        "--include-tracks", "--include-pads", "--include-zones", "--include-silkscreen",
        "--include-soldermask", "--cut-vias-in-body", "--no-extra-pad-thickness",
        "--user-origin", "65x34mm", str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    (output / "native-export.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    names = {n.get("name") for n in read_glb(glb)["nodes"]}
    sources = []
    for declared in sorted({m for c in layout["components"] for m in c["models"]}):
        path = Path(declared.replace("${KICAD10_3DMODEL_DIR}", str(args.model_dir)))
        sources.append({"declared": declared, "resolved": str(path),
                        "sha256": digest(path) if path.is_file() else None})
    manifest = {
        "schema": "deepreal.private-candidate-native.v1", "revision": REVISION,
        "source_board_sha256": digest(target),
        "source_export_sha256": digest(output / "engineering-layout-export.json"),
        "source_status_sha256": layout["metadata"]["source_status_sha256"],
        "package_audit_sha256": digest(output / "package-audit.json"),
        "glb_sha256": digest(glb), "glb": glb.name, "origin_mm": [65, 34],
        "native_model_refs": sorted(c["ref"] for c in layout["components"] if c["ref"] in names),
        "missing_model_refs": sorted(c["ref"] for c in layout["components"] if c["models"] and c["ref"] not in names),
        "pad_or_hole_only_refs": sorted(c["ref"] for c in layout["components"] if not c["models"]),
        "model_sources": sources, "command": command,
        "warning": "U1/U6/U7 are maximum package envelopes; vendor lands/mask/stencil not released",
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
    }
    (output / "native-review-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if digest(source) != PREDECESSOR_HASH:
        raise ValueError("predecessor changed during build")
    print("MECH-FIT-05: 238 footprints, 2626 primitives; only U1/U6/U7 replaced")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("predecessor", "proposal", "output", "kicad-cli", "model-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    arguments = parser.parse_args()
    if any(not p.is_absolute() for p in vars(arguments).values()):
        parser.error("absolute paths required")
    build(arguments)
