#!/usr/bin/env python3
"""Structural, routing, and clearance checks for the DeepReal model."""

import math

import bpy
from mathutils.bvhtree import BVHTree


REQUIRED = {
    "enclosure": ("Main_Housing",),
    "sensor drums": ("Face_Sensor_Head", "Interaction_Sensor_Head"),
    "compute": (
        "Main_PCBA", "NXP_iMX95", "Face_CrossLink_NX",
        "Interaction_CrossLink_NX", "LPDDR4X_4GB", "eMMC_32GB",
        "Board_ID_EEPROM",
    ),
    "power and drivers": (
        "PMIC_PF09", "PF53_SOC", "PF53_ARM",
        "USB_PD_Controller", "System_5V_Buck", "Motor_6V_Buck", "VBUS_eFuse",
        "USB_SS_Mux", "USB_C_Receptacle",
        "Face_Motor_Driver", "Interaction_Motor_Driver",
    ),
    "electronics shield enclosure": (
        "Shield_Rear_Tray", "Shield_Front_Lid",
        "PCB_Ground_Ring_Left", "PCB_Ground_Ring_Right",
        "PCB_Ground_Ring_Top", "PCB_Ground_Ring_Apron",
        "Shield_Chassis_Bond_Left", "Shield_Chassis_Bond_Center",
        "Shield_Chassis_Bond_Right",
    ),
    "thermal path": ("Thermal_Spreader", "Housing_Thermal_Pad"),
    "motion": (
        "Face_Geared_Motor", "Interaction_Geared_Motor",
        "Face_Ring_Gear", "Interaction_Ring_Gear",
        "Face_Bearing_Inner", "Face_Bearing_Outer",
        "Interaction_Bearing_Inner", "Interaction_Bearing_Outer",
    ),
    "position sensing": (
        "Face_Encoder_Board", "Interaction_Encoder_Board",
        "Face_Rotation_Stop", "Interaction_Rotation_Stop",
    ),
    "camera data lanes": (
        "Face_Data_Lane", "Interaction_Data_Lane",
        "Face_Optical_Head_Flex", "Interaction_Optical_Head_Flex",
    ),
    "power and motion lanes": (
        "Face_Motor_Encoder_Harness", "Interaction_Motor_Encoder_Harness",
    ),
    "connector apron": (
        "Face_Connector_Bank", "Auxiliary_Connector_Bank",
        "Interaction_Connector_Bank",
        "Face_Motor_Encoder", "Face_Optical_Head_Connector",
        "Interaction_Optical_Head_Connector",
        "Interaction_Motor_Encoder",
    ),
    "grounded cable supports": (
        "Face_Data_Lane_Grounded_Clip",
        "Face_Power_Motion_Lane_Grounded_Clip",
        "Interaction_Data_Lane_Grounded_Clip",
        "Interaction_Power_Motion_Lane_Grounded_Clip",
        "Face_Lane_Grounded_Divider",
        "Interaction_Lane_Grounded_Divider",
        "Face_Boundary_Ground_Clamp",
        "Interaction_Boundary_Ground_Clamp",
    ),
    "strain relief": (
        "Face_Drum_Data_Strain_Relief",
        "Face_Drum_Power_Strain_Relief",
        "Face_PCBA_Data_Strain_Relief",
        "Face_PCBA_Power_Strain_Relief",
        "Interaction_Drum_Data_Strain_Relief",
        "Interaction_Drum_Power_Strain_Relief",
        "Interaction_PCBA_Data_Strain_Relief",
        "Interaction_PCBA_Power_Strain_Relief",
    ),
    "internal supports": (
        "PCBA_Standoff_L_B", "PCBA_Standoff_L_T",
        "PCBA_Standoff_R_B", "PCBA_Standoff_R_T",
        "PCBA_Fastener_L_B", "PCBA_Fastener_L_T",
        "PCBA_Fastener_R_B", "PCBA_Fastener_R_T",
        "Face_Bearing_Carrier", "Interaction_Bearing_Carrier",
    ),
    "other required": ("PDM_MEMS_Microphone", "Case_Open_Tamper_Switch"),
}

SHIELD_PARTS = ("Shield_Rear_Tray", "Shield_Front_Lid")

PROTECTED_COMPONENTS = (
    "NXP_iMX95", "Face_CrossLink_NX", "Interaction_CrossLink_NX",
    "LPDDR4X_4GB", "eMMC_32GB", "PMIC_PF09", "PF53_SOC", "PF53_ARM",
    "USB_PD_Controller", "System_5V_Buck", "Motor_6V_Buck", "VBUS_eFuse",
    "USB_SS_Mux", "USB_C_Receptacle", "Face_Motor_Driver",
    "Interaction_Motor_Driver", "Board_ID_EEPROM",
)

