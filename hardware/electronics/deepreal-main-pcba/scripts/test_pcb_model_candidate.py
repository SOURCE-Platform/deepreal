import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pcb_model_candidate import (
    ROOT, LOCKED, merge_footprints, reference, transformed_point,
    moved_polygons, verify_layout, in_profile, plan_placements,
)
from export_pcb_model_candidate import checked_layout
from build_pcb_fit_candidate import top_level_blocks


WORK = ROOT / "tmp/pcb-model-candidate-2026-10-13"
BEFORE = ROOT / "tmp/pcb-connector-candidate-2026-10-13/corrected-01"
AFTER = WORK / "placement-03"


class ModelGeometryTests(unittest.TestCase):
    def test_bottom_flip_matches_kicad_not_viewer_rotation(self):
        old = {"position_mm": [106.075, 34], "rotation_deg": 0, "side": "TOP"}
        new = {"position_mm": [116.5, 40.4], "rotation_deg": 0, "side": "BOTTOM"}
        self.assertEqual(transformed_point([103.325, 28.98], old, new), [113.75, 45.42])
        new["rotation_deg"] = 180
        self.assertEqual(transformed_point([103.325, 28.98], old, new), [119.25, 35.38])

    def test_quarter_turn_keeps_contact_distances(self):
        old = {"position_mm": [31, 46.2], "rotation_deg": 0, "side": "TOP"}
        new = {"position_mm": [27, 45.5], "rotation_deg": 90, "side": "TOP"}
        self.assertEqual(transformed_point([31, 51.2], old, new), [32, 45.5])

    def test_profile_step_is_not_bounding_rectangle(self):
        self.assertTrue(in_profile([111, 40, 121, 46]))
        self.assertFalse(in_profile([111, 40, 121, 47]))
        self.assertFalse(in_profile([19.9, 30, 22, 31]))

    def test_polygon_flip_uses_same_registration(self):
        old = {"position_mm": [10, 10], "rotation_deg": 0, "side": "TOP",
               "courtyard_polygons_mm": [[[8, 7], [12, 7], [12, 11], [8, 11]]]}
        result = moved_polygons(old, ([20, 20], 0, "BOTTOM"))
        self.assertEqual(result, [[[18, 23], [22, 23], [22, 19], [18, 19]]])

    def test_merge_preserves_nonfootprint_blocks(self):
        fp = '(footprint "Package" (property "Reference" "U1") (at 1 2))'
        source = '(kicad_pcb (general (thickness 1.6)) ' + fp + ' (gr_line (layer "Edge.Cuts")))'
        saved = source.replace("(at 1 2)", "(at 3 4)")
        self.assertEqual(merge_footprints(source, saved, {"U1"}), saved)
        self.assertEqual(merge_footprints(source, saved, set()), source)
        with self.assertRaises(ValueError):
            merge_footprints(source, saved, {"J1"})

    def test_reference_rejects_ambiguous_properties(self):
        with self.assertRaises(ValueError):
            reference('(footprint "P" (property "Reference" "J1") (property "Reference" "J2"))')


class SavedModelCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((BEFORE / "engineering-layout-export.json").read_text())
        cls.after = json.loads((AFTER / "engineering-layout-export.json").read_text())

    def test_saved_population_and_all_pad_registration(self):
        verify_layout(self.before, self.after)
        self.assertEqual(len(self.after["components"]), 238)
        self.assertEqual(len(self.after["pads"]), 2419)

    def test_pad_size_number_and_angle_mutations_rejected(self):
        for key, value in (("size_mm", [4, 4]), ("number", "invented"), ("rotation_deg", 13)):
            modified = copy.deepcopy(self.after)
            modified["pads"][0][key] = value
            with self.assertRaises(ValueError):
                verify_layout(self.before, modified)

    def test_drill_and_locked_part_mutations_rejected(self):
        modified = copy.deepcopy(self.after)
        modified["holes"][0]["drill_mm"] = [0.8, 0.8]
        with self.assertRaises(ValueError):
            verify_layout(self.before, modified)
        modified = copy.deepcopy(self.after)
        next(c for c in modified["components"] if c["ref"] == "U1")["position_mm"][0] += 1
        with self.assertRaises(ValueError):
            verify_layout(self.before, modified)

    def test_only_moved_footprint_blocks_changed(self):
        a = (BEFORE / self.before["metadata"]["source_board"]).read_text()
        b = (AFTER / self.after["metadata"]["source_board"]).read_text()
        old = top_level_blocks(a)[0]
        new = top_level_blocks(b)[0]
        changed = set(json.loads((AFTER / "fit-screen.json").read_text())["changed_refs"])
        self.assertEqual(len(old), len(new))
        for (_, _, left), (_, _, right) in zip(old, new):
            if not left.startswith("(footprint ") or reference(left) not in changed:
                self.assertEqual(left, right)

    def test_plan_is_deterministic_and_keeps_core(self):
        plan = plan_placements(self.before)
        actual = {c["ref"]: (c["position_mm"], c["rotation_deg"], c["side"])
                  for c in self.after["components"]}
        self.assertEqual(plan, plan_placements(self.before))
        for ref, pose in plan.items():
            self.assertEqual(pose[1:], actual[ref][1:], ref)
            for requested, saved in zip(pose[0], actual[ref][0]):
                # KiCad's FromMM/serialization can quantize one nanometre.
                self.assertLessEqual(abs(requested - saved), 0.000003, ref)
        old = {c["ref"]: c for c in self.before["components"]}
        for ref in LOCKED:
            self.assertEqual(plan[ref][0], old[ref]["position_mm"])

    def test_export_boundary_and_release_locks(self):
        checked_layout(AFTER)
        with self.assertRaises(ValueError):
            checked_layout(ROOT / "hardware/electronics/deepreal-main-pcba")
        self.assertTrue(all(self.after["metadata"][k] is False for k in
                            ("is_canonical", "fabrication_allowed", "public_visual_allowed",
                             "viewer_integration_allowed")))


if __name__ == "__main__":
    unittest.main()
