"""Small numerical regressions for the sampled mounting-contact audit.

Run with Blender, without loading or saving a source assembly.
"""

import sys
import unittest
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_web_camera_mount import mesh_signature, nearest_contact_depth, point_triangle_distance, sampled_gap
from export_web_assembly import cut_web_proxy
from web_camera_mount import HEADS, box, create_optical_support, material, optical_support_contacts


class TriangleDistanceTests(unittest.TestCase):
    triangle = ((0, 0, 0), (2, 0, 0), (0, 2, 0))

    def test_face_projection(self):
        self.assertAlmostEqual(point_triangle_distance((.5, .5, .3), *self.triangle), .3)

    def test_edge_projection(self):
        self.assertAlmostEqual(point_triangle_distance((1, -1, 0), *self.triangle), 1)

    def test_vertex_projection(self):
        self.assertAlmostEqual(point_triangle_distance((-1, -1, 0), *self.triangle), 2**.5)

    def test_degenerate_triangle(self):
        self.assertAlmostEqual(point_triangle_distance(
            (.5, 2, 0), (0, 0, 0), (1, 0, 0), (1, 0, 0)), 2)

    def test_thin_face_does_not_create_intrusion(self):
        self.assertAlmostEqual(point_triangle_distance(
            (-40, .005, .00001), (-50, 0, 0), (0, 0, 0), (-50, .05, 0)), .00001)


class SolidContactTests(unittest.TestCase):
    def pair(self, separation):
        mat = material("TEST_Contact", (.5, .5, .5))
        first = box("TEST_First", ((-1, 1), (-1, 1), (-1, 1)), Matrix.Identity(4), mat)
        second = box("TEST_Second", ((1 + separation, 3 + separation), (-1, 1), (-1, 1)),
                     Matrix.Identity(4), mat)
        self.addCleanup(self.remove, first, second)
        return first, second

    @staticmethod
    def remove(*objects):
        import bpy
        for obj in objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    def test_touching_surfaces(self):
        a, b = self.pair(0)
        self.assertLess(sampled_gap(a, b), .001)
        self.assertLess(nearest_contact_depth(a, b), .001)

    def test_real_intrusion_is_rejected(self):
        a, b = self.pair(-.2)
        self.assertAlmostEqual(nearest_contact_depth(a, b), .2, places=4)

    def test_disconnected_surfaces(self):
        a, b = self.pair(.25)
        self.assertAlmostEqual(sampled_gap(a, b), .25, places=4)
        self.assertEqual(nearest_contact_depth(a, b), 0)


class OpticalSupportTests(unittest.TestCase):
    def proposal(self, side):
        import bpy
        before = set(bpy.data.objects)
        self.addCleanup(self.remove_added, before)
        config = HEADS[side]
        frame = Matrix.Identity(4)
        mat = material("TEST_Optical_Support", (.2, .2, .2))
        front = config["carrier_rear_mm"] + 1
        objects = [
            box(config["camera"], ((-5.4, 5.4), (-5.4, 5.4), (-.3, .3)), frame, mat),
            box(config["lens"], ((-2, 2), (-2, 2), (0, config["lens_depth_mm"])), frame, mat),
            box(f"{side}_Internal_Optical_Carrier_WEB",
                ((-41, -7.9), (-6, 6), (front - 1, front)), frame, mat),
            box(f"{side}_SL_Projector_Bracket_WEB",
                ((-16.2, -13.2), (-.7, 2.3), (front - 1.8, front - .2)), frame, mat),
            box(f"{side}_SL_Projector_Body_WEB",
                ((-17.5, -11.9), (-2.2, 3.8), (front + .1, front + 4.1)), frame, mat),
            box(f"{side}_IR_Depth_Module_Body_WEB",
                ((-42, -34), (-4, 4), (front + .6, front + 4.6)), frame, mat),
        ]
        signatures = {obj.name: mesh_signature(obj) for obj in objects
                      if obj.name.endswith(("Module_Body_WEB", "SL_Projector_Body_WEB"))}
        added, _ = create_optical_support(objects, cut_web_proxy, side)
        objects = {obj.name: obj for obj in objects + added}
        for name, signature in signatures.items():
            self.assertEqual(mesh_signature(objects[name]), signature)
        return objects

    @staticmethod
    def remove_added(before):
        import bpy
        for obj in set(bpy.data.objects) - before:
            bpy.data.objects.remove(obj, do_unlink=True)

    def check_contacts(self, side):
        objects = self.proposal(side)
        for a, b in optical_support_contacts(side):
            with self.subTest(parts=(a, b)):
                self.assertLess(sampled_gap(objects[a], objects[b]), .001)
                self.assertLess(nearest_contact_depth(objects[a], objects[b]), .001)

    def test_face_supports_connect_without_intrusion(self):
        self.check_contacts("Face")

    def test_interaction_supports_connect_without_intrusion(self):
        self.check_contacts("Interaction")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if not result.wasSuccessful():
        raise RuntimeError("Camera mount audit regressions failed")
