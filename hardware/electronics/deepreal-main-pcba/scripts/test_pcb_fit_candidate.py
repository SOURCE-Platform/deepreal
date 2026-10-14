"""Boundary tests for a separate, explicitly unapproved fit candidate."""

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from build_pcb_fit_candidate import (
    matching_drill, profile_candidate_text, top_level_blocks, validate_inputs,
)


class CandidateBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.output = self.root / "tmp/candidate"
        for name in ("deepreal-main-pcba.kicad_pcb",
                     "engineering-layout-export.json", "design-status.json"):
            (self.project / name).write_text(name)
        source = self.root / "native.blend"
        source.write_text("retained source")
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        self.status = {"fabrication_allowed": False, "public_visual_allowed": False}
        self.contract = {
            "schema": "deepreal.pcb-mechanical-interface.v1",
            **self.status, "viewer_integration_allowed": False,
            "sources_sha256": {"native.blend": sha(source)},
            "source_board_sha256": sha(self.project / "deepreal-main-pcba.kicad_pcb"),
            "source_export_sha256": sha(self.project / "engineering-layout-export.json"),
            "source_status_sha256": sha(self.project / "design-status.json"),
            "profile_loops_kicad_mm": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
        }

    def validate(self, contract=None, status=None, output=None):
        validate_inputs(self.contract if contract is None else contract,
                        self.status if status is None else status,
                        self.output if output is None else output,
                        self.root, self.project)

    def test_separate_locked_candidate_accepted(self):
        self.validate()

    def test_baseline_and_public_outputs_rejected(self):
        for output in (self.project, self.root / "public/candidate"):
            with self.assertRaisesRegex(ValueError, "internal tmp"):
                self.validate(output=output)

    def test_existing_output_rejected(self):
        self.output.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "internal tmp"):
            self.validate()

    def test_release_permission_unknown_or_true_rejected(self):
        for key in ("fabrication_allowed", "public_visual_allowed"):
            for document in ("contract", "status"):
                for value in (None, True, 0):
                    contract, status = copy.deepcopy(self.contract), dict(self.status)
                    (contract if document == "contract" else status)[key] = value
                    with self.assertRaisesRegex(ValueError, "explicitly false"):
                        self.validate(contract, status)

    def test_viewer_integration_not_granted(self):
        contract = dict(self.contract, viewer_integration_allowed=True)
        with self.assertRaisesRegex(ValueError, "integration-blocked"):
            self.validate(contract)

    def test_changed_baseline_rejected(self):
        (self.project / "deepreal-main-pcba.kicad_pcb").write_text("changed")
        with self.assertRaisesRegex(ValueError, "changed candidate input"):
            self.validate()

    def test_changed_blender_source_rejected(self):
        (self.root / "native.blend").write_text("changed")
        with self.assertRaisesRegex(ValueError, "changed mechanical/native"):
            self.validate()

    def test_nonfinite_profile_rejected(self):
        contract = copy.deepcopy(self.contract)
        contract["profile_loops_kicad_mm"][0][0][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "invalid measured profile"):
            self.validate(contract)

    def test_only_matching_circle_reuses_drill(self):
        holes = [{"ref": "H1", "position_mm": [0, 0], "drill_mm": [2, 2]}]
        self.assertEqual(matching_drill([[1, 0], [0, 1], [-1, 0], [0, -1]], holes), "H1")
        self.assertIsNone(matching_drill([[1, 1], [-1, 1], [-1, -1], [1, -1]], holes))
        self.assertIsNone(matching_drill([[2, 0], [0, 2], [-2, 0], [0, -2]], holes))

    def test_profile_edit_preserves_footprint_and_quoted_parentheses(self):
        footprint = '(footprint "a" (property "Reference" "J2 (quoted \\"text\\")"))'
        source = ('(kicad_pcb (version 1) ' + footprint +
                  ' (gr_line (start 0 0) (end 1 0) (layer "Edge.Cuts")))')
        result, cutouts = profile_candidate_text(
            source, [[[0, 0], [2, 0], [2, 1], [0, 1]]], [])
        self.assertIn(footprint, result)
        self.assertEqual(result.count('(layer "Edge.Cuts")'), 4)
        self.assertEqual(cutouts, [])

    def test_profile_edit_is_deterministic(self):
        source = '(kicad_pcb (gr_line (start 0 0) (end 1 0) (layer "Edge.Cuts")))'
        loops = [[[0, 0], [1, 0], [1, 1]]]
        self.assertEqual(profile_candidate_text(source, loops, []),
                         profile_candidate_text(source, loops, []))

    def test_invalid_board_and_trailing_data_rejected(self):
        for source in ('(not_a_board)', '(kicad_pcb (version 1)',
                       '(kicad_pcb) extra'):
            with self.assertRaises(ValueError):
                top_level_blocks(source)


if __name__ == "__main__":
    unittest.main()
