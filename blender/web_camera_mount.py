"""Two-head RGB support/layout proposal, applied only to staged web meshes.

Coordinates below are millimetres in each head's camera frame:
X across the drum, Y up in the image, Z outward along the lens.
Source files, exterior optics and drum geometry are never saved or changed.
"""

import math

import bpy
from mathutils import Matrix, Vector
from web_assembly_cables import flex_material

MM = .001
PREFIX = "WEB_Interaction_RGB_"
BOARD = "Interaction_Head_PCBA_Carrier_CONCEPT_WEB"
CAMERA = "Interaction_RGB_Wide_Assembly_10p8mm_ENVELOPE_R20_WEB"
LENS = "Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20_WEB"
HEADS = {
    "Face": {
        "board": "Face_Head_PCBA_Carrier_CONCEPT_WEB",
        "camera": "Face_RGB_Module_Body_WEB",
        "lens": "Face_RGB_Module_Barrel_WEB",
        "lens_depth_mm": 6.98, "lens_diameter_mm": 5.75,
        "board_offset_mm": 1.72, "carrier_rear_mm": -1.42,
        "fov_degrees": [66, 41],
    },
    "Interaction": {
        "board": BOARD, "camera": CAMERA, "lens": LENS,
        "lens_depth_mm": 8.3, "lens_diameter_mm": 6.95,
        "board_offset_mm": 1, "carrier_rear_mm": -.1,
        "fov_degrees": [102, 67],
    },
}


def camera_frame(by_name, side="Interaction"):
    def center(obj):
        return sum((obj.matrix_world @ v.co for v in obj.data.vertices),
                   Vector()) / len(obj.data.vertices)

    config = HEADS[side]
    origin = center(by_name[config["camera"]])
    outward = (center(by_name[config["lens"]]) - origin).normalized()
    across = Vector((1, 0, 0))
    up = outward.cross(across).normalized()
    frame = Matrix((across, up, outward)).transposed().to_4x4()
    frame.translation = origin
    return frame


def material(name, color, metallic=0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Roughness"].default_value = .48
    shader.inputs["Metallic"].default_value = metallic
    return mat


def prism(name, outline, depth, frame, mat):
    count = len(outline)
    vertices = [(x * MM, y * MM, z * MM)
                for z in depth for x, y in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count)
                 for i in range(count))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = frame.copy()
    obj["Web_Proposal_Status"] = (
        "review-only; support surfaces, tolerances, materials and mating unverified")
    return obj


def box(name, limits, frame, mat):
    (x0, x1), (y0, y1), depth = limits
    return prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                 depth, frame, mat)


def merge_solid(target, addition):
    modifier = target.modifiers.new("Proposal union", "BOOLEAN")
    modifier.operation = "UNION"
    modifier.solver = "EXACT"
    modifier.object = addition
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(
        target.evaluated_get(depsgraph),
        preserve_all_data_layers=True, depsgraph=depsgraph)
    target.modifiers.remove(modifier)
    target.data = mesh
    bpy.data.objects.remove(addition, do_unlink=True)


def replace_face_camera(by_name):
    """Use the standard published envelope at the retained visual nose datum."""
    frame = camera_frame(by_name, "Face")
    normal = frame.col[2].to_3d()
    window = bpy.data.objects["Face_Drum_Lens_RGB_Element"]
    nose = sum((window.matrix_world @ v.co for v in window.data.vertices),
               Vector()) / len(window.data.vertices) - normal * (.35 * MM)
    frame.translation = nose - normal * (6.98 * MM)
    body = box("WEB_Face_Standard_Sensor_Temp",
               ((-5.4, 5.4), (-5.4, 5.4), (-.3, .3)), frame,
               by_name[CAMERA].data.materials[0])
    radius = 5.75 / 2
    lens = prism("WEB_Face_Standard_Lens_Temp",
                 [(radius * math.cos(2 * math.pi * i / 64),
                   radius * math.sin(2 * math.pi * i / 64)) for i in range(64)],
                 (0, 6.98), frame, by_name[LENS].data.materials[0])
    for target_name, replacement in (
        (HEADS["Face"]["camera"], body), (HEADS["Face"]["lens"], lens),
    ):
        target = by_name[target_name]
        target.data = replacement.data
        target.matrix_world = frame.copy()
        target["Web_Proposal_Status"] = (
            "SA31VA30P standard published 10.8 mm outline / 5.75 x 6.98 mm "
            "conservative lens envelope; visual nose datum and 0.6 mm display "
            "plate are provisional, not complete manufacturer CAD")
        bpy.data.objects.remove(replacement, do_unlink=True)


