#!/usr/bin/env python3
"""Create a separate KiCad outline/H5 placement study, never a release PCB."""

import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = (REPO / "hardware/electronics/deepreal-main-pcba/"
          "deepreal-main-pcba.kicad_pcb")
OUTPUT = HERE / "native-outline-H5-study-NOT-FOR-FAB.kicad_pcb"


def edge(a, b):
    eid = uuid.uuid5(uuid.NAMESPACE_URL, f"deepreal-r12-edge-{a}-{b}")
    return (f'\t(gr_line\n\t\t(start {a[0]} {a[1]})\n'
            f'\t\t(end {b[0]} {b[1]})\n'
            '\t\t(stroke\n\t\t\t(width 0.1)\n'
            '\t\t\t(type default)\n\t\t)\n'
            '\t\t(layer "Edge.Cuts")\n'
            f'\t\t(uuid "{eid}")\n\t)')


def main():
    data = SOURCE.read_text()
    blocks = re.findall(r'\t\(gr_line\n.*?\n\t\)', data, re.S)
    old_edges = [b for b in blocks if '(layer "Edge.Cuts")' in b]
    assert len(old_edges) == 4
    points = [(20, 20), (122.5, 20), (122.5, 46.5),
              (110, 46.5), (110, 48), (20, 48)]
    new_edges = '\n'.join(edge(a, b) for a, b in
                          zip(points, points[1:] + points[:1]))
    for i, block in enumerate(old_edges):
        data = data.replace(block, new_edges if i == 0 else '', 1)

    footprints = re.findall(r'\t\(footprint .*?\n\t\)', data, re.S)
    source_h4 = [b for b in footprints if '(property "Reference" "H4"' in b]
    assert len(source_h4) == 1
    h4 = source_h4[0]
    h5 = h4.replace('(at 107 23)', '(at 117 27.5)', 1).replace(
        '(property "Reference" "H4"', '(property "Reference" "H5"', 1)

    def newid(match):
        uid = uuid.uuid5(uuid.NAMESPACE_URL,
                         "deepreal-r12-h5-" + match.group(1))
        return f'(uuid "{uid}")'

    h5 = re.sub(r'\(uuid "([0-9a-f-]{36})"\)', newid, h5)
    assert h5 != h4 and '(property "Reference" "H5"' in h5
    data = data.replace(h4, h4 + '\n' + h5, 1)
    assert data.count('(layer "Edge.Cuts")') == 6
    assert data.count('\t(footprint ') == len(footprints) + 1
    OUTPUT.write_text(data)
    print("R12 OUTLINE/H5 STUDY", OUTPUT)


if __name__ == "__main__":
    main()
