"""Blender-native DeepReal concept dimensions and product manifest.

Blender is the current design authority.  Values here replace the legacy
FreeCAD-exported manifest and intentionally describe the approved concept:
two 24 mm drums above a curved, behind-lid electronics compartment.
All dimensions are millimetres in the established X/Y/Z product frame.
"""

import math


PARAMS = {
    "DISPLAY_LID_THICKNESS": 3.0,
    "DISPLAY_REFERENCE_HEIGHT": 215.0,
    "DISPLAY_REFERENCE_WIDTH": 304.0,
    "FACE_HEAD_DIAMETER": 24.0,
    "FACE_HEAD_LENGTH": 54.0,
    "FACE_HEAD_ROTATION_DEG": 0.0,
    "INTERACTION_HEAD_DIAMETER": 24.0,
    "INTERACTION_HEAD_LENGTH": 54.0,
    "INTERACTION_HEAD_ROTATION_DEG": 45.0,
    "MAIN_BODY_DEPTH": 24.0,
    "MAIN_BODY_HEIGHT": 30.0,
    "MAIN_BODY_WIDTH": 120.0,
    "MAIN_BODY_DISPLAY_OFFSET_Y": 10.5,
    "MAIN_BODY_DISPLAY_OFFSET_Z": 5.0,
    "REAR_ARM_ARC_CENTER_Z": 5.0,
    "REAR_ARM_BOTTOM_Z": -27.0,
    "REAR_ARM_MOUNT_FACE_Y": 3.5,
    "REAR_ARM_RADIUS": 19.0,
    # Curved electronics compartment, derived from the approved cyan sketch.
    "ELECTRONICS_FRONT_Y": 3.5,
    "ELECTRONICS_REAR_Y": 24.5,
    "ELECTRONICS_BOTTOM_Z": -29.0,
    "ENCLOSURE_WALL": 1.5,
}


def _cubic(p0, p1, p2, p3, steps=12):
    points = []
    for index in range(1, steps + 1):
        t = index / float(steps)
        u = 1.0 - t
        points.append((
            u ** 3 * p0[0] + 3 * u * u * t * p1[0]
            + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1]
            + 3 * u * t * t * p2[1] + t ** 3 * p3[1],
        ))
    return points


def housing_profile():
    """Closed outer Y/Z profile for the curved reference enclosure."""
    front = -1.5
    rear = 22.5
    body_bottom = 5.0
    body_top = 35.0
    bay_front = PARAMS["ELECTRONICS_FRONT_Y"]
    bay_rear = PARAMS["ELECTRONICS_REAR_Y"]
    bay_bottom = PARAMS["ELECTRONICS_BOTTOM_Z"]

    points = [
        (front, body_top),
        (front, body_bottom),
        (bay_front, body_bottom),
        (bay_front, bay_bottom + 2.0),
    ]
    points += _cubic(
        points[-1],
        (bay_front + 7.0, bay_bottom - 2.0),
        (bay_rear, bay_bottom - 1.0),
        (bay_rear, -16.0),
    )
    points += _cubic(
        points[-1],
        (bay_rear, -5.0),
        (rear, 0.0),
        (rear, body_bottom),
        steps=8,
    )
    points += [(rear, body_top)]
    return points


def _polygon_area(points):
    return abs(sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1])
    )) / 2.0


def _part(name, minimum, maximum, volume_mm3=1.0):
    return {
        "name": name,
        "kind": "product",
        "bbox_mm": {"min": list(minimum), "max": list(maximum)},
        "volume_mm3": volume_mm3,
    }


def manifest():
    profile = housing_profile()
    width = PARAMS["MAIN_BODY_WIDTH"]
    housing = _part(
        "Main_Housing",
        (-width / 2.0, min(p[0] for p in profile),
         min(p[1] for p in profile)),
        (width / 2.0, max(p[0] for p in profile),
         max(p[1] for p in profile)),
        _polygon_area(profile) * width,
    )
    face = _part("Face_Sensor_Head", (-56.0, -13.5, 8.0),
                 (-2.0, 10.5, 32.0), math.pi * 12.0 ** 2 * 54.0)
    interaction = _part("Interaction_Sensor_Head", (2.0, -13.5, 8.0),
                        (56.0, 10.5, 32.0), math.pi * 12.0 ** 2 * 54.0)
    return {
        "params": dict(PARAMS),
        "parts": [housing, face, interaction],
        "profiles": {
            "Main_Housing": {
                "plane": "YZ at X=0",
                "points_yz_mm": [list(point) for point in profile],
            }
        },
        "authority": "Blender concept baseline",
    }
