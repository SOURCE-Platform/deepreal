"""Replace the exposed R14 drive with an internal ring-drive study."""

import bpy
from mathutils import Vector

import macbook
from assembly_primitives import cylinder, tube
from r15_shell import _boolean

MM = 0.001


def cuboid(name, center_mm, size_mm, mat, collection):
    cx, cy, cz = (v * MM for v in center_mm)
    sx, sy, sz = (v * MM / 2.0 for v in size_mm)
    vertices = [(cx + x * sx, cy + y * sy, cz + z * sz)
                for x, y, z in ((-1, -1, -1), (1, -1, -1),
                                (1, 1, -1), (-1, 1, -1),
                                (-1, -1, 1), (1, -1, 1),
                                (1, 1, 1), (-1, 1, 1))]
    faces = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    if mat:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def _replace(name, make):
    original = bpy.data.objects[name]
    collection = original.users_collection[0]
    bpy.data.objects.remove(original, do_unlink=True)
    obj = make(collection)
    assert obj.name == name
    obj["R15_Source"] = "new envelope replacing colliding R14 concept"
    obj["R15_Engineering"] = (
        "geometry only; part, teeth, torque, fit and mounting unverified")
    return obj


def _cap_cut(cap, side, sign, y, z, size_y, size_z, label):
    cutter = macbook.slab(
        side + "_" + label + "_TEMP",
        Vector((sign * 54.12 * MM, y * MM, z * MM)),
        macbook.Y, macbook.Z,
        (size_y * MM, size_z * MM), 0.1 * MM, 1.0 * MM)
    bpy.context.scene.collection.objects.link(cutter)
    _boolean(cap, cutter, "DIFFERENCE")


def _open_fixed_endcap(side, sign):
    face_name = (side + "_Sensor_Head_Flat_End_"
                 + ("Left" if sign < 0 else "Right"))
    cap = bpy.data.objects[face_name]
    bore = macbook.cylinder(
        side + "_Axle_Bore_TEMP",
        Vector((sign * 54.12 * MM, -1.5 * MM, 20 * MM)),
        macbook.X, 2.35 * MM, 1.0 * MM, None, seg=64)
    bpy.context.scene.collection.objects.link(bore)
    _boolean(cap, bore, "DIFFERENCE")
    for index, z in enumerate((16.2, 23.8)):
        _cap_cut(cap, side, sign, 4.8, z, 0.95, 0.95,
                 "Mount_Arm_%d" % index)
    _cap_cut(cap, side, sign, -5.3, 25.0 if sign < 0 else 15.0,
             2.5, 2.5, "Head_Flex_Slot")
    cap["R15_Fixed_Endcap"] = (
        "fixed outer side cover with axle, motor-mount and optical-flex "
        "passages; attachment and seals unverified")
    return cap


def _extend_axle(side, sign):
    axle = bpy.data.objects[side + "_Drum_Axle"]
    axle.data = axle.data.copy()
    matrix = axle.matrix_world
    inv = matrix.inverted()
    old_end = sign * 53.0 * MM
    new_end = sign * 55.15 * MM
    edited = 0
    for vertex in axle.data.vertices:
        point = matrix @ vertex.co
        if abs(point.x - old_end) < 0.00002:
            point.x = new_end
            vertex.co = inv @ point
            edited += 1
    assert edited > 0, (side, edited)
    axle.data.update()
    axle["R15_Axle_Extension"] = (
        "outer stub reaches encoder magnet through fixed endcap bore")


def build(scene):
    dark = bpy.data.materials["Motion_Gear"]
    motor_mat = bpy.data.materials["Motion_Motor"]
    bracket_mat = bpy.data.materials["Motion_Bracket"]
    board_mat = bpy.data.materials["Motion_Encoder_PCBA"]
    magnet_mat = bpy.data.materials["Motion_Encoder_Magnet"]
    steel = bpy.data.materials["Motion_Steel"]
    created = []
    for side, sign in (("Face", -1), ("Interaction", 1)):
        _open_fixed_endcap(side, sign)
        _extend_axle(side, sign)
        ring = _replace(side + "_Ring_Gear", lambda col: tube(
            side + "_Ring_Gear", (sign * 52.6, -1.5, 20),
            macbook.X, 8.2, 10.45, 2.0, dark, col, segments=96))
        ring["R15_Gear_Position"] = (
            "inside intact 3 mm outer drum end band; shell coupling "
            "requires keyed features and tolerance design")
        motor = _replace(side + "_Geared_Motor", lambda col: cylinder(
            side + "_Geared_Motor", (sign * 44.8, 4.8, 20),
            macbook.X, 3.5, 12.0, motor_mat, col, segments=48))
        motor["R15_Motor_Status"] = (
            "7 mm diameter envelope only; supplier, torque and mounting "
            "not selected")
        pinion = _replace(side + "_Motor_Pinion", lambda col: cylinder(
            side + "_Motor_Pinion", (sign * 52.6, 4.8, 20),
            macbook.X, 1.85, 2.0, dark, col, segments=48))
        pinion["R15_Mesh_Status"] = (
            "inside ring, 0.05 mm envelope gap; teeth/backlash unmodeled")
        fixed_col = motor.users_collection[0]
        shaft = cylinder(side + "_Motor_Output_Shaft_CONCEPT",
                         (sign * 51.1, 4.8, 20), macbook.X,
                         0.8, 1.6, steel, fixed_col)
        _replace(side + "_Motor_Bracket", lambda col: cuboid(
            side + "_Motor_Bracket", (sign * 55.7, 5.5, 20),
            (2.0, 5.8, 9.0), bracket_mat, col))
        for label, z in (("Low", 16.2), ("High", 23.8)):
            arm = cuboid(side + "_Motor_Mount_Arm_" + label + "_CONCEPT",
                         (sign * 52.9, 4.8, z), (6.2, 0.7, 0.7),
                         bracket_mat, fixed_col)
            arm["R15_Fixed_Support"] = (
                "mount passes through fixed outer cap; fastening unverified")
            created.append(arm)
        for label, y, z in (("Low", 3.4, 17.1),
                            ("High", 7.4, 22.9)):
            spacer = cylinder(
                side + "_Motor_Mount_Standoff_" + label + "_CONCEPT",
                (sign * 57.2, y, z), macbook.X,
                0.7, 2.0, bracket_mat, fixed_col, segments=24)
            spacer["R15_Fixed_Support"] = (
                "housing-side bracket standoff; fastener not specified")
            created.append(spacer)
        encoder = _replace(side + "_Encoder_Board", lambda col: cuboid(
            side + "_Encoder_Board", (sign * 56.8, -1.5, 20),
            (0.8, 6.0, 6.0), board_mat, col))
        encoder["R15_Encoder_Status"] = (
            "fixed board faces rotating axle magnet across 0.5 mm envelope gap; "
            "IC and magnetic design unverified")
        magnet = _replace(side + "_Encoder_Magnet", lambda col: cylinder(
            side + "_Encoder_Magnet", (sign * 55.5, -1.5, 20),
            macbook.X, 2.0, 0.8, magnet_mat, col, segments=48))
        magnet["R15_Rotating_Assembly"] = side
        created.extend((ring, motor, pinion, shaft, encoder, magnet))
    return created
