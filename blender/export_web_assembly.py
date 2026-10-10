#!/usr/bin/env python3
"""Export provisional internal assemblies for website animation review.

The output is intentionally separate from the public exterior GLB. Its head
boards and many electronic bodies are visual envelopes, not released designs.
"""

import os
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_export_common import export_glb, require_r36_source, stage_meshes, write_manifest

OUTPUT = Path(os.environ.get(
    "DEEPREAL_WEB_ASSEMBLY_OUT",
    str(Path(__file__).resolve().parent / "review-output/web/deepreal-assembly-review.glb"),
))
MANIFEST = OUTPUT.with_name("deepreal-assembly-review-manifest.json")

MAIN = (
    "Main_PCBA_Near_Full_Height_Right_Wing_PROPOSAL",
    "NXP_iMX95", "LPDDR4X_4GB", "eMMC_32GB",
    "Face_CrossLink_NX", "Interaction_CrossLink_NX",
    "PMIC_PF09", "PF53_ARM", "PF53_SOC",
    "System_5V_Buck", "Motor_6V_Buck", "USB_PD_Controller",
    "USB_SS_Mux", "USB_SS_ESD", "USB2_ESD", "VBUS_eFuse", "VBUS_TVS",
    "Sensor_Clock_Buffer", "PDM_MEMS_Microphone", "Board_ID_EEPROM",
    "Main_Board_Temperature", "Face_Motor_Driver", "Interaction_Motor_Driver",
    "J2_Face_Optical_Head_Connector_ENVELOPE",
    "J3_Interaction_Optical_Head_Connector_ENVELOPE",
    "J4_Face_Motor_Encoder_Connector_PROXY",
    "J5_Interaction_Motor_Encoder_Connector_PROXY",
)

STATIONARY = (
    "Shield_Front_Lid", "Shield_Rear_Tray", "Thermal_Spreader",
    "Face_Center_Fed_Motor_Stator_ENV_R21",
    "Interaction_Center_Fed_Motor_Stator_ENV_R21",
    "Face_Motor_Cantilever_R21", "Interaction_Motor_Cantilever_R21",
    "Face_Inner_Bearing_Fixed_Race_ENV_R21",
    "Interaction_Inner_Bearing_Fixed_Race_ENV_R21",
    "R34_Face_Outer_Bearing_ENV", "Interaction_Outer_Bearing_ENV_R21",
    "R34_Face_Axial_Sensor_PCB_ENV", "R34_Face_Axial_Sensor_IC_ENV",
    "Interaction_End_Encoder_PCB_ENV_R21",
    "Interaction_End_Encoder_IC_ENV_R21",
)

HEAD_PART_SUFFIXES = (
    "Head_PCBA_Carrier_CONCEPT", "Internal_Optical_Carrier",
    "Head_Flex_Connector_PROXY",
    "IR_Depth_Module_Body", "IR_Depth_Module_Barrel",
    "SL_Projector_Body", "SL_Projector_Emitter", "SL_Projector_DOE",
    "SL_Projector_Barrel_Pinhole", "SL_Projector_Barrel_ProjA",
    "SL_Projector_Barrel_ProjB", "SL_Projector_Bracket",
    "Inner_Bearing_Rotating_Race_ENV_R21",
    "Internal_Ring_Gear_ENV_R21", "Motor_Pinion_ENV_R21",
    "Open_Inner_End_Ring_R21", "Flat_Outer_End_R21",
)

EXTRA_HEAD = {
    "Face": ("R34_Face_Axial_Magnet_ENV", "R35_Face_Outer_Hub_ENV",
             "Face_RGB_Module_Body", "Face_RGB_Module_Barrel"),
    "Interaction": ("Interaction_End_Encoder_Magnet_R21",
                    "Interaction_Outer_Rotating_Hub_R21",
                    "Interaction_RGB_Wide_Assembly_10p8mm_ENVELOPE_R20",
                    "Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20"),
}

# These are inherited visual cable proxies. The face strip has no fixed end;
# neither drum has a verified dynamic cable route at the requested travel.
PARTIAL_CABLES = (
    "R36_Face_Full_Width_Straight_Exit_ENV",
    "Interaction_Moving_Head_Flex_PROXY_R21",
    "Interaction_Fixed_Harness_PROXY_R21",
)


def groups():
    result = {"main": list(MAIN), "stationary": list(STATIONARY)}
    for head in ("Face", "Interaction"):
        result[head.lower()] = [f"{head}_{suffix}" for suffix in HEAD_PART_SUFFIXES]
        result[head.lower()].extend(EXTRA_HEAD[head])
    result["partial_cables"] = list(PARTIAL_CABLES)
    return result


def main():
    source = require_r36_source()
    named_groups = groups()
    names = [name for group in named_groups.values() for name in group]
    if len(names) != len(set(names)):
        raise RuntimeError("An assembly object belongs to more than one group")
    missing = [name for name in names if name not in bpy.data.objects]
    if missing:
        raise RuntimeError("Missing internal objects: " + ", ".join(missing))
    staged = stage_meshes([bpy.data.objects[name] for name in names],
                          "WEB EXPORT — INTERNAL REVIEW")
    export_glb(OUTPUT, staged)
    write_manifest(MANIFEST, source, OUTPUT, {
        "milestone": "internal reveal source inventory",
        "groups": {key: [name + "_WEB" for name in value]
                   for key, value in named_groups.items()},
        "status": "review-only concept; moving cable paths and head boards incomplete",
        "excluded": "native KiCad board import marked PCBA_PublicAllowed=False",
    })


if __name__ == "__main__":
    main()
