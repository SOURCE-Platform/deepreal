#!/usr/bin/env python3
"""Make an isolated KiCad board-outline study; never edit the source board."""

import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = (REPO / "hardware/electronics/deepreal-main-pcba/"
          "deepreal-main-pcba.kicad_pcb")
OUTPUT = HERE / "native-outline-study-NOT-FOR-FAB.kicad_pcb"


def edge(a, b):
    edge_id = uuid.uuid5(uuid.NAMESPACE_URL, f"deepreal-r10-edge-{a}-{b}")
    return (f'\t(gr_line\n\t\t(start {a[0]} {a[1]})\n'
            f'\t\t(end {b[0]} {b[1]})\n'
            '\t\t(stroke\n\t\t\t(width 0.1)\n'
            '\t\t\t(type default)\n\t\t)\n'
            '\t\t(layer "Edge.Cuts")\n'
            f'\t\t(uuid "{edge_id}")\n\t)')


def main():
    data = SOURCE.read_text()
    blocks = re.findall(r'\t\(gr_line\n.*?\n\t\)', data, re.S)
    old = [block for block in blocks if '(layer "Edge.Cuts")' in block]
    assert len(old) == 4, f"expected four original outline edges, found {len(old)}"
    outline = [(20, 20), (110, 20), (110, 32.5), (122.5, 32.5),
               (122.5, 45), (110, 45), (110, 48), (20, 48)]
    replacement = '\n'.join(edge(a, b) for a, b in
                            zip(outline, outline[1:] + outline[:1]))
    for index, block in enumerate(old):
        data = data.replace(block, replacement if index == 0 else '', 1)
    assert data.count('(layer "Edge.Cuts")') == len(outline)
    OUTPUT.write_text(data)
    print("OUTLINE STUDY", OUTPUT)


if __name__ == "__main__":
    main()
