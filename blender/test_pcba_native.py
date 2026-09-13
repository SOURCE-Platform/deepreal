"""Regression tests for provenance rejection; run with Blender's Python."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pcba_native_import as native


class ProvenanceTests(unittest.TestCase):
    def test_current_inputs(self):
        data, manifest = native.checked_inputs()
        accounted = (manifest["native_model_refs"] + manifest["missing_model_refs"]
                     + manifest["pad_or_hole_only_refs"])
        self.assertEqual(sorted(accounted), sorted(c["ref"] for c in data["components"]))
        self.assertFalse(manifest["public_visual_allowed"])
        self.assertFalse(manifest["fabrication_allowed"])

    def reject_changed(self, filename):
        actual = native.digest
        with patch.object(native, "digest", side_effect=lambda p:
                          "changed" if p.name == filename else actual(p)):
            with self.assertRaises(ValueError):
                native.checked_inputs()

    def test_changed_board_rejected(self):
        self.reject_changed("deepreal-main-pcba.kicad_pcb")

    def test_changed_export_rejected(self):
        self.reject_changed("engineering-layout-export.json")

    def test_changed_geometry_rejected(self):
        self.reject_changed("main-pcba-native.glb")

    def test_changed_status_rejected(self):
        self.reject_changed("design-status.json")

    def test_changed_library_rejected(self):
        _, manifest = native.checked_inputs()
        model = next(m for m in manifest["model_sources"] if m["sha256"])
        self.reject_changed(Path(model["resolved"]).name)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ProvenanceTests))
    if not result.wasSuccessful():
        raise RuntimeError("provenance regression tests failed")
