# R37 rear cable space reservation

R37 continues the [R36 inner-bearing study](../r36/README.md). The orange
volume in the [internal view](r37-rear-volume-internal.png) is a possible
passage through the center divider. The cyan volume is a possible chamber
inside the rear enclosure. They are **space reservations**, not cavities,
cable solids, or a working cable route. The public exterior is unchanged.

The passage spans X −0.8 to 1.2 mm, Y −1.7 to 13.25 mm, and Z 11.5 to
28.5 mm. The chamber spans X −26 to −0.2 mm, Y 13 to 20 mm, and Z 10.5 to
28.5 mm. These sizes test where room might exist; they are not bend-radius
requirements or approved wall dimensions.

## Finding

The passage crosses the current fixed **rear bearing support web** (four
surface triangle contacts). All 27 interior points sampled in the passage
are inside the solid R30 visual enclosure. In the rear chamber, 26 of 27
sampled points are also inside the solid enclosure. The remaining point,
at X −13.1, Y 18.6, Z 24.9 mm, lies outside the curved rear skin; a
rectangular cut there would break through the exterior. The test found no
contacts with the optical carrier, motor, or drums at the straight-ahead
pose. This is an occupancy study; a surface-only collision test would have
missed a volume fully contained by the shell.

The R36 moving cable exits along X with its 15.6 mm mating-end width along
Z. Sending it toward the rear (+Y) would require an **edgewise turn** of
that flat strip. Simply hollowing the indicated chamber does not make a
working dynamic cable. The fixed bearing web would also lose its present
attachment if the passage were cut as drawn. A replacement bearing load
path, a realizable flex orientation and loop, and a fixed electrical
termination need to be designed together before altering the enclosure.

There is a size problem as well. Würth Elektronik's
[dynamic-flex application example](https://www.we-online.com/files/pdf1/webinar-rigidflex-flexibility-cbt-en.pdf)
lists an inside bend radius **greater than 12 mm** for its roughly 120 µm,
single-layer flex. A 180° return at that radius needs over 24 mm across.
This proposed chamber is only 7 mm deep (Y) and 18 mm high (Z). It therefore
cannot house that example loop in either of those directions. This is a
supplier illustration, not a selected DeepReal stack or a universal limit;
the actual motion and cable vendor must determine the necessary space.

Würth Elektronik's [Flex Solutions design guide](https://www.we-online.com/files/pdf1/design-guide-flex-solutions-cbt-en.pdf)
calls for specifying the actual dynamic stack, bend shape, radius, frequency,
and cycle count early in the mechanical/electrical design. Its guide also
notes that dynamic flex often favors a single layer in the bending area.
That guidance is a reason to involve the cable fabricator, not a validation
of this reservation. The 0.2 mm in the R36 straight visualization is not a
validated dynamic stack thickness.

## Next design action

Redesign the moving cable and inner bearing support as one module. Compare
a loop that bends across the flex's thin dimension with alternative
head-board/connector locations, then screen the full face-drum −45° to +45°
sweep. Only after a route clears the optical carrier, motor, supports,
enclosure and both drum end rings should the chamber be cut into the shell.
Check the interaction drum separately with its own travel limits. Vendor
review must establish flex stack, impedance, strain relief and cycle life.

## Reproduce

```sh
blender -b -t 4 --python blender/refinements/r37/study_r37.py
```

Outputs: editable `deepreal-rear-cable-volume-r37.blend`, internal view,
and `r37-volume-check.json` with bounds and occupancy results.
