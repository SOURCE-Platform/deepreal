# R20 interaction wide RGB optical study

[Open the Blender study](deepreal-wide-interaction-optics-r20.blend). This starts from R16 and adds the published 10.8 × 10.8 mm interaction RGB assembly outline and a conservative Ø6.95 × 8.3 mm lens envelope. The file opens in an isolated inspection view: the two cyan envelopes and the existing gray optical carrier are visible. Press **Alt-H** in the viewport to reveal the rest of the assembly. The new objects are in `10 — R20 WIDE RGB PHYSICAL ENVELOPES`. The old lens and internal module are retained as visual proxies.

R20 **does not implement the proposed open-top cradle**, real motor/bearings, cable path, or new housing. Its purpose is to expose the size change and test simple RGB sightlines while that mechanical concept is developed. The saved interaction rotation is 45° down; its trial poses are straight, 22.5° down and 45° down. The face trial poses are 45° up, straight and 45° down. No hard stops are modeled.

## Results

- [Envelope check](r20-envelope-check.json): neither added wide assembly envelope intersects the rotating shell in this provisional position. Both **intersect the current internal optical carrier proxy**. Thus the carrier layout must change; this is not a fit approval.
- [Isolated envelope view](r20-wide-envelope-vs-carrier.png): the cyan lens/assembly envelope crosses the existing light-gray carrier near its end. Other parts are hidden for this diagnostic render.
- [Nine-ray RGB check](r20-rgb-cone-check.json): sampled center/edge rays at each proposed pose do not intersect the existing shell or housing. This only starts rays at the modeled cover center; it does **not** check every ray through the real entrance pupil, glass, or window, nor does it validate the actual wide lens optical datum.
- [Desk coverage plot](r20-interaction-desk-coverage.png) and [data](r20-desk-coverage.json): on an unobstructed flat desk, the wide RGB image at 45° down reaches from 0.20 to 4.91 times the camera's height ahead of it. This is an idealized 2D section. Actual mounting height, target distances, focus, distortion and depth-system overlap are still inputs.

The [dated optical decision](../../../docs/optics/interaction-wide-rgb-decision-2026-10-06.md) records the part choices and closure gates. The baseline R16 file remains unchanged.
