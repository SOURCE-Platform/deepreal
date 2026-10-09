#!/usr/bin/env python3
"""Draw the R30 side-section dimensions from the provisional mount stack."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "r30-monitor-mount-section.png"


def block(ax, rear_y, front_y, bottom_z, top_z, color, label):
    patch = Rectangle((-rear_y, bottom_z), rear_y - front_y,
                      top_z - bottom_z, facecolor=color,
                      edgecolor="#273642", linewidth=1.1, label=label)
    ax.add_patch(patch)


def dimension(ax, x0, x1, z, label, label_z):
    ax.annotate("", xy=(x0, z), xytext=(x1, z),
                arrowprops={"arrowstyle": "<->", "color": "#304b5b",
                            "linewidth": 1.2})
    ax.text((x0 + x1) / 2, label_z, label, ha="center", va="center",
            fontsize=10, color="#203843",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})


def main():
    fig, ax = plt.subplots(figsize=(10, 8), dpi=180)
    fig.patch.set_facecolor("#f7fafb")
    ax.set_facecolor("#f7fafb")
    body = [(-5.5, -29), (-22.5, -29), (-22.5, 20),
            (-11.7, 20), (-11.7, 6.8), (1.5, 6.8),
            (1.5, 0), (-5.5, 0)]
    ax.add_patch(Polygon(body, closed=True, facecolor="#d3dce1",
                         edgecolor="#243947", linewidth=1.7,
                         label="Enclosure and top ledge"))
    block(ax, 5.5, 3.5, -14, -1, "#9cb7c3", "Integral magnet pad")
    block(ax, 3.5, 2.6, -13, -1, "#cb8057", "0.90 mm device magnet")
    block(ax, 2.25, 1.9, -13, -1, "#84939c", "0.35 mm steel plate")
    block(ax, 1.9, 1.5, -13, -1, "#efce87", "0.40 mm foam tape")
    block(ax, 1.5, -1.5, -17, 0, "#39576a", "3.0 mm display lid")
    ax.add_patch(Rectangle((-2.6, -13), .35, 12,
                           facecolor="#edf4f6", hatch="///",
                           edgecolor="#78909c", linewidth=1,
                           label="0.35 mm air gap"))

    dimension(ax, -5.5, 1.5, 8.1, "7.0 mm ledge depth", 9.25)
    dimension(ax, -3.5, -1.5, -15.4, "2.0 mm attachment stack", -16.45)
    ax.text(-3.5, 2.2, "Top of monitor", ha="left", fontsize=10,
            color="#304b5b")
    ax.plot([-3.5, 0], [1.9, 0], color="#69808d", linewidth=1)
    ax.set_xlim(-8, 5)
    ax.set_ylim(-18, 10.8)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("DeepReal monitor-top ledge · R30 section",
                 fontsize=17, loc="left", pad=18, color="#203843")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, -.18),
              ncol=2, frameon=False, fontsize=9)
    fig.text(.07, .025,
             "Reference stack from mounting_stack.py; magnet, adhesive, and production clearances remain provisional.",
             fontsize=9, color="#596e79")
    fig.subplots_adjust(left=.06, right=.97, top=.90, bottom=.20)
    fig.savefig(OUTPUT, dpi=180, facecolor=fig.get_facecolor())
    print(OUTPUT)


if __name__ == "__main__":
    main()
