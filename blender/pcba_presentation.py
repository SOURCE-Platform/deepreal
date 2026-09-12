"""Orthographic PCBA packaging-study views derived from canonical geometry."""

import math

import bpy
from mathutils import Matrix, Vector

from assembly_primitives import box, material, tag, wire
from pcba_bom import ALL_PARTS, BOARD
import presentation_views as pv


EXCLUDED = (
    "Shield_", "PCB_Ground_Ring_", "Thermal_", "Housing_Thermal_",
    "Face_Connector_Bank", "Auxiliary_Connector_Bank",
    "Interaction_Connector_Bank", "Main_PCBA_Populated_Keepout",
)


def _is_pcba(obj):
    if obj.name == "Main_PCBA":
        return True
    if obj.name.startswith(EXCLUDED) or obj.hide_render:
        return False
    return "Electronics Assembly" in {
        collection.name for collection in obj.users_collection}


def _text(collection, text, x, y, z, size=1.5, align="CENTER", front=True):
    curve = bpy.data.curves.new("View_Label_" + text, "FONT")
    curve.body = text
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.size = size * 0.001
    curve.extrude = 0.015 * 0.001
    obj = bpy.data.objects.new("View_Label_" + text, curve)
    obj.location = (x * 0.001, y * 0.001, z * 0.001)
    obj.rotation_euler.x = math.radians(90.0 if front else -90.0)
    if not front:
        obj.scale.x = -1.0
        obj.scale.y = -1.0
    collection.objects.link(obj)
    return obj


def _ortho_rig(scene, prefix, front=True, scale=112, target_x=0, target_z=None):
    rig = pv._collection(scene, prefix + " Rig")
    rig.hide_viewport = True
    z = BOARD["center_z"] if target_z is None else target_z
    target = Vector((target_x*0.001, BOARD["center_y"]*0.001, z*0.001))
    data = bpy.data.cameras.new(prefix + " Camera")
    data.type = "ORTHO"
    data.ortho_scale = scale * 0.001
    camera = bpy.data.objects.new(prefix + " Camera", data)
    camera.location = (target.x, (-0.20 if front else 0.20), target.z)
    rig.objects.link(camera)
    pv._aim(camera, target)
    scene.camera = camera
    light_y = -0.16 if front else 0.16
    pv._light(rig, prefix + " Key", (-0.08, light_y, 0.08), 1.2, 0.25,
              target)
    pv._light(rig, prefix + " Fill", (0.10, light_y, -0.05), .5, 0.22,
              target)


def _clone_pcba(scene, prefix, transform=None):
    geometry = pv._collection(scene, prefix + " Linked PCBA")
    clones = []
    for source in pv._sources(("Electronics Assembly",)):
        if not _is_pcba(source):
            continue
        clone = pv._clone(source, geometry, prefix)
        if transform is not None:
            clone.matrix_world = transform @ clone.matrix_world
        clones.append(clone)
    return clones


def _board_view(name, prefix, front):
    side = "top" if front else "bottom"
    scene = pv._scene(name, "Orthographic {} assembly view of the 90 x 28 mm preliminary PCBA.".format(side))
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 900
    _clone_pcba(scene, prefix)
    labels = pv._collection(scene, prefix + " Labels")
    _text(labels, "DEEPREAL MAIN PCBA - {} SIDE - PRELIMINARY PACKAGING".format(side.upper()),
          0, 9.5 if front else 23.0, 6.5, 1.75, front=front)
    _ortho_rig(scene, prefix, front=front, scale=125, target_z=-9.5)
    return scene


def _dimension_view():
    scene = pv._scene("08 PCBA Dimensioned", "Dimensioned 90 x 28 x 1.6 mm packaging-study view.")
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 1100
    _clone_pcba(scene, "DIM")
    labels = pv._collection(scene, "DIM Labels")
    lines = pv._collection(scene, "DIM Lines")
    ink = material("PCBA_Dimension_Ink", (0.88, 0.74, 0.18),
                   metallic=0.15, roughness=0.42)
    y = 10.0
    for name, points in (
        ("DIM_Width", ((-45,y,-29), (45,y,-29))),
        ("DIM_Depth", ((-49,y,-25.5), (-49,y,2.5))),
        ("DIM_Width_Left", ((-45,y,-27.5), (-45,y,-30.5))),
        ("DIM_Width_Right", ((45,y,-27.5), (45,y,-30.5))),
        ("DIM_Depth_Bottom", ((-47.5,y,-25.5), (-50.5,y,-25.5))),
        ("DIM_Depth_Top", ((-47.5,y,2.5), (-50.5,y,2.5))),
    ):
        tag(wire(name, points, 0.09, ink, lines), "PCBA dimensions", "MEASURED")
    _text(labels, "90.0 mm", 0, 9.7, -31.0, 1.45)
    _text(labels, "28.0 mm", -52.0, 9.7, -11.5, 1.45)
    _text(labels, "PCB 1.60 mm | TOP MAX 3.16 mm | BOTTOM MAX 1.30 mm | POPULATED STACK 6.06 mm",
          0, 9.7, 6.8, 1.25)
    _ortho_rig(scene, "DIM", front=True, scale=130, target_z=-11.0)
    return scene


