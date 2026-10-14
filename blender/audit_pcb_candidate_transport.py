"""Check every private review mesh vertex through the exported GLB."""

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils.kdtree import KDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pcb_candidate_review_data import ROOT, digest


def mesh_key(obj):
    return "ref:" + obj["PCBA_Ref"] if obj.get("PCBA_Ref") else "surface:" + obj.name


def capture(objects):
    result = {}
    for obj in objects:
        if obj.type != "MESH":
            continue
        key = mesh_key(obj)
        if key in result:
            raise ValueError("duplicated mesh identity: " + key)
        if bool(obj.get("PCBA_PublicAllowed", True)):
            raise ValueError("unlocked mesh")
        result[key] = [obj.matrix_world @ vertex.co * 1000 for vertex in obj.data.vertices]
    return result


def distance_to(points, targets):
    if not points or not targets:
        raise ValueError("empty review mesh")
    tree = KDTree(len(targets))
    for index, point in enumerate(targets):
        tree.insert(point, index)
    tree.balance()
    return max(tree.find(point)[2] for point in points)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    directory = args.model_dir.resolve()
    if not directory.is_relative_to(ROOT / "tmp"):
        raise ValueError("private review only")
    output = directory / "transport-audit.json"
    if output.exists():
        raise ValueError("do not overwrite an audit")
    audit = json.loads((directory / "model-audit.json").read_text())
    for name, sha in audit["output_sha256"].items():
        if digest(directory / name) != sha:
            raise ValueError("changed model artifact: " + name)
    bpy.ops.wm.open_mainfile(filepath=str(directory / "deepreal-mech-fit-03-review.blend"))
    before = capture(bpy.data.collections["Complete Candidate PCBA"].objects)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(directory / "candidate-board.glb"))
    after = capture(bpy.context.scene.objects)
    if set(before) != set(after):
        raise ValueError("lost or added mesh identities")
    maximum = 0
    for key, points in before.items():
        maximum = max(maximum, distance_to(points, after[key]), distance_to(after[key], points))
    if maximum > .00005:
        raise ValueError("mesh transport difference exceeds 50 nanometres")
    record = {
        "schema": "deepreal.private-pcb-transport-audit.v1", "status": "PASS",
        "source_blend_sha256": audit["output_sha256"]["deepreal-mech-fit-03-review.blend"],
        "source_glb_sha256": audit["output_sha256"]["candidate-board.glb"],
        "mesh_identities_preserved": len(before),
        "body_identities_preserved": sum(k.startswith("ref:") for k in before),
        "surface_identities_preserved": sum(k.startswith("surface:") for k in before),
        "source_vertices_checked": sum(map(len, before.values())),
        "export_vertices_checked": sum(map(len, after.values())),
        "max_bidirectional_vertex_difference_mm": maximum,
        "geometry_approval": "TRANSPORT_ONLY_NOT_ELECTRICAL_OR_INTERFACE_FIT",
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
    }
    output.write_text(json.dumps(record, indent=2) + "\n")
    print("TRANSPORT PASS:", len(before), "meshes; max vertex difference mm:", maximum)


if __name__ == "__main__":
    main()
