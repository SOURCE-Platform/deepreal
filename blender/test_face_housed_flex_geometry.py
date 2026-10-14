"""Run with Python; these tests do not need Blender."""

import math
import unittest

from face_housed_flex_geometry import (
    radial_distance,
    return_space_screen,
    ribbon_corner_radius,
    rotate_x,
)


CHAMBER = ((-26, -.2), (13, 20), (10.5, 28.5))


class FaceFlexGeometryTests(unittest.TestCase):
    def test_identity_pose(self):
        point = (-33, -1.65, 20)
        self.assertEqual(rotate_x(point, (0, -1.5, 20), 0), point)

    def test_quarter_turn(self):
        self.assertEqual(rotate_x((4, 2, 0), (0, 0, 0), 90)[0], 4)
        self.assertAlmostEqual(rotate_x((4, 2, 0), (0, 0, 0), 90)[2], 2)

    def test_rotation_preserves_radius_and_x(self):
        point, pivot = (-33, -1.65, 20), (0, -1.5, 20)
        for angle in range(-45, 46, 5):
            moved = rotate_x(point, pivot, angle)
            self.assertEqual(moved[0], point[0])
            self.assertAlmostEqual(radial_distance(moved, pivot), .15)

    def test_endpoint_travel_is_not_orientation_travel(self):
        point, pivot = (-33, -1.65, 20), (0, -1.5, 20)
        low, high = [rotate_x(point, pivot, angle) for angle in (-45, 45)]
        self.assertAlmostEqual(math.dist(low, high), .15 * math.sqrt(2))

    def test_corner_radius(self):
        self.assertAlmostEqual(ribbon_corner_radius(15.6, .2), math.hypot(7.8, .1))

    def test_supplier_example_rejected_even_at_lower_radius_boundary(self):
        result = return_space_screen(CHAMBER, 15.6, .12, 0, 12)
        self.assertTrue(result["axial_width_bound_satisfied"])
        self.assertFalse(result["diameter_bound_satisfied"])
        self.assertAlmostEqual(result["usable_yz_diagonal_mm"], math.hypot(7, 18))

    def test_small_radius_is_not_route_approval(self):
        result = return_space_screen(CHAMBER, 15.6, .12, .25, 3)
        self.assertTrue(result["necessary_bounds_satisfied"])
        self.assertFalse(result["route_qualified"])

    def test_width_cannot_be_ignored(self):
        result = return_space_screen(((0, 10), (0, 50), (0, 50)), 15.6, .12, 0, 3)
        self.assertTrue(result["diameter_bound_satisfied"])
        self.assertFalse(result["necessary_bounds_satisfied"])

    def test_thickness_and_clearance_reduce_radius_bound(self):
        loose = return_space_screen(CHAMBER, 15.6, .12, 0, 3)
        tight = return_space_screen(CHAMBER, 15.6, .2, .5, 3)
        self.assertLess(tight["maximum_inside_radius_from_chord_bound_mm"],
                        loose["maximum_inside_radius_from_chord_bound_mm"])

    def test_collapsed_clearance_is_not_diagonal_space(self):
        result = return_space_screen(((0, 30), (0, 1), (0, 1)), 15.6, .12, 1, 2)
        self.assertEqual(result["usable_yz_diagonal_mm"], 0)
        self.assertFalse(result["diameter_bound_satisfied"])

    def test_invalid_dimensions_rejected(self):
        for width, thickness, clearance, radius in (
            (0, .12, 0, 3), (15.6, 0, 0, 3), (15.6, .12, -1, 3),
            (15.6, .12, 0, 0), (float("nan"), .12, 0, 3),
        ):
            with self.assertRaises(ValueError):
                return_space_screen(CHAMBER, width, thickness, clearance, radius)

    def test_inverted_bounds_rejected(self):
        with self.assertRaises(ValueError):
            return_space_screen(((1, 0), (0, 10), (0, 10)), 15.6, .12, 0, 3)


if __name__ == "__main__":
    unittest.main()
