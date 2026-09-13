# Hirose CX90M3-24P source record

- Part: Hirose CX90M3-24P USB Type-C receptacle, CL0480-0919-0-00
- Status: CONFIRMED mechanical candidate
- Manufacturer page: https://www.hirose.com/product/p/CL0480-0919-0-00
- Source file: `CX90M3-24P_4800919000_STEP.stp`
- Retrieved: 2026-09-10
- Manufacturer recommended PCB thickness: 0.8 mm maximum
- Derived file: `CX90M3-24P_4800919000_STEP.stl`
- Conversion: STEP tessellated with Open CASCADE/OCP for Blender import; source
  dimensions remain in millimetres.

The STEP file is the manufacturer-supplied model. The STL is only a Blender
transport derivative and must not be treated as the authoritative drawing.

## Blocking integration issue

The current main-board candidate is 1.6 mm thick. That conflicts with Hirose's
listed 0.8 mm maximum recommended PCB thickness for this mid-mount receptacle.
J1 therefore remains a mechanical/selection candidate, not an approved footprint.
Resolve with an officially supported board treatment, a compatible alternative
receptacle, or a separately engineered connector board.
