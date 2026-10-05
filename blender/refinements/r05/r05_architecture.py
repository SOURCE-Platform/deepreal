"""R05 internal packaging and interconnect concept helpers."""

import bpy
from mathutils import Matrix, Vector

import device
import macbook

MM = 0.001


def material(name, color, metallic=0.0, roughness=0.45):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = color
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return value


def append_shifted_electronics(source_blend, name):
    """Append every electronics object and preserve relative placement."""
    with bpy.data.libraries.load(str(source_blend), link=False) as (src, dst):
        if "Electronics Assembly" not in src.collections:
            raise RuntimeError("Electronics Assembly missing from source blend")
        dst.collections = ["Electronics Assembly"]
    imported = dst.collections[0]
    imported.name = name
    bpy.context.scene.collection.children.link(imported)
    imported.hide_viewport = imported.hide_render = False
    bpy.context.view_layer.update()
    shift = Matrix.Translation(Vector((0.0, -5.0 * MM, 0.0)))
    objects = list(imported.all_objects)
    # Electronics geometry is baked in product coordinates and every object in
    # the authoritative collection has an identity matrix_basis.  The source
    # Lid_Pivot is only a presentation transform, so preserve matrix_basis and
    # deliberately discard the imported pivot rather than baking its open-lid
    # rotation into the isolated enclosure model.
    local_matrices = {obj: obj.matrix_basis.copy() for obj in objects}
    identity = Matrix.Identity(4)
    nonidentity = [obj.name for obj, value in local_matrices.items()
                   if not all(abs(value[i][j] - identity[i][j]) < 1e-9
                              for i in range(4) for j in range(4))]
    if nonidentity:
        raise RuntimeError("unexpected electronics local transforms: " +
                           ", ".join(nonidentity[:8]))
    for obj in objects:
        obj.parent = None
        obj.matrix_parent_inverse = Matrix.Identity(4)
    for obj in objects:
        obj.matrix_world = shift @ local_matrices[obj]
        obj["R05_Forward_Shift_mm"] = 5.0
        obj.hide_viewport = obj.hide_render = False
        obj.hide_set(False)
    bpy.context.view_layer.update()
    return imported


