# Private USB comparison and PCB marking checkpoint

The marking candidate removes 122 annotation findings without changing copper,
component placement or design rules. **Native DRC still fails, and no replacement
USB receptacle is selected.** Canonical electronics, Blender assemblies and the
website remain unchanged.

## Candidate and scope

Artifacts are under `tmp/usb-pcb-closure-2026-10-14/`.
The retained candidate is `marking-04/`; `marking-05-repeat/` is its independent
repeat build from the unchanged MECH-FIT-05 `package-07/` predecessor.

- Candidate PCB SHA-256:
  `21d8dfb970f8790c83c308c2d3837a3ec446a818192679ea97947e271d00ef84`.
- Both PCB files are byte-identical, and their annotation plans agree.
- The plan contains 51 entries. All targeted silkscreen texts have a conservative
  placement, at least 0.8 mm font size, and a subsequent native DRC check.
- Board-level warnings may move across the board and wrap whole words.
  Reference labels remain within the planner's local ±12 mm search window.
  That limit is not an assembly-readability qualification.
- Warning words, visibility, layers, mirroring and component association remain
  intact. The obsolete U1 proxy note now reads
  `U1: 548 positions; AF22 unresolved; lands provisional`.
- A serialized scope guard permits only listed annotation placement, font size,
  warning whitespace and that exact U1 note correction.
- Native exports of the outline, components, pads, holes, tracks, vias and zones
  match the predecessor exactly: 238 footprints, 2,626 pad primitives, no routing.
  The four manufacturer-local package nets do not establish system circuitry.

The changes do not qualify assembly readability or manufacturing marking
requirements. The failed-shutdown `marking-01/` and intermediate `marking-02/`
and `marking-03/` artifacts remain as investigation evidence, not final outputs.

## Native DRC

| Finding | Predecessor | Marking-04 |
| --- | ---: | ---: |
| Copper clearance | 340 | 340 |
| Copper-to-edge clearance | 2 | 2 |
| Drill outside allowed range | 29 | 29 |
| Text height | 48 | 0 |
| Silkscreen-to-edge | 3 | 0 |
| Silkscreen overlap | 16 | 0 |
| Silkscreen over exposed copper | 56 | 1 |
| Violations subtotal | 494 | 372 |
| Unconnected items | 2 | 2 |
| Total | 496 | 374 |

DRC exits **5**, not success: 373 errors including unconnected items, plus one
warning. The remaining warning is U9's existing filled pin-1 triangle against
C57 pad 2. It was not moved or deleted to clear a cosmetic check. Its orientation
marking function needs a justified correction.

Full electrical finding/item multisets agree, including UUIDs, positions,
descriptions and severity. Report ordering is not stable and was not used as an
identity check. All five inherited ignored checks remain unchanged; none was
added or relaxed.

## Export and regressions

The native GLB export exits 0. Its binary length, buffer-view bounds and position
values were checked, and its model identities match the predecessor:
219 native component references, 15 inherited missing-model references and four
pad/hole-only mounting references.

The missing-model warnings, skipped geometry nodes and transient Cocoa
output-file-not-found message remain in `marking-04/native-export.log`.
File existence and binary inspection, not exit status alone, establish that an
export was produced. This incomplete native export is not a new installed
assembly, and the earlier USB clash results have not been rerun or cleared.

The 71 CAD/marking tests and 14 NXP evidence tests pass. Three new Python scripts
parse. An initial combined run used KiCad's Python for the NXP tests and failed
two tests because `fitz` was absent. The successful rerun uses the established
Python 3.11 NXP environment; both attempt records remain available.

The earlier Blender registration, optical and saved-assembly suites were not
rerun: their inputs are protected and unchanged, and no new installed model was
created. All 340 protected input hashes were rechecked. Both repositories pass
`git diff --check`. The site has four additional vision-page status entries
outside this task; they were left untouched. Its protected DeepReal assets
remain unchanged.

Evidence: `candidate-validation.json`, `regression-results-02.json`,
`marking-04/drc-command.json`, `marking-04/native-review-manifest.json` and
`final-validation.json`.

## USB comparison and access limits

The comparison binds five official GCT drawings by SHA-256. It is not an
approved-part list or a generated land pattern.

| Family | Result for the retained board |
| --- | --- |
| USB4065 | Rejected: drawing marked obsolete; recommends 1.20 mm PCB |
| USB4745 | Rejected: 0.6 ±0.1 mm PCB |
| USB4056 | Rejected: 1.00–1.20 mm PCB |
| USB4230 | Thickness and attachment acceptance unresolved |
| USB4910 | Investigation only; thickness and short-stake attachment unresolved |

The official USB4910 page lists a 24-contact USB 3.2 Gen 2 top-mount part.
Its Product Spec download returns HTTP 403, both directly and through the
rendered page. No specification or manufacturer CAD was obtained, and no
contact, quote, signup or order was submitted.

The earlier approximately 1.509994 mm native measurement describes the **bare
substrate mesh**, not a complete manufactured board. In this export:

- Copper spans board-normal −0.035 to 1.544994 mm.
- Soldermask surfaces lie at −0.05 and 1.559994 mm.
- Silkscreen surfaces lie at −0.075 and 1.584994 mm.

These are exported surface extents, not an approved stack-up or thickness
tolerance. The 1.5 mm mechanical nominal and 1.6 mm KiCad setting still need a
single manufacturing definition. See `native-surface-thickness-observation.json`;
the original comparison remains retained rather than silently rewritten.

Before selecting a replacement, establish the exact ordering variant, accepted
board construction, shell-stake/peg attachment, mouth and mounting datums,
plug/overmold insertion envelope, load path, and production lands/mask/paste.
Top-mount marketing alone is not compatibility evidence.

## Remaining gates

- Resolve the 340 clearance, two copper-edge, 29 drill and two unconnected
  findings using qualified packages and circuitry, not relaxed rules.
- Resolve U1 AF22, production lands/stencils and the other inherited package
  substitutions, including U5/U10, sensors, headers and FFC variants.
- Correct the four previously measured nominal USB intersections. They remain
  recorded, not cleared by marking changes.
- Establish enclosure/tray/shield and harness clearances, attachments,
  tolerances, insertion loads, assembly/tool access and moving-flex qualification.
- Complete system circuitry, power sequencing, stack-up and routing.

All canonical-replacement, manufacturing, public-export and deployment permissions
remain false. No commit, push, site update or deployment was performed.
