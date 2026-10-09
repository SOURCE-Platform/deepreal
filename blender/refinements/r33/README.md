# DeepReal creased press profile — R33

This is the requested profile revision of the R32 laptop target plate. The
plate and logo dimensions remain 112 × 26 mm and 103 mm wide, respectively.
The 0.15 mm pressed depth and 0.95 mm shoulder radius also remain the same.

The logo line is now a narrow crease at the deepest point. The shoulder
curves return smoothly to the original plate height. The R32 rounded-bottom
comparison is preserved in its own `.blend` and renders.

Build with:

```sh
/opt/homebrew/bin/blender -b --python blender/refinements/r33/build_creased_plate.py
```

This models the intended appearance, not the tool or forming behavior of a
specific steel stock. Production depth and crease radius need prototyping.

## Material direction

The appearance study uses satin 430 ferritic stainless steel (EN 1.4016).
The grade is magnetizable and supplied as cold-rolled sheet. A forming grade
such as Aperam K30ED is another candidate for pressed artwork. The 0.35 mm
sheet and 0.15 mm modeled crease are provisional; a physical sample must
check forming, flatness, adhesive contact, finish, corrosion, and magnetic
holding force.

- [Outokumpu Moda range datasheet](https://www.outokumpu.com/-/media/files/products/moda/outokumpu-moda-range-datasheet.pdf)
- [Aperam K30/K30ED technical sheet](https://www.aperam.com/sites/default/files/documents/FT_K30-K30ED_en_web.pdf)

## Moving-light study

`animate_sheen.py` loads the saved R33 Blender file and animates a strip
light across the logo. The script produces PNG frames in `sheen-frames/`;
`r33-moving-sheen.mp4` is the cropped, three-second H.264 review export.
`deepreal-creased-logo-light-sweep-r33.blend` has the editable light
keyframes. The material shader is an illustrative satin finish, not a measured
sample of a particular supplier's sheet.
