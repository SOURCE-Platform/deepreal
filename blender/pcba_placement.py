"""Merge KiCad-authoritative placement with presentation-only part metadata."""

from pcba_bom import ALL_PARTS, BOARD
from pcba_kicad_data import board_to_blender, load


def engineering_parts():
    payload = load()
    bounds = payload["board"]["bounds_mm"]
    by_ref = {item["ref"]: item for item in payload["components"]}
    result = []
    for metadata in ALL_PARTS:
        part = dict(metadata)
        placed = by_ref.get(part["ref"])
        if placed is None:
            continue  # Missing parts are issues, never historical-position fallbacks.
        else:
            part["x"], part["z"] = board_to_blender(
                *placed["position_mm"], bounds,
                center_x_mm=0.0, center_z_mm=BOARD["center_z"])
            part["side"] = placed["side"]
            part["rotation_deg"] = placed["rotation_deg"]
            part["footprint"] = placed["footprint"]
            part["placement_state"] = "FROM_CANONICAL_KICAD"
        result.append(part)
    return tuple(result)


ENGINEERING_PARTS = engineering_parts()
