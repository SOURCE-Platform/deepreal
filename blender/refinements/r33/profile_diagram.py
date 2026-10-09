#!/usr/bin/env python3
"""Draw the actual R32/R33 groove equations as comparable cross-sections."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "r33-profile-comparison.png"
SCALE = 3
WIDTH, HEIGHT = 1600, 650
RADIUS, DEPTH = .95, .15


def font(size, bold=False):
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    path = Path("/System/Library/Fonts/Supplemental") / name
    return ImageFont.truetype(str(path), size * SCALE)


def groove(distance, profile):
    u = max(0, 1 - abs(distance) / RADIUS)
    return DEPTH * (u * u if profile == "creased" else
                    u * u * (3 - 2 * u))


def panel(draw, x0, title, subtitle, profile):
    sx, top, bottom = SCALE, 205 * SCALE, 455 * SCALE
    xleft, xright = (x0 + 80) * sx, (x0 + 690) * sx
    center = (xleft + xright) / 2
    mm_to_px = 230 * sx
    depth_to_px = 135 * sx
    profile_points = []
    for px in range(int(xleft), int(xright) + 1):
        distance = (px - center) / mm_to_px
        profile_points.append((px, top + groove(distance, profile) /
                               DEPTH * depth_to_px))
    polygon = profile_points + [(xright, bottom), (xleft, bottom)]
    draw.polygon(polygon, fill="#e7eef1")
    draw.line(profile_points, fill="#284852", width=4 * sx, joint="curve")
    draw.line([(xleft, bottom), (xright, bottom)], fill="#284852",
              width=3 * sx)
    draw.line([(xleft, top), (xleft, bottom)], fill="#284852", width=3 * sx)
    draw.line([(xright, top), (xright, bottom)], fill="#284852", width=3 * sx)
    draw.text(((x0 + 80) * sx, 65 * sx), title, font=font(34, True),
              fill="#213842")
    draw.text(((x0 + 80) * sx, 115 * sx), subtitle, font=font(22),
              fill="#54707a")
    draw.line([(center, (top + depth_to_px + 13 * sx)),
               (center, 515 * sx)], fill="#6a919f", width=2 * sx)
    label = "smooth bottom" if profile == "rounded" else "deepest logo line"
    draw.text((center - 93 * sx, 525 * sx), label, font=font(20),
              fill="#54707a")


canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "#f7f9f9")
pen = ImageDraw.Draw(canvas)
panel(pen, 0, "R32 · rounded bottom", "Current smooth trough", "rounded")
panel(pen, 800, "R33 · central crease", "Requested pressed line", "creased")
pen.text((80 * SCALE, 602 * SCALE),
         "Same 0.15 mm depth and 0.95 mm shoulder; only the center shape changes.",
         font=font(20), fill="#54707a")
canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(OUT)
print(OUT)
