"""Provisional web-only cable paths for the internal reveal study.

These paths show connection intent. They have not passed collision, bend,
signal-integrity, or rotation-cycle checks and must not drive fabrication.
"""

import math

import bpy
from mathutils import Vector


FPC_CONTACTS = 51
FPC_END_WIDTH_MM = 15.6
FPC_CONTACT_PITCH_MM = 0.3


def head_local_path(side, points):
    """Locate a visual cable start on the actual (possibly tilted) head board."""
    board = bpy.data.objects[f"{side}_Head_PCBA_Carrier_CONCEPT"]
    return [tuple((board.matrix_world @ (Vector(point) * 0.001)) * 1000)
            for point in points]


def optical_path(side):
    """Rest-pose loop with broad bends through the film's thin dimension."""
    start = head_local_path(side, [
        ((-34 if side == "Face" else 23), -3.55 if side == "Face" else -1.05, 20),
    ])[0]
    board = bpy.data.objects[f"{side}_Head_PCBA_Carrier_CONCEPT"]
    entry = board.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    tilt = math.atan2(entry.y, -entry.z)
    head_radius = 16.0
    head_arc = []
    for step in range(11):
        angle = (math.pi / 2 - tilt) * step / 10
        head_arc.append((
            start[0],
            start[1] + head_radius * (math.cos(tilt) - math.cos(tilt + angle)),
            start[2] + head_radius * (math.sin(tilt) - math.sin(tilt + angle)),
        ))
    sign = -1 if side == "Face" else 1
    height = head_arc[-1][2]
    rear = 41.55
    exit_y = head_arc[-1][1]
    departure_x = 36 if side == "Face" else 25
    stem = [(sign * departure_x, exit_y + distance, height)
            for distance in (2, 4, 6)]
    sweep_start = stem[-1][1]
    sweep_radius = rear - sweep_start
    sweep = []
    for step in range(1, 25):
        fraction = step / 24
        angle = math.pi * fraction / 2
        # Keep both lateral slope and curvature continuous where the sweep
        # meets the straight stem and descent.
        eased = fraction**3 * (10 + fraction * (-15 + 6 * fraction))
        sweep.append((
            sign * (departure_x + (22 - departure_x) * eased),
            sweep_start + sweep_radius * math.sin(angle),
            height + sweep_radius * (math.cos(angle) - 1),
        ))
    exit_height = sweep[-1][2]
    straight_steps = math.ceil((exit_height + 30) / 2.5)
    straight = [
        (sign * 22, rear, exit_height + (-30 - exit_height) * step / straight_steps)
        for step in range(1, straight_steps)
    ]
    landing_y = 9.85
    return_radius = (rear - landing_y) / 2
    loop = [
        (sign * 22, landing_y + return_radius * (1 + math.cos(math.pi * step / 16)),
         -30 - return_radius * math.sin(math.pi * step / 16))
        for step in range(17)
    ]
    return head_arc + stem + sweep + straight + loop + [
        (sign * 22, landing_y, -27), (sign * 22, landing_y, -23.5),
    ]


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


def flex_images():
    """Translucent film with contact-density artwork, not a routed pin map."""
    width, height = 1024, 256
    color = bpy.data.images.new("WEB_FPC_Amber_51_Contacts", width=width, height=height, alpha=True)
    normal = bpy.data.images.new("WEB_FPC_Fine_Trace_Normal", width=width, height=height, alpha=True)
    normal.colorspace_settings.name = "Non-Color"
    colors, normals = [], []
    # The 51 fine bands depict contact density only. Continuity, shielding and
    # the dynamic copper stack still require a numbered flex design and SI review.
    lanes = [(FPC_CONTACT_PITCH_MM * (index + 1)) / FPC_END_WIDTH_MM
             for index in range(FPC_CONTACTS)]
    cross_section = []
    for column in range(width):
        u = (column + 0.5) / width
        distance = min(abs(u - center) for center in lanes)
        conductor = distance < 0.003
        slope = (distance / 0.007) * math.exp(-(distance / 0.007) ** 2) * 0.42
        nearest = min(lanes, key=lambda center: abs(u - center))
        if u < nearest:
            slope = -slope
        cross_section.append((conductor, slope))
    for row in range(height):
        v = (row + 0.5) / height
        exposed = v < 0.018 or v > 0.982
        stiffener = v < 0.042 or v > 0.958
        for conductor, slope in cross_section:
            if conductor:
                rgb = (0.98, 0.77, 0.35) if exposed else (0.78, 0.45, 0.15)
                opacity = 1.0
            elif stiffener:
                rgb = (0.53, 0.29, 0.085)
                opacity = 0.86
            else:
                rgb = (0.82, 0.47, 0.12)
                opacity = 0.28
            colors.extend((*rgb, opacity))
            normals.extend((0.5 - slope * 0.5, 0.5, 0.5 + math.sqrt(1 - slope*slope) * 0.5, 1.0))
    color.pixels.foreach_set(colors)
    normal.pixels.foreach_set(normals)
    color.pack()
    normal.pack()
    return color, normal


def flex_material():
    result = material("WEB_FPC_Amber_Film", (0.72, 0.39, 0.105))
    result.surface_render_method = "BLENDED"
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.42
    color, normal = flex_images()
    color_node = result.node_tree.nodes.new("ShaderNodeTexImage")
    color_node.image = color
    result.node_tree.links.new(color_node.outputs["Color"], shader.inputs["Base Color"])
    result.node_tree.links.new(color_node.outputs["Alpha"], shader.inputs["Alpha"])
    normal_node = result.node_tree.nodes.new("ShaderNodeTexImage")
    normal_node.image = normal
    bump = result.node_tree.nodes.new("ShaderNodeNormalMap")
    bump.inputs["Strength"].default_value = 0.6
    result.node_tree.links.new(normal_node.outputs["Color"], bump.inputs["Color"])
    result.node_tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return result


