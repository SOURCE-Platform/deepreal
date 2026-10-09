# R27 integrated enclosure review

This appearance model joins the contoured partial roof, the left and right side supports, the center island, and the lower enclosure into one continuous mesh. The roof and supports retain the nominal 0.5 mm radial gap around the drums. Assembly splits, fasteners, and production tolerances are intentionally deferred.

Open `deepreal-support-review-r27.blend` for the assembled presentation view. `deepreal-integrated-three-supports-r27.blend` is the source model without review lighting changes.

- `r27-connected-shell.png` shows the enclosure by itself, so the three roof-to-body connections are visible.
- `r27-assembled-preview.png` shows the same enclosure with both drums installed.
- `r27-connected-shell-low.png` shows the shell from a lower angle.
- `r27-enclosure-check.json` records mesh continuity and six sampled drum positions.

Regenerate the model with `blender -b -t 4 --python build_r27.py`; render with `render_r27.py`; check with `check_r27.py`.
