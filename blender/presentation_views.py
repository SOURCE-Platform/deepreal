"""Build the linked overview, detail, exploded, and shield-cutaway scenes.

The presentation objects are linked duplicates: every copy has its own
transform, but continues to share the canonical mesh/curve datablock. Editing
source geometry therefore propagates to every view.
"""

import math
from pcba_render_settings import configure
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
    configure(scene)
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
    _light(rig, prefix + " Key", (-0.18, -0.20, 0.22), 2.0, 0.35,
           target)
    _light(rig, prefix + " Fill", (0.20, -0.08, 0.18), 1.1, 0.30,
           target)
    _light(rig, prefix + " Rim", (0.04, 0.18, 0.16), 1.5, 0.24,
           target)


def _overview_rig(scene):
    rig = _collection(scene, "OVERVIEW Rig")
    rig.hide_viewport = True
    target = Vector((0.0, 0.0, -0.050))
    data = bpy.data.cameras.new("OVERVIEW Camera")
    data.type = "ORTHO"
    data.ortho_scale = 0.600
    camera = bpy.data.objects.new("OVERVIEW Camera", data)
    camera.location = (0.0, -0.65, -0.050)
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
    "Shield_Front_Lid": (-108, -12, 24),
    "Shield_Rear_Tray": (108, 15, 24),
    "Face_Connector_Bank": (-56, 0, 69),
    "Auxiliary_Connector_Bank": (0, 0, 69),
    "Interaction_Connector_Bank": (56, 0, 69),
    "Face_Motor_Encoder": (-65, 0, 82),
    "Face_Optical_Head_Connector": (-35, 0, 82),
    "Interaction_Optical_Head_Connector": (35, 0, 82),
    "Interaction_Motor_Encoder": (65, 0, 82),
    "PDM_MEMS_Microphone": (-5, 0, 82),
    "Case_Open_Tamper_Switch": (5, 0, 82),
    "Face_CrossLink_NX": (-44, 0, 24), "NXP_iMX95": (-18, 0, 24),
    "LPDDR4X_4GB": (8, 0, 24), "Interaction_CrossLink_NX": (30, 0, 24),
    "eMMC_32GB": (50, 0, 24), "PMIC_PF09": (-50, 0, -28),
    "PF53_SOC": (-38, 0, -28), "PF53_ARM": (-28, 0, -28),
    "Face_Motor_Driver": (-16, 0, -28),
    "Interaction_Motor_Driver": (-4, 0, -28),
    "USB_PD_Controller": (12, 0, -28),
    "System_5V_Buck": (24, 0, -28), "Motor_6V_Buck": (36, 0, -28),
    "VBUS_eFuse": (48, 0, -28),
    "USB_SS_Mux": (60, 0, -28), "USB_C_Receptacle": (78, 0, -28),
    "Thermal_Spreader": (106, 18, -15),
    "Housing_Thermal_Pad": (106, 30, -48),
}


def _is_cable_support(obj):
    return any(fragment in obj.name for fragment in (
        "_Lane_Grounded_", "_Boundary_Ground_Clamp",
        "_Strain_Relief",
    ))


def _is_exploded_part(obj):
    collections = {collection.name for collection in obj.users_collection}
    if "Electronics Assembly" in collections:
        return obj.name != "Main_PCBA_Populated_Keepout"
    if "Interconnect Routing" in collections:
        return True
    if "Drum Motion" in collections:
        return obj.name.endswith("_Motor_Encoder_Harness")
    return "Internal Supports" in collections and _is_cable_support(obj)


def _place_exploded(clone, source):
    desired = EXPLODED_CENTERS_MM.get(source.name)
    if desired:
        clone.location += Vector(tuple(value * 0.001 for value in desired)) \
            - _center(clone)
        return
    if (source.get("PCBA_Component") or source.get("PCBA_NativeSurface")
            or "Pad_Field" in source.name or "_51_Pin_Lands" in source.name
            or source.name.startswith(("Silkscreen_", "PCBA_Ground_Via_"))
            or source.name.endswith("_Latch")):
        clone.location += Vector((0.0, 0.02165, 0.0115))
        return
    if source.name.startswith(("PCB_Ground_Ring_",
                               "Shield_Ground_Via_",
                               "Shield_Chassis_Bond_")):
        clone.location += Vector((0.0, -0.020, 0.020))
    elif "Interconnect Routing" in {
            collection.name for collection in source.users_collection}:
        offset_x = -0.105 if source.name.startswith("Face_") else 0.105
        clone.location += Vector((offset_x, -0.030, -0.075))
    elif source.name.endswith("_Motor_Encoder_Harness"):
        offset_x = -0.105 if source.name.startswith("Face_") else 0.105
        clone.location += Vector((offset_x, -0.030, -0.075))
    elif _is_cable_support(source):
        offset_x = -0.035 if source.name.startswith("Face_") else 0.035
        clone.location += Vector((offset_x, 0.025, -0.055))


def _exploded_view():
    scene = _scene(
        "04 Electronics Exploded",
        "Separated linked electronics, shield, apron, cable, and clip parts.")
    geometry = _collection(scene, "EXP Linked Electronics")
    sources = _sources((
        "Electronics Assembly", "Interconnect Routing",
        "Drum Motion", "Internal Supports",
    ))
    for source in sources:
        if not _is_exploded_part(source):
            continue
        clone = _clone(source, geometry, "EXP")
        _place_exploded(clone, source)
    _rig(scene, "EXP", (310, -500, 185), (0, 0, -30), lens=48)
    return scene


def _is_cutaway_part(obj):
    collections = {collection.name for collection in obj.users_collection}
    if "Electronics Assembly" in collections:
        return obj.name not in {
            "Main_PCBA_Populated_Keepout", "Shield_Front_Lid",
        }
    if "Interconnect Routing" in collections:
        return True
    if "Drum Motion" in collections:
        return obj.name.endswith("_Motor_Encoder_Harness")
    return "Internal Supports" in collections and _is_cable_support(obj)


def _cutaway_view():
    scene = _ordinary_view(
        "05 Shield Cutaway", "CUT",
        "Front lid removed to explain the shield boundary and lower apron.",
        _is_cutaway_part, (125, -165, -2), (0, 16, -12))
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
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
    for source in _sources((
            "Electronics Assembly", "Interconnect Routing",
            "Drum Motion", "Internal Supports")):
        if not _is_exploded_part(source):
            continue
        clone = _clone(source, geometry, "OV4")
        _place_exploded(clone, source)
        clone.location += exploded_offset

    _label(labels, "1  FULLY ASSEMBLED", -112, 23)
    _label(labels, "2  HOUSING REMOVED", 112, 23)
    _label(labels, "3  FUNCTIONAL CORE", -112, -15)
    _label(labels, "4  ELECTRONICS EXPLODED", 95, -15)
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
    """Create and return the overview plus linked review scenes."""
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
        _cutaway_view(),
    ]

    pivot.rotation_euler = original_rotation
    bpy.context.view_layer.update()
    _set_camera_view(scenes[0])
    return scenes
