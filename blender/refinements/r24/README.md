# R24 finished exterior

This revision completes the visible enclosure shape for the DeepReal website concept. The enclosure is one connected mesh with a flat roof spanning both drums, a rounded rear transition, a vertical back, a smooth lower rear corner, and integrated left, center, and right supports. The interaction drum is saved in a 22.5° downward pose for the website view.

## Files

- `deepreal-finished-exterior-r24.blend` — editable exterior model.
- `deepreal-website-presentation-r24.blend` — same model with the hero camera and studio lighting saved.
- `r24-website-hero-dark.png` — website render on a dark background, 1800 × 1125.
- `r24-website-hero-transparent.png` — same render with an alpha channel.
- `r24-front-preview.png`, `r24-side-preview.png`, `r24-above-preview.png` — review views.
- `r24-enclosure-check.json` — mesh and sampled rotation checks.

Rebuild the model with `blender -b -t 4 --python build_r24.py`, check it with `blender -b -t 4 --python check_r24.py`, and render the website assets with `blender -b -t 8 --python render_website_r24.py`.

The appearance is ready for review. Parting seams, snap features, installation sequence, and production clearances are deferred.
