#!/usr/bin/env python3
"""Structural checks for the canonical Blender reference model."""

import bpy
from mathutils import Vector


REQUIRED = {
    "enclosure": ("Main_Housing",),
    "sensor drums": ("Face_Sensor_Head", "Interaction_Sensor_Head"),
    "compute": ("Main_PCBA", "NXP_iMX95", "CrossLink_NX_FPGA",
                "LPDDR_1", "LPDDR_2", "eMMC_Storage"),
    "power and drivers": ("PMIC_PF09", "PMIC_PF53", "USB_PD_Controller",
                          "USB_ESD_Protection", "Motor_Driver_A",
                          "Motor_Driver_B", "Projector_Driver_A",
                          "Projector_Driver_B"),
    "shield and thermal": ("EMI_Shield_Can_Lid", "Thermal_Spreader",
                           "Housing_Thermal_Pad"),
    "motion": ("Face_Geared_Motor", "Interaction_Geared_Motor",
               "Face_Ring_Gear", "Interaction_Ring_Gear",
               "Face_Bearing_Inner", "Face_Bearing_Outer",
               "Interaction_Bearing_Inner", "Interaction_Bearing_Outer"),
    "position sensing": ("Face_Encoder_Board", "Interaction_Encoder_Board",
                         "Face_Rotation_Stop", "Interaction_Rotation_Stop"),
    "interconnect": ("Face_RGB_MIPI_Flex", "Face_Depth_MIPI_Flex",
                     "Interaction_Depth_MIPI_Flex",
                     "Interaction_Tracking_MIPI_Flex"),
    "external connector strip": ("Face_Motor_Connector",
                                  "Face_Projector_Connector",
                                  "Camera_Flex_Connector_1",
                                  "Camera_Flex_Connector_2",
                                  "Camera_Flex_Connector_3",
                                  "Camera_Flex_Connector_4",
                                  "Interaction_Projector_Connector",
                                  "Interaction_Motor_Connector"),
    "internal supports": ("PCBA_Standoff_L_B", "PCBA_Standoff_R_T",
                          "Face_Bearing_Carrier",
                          "Interaction_Bearing_Carrier"),
    "other required": ("PDM_MEMS_Microphone", "Case_Open_Tamper_Switch"),
}


def _bounds(name):
    obj = bpy.data.objects[name]
    points = [Vector(vertex.co) for vertex in obj.data.vertices]
    return tuple(min(point[i] for point in points) for i in range(3)), tuple(
        max(point[i] for point in points) for i in range(3))


def _overlap(a_name, b_name):
    a0, a1 = _bounds(a_name)
    b0, b1 = _bounds(b_name)
    return all(min(a1[i], b1[i]) - max(a0[i], b0[i]) > 1e-6
               for i in range(3))


def _inside_xz(inner_name, outer_name):
    inner0, inner1 = _bounds(inner_name)
    outer0, outer1 = _bounds(outer_name)
    return (outer0[0] <= inner0[0] <= inner1[0] <= outer1[0]
            and outer0[2] <= inner0[2] <= inner1[2] <= outer1[2])


def _curve_min_z(name):
    obj = bpy.data.objects[name]
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return min(vertex.co.z for vertex in mesh.vertices)
    finally:
        evaluated.to_mesh_clear()


def _drum_optics_axial_bounds(prefix):
    objects = [obj for obj in bpy.data.objects
               if obj.name.startswith(prefix + "_")
               and obj.type == "MESH"
               and "Drum Optics" in {c.name for c in obj.users_collection}
               and "_Cutter_" not in obj.name
               and not obj.name.endswith("_KeepOut")]
    minima = [_bounds(obj.name)[0][0] for obj in objects]
    maxima = [_bounds(obj.name)[1][0] for obj in objects]
    return min(minima), max(maxima)


