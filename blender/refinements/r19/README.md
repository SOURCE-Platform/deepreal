# R19 role-specific drum sweep study

[Open the Blender study](deepreal-role-specific-sweep-r19.blend). This revises the R18 rear-support sightline experiment using the different provisional ranges requested for the two sensor drums. It is a visibility and clearance mockup, **not** a working motor, bearing, encoder, or cable assembly.

Angles describe where the sensors point relative to straight ahead:

| Drum | Highest pose | Center pose | Lowest pose |
| --- | --- | --- | --- |
| Face | [45° up](renders/r19-face-up45-front.png) | [straight](renders/r19-face-straight-front.png) | [45° down](renders/r19-face-down45-front.png) |
| Interaction | [straight](renders/r19-interaction-straight-front.png) | [45° down](renders/r19-interaction-down45-front.png) | [90° down](renders/r19-interaction-down90-front.png) |

Additional oblique views reveal the arm openings at the range ends: [face up](renders/r19-face-up45-oblique.png), [face down](renders/r19-face-down45-oblique.png), [interaction straight](renders/r19-interaction-straight-oblique.png), and [interaction down](renders/r19-interaction-down90-oblique.png).

Above-front views with the enclosure installed: [face 45° up](renders/r19-face-up45-above.png), [face 45° down](renders/r19-face-down45-above.png), [interaction straight](renders/r19-interaction-straight-above.png), and [interaction 90° down](renders/r19-interaction-down90-above.png). In this view, two dark arm slots are plainly visible near the top at face 45° down and interaction 90° down. They are not visible from this same camera at face 45° up or interaction straight. Other viewpoints can still reveal them.

## Findings

- The face drum's two narrow rear-arm slots remain much less prominent than they were in the earlier 150° trial, but the openings still face partly forward at ±45° and can be seen from oblique views.
- The interaction drum's slots likewise face partly forward at its 0° and 90° ends. Their appearance depends on viewpoint and the surrounding enclosure.
- A center-ray test against the existing housing first detects an obstruction at **87° down** for the interaction drum's pinhole, then also for the modeled depth and RGB lenses at **90° down**. This tests lens centers only; useful field of view can be clipped sooner. The housing needs a new lower opening or a lower practical motion stop before 90° can be treated as usable.
- The [machine-readable check](r19-sweep-check.json) still flags a face outer-arm/shell triangle intersection at 45° down. Do not interpret the current arm slots as mechanically cleared.

To inspect the poses in Blender, select `Face_Rotating_Drum_Pivot_R15` and set local X rotation to -45°, 0°, or +45°. The interaction pivot's saved pose points 45° down; set its local X rotation to -45°, 0°, or +45° to point straight, 45° down, or 90° down. The range limits are conceptual and no physical stops are modeled.

R19 leaves the R16 model unchanged. The mockup removes the old exposed side-drive proxies and adds fixed rear yokes, two arms and bearing envelopes per drum, plus rotating plain outer faces. It does not yet reconnect those bearing envelopes to the rotating shell, establish a load path to the housing, or route the moving head cable. The purpose is to check sightlines before detailed internal design.
