#!/usr/bin/env python3
"""Export provisional internal assemblies for website animation review.

The output is intentionally separate from the public exterior GLB. Its head
boards and many electronic bodies are visual envelopes, not released designs.
"""

import os
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_export_common import export_glb, require_r36_source, stage_meshes, write_manifest
from web_assembly_cables import create_cables
from web_camera_mount import create_camera_mounts, create_optical_supports

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
    "Face_Center_Fed_Motor_Stator_ENV_R21",
    "Interaction_Center_Fed_Motor_Stator_ENV_R21",
    "Face_Motor_Cantilever_R21", "Interaction_Motor_Cantilever_R21",
    "Face_Motor_Pinion_ENV_R21", "Interaction_Motor_Pinion_ENV_R21",
    "Face_Inner_Bearing_Fixed_Race_ENV_R21",
    "Interaction_Inner_Bearing_Fixed_Race_ENV_R21",
    "R34_Face_Outer_Bearing_ENV", "Interaction_Outer_Bearing_ENV_R21",
    "R34_Face_Axial_Sensor_PCB_ENV", "R34_Face_Axial_Sensor_IC_ENV",
    "Interaction_End_Encoder_PCB_ENV_R21",
    "Interaction_End_Encoder_IC_ENV_R21",
)

SHIELDS = ("Shield_Front_Lid", "Shield_Rear_Tray", "Thermal_Spreader")

