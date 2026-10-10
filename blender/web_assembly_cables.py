"""Provisional web-only cable paths for the internal reveal study.

These paths show connection intent. They have not passed collision, bend,
signal-integrity, or rotation-cycle checks and must not drive fabrication.
"""

import bpy
from mathutils import Vector


def material(name, color, metallic=0.0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = 0.58
    return result


def smooth_path(control, steps=6):
    points = [Vector(point) * 0.001 for point in control]
    out = []
    for index in range(len(points) - 1):
        a = points[max(index - 1, 0)]
        b = points[index]
        c = points[index + 1]
        d = points[min(index + 2, len(points) - 1)]
        for step in range(steps):
            t = step / steps
            value = 0.5 * ((2 * b) + (-a + c) * t
                           + (2*a - 5*b + 4*c - d) * t*t
                           + (-a + 3*b - 3*c + d) * t*t*t)
            out.append(value)
    out.append(points[-1])
    return out


def ribbon(name, control, color):
    path = smooth_path(control)
    widths = [0.006 + 0.0096 * max(0, 1 - index / 6,
                                  1 - (len(path) - index - 1) / 6)
              for index in range(len(path))]
    vertices = []
    faces = []
    side = Vector((0, 0, 1))
    for index, center in enumerate(path):
        tangent = path[min(index+1, len(path)-1)] - path[max(index-1, 0)]
        tangent.normalize()
        side -= tangent * side.dot(tangent)
        if side.length < 0.1:
            side = tangent.cross(Vector((0, 1, 0)))
        side.normalize()
        across = side * widths[index] / 2
        thick = tangent.cross(side).normalized() * 0.0002
        vertices.extend((center - across - thick, center + across - thick,
                         center - across + thick, center + across + thick))
        if index:
            p = (index - 1) * 4
            q = index * 4
            faces.extend(((p, p+1, q+1, q), (p+2, q+2, q+3, p+3),
                          (p, q, q+2, p+2), (p+1, p+3, q+3, q+1)))
    faces.extend(((0, 2, 3, 1),
                  tuple((len(path)-1)*4 + offset for offset in (0, 1, 3, 2))))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(material("WEB_Optical_Flex_Concept", color))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["Web_Status"] = "connection intent only; no proven moving cable route"
    return obj


def wire(name, control, color):
    path = smooth_path(control)
    data = bpy.data.curves.new(name + "_Curve", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 12
    data.bevel_depth = 0.00038
    data.bevel_resolution = 3
    spline = data.splines.new("POLY")
    spline.points.add(len(path) - 1)
    for point, coordinate in zip(spline.points, path):
        point.co = (*coordinate, 1)
    data.materials.append(material(name + "_Material", color))
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["Web_Status"] = "stationary harness concept; connector pinout open"
    return obj


def create_cables():
    data_color = (0.58, 0.42, 0.16)
    motor_color = (0.24, 0.27, 0.31)
    angle_color = (0.27, 0.37, 0.41)
    result = {}
    result["optical_concepts"] = [
        ribbon("WEB_Face_Optical_Flex_CONCEPT", [
            (-36, -5.7, 20), (-28, -4, 20), (-11, 0, 20),
            (-2.5, 4, 17), (-5, 9, 8), (-16, 10, -12), (-22, 10, -23),
        ], data_color),
        ribbon("WEB_Interaction_Optical_Flex_CONCEPT", [
            (36, -5.7, 18), (46, -3, 19), (55, 2, 17),
            (57, 9, 8), (46, 10, -9), (29, 10, -18), (22, 10, -23),
        ], data_color),
    ]
    result["motor_harness_concepts"] = [
        wire("WEB_Face_Motor_Harness_CONCEPT", [
            (-9.7, 5, 20), (-10, 8, 15), (-20, 10, -3), (-34, 10, -23.5),
        ], motor_color),
        wire("WEB_Interaction_Motor_Harness_CONCEPT", [
            (9.7, 5, 20), (10, 9, 13), (20, 10, -4), (34, 10, -23.5),
        ], motor_color),
    ]
    result["angle_harness_concepts"] = [
        wire("WEB_Face_Angle_Harness_CONCEPT", [
            (-59.55, -1.5, 20), (-58, 9, 13), (-48, 10, -5), (-34, 10, -23.5),
        ], angle_color),
        wire("WEB_Interaction_Angle_Harness_CONCEPT", [
            (57, 4.5, 20), (58, 9, 13), (48, 10, -5), (34, 10, -23.5),
        ], angle_color),
    ]
    return result
