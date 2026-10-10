# R38 exterior mount and cable appearance

R38 starts from R36, preserving its drums, supports, and exposed-top
silhouette. The narrow R30 40 × 13 mm housing-colored pad is absorbed into a
continuous inner enclosure leg, extended to Y = 3.5 mm across the device.
A distinct satin-metal **112 × 26 mm** device-side magnetic face, centered at
Z = −14 mm, sits directly on that leg. It matches the R32 laptop-side target
plate in width, height and position. There is no separate mount riser. The
provisional 0.9 mm face, 0.35 mm air gap, 0.35 mm laptop plate and 0.40 mm
tape keep the R30 nominal mount plane; the ledge depth is now 5.0 mm at its
inner leg rather than 7.0 mm.

The USB cable's visual outer diameter changes from 4.0 to 3.2 mm. The plug
has a longer hard molded handle with a rounded V-taper, a subtle vertical
DeepReal wordmark, then a **distinct, straight-sided sleeve**
over the cable jacket. The sleeve reads as a separate piece rather than the
entire handle narrowing to cable diameter. The website viewer fades the free
end; the Blender cable itself has no physical fade.

Neither the sleeve's retention/bend performance, cable specification nor
magnetic force, material, embedding, adhesive, hinge load, enclosure
wall/volume changes, tolerances and laptop fit have been validated. The
magnetic face has a dark satin finish for visual distinction; that finish
does not establish the magnet's physical material or construction.

Build and export from the DeepReal repository root:

```sh
blender -b -t 4 --python-exit-code 1 --python blender/refinements/r38/build_r38.py
blender -b -t 4 --python-exit-code 1 --python blender/refinements/r38/render_plug_r38.py
blender -b -t 4 blender/refinements/r38/deepreal-exterior-mount-r38.blend \
  --python-exit-code 1 --python blender/export_web_exterior.py
```
