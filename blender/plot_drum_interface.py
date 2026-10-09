#!/usr/bin/env python3
"""Draw an end-on explanation of the measured R30 drum interface conflict."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT = ROOT / "docs/electrical/drum-interface-measurement-2026-10-09.json"
OUTPUT = ROOT / "docs/electrical/drum-interface-measurement-2026-10-09.png"


def base_axis(ax, title):
    ax.add_patch(Circle((0, 0), 12, facecolor="#dce4e9",
                        edgecolor="#324b57", linewidth=2))
    ax.add_patch(Circle((0, 0), 2, facecolor="#a4b3bb",
                        edgecolor="#324b57", linewidth=1.5))
    ax.axhline(0, color="#728892", lw=.6)
    ax.axvline(0, color="#728892", lw=.6)
    ax.plot(0, 0, marker="+", ms=12, mew=2, color="#163b50")
    ax.set(xlim=(-14, 14), ylim=(-14, 14), aspect="equal", title=title,
           xlabel="Y from drum axis (mm)", ylabel="Z from drum axis (mm)")
    ax.grid(alpha=.16)


def main():
    data = json.loads(MEASUREMENT.read_text())
    face = data["drums"]["Face"]
    axis = face["pivot_center_xyz_mm"]
    magnet = face["magnet_center_xyz_mm"]
    relative_y = magnet[1] - axis[1]
    relative_z = magnet[2] - axis[2]
    width = data["outer_exit_screen"]["connector_fpc_end_width_mm"]
    bore = data["outer_exit_screen"]["spindle_bore_diameter_mm"]

    fig, plots = plt.subplots(1, 2, figsize=(12.8, 6.5), layout="constrained")
    fig.set_facecolor("#f7f9fa")
    for ax in plots:
        ax.set_facecolor("#f7f9fa")
    base_axis(plots[0], "Angle sensor location now modeled")
    plots[0].add_patch(Circle((relative_y, relative_z), 1,
                              facecolor="#e78d68", edgecolor="#8e432d", lw=1.5))
    plots[0].plot(relative_y, relative_z, marker="x", ms=10, mew=2,
                  color="#392c2a")
    plots[0].annotate("Magnet + sensor envelope\n6.0 mm off axis",
                      xy=(relative_y, relative_z), xytext=(3, 8),
                      arrowprops={"arrowstyle": "->", "color": "#8e432d"},
                      fontsize=10, color="#653625")
    plots[0].annotate("Drum axis", xy=(0, 0), xytext=(-11, -7),
                      arrowprops={"arrowstyle": "->", "color": "#163b50"},
                      fontsize=10, color="#163b50")

    base_axis(plots[1], "Proposed optical flex through outer spindle")
    plots[1].add_patch(Circle((0, 0), bore / 2, facecolor="#f7f9fa",
                              edgecolor="#142f3f", linewidth=2))
    plots[1].add_patch(Rectangle((-width / 2, -.35), width, .7,
                                  facecolor="#ddaa5b", edgecolor="#765728",
                                  alpha=.9))
    plots[1].annotate(f"51-contact FPC end: {width:g} mm wide",
                      xy=(width / 2, 0), xytext=(1, 7),
                      arrowprops={"arrowstyle": "->", "color": "#765728"},
                      fontsize=10, color="#5c4528")
    plots[1].annotate(f"Spindle bore: Ø{bore:g} mm",
                      xy=(0, -bore / 2), xytext=(-12, -7),
                      arrowprops={"arrowstyle": "->", "color": "#163b50"},
                      fontsize=10, color="#163b50")
    fig.suptitle("R30 / R21 drum interface: measured geometry, end view",
                 fontsize=15, weight="bold", color="#173746")
    fig.savefig(OUTPUT, dpi=170, bbox_inches="tight", pad_inches=.18)
    print("WROTE", OUTPUT)


if __name__ == "__main__":
    main()
