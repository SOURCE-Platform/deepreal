# R31 decorative laptop target plate

Open `deepreal-logo-mount-plate-review-r31.blend`. Its saved camera faces the
back of the laptop lid, with DeepReal removed so the plate and logo are visible.
The existing R30 device and enclosure files are unchanged.

The visual study uses the supplied `assets/deepreal-logo-v0.svg` on a 110 × 16 mm
steel target near the lid's top edge. A separate 106 × 14 × 0.4 mm foam sticker
sits between the plate and the 3 mm laptop-lid proxy. The steel target is shown
as 0.35 mm thick to match the earlier provisional mounting stack. Its grade,
thickness, attachment strength, and laptop fit remain unverified.

The logo is a dark laser-mark appearance made from the SVG curves. It is **not**
a fabrication-ready engraved or debossed cut: physical recess depth and minimum
line width need a manufacturing sample. A 430 ferritic stainless finish is a
material candidate, represented here by a satin steel shader.

- `r31-laptop-back.png`: saved rear-view camera and overall placement.
- `r31-full-width-plate.png`: closer view of the plate across the attachment zone.
- `r31-logo-and-foam-detail.png`: angled logo and plate-edge view.
- `r31-attachment-layers-exploded.png`: illustration with the plate lifted from
  the foam sticker; this is a render pose, not the assembled file state.
- `build_mount_plate.py`: repeatable Blender build and render script.

This file reviews the laptop-side target only. The R30 device-side 40 mm magnet
pad has not yet been updated to match the wider attachment concept.
