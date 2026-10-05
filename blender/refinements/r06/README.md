# DeepReal enclosure refinement R06

R06 corrects the visible underside conflicts and USB seating shown in the R05
review screenshots. It remains an engineering-review model.

## One-click housing visibility

The solid `Main_Housing` is the only object in the top-level collection:

`00 — HOUSING SHELL — CLICK EYE OR CAMERA`

- Click the **eye** beside that collection to hide/show the housing in the
  viewport while leaving the drums, PCB, routes, and USB parts visible.
- Click the **camera** beside that collection to include/exclude the housing
  from a render.

## Corrected protruding objects

J2 and J3 were using an unverified body with the 16.8 mm connector length
standing vertically. Hirose lists the exact `FH26W-51S-0.3SHW(97)` as 16.8 mm
long, 3.2 mm wide, and 1.0 mm high. R06 preserves the bad source bodies in a
hidden evidence collection and displays simple proxies with those documented
dimensions in the correct board-plane orientation.

J4 and J5 are reserved six-position motor/encoder **connectors**, not the motor
encoders themselves. No exact manufacturer part is recorded. Their generic
pin-header bodies are therefore preserved in the hidden evidence collection
and excluded from the normal assembly view. Their physical envelope remains a
blocker rather than a guessed shape.

Manufacturer source, accessed 2026-10-01:
https://www.hirose.com/product/p/CL0580-2415-6-97

## USB seating

The plug overmold is the hard black plastic grip. R06 moves it 1.2 mm inward,
leaving its top 1.0 mm inside the housing surface. A 9.4 × 5.4 × 2.2 mm local
recess provides 0.2 mm nominal clearance per side. The external portion of the
metal plug shell is consequently covered by the overmold in the model.

This does not validate insertion force, connector retention, strain relief,
tooling radii, tolerances, or cable bend life.
