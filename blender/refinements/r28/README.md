# R28 three-divider enclosure

The left, center, and right dividers now extend forward around the drum ends and join the partial roof and lower enclosure as one shell. The roof profile retains its nominal 0.5 mm clearance above the rotating drums. This is an exterior appearance study; production tolerances, assembly splits, and fasteners remain open.

Open `deepreal-divider-review-r28.blend` to inspect the assembled model. `deepreal-three-divider-enclosure-r28.blend` is the source scene.

- `r28-three-dividers-shell.png`: direct front view of the shell alone.
- `r28-three-dividers-assembled.png`: direct front view with the drums.
- `r28-connected-shell.png`: perspective view of the shell alone.
- `r28-assembled-preview.png`: perspective view with the drums.
- `r28-enclosure-check.json`: one mesh component, zero nonmanifold edges, and no triangle intersections in six sampled drum poses.

Regenerate with `build_r28.py`, render with `render_r28.py`, and validate with `check_r28.py` in Blender background mode.
