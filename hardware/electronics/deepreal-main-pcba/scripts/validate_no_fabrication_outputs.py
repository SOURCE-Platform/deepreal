#!/usr/bin/env python3
"""Fail if a fabrication-release artifact appears during the review-draft phase."""

from pathlib import Path
import sys


PROJECT = Path(__file__).resolve().parent.parent
FORBIDDEN_SUFFIXES = {".gbr", ".ger", ".drl", ".pos", ".job"}
FORBIDDEN_NAMES = {"gerbers", "fabrication", "pick-and-place", "pick_place"}


def main():
    found = []
    for path in PROJECT.rglob("*"):
        if not path.is_file():
            continue
        if path.relative_to(PROJECT).parts[0] == "scripts":
            continue
        lowered = path.name.lower()
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            found.append(path)
        elif any(token in lowered for token in FORBIDDEN_NAMES):
            found.append(path)
    if found:
        raise RuntimeError("fabrication outputs are prohibited:\n" +
                           "\n".join(str(path) for path in found))
    print("PASS: no Gerber, drill, placement, or fabrication-release artifacts exist")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("FAIL:", error, file=sys.stderr)
        raise
