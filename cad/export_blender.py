#!/usr/bin/env python3
"""
DeepReal CAD -> Blender mesh exporter.

Tessellates every generated shape and writes, under blender/assets/:

    parts/<ObjectName>.stl   binary STL, millimetres, Z-up (Blender is
                             also Z-up, so the Blender side only needs a
                             x0.001 mm->m scale, no axis rotation)
    manifest.json            the contract consumed by blender/build_scene.py:
                             per-part name/group/kind/colour/bbox/triangle
                             count plus every resolved parameter, so the
                             render-side code (MacBook model, mounting
                             stack) is sized from the same numbers as the
                             CAD instead of eyeballing them

Reads geometry through document.generated_shape_map() in memory; the
saved deepreal.FCStd is neither opened nor modified.

Run headless from the repository root:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cad/export_blender.py

freecadcmd executes this file with __name__ set to the module name, not
"__main__", so main() is invoked unconditionally at import time. Do not
import this module; import document.py instead.
"""

import json
import math
import os
import struct
import subprocess
import sys

# Make sibling modules importable whether this file is run by freecadcmd
# from the repo root, or exec'd from the FreeCAD GUI console.
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.getcwd()
    if not os.path.exists(os.path.join(HERE, "parameters.py")):
        HERE = os.path.join(HERE, "cad")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402

import document   # noqa: E402
import parameters # noqa: E402

REPO_ROOT = os.path.dirname(HERE)
ASSETS_DIR = os.path.join(REPO_ROOT, "blender", "assets")
PARTS_DIR = os.path.join(ASSETS_DIR, "parts")
MANIFEST_PATH = os.path.join(ASSETS_DIR, "manifest.json")

# Chordal deviation for tessellation. 0.01 mm keeps silhouettes visually
# exact even in close-up product shots (cylinders tessellate to ~80
# segments) while meshes stay small.
TESSELLATE_TOLERANCE_MM = 0.01

# Chordal deviation when discretising the Main_Housing Y-Z profile
# polyline. The Blender side re-extrudes this profile into a clean
# quad/n-gon prism, so this controls how faithfully the rear-arm arc
# survives the CAD -> Blender hop.
PROFILE_DEFLECTION_MM = 0.005


def _classify(name):
    """Render-side role of an object, from the naming conventions."""
    if name.endswith("_Orientation_Reference"):
        return "debug-mark"
    if "Reference" in name:
        return "reference"
    return "product"


def _git_commit():
    """Short commit hash for manifest provenance, or None outside git."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None


def _facet_normal(a, b, c):
    """Unit normal of triangle (a, b, c), or the zero vector if degenerate."""
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0.0:
        return (0.0, 0.0, 0.0)
    return (nx / length, ny / length, nz / length)


def write_binary_stl(path, shape):
    """Tessellate `shape` and write one binary STL in millimetres.

    Returns the triangle count. FreeCAD's Shape.tessellate() returns
    (points, facets) with 1-based facet indices.
    """
    points, facets = shape.tessellate(TESSELLATE_TOLERANCE_MM)
    vertices = [(p.x, p.y, p.z) for p in points]
    with open(path, "wb") as handle:
        handle.write(b"DeepReal CAD export, mm, Z-up".ljust(80, b"\0"))
        handle.write(struct.pack("<I", len(facets)))
        pack = struct.Struct("<12fH").pack
        for i, j, k in facets:
            a = vertices[i - 1]
            b = vertices[j - 1]
            c = vertices[k - 1]
            handle.write(pack(*_facet_normal(a, b, c),
                              *a, *b, *c, 0))
    return len(facets)


def main():
    params = parameters.resolve(parameters.get_params())
    shapes = document.generated_shape_map(params)

    os.makedirs(PARTS_DIR, exist_ok=True)
    parts = []
    for name in sorted(shapes):
        shape, group = shapes[name]
        style = document.OBJECT_STYLES.get(name, {})
        stl_name = name + ".stl"
        triangles = write_binary_stl(os.path.join(PARTS_DIR, stl_name), shape)
        bb = shape.BoundBox
        parts.append({
            "name": name,
            "group": group,
            "kind": _classify(name),
            "stl": "parts/" + stl_name,
            "triangles": triangles,
            "volume_mm3": shape.Volume,
            "bbox_mm": {
                "min": [bb.XMin, bb.YMin, bb.ZMin],
                "max": [bb.XMax, bb.YMax, bb.ZMax],
            },
            "color": list(style.get("color", (0.8, 0.8, 0.8))),
            "transparency": style.get("transparency", 0),
        })
        print("  {:<44} {:>6} tris  [{:.1f} x {:.1f} x {:.1f}] mm".format(
            name, triangles, bb.XLength, bb.YLength, bb.ZLength))

    # Main_Housing Y-Z profile polyline: the housing is one profile
    # extruded along X, so the Blender side can rebuild it as a clean
    # quad-wall / n-gon-cap prism that is dimensionally identical to the
    # CAD solid (verified by volume there). Slice the solid at X = 0.
    manifest_profiles = {}
    housing_shape, _group = shapes["Main_Housing"]
    wires = housing_shape.slice(App.Vector(1, 0, 0), 0.0)
    if len(wires) != 1:
        raise RuntimeError(
            "Main_Housing X=0 slice produced {} wires (expected 1)".format(
                len(wires)))
    points = wires[0].discretize(Deflection=PROFILE_DEFLECTION_MM)
    manifest_profiles["Main_Housing"] = {
        "plane": "YZ at X=0",
        "points_yz_mm": [[p.y, p.z] for p in points],
    }
    print("  Main_Housing profile: {} points".format(len(points)))

    manifest = {
        "units": "mm",
        "up": "Z",
        "tessellate_tolerance_mm": TESSELLATE_TOLERANCE_MM,
        "source_commit": _git_commit(),
        "params": params,
        "parts": parts,
        "profiles": manifest_profiles,
    }
    with open(MANIFEST_PATH, "w") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("Wrote {} parts + manifest: {}".format(
        len(parts), os.path.relpath(MANIFEST_PATH, REPO_ROOT)))


try:
    main()
# freecadcmd quirks: an unhandled exception makes it run the script a
# second time and still exit 0, and sys.exit() drops buffered stdout.
# Catch everything, flush explicitly, and exit with a real status code.
except SystemExit:
    raise
except Exception:
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(1)
