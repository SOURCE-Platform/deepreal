"""Scoped source, fresh-parse and mutation tests for MECH-FIT-04."""

import copy
import json
import unittest
from pathlib import Path

from build_pcb_package_candidate import (
    ROOT, LABELS, checked_predecessor, fix_back_labels, verify_scope,
)
from build_pcb_fit_candidate import top_level_blocks, courtyard_candidates
from build_pcb_connector_candidate import child
from build_pcb_model_candidate import reference
from pcb_package_review_data import checked_inputs


DIRECTORY = ROOT / "tmp/pcb-package-fit-2026-10-13/package-02"
PREVIOUS = ROOT / "tmp/pcb-model-candidate-2026-10-13/placement-03"


class PackageCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before, cls.source = checked_predecessor(PREVIOUS)
        cls.after, cls.manifest = checked_inputs(DIRECTORY, DIRECTORY / "unused-test-output")
        cls.board_path = DIRECTORY / cls.after["metadata"]["source_board"]

    def test_scoped_population_and_pad_changes(self):
        verify_scope(self.before, self.after)

    def test_all_unrelated_source_blocks_byte_identical(self):
        def retained(text):
            return [b for _, _, b in top_level_blocks(text)[0] if not (
                b.startswith("(footprint ") and reference(b) == "D2") and not (
                b.startswith("(gr_text ") and any(identity in b for identity in LABELS))]
        self.assertEqual(retained(self.source.read_text()), retained(self.board_path.read_text()))

    def test_back_labels_change_only_justification(self):
        def texts(text):
            return {child(b, "gr_text", "uuid")[2]: b for _, _, b in top_level_blocks(text)[0]
                    if b.startswith("(gr_text ") and any(identity in b for identity in LABELS)}
        expected = texts(fix_back_labels(self.source.read_text()))
        self.assertEqual(expected, texts(self.board_path.read_text()))
        self.assertEqual(len(expected), 2)
        self.assertTrue(all("(justify mirror)" in b for b in expected.values()))

    def test_back_label_repeated_or_missing_fix_rejected(self):
        with self.assertRaises(ValueError):
            fix_back_labels(self.board_path.read_text())
        with self.assertRaises(ValueError):
            fix_back_labels(self.source.read_text().replace(next(iter(LABELS)), "unexpected-uuid"))

    def test_d2_numbered_pad_registration(self):
        expected = {"1": [115.575, 32.85], "2": [115.575, 32.15], "3": [116.425, 32.5]}
        pads = [p for p in self.after["pads"] if p["ref"] == "D2"]
        self.assertEqual(len(pads), 3)
        self.assertEqual({p["number"]: p["position_mm"] for p in pads}, expected)
        for pad in pads:
            self.assertEqual(pad["rotation_deg"], 90)
            self.assertTrue(pad["copper_bottom"] and pad["mask_open_bottom"])
            self.assertFalse(pad["copper_top"] or pad["mask_open_top"])
        old = {p["uuid"] for p in self.before["pads"] if p["ref"] == "D2"}
        self.assertFalse(old & {p["uuid"] for p in pads})

    def test_no_new_courtyard_candidates(self):
        self.assertEqual(courtyard_candidates(self.after["components"]), [])

    def test_fresh_native_parse_all_seven_sections(self):
        import export_kicad_design as cad
        import pcbnew
        board = pcbnew.LoadBoard(str(self.board_path))
        tracks, vias = cad.copper(board)
        actual = {"board": cad.board_outline(board), "components": cad.components(board),
                  "pads": cad.pads(board), "holes": cad.holes(board), "tracks": tracks,
                  "vias": vias, "zones": cad.zones(board)}
        for key, value in actual.items():
            self.assertEqual(value, self.after[key], key)
        labels = [t for t in board.GetDrawings()
                  if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() in LABELS.values()]
        self.assertEqual(len(labels), 2)
        self.assertTrue(all(t.IsMirrored() for t in labels))

    def test_unscoped_pad_and_component_mutations_rejected(self):
        for section, index, key, value in (
            ("pads", 0, "size_mm", [9, 9]),
            ("components", 0, "position_mm", [1, 1]),
            ("components", 0, "uuid", "changed"),
        ):
            data = copy.deepcopy(self.after)
            data[section][index][key] = value
            with self.assertRaises(ValueError):
                verify_scope(self.before, data)

    def test_d2_pose_and_pin_mutations_rejected(self):
        data = copy.deepcopy(self.after)
        next(c for c in data["components"] if c["ref"] == "D2")["side"] = "TOP"
        with self.assertRaises(ValueError):
            verify_scope(self.before, data)
        data = copy.deepcopy(self.after)
        next(p for p in data["pads"] if p["ref"] == "D2")["position_mm"][0] += 0.1
        with self.assertRaises(ValueError):
            verify_scope(self.before, data)
        data = copy.deepcopy(self.after)
        next(p for p in data["pads"] if p["ref"] == "D2")["number"] = "4"
        with self.assertRaises(ValueError):
            verify_scope(self.before, data)

    def test_nonprivate_or_existing_output_rejected(self):
        for output in (ROOT / "blender/review-output", DIRECTORY):
            with self.assertRaises(ValueError):
                checked_inputs(DIRECTORY, output)

    def test_backwards_revision_guard_remains_separate(self):
        from pcb_candidate_review_data import checked_inputs as previous_guard
        with self.assertRaises(ValueError):
            previous_guard(DIRECTORY, DIRECTORY / "unused-test-output")


if __name__ == "__main__":
    unittest.main()
