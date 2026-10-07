#!/usr/bin/env python3
"""Plot illustrative desk visibility as distance divided by camera height."""

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
PNG = HERE / "r20-interaction-desk-coverage.png"
REPORT = HERE / "r20-desk-coverage.json"
ROWS = [
    ("Wide, straight", 67, 0, "#2c7f83"),
    ("Wide, 22.5° down", 67, 22.5, "#2c7f83"),
    ("Wide, 45° down", 67, 45, "#2c7f83"),
    ("Standard, 45° down", 41, 45, "#bd784b"),
]
PLOT_LIMIT = 5.5


def interval(vertical_fov, tilt):
    upper = tilt - vertical_fov / 2
    lower = tilt + vertical_fov / 2
    near = 0 if lower >= 90 else 1 / math.tan(math.radians(lower))
    far = None if upper <= 0 else 1 / math.tan(math.radians(upper))
    return near, far


def main():
    fig, ax = plt.subplots(figsize=(9, 4.3), dpi=180)
    results = []
    for index, (label, fov, tilt, color) in enumerate(ROWS):
        near, far = interval(fov, tilt)
        ax.barh(index, min(far or PLOT_LIMIT, PLOT_LIMIT) - near,
                left=near, height=.55, color=color)
        results.append({"pose": label, "vertical_fov_deg": fov,
                        "optical_down_deg": tilt,
                        "near_distance_over_height": round(near, 3),
                        "far_distance_over_height": (
                            round(far, 3) if far is not None else None)})
    ax.set_yticks(range(len(ROWS)), [row[0] for row in ROWS])
    ax.invert_yaxis()
    ax.set_xlim(0, PLOT_LIMIT)
    ax.set_xlabel("Horizontal desk distance from camera ÷ camera height")
    ax.set_title("Geometric desk coverage of the RGB lens")
    ax.grid(axis="x", alpha=.2)
    ax.set_axisbelow(True)
    ax.text(.99, -.23, "Beyond chart: coverage continues for straight and 22.5° poses",
            transform=ax.transAxes, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(PNG, bbox_inches="tight")
    plt.close(fig)
    REPORT.write_text(json.dumps({
        "basis": "Flat desk below camera; optic level; no housing, lens distortion, focus, or depth-system overlap modeled.",
        "source_vertical_fov_deg": {"standard": 41, "wide": 67},
        "rows": results,
        "directly_below_requires_at_least_deg": {
            "wide": 56.5, "standard": 69.5},
    }, indent=2) + "\n")
    print(PNG)
    print(REPORT)


if __name__ == "__main__":
    main()
