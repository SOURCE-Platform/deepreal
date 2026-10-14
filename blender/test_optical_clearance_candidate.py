#!/usr/bin/env python3
"""Blender regression checks for the scoped optical-opening candidate."""

import json
from pathlib import Path
import sys
import unittest

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_optical_clearance_candidate as builder  # noqa: E402
from pcb_solid_fit import snapshot  # noqa: E402


class OpticalClearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = HERE.parent / "tmp/assembly-corrections-2026-10-14/optical-04"
        cls.audit = json.loads((cls.output / "optical-clearance-audit.json").read_text())
        bpy.ops.wm.open_mainfile(filepath=str(cls.output / "deepreal-optical-clearance-candidate.blend"))
        bpy.context.view_layer.update()

    def test_exactly_one_mechanical_mesh_changes(self):
        self.assertEqual(self.audit["changed_geometry_objects"], [builder.SLEEVE])
        before = self.audit["geometry_hashes_before"]
        after = self.audit["geometry_hashes_after"]
        self.assertEqual(set(before), set(after))
        self.assertEqual([name for name in before if before[name] != after[name]], [builder.SLEEVE])
        for name, expected in after.items():
            self.assertEqual(builder.geometry_hash(bpy.data.objects[name]), expected, name)

    def test_sleeve_remains_closed_and_connected(self):
        solid = snapshot(bpy.data.objects[builder.SLEEVE])
        self.assertEqual(solid["nonmanifold_edges"], 0)
        self.assertEqual(len(solid["representatives"]), 1)
        self.assertGreater(self.audit["retained_volume_fraction"], .95)
        self.assertLess(self.audit["retained_volume_fraction"], 1)

    def test_nominal_load_path_overlaps_remain(self):
        for contact in self.audit["nominal_load_path_overlaps"].values():
            self.assertEqual(contact["before"]["status"], "POSITIVE_NOMINAL_SOLID_INTERSECTION")
            self.assertEqual(contact["after"]["status"], "POSITIVE_NOMINAL_SOLID_INTERSECTION")
            self.assertGreater(contact["after"]["intersection_volume_mm3"], .00001)

    def test_matching_bore_removes_sleeve_occlusion(self):
        before = next(a for a in self.audit["opening_audit_before"] if a["aperture"] == "Face_Depth")
        after = next(a for a in self.audit["opening_audit_after"] if a["aperture"] == "Face_Depth")
        self.assertGreater(before["blockers"].get(builder.SLEEVE, 0), 0)
        self.assertNotIn(builder.SLEEVE, after["blockers"])
        self.assertEqual(after["unexpected_blockers"], {})
        self.assertEqual(after["blocked_rays"], after["retaining_baffle_edge_hits"])
        self.assertLess(after["blocked_rays"], before["blocked_rays"])

    def test_all_ten_openings_have_no_unexpected_normal_blockers(self):
        self.assertEqual(len(self.audit["opening_audit_after"]), 10)
        for aperture in self.audit["opening_audit_after"]:
            self.assertEqual(aperture["sampled_rays"], 197)
            self.assertEqual(aperture["unexpected_blockers"], {}, aperture["aperture"])

    def test_projector_axis_comes_from_evaluated_geometry(self):
        for prefix in ("Face", "Interaction"):
            camera_axis = builder.window_frame(prefix, "Depth")["outward"]
            for kind in ("ProjA", "ProjB", "Pinhole"):
                frame = builder.window_frame(prefix, kind)
                self.assertGreater(frame["outward"].dot(camera_axis), .99999)

    def test_unexpected_window_radius_rejected_before_cut(self):
        sleeve = bpy.data.objects[builder.SLEEVE]
        before = builder.geometry_hash(sleeve)
        frame = builder.window_frame("Face", "Depth")
        frame["radius"] += .001
        with self.assertRaisesRegex(ValueError, "unexpected depth window radius"):
            builder.apply_matching_bore(sleeve, frame)
        self.assertEqual(builder.geometry_hash(sleeve), before)

    def test_no_red_materials_in_normal_saved_review(self):
        targets = [o for o in bpy.context.scene.objects if o.type == "MESH"
                   and not o.hide_render and not o.hide_get()
                   and (o.get("PCBA_Ref") == "J1" or o.data.name.endswith("_PCB"))]
        self.assertEqual(len(targets), 2)
        for obj in targets:
            self.assertFalse(any(m and m.name == "Measured collision red" for m in obj.data.materials))

    def test_release_gates_stay_closed(self):
        for flag in ("fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed"):
            self.assertIs(self.audit[flag], False)
        for cone in self.audit["rgb_cone_audit_after"]:
            self.assertEqual(cone["qualification"], "PLACEHOLDER_PUPIL_SCREEN_NOT_OPTICAL_FOV_APPROVAL")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OpticalClearanceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
