"""Tests for a locked, source-level optical connector study."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from build_pcb_connector_candidate import (
    LIBRARY_PART, PASTE, children, connector_candidate_text, correct_footprint,
    digest, inset_positions, transform_bodies, validate_predecessor, verify_layout,
)


def footprint(ref):
    pads = []
    index = 0
    for size, (_, count) in PASTE.items():
        for _ in range(count):
            index += 1
            number = str(index) if size != (0.95, 0.4) else "MP"
            pads.append(
                '(pad "{}" smd rect (at 1 {}) (size {} {}) '
                '(layers "F.Cu" "F.Mask" "F.Paste") (uuid "{}-{}"))'.format(
                    number, index, *size, ref, index))
    return ('(footprint "' + LIBRARY_PART + '" (layer "F.Cu") (at 43 46) '
            '(property "Reference" "' + ref + '" (at -0.27 -9.6 0)) '
            '(property "Value" "FH26W (unapproved)" (at 0 9.6 0)) ' +
            " ".join(pads) + ' (model "retained.step" (rotate (xyz 0 0 0))))')


class ConnectorTextTests(unittest.TestCase):
    def setUp(self):
        self.other = '(footprint "other" (property "Reference" "U1"))'
        self.source = '(kicad_pcb (version 1) ' + footprint("J2") + " " + \
            self.other + " " + footprint("J3") + \
            ' (gr_line (start 1 0) (end 1 1) (layer "Edge.Cuts")))'
        self.positions = {"J2": [43, 45.055], "J3": [87, 45.055]}

    def test_child_offsets_match_original_root(self):
        text = '(pad "1" (at 0 1) (uuid "a (quoted \\"value\\")"))'
        blocks = children(text, "pad")
        self.assertEqual(len(blocks), 2)
        for start, end, block in blocks:
            self.assertEqual(text[start:end], block)

    def test_correction_keeps_copper_numbers_sizes_and_model(self):
        source = footprint("J2")
        result = correct_footprint(source, "J2", [43, 45.055])
        self.assertIn('(at 43 45.055 90)', result)
        self.assertIn('(at -0.27 -9.6 90)', result)
        self.assertIn('(model "retained.step" (rotate (xyz 0 0 0)))', result)
        self.assertEqual(result.count('(layers "F.Cu" "F.Mask")'), 53)
        self.assertEqual(result.count('(layers "F.Paste")'), 53)
        self.assertNotIn('(layers "F.Cu" "F.Mask" "F.Paste")', result)
        for size, (paste, count) in PASTE.items():
            self.assertEqual(result.count('(size {:g} {:g})'.format(*size)), count)
            self.assertEqual(result.count('(size {:g} {:g})'.format(*paste)), count)
        self.assertEqual(result.count('(pad "MP"'), 2)
        for index in range(1, 52):
            self.assertIn('(pad "' + str(index) + '"', result)
            self.assertIn('(uuid "J2-' + str(index) + '")', result)

    def test_only_optical_blocks_change_deterministically(self):
        result = connector_candidate_text(self.source, self.positions)
        self.assertEqual(result, connector_candidate_text(self.source, self.positions))
        self.assertIn(self.other, result)
        self.assertIn('(gr_line (start 1 0) (end 1 1) (layer "Edge.Cuts"))', result)
        self.assertEqual(result.count('(layers "F.Paste")'), 106)

    def test_wrong_part_side_or_pose_rejected(self):
        source = footprint("J2")
        for changed in (
                source.replace(LIBRARY_PART, "different-part", 1),
                source.replace('(layer "F.Cu")', '(layer "B.Cu")', 1),
                source.replace("(at 43 46)", "(at 43 46 90)", 1)):
            with self.assertRaises(ValueError):
                correct_footprint(changed, "J2", [43, 45])

    def test_unexpected_pads_and_paste_settings_rejected(self):
        source = footprint("J2")
        for changed in (
                source.replace('(pad "1" smd rect', '(pad "1" smd circle', 1),
                source.replace("(size 0.8 0.3)", "(size 0.81 0.3)", 1),
                source.replace('(layers "F.Cu" "F.Mask" "F.Paste")',
                               '(layers "F.Cu" "F.Mask")', 1),
                source.replace('(uuid "J2-1")', '(uuid "J2-1") (solder_paste_margin 0)', 1)):
            with self.assertRaises(ValueError):
                correct_footprint(changed, "J2", [43, 45])

    def test_missing_or_duplicate_connector_rejected(self):
        for source in (self.source.replace(footprint("J3"), ""),
                       self.source.replace(footprint("J3"), footprint("J2"))):
            with self.assertRaises(ValueError):
                connector_candidate_text(source, self.positions)

    def test_nonfinite_or_incomplete_positions_rejected(self):
        for positions in ({"J2": [43, 45]}, dict(self.positions, J3=[87, float("nan")]),
                          dict(self.positions, J4=[0, 0])):
            with self.assertRaises(ValueError):
                connector_candidate_text(self.source, positions)

    def test_already_corrected_source_rejected(self):
        once = connector_candidate_text(self.source, self.positions)
        with self.assertRaises(ValueError):
            connector_candidate_text(once, self.positions)

    def test_inset_uses_fixed_x_and_actual_rotated_courtyard(self):
        parts = [
            {"ref": ref, "side": "TOP", "rotation_deg": 0, "position_mm": [x, 46],
             "courtyard_polygons_mm": [[[x-2.645, 37.105], [x+2.295, 37.105],
                                         [x+2.295, 54.895], [x-2.645, 54.895]]]}
            for ref, x in (("J2", 43), ("J3", 87))]
        positions = inset_positions({"components": parts, "board": {"bounds_mm": [20, 20, 122.5, 48]}})
        self.assertEqual(positions, self.positions)

    def test_body_registration_is_rigid_and_does_not_recentre(self):
        contract = {"coordinate_system": {"kicad_origin_mm": [65, 34],
                    "board_center_height_mm": -11.5}, "retained_component_bodies": {}}
        old, new = {}, {}
        for ref, x in (("J2", 43), ("J3", 87)):
            contract["retained_component_bodies"][ref] = {
                "min_mm": [x-65-1.95, -31.9, -10.51],
                "max_mm": [x-65+1.6, -15.1, -9.46], "model_status": "UNVERIFIED"}
            old[ref] = {"position_mm": [x, 46]}
            new[ref] = {"position_mm": [x, 45.055]}
        source = copy.deepcopy(contract)
        bodies = transform_bodies(contract, old, new)
        self.assertEqual(source, contract)
        self.assertAlmostEqual(bodies["J2"]["center_mm"][0], -22)
        self.assertAlmostEqual(bodies["J3"]["center_mm"][0], 22)
        self.assertAlmostEqual(bodies["J2"]["center_mm"][1], -22.73)
        self.assertEqual(bodies["J2"]["min_mm"][2], -10.51)
        self.assertAlmostEqual(bodies["J2"]["size_mm"][0], 16.8)


class ConnectorInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.path = self.root / "tmp/predecessor.kicad_pcb"
        self.path.parent.mkdir()
        self.path.write_text("(kicad_pcb)")
        self.layout = {"metadata": {
            "design_revision": "MECH-FIT-01", "is_canonical": False,
            "fabrication_allowed": False, "public_visual_allowed": False,
            "viewer_integration_allowed": False, "source_board": self.path.name,
            "source_board_sha256": digest(self.path), "fixed_origin_mm": [65, 34]},
            "tracks": [], "vias": [], "zones": [], "pads": [{"net": "", "net_code": 0}]}
        self.contract = {"coordinate_system": {"kicad_origin_mm": [65, 34]}}

    def validate(self, layout=None, path=None):
        validate_predecessor(path or self.path, layout or self.layout, self.contract, self.root)

    def test_locked_unrouted_predecessor_accepted(self):
        self.validate()

    def test_changed_source_and_noninternal_path_rejected(self):
        self.path.write_text("(kicad_pcb (changed))")
        with self.assertRaisesRegex(ValueError, "changed predecessor"):
            self.validate()
        with self.assertRaisesRegex(ValueError, "internal candidate"):
            self.validate(path=self.root / "baseline.kicad_pcb")

    def test_unlocked_canonical_and_changed_datum_rejected(self):
        for field, value in (
                ("fabrication_allowed", True), ("public_visual_allowed", None),
                ("viewer_integration_allowed", 0), ("is_canonical", True),
                ("fixed_origin_mm", [71.25, 34])):
            changed = copy.deepcopy(self.layout)
            changed["metadata"][field] = value
            with self.assertRaises(ValueError):
                self.validate(changed)

    def test_copper_or_connected_circuits_rejected(self):
        for key in ("tracks", "vias", "zones", "pads"):
            changed = copy.deepcopy(self.layout)
            changed[key] = [{"net": "GND", "net_code": 1}]
            with self.assertRaises(ValueError):
                self.validate(changed)

    def test_saved_candidate_has_no_unexpected_mutations(self):
        # Exercise the real parsed inventory when a local candidate exists.
        root = Path(__file__).resolve().parents[4]
        work = root / "tmp/pcb-connector-candidate-2026-10-13/corrected-01"
        if not (work / "engineering-layout-export.json").is_file():
            self.skipTest("generated candidate not present")
        before = json.loads((root / "tmp/pcb-fit-candidate-2026-10-13/profile-03/"
                             "engineering-layout-export.json").read_text())
        after = json.loads((work / "engineering-layout-export.json").read_text())
        verify_layout(before, after)
        changed = copy.deepcopy(after)
        changed["pads"][0]["net"] = "invented"
        with self.assertRaises(ValueError):
            verify_layout(before, changed)
        changed = copy.deepcopy(after)
        changed["components"][0]["value"] = "unrelated edit"
        with self.assertRaises(ValueError):
            verify_layout(before, changed)


if __name__ == "__main__":
    unittest.main()
