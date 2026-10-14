"""Tests for mechanical PCB profile transport, not engineering signoff."""

import unittest

from pcb_fit_geometry import (
    from_kicad, positive_box_overlap, section_loops, signed_area, to_kicad,
)


class FitGeometryTests(unittest.TestCase):
    def cube(self):
        vertices = [(x, y, z) for x in (0, 2) for y in (0, 1) for z in (0, 3)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                 (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        triangles = [t for a, b, c, d in faces for t in ((a, b, c), (a, c, d))]
        return vertices, triangles

    def test_true_section_not_box(self):
        vertices, triangles = self.cube()
        loop, = section_loops(vertices, triangles, 0.5)
        self.assertEqual(len(loop), 4)
        self.assertAlmostEqual(abs(signed_area(loop)), 6)

    def test_disjoint_loops_retained(self):
        vertices, triangles = self.cube()
        moved = [(x + 5, y, z) for x, y, z in vertices]
        loops = section_loops(vertices + moved, triangles +
                              [tuple(i + 8 for i in t) for t in triangles], 0.5)
        self.assertEqual(len(loops), 2)

    def test_open_section_rejected(self):
        vertices, triangles = self.cube()
        with self.assertRaisesRegex(ValueError, "closed loops"):
            section_loops(vertices, triangles[:-4], 0.5)

    def test_coplanar_section_rejected(self):
        with self.assertRaisesRegex(ValueError, "coplanar"):
            section_loops([(0, 1, 0), (1, 1, 0), (0, 1, 1)], [(0, 1, 2)], 1)

    def test_no_section_rejected(self):
        vertices, triangles = self.cube()
        with self.assertRaisesRegex(ValueError, "no board"):
            section_loops(vertices, triangles, 4)

    def test_core_datum_not_wing_center(self):
        origin = [65, 34]
        self.assertEqual(to_kicad([-45, 2.5], origin, -11.5), [20, 20])
        self.assertEqual(to_kicad([57.5, -25.5], origin, -11.5), [122.5, 48])
        self.assertEqual(from_kicad([43, 46], origin, -11.5), [-22, -23.5])

    def test_coordinate_roundtrip(self):
        for point in [[-45, 2.5], [51.5, -17.6], [-22, -23.5]]:
            self.assertEqual(from_kicad(to_kicad(point, [65, 34], -11.5),
                                       [65, 34], -11.5), point)

    def test_box_screen_excludes_touch(self):
        a = {"min_mm": [0, 0, 0], "max_mm": [1, 1, 1]}
        b = {"min_mm": [1, 0, 0], "max_mm": [2, 1, 1]}
        self.assertIsNone(positive_box_overlap(a, b))
        b["min_mm"][0] = 0.5
        self.assertEqual(positive_box_overlap(a, b), [0.5, 1, 1])


if __name__ == "__main__":
    unittest.main()
