"""Build an overview and four maintainable presentation scenes.

The presentation objects are linked duplicates: every copy has its own
transform, but continues to share the canonical mesh/curve datablock. Editing
source geometry therefore propagates to every view.
"""

import math

import bpy
from mathutils import Vector


SOURCE_COLLECTIONS = (
    "DeepReal Product",
    "Drum Optics",
    "Electronics Assembly",
    "Drum Motion",
    "Interconnect Routing",
    "Internal Supports",
    "USB Port (provisional)",
)

SHELL_NAMES = {"Main_Housing", "Face_Sensor_Head",
               "Interaction_Sensor_Head"}
SUPPORT_SUFFIXES = ("_Motor_Bracket", "_Bearing_Carrier")
HOUSING_ATTACHED_PREFIXES = (
    "Main_Housing_USB_",
    "USB_Plug_A_",
    "USB_Plug_B_",
)
HOUSING_ATTACHED_NAMES = {"USB_Cable"}


def _sources(collection_names):
    seen = set()
    result = []
    for collection_name in collection_names:
        collection = bpy.data.collections.get(collection_name)
        if not collection:
            continue
        for obj in collection.objects:
            if obj.name in seen or obj.type not in {"MESH", "CURVE"}:
                continue
            if obj.hide_render or "_Cutter_" in obj.name \
                    or obj.name.endswith("_KeepOut"):
                continue
            seen.add(obj.name)
            result.append(obj)
    return result


