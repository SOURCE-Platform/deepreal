# Drum-internals feasibility study (exploration branch)

Question: can the two approved Ø24 × 54 mm sensor-head drums physically
contain the sensing hardware (RGB + depth), actuators, bearings, and
wiring needed for 140–160° of motorized rotation — without changing the
approved exterior (`cad/deepreal.FCStd` @ dacd90c)?

This directory holds **Gate 1** of the study (sourced component
envelopes, a registry of manufacturer data, drum context geometry, and a
non-destructive review system) and **Gate 1.5B** (discrete
depth-sensing architectures — RGB sensor assembly, IR camera, SL
projectors, ToF imagers — with three validated in-drum layout studies).
Actuator packaging is the next gate, pending approval.

## Contents

| File | Purpose |
|---|---|
| `registry.py` | Machine-readable component dims/status/evidence (single truth) |
| `component_sources.md` | Provenance: URLs, dims, weights, electrical, CAD assets, discrepancies |
| `envelopes.py` | True-size envelope builders, multi-part aware (library row) |
| `exterior_reference.py` | Read-only copy of the approved exterior |
| `drum_context.py` | Drum shells, assumed interiors, travel markers |
| `layouts.py` | In-drum layout studies SL-A / SL-B / ToF-A (Gate 1.5B) |
| `groups.py` | 19 visibility groups |
| `review_presets.py` | 10 non-destructive review presets |
| `build.py` | Builds `drum_internals.FCStd` |
| `validate_feasibility.py` | Gate 1 + 1.5B checks incl. deepreal.FCStd checksum guard |
| `render_layouts.py` | Schematic SVG cross-sections of the layouts |
| `depth_architecture_report.md` | Gate 1.5B report (11 sections) |
| `assets/` | Downloaded datasheets, drawings, STEP files (see registry) |
| `assets/renders/` | Generated layout schematics (SVG) |

## Rebuild / validate / render

```sh
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD --console cad/feasibility/build.py
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD --console cad/feasibility/validate_feasibility.py
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD --console cad/feasibility/render_layouts.py
```

## Review presets (GUI)

Open `drum_internals.FCStd`, then in the FreeCAD Python console:

```python
import sys; sys.path.insert(0, "<repo>/cad/feasibility")
import review_presets
review_presets.list_presets()
review_presets.apply_preset(7)   # e.g. Depth_Candidates vs drum interior
```

Presets only toggle group visibility and move the camera; they never
modify geometry.

## Gate status

- **Gate 1 (committed):** component envelopes + drum context — done.
- **Gate 1.5B (this working tree): STOP** — discrete depth architectures
  and in-drum layout studies validated; see
  `depth_architecture_report.md`. Awaiting review before any actuator
  packaging work.
