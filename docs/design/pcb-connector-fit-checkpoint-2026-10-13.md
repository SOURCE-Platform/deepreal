# PCB connector correction candidate, 2026-10-13

## Result

`MECH-FIT-02` changes J2/J3 in a separate KiCad candidate. It preserves the
measured USB-wing outline, the fixed core datum, all 238 footprints and all
2,313 original pad identities. It does not change the canonical board,
schematics, design gates, retained Blender sources or installed website assets.

J2/J3 now have horizontal long axes and smaller paste apertures matching the
retained Hirose catalog's dimensions. Their lower courtyards sit 0.30 mm inside
the board edge. These are limited mechanical and paste-pattern corrections,
not an approved connector layout. Pin continuity, the exact FH26W model,
latch access and the moving cable remain unresolved.

**Full fit and native DRC still fail.** No Blender or viewer integration was
performed. Fabrication, publication and integration permissions remain false.
No commit, push or deployment was made.

## What changed

| Item | Change |
| --- | --- |
| J2 pose | KiCad anchor `[43, 45.055]` mm, 90°; previously `[43, 46]`, 0° |
| J3 pose | KiCad anchor `[87, 45.055]` mm, 90°; previously `[87, 46]`, 0° |
| Numbered copper contacts | Preserved, including pad UUIDs, sizes, mask openings and net state |
| Paste | Removed copper-sized paste from the contacts; added 53 separate paste-only rectangles per connector |
| Other source blocks | Byte-identical to `MECH-FIT-01`, including USB, motor headers, outline and thickness |
| Copper routing | None added; no nets invented |

The complete footprints rotate in KiCad, including their pads and text. No
viewer-only model rotation or scaling is used. The smaller paste rectangles
are centred on their associated lands. Their dimensions are:

| Copper size (mm) | Paste size (mm) | Count per connector |
| --- | --- | --- |
| 0.80 × 0.30 | 0.65 × 0.23 | 26 |
| 0.65 × 0.30 | 0.55 × 0.23 | 25 |
| 0.95 × 0.40 | 0.70 × 0.30 | 2 retention tabs |

This adds 106 **paste-only primitives**, not components, copper pads or
electrical connections. The export contains 2,419 pad primitives, of which
2,313 retain the original pad identities.

The inset is derived from the actual rotated courtyard. It moves the retained
body centre about 0.77 mm inward from the presentation target. This difference
is recorded rather than silently redefining the housing or cable interface.
The model's depth and its approximately 0.11 mm centre difference from the
target remain unapproved. The body screen rigidly transforms the retained
model boxes; it is not a fresh solid-model import.

## Manufacturer evidence and selections

### J2/J3

The retained `references/components/datasheets/hirose-fh26-D49355-en.pdf`,
SHA-256 `38e5c3c1278d7843146da4eb44c1a360f847659dd8d758143c5d55407148a40c`,
provides the body dimensions on pages 6–7, land and paste dimensions on page 8,
and bottom-contact insertion instructions on pages 14 and 17. Page 16 shows a
135° maximum actuator opening.

The inherited library part and model are named **FH26-51S**, while the intended
part is **FH26W-51S-0.3SHW(97)**. Page 5 distinguishes black LCP from the
FH26W light-brown PA housing. Matching catalog dimensions do not approve the
inherited model as the exact FH26W variant.

The exact numbered drawing was identified in the manufacturer's product index,
but the attempted official document retrieval returned HTTP 403. No pin-number
approval, material substitution or head-to-main continuity claim is made.
The 90° pose remains a mechanical candidate, not a selected cable-exit or
electrical orientation.

### USB, J1

The BOM names Hirose **CX90M3-24P**. The actual inherited footprint and model
are Amphenol **12401610E4-2A**, whose catalog ordering name uses `#2A`.
These are different parts.

The indexed Amphenol family datasheet identifies 12401610E4#2A as a USB 3.1
Gen 2 right-angle, top-mount dual-SMT receptacle with 2.1 mm shell tabs.
An exact drawing and supported PCB-thickness range were not retained; the
official requests returned HTTP 403. Shell-tab length alone is not proof of
compatibility with the 1.6 mm board or the below-board mating target.

GCT USB4085 was rejected as a SuperSpeed candidate because its manufacturer
identifies it as USB 2.0 with 16 contacts. Amphenol 12401548E4#2A remains a
different, unverified alternative. J1 was not moved, renamed or substituted.
The earlier Hirose 0.8 mm maximum recommended PCB-thickness conflict remains.

### Motor/encoder connectors, J4/J5

The official JST SH catalog was retained at
`../../tmp/pcb-connector-candidate-2026-10-13/manufacturer/jst-sh-catalog.pdf`,
SHA-256 `ea3071ca5ee5a6069eba534fa39a10f34c9fb742ee42135a69ab4156bfa0f5de`.
It identifies SM06B-SRSS-TB(LF)(SN), SHR-06V-S mating housing and
SSH-003T-P0.2-H contacts. The catalog rating is 1 A with AWG 28 wire.