def remove_r04_thermal_parts():
    for name in (
            "Housing_Thermal_Pad", "Housing_Thermal_Pad_Left",
            "Housing_Thermal_Pad_Right", "Housing_Thermal_Boss_Left",
            "Housing_Thermal_Boss_Right"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def cut_service_slot(obj, x_width, z0, z1, y_depth, label):
    low, high = sorted((z0, z1))
    cutter = macbook.slab(
        "_" + label + "_Cutter", Vector((0.0, 11.0 * MM, (low + high) / 2 * MM)),
        macbook.X, macbook.Z, (x_width * MM, (high - low) * MM),
        1.0 * MM, y_depth * MM, None)
    bpy.context.scene.collection.objects.link(cutter)
    device._difference(obj, cutter, label)
    obj["R05_Service_Slot_Width_mm"] = x_width
    obj["R05_Service_Slot_Z_mm"] = [low, high]


def open_usb_service_path():
    spreader = bpy.data.objects["Thermal_Spreader"]
    tray = bpy.data.objects["Shield_Rear_Tray"]
    lid = bpy.data.objects["Shield_Front_Lid"]
    cut_service_slot(spreader, 15.0, -24.0, -13.5, 12.0,
                     "Centered_USB_Spreader_Slot")
    cut_service_slot(tray, 15.0, -24.0, -13.5, 18.0,
                     "Centered_USB_Tray_Slot")
    cut_service_slot(lid, 15.0, -24.0, -13.5, 12.0,
                     "Centered_USB_Lid_Slot")
    return spreader, tray, lid


def add_thermal_straps(target):
    copper = bpy.data.materials["Thermal_Spreader_Copper"]
    pad_material = bpy.data.materials["Thermal_Pad"]
    objects = []
    for side, x in (("Left", -20.0), ("Right", 20.0)):
        strap = macbook.slab(
            "Thermal_Link_" + side, Vector((x * MM, 17.7875 * MM, -10.5 * MM)),
            macbook.X, macbook.Z, (18.0 * MM, 9.0 * MM), 1.0 * MM,
            4.425 * MM, copper)
        pad = macbook.slab(
            "Housing_Thermal_Pad_" + side,
            Vector((x * MM, 20.5 * MM, -10.5 * MM)), macbook.X, macbook.Z,
            (18.0 * MM, 9.0 * MM), 1.0 * MM, 1.0 * MM, pad_material)
        target.objects.link(strap)
        target.objects.link(pad)
        strap["DeepReal_Status"] = "concept copper/graphite link; unvalidated"
        pad["DeepReal_Status"] = "small rear housing interface; unvalidated"
        objects.extend((strap, pad))
    return objects


def _curve(name, points, bevel, mat, target, status):
    data = bpy.data.curves.new(name + "_Path", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = bevel * MM
    data.bevel_resolution = 3
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coords in zip(spline.points, points):
        point.co = (*tuple(Vector(coords) * MM), 1.0)
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj["DeepReal_Status"] = status
    return obj


def add_usb_daughterboard(target):
    pcb = material("R05_USB_Daughterboard_Green", (0.04, 0.22, 0.12, 1.0),
                   0.05, 0.42)
    flex = material("R05_Flex_Amber", (0.92, 0.37, 0.04, 1.0), 0.2, 0.38)
    connector = material("R05_Connector_Dark", (0.035, 0.04, 0.05, 1.0),
                         0.0, 0.5)
    board = macbook.slab(
        "Centered_USB_Daughterboard", Vector((0.0, 15.9 * MM, -17.5 * MM)),
        macbook.X, macbook.Z, (16.0 * MM, 13.0 * MM), 1.0 * MM,
        1.0 * MM, pcb)
    main = macbook.slab(
        "Mainboard_USB_Flex_Connector_CONCEPT",
        Vector((0.0, 12.7 * MM, -15.0 * MM)), macbook.X, macbook.Z,
        (10.0 * MM, 4.0 * MM), 0.5 * MM, 1.2 * MM, connector)
    target.objects.link(board)
    target.objects.link(main)
    board["DeepReal_Status"] = "centered USB-C daughterboard; exact part unselected"
    main["DeepReal_Status"] = "requires main-PCB revision; pin mapping unverified"
    usb_flex = _curve(
        "USB3_PD_Internal_Flex_CONCEPT",
        ((0, 15.4, -17.0), (0, 14.0, -17.0), (0, 13.0, -15.0)),
        0.65, flex, target,
        "controlled-impedance flex concept; stackup and pinout unverified")
    return board, main, usb_flex, flex


def add_head_routes(target, flex_material):
    status = "candidate 51-contact head-flex route; bend envelope and pinout unverified"
    connector = material("R05_Head_Connector_Dark", (0.035, 0.04, 0.05, 1.0),
                         0.0, 0.5)
    interfaces = []
    for side, x in (("Face", -20.0), ("Interaction", 20.0)):
        interface = macbook.slab(
            side + "_Head_Flex_Interface_CONCEPT",
            Vector((x * MM, 9.4 * MM, -9.5 * MM)), macbook.X, macbook.Z,
            (8.0 * MM, 4.0 * MM), 0.5 * MM, 1.2 * MM, connector)
        target.objects.link(interface)
        interface["DeepReal_Status"] = (
            "visible route endpoint only; connector and pin mapping unverified")
        interfaces.append(interface)
    face = _curve(
        "Face_Head_Power_Data_Flex_CONCEPT",
        ((-22, 9.7, -23.5), (-30, 8.5, -18.0), (-28, 8.8, -12.0),
         (-20, 9.0, -9.5)), 0.55, flex_material, target, status)
    interaction = _curve(
        "Interaction_Head_Power_Data_Flex_CONCEPT",
        ((22, 9.7, -23.5), (30, 8.5, -18.0), (28, 8.8, -12.0),
         (20, 9.0, -9.5)), 0.55, flex_material, target, status)
    return face, interaction, interfaces


def mark_legacy_j1():
    legacy = bpy.data.objects.get("USB_C_Receptacle")
    if legacy:
        legacy.name = "USB_C_Receptacle_J1_LEGACY_LOCATION"
        legacy.hide_viewport = True
        legacy.hide_render = True
        legacy["DeepReal_Status"] = (
            "current PCB J1 conflicts with centered-port architecture; hidden reference")
    return legacy


def add_housing_inspection_copy(housing, target):
    wire = housing.copy()
    wire.data = housing.data
    wire.name = "Main_Housing_Inspection_Wireframe"
    wire.display_type = "WIRE"
    wire.hide_viewport = True
    wire.hide_render = True
    wire["DeepReal_Status"] = (
        "optional inspection overlay; hide Main_Housing before enabling")
    target.objects.link(wire)
    housing.display_type = "SOLID"
    return wire
