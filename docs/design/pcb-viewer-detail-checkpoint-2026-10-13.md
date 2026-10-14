# Development viewer PCB detail, 2026-10-13

## First-pass scope

The first pass made the development-only `/deepreal/assembly-review` viewer load the retained
Blender PCB when **Main board** is selected. It replaces the simplified display
board only in that standalone view. All parts kept the existing assembly
proposal. The native 90 × 28 mm board is not stretched into the assembly's
different USB-wing outline, and no connector or component is relocated.

The restored snapshot contains 234 component bodies: 216 native models and
18 representative envelopes for missing models. Six native surface objects
carry the substrate, pads, solder mask and front/back silkscreen. The retained
layout export lists 2,313 pads and no tracks, vias or zones. The viewer labels
this as **Unrouted PCB review** and identifies the **18 component model
placeholders**. Existing package shapes and colors are preserved, not replaced
with invented pins, labels, copper or solder.

Head-board detail, missing package models, PCB routing and assembly-outline
reconciliation are not part of this restoration.

## Source and serving boundary

Source: `blender/deepreal.blend`, SHA-256
`4c65762f65d35f5345bb3ad601aafdb0ce2809681931aad480586cc5747d3412`.

Installed internal asset: `blender/review-output/web/main-pcba-review.glb`,
14,455,828 bytes, SHA-256
`4ee6eb07b39351dbb455f2937b2085dd7c29a7bcc0eae349bab1aa2bc2e3b2d4`.
Its sibling JSON records source hashes, object inventory, model status and
the unchanged publication/fabrication locks.

The native export's recorded design-status hash does not match the current
`design-status.json`. The existing `pcba_native_import.checked_inputs()` guard
still rejects a fresh native import. This pass does not bypass that guard,
rewrite the status, regenerate electronics or claim a current engineering
validation. It transports the retained Blender review snapshot, verifies the
unchanged board/export/native-GLB hashes, and records both status fingerprints.
Both current and retained publication/fabrication permissions must be exactly
false; unknown permissions are rejected.

The detailed asset stays outside the site's `public/` directory. The
`/api/development/deepreal/pcb-review` endpoint returns 404 outside development
before reading files. Development responses use `private, no-store`; model
bytes must match the manifest's size and SHA-256. The page's production
`notFound()` guard and the installed assembly/exterior assets are unchanged.
In the first pass, the 14.5 MB model loaded only when Main board was selected
and remained in memory for subsequent filter changes within that viewer session.

## Validation

- Exact inventory: 240 exported mesh objects, with no objects from the other
  Blender presentation scenes. Multi-material objects may become several
  Three.js primitives; the client checks coverage of every exported object
  rather than treating those primitives as extra components.
- Bidirectional world-space vertex comparison against the retained Blender
  source: maximum measured difference **0 mm**, acceptance threshold 0.001 mm.
  This is a geometry-transport check, not a tolerance or placement approval.
- All 18 exported materials retain source base color, alpha, metallic and
  roughness values.
- 18 focused viewer/API/geometry tests pass. Six new Blender export-boundary
  tests pass. The final exporter reproduces the installed audited GLB exactly.
  Focused TypeScript, scoped ESLint, Python syntax and repository diff checks
  pass.
- Desktop 1600 × 900 and mobile 390 × 844 captures are intact and show the
  detailed board and its review labels. The mobile capture keeps the board
  above the controls. These captures do not establish photographic material
  accuracy.
- Programmatic browser events on desktop and mobile confirm all five stage
  titles/values, filter disabling and the retained Inside-stage value when
  returning to All parts. Mobile filter buttons fit without document overflow;
  returning to Main board does not fetch the detailed asset again.
  Native-pointer automation delivered no DOM click events in the embedded
  pane. A rendered-frame sequence check stalled and was stopped. Neither is
  claimed as passed; continuous playback, pointer/orbit behavior and measured
  mobile frame rate were not signed off in this pass.
- All 76 protected source, electronics, installed-asset and page-guard hashes
  match the pre-restoration snapshot.
- The existing six-test native-import suite has four passes and two errors
  from the pre-existing stale status fingerprint. Those inputs and tests
  remain unchanged. The full-site typecheck/build was not rerun after earlier
  unrelated failures.

The accepted captures and detailed transport report are retained under
`tmp/pcb-viewer-fidelity-2026-10-13/`. Earlier rejected export/capture candidates
are not the installed asset.

## Withdrawn follow-up: detailed board in All parts

