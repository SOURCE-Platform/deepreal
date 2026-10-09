#!/usr/bin/env python3
"""Render the narrow-crease profile requested for the DeepReal plate."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r32"))

import build_pressed_plate as build  # noqa: E402

build.HERE = HERE
build.MODEL = HERE / "deepreal-creased-logo-plate-review-r33.blend"
build.RENDER_PREFIX = "r33"
build.pressed.PROFILE = "creased"

if __name__ == "__main__":
    build.main()
