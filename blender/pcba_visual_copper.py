"""Blender geometry for the shared production-intent copper artwork."""

from mathutils import Vector

from assembly_primitives import box, cylinder, material, routed_wire, tag, tube
from pcba_bom import BOARD
from pcba_visual_layout import DISCLAIMER, POURS, TEST_PADS, TRACE_GROUPS, VIAS


def _surface_y(side, outward=0.0):
    direction = -1.0 if side == "TOP" else 1.0
    return BOARD["center_y"] + direction * (BOARD["thickness"] / 2 + outward)


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
        y = _surface_y(group["side"], 0.035)
        trace_mat = masked_power if group["width"] >= 0.30 else masked
        for index, path in enumerate(group["paths"], 1):
            points = tuple((x, y, z) for x, z in path)
            obj = routed_wire("Visual_{}_{}".format(group["name"], index),
                              points, group["width"] / 2.0, 0.18,
                              trace_mat, collection, corner_segments=4)
            obj["PCBA_Visual_Copper"] = True
            obj["PCBA_Side"] = group["side"]
            obj["PCBA_Trace_Class"] = group["class"]
            objects.append(tag(obj, group["subsystem"], DISCLAIMER))
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
