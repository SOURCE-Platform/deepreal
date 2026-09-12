#!/usr/bin/env python3
"""Mechanical-BOM, placement, density, and stack checks for Main PCBA."""

import itertools
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pcba_bom import ALL_PARTS, BOARD


VALID_STATUS = {
    "BASELINE", "CALC_REQUIRED", "COMPILE_REQUIRED",
    "DDR_VALIDATION_REQUIRED", "FLEX_SI_GATE", "MECHANICAL_GATE",
    "PINMAP_REQUIRED", "RESERVED", "SELECTION_REQUIRED",
    "SEQUENCE_REVIEW", "SI_REVIEW", "SUPPLY_RECHECK",
}
MOUNT_POINTS = ((-42,-22.5), (-42,-.5), (42,-22.5), (42,-.5))


def _mesh_data(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        polygons = [tuple(poly.vertices) for poly in mesh.polygons]
        return vertices, polygons
    finally:
        evaluated.to_mesh_clear()


def _bounds(obj):
    vertices, _ = _mesh_data(obj)
    return tuple(min(v[i] for v in vertices) for i in range(3)), \
        tuple(max(v[i] for v in vertices) for i in range(3))


def _tree(obj):
    vertices, polygons = _mesh_data(obj)
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def _intersects(a, b):
    return bool(_tree(a).overlap(_tree(b)))


def _dimensions(obj):
    lo, hi = _bounds(obj)
    return tuple((hi[i]-lo[i])*1000 for i in range(3))


def _overlap_2d(a, b, clearance=.05):
    a0, a1 = _bounds(a)
    b0, b1 = _bounds(b)
    return (min(a1[0], b1[0])-max(a0[0], b0[0]) > clearance*.001
            and min(a1[2], b1[2])-max(a0[2], b0[2]) > clearance*.001)


def _occupancy(side):
    step = .5
    xs = [(-45 + step/2) + i*step for i in range(int(90/step))]
    zs = [(-25.5 + step/2) + i*step for i in range(int(28/step))]
    canonical = bpy.data.collections["Electronics Assembly"].objects
    parts = [obj for obj in canonical
             if obj.get("PCBA_Component") and obj.get("PCBA_Side") == side]
    rectangles = []
    for obj in parts:
        lo, hi = _bounds(obj)
        rectangles.append((lo[0]*1000, hi[0]*1000, lo[2]*1000, hi[2]*1000))
    occupied = sum(
        1 for x in xs for z in zs
        if any(x0 <= x <= x1 and z0 <= z <= z1
               for x0, x1, z0, z1 in rectangles))
    return occupied * step * step, len(parts)


def main():
    failures, warnings = [], []
    pivot = bpy.data.objects.get("Lid_Pivot")
    original = pivot.rotation_euler.copy() if pivot else None
    if pivot:
        pivot.rotation_euler = (0,0,0)
        bpy.context.view_layer.update()
    try:
        board = bpy.data.objects.get("Main_PCBA")
        if not board:
            raise RuntimeError("Main_PCBA missing")
        got = _dimensions(board)
        expected = (BOARD["width"], BOARD["thickness"], BOARD["depth"])
        if any(abs(a-b) > .05 for a, b in zip(got, expected)):
            failures.append("board dimensions {} != {} mm".format(got, expected))

        part_objects = []
        for part in ALL_PARTS:
            obj = bpy.data.objects.get(part["name"])
            if not obj:
                failures.append("missing mechanical BOM part " + part["name"])
                continue
            part_objects.append((part, obj))
            if obj.get("PCBA_Status") not in VALID_STATUS:
                failures.append(part["name"] + " lacks valid status metadata")
            dx, dy, dz = _dimensions(obj)
            wanted = (part["width"], part["height"], part["depth"])
            tolerance = .18 if part["name"] == "USB_C_Receptacle" else .06
            if any(abs(a-b) > tolerance for a, b in zip((dx,dy,dz), wanted)):
                failures.append("{} body {:.2f}x{:.2f}x{:.2f} != {:.2f}x{:.2f}x{:.2f} mm".format(
                    part["name"], dx,dy,dz,*wanted))
            lo, hi = _bounds(obj)
            surface = BOARD["center_y"] + (-.8 if part["side"] == "TOP" else .8)
            contact = hi[1]*1000 if part["side"] == "TOP" else lo[1]*1000
            if abs(contact-surface) > .08:
                failures.append(part["name"] + " does not seat on PCB")
            if lo[0] < -.04505 or hi[0] > .04505 or lo[2] < -.02555 or hi[2] > .00255:
                failures.append(part["name"] + " exceeds PCB X/Z envelope")
            for hx, hz in MOUNT_POINTS:
                nearest_x = max(lo[0]*1000, min(hx, hi[0]*1000))
                nearest_z = max(lo[2]*1000, min(hz, hi[2]*1000))
                if (nearest_x-hx)**2 + (nearest_z-hz)**2 < 2.05**2:
                    failures.append(part["name"] + " enters mounting keep-out")

        for (part_a, a), (part_b, b) in itertools.combinations(part_objects, 2):
            if part_a["side"] == part_b["side"] and _overlap_2d(a, b) \
                    and _intersects(a, b):
                failures.append("major component collision: {} / {}".format(
                    part_a["name"], part_b["name"]))

        canonical = bpy.data.collections["Electronics Assembly"].objects
        components = [obj for obj in canonical if obj.get("PCBA_Component")]
        component_bounds = {obj: _bounds(obj) for obj in components}
        for a, b in itertools.combinations(components, 2):
            if a.get("PCBA_Side") != b.get("PCBA_Side"):
                continue
            a0, a1 = component_bounds[a]
            b0, b1 = component_bounds[b]
            if min(a1[0], b1[0]) > max(a0[0], b0[0]) + .00002 \
                    and min(a1[2], b1[2]) > max(a0[2], b0[2]) + .00002:
                failures.append("component courtyard overlap: {} / {}".format(
                    a.name, b.name))
        component_count = sum(1 for obj in canonical
                              if obj.get("PCBA_Component"))
        if component_count < 100:
            failures.append("only {} modeled PCBA components".format(component_count))
        if component_count > 300:
            warnings.append("{} bodies exceed the preliminary density range".format(component_count))

        top = [(_bounds(obj)[0][1]*1000, _bounds(obj)[1][1]*1000)
               for part, obj in part_objects if part["side"] == "TOP"]
        bottom = [(_bounds(obj)[0][1]*1000, _bounds(obj)[1][1]*1000)
                  for part, obj in part_objects if part["side"] == "BOTTOM"]
        front_surface = BOARD["center_y"] - BOARD["thickness"]/2
        rear_surface = BOARD["center_y"] + BOARD["thickness"]/2
        top_height = front_surface - min(v[0] for v in top)
        bottom_height = max(v[1] for v in bottom) - rear_surface
        stack = top_height + BOARD["thickness"] + bottom_height
        if stack > 15.0:
            failures.append("populated stack {:.2f} mm exceeds 15 mm".format(stack))

        top_area, top_count = _occupancy("TOP")
        bottom_area, bottom_count = _occupancy("BOTTOM")
        usb = bpy.data.objects["USB_C_Receptacle"]
        housing_usb = bpy.data.objects.get("Main_Housing_USB_Shell")
        if housing_usb:
            separation = (_bounds(usb)[0][0] + _bounds(usb)[1][0])/2 - \
                (_bounds(housing_usb)[0][0] + _bounds(housing_usb)[1][0])/2
            if abs(separation) > .005:
                warnings.append("board USB-C and housing opening are not aligned ({:.1f} mm X offset)".format(separation*1000))

        print("PCBA PACKAGING METRICS")
        print("  board: 90.00 x 28.00 x 1.60 mm")
        print("  modeled component bodies: {} (top {}, bottom {})".format(
            component_count, top_count, bottom_count))
        print("  tallest top / bottom: {:.2f} / {:.2f} mm".format(top_height, bottom_height))
        print("  populated thickness: {:.2f} mm of 15.00 mm envelope".format(stack))
        print("  body-projected area: top {:.0f} mm2, bottom {:.0f} mm2".format(top_area, bottom_area))
        print("  unoccupied projection: top {:.0f} mm2, bottom {:.0f} mm2".format(
            2520-top_area, 2520-bottom_area))
        for warning in warnings:
            print("  OPEN: " + warning)
    finally:
        if pivot and original is not None:
            pivot.rotation_euler = original
            bpy.context.view_layer.update()
    if failures:
        raise RuntimeError("\n".join(failures))
    print("PASS: mechanical BOM, two-sided seating, density, mounting, and 15 mm stack")


if __name__ == "__main__":
    main()
