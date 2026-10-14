#!/usr/bin/env python3
"""Plot the measured fit candidate and unresolved body-box overlaps."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a new figure path")
    contract = json.loads(args.contract.read_text())
    report = json.loads(args.report.read_text())
    if hashlib.sha256(args.contract.read_bytes()).hexdigest() != report["mechanical_contract_sha256"]:
        raise ValueError("report/contract mismatch")
    if report["viewer_integration_allowed"] is not False:
        raise ValueError("figure must remain a blocked diagnostic")
    bodies = report.get("retained_component_bodies", contract["retained_component_bodies"])
    flagged = {ref for pair in report["body_aabb_overlap_candidates"] for ref in pair["refs"]}
    connector_study = report.get("schema") == "deepreal.pcb-connector-candidate.v1"
    fig, axes = plt.subplots(2, 1, figsize=(15, 10))
    fig.subplots_adjust(left=0.065, right=0.985, top=0.90, bottom=0.13, hspace=0.42)
    title = ("MECH-FIT-02: J2/J3 rotation and inset, full fit blocked"
             if connector_study else
             "MECH-FIT-01: wing outline aligned, component placement not corrected")
    fig.suptitle(title,
                 fontsize=17, fontweight="bold")
    for ax, side in zip(axes, ("TOP", "BOTTOM")):
        ax.add_patch(Polygon(contract["profile_loops_web_mm"][0],
                             facecolor="#e4efe7", edgecolor="#316346", linewidth=1.6))
        ax.add_patch(Rectangle((-45, -25.5), 90, 28, fill=False,
                               edgecolor="#77818c", linestyle="--", linewidth=1))
        for loop in contract["profile_loops_web_mm"][1:]:
            ax.add_patch(Polygon(loop, facecolor="white", edgecolor="#316346", linewidth=0.8))
        for ref, item in sorted(bodies.items()):
            if item["side"] != side:
                continue
            lo, hi = item["min_mm"], item["max_mm"]
            color = "#bd3644" if ref in flagged else "#65727e"
            ax.add_patch(Rectangle(lo[:2], hi[0] - lo[0], hi[1] - lo[1],
                                   edgecolor=color, facecolor=color, alpha=0.22,
                                   linewidth=0.65))
            if ref[0] in "UJL" or ref in flagged:
                ax.text(*item["center_mm"][:2], ref, fontsize=6.7,
                        ha="center", va="center", color="#952030" if ref in flagged else "#263642")
        for ref, item in contract["interfaces"].items():
            if ref == "usb_plug_shell" or (ref == "J1") != (side == "BOTTOM"):
                continue
            lo, hi = item["min_mm"], item["max_mm"]
            ax.add_patch(Rectangle(lo[:2], hi[0] - lo[0], hi[1] - lo[1],
                                   edgecolor="#245fb7", fill=False, linestyle="--",
                                   linewidth=1.5))
            ax.text(item["center_mm"][0], lo[1] - 1, ref + " target",
                    fontsize=7.5, ha="center", color="#245fb7")
        ax.set(xlim=(-48, 61), ylim=(-34, 5), aspect="equal",
               xlabel="Device X (mm)", ylabel="Device height (mm)",
               title=side.title() + " population, same device coordinates (bottom not mirrored)")
        ax.grid(alpha=0.15)
    scope = ("J2/J3 quarter-turned and inset; other bodies unchanged. No routing. "
             "Body boxes are transformed retained models, not a fresh solid import."
             if connector_study else "No parts moved, no routing added.")
    fig.text(0.5, 0.018,
             "Green: measured outline. Gray dashed: old 90 mm rectangle. Blue: unselected mechanical connector envelopes.\n"
             "Red: conservative 3D body-box overlap candidates, not exact solid collisions.\n" + scope,
             ha="center", fontsize=10)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
