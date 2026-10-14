#!/usr/bin/env python3
"""Measure current proxy endpoints and screen reserved space without saving CAD.

Run with R36 loaded, then pass -- --output /absolute/new-report.json.
The output is exclusive: no prior report, source, GLB or gate is overwritten.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from face_housed_flex_geometry import (  # noqa: E402
    radial_distance,
    return_space_screen,
    ribbon_corner_radius,
    rotate_x,
)
from web_export_common import require_r36_source  # noqa: E402


def world_points_mm(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return [tuple(float(c) * 1000 for c in evaluated.matrix_world @ vertex.co)
                for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def bounds(points):
    return [[min(point[axis] for point in points), max(point[axis] for point in points)]
            for axis in range(3)]


def section_frames(obj):
    """Recover ribbon sections by UV distance, not glTF's reordered vertices."""
    uv = obj.data.uv_layers.active
    if uv is None:
        raise ValueError("The installed conceptual flex must retain section UVs")
    grouped = {}
    for loop in obj.data.loops:
        coordinate = obj.matrix_world @ obj.data.vertices[loop.vertex_index].co
        point = tuple(round(float(c) * 1000, 7) for c in coordinate)
        distance = round(float(uv.data[loop.index].uv.y), 7)
        grouped.setdefault(distance, set()).add(point)
    sections = []
    for distance, corners in sorted(grouped.items()):
        if len(corners) != 4:
            raise ValueError(f"Expected four unique section corners, got {len(corners)}")
        center = tuple(sum(point[axis] for point in corners) / 4 for axis in range(3))
        # The longest edge is the displayed width, independent of UV u seams.
        edges = [(math.dist(a, b), a, b) for a in corners for b in corners if a != b]
        _, a, b = max(edges)
        direction = Vector(b) - Vector(a)
        # The long diagonal includes film thickness, so report width separately.
        sections.append({"uv_distance": distance, "center_mm": center,
                         "corner_bounds_mm": bounds(corners),
                         "long_diagonal_unit": list(direction.normalized())})
    return sections


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args(args).output
    if not output.is_absolute() or output.exists():
        raise ValueError("Output must be an absolute, new path")
    source = require_r36_source()
    asset = ROOT / "blender/review-output/web/deepreal-assembly-review.glb"
    manifest_path = asset.with_name("deepreal-assembly-review-manifest.json")
    manifest = json.loads(manifest_path.read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest["source_sha256"]
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == manifest["asset_sha256"]
    pivot = tuple(float(c) * 1000 for c in
                  bpy.data.objects["Face_Rotating_Drum_Pivot_R15"].matrix_world.translation)
    source_names = (
        "R36_Face_Full_Width_Straight_Exit_ENV",
        "R36_Face_Fixed_Bearing_Axial_Neck_ENV",
        "R36_Face_Inner_Race_Rear_Side_Web_ENV",
        "Face_Open_Inner_End_Ring_R21",
    )
    source_points = {name: world_points_mm(bpy.data.objects[name]) for name in source_names}
    source_bounds = {name: bounds(points) for name, points in source_points.items()}
    neck_radii = [radial_distance(p, pivot)
                  for p in source_points["R36_Face_Fixed_Bearing_Axial_Neck_ENV"]]
    lip_radii = [radial_distance(p, pivot)
                 for p in source_points["Face_Open_Inner_End_Ring_R21"]]
    prior = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(asset))
    imported = {o.name: o for o in set(bpy.data.objects) - prior if o.type == "MESH"}
    names = (
        "Face_Head_Flex_Connector_PROXY_WEB",
        "J2_Face_Optical_Head_Connector_ENVELOPE_WEB",
        "Face_Head_PCBA_Carrier_CONCEPT_WEB",
        "Face_Internal_Optical_Carrier_WEB",
        "WEB_Face_Optical_Flex_CONCEPT_WEB",
    )
    installed_bounds = {name: bounds(world_points_mm(imported[name])) for name in names}
    sections = section_frames(imported["WEB_Face_Optical_Flex_CONCEPT_WEB"])
    expected_start = (-33, -1.65, 20)
    if math.dist(sections[-1]["center_mm"], expected_start) < math.dist(
        sections[0]["center_mm"], expected_start
    ):
        sections.reverse()
    entry, terminal = sections[0], sections[-1]
    assert math.dist(entry["center_mm"], expected_start) < .001, entry
    width_axis = Vector(entry["long_diagonal_unit"])
    # Ignore the film contribution when classifying the major width axis.
    assert abs(width_axis.x) > .99, width_axis
    entry_radius = radial_distance(entry["center_mm"], pivot)
    poses = {str(angle): list(rotate_x(entry["center_mm"], pivot, angle))
             for angle in range(-45, 46, 5)}
    historical = ROOT / "blender/refinements/r37/r37-volume-check.json"
    reservation = json.loads(historical.read_text())
    chamber = reservation["volumes"]["R37_Rear_Service_Chamber_RESERVATION"]
    neck_bore = min(neck_radii)
    strip = source_bounds["R36_Face_Full_Width_Straight_Exit_ENV"]
    report = {
        "schema": "deepreal.face-housed-flex-screen.v1",
        "status": "CONDITIONAL_SPACE_SCREEN_ROUTE_BLOCKED",
        "units": "mm",
        "source_blend": str(source.relative_to(ROOT)),
        "source_sha256": manifest["source_sha256"],
        "installed_assembly": str(asset.relative_to(ROOT)),
        "installed_assembly_sha256": manifest["asset_sha256"],
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "historical_reservation_source": str(historical.relative_to(ROOT)),
        "historical_reservation_sha256": hashlib.sha256(historical.read_bytes()).hexdigest(),
        "reference": {
            "drum": "Face",
            "pivot_world_mm": pivot,
            "rotation_axis_world": [1, 0, 0],
            "provisional_travel_degrees": [-45, 45],
            "sample_step_degrees": 5,
        },
        "installed_proxy_bounds_xyz_mm": installed_bounds,
        "source_exit_and_support_bounds_xyz_mm": source_bounds,
        "endpoints": {
            "moving_web_entry_world_mm": entry["center_mm"],
            "stationary_web_main_J2_landing_world_mm": terminal["center_mm"],
            "entry_width_major_axis": "X",
            "entry_radius_about_drum_axis_mm": entry_radius,
            "entry_at_sampled_poses_world_mm": poses,
            "entry_extreme_to_extreme_displacement_mm": math.dist(poses["-45"], poses["45"]),
            "entry_orientation_change_degrees": 90,
            "gap_along_x_to_historical_straight_segment_mm":
                strip[0][0] - entry["center_mm"][0],
            "historical_straight_segment_width_major_axis": "Z at zero pose",
            "mechanical_strain_relief_and_contact_datum_verified": False,
        },
        "nominal_bearing_screen": {
            "measured_axial_neck_inner_radius_mm": neck_bore,
            "measured_axial_neck_outer_radius_mm": max(neck_radii),
            "measured_rotating_lip_inner_radius_mm": min(lip_radii),
            "neck_to_lip_nominal_radial_space_mm": min(lip_radii) - max(neck_radii),
            "assumed_rectangular_15p6_by_0p2_mm_corner_radius_mm": ribbon_corner_radius(15.6, .2),
            "bore_minus_rectangular_strip_corner_radius_mm":
                neck_bore - ribbon_corner_radius(15.6, .2),
            "tolerance_or_dynamic_clearance_approval": False,
        },
        "conditional_architecture": {
            "candidate": "one continuous flex: moving head lead, planar rolling return, stationary strain relief, fixed tail to main J2",
            "return_width_axis": "X",
            "return_bending_plane": "YZ, through the thin dimension",
            "bearing_transition": "Unrouted; the R36 axial strip and current J1 do not share a developed cable frame",
            "moving_and_stationary_anchor_hardware": None,
            "developed_constant_length_shape": None,
            "continuous_motion_collision_result": None,
        },
        "historical_rear_reservation": {
            "bounds_xyz_mm": chamber["bounds_xyz_mm"],
            "sampled_points_inside_visual_enclosure_of_27":
                chamber["sampled_inside_points_of_27"]["R30_One_Piece_Enclosure"],
            "outside_visual_shell_points_mm": reservation["chamber_points_outside_visual_shell_mm"],
            "divider_passage_rear_web_triangle_contacts":
                reservation["volumes"]["R37_Center_Divider_Passage_RESERVATION"]["triangle_hits"]
                ["R36_Face_Inner_Race_Rear_Side_Web_ENV"],
            "occupancy_is_historical_not_new_mesh_test": True,
            "actual_available_cavity": False,
        },
        "radius_sensitivity_not_vendor_limits": [
            return_space_screen(chamber["bounds_xyz_mm"], 15.6, .12, .25, radius)
            for radius in (2, 3, 4, 6, 8, 12)
        ],
        "historical_supplier_example_lower_boundary_screen":
            return_space_screen(chamber["bounds_xyz_mm"], 15.6, .12, 0, 12),
        "supplier_example_caveat": "R37 records >12 mm inside radius for approximately 120 um single-layer flex. Testing 12 mm is a more permissive lower boundary, not a newly audited source or a DeepReal limit.",
        "unapproved_requirements": {
            "supplier": None, "dynamic_stack": None, "dynamic_trunk_width": None,
            "minimum_dynamic_inside_radius_mm": None, "minimum_straight_entry_mm": None,
            "numbered_continuity": None, "six_pair_signal_integrity": None,
            "load_and_voltage_drop": None, "cycle_life": None, "speed_and_acceleration": None,
            "tolerance_stack": None, "cable_torque_budget": None,
        },
        "housed_route_qualified": False,
        "interface_freeze_allowed": False,
        "source_or_installed_assets_written": False,
        "limits": [
            "Endpoint poses describe rigid motion only, not cable deformation or fatigue.",
            "Necessary return diameter/width bounds never establish a routed cable.",
            "The historical chamber is occupied visual solid, not an available cavity.",
            "No connector, bearing, carrier, housing, PCB or gate is modified.",
            "Face-only screen; interaction is not validated by symmetry.",
        ],
    }
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print("FACE FLEX SCREEN", output)
    print("MOVING ENTRY", entry["center_mm"], "FIXED LANDING", terminal["center_mm"])
    print("ENDPOINT TRAVEL", report["endpoints"]["entry_extreme_to_extreme_displacement_mm"])
    print("RETURN EXAMPLE REJECTED", not report["historical_supplier_example_lower_boundary_screen"]
          ["necessary_bounds_satisfied"])


if __name__ == "__main__":
    main()
