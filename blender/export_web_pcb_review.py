#!/usr/bin/env python3
"""Export the defective retained native PCB for a separate layout review.

No geometry is fitted to the assembly outline and no copper is invented.
The asset must stay outside the site's public directory.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from web_export_common import export_glb  # noqa: E402

OUTPUT = Path(os.environ.get(
    "DEEPREAL_WEB_PCB_REVIEW_OUT",
    str(HERE / "review-output/web/main-pcba-review.glb"),
)).resolve()


def main():
    if not any(OUTPUT.is_relative_to(root) for root in (
        HERE / "review-output", ROOT / "tmp",
    )):
        raise ValueError("Internal PCB review output must remain in DeepReal review-output or tmp")
    if OUTPUT.exists() or OUTPUT.with_suffix(".json").exists():
        raise ValueError("Choose a new output path; an existing review is never overwritten")
    electronics = ROOT / "hardware/electronics/deepreal-main-pcba"
    data = json.loads((electronics / "engineering-layout-export.json").read_text())
    source_manifest = json.loads((electronics / "generated-review/native-review-manifest.json").read_text())
    status_path = electronics / "design-status.json"
    status = json.loads(status_path.read_text())
    if any(record.get(gate) is not False
           for record in (status, source_manifest)
           for gate in ("public_visual_allowed", "fabrication_allowed")):
        raise ValueError("This exporter is specifically for the locked internal review")
    for path, field in (
        (electronics / "deepreal-main-pcba.kicad_pcb", "source_board_sha256"),
        (electronics / "engineering-layout-export.json", "source_export_sha256"),
        (electronics / "generated-review" / source_manifest["glb"], "glb_sha256"),
    ):
        if hashlib.sha256(path.read_bytes()).hexdigest() != source_manifest[field]:
            raise ValueError("PCB geometry snapshot source changed: " + str(path))
    # The retained native export has an old status fingerprint. Do not bypass
    # checked_inputs() or regenerate authoritative electronics to hide that.
    # Transport the already-retained Blender review as a hash-identified snapshot.
    source_blend = HERE / "deepreal.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    bpy.context.window.scene = bpy.data.scenes["SOURCE - Canonical Assembly"]
    bpy.data.objects["Lid_Pivot"].rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    objects = [o for o in bpy.data.collections["Electronics Assembly"].objects
               if o.get("PCBA_Component") or o.get("PCBA_NativeSurface")]
    review_scene = bpy.data.scenes.new("Standalone PCB development review")
    collection = bpy.data.collections.new("Native PCB development review")
    review_scene.collection.children.link(collection)
    components = [o for o in objects if o.get("PCBA_Component")]
    surfaces = [o for o in objects if o.get("PCBA_NativeSurface")]
    expected = {c["ref"] for c in data["components"]} - set(source_manifest["pad_or_hole_only_refs"])
    assert {o["PCBA_Ref"] for o in components} == expected
    assert len(components) == len(expected)
    native_refs = set(source_manifest["native_model_refs"])
    placeholder_refs = set(source_manifest["missing_model_refs"])
    assert {o["PCBA_Ref"] for o in components
            if o["PCBA_ModelStatus"] == "NATIVE_MODEL_UNVERIFIED_FOOTPRINT"} == native_refs
    assert {o["PCBA_Ref"] for o in components
            if o["PCBA_ModelStatus"] == "REPRESENTATIVE_ENVELOPE_MISSING_KICAD_MODEL"} == placeholder_refs
    assert all(o.get("PCBA_SourceBoardHash") == source_manifest["source_board_sha256"]
               for o in objects)
    assert not any(data[key] for key in ("tracks", "vias", "zones"))
    staged = []
    for original in objects:
        clone = original.copy()
        clone.data = original.data.copy()
        clone.name = original.name + "_WEB"
        clone.parent = None
        clone.matrix_world = original.matrix_world.copy()
        collection.objects.link(clone)
        staged.append(clone)
    # glTF can export selected objects from other Blender scenes too. Isolate the
    # transport scene in this process, without saving or changing the source file.
    bpy.context.window.scene = review_scene
    for scene in list(bpy.data.scenes):
        if scene != review_scene:
            bpy.data.scenes.remove(scene)
    export_glb(OUTPUT, staged)
    report = {
        "schema": "deepreal.web-pcb-review.v3",
        "status": "UNROUTED_INTERNAL_REVIEW",
        "display_scope": "DEVELOPMENT_STANDALONE_LAYOUT_REVIEW",
        "standalone_only": True,
        "layout_clearance_validated": False,
        "package_fit_validated": False,
        "public_visual_allowed": False,
        "fabrication_allowed": False,
        "asset_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "asset_bytes": OUTPUT.stat().st_size,
        "source_board_sha256": source_manifest["source_board_sha256"],
        "source_export_sha256": source_manifest["source_export_sha256"],
        "source_native_glb_sha256": source_manifest["glb_sha256"],
        "source_blend": "blender/deepreal.blend",
        "source_blend_sha256": hashlib.sha256(source_blend.read_bytes()).hexdigest(),
        "current_status_sha256": hashlib.sha256(status_path.read_bytes()).hexdigest(),
        "native_export_recorded_status_sha256": data["metadata"]["source_status_sha256"],
        "source_classification": "RETAINED_BLENDER_REVIEW_SNAPSHOT_NOT_A_FRESH_NATIVE_IMPORT",
        "component_count": len(components),
        "native_model_count": len(source_manifest["native_model_refs"]),
        "placeholder_count": len(source_manifest["missing_model_refs"]),
        "surface_count": len(surfaces),
        "pad_count": len(data["pads"]),
        "track_count": len(data["tracks"]),
        "via_count": len(data["vias"]),
        "zone_count": len(data["zones"]),
        "objects": [o.name for o in staged],
        "components": [{
            "name": o.name + "_WEB", "reference": o["PCBA_Ref"],
            "model_status": o["PCBA_ModelStatus"],
        } for o in components],
        "limits": [
            "Existing unverified footprints, placements and 18 model envelopes remain visible.",
            "The native 90 x 28 mm board is not fitted to the assembly's proposed USB wing.",
            "Known chip/connector clashes remain in this retained layout. It must not replace the R36 mechanical assembly board.",
            "No traces, vias, planes, solder fillets or package pins are invented.",
            "Development-only serving does not change the engineering or publication gates.",
            "The native export's status fingerprint is stale; its original guard remains unchanged. This is the retained Blender review snapshot.",
        ],
    }
    with OUTPUT.with_suffix(".json").open("x") as out:
        json.dump(report, out, indent=2)
        out.write("\n")
    print("PCB REVIEW", len(components), "components;", len(surfaces), "native surfaces")


if __name__ == "__main__":
    main()