The side-entry header is approximately 8 × 4.25 × 2.95 mm, with a 6.25 mm
assembled depth. It exceeds the current 5 × 2 × 1.2 mm proxy in every axis.
Motor stall current, current limiting, harness loading and retention are not
defined well enough to select it. The generic vertical pin headers remain
unchanged placeholders, not approved physical interfaces.

## Validation

| Check | Result |
| --- | --- |
| New connector tests | 15 pass, including real saved-candidate inventory |
| Existing candidate boundary tests | 12 pass |
| Existing geometry tests | 8 pass |
| Fresh KiCad parse and descriptive export | Exact equality with saved candidate export |
| Effective J2/J3 paste inventory | 53 separate apertures per connector; dimension, centre and angle screens pass |
| Actual F.Paste Gerber inspection | All 106 optical apertures match the saved candidate's centres, angles and dimensions |
| J2/J3 copper-edge findings | 0 for both, previously 4 each |
| Full-population positive body-box overlaps | 16 candidates, previously 19 |
| Native courtyard overlaps | 54, previously 56 |
| Native standalone DRC | **Fail, exit 5: 958 findings, 725 errors and 233 warnings** |
| Named pad nets / tracks / vias / zones | 0 / 0 / 0 / 0 |
| Protected input hash check | 108 files unchanged |

Both candidates were run with KiCad 10.0.6 and the same standalone flags:
`pcb drc --format json --all-track-errors --exit-code-violations`.
The repeated predecessor run reports 995 findings, 735 errors and 260 warnings.
Neither candidate inherits the canonical `.kicad_pro` or custom `.kicad_dru`.
No new exclusions or severity suppressions were added; KiCad's standard ignored
checks remain listed in each JSON report.

The lower total is not a fit approval. Of the candidate's 499 clearance
findings, 340 concern pads within a single footprint under the standalone
0.20 mm default. Fabrication and package evidence must establish suitable rules;
blanket suppression would not resolve them. Zero unconnected items is not
meaningful with zero named pad nets.

Two unchanged U5/L5/L6 pad pairs are reported as hole-clearance findings in the
candidate, but as copper-clearance findings in the predecessor. Their saved pad
geometry is identical. Category counts alone therefore do not establish that a
part moved or a physical conflict was introduced or removed.

Native DRC confirms these remaining optical-connector courtyard conflicts:

- J2: C74, C81, C82, C93, U2 and U21.
- J3: C79, C86, C87, U22 and U3.

The body-box screen still flags C81/C82 against J2 and C86/C87 against J3.
It also retains the PMIC/inductor and bridge/power clashes. No passives were
deleted or scattered around the board to improve its appearance.

## Retained outputs and next placement work

Candidate:
`../../tmp/pcb-connector-candidate-2026-10-13/corrected-01/deepreal-main-pcba-mech-fit-02.kicad_pcb`

Candidate PCB SHA-256:
`970c1e2a82e871d101ab852ab29a1475e24fb5357c8f4c5ff567ac78d27aeda7`.

Sibling outputs include `engineering-layout-export.json`, `fit-screen.json`,
`drc.json`, `paste-export-audit.json` and `connector-fit-review-final.png`.
The parent directory holds `connector-evidence.json`,
`drc-predecessor-comparable.json`, `drc-comparison.json`,
`protected-before.json` and `validation-final.json`.
The single paste Gerber is under `inspection-only-paste`, not a fabrication
output set.

Next, reconcile the bridge and head-power clusters around the J2/J3 strip,
with their associated support components kept together. Audit the actual
package land patterns before adjusting the PMIC/inductor region. Continue the
USB drawing/thickness and motor-current/interface work in parallel with that
placement investigation. Do not promote this candidate into the assembly.

The schematic remains note-only and the board remains unrouted. This pass does
not approve the circuit, stack-up, numbered interfaces, cable or manufacturing.

## Reproduce

From the repository root, use a new output directory:

```sh
'/Users/adam/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3' \
  hardware/electronics/deepreal-main-pcba/scripts/build_pcb_connector_candidate.py \
  --contract "$PWD/docs/design/pcb-mechanical-interface-2026-10-13.json" \
  --predecessor-dir "$PWD/tmp/pcb-fit-candidate-2026-10-13/profile-03" \
  --evidence "$PWD/tmp/pcb-connector-candidate-2026-10-13/connector-evidence.json" \
  --output-dir "$PWD/tmp/new-connector-candidate"

python3 -m unittest discover \
  -s hardware/electronics/deepreal-main-pcba/scripts \
  -p test_pcb_connector_candidate.py -v
```
