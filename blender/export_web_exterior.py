#!/usr/bin/env python3
"""Export the current reviewed exterior and USB pigtail for the SOURCE site."""

import os
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_export_common import export_glb, require_r38_source, stage_meshes, write_manifest

OUTPUT = Path(os.environ.get(
    "DEEPREAL_WEB_OUT",
    str(Path(__file__).resolve().parents[2] / "source-public-site/public/models/deepreal.glb"),
))
MANIFEST = OUTPUT.with_name("deepreal-exterior-manifest.json")

HOUSING = "R30_One_Piece_Enclosure"
MAGNET = "R38_Device_Magnet_Face_CONCEPT"
DRUMS = ("Face_Sensor_Head", "Interaction_Sensor_Head")
USB = (
    "USB_C_Cable",
    "USB_C_Plug_Overmold",
    "R38_USB_Molded_Handle_Taper",
    "R38_USB_Cable_Sleeve",
    "R38_USB_DeepReal_Wordmark",
    "USB_C_Male_Metal_Shell",
    "USB_C_Male_Internal_Insert",
    "USB_C_Male_Contact_Tongue",
)


def source_objects():
    require_r38_source()
    names = [HOUSING, MAGNET, *DRUMS, *USB]
    names.extend(sorted(
        obj.name for obj in bpy.data.objects
        if obj.type == "MESH"
        and (obj.name.startswith("Face_Drum_Lens_")
             or obj.name.startswith("Interaction_Drum_Lens_"))
    ))
    missing = [name for name in names if name not in bpy.data.objects]
    if missing:
        raise RuntimeError("Missing exterior objects: " + ", ".join(missing))
    return [bpy.data.objects[name] for name in names]



def main():
    source = require_r38_source()
    staged = stage_meshes(source_objects(), "WEB EXPORT — EXTERIOR + USB")
    export_glb(OUTPUT, staged)
    write_manifest(MANIFEST, source, OUTPUT, {
        "milestone": "website exterior with matching magnetic face and visible USB cable",
        "objects": [obj.name for obj in staged],
        "status": "appearance model; magnetic mount, cable, internal wiring and fabrication remain open",
    })


if __name__ == "__main__":
    main()