def sensor_tail(frame, mat, side, offset):
    """Fold a static tail behind the sensor, retaining the H/V optical axes."""
    # Product brief: 8.9 mm tail width, 7.3 mm flat length. Its notched terminal
    # and exact mating stacks are not reproduced. Use the length as a
    # centreline budget. A 180-degree assembly orientation puts its tail at
    # the upper edge without swapping either head's H/V optical field axes.
    # The review folds are 1.565 mm for Face and 1.205 mm for Interaction,
    # putting the flipped plug towards each PCB's rear surface. Standard
    # drawing R=0.8 / 20 assembly bends is NOT a formed-stack, wide-tail or
    # dynamic-flex qualification.
    # Keep the same 7.3 mm budget when the face board sits farther rearward
    # to clear its inherited optical carrier. This is a static illustration.
    radius = (offset + 1.41) / 2
    points = [(5.4, -.235), (5.6, -.235)]
    for i in range(1, 65):
        angle = math.pi * i / 64
        points.append((5.6 + radius * math.sin(angle),
                       -.235 - radius * (1 - math.cos(angle))))
    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
    points.append((points[-1][0] - (7.3 - length), -.235 - 2 * radius))
    vertices = []
    for i, (y, z) in enumerate(points):
        before, after = points[max(0, i - 1)], points[min(len(points) - 1, i + 1)]
        tangent = Vector((0, after[0] - before[0], after[1] - before[1])).normalized()
        normal = Vector((0, -tangent.z, tangent.y))
        # Four vertices per cross section, 0.13 mm display film.
        for x, sign in ((-4.45, -1), (4.45, -1), (4.45, 1), (-4.45, 1)):
            vertices.append(tuple((Vector((x, y, z)) + normal * (.065 * sign)) * MM))
    faces = [(3, 2, 1, 0)]
    for i in range(len(points) - 1):
        for j in range(4):
            faces.append((4 * i + j, 4 * i + (j + 1) % 4,
                          4 * (i + 1) + (j + 1) % 4, 4 * (i + 1) + j))
    end = 4 * (len(points) - 1)
    faces.append(tuple(range(end, end + 4)))
    faces = [tuple(reversed(face)) for face in faces]
    mesh = bpy.data.meshes.new(f"WEB_{side}_RGB_Static_Sensor_Tail_PROPOSAL_WEB")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    uv = mesh.uv_layers.new(name="Illustrative_Sensor_Tail_Bands")
    distance = [0]
    for a, b in zip(points, points[1:]):
        distance.append(distance[-1] + math.dist(a, b))
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            section, corner = divmod(mesh.loops[loop_index].vertex_index, 4)
            uv.data[loop_index].uv = (
                float(corner in (1, 2)), distance[section] / distance[-1])
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = frame.copy()
    obj["Web_Proposal_Status"] = (
        "180-degree sensor orientation retains H/V axes; 7.3 mm centreline / "
        f"8.9 mm tail envelope; {radius:.3f} mm static fold; illustrative bands "
        "are not a contact pitch, pinout or verified conductor layout; notch "
        "and mating unverified")
    return obj


