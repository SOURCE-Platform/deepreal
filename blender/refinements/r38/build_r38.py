#!/usr/bin/env python3
"""Revise the web exterior's mount face and USB cable, without releasing a mount design."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "blender"))
sys.path.insert(0, str(HERE.parent / "r21"))

import macbook  # noqa: E402
from r21_chassis import material  # noqa: E402

MM = .001
SOURCE = HERE.parent / "r36/deepreal-inner-bearing-window-r36.blend"
OUTPUT = HERE / "deepreal-exterior-mount-r38.blend"


def rounded_transition(name, center_x, center_y, plug_end_z, rings, material_name,
                       collection, status):
    sides = 48
    vertices = [
        (center_x + rx * MM * math.cos(2 * math.pi * i / sides),
         center_y + ry * MM * math.sin(2 * math.pi * i / sides),
         plug_end_z + dz * MM)
        for dz, rx, ry in rings for i in range(sides)
    ]
    faces = [tuple(range(sides))]
    for j in range(len(rings) - 1):
        for i in range(sides):
            nxt = (i + 1) % sides
            faces.append((j * sides + i, (j + 1) * sides + i,
                          (j + 1) * sides + nxt, j * sides + nxt))
    faces.append(tuple((len(rings) - 1) * sides + i
                       for i in range(sides - 1, -1, -1)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for face in mesh.polygons[1:-1]:
        face.use_smooth = True
    mesh.materials.append(bpy.data.materials[material_name])
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj["R38_Status"] = status
    return obj


def add_usb_plug_finish(collection):
    overmold = bpy.data.objects["USB_C_Plug_Overmold"]
    corners = [overmold.matrix_world @ Vector(corner)
               for corner in overmold.bound_box]
    center_x = (min(p.x for p in corners) + max(p.x for p in corners)) / 2
    center_y = (min(p.y for p in corners) + max(p.y for p in corners)) / 2
    plug_end_z = min(p.z for p in corners)

    # A long molded handle, with a smooth V-shaped shoulder, encloses the
    # cable before it reaches the narrower, visibly separate sleeve.
    material("R38_USB_Sleeve_Rubber", (.034, .038, .041, 1), .0, .78)
    rounded_transition(
        "R38_USB_Molded_Handle_Taper", center_x, center_y, plug_end_z,
        (
            (.2, 4.3, 2.35),
            (0, 4.3, 2.35),
            (-1.5, 4.1, 2.3),
            (-3.8, 3.5, 2.15),
            (-6.5, 2.55, 1.93),
            (-8.3, 1.95, 1.8),
            (-8.6, 1.95, 1.8),
        ),
        "Cable_Overmold", collection,
        "hard molded handle silhouette; production mold and cable retention unverified")
    rounded_transition(
        "R38_USB_Cable_Sleeve", center_x, center_y, plug_end_z,
        (
            (-8.45, 1.84, 1.72),
            (-8.65, 1.84, 1.72),
            (-12.4, 1.78, 1.68),
            (-12.7, 1.7, 1.7),
            (-12.95, 1.7, 1.7),
        ),
        "R38_USB_Sleeve_Rubber", collection,
        "separate visual sleeve over cable; elastomer and strain relief unverified")

    # A restrained wordmark in the narrow front face, as a finish concept.
    mark = bpy.data.curves.new("R38_USB_DeepReal_Wordmark", "FONT")
    mark.body = "DEEPREAL"
    mark.size = 1.05 * MM
    mark.space_character = 1.18
    mark.align_x = "CENTER"
    mark.align_y = "CENTER"
    mark.extrude = .012 * MM
    mark.materials.append(material(
        "R38_USB_Subtle_Logo_Ink", (.13, .15, .16, 1), .0, .72))
    obj = bpy.data.objects.new("R38_USB_DeepReal_Wordmark", mark)
    collection.objects.link(obj)
    obj.location = (center_x, min(p.y for p in corners) - .09 * MM,
                    plug_end_z + 5 * MM)
    obj.rotation_euler = Matrix((
        (0, 1, 0),
        (0, 0, -1),
        (-1, 0, 0),
    )).to_euler()
    obj["R38_Status"] = "DeepReal wordmark finish concept; print/etch process unselected"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    shell = bpy.data.objects["R30_One_Piece_Enclosure"]
    collection = bpy.data.collections.new("38 — WEB EXTERIOR MOUNT STUDY")
    bpy.context.scene.collection.children.link(collection)

    # Bring the entire inner leg forward to the original magnet plane. This
    # absorbs the old narrow pad into a single continuous enclosure face.
    leg = macbook.slab(
        "R38_Temporary_Continuous_Inner_Leg",
        Vector((0, 4.6 * MM, -14.5 * MM)),
        macbook.X, macbook.Z, (120 * MM, 29 * MM),
        0, 2.2 * MM, shell.data.materials[0])
    collection.objects.link(leg)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = shell
    shell.select_set(True)
    union = shell.modifiers.new("R38_Extend_Inner_Leg", "BOOLEAN")
    union.operation = "UNION"
    union.solver = "EXACT"
    union.object = leg
    shell.modifiers.move(len(shell.modifiers) - 1, 0)
    bpy.ops.object.modifier_apply(modifier=union.name)
    shell.select_set(False)
    bpy.data.objects.remove(leg, do_unlink=True)

    # Only the thin magnetic face projects from the continuous enclosure leg.
    # Attachment, retention and pull force remain unproven.
    magnet = macbook.slab(
        "R38_Device_Magnet_Face_CONCEPT",
        Vector((0, 3.05 * MM, -14 * MM)),
        macbook.X, macbook.Z, (112 * MM, 26 * MM),
        1.6 * MM, .9 * MM,
        material("R38_Dark_Satin_Magnet_Face", (.018, .024, .028, 1), .25, .58))
    collection.objects.link(magnet)
    magnet["R38_Status"] = (
        "visual magnetic face; material, segmentation and retention unverified")
    magnet["R38_Mating_Plate_mm"] = "112 x 26, centered at Z=-14"

    # Match the hidden mount-stack references to the R32 laptop target.
    bpy.data.objects.remove(bpy.data.objects["Mount_Magnet_Reference"],
                            do_unlink=True)
    for name, x_size, z_size in (
        ("Mount_Steel_Plate_Reference", 112, 26),
        ("Mount_Foam_Tape_Reference", 109, 23),
    ):
        obj = bpy.data.objects[name]
        obj.scale.x *= x_size / (obj.dimensions.x / MM)
        obj.scale.z *= z_size / (obj.dimensions.z / MM)
        obj.location.z = -14 * MM - (obj.bound_box[0][2] + obj.bound_box[6][2]) * obj.scale.z / 2
        obj["R38_Size_mm"] = [x_size, z_size]

    cable = bpy.data.objects["USB_C_Cable"]
    cable.data.bevel_depth = 1.6 * MM
    cable["R38_Status"] = "3.2 mm jacket appearance trial; electrical cable not selected"
    add_usb_plug_finish(collection)
    shell["R38_Mount_Status"] = (
        "112 x 26 mm matching magnetic face over continuous inner leg; "
        "magnet selection, holding force and assembly remain open")
    shell["R30_Design_Intent"] = (
        "R38 supersedes R30's narrow magnet pad with a continuous inner leg "
        "and a separate matching magnetic face")
    bpy.context.scene.name = "DeepReal Exterior Mount Study R38"
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r38-exterior-manifest.json").write_text(json.dumps({
        "source": SOURCE.name,
        "model": OUTPUT.name,
        "mating_plate_mm": [112, 26],
        "magnetic_face_mm": [112, 26, .9],
        "magnetic_face_center_z_mm": -14,
        "continuous_inner_leg_face_y_mm": 3.5,
        "cable_outer_diameter_mm": 3.2,
        "visual_molded_handle_extension_mm": 8.6,
        "visual_separate_sleeve_length_mm": 4.5,
        "plug_mark": "small DeepReal wordmark, appearance only",
        "status": "appearance study, not a validated magnetic mount or cable",
    }, indent=2) + "\n")
    print("R38 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
