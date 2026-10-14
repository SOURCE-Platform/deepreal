"""Necessary space bounds, not a dynamic-flex or clearance qualification."""

import math


def positive(value, name, allow_zero=False):
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{name} must be finite and {'nonnegative' if allow_zero else 'positive'}")
    return value


def rotate_x(point, pivot, angle_degrees):
    """Rigid endpoint motion about the drum axis, in the input length units."""
    angle = math.radians(angle_degrees)
    x, y, z = point
    dy, dz = y - pivot[1], z - pivot[2]
    return (
        x,
        pivot[1] + dy * math.cos(angle) - dz * math.sin(angle),
        pivot[2] + dy * math.sin(angle) + dz * math.cos(angle),
    )


def radial_distance(point, pivot):
    return math.hypot(point[1] - pivot[1], point[2] - pivot[2])


def ribbon_corner_radius(width_mm, thickness_mm):
    return math.hypot(positive(width_mm, "width") / 2,
                      positive(thickness_mm, "thickness") / 2)


def return_space_screen(bounds, width_mm, thickness_mm, clearance_mm, inside_radius_mm):
    """Reject impossible 180° circular returns in the YZ plane, width along X.

    The diameter chord is a necessary bound only. Passing this bound does not
    fit the semicircle, its legs, endpoint motion or a developed cable shape.
    Clearance and thickness are explicit study assumptions, not vendor limits.
    """
    width = positive(width_mm, "width")
    thickness = positive(thickness_mm, "thickness")
    clearance = positive(clearance_mm, "clearance", allow_zero=True)
    radius = positive(inside_radius_mm, "inside radius")
    spans = [positive(high - low, "reservation span") for low, high in bounds]
    if len(spans) != 3:
        raise ValueError("reservation must have three axes")
    available_y, available_z = (max(0, span - 2 * clearance) for span in spans[1:])
    chord_space = math.hypot(available_y, available_z)
    outside_diameter = 2 * (radius + thickness)
    width_fits = width + 2 * clearance <= spans[0]
    diameter_fits = outside_diameter <= chord_space
    return {
        "inside_radius_mm": radius,
        "assumed_dynamic_thickness_mm": thickness,
        "assumed_clearance_per_side_mm": clearance,
        "assumed_full_trunk_width_mm": width,
        "outside_return_diameter_mm": outside_diameter,
        "usable_yz_diagonal_mm": chord_space,
        "axial_width_bound_satisfied": width_fits,
        "diameter_bound_satisfied": diameter_fits,
        "necessary_bounds_satisfied": width_fits and diameter_fits,
        "maximum_inside_radius_from_chord_bound_mm": max(0, chord_space / 2 - thickness),
        "route_qualified": False,
    }