def _scene(name, description):
    scene = bpy.data.scenes.new(name)
    scene["DeepReal_View"] = description
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"

    world = bpy.data.worlds.new(name + " World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = \
        (0.012, 0.014, 0.018, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.3
    scene.world = world
    return scene


def _collection(scene, name):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection


def _clone(source, collection, prefix):
    clone = source.copy()
    clone.data = source.data
    clone.name = "{}__{}".format(prefix, source.name)
    clone.parent = None
    clone.matrix_world = source.matrix_world.copy()
    clone.hide_viewport = False
    clone.hide_render = False
    clone.hide_set(False)
    clone["Linked_Source_Object"] = source.name
    clone["Presentation_Instance"] = prefix
    collection.objects.link(clone)
    return clone


def _aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat(
        "-Z", "Y").to_euler()


def _light(collection, name, location, energy, size, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    collection.objects.link(obj)
    _aim(obj, target)


def _rig(scene, prefix, eye_mm, target_mm, lens=58):
    rig = _collection(scene, prefix + " Rig")
    rig.hide_viewport = True
    target = Vector(tuple(value * 0.001 for value in target_mm))
    data = bpy.data.cameras.new(prefix + " Camera")
    data.lens = lens
    camera = bpy.data.objects.new(prefix + " Camera", data)
    camera.location = tuple(value * 0.001 for value in eye_mm)
    rig.objects.link(camera)
    _aim(camera, target)
    scene.camera = camera
    _light(rig, prefix + " Key", (-0.18, -0.20, 0.22), 55, 0.35,
           target)
    _light(rig, prefix + " Fill", (0.20, -0.08, 0.18), 32, 0.30,
           target)
    _light(rig, prefix + " Rim", (0.04, 0.18, 0.16), 42, 0.24,
           target)


def _overview_rig(scene):
    rig = _collection(scene, "OVERVIEW Rig")
    rig.hide_viewport = True
    target = Vector((0.0, 0.0, 0.0))
    data = bpy.data.cameras.new("OVERVIEW Camera")
    data.type = "ORTHO"
    data.ortho_scale = 0.480
    camera = bpy.data.objects.new("OVERVIEW Camera", data)
    camera.location = (0.0, -0.65, 0.0)
    rig.objects.link(camera)
    _aim(camera, target)
    scene.camera = camera
    _light(rig, "OVERVIEW Key", (-0.20, -0.24, 0.24), 95, 0.55, target)
    _light(rig, "OVERVIEW Fill", (0.25, -0.16, 0.14), 55, 0.48, target)
    _light(rig, "OVERVIEW Rim", (0.0, 0.20, 0.20), 65, 0.40, target)


def _label(collection, text, x_mm, z_mm):
    curve = bpy.data.curves.new("Label " + text, "FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 0.006
    curve.extrude = 0.00008
    obj = bpy.data.objects.new("Label " + text, curve)
    obj.location = (x_mm * 0.001, -0.150, z_mm * 0.001)
    obj.rotation_euler.x = math.radians(90.0)
    collection.objects.link(obj)
    return obj


def _ordinary_view(name, prefix, description, predicate, eye, target):
    scene = _scene(name, description)
    geometry = _collection(scene, prefix + " Linked Geometry")
    for source in _sources(SOURCE_COLLECTIONS):
        if predicate(source):
            _clone(source, geometry, prefix)
    _rig(scene, prefix, eye, target)
    return scene


def _center(obj):
    return sum((obj.matrix_world @ Vector(corner)
                for corner in obj.bound_box), Vector()) / 8.0


EXPLODED_CENTERS_MM = {
    "Main_PCBA": (0, 38, 0),
    "EMI_Shield_Can_Lid": (-82, -8, 27),
    "EMI_Shield_Can_Wall_Left": (-120, 0, 27),
    "EMI_Shield_Can_Wall_Right": (-44, 0, 27),
    "EMI_Shield_Can_Wall_Top": (-82, 0, 51),
    "EMI_Shield_Can_Wall_Bottom": (-82, 0, 3),
    "Face_Motor_Connector": (-64, 0, 70),
    "Face_Projector_Connector": (-46, 0, 70),
    "Camera_Flex_Connector_1": (-28, 0, 70),
    "Camera_Flex_Connector_2": (-10, 0, 70),
    "Camera_Flex_Connector_3": (8, 0, 70),
    "Camera_Flex_Connector_4": (26, 0, 70),
    "Interaction_Projector_Connector": (44, 0, 70),
    "Interaction_Motor_Connector": (62, 0, 70),
    "PDM_MEMS_Microphone": (83, 0, 70),
    "Case_Open_Tamper_Switch": (104, 0, 70),
    "CrossLink_NX_FPGA": (-38, 0, 24),
    "NXP_iMX95": (-12, 0, 24),
    "LPDDR_1": (10, 0, 24),
    "LPDDR_2": (27, 0, 24),
    "eMMC_Storage": (48, 0, 24),
    "PMIC_PF09": (-45, 0, -28),
    "PMIC_PF53": (-28, 0, -28),
    "Motor_Driver_A": (-10, 0, -28),
    "Motor_Driver_B": (5, 0, -28),
    "Projector_Driver_A": (20, 0, -28),
    "Projector_Driver_B": (35, 0, -28),
    "USB_PD_Controller": (50, 0, -28),
    "USB_ESD_Protection": (65, 0, -28),
    "Thermal_Spreader": (94, 16, 26),
    "Housing_Thermal_Pad": (94, 30, -27),
}


def _exploded_view():
    scene = _scene(
        "04 Electronics Exploded",
        "Widely separated linked instances of every lower electronics part.")
    geometry = _collection(scene, "EXP Linked Electronics")
    electronics = _sources(("Electronics Assembly",))
    for source in electronics:
        if source.name == "Main_PCBA_Populated_Keepout":
            continue
        clone = _clone(source, geometry, "EXP")
        desired = EXPLODED_CENTERS_MM.get(source.name)
        if desired:
            clone.location += Vector(tuple(value * 0.001 for value in desired)) \
                - _center(clone)
    _rig(scene, "EXP", (205, -310, 115), (0, 8, 8), lens=62)
    return scene


def _in_support_collection(obj):
    return "Internal Supports" in {collection.name
                                    for collection in obj.users_collection}


def _is_housing_off(obj):
    return obj.name not in SHELL_NAMES \
        and obj.name not in HOUSING_ATTACHED_NAMES \
        and not obj.name.startswith(HOUSING_ATTACHED_PREFIXES)


def _is_core(obj):
    return _is_housing_off(obj) and not _in_support_collection(obj) \
        and not obj.name.endswith(SUPPORT_SUFFIXES)


def _fits_overview(obj):
    """Omit the laptop-bound cable tail from the product comparison grid."""
    return obj.name != "USB_Cable" and not obj.name.startswith("USB_Plug_B_")


def _overview_group(sources, collection, prefix, offset_mm, predicate):
    offset = Vector(tuple(value * 0.001 for value in offset_mm))
    for source in sources:
        if predicate(source):
            clone = _clone(source, collection, prefix)
            clone.location += offset


def _overview_view():
    scene = _scene(
        "00 Four View Overview",
        "Labeled overview of all four linked DeepReal presentations.")
    geometry = _collection(scene, "OVERVIEW Linked Geometry")
    labels = _collection(scene, "OVERVIEW Labels")
    sources = _sources(SOURCE_COLLECTIONS)

    _overview_group(sources, geometry, "OV1", (-112, 0, 65),
                    _fits_overview)
    _overview_group(sources, geometry, "OV2", (112, 0, 65),
                    lambda obj: _fits_overview(obj) and _is_housing_off(obj))
    _overview_group(sources, geometry, "OV3", (-112, 0, -80),
                    lambda obj: _fits_overview(obj) and _is_core(obj))

    exploded_offset = Vector((0.075, 0.0, -0.120))
    for source in _sources(("Electronics Assembly",)):
        if source.name == "Main_PCBA_Populated_Keepout":
            continue
        clone = _clone(source, geometry, "OV4")
        desired = EXPLODED_CENTERS_MM.get(source.name)
        if desired:
            clone.location += Vector(tuple(value * 0.001
                                            for value in desired)) \
                - _center(clone)
        clone.location += exploded_offset

    _label(labels, "1  FULLY ASSEMBLED", -112, 23)
    _label(labels, "2  HOUSING REMOVED", 112, 23)
    _label(labels, "3  FUNCTIONAL CORE", -112, -36)
    _label(labels, "4  ELECTRONICS EXPLODED", 95, -36)
    _overview_rig(scene)
    return scene


def _set_camera_view(scene):
    window = bpy.context.window
    if window:
        window.scene = scene
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"


def build():
    """Create and return the overview plus four detail scenes."""
    pivot = bpy.data.objects["Lid_Pivot"]
    original_rotation = pivot.rotation_euler.copy()
    pivot.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    scenes = [
        _overview_view(),
        _ordinary_view(
            "01 Fully Assembled", "ASM",
            "Complete DeepReal hardware with the production-intent shell.",
            lambda _obj: True, (160, -175, 58), (0, 5, 2)),
        _ordinary_view(
            "02 Housing Removed", "OPEN",
            "Housing and drum shells removed; mounting hardware remains.",
            _is_housing_off, (150, -190, 52), (0, 7, 0)),
        _ordinary_view(
            "03 Functional Core", "CORE",
            "Functional internals only; enclosure supports are omitted.",
            _is_core, (150, -190, 52), (0, 7, 0)),
        _exploded_view(),
    ]

    pivot.rotation_euler = original_rotation
    bpy.context.view_layer.update()
    _set_camera_view(scenes[0])
    return scenes
