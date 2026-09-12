# DeepReal Electronics Design Source

This directory is the controlled handoff between the system architecture, future
EDA capture, PCB layout and Blender packaging model.

## Designs

- `deepreal-main-pcba/` - stationary 90 x 28 mm compute, power, camera bridge,
  USB and motor-control board.
- `deepreal-optical-head/` - one rotating RGB/IR/projector carrier design. The
  identical design is populated twice, once for each drum.

## What exists now

The files define the sheet hierarchy, component/reference-designator ownership,
named power and signal nets, drum-connector allocation, circuit intent and the
vendor pin maps that must be imported before an ERC-clean EDA schematic can be
claimed. KiCad 10 is installed and the main-board directory contains a navigable
15-page hierarchy plus a real 90 x 28 mm placement study. Several authoritative
BGA pin maps are still not stored locally.

This is electrical design source, but it is **not yet** a completed circuit
schematic, routed netlist or manufacturing package. `TBD_PINMAP` is an explicit
gate, never a guessed connection.

## Release rule

Blender geometry may use the component packages and support-population counts in
this directory. The separately named KiCad/Blender presentation derivative may use
shared illustrative copper labelled `ILLUSTRATIVE COPPER - NOT ELECTRICALLY
ROUTED`. The canonical KiCad board must remain free of decorative copper.
