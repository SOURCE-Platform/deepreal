"""Independently reopen and verify the final private correction review."""

import json
import math
import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Matrix

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_assembly_corrections_review import WORK, CHANGED, inputs
from build_pcb_package_review import BOARD_COLLECTION, CONTRACT_PATH
from build_pcb_candidate_review import box
from build_optical_clearance_candidate import geometry_hash
from pcb_candidate_review_data import ROOT, digest
from audit_pcb_candidate_transport import capture, distance_to


class AssemblyCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = WORK / "model-03"
        cls.audit = json.loads((cls.directory / "corrections-review-audit.json").read_text())
        cls.layout, cls.manifest, _ = inputs(WORK / "package-07", WORK / "optical-04")
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "tmp/pcb-package-fit-2026-10-13/model-04/deepreal-mech-fit-04-board.blend"))
        cls.old_bodies = capture([o for o in bpy.data.collections[BOARD_COLLECTION].objects if o.get("PCBA_Ref")])
        bpy.ops.wm.open_mainfile(filepath=str(cls.directory / "deepreal-mech-fit-05-board.blend"))
        cls.native = capture(bpy.data.collections[BOARD_COLLECTION].objects)
        cls.new_bounds = {o["PCBA_Ref"]: box(o) for o in bpy.data.collections[BOARD_COLLECTION].objects
                          if o.get("PCBA_Ref")}
        cls.substrate_bounds = box(next(o for o in bpy.data.collections[BOARD_COLLECTION].objects
                                       if o.data.name.endswith("_PCB")))
        bpy.ops.wm.open_mainfile(filepath=str(cls.directory / "deepreal-assembly-corrections-review.blend"))
        bpy.context.view_layer.update()
        cls.installed = list(bpy.data.collections[BOARD_COLLECTION].objects)

    def test_all_saved_artifacts_have_current_hashes(self):
        for name, sha in self.audit["output_sha256"].items():
            self.assertEqual(digest(self.directory / name), sha)
        self.assertEqual(self.audit["source_board_sha256"], self.manifest["source_board_sha256"])

    def test_three_maximum_envelopes_have_correct_dimensions(self):
        for ref, expected in CHANGED.items():
            bounds = self.new_bounds[ref]
            actual = [b-a for a, b in zip(bounds["min_mm"], bounds["max_mm"])]
            for a, b in zip(actual, expected):
                self.assertAlmostEqual(a, b, delta=.00005)

    def test_other_231_component_bodies_are_preserved(self):
        for key, old in self.old_bodies.items():
            if key.removeprefix("ref:") in CHANGED:
                continue
            new = self.native[key]
            self.assertEqual(len(old), len(new), key)
            self.assertLessEqual(max(distance_to(old, new), distance_to(new, old)), .00005, key)
        self.assertEqual(len(self.old_bodies)-len(CHANGED), 231)

    def test_rigid_datum_is_correct_for_every_saved_board_vertex(self):
        contract = json.loads(CONTRACT_PATH.read_text())["coordinate_system"]
        z = sum(self.substrate_bounds[k][2] for k in ("min_mm", "max_mm")) / 2 * .001
        transform = Matrix.Translation((0, -contract["board_center_web_depth_mm"]*.001+z,
                                        contract["board_center_height_mm"]*.001)) @ \
            Matrix.Rotation(math.pi/2, 4, "X")
        actual = capture(self.installed)
        self.assertEqual(actual.keys(), self.native.keys())
        maximum = 0
        for key, points in self.native.items():
            expected = [transform @ (p*.001)*1000 for p in points]
            self.assertEqual(len(expected), len(actual[key]), key)
            maximum = max(maximum, max((a-b).length for a, b in zip(expected, actual[key])))
        self.assertLessEqual(maximum, .00005)
        self.assertEqual(len(actual), 240)

    def test_retained_mechanical_geometry_matches_saved_audit(self):
        hashes = self.audit["fit"]["retained_geometry_hashes"]
        self.assertEqual({name: geometry_hash(bpy.data.objects[name]) for name in hashes}, hashes)
        self.assertIn("R35_Face_Outer_Drum_Wall_Sleeve_ENV", hashes)

    def test_sampled_openings_and_rgb_cones_stay_clear_of_unexpected_structure(self):
        fit = self.audit["fit"]
        self.assertEqual(len(fit["opening_audit"]), 10)
        for opening in fit["opening_audit"]:
            self.assertEqual(opening["sampled_rays"], 197)
            self.assertEqual(opening["unexpected_blockers"], {})
        for cone in fit["rgb_cone_audit"]:
            self.assertEqual(cone["sampled_rays"], 221)
            self.assertEqual(cone["blocked_rays"], 0)
            self.assertIn("NOT_OPTICAL", cone["qualification"])

    def test_usb_fit_failures_remain_explicit_not_cosmetically_cleared(self):
        findings = self.audit["fit"]["rest_findings"]
        positives = [r for r in findings if r["status"] == "POSITIVE_NOMINAL_SOLID_INTERSECTION"]
        self.assertEqual(len(positives), 4)
        self.assertEqual({r["ref"] for r in positives}, {"J1", "BOARD_SUBSTRATE"})
        self.assertTrue(all(r["mechanical"].startswith("USB_C_") for r in positives))
        self.assertEqual(self.audit["fit"]["rest_status_counts"]["OPEN_GEOMETRY_UNRESOLVED"], 445)
        self.assertEqual(self.audit["fit"]["rest_status_counts"]["BOOLEAN_TOPOLOGY_UNRESOLVED"], 1)

    def test_normal_usb_materials_and_source_labels(self):
        targets = [o for o in self.installed if o.get("PCBA_Ref") == "J1" or o.data.name.endswith("_PCB")]
        self.assertEqual(len(targets), 2)
        for obj in targets:
            self.assertFalse(any(m and m.name.startswith("Measured collision red") for m in obj.data.materials))
            self.assertEqual(obj["PCBA_SourceBoardHash"], self.manifest["source_board_sha256"])
        for ref in CHANGED:
            obj = next(o for o in self.installed if o.get("PCBA_Ref") == ref)
            self.assertEqual(obj["PCBA_ModelStatus"], "MANUFACTURER_MAXIMUM_BOUNDING_ENVELOPE_NOT_DETAILED_MODEL")

    def test_sampled_motion_transport_and_release_limits(self):
        fit = self.audit["fit"]
        self.assertEqual(len(fit["rigid_pose_samples"]["Face"]["angles_deg"]), 19)
        self.assertEqual(len(fit["rigid_pose_samples"]["Interaction"]["angles_deg"]), 10)
        self.assertTrue(all(not r["events"] for r in fit["rigid_pose_samples"].values()))
        self.assertLessEqual(fit["restored_matrix_error"], 1e-8)
        self.assertEqual(self.audit["board"]["transport"]["status"], "PASS")
        self.assertLessEqual(self.audit["board"]["transport"]["max_bidirectional_vertex_error_mm"], .00005)
        for flag in ("fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed"):
            self.assertIs(self.audit[flag], False)


if __name__ == "__main__":
    unittest.main(verbosity=2, argv=[sys.argv[0]])
