#!/usr/bin/env python3
"""Report approximate closest points between routed cable centerlines."""

import itertools

import bpy


NAMES = (
    "Face_RGB_MIPI_Flex", "Face_Depth_MIPI_Flex",
    "Interaction_Depth_MIPI_Flex", "Interaction_Tracking_MIPI_Flex",
    "Face_Projector_Power", "Interaction_Projector_Power",
    "Face_Motor_Encoder_Harness", "Interaction_Motor_Encoder_Harness",
)


def _points(name):
    obj = bpy.data.objects[name]
    spline = obj.data.splines[0]
    return [obj.matrix_world @ point.co.xyz for point in spline.points]


def _sample(points, steps=8):
    values = []
    for a, b in zip(points, points[1:]):
        values += [a.lerp(b, index / steps) for index in range(steps)]
    values.append(points[-1])
    return values


def main():
    for a_name, b_name in itertools.combinations(NAMES, 2):
        if a_name.split("_")[0] != b_name.split("_")[0]:
            continue
        best = min(
            ((a-b).length, a, b)
            for a in _sample(_points(a_name))
            for b in _sample(_points(b_name))
        )
        if best[0] < 0.002:
            print("{:.3f} mm | {} <> {} | {} <> {}".format(
                best[0]*1000, a_name, b_name,
                tuple(round(v*1000, 2) for v in best[1]),
                tuple(round(v*1000, 2) for v in best[2])))


if __name__ == "__main__":
    main()
