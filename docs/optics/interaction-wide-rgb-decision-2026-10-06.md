# RGB lens roles — 6 October 2026

Status: **EVT optical choice; packaging and coverage not yet validated**.
This supersedes the two-standard-RGB-lens entry in the historical
`docs/research/main-pcba-architecture-input-decisions-v0.1.md`. It does not
resolve that document's independent FPGA-topology question.

| Drum | RGB assembly | Published horizontal × vertical FoV | Provisional optical travel |
| --- | --- | --- | --- |
| Face | Raspberry Pi SA31VA30P standard | 66° × 41° | 45° up to 45° down |
| Interaction | Raspberry Pi SA36VA30P wide | 102° × 67° | straight to 45° down |

Manufacturer basis: [Raspberry Pi Camera Module 3 Sensor Assembly product brief](https://datasheets.raspberrypi.com/camera/sensor-assembly-product-brief.pdf), physical specification and variants table. Both assemblies have a 10.8 × 10.8 mm outline. The standard lens is Ø5.75 mm with a 6.98 mm depth dimension; the wide lens is Ø6.95 mm with an 8.3 mm depth dimension. The wide lens focuses down to 5 cm versus 10 cm for standard. Both are IMX708-based visible-light variants.

## What this changes

- Populate the face head with SA31VA30P and the interaction head with SA36VA30P. The shared electrical head-carrier design remains a target. Verify the wide variant's exact connector mating, pinout, autofocus load and support components before treating the populations as interchangeable.
- Reserve the larger interaction lens space. The [R20 Blender envelope study](../../blender/refinements/r20/README.md) places the published outline and a conservative lens cylinder against the current R16 drum. It finds no triangle overlap with the rotating shell, **but the larger envelope intersects the old internal optical-carrier proxy**. That carrier must be redesigned. The existing 9 mm *visual* bore does not prove wide-angle optical clearance.
- Use the [desk-coverage study](../../blender/refinements/r20/r20-interaction-desk-coverage.png) to select travel after mounting height and target work area are known. At 45° down, the wide RGB field reaches 78.5° down, leaving 11.5° to vertical. A point directly below the camera is outside that idealized image. The face and interaction proposed ranges are shorter than 180° and are not physical stops yet.
- Check the depth receiver lens and projector field separately. Their useful overlap with the wide RGB image has not been established. Calibrate RGB lens distortion and alignment on hardware.

## Required closure before fabrication

1. Fix camera mounting height and horizontal offset from the keyboard/work area, then mark the nearest and farthest points that must be visible. Run full 3D field, window, enclosure and focus checks at every selected drum pose.
2. Obtain the exact wide assembly CAD or optical datum; redesign the optical carrier and window with assembly and tolerance clearance. The R20 cylinder is an envelope, not a validated lens model.
3. Compare standard and wide assembly electrical datasheets, power demand and connector mating; update the common carrier and rail budget accordingly.
4. Measure RGB, IR/depth and projector overlap on an optical bench, then set hard stops and moving-cable routing. The future open-top/center-divider support concept needs its own mechanical build.
