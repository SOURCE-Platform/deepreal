# PCB browser materials, 2026-10-13

## Current appearance

The board detail is a CAD review, not a photorealistic finish.

The detailed main-board GLB has 18 solid-color PBR materials and **no image
textures**. Pads and silkscreen are geometry, not painted detail. The mask is
dark green, non-metallic, with uniform roughness 0.5. The substrate uses one
matte olive material (roughness 0.8) across its faces and cut edges. It has
no separate edge material or texture coordinates. There is no glass-fiber
grain, machining variation, normal map, roughness map or ambient-occlusion map.

The two head-board proxies use one green, non-metallic material with roughness
0.43 for both faces and edges. They also have no texture coordinates or image
maps. They are outline proposals, not populated native PCB layouts.

The assembly's four image textures belong to the illustrated amber flex
materials, not to a realistic PCB finish or released copper routing.

Some imported component materials need physical classification. For example,
the dark housing and colored regions of the optical connector, the USB
connector's dark insert, and the resistor's dark body have no explicit
metallic factor. glTF defaults that factor to 1. This is not an appropriate
assumption for a plastic or ceramic body. Correcting material categories
matters more than covering those surfaces with elaborate image textures.

The browser already uses physically based materials, a generated room-light
environment, ACES tone mapping and directional/ambient light. It does not
enable contact shadows or use an AO map. Uniform surface response and the
lack of small contact shadows make close-ups look flatter than photographs.
The 18 missing-model envelopes are another visible limitation that texture
cannot resolve.

## Recommended order

1. Settle visible geometry and replace the important missing package models
   with traceable CAD. Keep the electrical and package-fit limitations visible.
2. Correct material categories: dielectric resin/plastic/ceramic versus
   metallic contacts and connector shells. Calibrate mask, substrate and
   silkscreen colors/roughness under consistent lighting.
3. Give cut edges their own material assignment and physically scaled
   UVs. Use restrained laminate/fiber grain and machining roughness, not
   conspicuous stripes or painted copper. This preparation can happen before
   the final texture polish.
4. Add subtle mask and edge normal/roughness maps, contact shading and suitable
   lighting. Bake Blender-only procedural effects into glTF-supported maps;
   arbitrary Blender shader nodes do not transfer automatically.
5. Check angled close-ups and full-device views on desktop and mobile. Use
   reusable, modest-size maps and mipmaps, then measure loading, frame rate and
   memory before increasing texture resolution or adding expensive effects.

Final edge polish belongs late in the appearance pass. Basic material
classification should happen earlier. Layer counts, copper bands, finish,
solder fillets, routing and component markings must not be invented to make
the board look finished.

No PCB texture or material was changed in this assessment. The browser can
render substantially more realistic surfaces, but that needs material and
geometry work, not a higher-quality rendering switch alone.