DRUM_CONNECTORS = (
    "Face_Motor_Encoder", "Face_Optical_Head_Connector",
    "Interaction_Optical_Head_Connector", "Interaction_Motor_Encoder",
)

CABLES = (
    "Face_Optical_Head_Flex", "Interaction_Optical_Head_Flex",
    "Face_Motor_Encoder_Harness", "Interaction_Motor_Encoder_Harness",
)

CABLE_CONNECTORS = {
    "Face_Optical_Head_Flex": "Face_Optical_Head_Connector",
    "Interaction_Optical_Head_Flex": "Interaction_Optical_Head_Connector",
    "Face_Motor_Encoder_Harness": "Face_Motor_Encoder",
    "Interaction_Motor_Encoder_Harness": "Interaction_Motor_Encoder",
}

CABLE_SUPPORTS = tuple(
    name for group in ("grounded cable supports", "strain relief")
    for name in REQUIRED[group]
    if "_Divider" not in name
)

CHAMBER_BOUNDS = (
    (-0.04555, 0.012025, -0.02045),
    (0.04555, 0.018825, 0.00305),
)


def _mesh_data(name):
    obj = bpy.data.objects[name]
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        vertices = [evaluated.matrix_world @ vertex.co
                    for vertex in mesh.vertices]
        polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
        return vertices, polygons
    finally:
        evaluated.to_mesh_clear()


def _bounds(name):
    vertices, _polygons = _mesh_data(name)
    return (
        tuple(min(vertex[index] for vertex in vertices) for index in range(3)),
        tuple(max(vertex[index] for vertex in vertices) for index in range(3)),
    )


def _tree(name):
    vertices, polygons = _mesh_data(name)
    return BVHTree.FromPolygons(
        vertices, polygons, all_triangles=False) if polygons else None


def _intersects(a_name, b_name):
    a_tree = _tree(a_name)
    b_tree = _tree(b_name)
    return bool(a_tree and b_tree and a_tree.overlap(b_tree))


def _aabb_overlap(a_name, b_name):
    a0, a1 = _bounds(a_name)
    b0, b1 = _bounds(b_name)
    return all(min(a1[index], b1[index])
               - max(a0[index], b0[index]) >= 0.0
               for index in range(3))


def _inside(inner, outer, clearance=0.0):
    inner0, inner1 = inner
    outer0, outer1 = outer
    return all(
        outer0[index] + clearance <= inner0[index]
        and inner1[index] <= outer1[index] - clearance
        for index in range(3)
    )


def _fail_if_intersects(failures, a_name, b_name, category):
    if _intersects(a_name, b_name):
        failures.append(
            "{}: {} intersects {}".format(category, a_name, b_name))


def _require_channel(failures, cable_name, support_name):
    if not _aabb_overlap(cable_name, support_name):
        failures.append(
            "unsupported cable: {} misses {}".format(
                cable_name, support_name))
    elif _intersects(cable_name, support_name):
        failures.append(
            "support collision: {} penetrates solid {}".format(
                cable_name, support_name))


def _drum_optics_axial_bounds(prefix):
    objects = [
        obj for obj in bpy.data.objects
        if obj.name.startswith(prefix + "_")
        and obj.type == "MESH"
        and "Drum Optics" in {collection.name
                              for collection in obj.users_collection}
        and "_Cutter_" not in obj.name
        and not obj.name.endswith("_KeepOut")
    ]
    minima = [_bounds(obj.name)[0][0] for obj in objects]
    maxima = [_bounds(obj.name)[1][0] for obj in objects]
    return min(minima), max(maxima)


def _pivot_descendants(pivot):
    descendants = []
    for obj in bpy.data.objects:
        parent = obj.parent
        while parent:
            if parent is pivot:
                if (obj.type in {"MESH", "CURVE"} and not obj.hide_render
                        and "_Cutter_" not in obj.name
                        and not obj.name.endswith("_KeepOut")):
                    descendants.append(obj)
                break
            parent = parent.parent
    return descendants


