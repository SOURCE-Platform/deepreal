"""Parametric full-width ribbon for the R35 torsion-route feasibility study."""

import math

import bpy

MM = .001
AXIS_Y_MM = -1.5
AXIS_Z_MM = 20.0


def section_vertices(x_mm, angle_rad, width_mm, thickness_mm):
    """Four corners of one ribbon section about the drum rotation axis."""
    along_y = math.sin(angle_rad)
    along_z = math.cos(angle_rad)
    normal_y = math.cos(angle_rad)
    normal_z = -math.sin(angle_rad)
    corners = []
    for side, face in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
        y = AXIS_Y_MM + side * width_mm / 2 * along_y
        y += face * thickness_mm / 2 * normal_y
        z = AXIS_Z_MM + side * width_mm / 2 * along_z
        z += face * thickness_mm / 2 * normal_z
        corners.append((x_mm * MM, y * MM, z * MM))
    return corners


def ribbon_vertices(x_start_mm, x_end_mm, angle_deg, width_mm=15.6,
                    thickness_mm=.2, segments=60):
    """Twist from a moving anchor to a stationary anchor on a straight axis."""
    vertices = []
    for step in range(segments + 1):
        fraction = step / segments
        eased = fraction * fraction * (3 - 2 * fraction)
        angle = math.radians(angle_deg) * (1 - eased)
        x = x_start_mm + (x_end_mm - x_start_mm) * fraction
        vertices.extend(section_vertices(x, angle, width_mm, thickness_mm))
    return vertices


def ribbon_faces(segments):
    faces = [(3, 2, 1, 0)]
    for step in range(segments):
        first = 4 * step
        second = first + 4
        for corner in range(4):
            other = (corner + 1) % 4
            faces.append((first + corner, first + other,
                          second + other, second + corner))
    last = 4 * segments
    faces.append((last, last + 1, last + 2, last + 3))
    return faces


def create_ribbon(name, collection, material, x_start_mm, x_end_mm,
                  width_mm, thickness_mm=.2, segments=60):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(ribbon_vertices(x_start_mm, x_end_mm, 0, width_mm,
                                    thickness_mm, segments), [],
                     ribbon_faces(segments))
    mesh.update()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj["R35_Moving_Anchor_X_mm"] = x_start_mm
    obj["R35_Fixed_Anchor_X_mm"] = x_end_mm
    obj["R35_Width_mm"] = width_mm
    obj["R35_Thickness_mm"] = thickness_mm
    obj["R35_Status"] = "candidate torsion strip, not a routed production flex"
    return obj


def set_pose(obj, angle_deg):
    data = ribbon_vertices(obj["R35_Moving_Anchor_X_mm"],
                           obj["R35_Fixed_Anchor_X_mm"], angle_deg,
                           obj["R35_Width_mm"], obj["R35_Thickness_mm"],
                           (len(obj.data.vertices) // 4) - 1)
    for vertex, position in zip(obj.data.vertices, data):
        vertex.co = position
    obj.data.update()