HEAD_PART_SUFFIXES = (
    "Head_PCBA_Carrier_CONCEPT", "Internal_Optical_Carrier",
    "Head_Flex_Connector_PROXY",
    "IR_Depth_Module_Body", "IR_Depth_Module_Barrel",
    "SL_Projector_Body", "SL_Projector_Emitter", "SL_Projector_DOE",
    "SL_Projector_Barrel_Pinhole", "SL_Projector_Barrel_ProjA",
    "SL_Projector_Barrel_ProjB", "SL_Projector_Bracket",
    "Inner_Bearing_Rotating_Race_ENV_R21",
    "Internal_Ring_Gear_ENV_R21",
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

def groups():
    result = {"main": list(MAIN), "stationary": list(STATIONARY),
              "shields": list(SHIELDS)}
    for head in ("Face", "Interaction"):
        result[head.lower()] = [f"{head}_{suffix}" for suffix in HEAD_PART_SUFFIXES]
        result[head.lower()].extend(EXTRA_HEAD[head])
    return result


def size_web_head_connectors(staged):
    """Place web-only FH26 envelopes below the optical head boards."""
    for obj in staged:
        if obj.name not in {
            "Face_Head_Flex_Connector_PROXY_WEB",
            "Interaction_Head_Flex_Connector_PROXY_WEB",
        }:
            continue
        # Blender local X/Y/Z dimensions become web X/depth/height.
        # Source proxies are 5 x 0.8 x 2 mm; the intended 51-contact body
        # is 16.8 x 1 x 3.2 mm. This remains an unapproved placement.
        for axis, target in (("x", .0168), ("y", .001), ("z", .0032)):
            center = sum(getattr(vertex.co, axis) for vertex in obj.data.vertices) / len(obj.data.vertices)
            coordinates = [getattr(vertex.co, axis) for vertex in obj.data.vertices]
            scale = target / (max(coordinates) - min(coordinates))
            for vertex in obj.data.vertices:
                setattr(vertex.co, axis, center + (getattr(vertex.co, axis) - center) * scale)
        for vertex in obj.data.vertices:
            if obj.name.startswith("Interaction_"):
                # The old outward shift put J1 inside the wide RGB camera.
                # Use the gap between IR and projector, behind their bodies.
                vertex.co.x -= .011
                vertex.co.y += .004
            else:
                vertex.co.y += .0015
        obj.data.update()


def cut_web_proxy(target, frame, limits, label):
    """Apply a review-only rectangular relief in the reference object's frame."""
    (x0, x1), (y0, y1), (z0, z1) = limits
    vertices = [(x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0),
                (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)]
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4),
             (1,2,6,5), (2,3,7,6), (3,0,4,7)]
    mesh = bpy.data.meshes.new(f"WEB_{label}_Cutout_Temp")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    cutter = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(cutter)
    cutter.matrix_world = frame.matrix_world.copy()
    modifier = target.modifiers.new(label + " review relief", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    depsgraph = bpy.context.evaluated_depsgraph_get()
    cut_mesh = bpy.data.meshes.new_from_object(
        target.evaluated_get(depsgraph),
        preserve_all_data_layers=True, depsgraph=depsgraph)
    target.modifiers.remove(modifier)
    bpy.data.objects.remove(cutter, do_unlink=True)
    if not cut_mesh.vertices or not cut_mesh.polygons:
        raise RuntimeError(f"Empty {target.name} after {label} review relief")
    target.data = cut_mesh


def pocket_web_carriers(staged):
    """Cut J1 envelopes into web-only carrier proxies, leaving R36 unchanged."""
    by_name = {obj.name: obj for obj in staged}
    for side in ("Face", "Interaction"):
        connector = by_name[f"{side}_Head_Flex_Connector_PROXY_WEB"]
        carrier = by_name[f"{side}_Internal_Optical_Carrier_WEB"]
        x = [vertex.co.x for vertex in connector.data.vertices]
        z = [vertex.co.z for vertex in connector.data.vertices]
        x0, x1 = min(x) - .0009, max(x) + .0009
        # The film leaves the rear of J1 gradually; keep its first short arc
        # clear of the conceptual carrier instead of clipping the plate.
        z0, z1 = min(z) - .0024, max(z) + .0004
        cut_web_proxy(
            carrier, connector, ((x0, x1), (-.01, .002), (z0, z1)),
            f"{side}_J1",
        )


def relieve_wide_rgb_envelope(staged):
    """Show the wide RGB envelope without the inherited carrier/PCB overlap."""
    by_name = {obj.name: obj for obj in staged}
    camera = (
        by_name["Interaction_RGB_Wide_Assembly_10p8mm_ENVELOPE_R20_WEB"],
        by_name["Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20_WEB"],
    )
    for name in ("Interaction_Internal_Optical_Carrier_WEB",
                 "Interaction_Head_PCBA_Carrier_CONCEPT_WEB"):
        target = by_name[name]
        to_local = target.matrix_world.inverted()
        camera_points = [
            to_local @ part.matrix_world @ vertex.co
            for part in camera for vertex in part.data.vertices
        ]
        target_points = [vertex.co for vertex in target.data.vertices]
        # Open the outer edge of these web-only proxies. This makes the
        # previously documented wide RGB collision visible as a missing
        # mounting region, not as a falsely fitted camera module.
        x0 = min(point.x for point in camera_points) - .0025
        limits = (
            (x0, max(point.x for point in camera_points + target_points) + .001),
            (min(point.y for point in camera_points + target_points) - .001,
             max(point.y for point in camera_points + target_points) + .001),
            (min(point.z for point in camera_points + target_points) - .001,
             max(point.z for point in camera_points + target_points) + .001),
        )
        cut_web_proxy(target, target, limits, "Interaction_Wide_RGB")
        target["Web_Wide_RGB_Status"] = (
            "outer review-only relief; wide RGB mount and common PCB fit unresolved")


def verify_camera_route_separation(staged):
    """Reject camera, J1 and ring-gear crossings in the web rest pose."""
    by_name = {obj.name: obj for obj in staged}
    prefix = "Interaction_"
    ribbon = by_name["WEB_Interaction_Optical_Flex_CONCEPT_WEB"]
    connector = by_name[prefix + "Head_Flex_Connector_PROXY_WEB"]
    camera = (
        by_name[prefix + "RGB_Wide_Assembly_10p8mm_ENVELOPE_R20_WEB"],
        by_name[prefix + "RGB_Wide_Lens_6p95mm_ENVELOPE_R20_WEB"],
    )
    pairs = [
        (ribbon, by_name[prefix + "Internal_Ring_Gear_ENV_R21_WEB"]),
        (ribbon, by_name[prefix + "Head_PCBA_Carrier_CONCEPT_WEB"]),
        (ribbon, by_name[prefix + "Internal_Optical_Carrier_WEB"]),
    ]
    for part in camera:
        pairs.extend(
            (part, other) for other in (
                ribbon, connector,
                by_name[prefix + "Head_PCBA_Carrier_CONCEPT_WEB"],
                by_name[prefix + "Internal_Optical_Carrier_WEB"],
            )
        )
    pairs.extend((connector, by_name[prefix + suffix + "_WEB"])
                 for suffix in ("IR_Depth_Module_Body", "SL_Projector_Body",
                                "SL_Projector_Bracket"))

    def tree(obj):
        return BVHTree.FromPolygons(
            [obj.matrix_world @ vertex.co for vertex in obj.data.vertices],
            [tuple(face.vertices) for face in obj.data.polygons],
            all_triangles=False,
        )

    trees = {obj.name: tree(obj) for pair in pairs for obj in pair}
    for first, second in pairs:
        if trees[first.name].overlap(trees[second.name]):
            raise RuntimeError(
                f"Web rest-pose crossing: {first.name} / {second.name}")


def main():
    source = require_r36_source()
    named_groups = groups()
    concept_cables = create_cables()
    named_groups.update({key: [obj.name for obj in value]
                         for key, value in concept_cables.items()})
    names = [name for group in named_groups.values() for name in group]
    if len(names) != len(set(names)):
        raise RuntimeError("An assembly object belongs to more than one group")
    missing = [name for name in names if name not in bpy.data.objects]
    if missing:
        raise RuntimeError("Missing internal objects: " + ", ".join(missing))
    staged = stage_meshes([bpy.data.objects[name] for name in names],
                          "WEB EXPORT — INTERNAL REVIEW")
    size_web_head_connectors(staged)
    pocket_web_carriers(staged)
    relieve_wide_rgb_envelope(staged)
    mounts, mount_review = create_camera_mounts(staged, cut_web_proxy)
    for mount in mounts.values():
        staged.extend(mount)
    supports, support_review = create_optical_supports(staged, cut_web_proxy)
    for group, support in supports.items():
        staged.extend(support)
        mounts[group].extend(support)
    verify_camera_route_separation(staged)
    export_glb(OUTPUT, staged)
    write_manifest(MANIFEST, source, OUTPUT, {
        "milestone": "internal reveal source inventory",
        "groups": {key: [name + "_WEB" for name in value]
                   + [obj.name for obj in mounts.get(key, [])]
                   for key, value in named_groups.items()},
        "status": "review-only concept; two camera supports/shared board outline, moving cables and electronics unvalidated",
        "wide_rgb_review": mount_review["interaction"],
        "head_mount_review": mount_review,
        "optical_support_review": support_review,
        "common_head_board_review": {
            "status": "shared outline and keepouts only, not an approved common PCB",
            "board_envelope_mm": [47.3, 12, .6],
            "face_rear_offset_mm": 1.72,
            "interaction_rear_offset_mm": 1,
            "shared_projector_bracket_keepout_mm": [[-16.45, -12.95], [-.95, 2.55]],
        },
        "excluded": "native KiCad board import marked PCBA_PublicAllowed=False",
    })


if __name__ == "__main__":
    main()