def _validate_drum_sweep(failures):
    obstacles = SHIELD_PARTS
    angles = (-80.0, -40.0, 0.0, 40.0, 80.0)
    for side in ("Face", "Interaction"):
        pivot = bpy.data.objects[side + "_Drum_Optics_Pivot"]
        original = pivot.rotation_euler.copy()
        moving = _pivot_descendants(pivot)
        try:
            for angle in angles:
                pivot.rotation_euler.x = math.radians(angle)
                bpy.context.view_layer.update()
                for obj in moving:
                    for obstacle in obstacles:
                        if _intersects(obj.name, obstacle):
                            failures.append(
                                "drum sweep collision at {:+.0f} deg: {} "
                                "intersects {}".format(
                                    angle, obj.name, obstacle))
        finally:
            pivot.rotation_euler = original
            bpy.context.view_layer.update()


def _validate_presentations(failures):
    scene_names = (
        "00 Four View Overview", "01 Fully Assembled",
        "02 Housing Removed", "03 Functional Core",
        "04 Electronics Exploded", "05 Shield Cutaway",
    )
    for scene_name in scene_names:
        scene = bpy.data.scenes.get(scene_name)
        if scene is None:
            failures.append("missing presentation scene: " + scene_name)
            continue
        linked = [
            obj for obj in scene.objects if obj.get("Linked_Source_Object")
        ]
        if len(linked) < 20:
            failures.append(
                "{} contains only {} linked source objects".format(
                    scene_name, len(linked)))
        for clone in linked:
            source = bpy.data.objects.get(clone["Linked_Source_Object"])
            if source is None or clone.data is not source.data:
                failures.append(
                    "{} is not linked to canonical geometry".format(
                        clone.name))

    cutaway = bpy.data.scenes.get("05 Shield Cutaway")
    if cutaway:
        sources = {
            obj.get("Linked_Source_Object") for obj in cutaway.objects
        }
        if "Shield_Front_Lid" in sources:
            failures.append("shield cutaway still contains the front lid")
        for required in (
                "Shield_Rear_Tray", "Main_PCBA",
                "Face_Connector_Bank", "Interaction_Connector_Bank"):
            if required not in sources:
                failures.append("shield cutaway omits " + required)


