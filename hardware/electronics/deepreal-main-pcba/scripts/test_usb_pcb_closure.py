import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from audit_usb_receptacle_candidates import DRAWINGS, FACTS, compile_audit
from build_pcb_marking_candidate import (
    NEW_NOTE, OLD_NOTE, annotation_signature, annotations, placement_offsets,
    verify_scope, warning_variants,
)


SAMPLE = '''(kicad_pcb
 (version 20260101)
 (footprint "Test" (layer "F.Cu") (at 10 20)
  (property "Reference" "U1" (at 0 -2) (layer "F.SilkS")
   (uuid "ref") (effects (font (size 0.6 0.6) (thickness 0.15))))
  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu" "F.Mask"))
 )
 (gr_text "U1 PROXY: 548-BALL MAP REQUIRED" (at 10 20)
  (layer "F.Fab") (uuid "note")
  (effects (font (size 0.55 0.55) (thickness 0.15))))
)'''


class ScopeTests(unittest.TestCase):
    def test_annotation_positions_and_size_allowed(self):
        changed = SAMPLE.replace("(at 0 -2)", "(at 0 -3)").replace("0.6 0.6", "0.8 0.8")
        verify_scope(SAMPLE, changed, ["ref"])

    def test_pad_mutation_rejected(self):
        with self.assertRaises(ValueError):
            verify_scope(SAMPLE, SAMPLE.replace("(size 1 1)", "(size 2 2)"), ["ref"])

    def test_layer_mutation_rejected(self):
        with self.assertRaises(ValueError):
            verify_scope(SAMPLE, SAMPLE.replace('"F.SilkS"', '"F.Fab"'), ["ref"])

    def test_hiding_rejected(self):
        with self.assertRaises(ValueError):
            verify_scope(SAMPLE, SAMPLE.replace('(uuid "ref")', '(uuid "ref") (hide yes)'), ["ref"])

    def test_mirror_mutation_rejected(self):
        with self.assertRaises(ValueError):
            verify_scope(SAMPLE, SAMPLE.replace("(thickness 0.15)", "(thickness 0.15) (justify mirror)", 1),
                         ["ref"])

    def test_rules_mutation_rejected(self):
        with self.assertRaises(ValueError):
            verify_scope(SAMPLE, SAMPLE.replace("(version 20260101)", "(version 20260102)"), ["ref"])

    def test_truthful_u1_note_allowed(self):
        verify_scope(SAMPLE, SAMPLE.replace(OLD_NOTE, NEW_NOTE), ["note"])

    def test_arbitrary_text_change_rejected(self):
        with self.assertRaises(ValueError):
            verify_scope(SAMPLE, SAMPLE.replace(OLD_NOTE, "APPROVED"), ["note"])

    def test_warning_line_wrap_allowed(self):
        source = SAMPLE.replace(OLD_NOTE, "DO NOT FABRICATE")
        changed = source.replace('"DO NOT FABRICATE"', json.dumps("DO NOT\nFABRICATE"))
        verify_scope(source, changed, ["note"])

    def test_warning_words_cannot_be_removed(self):
        source = SAMPLE.replace(OLD_NOTE, "DO NOT FABRICATE")
        with self.assertRaises(ValueError):
            verify_scope(source, source.replace("DO NOT FABRICATE", "FABRICATE"), ["note"])

    def test_warning_words_cannot_be_merged(self):
        source = SAMPLE.replace(OLD_NOTE, "DO NOT FABRICATE")
        with self.assertRaises(ValueError):
            verify_scope(source, source.replace("DO NOT FABRICATE", "DONOTFABRICATE"), ["note"])

    def test_reflow_preserves_every_word(self):
        source = "PRELIMINARY PLACEMENT — NOT FOR FABRICATION"
        variants = warning_variants(source)
        self.assertGreater(len(variants), 2)
        for variant in variants:
            self.assertEqual(variant.split(), source.split())

    def test_only_board_warnings_have_global_search(self):
        bounds = (0, 0, 200, 20)
        global_offsets = placement_offsets((100, 10), bounds, 1, True)
        local_offsets = placement_offsets((100, 10), bounds, 1, False)
        self.assertIn((100, 0), global_offsets)
        self.assertNotIn((100, 0), local_offsets)
        self.assertEqual(local_offsets[0], (0, 0))

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            annotations(SAMPLE.replace('(uuid "note")', '(uuid "ref")'))

    def test_signature_does_not_hide_visibility(self):
        field = annotations(SAMPLE)["ref"][2]
        hidden = field[:-1] + " (hide yes))"
        self.assertNotEqual(annotation_signature(field), annotation_signature(hidden))


class EvidenceTests(unittest.TestCase):
    def test_five_hash_bound_drawings(self):
        self.assertEqual(set(DRAWINGS), set(FACTS))
        self.assertEqual(len(DRAWINGS), 5)
        self.assertTrue(all(len(value) == 64 for value in DRAWINGS.values()))

    def test_thin_board_candidates_rejected(self):
        for name in ("usb4056", "usb4065", "usb4745"):
            with self.subTest(name=name):
                self.assertEqual(FACTS[name]["status"], "REJECTED")
                self.assertLess(FACTS[name]["pcb_thickness_mm"][1], 1.5)

    def test_unknown_thickness_is_not_approval(self):
        for name in ("usb4230", "usb4910"):
            with self.subTest(name=name):
                self.assertIsNone(FACTS[name]["pcb_thickness_mm"])
                self.assertNotEqual(FACTS[name]["status"], "APPROVED")

    def test_facts_are_not_mutated_by_consumers(self):
        facts = copy.deepcopy(FACTS)
        facts["usb4910"]["status"] = "APPROVED"
        self.assertEqual(FACTS["usb4910"]["status"], "INVESTIGATE_ONLY")

    def test_drawing_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in DRAWINGS:
                (root / (name + ".pdf")).write_bytes(b"wrong drawing")
            with self.assertRaises(ValueError):
                compile_audit(root)

    def test_compiler_preserves_release_locks_and_unknowns(self):
        data = b"synthetic test drawing, not manufacturer evidence"
        hashes = {name: hashlib.sha256(data).hexdigest() for name in DRAWINGS}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in DRAWINGS:
                (root / (name + ".pdf")).write_bytes(data)
            with patch.dict(DRAWINGS, hashes):
                result = compile_audit(root)
        self.assertIsNone(result["selected_part"])
        self.assertFalse(any(result["release_permissions"].values()))
        self.assertTrue(all(not row["approved"] for row in result["candidates"]))
        result["candidates"][-1]["signal_lands_count_and_size_mm"][1] = 99
        self.assertEqual(FACTS["usb4910"]["signal_lands_count_and_size_mm"][1], 0.85)


if __name__ == "__main__":
    unittest.main()
