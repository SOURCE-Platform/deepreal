"""Exploratory offset twist strip; electrical and fatigue design remain open."""

import math

MM = .001
AXIS_Y_MM = -1.5
AXIS_Z_MM = 20.0


def vertices(x_start_mm, x_end_mm, angle_deg, width_mm, thickness_mm,
             moving_offset_y_mm, segments):
    points = []
    for step in range(segments + 1):
        fraction = step / segments
        eased = fraction * fraction * (3 - 2 * fraction)
        fading = 1 - eased
        angle = math.radians(angle_deg) * fading
        cos_angle, sin_angle = math.cos(angle), math.sin(angle)
        offset = moving_offset_y_mm * fading
        center_y = AXIS_Y_MM + offset * cos_angle
        center_z = AXIS_Z_MM - offset * sin_angle
        x = x_start_mm + (x_end_mm - x_start_mm) * fraction
        for side, face in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            y = center_y + side * width_mm / 2 * sin_angle
            y += face * thickness_mm / 2 * cos_angle
            z = center_z + side * width_mm / 2 * cos_angle
            z -= face * thickness_mm / 2 * sin_angle
            points.append((x * MM, y * MM, z * MM))
    return points


def set_pose(obj, angle_deg, moving_offset_y_mm):
    points = vertices(obj["R35_Moving_Anchor_X_mm"],
                      obj["R35_Fixed_Anchor_X_mm"], angle_deg,
                      obj["R35_Width_mm"], obj["R35_Thickness_mm"],
                      moving_offset_y_mm,
                      (len(obj.data.vertices) // 4) - 1)
    for vertex, position in zip(obj.data.vertices, points):
        vertex.co = position
    obj.data.update()