def _identification_view():
    scene = pv._scene("09 PCBA Identification", "Top and bottom component-reference identification view.")
    scene.render.resolution_x = 2200
    scene.render.resolution_y = 1500
    top_shift = Matrix.Translation(Vector((-55*0.001, 0, 8*0.001)))
    center = Vector((0, BOARD["center_y"]*0.001, BOARD["center_z"]*0.001))
    flip = Matrix.Translation(Vector((55*0.001, 0, 8*0.001)) + center) @ \
        Matrix.Rotation(math.pi, 4, "X") @ Matrix.Translation(-center)
    _clone_pcba(scene, "ID_TOP", top_shift)
    _clone_pcba(scene, "ID_BOTTOM", flip)
    labels = pv._collection(scene, "ID Labels")
    _text(labels, "TOP / FRONT", -55, 8.0, 13.0, 1.8)
    _text(labels, "BOTTOM / REAR", 55, 8.0, 13.0, 1.8)
    top_parts = [p for p in ALL_PARTS if p["side"] == "TOP"]
    bottom_parts = [p for p in ALL_PARTS if p["side"] == "BOTTOM"]
    for column, parts, x in ((0, top_parts, -110), (1, bottom_parts, 10)):
        for index, part in enumerate(parts):
            z = -34.0 - index * 2.35
            _text(labels, "{}  {}".format(part["ref"], part["name"]),
                  x, 8.0, z, 1.05, align="LEFT")
    _ortho_rig(scene, "ID", front=True, scale=235, target_z=-22.0)
    return scene


def _flex_study():
    scene = pv._scene("10 Camera Flex Study", "Two combined drum interfaces versus the four-camera fallback.")
    scene.render.resolution_x = 2100
    scene.render.resolution_y = 1000
    geometry = pv._collection(scene, "FLEX Geometry")
    labels = pv._collection(scene, "FLEX Labels")
    board_mat = bpy.data.materials["Electronics_PCBA"]
    conn_mat = bpy.data.materials["PCBA_Connector_Housing"]
    flex_mat = bpy.data.materials["Interconnect_Flex"]
    for x, label in ((-55, "CURRENT: 2 x 51-PIN DRUM INTERFACES"),
                     (55, "SI FALLBACK: SEPARATE CAMERA FLEXES")):
        board = box("Flex_Study_Board_" + str(x),
                    (x, BOARD["center_y"], BOARD["center_z"]),
                    (90, 1.6, 28), .8, board_mat, geometry)
        tag(board, "Packaging alternative", "DIAGRAM ONLY")
        _text(labels, label, x, 10.0, 6.0, 1.55)
    for x in (-73, -37):
        connector = box("Consolidated_Drum_FPC_" + str(x),
                        (x, 15.0, -23.3), (15.6, 1.0, 3.2), .20,
                        conn_mat, geometry)
        tag(connector, "Two-interface baseline", "51-PIN - SI UNPROVEN")
        flex = box("Consolidated_Drum_Flex_" + str(x),
                   (x, 14.2, -29.0), (16, .25, 8), .8, flex_mat, geometry)
        tag(flex, "Drum flex baseline", "PACKAGING STUDY ONLY")
    for side_x in (37, 73):
        for layer, y in (("Front", 15.05), ("Rear", 17.65)):
            connector = box("Four_FPC_{}_{}".format(side_x, layer),
                            (side_x, y, -23.6), (13, 1, 3.8), .18,
                            conn_mat, geometry)
            tag(connector, "Four-interface fallback", "13 x 3.8 mm FPC")
    _text(labels, "31.2 mm total connector body length; contact order open", -55, 10, -32, 1.15)
    _text(labels, "Lower flex integration risk, greater edge and routing demand", 55, 10, -32, 1.15)
    _ortho_rig(scene, "FLEX", front=True, scale=230, target_z=-13.5)
    return scene


def build():
    pivot = bpy.data.objects["Lid_Pivot"]
    original = pivot.rotation_euler.copy()
    pivot.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    scenes = [
        _board_view("06 PCBA Top", "PCBA_TOP", True),
        _board_view("07 PCBA Bottom", "PCBA_BOTTOM", False),
        _dimension_view(), _identification_view(), _flex_study(),
    ]
    pivot.rotation_euler = original
    bpy.context.view_layer.update()
    return scenes
