#!/usr/bin/env python3
"""Add a three-support curved dust canopy to the R21 drum concept."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21"):
    sys.path.insert(0, str(path))

from r21_chassis import material, yz_prism  # noqa: E402

SOURCE = HERE.parent / "r21/deepreal-side-supported-drums-r21.blend"
OUTPUT = HERE / "deepreal-curved-drum-canopy-r22.blend"
AXIS_Y, AXIS_Z = -1.5, 20.0
INNER_RADIUS = 13.0
OUTER_RADIUS = 14.0
START_DEG, END_DEG = 75.0, 180.0


def roof_profile():
    angles = [START_DEG + (END_DEG - START_DEG) * i / 64
              for i in range(65)]
    def point(radius, angle):
        theta = math.radians(angle)
        return (AXIS_Y - radius * math.cos(theta),
                AXIS_Z + radius * math.sin(theta))
    return ([point(OUTER_RADIUS, angle) for angle in angles] +
            [point(INNER_RADIUS, angle) for angle in reversed(angles)])


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.name = "DeepReal Curved Drum Canopy Concept R22"
    collection = bpy.data.collections.new("13 — R22 CURVED DUST CANOPY")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    roof_mat = material("R22_Satin_Graphite_Canopy",
                        (.085, .105, .115, 1), .2, .42)
    pieces = []
    profile = roof_profile()
    for label, center_x, width in (
            ("Left_Outer_Crown", -58.3, 2.2),
            ("Face_Roof", -29.35, 55.7),
            ("Center_Crown", 0, 3.0),
            ("Interaction_Roof", 29.35, 55.7),
            ("Right_Outer_Crown", 58.3, 2.2)):
        obj = yz_prism("R22_" + label, profile, center_x, width,
                       roof_mat, collection)
        obj["R22_Role"] = "fixed curved cover, attached to side supports"
        obj["R22_Status"] = (
            "appearance envelope; joints, seals, stiffness, material and "
            "removal sequence unverified")
        pieces.append(obj.name)
    scene["R22_Design_Intent"] = (
        "two curved cover panels over drum tops, joined by center and "
        "outside support crowns; optics exposed at the front")
    scene["R22_Dust_Status"] = (
        "shields falling dust; front slot and seams are not sealed")
    scene["R22_Optical_Clearance_Status"] = (
        "75-degree leading edge leaves nominal 9.5 degrees beyond the "
        "face camera 45-degree-up bore and 20.5-degree vertical half-FOV; "
        "actual lens ray envelope unverified")
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {
        "source": str(SOURCE), "model": str(OUTPUT),
        "canopy_pieces": pieces,
        "inner_radius_mm": INNER_RADIUS,
        "outer_radius_mm": OUTER_RADIUS,
        "cross_section_angles_deg": [START_DEG, END_DEG],
        "shell_radial_clearance_mm": INNER_RADIUS - 12.0,
        "status": "appearance and clearance concept only",
    }
    (HERE / "r22-canopy-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R22 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