def main():
    failures = []
    for subsystem, names in REQUIRED.items():
        absent = [name for name in names if bpy.data.objects.get(name) is None]
        if absent:
            failures.append(
                "missing {}: {}".format(subsystem, ", ".join(absent)))

    if failures:
        raise RuntimeError("\n".join(failures))

    source_scene = bpy.data.scenes.get("SOURCE - Canonical Assembly")
    if source_scene and bpy.context.window:
        bpy.context.window.scene = source_scene
    product_pivot = bpy.data.objects.get("Lid_Pivot")
    original_product_rotation = (
        product_pivot.rotation_euler.copy() if product_pivot else None)
    if product_pivot:
        product_pivot.rotation_euler = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    try:
        forbidden_prefixes = (
            "Current_", "Compact_", "EMI_Shield_Can_",
            "Camera_Flex_Connector_", "Shield_Wall_",
            "Shield_Rear_Base",
        )
        legacy = [
            obj.name for obj in bpy.data.objects
            if obj.name.startswith(forbidden_prefixes)
        ]
        if legacy:
            failures.append(
                "legacy geometry remains: " + ", ".join(legacy))

        tray = bpy.data.objects["Shield_Rear_Tray"]
        if "left, right, top" not in tray.get("Integrated_Walls", ""):
            failures.append(
                "shield tray does not identify integrated perimeter walls")

        for component in PROTECTED_COMPONENTS:
            if not _inside(_bounds(component), CHAMBER_BOUNDS, 0.00035):
                failures.append(
                    "{} lacks 0.35 mm shield clearance".format(component))

        for shield in SHIELD_PARTS:
            _fail_if_intersects(
                failures, "Main_PCBA", shield, "PCB/shield collision")
            _fail_if_intersects(
                failures, shield, "Main_Housing",
                "housing-envelope collision")

        board_bounds = _bounds("Main_PCBA")
        if (board_bounds[0][0] < CHAMBER_BOUNDS[0][0]
                or board_bounds[1][0] > CHAMBER_BOUNDS[1][0]
                or board_bounds[1][2] > CHAMBER_BOUNDS[1][2]):
            failures.append(
                "shield does not cover the PCB top and side edges")

        apron_top = CHAMBER_BOUNDS[0][2]
        for connector in DRUM_CONNECTORS:
            connector_bounds = _bounds(connector)
            if connector_bounds[1][2] >= apron_top - 0.0005:
                failures.append(
                    "{} is not below the shield boundary".format(connector))
            for shield in SHIELD_PARTS:
                _fail_if_intersects(
                    failures, connector, shield,
                    "connector/shield collision")

        face_connectors = DRUM_CONNECTORS[:2]
        interaction_connectors = DRUM_CONNECTORS[2:]
        if any(_bounds(name)[1][0] >= 0.0 for name in face_connectors):
            failures.append("face connector bank crosses product center")
        if any(_bounds(name)[0][0] <= 0.0
               for name in interaction_connectors):
            failures.append(
                "interaction connector bank crosses product center")

        for index, cable in enumerate(CABLES):
            if bpy.data.objects[cable].get("Minimum_Bend_Radius_mm", 0) < 3.0:
                failures.append(
                    "{} lacks the 3 mm bend-radius contract".format(cable))
            expected_side = (
                "Face_" if cable.startswith("Face_") else "Interaction_")
            if not bpy.data.objects[cable].get(
                    "Cable_Lane", "").startswith(expected_side):
                failures.append(
                    "{} lacks correct side-lane metadata".format(cable))
            for other in CABLES[index + 1:]:
                _fail_if_intersects(
                    failures, cable, other, "cable/cable collision")
            for obstacle in (
                    "Main_Housing", "Shield_Rear_Tray",
                    "Shield_Front_Lid", "Face_Ring_Gear",
                    "Interaction_Ring_Gear"):
                _fail_if_intersects(
                    failures, cable, obstacle, "cable/rigid collision")
            connector = CABLE_CONNECTORS[cable]
            if not _intersects(cable, connector):
                failures.append(
                    "unterminated cable: {} misses {}".format(
                        cable, connector))

        for side in ("Face", "Interaction"):
            for cable, channel in (
                    (side + "_Optical_Head_Flex", "Data"),
                    (side + "_Motor_Encoder_Harness", "Power")):
                lane_name = "Power_Motion" if channel == "Power" else "Data"
                suffixes = (
                    lane_name + "_Lane_Grounded_Clip",
                    "Boundary_Ground_Clamp",
                    "Drum_" + channel + "_Strain_Relief",
                    "PCBA_" + channel + "_Strain_Relief",
                )
                for suffix in suffixes:
                    _require_channel(failures, cable, side + "_" + suffix)

        for x_label in ("L", "R"):
            for z_label in ("B", "T"):
                standoff = "PCBA_Standoff_{}_{}".format(x_label, z_label)
                fastener = "PCBA_Fastener_{}_{}".format(x_label, z_label)
                _fail_if_intersects(
                    failures, standoff, "Shield_Rear_Tray",
                    "mounting-hole collision")
                _fail_if_intersects(
                    failures, fastener, "Main_PCBA",
                    "fastener/PCB collision")
                if not _aabb_overlap(standoff, "Main_PCBA"):
                    failures.append(
                        "{} does not seat against the PCB".format(standoff))
                if not _aabb_overlap(fastener, "Main_PCBA"):
                    failures.append(
                        "{} does not seat against the PCB".format(fastener))

        if not _intersects("Shield_Rear_Tray", "Thermal_Spreader"):
            failures.append(
                "missing thermal contact: tray to thermal spreader")
        if not _intersects("Thermal_Spreader", "Housing_Thermal_Pad"):
            failures.append(
                "missing thermal contact: spreader to housing pad")
        if not _intersects("Housing_Thermal_Pad", "Main_Housing"):
            failures.append(
                "missing thermal contact: housing pad to housing")

        gear_clearance = 0.0005
        face_optics = _drum_optics_axial_bounds("Face_Drum")
        face_gear = _bounds("Face_Ring_Gear")
        face_gap = face_optics[0] - face_gear[1][0]
        interaction_optics = _drum_optics_axial_bounds("Interaction_Drum")
        interaction_gear = _bounds("Interaction_Ring_Gear")
        interaction_gap = (
            interaction_gear[0][0] - interaction_optics[1])
        if face_gap < gear_clearance:
            failures.append(
                "Face ring gear clearance is {:.2f} mm".format(
                    face_gap * 1000.0))
        if interaction_gap < gear_clearance:
            failures.append(
                "Interaction ring gear clearance is {:.2f} mm".format(
                    interaction_gap * 1000.0))

        _validate_drum_sweep(failures)
        _validate_presentations(failures)
    finally:
        if product_pivot and original_product_rotation is not None:
            product_pivot.rotation_euler = original_product_rotation
            bpy.context.view_layer.update()

    if failures:
        raise RuntimeError("\n".join(failures))
    print(
        "PASS: tray/lid shielding, routed cables, fitted supports, "
        "thermal contacts, and sampled drum travel are collision-free")


if __name__ == "__main__":
    main()
