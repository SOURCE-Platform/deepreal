#!/usr/bin/env python3
"""Read-only head interface screening. No geometry or pin assignment is invented."""

import hashlib
import math


REQUIRED_CLOSURES = {
    "exact_numbered_connector_drawing_and_pad_audit",
    "main_and_head_connector_orientation_and_continuity",
    "head_native_schematic_and_netlist",
    "head_current_startup_pulse_recharge_and_fault_budget",
    "parallel_contact_derating_and_voltage_drop",
    "six_differential_pairs_impedance_and_crosstalk",
    "flex_stackup_stiffener_strain_relief_and_bend_life",
    "latch_access_and_full_motion_clearance",
    "head_safe_default_hardware_interlock",
}


def bounds(polygons):
    points = [p for polygon in polygons for p in polygon]
    if not points:
        raise ValueError("Missing courtyard; do not substitute a body envelope")
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def rotate(polygons, old_position, new_position, delta_deg):
    """KiCad positive rotation is counterclockwise in screen-down Y coordinates."""
    angle = math.radians(delta_deg)
    c, s = math.cos(angle), math.sin(angle)
    result = []
    for polygon in polygons:
        moved = []
        for x, y in polygon:
            x, y = x-old_position[0], y-old_position[1]
            moved.append([round(new_position[0]+c*x+s*y, 6),
                          round(new_position[1]-s*x+c*y, 6)])
        result.append(moved)
    return result


def overlaps(a, b):
    return min(a[2], b[2]) > max(a[0], b[0])+1e-6 and \
        min(a[3], b[3]) > max(a[1], b[1])+1e-6


def placement_screen(layout, ref, new_position=None, rotation=None):
    components = {c["ref"]: c for c in layout["components"]}
    component = components[ref]
    position = new_position or component["position_mm"]
    rotation = component["rotation_deg"] if rotation is None else rotation
    polygons = rotate(component["courtyard_polygons_mm"],
                      component["position_mm"], position,
                      rotation-component["rotation_deg"])
    box = bounds(polygons)
    edge = layout["board"]["bounds_mm"]
    overhang = [max(0, edge[0]-box[0]), max(0, edge[1]-box[1]),
                max(0, box[2]-edge[2]), max(0, box[3]-edge[3])]
    conflicts, unknown = [], []
    for other in layout["components"]:
        if other["ref"] == ref or other["side"] != component["side"]:
            continue
        if not other["courtyard_polygons_mm"]:
            unknown.append(other["ref"])
            continue
        if overlaps(box, bounds(other["courtyard_polygons_mm"])):
            conflicts.append(other["ref"])
    return {
        "ref": ref, "position_mm": position, "rotation_deg": rotation,
        "courtyard_polygons_mm": polygons, "courtyard_bounds_mm": box,
        "outline_overhang_left_top_right_bottom_mm": [round(v, 6) for v in overhang],
        "same_side_courtyard_aabb_candidates": sorted(conflicts),
        "same_side_missing_courtyard_refs": sorted(unknown),
        "status": "NOT_APPROVED",
        "limitation": "AABB screen only; not polygon DRC, pad clearance, verified body, shield, latch, cable, motion, or electrical feasibility. Other components remain fixed."
    }


def capacity_screen(rows, evidence):
    counts = {row["Group"]: int(row["Contacts"]) for row in rows}
    power = counts["Head_3V3"]
    ground = counts["Power_returns"]
    if min(power, ground) < 1:
        raise ValueError("Power and dedicated return contacts must be positive")
    connector = evidence["connector"]
    nominal = min(power, ground)*connector["current_rating_per_contact_a"]
    conservative = nominal*connector["all_contacts_loaded_factor"]
    rgb, ir = counts["RGB_CSI_signals"], counts["IR_CSI_signals"]
    if rgb != 6 or ir != 6:
        raise ValueError("Each two-data-lane camera needs six contacts: two data pairs plus clock pair")
    return {
        "contacts_per_head": sum(counts.values()),
        "camera_differential_pairs_per_head": (rgb+ir)//2,
        "supply_contacts": power, "dedicated_return_contacts": ground,
        "ideal_equal_sharing_rating_sum_a": round(nominal, 6),
        "conservative_70_percent_screen_a": round(conservative, 6),
        "screen_input_power_before_losses_w": round(conservative*
            evidence["screening_assumptions"]["supply_voltage_v"], 6),
        "required_peak_input_current_a": None,
        "power_feasibility": "BLOCKED_MISSING_LOAD_AND_DERATING_EVIDENCE"
    }


