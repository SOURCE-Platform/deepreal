"""Build visible PCB copper only from the canonical KiCad geometry export."""

import math

import bpy
from mathutils import Vector

from assembly_primitives import MM, material, tag, tube
from pcba_bom import BOARD
from pcba_kicad_data import board_to_blender, load


STATUS = "CANONICAL KICAD COPPER"


def _surface_y(side, outward=0.0):
    direction = -1.0 if side == "TOP" else 1.0
    return BOARD["center_y"] + direction * (BOARD["thickness"] / 2 + outward)


def _track_mesh(name, side, start, end, width, mat, collection):
    x0, z0 = start
    x1, z1 = end
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    if length < 0.001:
        return None
    ux, uz = dx / length, dz / length
    px, pz = -uz * width / 2.0, ux * width / 2.0
    y = _surface_y(side, 0.006)
    thickness = 0.012
    vertices = [
        ((x0 + px) * MM, (y - thickness / 2) * MM, (z0 + pz) * MM),
        ((x1 + px) * MM, (y - thickness / 2) * MM, (z1 + pz) * MM),
        ((x1 - px) * MM, (y - thickness / 2) * MM, (z1 - pz) * MM),
        ((x0 - px) * MM, (y - thickness / 2) * MM, (z0 - pz) * MM),
        ((x0 + px) * MM, (y + thickness / 2) * MM, (z0 + pz) * MM),
        ((x1 + px) * MM, (y + thickness / 2) * MM, (z1 + pz) * MM),
        ((x1 - px) * MM, (y + thickness / 2) * MM, (z1 - pz) * MM),
        ((x0 - px) * MM, (y + thickness / 2) * MM, (z0 - pz) * MM),
    ]
    faces = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def build(collection):
    payload = load()
    bounds = payload["board"]["bounds_mm"]
    masked = material("PCBA_KiCad_Masked_Copper", (0.016, 0.11, 0.035),
                      metallic=0.18, roughness=0.38)
    exposed = material("PCBA_KiCad_Exposed_ENIG", (0.78, 0.52, 0.12),
                       metallic=0.96, roughness=0.20)
    objects = []
    for index, track in enumerate(payload["tracks"], 1):
        if track["layer"] not in {"F.Cu", "B.Cu"}:
            continue
        side = "TOP" if track["layer"] == "F.Cu" else "BOTTOM"
        start = board_to_blender(*track["start_mm"], bounds)
        end = board_to_blender(*track["end_mm"], bounds)
        obj = _track_mesh("KiCad_Track_{:05d}".format(index), side,
                          start, end, track["width_mm"], masked, collection)
        if obj:
            obj["PCBA_Net"] = track["net"]
            obj["PCBA_Layer"] = track["layer"]
            objects.append(tag(obj, "PCB copper", STATUS))
    for index, via in enumerate(payload["vias"], 1):
        x, z = board_to_blender(*via["position_mm"], bounds)
        is_open = via.get("mask_open_top") or via.get("mask_open_bottom")
        obj = tube("KiCad_Via_{:05d}".format(index),
                   (x, BOARD["center_y"], z), Vector((0, 1, 0)),
                   via["drill_mm"] / 2.0, via["diameter_mm"] / 2.0,
                   BOARD["thickness"] + 0.03,
                   exposed if is_open else masked, collection, segments=20)
        obj["PCBA_Net"] = via["net"]
        obj["PCBA_ViaType"] = via["via_type"]
        objects.append(tag(obj, "PCB copper", STATUS))
    return objects
