"""Small Blender primitives shared by the internal-assembly builders."""

import bpy
from mathutils import Vector

import macbook


MM = 0.001


def link_only(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def box(name, center_mm, dimensions_mm, radius_mm, material, collection):
    center = Vector(tuple(value * MM for value in center_mm))
    dx, dy, dz = (value * MM for value in dimensions_mm)
    obj = macbook.slab(name, center, macbook.X, macbook.Z, (dx, dz),
                       radius_mm * MM, dy, material)
    return link_only(obj, collection)


def cylinder(name, center_mm, axis, radius_mm, length_mm, material,
             collection, segments=48):
    center = Vector(tuple(value * MM for value in center_mm))
    obj = macbook.cylinder(name, center, axis, radius_mm * MM,
                           length_mm * MM, material, seg=segments)
    return link_only(obj, collection)


def tube(name, center_mm, axis, inner_radius_mm, outer_radius_mm,
         length_mm, material, collection, segments=48):
    center = Vector(tuple(value * MM for value in center_mm))
    obj = macbook.tube(name, center, axis, inner_radius_mm * MM,
                       outer_radius_mm * MM, length_mm * MM, material,
                       seg=segments)
    return link_only(obj, collection)


def wire(name, points_mm, radius_mm, material, collection):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = radius_mm * MM
    curve.bevel_resolution = 3
    curve.materials.append(material)
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points_mm) - 1)
    for point, coordinates in zip(spline.bezier_points, points_mm):
        point.co = tuple(value * MM for value in coordinates)
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    return obj


def routed_wire(name, points_mm, radius_mm, bend_radius_mm, material,
                collection, corner_segments=8):
    """Build a non-overshooting cable path with rounded waypoint corners."""
    points = [Vector(point) for point in points_mm]
    sampled = [points[0]]
    for index in range(1, len(points) - 1):
        previous, corner, following = points[index - 1:index + 2]
        to_previous = previous - corner
        to_following = following - corner
        previous_length = to_previous.length
        following_length = to_following.length
        if previous_length < 1e-6 or following_length < 1e-6:
            sampled.append(corner)
            continue
        to_previous.normalize()
        to_following.normalize()
        if to_previous.dot(to_following) < -0.999:
            sampled.append(corner)
            continue
        trim = min(
            bend_radius_mm,
            previous_length * 0.35,
            following_length * 0.35,
        )
        entry = corner + to_previous * trim
        exit_point = corner + to_following * trim
        sampled.append(entry)
        for step in range(1, corner_segments + 1):
            factor = step / corner_segments
            point = (
                (1.0 - factor) ** 2 * entry
                + 2.0 * (1.0 - factor) * factor * corner
                + factor ** 2 * exit_point
            )
            sampled.append(point)
    sampled.append(points[-1])

    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = radius_mm * MM
    curve.bevel_resolution = 3
    curve.materials.append(material)
    spline = curve.splines.new("POLY")
    spline.points.add(len(sampled) - 1)
    for point, coordinates in zip(spline.points, sampled):
        point.co = tuple(value * MM for value in coordinates) + (1.0,)
    obj = bpy.data.objects.new(name, curve)
    obj["Minimum_Bend_Radius_mm"] = bend_radius_mm
    collection.objects.link(obj)
    return obj


def material(name, color, metallic=0.0, roughness=0.45, alpha=1.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    mat.diffuse_color = (*color, alpha)
    if alpha < 1.0:
        try:
            mat.surface_render_method = "BLENDED"
        except AttributeError:
            pass
    return mat


def tag(obj, subsystem, evidence="CONCEPT ENVELOPE"):
    obj["DeepReal_Subsystem"] = subsystem
    obj["DeepReal_Evidence"] = evidence
    return obj