The same detailed geometry temporarily replaced all 27 main-board display proxies
in the development viewer's Inside, Drums lifted and Exploded stages, as well
as the Main board filter. It starts loading at reveal progress 0.14 and
becomes visible from 0.17, matching the existing internal visibility threshold.
It stays hidden in Exterior and both isolated head filters. Returning to All
parts uses the same loaded model, not a second copy.

Manifest v2 records a rigid `[0, 0, 0.005]` metre translation in web coordinates,
bound to the installed assembly's SHA-256. This registers the substrate's depth
plane; the left and upper/lower core-board edges already share coordinates.
The measured substrate-plane difference after registration is
0.0000005774 mm. Scale stays `[1, 1, 1]`; no component geometry or placement
within the board changes. Camera bounds include the registered detailed model.

This is **not** an approved package fit. The native rectangle has no proposed
USB wing, the native J2/J3 body orientation differs from the horizontal cable
illustration, and J4/J5 differ from their old display proxies. Cable paths and
the exterior USB lead are not rerouted to hide these discrepancies. All parts
adds the label **PCB fit and cable interfaces unresolved**.

The GLB bytes, 240-object inventory and all 18 materials remain unchanged.
The transport audit again measures 0 mm maximum vertex difference. All 78
protected source/asset hashes match. Twenty-two viewer tests, six export-guard
tests, focused TypeScript and scoped ESLint pass. Browser DOM checks confirm
the review label across the three internal stages, its absence in Exterior
and the head filters, and no additional PCB fetch on filter return.
The 390 × 844 exploded capture is intact. Desktop captures repeat page
sections and are rejected; full desktop visual signoff and continuous
playback/pointer checks remain open.

Follow-up evidence is under `tmp/pcb-all-parts-2026-10-13/`.

## Current correction: earlier assembly restored

User close-ups exposed source-layout conflicts that the transport and
visibility checks did not validate. Native body bounding boxes overlap for
U3/J3, U5/L5, U5/L6, U11/L6 and U11/L7. U20/U21 have only 0.02 mm nominal
body-box separation. These are screening measurements, not exact triangle
intersection or acceptable-clearance findings.

The native J2/J3 long axes do not match the earlier horizontal ribbon
illustration. J1 uses an Amphenol footprint/model while its named candidate is
Hirose CX90M3-24P. The board has no proposed USB wing or validated insertion
path. J4/J5 use substituted vertical pin headers, not the earlier low-profile
connector envelopes targeted by the conceptual cables.

The user approved restoring the earlier assembly and keeping the native layout
separate. All parts now again renders the unchanged R36 main-board proposal
and its original 27 display objects. The native layout neither loads nor
appears in the reveal, explosion or isolated head filters. Main board alone
loads it, centered separately, with **Native PCB layout, known clashes**.
Its bounds do not affect assembly framing.

Manifest v3 is standalone-only, records both layout clearance and package fit
as unvalidated, and rejects assembly-placement metadata. The detailed GLB,
public assembly/exterior assets, KiCad files and release locks are unchanged.
Twenty-one focused viewer tests and six export-guard tests pass; focused
TypeScript and scoped ESLint pass. Browser checks confirm zero native-asset
requests across the three internal assembly stages and correct separation
after returning from Main board. The restored mobile exploded capture is
intact.

This restores a mechanical illustration. It does not repair or approve the
native PCB layout, electrical design, housed cables or USB interface. Future
native integration requires actual component/courtyard clearance checks,
correct footprints/orientations and mechanical interface reconciliation,
not just geometry-preservation tests.

Correction evidence is under `tmp/pcb-assembly-restore-2026-10-13/`.

## Reproduce locally

From the DeepReal repository root, choose a new internal output path. The
exporter refuses to overwrite an existing GLB or manifest:

```sh
DEEPREAL_WEB_PCB_REVIEW_OUT="$PWD/tmp/pcb-review-new.glb" \
  blender -b -t 4 --factory-startup --python-exit-code 1 \
  --python blender/export_web_pcb_review.py

DEEPREAL_WEB_PCB_REVIEW_OUT="$PWD/tmp/pcb-review-new.glb" \
DEEPREAL_WEB_PCB_AUDIT_OUT="$PWD/tmp/pcb-review-new-audit.json" \
  blender -b -t 4 --factory-startup --python-exit-code 1 \
  --python blender/audit_web_pcb_review.py

blender -b -t 4 --factory-startup --python-exit-code 1 \
  --python blender/test_web_pcb_review.py
```

No commit, push, deployment, public release or fabrication output was made.