def land_pattern_screen(layout, ref, evidence):
    """Compare copper-pad dimensions without asserting catalog pin numbering."""
    component = next(c for c in layout["components"] if c["ref"] == ref)
    groups = {"long_row": [], "short_row": [], "retention_tabs": []}
    expected = evidence["catalog_land_pattern_mm"]
    errors = []
    for pad in (p for p in layout["pads"] if p["ref"] == ref):
        point = rotate([[pad["position_mm"]]], component["position_mm"],
                       [0, 0], -component["rotation_deg"])[0][0]
        matched = [name for name in groups if all(abs(a-b) < 1e-5 for a, b in
                   zip(pad["size_mm"], expected[name]["pad_size"]))]
        if len(matched) != 1:
            errors.append("Unexpected copper pad size: "+pad["number"])
        else:
            groups[matched[0]].append(point)
    centers = {}
    for name, points in groups.items():
        target = expected[name]
        if len(points) != target["count"]:
            errors.append(name+" count mismatch")
        if not points:
            continue
        ys = sorted(p[1] for p in points)
        if abs(ys[-1]-ys[0]-target["span"]) > 1e-5:
            errors.append(name+" span mismatch")
        if max(p[0] for p in points)-min(p[0] for p in points) > 1e-5:
            errors.append(name+" is not a straight row")
        if "pitch" in target and any(abs(b-a-target["pitch"]) > 1e-5
                                    for a, b in zip(ys, ys[1:])):
            errors.append(name+" pitch mismatch")
        centers[name] = sum(p[0] for p in points)/len(points)
    if "long_row" in centers and "short_row" in centers:
        spacing = abs(centers["long_row"]-centers["short_row"])
        if abs(spacing-expected["row_center_separation"]) > 1e-5:
            errors.append("row center separation mismatch")
    return {"ref": ref, "dimension_screen": "FAIL" if errors else "PASS",
            "errors": errors, "pad_counts": {k: len(v) for k, v in groups.items()},
            "pin_numbering_audited": False, "paste_apertures_audited": False,
            "warning": "Dimension subset only. Reflection, pin-one numbering, tab alignment, mask/paste, 3D model and mating orientation require exact-part audit."}


def audit(rows, evidence, layout, repo):
    source = evidence["source"]
    if hashlib.sha256((repo/source["file"]).read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError("Manufacturer source hash mismatch")
    closures = evidence["closure_evidence"]
    if set(closures) != REQUIRED_CLOSURES:
        raise ValueError("Incomplete or unexpected closure evidence categories")
    opened = []
    for name, item in closures.items():
        if item is None:
            opened.append(name)
        elif not isinstance(item, dict) or not item.get("reviewer") or not item.get("sha256"):
            raise ValueError("Closure needs a file, hash and named reviewer: "+name)
        elif hashlib.sha256((repo/item["file"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Closure evidence hash mismatch: "+name)
    refs = [item["main_connector"] for item in evidence["instances"]]
    if refs != ["J2", "J3"]:
        raise ValueError("Expected one instance per drum: J2 face, J3 interaction")
    current, trials = [], []
    components = {c["ref"]: c for c in layout["components"]}
    for ref in refs:
        current.append(placement_screen(layout, ref))
        for angle in (90, -90):
            trials.append(placement_screen(layout, ref,
                [components[ref]["position_mm"][0], 45.0], angle))
    return {
        "schema": "deepreal.head-interface-audit.v1",
        "source_board_sha256": layout["metadata"]["source_board_sha256"],
        "catalog_sha256": source["sha256"],
        "interface_status": "BLOCKED" if opened else "REQUIRES_INDEPENDENT_REVIEW",
        "fabrication_allowed": False, "public_visual_allowed": False,
        "capacity_screen": capacity_screen(rows, evidence),
        "copper_land_pattern_screens": [land_pattern_screen(layout, ref, evidence) for ref in refs],
        "open_closure_evidence": sorted(opened),
        "current_placements": current, "quarter_turn_trials_not_applied": trials,
        "warning": "Trial positions are diagnostic perturbations, not design decisions. No KiCad or Blender placement was changed."
    }
