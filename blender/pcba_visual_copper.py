"""Superseded handmade copper artwork retained only for history.

Do not import this module into a public or engineering scene. Canonical visible
copper is built by ``pcba_kicad_geometry.py`` from the KiCad export.
"""

import math

import bpy
from mathutils import Vector

from assembly_primitives import MM, box, cylinder, material, tag, tube
from pcba_bom import BOARD
from pcba_visual_layout import DISCLAIMER, POURS, TEST_PADS, TRACE_GROUPS, VIAS


def _surface_y(side, outward=0.0):
    direction = -1.0 if side == "TOP" else 1.0
    return BOARD["center_y"] + direction * (BOARD["thickness"] / 2 + outward)


def _flat_trace(name, side, path, width, trace_material, collection):
    """Build flush rectangular copper foil, never a raised wire-like curve."""
    y = _surface_y(side, 0.010)
    thickness = 0.018
    vertices, faces = [], []
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        dx, dz = x1 - x0, z1 - z0
        length = math.hypot(dx, dz)
        if length < 0.01:
            continue
        ux, uz = dx / length, dz / length
        px, pz = -uz * width / 2.0, ux * width / 2.0
        overlap = min(0.06, width * 0.40)
        ax, az = x0 - ux * overlap, z0 - uz * overlap
        bx, bz = x1 + ux * overlap, z1 + uz * overlap
        y0, y1 = y - thickness / 2.0, y + thickness / 2.0
        base = len(vertices)
        vertices.extend(
            (x * MM, yy * MM, z * MM)
            for x, yy, z in (
                (ax + px, y0, az + pz), (bx + px, y0, bz + pz),
                (bx - px, y0, bz - pz), (ax - px, y0, az - pz),
                (ax + px, y1, az + pz), (bx + px, y1, bz + pz),
                (bx - px, y1, bz - pz), (ax - px, y1, az - pz),
            )
        )
        faces.extend(tuple(base + index for index in face) for face in (
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
        ))
    if not vertices:
        return None
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(trace_material)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj["PCBA_Visual_Copper"] = True
    obj["PCBA_Side"] = side
    return obj


def build(collection):
    """Build the shared visual copper layer in the canonical PCBA collection."""
    masked = material("PCBA_Masked_Copper", (0.018, 0.115, 0.038),
                      metallic=0.22, roughness=0.34)
    masked_power = material("PCBA_Masked_Power_Copper", (0.022, 0.135, 0.044),
                            metallic=0.28, roughness=0.31)
    gold = material("PCBA_Exposed_ENIG", (0.78, 0.52, 0.12),
                    metallic=0.96, roughness=0.20)
    pour_mat = material("PCBA_Masked_Pours", (0.014, 0.095, 0.030),
                        metallic=0.18, roughness=0.40)
    objects = []
    for pour in POURS:
        side = pour["side"]
        y = _surface_y(side, 0.015)
        obj = box(pour["name"], (pour["center"][0], y, pour["center"][1]),
                  (pour["size"][0], 0.03, pour["size"][1]), 0.35,
                  pour_mat, collection)
        obj["PCBA_Visual_Copper"] = True
        obj["PCBA_Side"] = side
        objects.append(tag(obj, pour["subsystem"], DISCLAIMER))
    for group in TRACE_GROUPS:
        trace_mat = masked_power if group["width"] >= 0.30 else masked
        for index, path in enumerate(group["paths"], 1):
            name = "Visual_{}_{}".format(group["name"], index)
            trace = _flat_trace(name, group["side"], path,
                                group["width"], trace_mat, collection)
            if trace:
                trace["PCBA_Trace_Class"] = group["class"]
                objects.append(tag(trace, group["subsystem"], DISCLAIMER))
    for index, via in enumerate(VIAS, 1):
        obj = tube("Visual_Via_{:03d}".format(index),
                   (via["x"], BOARD["center_y"], via["z"]), Vector((0, 1, 0)),
                   0.12, 0.26, BOARD["thickness"] + 0.12,
                   gold, collection, segments=16)
        obj["PCBA_Visual_Copper"] = True
        obj["PCBA_Via_Kind"] = via["kind"]
        objects.append(tag(obj, "Layer transition", DISCLAIMER))
    for pad in TEST_PADS:
        y = _surface_y(pad["side"], 0.045)
        obj = cylinder("Visual_" + pad["name"], (pad["x"], y, pad["z"]),
                       Vector((0, 1, 0)), 0.42, 0.09, gold, collection,
                       segments=24)
        obj["PCBA_Visual_Copper"] = True
        obj["PCBA_Side"] = pad["side"]
        objects.append(tag(obj, "Test access", DISCLAIMER))
    return objects
