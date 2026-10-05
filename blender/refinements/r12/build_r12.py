#!/usr/bin/env python3
"""Build a wider supported PCB wing and visually flat drum ends."""

import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for folder in (REPO / "blender", HERE.parent / "r07"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import macbook  # noqa: E402
from r07_geometry import difference  # noqa: E402

MM = 0.001
SOURCE = HERE.parent / "r11" / "deepreal-exterior-refinement-r11.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r12.blend"
BOARD_NAME = "Main_PCBA_Near_Full_Height_Right_Wing_PROPOSAL"
MOUNT_XZ = (("H1", -42, -22.5), ("H2", -42, -0.5),
            ("H3", 42, -22.5), ("H4", 42, -0.5),
            ("H5_Proposed", 52, -5))


def new_board():
    old = bpy.data.objects["Main_PCBA_Continuous_Right_USB_Tab_PROPOSAL"]
    collection = old.users_collection[0]
    material = old.data.materials[0]
    bpy.data.objects.remove(old, do_unlink=True)
    # The wing retains 26.5 of the original board's 28 mm height. The small
    # lower step clears the existing housing; the exterior is not enlarged.
    outline = [(-45, -25.5), (45, -25.5), (45, -24),
               (57.5, -24), (57.5, 2.5), (-45, 2.5)]
    board = macbook.prism(
        BOARD_NAME, [(x * MM, z * MM) for x, z in outline],
        Vector((0, 11.35 * MM, 0)), macbook.X, macbook.Z,
        1.5 * MM, material)
    collection.objects.link(board)
    board["R12_Status"] = (
        "near-full-height one-piece PCB outline proposal; structural and "
        "electrical design unverified")
    board["R12_Outline_mm"] = str(outline)
    for name, x, z in MOUNT_XZ:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=48, radius=1.35 * MM, depth=3 * MM,
            location=(x * MM, 11.35 * MM, z * MM),
            rotation=(1.5707963267948966, 0, 0))
        difference(board, bpy.context.object, "R12_" + name + "_Hole")
    return board


def extend_surface(name, y_mm):
    # KiCad import retained separate top/bottom finish surfaces over the
    # original rectangle. Extend those same meshes and materials onto the
    # wing so the board no longer changes color at the former right edge.
    obj = bpy.data.objects[name]
    inverse = obj.matrix_world.inverted()
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    corners = [(45, -24), (57.5, -24), (57.5, 2.5), (45, 2.5)]
    verts = [mesh.verts.new(inverse @ Vector((x * MM, y_mm * MM, z * MM)))
             for x, z in corners]
    mesh.faces.new(verts)
    mesh.to_mesh(obj.data)
    mesh.free()
    obj.data.update()
    obj["R12_Status"] = "native board finish continued onto proposed wing"


def housing_support():
    housing = bpy.data.objects["Main_Housing"]
    housing.data = housing.data.copy()
    # A candidate load path from H5 to the existing inner housing wall.
    # It is not a dimensioned boss/insert/fastener design.
    boss = macbook.cylinder(
        "_R12_Housing_Boss_Cutter", Vector((52 * MM, 7.75 * MM, -5 * MM)),
        macbook.Y, 2.5 * MM, 5.7 * MM,
        bpy.data.materials["Device_Housing_Anodized.002"], seg=64)
    bpy.context.scene.collection.objects.link(boss)
    bpy.context.view_layer.objects.active = housing
    modifier = housing.modifiers.new("R12_H5_Support_Boss", "BOOLEAN")
    modifier.operation = "UNION"
    modifier.solver = "EXACT"
    modifier.object = boss
    housing.modifiers.move(len(housing.modifiers) - 1, 0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(boss, do_unlink=True)
    pilot = macbook.cylinder(
        "_R12_H5_Blind_Pilot", Vector((52 * MM, 8.7 * MM, -5 * MM)),
        macbook.Y, 1.1 * MM, 4.2 * MM, None, seg=48)
    bpy.context.scene.collection.objects.link(pilot)
    difference(housing, pilot, "R12_H5_Blind_Pilot")
    bpy.data.objects["Main_Housing_Inspection_Wireframe"].data = housing.data
    housing["R12_H5_Support"] = (
        "candidate integral housing boss under new H5 board hole; "
        "fastener, wall thickness, tooling and strength unverified")


def flat_ends():
    material = bpy.data.materials["Device_Sensor_Drum"]
    for name in ("Face_Sensor_Head", "Interaction_Sensor_Head"):
        drum = bpy.data.objects[name]
        collection = drum.users_collection[0]
        bounds = [((drum.matrix_world @ Vector(c)).x) for c in drum.bound_box]
        for side, edge, direction in (("Left", min(bounds), -1),
                                      ("Right", max(bounds), 1)):
            old = bpy.data.objects[name + "_Closed_End_" + side]
            bpy.data.objects.remove(old, do_unlink=True)
            # The front of this thin full-diameter face sits in front of the
            # annular shell rim. It masks the ring without coplanar flicker.
            # This is a presentation skin; a manufacturable closure remains
            # a separate design question.
            face = macbook.cylinder(
                name + "_Flat_End_" + side,
                Vector((edge + direction * 0.12 * MM,
                        -1.5 * MM, 20 * MM)),
                macbook.X, 12.0 * MM, 0.24 * MM, material, seg=128)
            collection.objects.link(face)
            face["R12_Status"] = (
                "flat presentation skin over tube end; assembly unresolved")
        drum["R12_Ends"] = (
            "flat visual ends; bearings and sealing unresolved")


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    new_board()
    extend_surface("PCBA_Native_Surface_04", 12.15)
    extend_surface("PCBA_Native_Surface_03", 10.55)
    housing_support()
    flat_ends()
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R12"
    scene["DeepReal_Status"] = (
        "near-full-height USB PCB wing and flat drum-end presentation; "
        "engineering readiness BLOCKED")
    scene["R12_Limits"] = (
        "USB footprint, routing, connector retention, boss strength and "
        "drum mechanism unverified")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R12 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
