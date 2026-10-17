"""Geometry tests only; passing these tests says nothing about circuit function."""

import unittest

from demo_pcb_router import DemoRouter, design_demo, inside_polygon, simplify


OUTLINE = [[20, 20], [32, 20], [32, 29], [20, 29]]


def endpoint(ref, point, layers=(0,)):
    return {"ref": ref, "pad": "1", "position": point, "layers": list(layers),
            "net": "", "aabb_size": [.3, .3]}


class DemoPCBRouterTests(unittest.TestCase):
    def test_polygon_membership_and_cutout(self):
        self.assertTrue(inside_polygon([21, 21], OUTLINE))
        self.assertFalse(inside_polygon([33, 21], OUTLINE))
        hole = [[25, 23], [27, 23], [27, 25], [25, 25]]
        router = DemoRouter([OUTLINE, hole], [])
        self.assertNotIn(router.cell([26, 24]), router.inside)
        self.assertIn(router.cell([22, 24]), router.inside)

    def test_simplification_preserves_bends_and_reversals(self):
        self.assertEqual(simplify([[0, 0], [1, 1], [2, 2], [3, 2]]),
                         [[0, 0], [2, 2], [3, 2]])
        self.assertEqual(simplify([[0, 0], [1, 0], [0, 0]]), [[0, 0], [1, 0], [0, 0]])

    def test_route_terminates_at_exact_pad_centers(self):
        a, b = endpoint("A", [21.13, 21.07]), endpoint("B", [30.11, 26.09])
        router = DemoRouter([OUTLINE], [a, b])
        self.assertTrue(router.route(a, b))
        connection = router.routes[0]
        self.assertEqual(connection["paths"][0]["points"][0], a["position"])
        self.assertEqual(connection["paths"][-1]["points"][-1], b["position"])
        self.assertTrue(connection["id"].startswith("DEMO_"))
        self.assertNotIn("signal", connection)

    def test_paths_stay_on_the_native_board_and_avoid_cutout(self):
        hole = [[25, 23], [27, 23], [27, 25], [25, 25]]
        a, b = endpoint("A", [22, 24]), endpoint("B", [30, 24])
        router = DemoRouter([OUTLINE, hole], [a, b])
        self.assertTrue(router.route(a, b))
        for path in router.routes[0]["paths"]:
            for point in path["points"]:
                self.assertTrue(inside_polygon(point, OUTLINE))
                self.assertFalse(inside_polygon(point, hole))

    def test_mixed_surface_connections_have_native_via_positions(self):
        a, b = endpoint("A", [22, 22], (0,)), endpoint("B", [30, 26], (1,))
        router = DemoRouter([OUTLINE], [a, b])
        self.assertTrue(router.route(a, b))
        self.assertEqual({p["layer"] for p in router.routes[0]["paths"]}, {0, 1})
        self.assertGreater(len(router.vias), 0)

    def test_invalid_endpoint_cannot_route_outside_board(self):
        router = DemoRouter([OUTLINE], [])
        self.assertFalse(router.route(endpoint("A", [18, 18]), endpoint("B", [30, 26])))
        self.assertEqual(router.routes, [])
        self.assertEqual(router.failures, 1)

    def test_existing_named_electrical_pads_are_not_demo_candidates(self):
        a, b = endpoint("U1", [22, 22]), endpoint("U4", [28, 22])
        a["net"], b["net"] = "ACTUAL_POWER", "ACTUAL_SIGNAL"
        result = design_demo({"pads": [a, b], "centers": {"U1": [22, 22], "U4": [28, 22]},
                              "outlines": [OUTLINE], "existing_surface_tracks": []})
        self.assertEqual(result["connections"], [])
        self.assertEqual(result["vias"], [])


if __name__ == "__main__":
    unittest.main()
