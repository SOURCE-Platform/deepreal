#!/bin/sh
# Start the DeepReal CAD development session in FreeCAD.
#
# Opens deepreal.FCStd, rebuilds geometry from the Python source, forces
# all generated objects visible, restores the review camera, and starts
# the live-reload watcher on the cad/*.py geometry sources.
#
# No global FreeCAD configuration is installed or modified.
set -eu

CAD_DIR="$(cd "$(dirname "$0")" && pwd)"
FREECAD="/Applications/FreeCAD.app/Contents/Resources/bin/freecad"

if [ ! -x "$FREECAD" ]; then
    echo "FreeCAD not found at $FREECAD" >&2
    exit 1
fi

exec "$FREECAD" "$CAD_DIR/start_dev.py"
