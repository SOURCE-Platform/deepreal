import unittest

from presentation_pcb_connectivity import CopperSpace, intersects_box, segment_distance


class PresentationCopperTests(unittest.TestCase):
    def setUp(self):
        self.space = CopperSpace([[[20, 20], [122, 20], [122, 48], [20, 48]]])
        self.first = {"ref": "C1", "pad": "1", "position": [30, 30], "aabb_size": [.4, .4]}
        self.second = {"ref": "C1", "pad": "2", "position": [30.7, 30], "aabb_size": [.4, .4]}
        self.space.pad(self.first, [1])
        self.space.pad(self.second, [1])

    def test_exemption_cannot_hide_the_other_terminal(self):
        self.assertTrue(self.space.clear([30, 30], [29.4, 30], 1, .06, exempt=("C1", "1")))
        self.assertFalse(self.space.clear([30, 30], [30.7, 30], 1, .06, exempt=("C1", "1")))

    def test_through_via_checks_pads_on_both_sides(self):
        self.assertFalse(self.space.clear([30, 30], [30, 30], 1, .15, exempt=("C1", "1"), via=True))
        self.assertTrue(self.space.clear([30, 30], [30, 30], 10, .15, via=True))
        self.space.via({"position_mm": [32, 30], "diameter_mm": .3}, "POWER")
        for layer in range(1, 11):
            self.assertFalse(self.space.clear([31.8, 30], [32.2, 30], layer, .08, "OTHER"))

    def test_same_net_can_join_but_different_nets_cannot_cross(self):
        self.space.line(4, [31, 29], [31, 31], .16, "SUPPLY")
        self.assertTrue(self.space.clear([30, 30], [32, 30], 4, .08, "SUPPLY"))
        self.assertFalse(self.space.clear([30, 30], [32, 30], 4, .08, "SIGNAL"))

    def test_entire_edges_are_checked_not_just_the_endpoints(self):
        self.assertTrue(intersects_box([29, 30], [32, 30], [30, 29, 31, 31]))
        self.assertFalse(intersects_box([29, 28], [32, 28], [30, 29, 31, 31]))
        self.assertFalse(intersects_box([82.1, 32.02], [82.5, 31.62], [81.795, 31.045, 82.405, 31.715]))
        self.assertEqual(segment_distance([0, 0], [2, 2], [0, 2], [2, 0]), 0)
        self.assertEqual(segment_distance([0, 0], [1, 0], [2, 0], [3, 0]), 1)


if __name__ == "__main__":
    unittest.main()
