"""Blender regression tests for evaluated, whole-board installation."""

import math
import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pcb_package_review import box, register_board


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.objects = []
        for ref, offset in (("J1", (.0515, -.0064, -.003)), ("U1", (0, 0, .002))):
            mesh = bpy.data.meshes.new(ref + "_body")
            mesh.from_pydata(
                [(x * .002, y * .001, z * .0005)
                 for x, y, z in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                 (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))],
                [], ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)))
            obj = bpy.data.objects.new(ref, mesh)
            bpy.context.scene.collection.objects.link(obj)
            obj["PCBA_Ref"] = ref
            obj.location = offset
            self.objects.append(obj)
        bpy.context.view_layer.update()
        self.audit = {"body_bounds_native_mm": {o["PCBA_Ref"]: box(o) for o in self.objects}}
        self.transform = Matrix.Translation((0, .012105, -.0115)) @ \
            Matrix.Rotation(math.pi / 2, 4, "X")

    def test_pending_world_matrices_are_evaluated_before_registration(self):
        # Change source transforms without a dependency-graph update.
        for obj in self.objects:
            obj.location.x += .003
            for key in ("min_mm", "max_mm"):
                self.audit["body_bounds_native_mm"][obj["PCBA_Ref"]][key][0] += 3
        result = register_board(self.objects, self.transform, self.audit)
        j1 = self.objects[0]
        expected = self.transform @ Vector((.0545, -.0064, -.003))
        self.assertLess((j1.matrix_world.translation - expected).length * 1000, .00005)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["vertices_checked"], 16)

    def test_relative_geometry_and_vertices_are_preserved(self):
        before = [[v.co.copy() for v in o.data.vertices] for o in self.objects]
        result = register_board(self.objects, self.transform, self.audit)
        for obj, points in zip(self.objects, before):
            self.assertEqual([tuple(v.co) for v in obj.data.vertices], [tuple(p) for p in points])
        self.assertLess(result["max_rigid_transform_vertex_error_mm"], .00005)
        self.assertLess(result["max_rigid_transform_bound_error_mm"], .00005)
        self.assertAlmostEqual(self.objects[0].matrix_world.translation.x, .0515, places=7)

    def test_wrong_source_bounds_rejected_before_moving(self):
        before = [o.matrix_world.copy() for o in self.objects]
        self.audit["body_bounds_native_mm"]["J1"]["min_mm"][0] += 1
        with self.assertRaisesRegex(ValueError, "standalone bounds"):
            register_board(self.objects, self.transform, self.audit)
        self.assertEqual([o.matrix_world for o in self.objects], before)

    def test_transform_parent_rejected(self):
        parent = bpy.data.objects.new("Unexpected parent", None)
        bpy.context.scene.collection.objects.link(parent)
        self.objects[0].parent = parent
        with self.assertRaisesRegex(ValueError, "transform parents"):
            register_board(self.objects, self.transform, self.audit)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RegistrationTests))
    if not result.wasSuccessful():
        raise SystemExit(1)
