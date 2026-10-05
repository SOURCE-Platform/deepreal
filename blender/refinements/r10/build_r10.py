#!/usr/bin/env python3
"""Build a continuous main-board outline and explicit USB seating study."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for folder in (REPO / "blender", HERE.parent / "r04",
               HERE.parent / "r07", HERE.parent / "r09"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import macbook  # noqa: E402
from r04_geometry import frame_viewports  # noqa: E402
from r07_geometry import difference  # noqa: E402

MM = 0.001
SOURCE = HERE.parent / "r09" / "deepreal-exterior-refinement-r09.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r10.blend"
BOARD = "Main_PCBA_Continuous_Right_USB_Tab_PROPOSAL"


def continuous_board():
    old = bpy.data.objects["Main_PCBA"]
    old.name = "Main_PCBA_Imported_Artwork_HIDDEN_REFERENCE"
    old.hide_set(True)
    old.hide_render = True
    old["R10_Status"] = "original native PCB artwork; outline unchanged in KiCad"
    bpy.data.objects.remove(
        bpy.data.objects["Main_PCBA_Right_USB_Tab_GEOMETRY_PROPOSAL"],
        do_unlink=True)

    # A single extrusion includes both the native rectangle and the right tab.
    # It is a packaging outline, not an electrically designed KiCad board.
    polygon_mm = [(-45, -25.5), (45, -25.5), (45, -22.5),
                  (57.5, -22.5), (57.5, -10), (45, -10),
                  (45, 2.5), (-45, 2.5)]
    board = macbook.prism(
        BOARD, [(x * MM, z * MM) for x, z in polygon_mm],
        Vector((0, 11.35 * MM, 0)), macbook.X, macbook.Z,
        1.5 * MM, bpy.data.materials["R05_USB_Daughterboard_Green"])
    target = bpy.data.collections["02 — STATIONARY ELECTRONICS — PROVISIONAL"]
    target.objects.link(board)
    board["R10_Outline_mm"] = str(polygon_mm)
    board["R10_Status"] = (
        "one continuous conceptual main-PCB substrate; KiCad board still unchanged")

    # Preserve the native board's four 2.7 mm mounting-hole locations.
    for name, x, z in (("H1", -42, -22.5), ("H2", -42, -0.5),
                       ("H3", 42, -22.5), ("H4", 42, -0.5)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=48, radius=1.35 * MM, depth=3 * MM,
            location=(x * MM, 11.35 * MM, z * MM),
            rotation=(1.5707963267948966, 0, 0))
        difference(board, bpy.context.object, "R10_" + name + "_Hole")
    return board


def socket_seating():
    socket = bpy.data.objects["USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED"]
    socket["R10_Status"] = (
        "socket outline and four seating tabs are visual-only; no selected "
        "connector, verified land pattern, contacts or solder joints")
    socket["R10_Seating"] = "shell overlaps board top by 0.1 mm nominal"
    material = socket.data.materials[0] if socket.data.materials else None
    collection = bpy.data.collections["05 — RIGHT BOARD-MOUNT USB — GEOMETRY ONLY"]
    for x in (47.2, 55.8):
        for z in (-19.6, -15.6):
            foot = macbook.slab(
                "USB_Socket_Illustrative_Seat_%s_%s" % (x, z),
                Vector((x * MM, 12.25 * MM, z * MM)),
                macbook.X, macbook.Z, (1.2 * MM, 0.8 * MM),
                0.1 * MM, 0.6 * MM, material)
            collection.objects.link(foot)
            # Join each marker into the socket body so selecting the socket
            # also selects its visible seating geometry. This is not a land
            # pattern or mechanically qualified retention design.
            bpy.context.view_layer.objects.active = socket
            modifier = socket.modifiers.new("R10_Illustrative_Socket_Seat", "BOOLEAN")
            modifier.operation = "UNION"
            modifier.solver = "EXACT"
            modifier.object = foot
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(foot, do_unlink=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    continuous_board()
    socket_seating()
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R10"
    scene["DeepReal_Status"] = (
        "continuous main-PCB outline and socket seating study; "
        "engineering readiness BLOCKED")
    scene["R10_Limits"] = (
        "KiCad unchanged; exact connector, footprint, copper, thermal and "
        "mechanical performance unverified")
    frame_viewports(target=(0.0, 0.004, -0.005), distance=0.14)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R10 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
