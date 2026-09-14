#!/usr/bin/env python3
"""Regression tests for the head-interface screen, not electrical sign-off."""

import copy
import csv
import json
from pathlib import Path
import unittest

from head_interface_audit import audit, bounds, capacity_screen, land_pattern_screen, placement_screen, rotate

PROJECT = Path(__file__).resolve().parent.parent


class HeadInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = json.loads((PROJECT/"engineering-layout-export.json").read_text())
        cls.evidence = json.loads((PROJECT/"head-interface-evidence.json").read_text())
        with (PROJECT/"connector-allocation.csv").open() as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_current_capacity_is_only_a_screen(self):
        result = capacity_screen(self.rows, self.evidence)
        self.assertEqual(result["contacts_per_head"], 51)
        self.assertEqual(result["camera_differential_pairs_per_head"], 6)
        self.assertEqual(result["conservative_70_percent_screen_a"], 1.12)
        self.assertEqual(result["screen_input_power_before_losses_w"], 3.696)
        self.assertIsNone(result["required_peak_input_current_a"])
        self.assertTrue(result["power_feasibility"].startswith("BLOCKED"))

    def test_return_contact_count_limits_current(self):
        rows = copy.deepcopy(self.rows)
        next(r for r in rows if r["Group"] == "Power_returns")["Contacts"] = "4"
        self.assertEqual(capacity_screen(rows, self.evidence)[
            "conservative_70_percent_screen_a"], 0.56)

    def test_missing_camera_clock_pair_rejected(self):
        rows = copy.deepcopy(self.rows)
        next(r for r in rows if r["Group"] == "RGB_CSI_signals")["Contacts"] = "4"
        with self.assertRaises(ValueError):
            capacity_screen(rows, self.evidence)

    def test_kicad_rotation_direction_and_round_trip(self):
        points = [[[3, 0], [4, 0], [4, 2], [3, 2]]]
        rotated = rotate(points, [0, 0], [10, 10], 90)
        self.assertEqual(rotated[0][0], [10, 7])
        self.assertEqual(rotate(rotated, [10, 10], [0, 0], -90), points)

    def test_existing_overhangs_are_reported(self):
        for ref in ("J2", "J3"):
            result = placement_screen(self.layout, ref)
            self.assertAlmostEqual(result[
                "outline_overhang_left_top_right_bottom_mm"][3], 6.895, places=3)

    def test_trials_never_mutate_layout(self):
        original = copy.deepcopy(self.layout)
        result = audit(self.rows, self.evidence, self.layout, PROJECT.parents[2])
        self.assertEqual(original, self.layout)
        self.assertEqual(result["interface_status"], "BLOCKED")
        self.assertEqual(len(result["quarter_turn_trials_not_applied"]), 4)
        self.assertFalse(result["public_visual_allowed"])
        self.assertFalse(result["fabrication_allowed"])

    def test_missing_courtyard_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            bounds([])

    def test_pad_dimensions_do_not_certify_pin_numbers(self):
        for ref in ("J2", "J3"):
            result = land_pattern_screen(self.layout, ref, self.evidence)
            self.assertEqual(result["dimension_screen"], "PASS")
            self.assertFalse(result["pin_numbering_audited"])
            self.assertFalse(result["paste_apertures_audited"])

    def test_wrong_pad_size_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        next(p for p in layout["pads"] if p["ref"] == "J2")["size_mm"] = [1, 1]
        self.assertEqual(land_pattern_screen(layout, "J2", self.evidence)["dimension_screen"], "FAIL")

    def test_changed_vendor_source_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["source"]["sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "source hash"):
            audit(self.rows, evidence, self.layout, PROJECT.parents[2])

    def test_missing_evidence_category_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["closure_evidence"].pop("head_safe_default_hardware_interlock")
        with self.assertRaisesRegex(ValueError, "categories"):
            audit(self.rows, evidence, self.layout, PROJECT.parents[2])


if __name__ == "__main__":
    unittest.main()