def main():
    missing = []
    for subsystem, names in REQUIRED.items():
        absent = [name for name in names if bpy.data.objects.get(name) is None]
        if absent:
            missing.append("{}: {}".format(subsystem, ", ".join(absent)))
        else:
            print("ok: {:<20} {} named objects".format(subsystem, len(names)))

    legacy = [obj.name for obj in bpy.data.objects
              if obj.name.startswith(("Current_", "Compact_"))]
    if legacy:
        missing.append("legacy comparison objects remain: " + ", ".join(legacy))

    can_parts = [obj for obj in bpy.data.objects
                 if obj.name.startswith("EMI_Shield_Can_")]
    if len(can_parts) != 5:
        missing.append("EMI shield can must have one lid and four walls")
    else:
        print("ok: one five-piece board-mounted EMI shield can")

    for motor in ("Face_Geared_Motor", "Interaction_Geared_Motor"):
        if _overlap("Main_PCBA_Populated_Keepout", motor):
            missing.append("electronics keep-out overlaps " + motor)
    print("ok: electronics keep-out clears both geared motors")

    gear_clearance = 0.0005
    face_optics = _drum_optics_axial_bounds("Face_Drum")
    face_gear = _bounds("Face_Ring_Gear")
    face_gap = face_optics[0] - face_gear[1][0]
    interaction_optics = _drum_optics_axial_bounds("Interaction_Drum")
    interaction_gear = _bounds("Interaction_Ring_Gear")
    interaction_gap = interaction_gear[0][0] - interaction_optics[1]
    if face_gap < gear_clearance:
        missing.append("Face ring gear clearance to optics is {:.2f} mm".format(
            face_gap * 1000.0))
    if interaction_gap < gear_clearance:
        missing.append(
            "Interaction ring gear clearance to optics is {:.2f} mm".format(
                interaction_gap * 1000.0))
    print("ok: ring gears clear all drum optics by at least 0.5 mm")

    shielded = (
        "NXP_iMX95", "CrossLink_NX_FPGA", "LPDDR_1", "LPDDR_2",
        "eMMC_Storage", "PMIC_PF09", "PMIC_PF53", "USB_PD_Controller",
        "USB_ESD_Protection", "Motor_Driver_A", "Motor_Driver_B",
        "Projector_Driver_A", "Projector_Driver_B",
    )
    lid_bounds = _bounds("EMI_Shield_Can_Lid")
    for component in shielded:
        if not _inside_xz(component, "EMI_Shield_Can_Lid"):
            missing.append(component + " falls outside EMI shield can footprint")
        component_bounds = _bounds(component)
        clearance = component_bounds[0][1] - lid_bounds[1][1]
        if clearance < 0.0005:
            missing.append(component + " lacks clearance beneath shield lid")
    print("ok: every populated internal IC sits beneath the shield can")

    connectors = REQUIRED["external connector strip"]
    for connector in connectors:
        for can_part in can_parts:
            if _overlap(connector, can_part.name):
                missing.append(connector + " intersects " + can_part.name)
    print("ok: all eight cable connectors remain outside the shield perimeter")

    harnesses = REQUIRED["interconnect"] + (
        "Face_Projector_Power", "Interaction_Projector_Power",
        "Face_Motor_Encoder_Harness", "Interaction_Motor_Encoder_Harness",
    )
    shield_top = lid_bounds[1][2]
    for harness in harnesses:
        if _curve_min_z(harness) <= shield_top + 0.0005:
            missing.append(harness + " crosses the shielded region")
    print("ok: external harness centerlines stay above the shield boundary")

    presentation_scenes = (
        "00 Four View Overview",
        "01 Fully Assembled", "02 Housing Removed",
        "03 Functional Core", "04 Electronics Exploded",
    )
    for scene_name in presentation_scenes:
        scene = bpy.data.scenes.get(scene_name)
        if scene is None:
            missing.append("missing presentation scene: " + scene_name)
            continue
        linked = [obj for obj in scene.objects
                  if obj.get("Linked_Source_Object")]
        if not linked:
            missing.append(scene_name + " has no linked presentation objects")
        for clone in linked:
            source = bpy.data.objects.get(clone["Linked_Source_Object"])
            if source is None or clone.data is not source.data:
                missing.append(clone.name + " is not linked to source geometry")
    print("ok: overview and four detail scenes share canonical datablocks")

    housing_only = (
        "Main_Housing_USB_Back", "Main_Housing_USB_Cutter",
        "Main_Housing_USB_Shell", "Main_Housing_USB_Tongue",
        "USB_Cable", "USB_Plug_A_Overmold", "USB_Plug_A_Shell",
        "USB_Plug_B_Overmold", "USB_Plug_B_Shell",
    )
    for scene_name in ("02 Housing Removed", "03 Functional Core"):
        scene = bpy.data.scenes.get(scene_name)
        if scene is None:
            continue
        linked_sources = {obj.get("Linked_Source_Object")
                          for obj in scene.objects}
        for object_name in housing_only:
            if object_name in linked_sources:
                missing.append(scene_name + " retains housing-mounted "
                               + object_name)
    print("ok: housing-off views omit the receptacle and external USB cable")

    if missing:
        raise RuntimeError("\n".join(missing))
    print("PASS: canonical Blender model contains every required subsystem")


if __name__ == "__main__":
    main()
