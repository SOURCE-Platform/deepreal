"""Open-roof lower housing and three side-support cheeks for the R21 study."""

import bpy
from mathutils import Vector

import macbook

MM = .001


def material(name, color, metallic=0.0, roughness=.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = color
    return mat


def yz_prism(name, outline_mm, center_x_mm, thickness_mm, mat, collection):
    obj = macbook.prism(
        name, [(y * MM, z * MM) for y, z in outline_mm],
        Vector((center_x_mm * MM, 0, 0)), macbook.Y, macbook.Z,
        thickness_mm * MM, mat)
    collection.objects.link(obj)
    return obj


def add_chassis(scene):
    for name in ("Main_Housing", "Main_Housing_Inspection_Wireframe"):
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    collection = bpy.data.collections.new("11 — R21 OPEN-TOP LOWER HOUSING")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    graphite = material("R21_Satin_Graphite_Housing",
                        (.13, .16, .18, 1), .35, .38)
    profile = [(-1.5, -29), (10, -29), (14, -28), (18, -25),
               (21, -21), (22.5, -16), (22.5, 25), (21, 28),
               (18, 31), (12, 32), (11.7, 32), (11.7, 6.8),
               (-1.5, 6.8)]
    body = yz_prism("R21_Lower_Housing_And_Rear_Spine", profile,
                    0, 120, graphite, collection)
    body["R21_Status"] = (
        "open front/top drum cradle study; section, wall thickness, "
        "thermal path, fasteners and manufacturing process unverified")

    # These three cheek profiles reach the rotation axis from the housing.
    # The outer cheeks are modeled separately so drum installation remains possible.
    cheek = [(-4.2, 17), (-4.2, 23), (0.5, 27.5), (8, 31.5),
             (12.5, 32), (18, 30), (22.5, 26), (22.5, 5.5),
             (6, 5.5), (6, 10), (2, 14)]
    supports = []
    for label, x, thickness in (("Left_Outer", -58.3, 2.2),
                                ("Center", 0, 3.0),
                                ("Right_Outer", 58.3, 2.2)):
        obj = yz_prism("R21_Support_" + label, cheek, x, thickness,
                       graphite, collection)
        obj["R21_Role"] = "fixed bearing and motor support"
        obj["R21_Assembly"] = (
            "center support fixed to lower housing; outer cheeks are "
            "removable concepts with unmodeled fasteners")
        supports.append(obj)
    fairing = macbook.cylinder(
        "R21_Center_Gap_Fairing", Vector((0, -1.5 * MM, 20 * MM)),
        macbook.X, 12 * MM, 3.0 * MM, graphite, seg=96)
    collection.objects.link(fairing)
    fairing["R21_Role"] = "fixed center baffle, hiding inner drum ends"
    fairing["R21_Status"] = (
        "visual enclosure surface; motor mounts and assembly joints open")
    supports.append(fairing)
    return body, supports
