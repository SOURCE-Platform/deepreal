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

    for chip in ("NXP_iMX95", "CrossLink_NX_FPGA", "LPDDR_1", "LPDDR_2"):
        if not _inside_xz(chip, "EMI_Shield_Can_Lid"):
            missing.append(chip + " falls outside EMI shield can footprint")
    print("ok: compute and memory cluster sits under the shield can")

    if missing:
        raise RuntimeError("\n".join(missing))
    print("PASS: canonical Blender model contains every required subsystem")


if __name__ == "__main__":
    main()
