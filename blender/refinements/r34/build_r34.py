#!/usr/bin/env python3
"""Face-drum study: centered outer encoder and full-width inner flex exit."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for path in (ROOT / "blender", HERE.parent / "r21"):
    sys.path.insert(0, str(path))

import macbook  # noqa: E402
from assembly_primitives import box, cylinder, material, tube  # noqa: E402
from r21_mechanism import AXIS  # noqa: E402

SOURCE = HERE.parent / "r30/deepreal-monitor-ledge-enclosure-r30.blend"
OUTPUT = HERE / "deepreal-face-interface-study-r34.blend"
HEAD_INTERFACE = ROOT / "hardware/electronics/deepreal-main-pcba/head-interface-evidence.json"
FPC_WIDTH_MM = json.loads(HEAD_INTERFACE.read_text())["connector"]["fpc_end_width_mm"]
MM = .001


def remove(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def rotate_with_drum(obj, pivot, status):
    obj.parent = pivot
    obj.matrix_parent_inverse = pivot.matrix_world.inverted()
    obj["R34_Role"] = "rotates with face drum"
    obj["R34_Status"] = status
    return obj


def stationary(obj, status):
    obj["R34_Role"] = "stationary enclosure-side envelope"
    obj["R34_Status"] = status
    return obj


def subtract(target, cutter):
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    modifier = target.modifiers.new("R34 interface clearance study", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    target.select_set(False)
    bpy.data.objects.remove(cutter, do_unlink=True)


def add_review_camera(scene):
    data = bpy.data.cameras.new("R34_Face_Interface_Camera")
    data.type = "ORTHO"
    data.ortho_scale = .105
    camera = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(camera)
    camera.location = (-.105, -.13, .073)
    target = Vector((-.034, -.001, .017))
    camera.rotation_euler = (target - camera.location).to_track_quat(
        "-Z", "Y").to_euler()
    scene.camera = camera


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    assert abs(pivot.rotation_euler.x) < 1e-6
    collection = bpy.data.collections.new("24 — R34 FACE DRUM INTERFACE STUDY")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_06"

    remove("Face_" + name for name in (
        "End_Encoder_Magnet_R21", "End_Encoder_PCB_ENV_R21",
        "End_Encoder_IC_ENV_R21", "Outer_Hollow_Fixed_Spindle_ENV_R21",
        "Outer_Bearing_ENV_R21", "Outer_Rotating_Hub_R21",
        "Moving_Head_Flex_PROXY_R21", "Fixed_Harness_PROXY_R21"))

    steel = material("R34_Bearing_Envelope", (.38, .47, .52), .65, .3)
    magnet_mat = material("R34_Diametric_Magnet_Concept", (.84, .36, .22), .3, .35)
    board_mat = material("R34_Angle_Board_Concept", (.02, .22, .18), .05, .5)
    ic_mat = material("R34_Angle_IC_Concept", (.12, .14, .17), .05, .4)
    flex_mat = material("R34_Optical_Flex_Full_Width", (.83, .53, .12), .1, .35)

    # The inherited inner cap is solid beneath its ring. A slot permits only
    # this straight ribbon segment; the deforming service loop remains open.
    drum = bpy.data.objects["Face_Sensor_Head"]
    slot = box("R34_Temporary_Inner_Flex_Slot", (-2.75, *AXIS),
               (1.9, .8, FPC_WIDTH_MM + .6), 0, flex_mat, collection)
    subtract(drum, slot)

    # Pocket through the cheek's inner face, leaving a thin outer concept skin.
    # This is a packaging cavity, not an approved wall/fastening thickness.
    housing = bpy.data.objects["R30_One_Piece_Enclosure"]
    pocket = cylinder("R34_Temporary_Encoder_Pocket",
                      (-58.6, *AXIS), macbook.X, 3.8, 2.4,
                      steel, collection, 64)
    subtract(housing, pocket)

    shaft = rotate_with_drum(cylinder("R34_Face_Outer_Rotating_Shaft_ENV",
                                       (-54.55, *AXIS), macbook.X,
                                       2.0, 2.3, steel, collection, 64),
                             pivot, "solid axle; coupling and loads unverified")
    bearing = stationary(tube("R34_Face_Outer_Bearing_ENV",
                              (-54.8, *AXIS), macbook.X,
                              2.08, 3.5, 1.8, steel, collection, 64),
                         "bearing dimensions are envelope only")
    hub = rotate_with_drum(tube("R34_Face_Outer_Rotating_Hub_ENV",
                                (-54.8, *AXIS), macbook.X,
                                3.62, 5.4, 1.8, steel, collection, 64),
                           pivot, "shaft-to-hub spokes are not modeled")
    magnet = rotate_with_drum(cylinder("R34_Face_Axial_Magnet_ENV",
                                       (-56.95, *AXIS), macbook.X,
                                       3.0, 2.5, magnet_mat, collection, 64),
                              pivot, "diametric magnet reference envelope; retention open")
    sensor = stationary(box("R34_Face_Axial_Sensor_IC_ENV",
                            (-59.05, *AXIS), (.6, 2.07, 2.63),
                            .04, ic_mat, collection),
                        "AS5600L package envelope; Hall center and pinout unverified")
    sensor_board = stationary(box("R34_Face_Axial_Sensor_PCB_ENV",
                                  (-59.55, *AXIS), (.4, 3.4, 3.4),
                                  .08, board_mat, collection),
                              "stationary cheek board; connector and mounting open")

    # A strip at the documented connector-end width clears the
    # inner bearing aperture but stops before the fixed center divider.
    flex = rotate_with_drum(box("R34_Face_Inner_Flex_Width_ENV",
                                (-5.35, *AXIS), (6.3, .2, FPC_WIDTH_MM),
                                .03, flex_mat, collection),
                            pivot, "straight pass-through only; no service loop, "
                                   "head termination or bend-life proof")
    flex["R34_Width_mm"] = FPC_WIDTH_MM
    flex["R34_Thickness_mm"] = .2

    scene.name = "DeepReal Face Drum Interface Study R34"
    scene["R34_Engineering_Status"] = (
        "centered encoder and full-width inner passage; service loop, "
        "shaft/hub fastening, pocket wall and assembly still open")
    scene["R34_Source"] = str(SOURCE)
    add_review_camera(scene)
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {
        "source": str(SOURCE), "model": str(OUTPUT),
        "face_drum_axis_yz_mm": list(AXIS),
        "magnet_diameter_thickness_mm": [6.0, 2.5],
        "nominal_magnet_to_sensor_face_gap_mm": .55,
        "inner_flex_envelope_width_thickness_mm": [FPC_WIDTH_MM, .2],
        "flex_width_source": str(HEAD_INTERFACE),
        "new_objects": [obj.name for obj in (shaft, bearing, hub, magnet,
                                              sensor, sensor_board, flex)],
        "status": "INTERFACE_STUDY_ONLY",
        "open": ["deforming flex service loop", "real bearing and axle",
                 "shaft-to-hub spokes", "magnet retention", "cheek wall/fasteners",
                 "angle IC pinout and field", "optical head termination"],
    }
    (HERE / "r34-interface-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R34 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
