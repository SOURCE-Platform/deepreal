#!/usr/bin/env python3
"""Add a face outer load path and candidate moving flex to the R34 study."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(HERE.parent / "r21"))

import macbook  # noqa: E402
from assembly_primitives import cylinder, material, tube  # noqa: E402
from r21_mechanism import AXIS  # noqa: E402
from flex_geometry import create_ribbon  # noqa: E402

SOURCE = HERE.parent / "r34/deepreal-face-interface-study-r34.blend"
OUTPUT = HERE / "deepreal-face-motion-study-r35.blend"
HEAD_INTERFACE = ROOT / "hardware/electronics/deepreal-main-pcba/head-interface-evidence.json"
FPC_WIDTH_MM = json.loads(HEAD_INTERFACE.read_text())["connector"]["fpc_end_width_mm"]


def rotating(obj, pivot, note):
    obj.parent = pivot
    obj.matrix_parent_inverse = pivot.matrix_world.inverted()
    obj["R35_Role"] = "rotates with face drum"
    obj["R35_Status"] = note
    return obj


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    assert abs(pivot.rotation_euler.x) < 1e-6
    collection = bpy.data.collections.new("25 — R35 FACE COUPLING AND FLEX STUDY")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_05"
    for name in ("R34_Face_Outer_Rotating_Shaft_ENV",
                 "R34_Face_Outer_Rotating_Hub_ENV",
                 "R34_Face_Inner_Flex_Width_ENV"):
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    steel = material("R35_Outer_Coupling_Steel_ENV", (.36, .45, .51), .7, .3)
    web_mat = material("R35_Rotating_Web_Graphite_ENV", (.08, .12, .15), .4, .35)
    flex_mat = material("R35_Moving_Flex_Collision_Candidate", (.9, .18, .06), .1, .4)

    # The web sits inboard of the stationary bearing. Its solid center
    # overlaps the shaft, annular hub and shell-side sleeve as one load path.
    # Fits, bonds and fasteners are deliberately not specified here.
    shaft = rotating(cylinder("R35_Face_Outer_Shaft_ENV",
                              (-53.95, *AXIS), macbook.X, 2.0, 3.5,
                              steel, collection, 64), pivot,
                     "rotating solid shaft; bearing/retention unselected")
    hub = rotating(tube("R35_Face_Outer_Hub_ENV",
                        (-53.95, *AXIS), macbook.X, 3.62, 5.4, 3.5,
                        steel, collection, 64), pivot,
                   "rotating bearing outer/hub envelope")
    web = rotating(cylinder("R35_Face_Outer_Coupling_Web_ENV",
                            (-53.35, *AXIS), macbook.X, 11.75, .5,
                            web_mat, collection, 96), pivot,
                   "concept load path from shaft and hub toward drum wall")
    sleeve = rotating(tube("R35_Face_Outer_Drum_Wall_Sleeve_ENV",
                           (-52.0, *AXIS), macbook.X, 11.55, 11.92, 3.0,
                           web_mat, collection, 96), pivot,
                      "concept overlap with drum sidewall; attachment open")

    # A full-width strip twists from the moving head side to a fixed datum
    # just beyond the inner bearing. This is deliberately a candidate to
    # sweep, not a claim of flex fatigue or collision clearance.
    flex = create_ribbon("R35_Face_Full_Width_Torsion_Candidate_ENV",
                         collection, flex_mat, -22.0, -1.2, FPC_WIDTH_MM)
    flex["R35_Anchor_Status"] = "moving and fixed anchor locations provisional"
    scene.name = "DeepReal Face Drum Motion Study R35"
    scene["R35_Engineering_Status"] = (
        "outer load path concept plus full-width torsion candidate; "
        "pose sweep and fatigue decision in r35-motion-check.json")
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {
        "source": str(SOURCE), "model": str(OUTPUT),
        "outer_load_path_objects": [obj.name for obj in
                                    (shaft, hub, web, sleeve)],
        "candidate_flex_object": flex.name,
        "flex_width_mm": FPC_WIDTH_MM,
        "moving_anchor_x_mm": -22.0,
        "fixed_anchor_x_mm": -1.2,
        "status": "FEASIBILITY_STUDY_ONLY",
        "open": ["actual rotating joints", "bearing selection",
                 "flex termination", "dynamic collision and fatigue proof",
                 "encoder magnet retention", "second drum"],
    }
    (HERE / "r35-motion-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R35 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
