"""Read the canonical KiCad geometry export without inventing placement data."""

import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXPORT = os.path.join(
    os.path.dirname(HERE), "hardware", "electronics", "deepreal-main-pcba",
    "engineering-layout-export.json")


def load(path=DEFAULT_EXPORT):
    with open(path, encoding="utf-8") as stream:
        payload = json.load(stream)
    metadata = payload.get("metadata", {})
    if metadata.get("schema") != "deepreal.pcba.kicad-export.v1":
        raise ValueError("unsupported or missing KiCad export schema")
    for key in ("board", "components", "holes", "pads", "tracks", "vias", "zones"):
        if key not in payload:
            raise ValueError("KiCad export missing " + key)
    return payload


def board_to_blender(x_mm, y_mm, bounds_mm, center_x_mm=0.0,
                     center_z_mm=-11.5):
    """Convert KiCad X/Y millimetres to centered Blender X/Z millimetres."""
    x0, y0, x1, y1 = bounds_mm
    return (center_x_mm + x_mm - (x0 + x1) / 2.0,
            center_z_mm + (y0 + y1) / 2.0 - y_mm)


def blender_to_board(x_mm, z_mm, bounds_mm, center_x_mm=0.0,
                     center_z_mm=-11.5):
    """Convert Blender X/Z millimetres back to KiCad board coordinates."""
    x0, y0, x1, y1 = bounds_mm
    return (x_mm - center_x_mm + (x0 + x1) / 2.0,
            center_z_mm + (y0 + y1) / 2.0 - z_mm)


def public_ready(payload):
    metadata = payload["metadata"]
    gates = payload.get("validation_status", {})
    return (metadata.get("public_visual_allowed") is True
            and gates.get("G11") == "PASS")