def create_camera_mount(staged, cut, side, film):
    """Apply one shared board outline/keepout template to either camera frame."""
    by_name = {obj.name: obj for obj in staged}
    config = HEADS[side]
    prefix = f"WEB_{side}_RGB_"
    board_name = config["board"]
    offset = config["board_offset_mm"]
    rear = -offset - .6
    frame = camera_frame(by_name, side)
    # cut() takes a reference object with matrix_world.
    reference = by_name[config["camera"]].copy()
    reference.matrix_world = frame
    green = by_name[board_name].data.materials[0]
    polymer = material("WEB_RGB_Insulating_Saddle", (.18, .23, .28))
    adhesive = material("WEB_RGB_Seat_Bond_Concept", (.39, .64, .69))
    connector = material("WEB_RGB_J2_Keepout", (.66, .61, .44), .25)
    added = []

    board = box(f"WEB_{side}_Head_Board_Temp",
                ((-41.75, 5.55), (-6, 6), (rear, -offset)), frame, green)
    old_board = by_name[board_name]
    old_board.data = board.data
    old_board.matrix_world = frame.copy()
    bpy.data.objects.remove(board, do_unlink=True)
    old_board["Web_Proposal_Status"] = (
        "47.3 x 12 x 0.6 mm flat layout envelope behind optics; rear J1 "
        "and rear J2 intent; shared outline/keepout study, not routed electronics")

    carrier = by_name[f"{side}_Internal_Optical_Carrier_WEB"]
    carrier["Web_Wide_RGB_Status"] = (
        "review-only rear saddle attachment; exact carrier unvalidated")

    if side == "Face":
        # Retain the source carrier's thickness. Open only its camera end,
        # as on the interaction side, rather than thinning the entire plate.
        cut(carrier, reference,
            ((-7.9 * MM, 8 * MM), (-8 * MM, 8 * MM), (-4 * MM, 8 * MM)),
            "Face_Standard_RGB")
        # Shared J1 location, with the face connector now flush on the PCB rear.
        j1 = by_name["Face_Head_Flex_Connector_PROXY_WEB"]
        template = by_name["Interaction_Head_Flex_Connector_PROXY_WEB"]
        to_template = camera_frame(by_name, "Interaction").inverted() @ template.matrix_world
        j1.data = template.data.copy()
        for vertex in j1.data.vertices:
            vertex.co = to_template @ vertex.co
            vertex.co.z -= (offset - HEADS["Interaction"]["board_offset_mm"]) * MM
        j1.matrix_world = frame.copy()

    saddle = prism(prefix + "Rear_Saddle_PROPOSAL_WEB", [
        (-10, -5.65), (5.55, -5.65), (5.55, 5.65), (-10, 5.65),
        (-10, 4.15), (4.15, 4.15), (4.15, -4.15), (-10, -4.15),
    ], (rear - .8, rear - .2), frame, polymer)
    # Rear J2 occupies the open upper centre; leave the four seats and both
    # carrier anchors connected through the lower rail and outer side.
    cut(saddle, reference,
        ((-4.05 * MM, 4.05 * MM), (2.3 * MM, 5.8 * MM),
         ((rear - 1.4) * MM, (rear + .1) * MM)), f"{side}_RGB_J2_Service_Notch")
    added.append(saddle)
    # Insulating posts pass through board keepouts. No screws or clamps touch
    # the lens/VCM or assume mounting holes in the sensor assembly.
    for x in (-4.8, 4.8):
        for y in (-4.65, 4.65):
            tag = f"{'Inner' if x < 0 else 'Outer'}_{'Lower' if y < 0 else 'Upper'}"
            limits = ((x - .45, x + .45), (y - .45, y + .45))
            post = box(prefix + tag + "_Seat_Temp",
                       (*limits, (rear - .3, -.5)), frame, polymer)
            merge_solid(saddle, post)
            added.append(box(prefix + tag + "_Bond_PROPOSAL_WEB",
                             (*limits, (-.5, -.3)), frame, adhesive))
            cut(old_board, reference,
                ((x * MM - .65 * MM, x * MM + .65 * MM),
                 (y * MM - .65 * MM, y * MM + .65 * MM),
                 (-4 * MM, 0)), tag + "_Seat")

    for y in (-5.15, 5.15):
        tag = "Lower" if y < 0 else "Upper"
        post = box(prefix + tag + "_Carrier_Anchor_Temp",
                   ((-9.7, -8.5), (y - .45, y + .45),
                    (rear - .3, config["carrier_rear_mm"])),
                   frame, polymer)
        merge_solid(saddle, post)
        cut(old_board, reference,
            ((-9.9 * MM, -8.3 * MM),
             ((y - .65) * MM, (y + .65) * MM), (-4 * MM, 0)),
            tag + "_Anchor")
    # These four standoffs support the remainder of the rear-offset board.
    for x in (-28, -20):
        for y in (-5.2, 5.2):
            added.append(box(
                f"WEB_{side}_Head_Board_Spacer_{abs(x)}_{'Lower' if y < 0 else 'Upper'}_PROPOSAL_WEB",
                ((x - .5, x + .5), (y - .45, y + .45),
                 (-offset, config["carrier_rear_mm"])),
                frame, polymer))

    # The face projector bracket extends into the new rear PCB plane.
    # Apply its clearance to BOTH copies, not a face-only board modification.
    cut(old_board, reference,
        ((-16.45 * MM, -12.95 * MM), (-.95 * MM, 2.55 * MM),
         (-4 * MM, 0)), f"{side}_Shared_Projector_Bracket")
    # Keepout, not manufacturer connector CAD. 0.98 mm is the DF37 family
    # mating-height baseline; the standard drawing names HLM-033M-3002-76.
    # Interchangeability with that plug and the wide assembly remains a gate.
    added.append(box(prefix + "J2_Mated_Keepout_PROPOSAL_WEB",
                     ((-3.8, 3.8), (2.5, 5.1), (rear - .98, rear)),
                     frame, connector))
    added.append(sensor_tail(frame, film, side, offset))
    bpy.data.objects.remove(reference, do_unlink=True)
    return added, {
        "status": f"{side.lower()} mechanical/layout proposal, not a released mount or PCB",
        "sensor_orientation": "tail exits upper edge, 180 degrees about unchanged optical axis; H/V axes retained",
        "support": "rear insulating saddle to retained carrier; four provisional bonded sensor seats",
        "board_envelope_mm": [47.3, 12, .6],
        "board_outward_bounds_mm": [rear, -offset],
        "lens_envelope_mm": [config["lens_diameter_mm"], config["lens_depth_mm"]],
        "fov_degrees": config["fov_degrees"],
        "J1": "shared rear FH26 position at local X=-23 mm; face departure updated, interaction retained",
        "J2": "7.6 x 2.6 x 0.98 mm rear mated keepout, not confirmed wide connector geometry",
        "sensor_tail": f"8.9 mm wide / 7.3 mm centreline; {(offset + 1.41) / 2:.3f} mm static fold, terminal notch omitted",
        "tail_artwork": "translucent amber film with 30 illustrative bands; not a verified pin map, pitch, EMI layer or copper stack",
        "limits": [
            "R20 0.6 mm assembly display thickness and optical datum remain provisional.",
            "Bond locations, material, stress, adhesive thickness and tolerances are not approved.",
            "Wide connector CAD, mating, pinout, autofocus and local support BOM remain open.",
            "Sensor orientation requires image/calibration review; lens and assembly outline unchanged.",
            "One shared outline/keepout template is studied; connector footprints, component layout and routed electronics remain open.",
            "Neither the static sensor-tail bend nor the expanded dynamic head flex is qualified.",
        ],
    }


