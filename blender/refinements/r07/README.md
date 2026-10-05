# DeepReal enclosure refinement R07

R07 fixes the USB packaging intersections visible in R06 and changes the
housing control from hide/show to a solid/wireframe viewport toggle.

## Housing mode toggle

In the Outliner, click the **eye** on:

`00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME`

- Eye on: the solid housing is visible and occludes the inset wire copy.
- Eye off: the solid housing disappears and the wireframe housing remains.

Keep `00A — WIREFRAME FALLBACK — KEEP VISIBLE` enabled. The wire copy is
0.3% smaller, so it stays behind the solid shell without z-fighting. It is
excluded from final renders.

## Corrected overlap

- The daughterboard is shortened and moved forward. It now has 0.5 mm nominal
  clearance from the plug overmold.
- The spreader and shield service opening is enlarged to 18 mm wide and
  extends from Z = -25 to -10 mm, providing 1 mm nominal board-edge clearance.
- The housing contains a full vertical plug chute and a separate daughterboard
  pocket. Native mesh intersection tests report zero intersections for the
  daughterboard, plug, spreader, shield layers, and housing pairs under test.

## Architecture decisions remain open

A USB daughterboard can isolate connector loads and permit a centered port,
but it adds connectors and transmission-line discontinuities. USB SuperSpeed,
Power Delivery, ESD placement, grounding, shield bonding, retention, and cable
service life must be designed and tested before accepting it.

Splitting a thermal interface pad is a packaging workaround. It may be valid
when two heat paths or a central service opening require it, but it reduces
continuous contact area and changes pressure distribution. Material, thickness,
compression, contact pressure, thermal resistance, assembly tolerance, and
physical testing are still required.

References:

- USB-IF Type-C system overview: https://www.usb.org/sites/default/files/D1T1-2%20-%20USB%20Type-C%20System%20Overview.pdf
- TI USB board design and layout guidance: https://www.ti.com/lit/pdf/slla414
- Henkel thermal gap-pad guidance: https://next.henkel-adhesives.com/us/en/applications/thermal-management-materials/thermal-gap-pad-materials.html
