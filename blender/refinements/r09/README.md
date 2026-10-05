# DeepReal enclosure refinement R09 — right-side USB board tab

Open `deepreal-exterior-refinement-r09.blend` in Blender. This is an **unbuilt
packaging proposal** for review, not an approved PCB, thermal solution, or
fabrication model. All files are inside the DeepReal repository.

## What changed from R08

- The USB cable enters vertically from the lower right, rather than the center.
- The proposed USB-C socket envelope sits against a green extension of the
  visual main PCB. The centered daughterboard and internal flex-route objects
  have been removed from this review scene.
- The spreader is continuous. The centered housing chute is closed. A lower
  right housing chute and a local right-side rear-shield clearance window are
  modeled. The cut shield edge is an EMI **problem to solve**, not a validated
  shield termination.
- The original J1 location imported from the native PCB is retained as a
  hidden reference. The actual KiCad board outline, J1 footprint, schematic,
  and routing have **not** been changed.

The modeled socket is an **unselected shape**, not the final USB-C part. The
native board presently names an Amphenol footprint while its component record
names Hirose CX90M3-24P and marks a mechanical conflict. R09 does not resolve
that discrepancy or imply that the socket can be soldered as pictured.

## Nominal geometry in the Blender scene

| Feature | Review envelope, mm | Meaning |
| --- | --- | --- |
| Source PCB | X = -45 to 45 | Imported native board visual |
| Proposed green tab | X = 44.6 to 57.5; Z = -22.5 to -10 | Visual outline proposal only |
| Spreader | X = -38 to 38 | Original uncut geometry |
| Proposed socket | X = 46.25 to 56.75 | 8.25 mm *lateral* gap to spreader edge |

The gap is a nominal geometric separation, **not a thermal clearance rating**.
The right tab touches the existing board visual and the socket envelope. Exact
mounting pads, board-stack dimensions, connector retention, mating depth,
insertion loads, assembly tolerances, and chassis support remain unresolved.

## Review the model

The saved viewport frames the whole product closely. In the Outliner, use the
eye on `00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME` to inspect the
internals while keeping `00A — WIREFRAME FALLBACK — KEEP VISIBLE` on.

Previews in `renders/`:

- `r09-exterior-front.png` — cable exits off-center at the bottom right.
- `r09-internal-rear.png` — spreader remains continuous beside the port.
- `r09-right-usb-detail.png` — socket, tab and rear shield edge together.
- `r09-port-tab-exposed.png` — diagnostic view with spreader/shield hidden for
  that image only; it reveals the original populated PCB behind the new tab.

## Verification and next engineering gates

Reproduce with the existing Blender 5.2.0 LTS executable:

```sh
/opt/homebrew/bin/blender --background --python blender/refinements/r09/build_r09.py
/opt/homebrew/bin/blender --background --python blender/refinements/r09/verify_r09.py
/opt/homebrew/bin/blender --background --python blender/refinements/r09/render_r09.py
```

The saved `r09-verification.json` reports geometric checks and source hashes.
R08's plug/spreader pair had 10 intersecting triangle pairs; R09 has zero.
The R09 tab, socket, plug, and cable have no listed unintended mesh intersection
with the spreader, rear shield or housing. This only checks the listed scene
geometry. It does not prove clearance for a real part, heat safety, USB signal
integrity, electrical connection, or mechanical strength. Readiness is
**BLOCKED**.

Before changing the native PCB, select one exact USB-C receptacle and mating
plug; reconcile J1's part and footprint; confirm the drawing, pads, pin map,
board edge, housing, plug travel and support under insertion force. Then capture
and route VBUS, ground, CC, USB2 and SuperSpeed through protection/PD/mux to the
processor; validate the stackup, impedance, ESD placement, shield bond and
boot/recovery path. Check assembly tolerances and heat flow; measure the real
spreader, socket shell and plug-grip temperatures under worst credible operating
conditions. No vents or manufacturing-release outputs were created.