def ribbon(name, control, film):
    steps = 4
    path = smooth_path(control, steps=steps)
    vertices = []
    faces = []
    previous_side = None
    for index, center in enumerate(path):
        tangent = path[min(index+1, len(path)-1)] - path[max(index-1, 0)]
        tangent.normalize()
        # The broad face stays across X as the loop bends through its thin
        # dimension in the depth/height plane. Project the width off the
        # centerline tangent instead of bending the width around an X/Z fan.
        desired = Vector((1, 0, 0))
        side = desired - tangent * desired.dot(tangent)
        if side.length < 1e-5:
            raise RuntimeError(f"{name}: ribbon frame degenerated at section {index}")
        side.normalize()
        if previous_side is not None and side.dot(previous_side) < 0:
            raise RuntimeError(f"{name}: ribbon frame flipped at section {index}")
        previous_side = side
        # Retain the planned 15.6 mm mating width along this visual-only path.
        # A narrowed trunk cannot be presumed to carry the 51-contact circuit.
        across = side * (FPC_END_WIDTH_MM * 0.0005)
        at_end = min(index, len(path) - 1 - index) / (len(path) - 1) < 0.042
        thick = tangent.cross(side).normalized() * (0.0001 if at_end else 0.00008)
        vertices.extend((center - across - thick, center + across - thick,
                         center - across + thick, center + across + thick))
        if index:
            p = (index - 1) * 4
            q = index * 4
            travel = center - path[index - 1]
            left = (vertices[q] - vertices[p]).dot(travel)
            right = (vertices[q+1] - vertices[p+1]).dot(travel)
            if left <= 0 or right <= 0:
                raise RuntimeError(
                    f"{name}: folded ribbon edge at section {index}, "
                    f"center {tuple(round(axis * 1000, 2) for axis in center)}, "
                    f"travel {travel.length * 1000:.2f} mm, "
                    f"edge advancement {left * 1e6:.2f}/{right * 1e6:.2f} mm²")
            faces.extend(((p, p+1, q+1, q), (p+2, q+2, q+3, p+3),
                          (p, q, q+2, p+2), (p+1, p+3, q+3, q+1)))
    faces.extend(((0, 2, 3, 1),
                  tuple((len(path)-1)*4 + offset for offset in (0, 1, 3, 2))))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="FPC_Traces")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.loops[loop_index].vertex_index
            section, across = divmod(vertex, 4)
            uv.data[loop_index].uv = (float(across in (1, 3)), section / (len(path) - 1))
    mesh.materials.append(film)
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
    film = flex_material()
    motor_color = (0.24, 0.27, 0.31)
    angle_color = (0.27, 0.37, 0.41)
    result = {}
    # The J1 tails pass behind the head carriers, arc behind the main PCB and
    # return below its lower edge to J2/J3. This large rest-pose shape is a
    # presentation study, not a checked enclosure cavity or moving service loop.
    result["optical_concepts"] = [
        ribbon("WEB_Face_Optical_Flex_CONCEPT", optical_path("Face"), film),
        ribbon("WEB_Interaction_Optical_Flex_CONCEPT",
               optical_path("Interaction"), film),
    ]
    result["motor_harness_concepts"] = [
        wire("WEB_Face_Motor_Harness_CONCEPT", [
            (-9.7, 5, 20), (-11, 4.2, 30), (-27, 4.5, 31),
            (-44, 4.5, 31), (-48, 5.2, 25), (-48, 5.5, 4),
            (-48, 9.7, -23), (-47, 9.3, -27.5), (-39, 9.0, -27.5),
            (-32.8, 9.1, -27.5), (-32.8, 9.85, -23.5),
        ], motor_color),
        wire("WEB_Interaction_Motor_Harness_CONCEPT", [
            (9.7, 5, 20), (11, 4.2, 30), (27, 4.5, 31),
            (44, 4.5, 31), (55, 5.2, 25), (55, 5.5, 4),
            (55, 9.7, -23), (47, 9.3, -27.5), (39, 9.0, -27.5),
            (32.8, 9.1, -27.5), (32.8, 9.85, -23.5),
        ], motor_color),
    ]
    result["angle_harness_concepts"] = [
        wire("WEB_Face_Angle_Harness_CONCEPT", [
            (-59.55, -1.5, 20), (-62, -1.7, 26), (-69, 0.5, 30),
            (-69, 3.0, 10), (-69, 4.2, -18), (-69, 4.7, -31),
            (-67, 4.8, -36.5), (-47, 5.0, -36.5),
            (-35.2, 5.0, -36.5), (-35.2, 4.8, -30),
            (-35.2, 9.8, -26), (-35.2, 9.85, -23.5),
        ], angle_color),
        wire("WEB_Interaction_Angle_Harness_CONCEPT", [
            (57, 4.5, 20), (62, 3.6, 26), (69, 4.2, 30),
            (69, 4.2, 10), (69, 4.2, -18), (69, 4.7, -31),
            (67, 4.8, -36.5), (47, 5.0, -36.5),
            (35.2, 5.0, -36.5), (35.2, 4.8, -30),
            (35.2, 9.8, -26), (35.2, 9.85, -23.5),
        ], angle_color),
    ]
    return result