def create_camera_mounts(staged, cut):
    by_name = {obj.name: obj for obj in staged}
    replace_face_camera(by_name)
    # Reuse the long-flex visual language, not its 51-contact image or pin map.
    film = flex_material(30, 8.9, .28, "WEB_RGB_Illustrative")
    additions, reviews = {}, {}
    for side in HEADS:
        additions[side.lower()], reviews[side.lower()] = create_camera_mount(
            staged, cut, side, film)
    return additions, reviews


def optical_support_contacts(side):
    prefix = f"WEB_{side}_Optics_"
    carrier = f"{side}_Internal_Optical_Carrier_WEB"
    projector = f"{side}_SL_Projector_Bracket_WEB"
    depth = prefix + "Depth_Seat_PROPOSAL_WEB"
    return (
        (carrier, projector),
        (projector, prefix + "Projector_Bond_PROPOSAL_WEB"),
        (prefix + "Projector_Bond_PROPOSAL_WEB", f"{side}_SL_Projector_Body_WEB"),
        (carrier, depth),
        (depth, prefix + "Depth_Bond_PROPOSAL_WEB"),
        (prefix + "Depth_Bond_PROPOSAL_WEB", f"{side}_IR_Depth_Module_Body_WEB"),
    )


def create_optical_support(staged, cut, side):
    """Replace legacy carrier/bracket proxies, never the optical modules.

    A service window stops before the projector footprint. Separate seats
    meet matching carrier recesses and provisional 0.1 mm rear bond layers.
    These are contact/layout concepts, not approved adhesive or fastener CAD.
    """
    by_name = {obj.name: obj for obj in staged}
    frame = camera_frame(by_name, side)
    inverse = frame.inverted()
    carrier = by_name[f"{side}_Internal_Optical_Carrier_WEB"]
    bracket = by_name[f"{side}_SL_Projector_Bracket_WEB"]
    rear = HEADS[side]["carrier_rear_mm"]
    front = rear + 1
    polymer = material("WEB_Optics_Insulating_Seat", (.18, .23, .28))
    adhesive = material("WEB_Optics_Rear_Bond_Concept", (.39, .64, .69))
    replacement = box(f"WEB_{side}_Optical_Carrier_Temp",
                      ((-41.75, -7.9), (-6, 6), (rear, front)),
                      frame, carrier.data.materials[0])
    carrier.data = replacement.data
    carrier.matrix_world = frame.copy()
    bpy.data.objects.remove(replacement, do_unlink=True)

    def relief(limits, label):
        cut(carrier, carrier,
            tuple(tuple(value * MM for value in interval) for interval in limits),
            f"{side}_{label}")

    # Keep the PCB-spacer and RGB-anchor rails intact. J1 and its broad flex
    # are behind this plate; their actual exported separation is audited.
    relief(((-32.5, -18.4), (-3.9, 3.9), (rear - .1, front + .1)),
           "Optical_Service_Window")
    carrier["Web_Proposal_Status"] = (
        "review-only optical carrier; separate service opening and recessed "
        "projector/depth seats; module datums unchanged; retention unapproved")
    added = []
    seats = []
    for role, body_name, footprint, bond_outline in (
        ("Projector", f"{side}_SL_Projector_Body_WEB",
         ((-18, -11.4), (-2.7, 4.3)), ((-17, -12.4), (-1.7, 3.3))),
        ("Depth", f"{side}_IR_Depth_Module_Body_WEB",
         ((-41.75, -33.6), (-4.4, 4.4)), ((-41.4, -34.5), (-3.4, 3.4))),
    ):
        body = by_name[body_name]
        body_rear = min((inverse @ body.matrix_world @ vertex.co).z
                        for vertex in body.data.vertices) / MM
        seat_rear = front - .5
        seat_front = body_rear - .1
        assert seat_front >= front - 1e-4, f"Seat enters {body_name}"
        relief((*footprint, (seat_rear, front + .1)), role + "_Seat_Recess")
        seat = box(f"WEB_{side}_Optics_{role}_Seat_PROPOSAL_WEB",
                   (*footprint, (seat_rear, seat_front)), frame, polymer)
        if role == "Projector":
            # Keep the existing manifest/node identity, replacing only the
            # disconnected, interpenetrating legacy bracket geometry.
            bracket.data = seat.data
            bracket.matrix_world = frame.copy()
            bpy.data.objects.remove(seat, do_unlink=True)
            seat = bracket
        else:
            added.append(seat)
        seat["Web_Proposal_Status"] = (
            "recessed support seat, not manufacturer bracket CAD; no invented "
            "module holes or lens clamp; rear bond/retention/load path unapproved")
        bond = box(f"WEB_{side}_Optics_{role}_Bond_PROPOSAL_WEB",
                   (*bond_outline, (seat_front, body_rear)), frame, adhesive)
        bond["Web_Proposal_Status"] = (
            "0.1 mm provisional rear bond layer; exact allowed bond site, "
            "adhesive, loads, thermal path and serviceability unqualified")
        added.append(bond)
        seats.append({
            "module": body_name, "seat": seat.name, "bond": bond.name,
            "seat_footprint_mm": footprint,
            "seat_outward_bounds_mm": [seat_rear, seat_front],
            "module_rear_mm": body_rear,
        })
    return added, {
        "status": "optical support/contact proposal, not a released carrier or mounting method",
        "carrier_bounds_mm": [[-41.75, -7.9], [-6, 6], [rear, front]],
        "service_window_mm": [[-32.5, -18.4], [-3.9, 3.9]],
        "seat_recess_depth_mm": .5, "illustrative_bond_thickness_mm": .1,
        "depth_module_left_overhang_mm": .25,
        "interfaces": seats,
        "limits": [
            "All optical-module geometry and transforms remain unchanged.",
            "Rear bond locations, retention, adhesive, stress, materials and tolerances are unapproved.",
            "The 0.25 mm depth-body overhang is supported by an inset rear bond, not a lens clamp.",
            "Seat/carrier contacts are a nominal geometric fit, not a joint-strength or manufacturing certificate.",
        ],
    }


def create_optical_supports(staged, cut):
    additions, reviews = {}, {}
    for side in HEADS:
        additions[side.lower()], reviews[side.lower()] = create_optical_support(staged, cut, side)
    return additions, reviews
