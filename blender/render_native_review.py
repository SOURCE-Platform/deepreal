"""Internal review renders only: no website release or fabrication claim."""

from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pcba_native_import import checked_inputs
from pcba_render_settings import configure

VIEWS = (
    ("06 PCBA Top", "main-top", 3200, 1440),
    ("07 PCBA Bottom", "main-bottom", 3200, 1440),
    ("08 PCBA Dimensioned", "main-dimensioned", 3200, 1760),
    ("04 Electronics Exploded", "electronics-exploded", 1800, 1238),
    ("05 Shield Cutaway", "shield-cutaway", 1800, 1238),
    ("02 Housing Removed", "installed-review", 1800, 1238),
)


def main():
    checked_inputs()
    output = HERE / "review-output"
    output.mkdir(exist_ok=True)
    requested = set(sys.argv[sys.argv.index("--")+1:]) if "--" in sys.argv else set()
    if requested - {v[1] for v in VIEWS}:
        raise ValueError("unknown review view")
    for name, stem, width, height in VIEWS:
        if requested and stem not in requested:
            continue
        scene = bpy.data.scenes[name]
        bpy.context.window.scene = scene
        bpy.context.view_layer.update()
        configure(scene)
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(output / (stem + ".png"))
        # Burn the restriction into every view, including device scenes.
        scene.render.use_stamp = True
        scene.render.use_stamp_note = True
        scene.render.stamp_note_text = "INTERNAL ENGINEERING REBUILD - NOT FOR PUBLICATION - UNVERIFIED PLACEMENT"
        scene.render.use_stamp_date = False
        scene.render.use_stamp_time = False
        scene.render.use_stamp_frame = False
        scene.render.use_stamp_filename = False
        scene.render.stamp_font_size = 16
        bpy.ops.render.render(write_still=True)
        print("INTERNAL REVIEW:", scene.render.filepath, flush=True)


if __name__ == "__main__":
    main()
