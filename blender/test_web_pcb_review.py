"""Export-boundary tests, run with Blender's Python."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_web_pcb_review as exporter


class ExportGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=exporter.ROOT / "tmp")
        self.output = Path(self.temp.name) / "review.glb"
        electronics = exporter.ROOT / "hardware/electronics/deepreal-main-pcba"
        self.data = json.loads((electronics / "engineering-layout-export.json").read_text())
        self.manifest = json.loads((electronics / "generated-review/native-review-manifest.json").read_text())
        self.status = json.loads((electronics / "design-status.json").read_text())

    def tearDown(self):
        self.temp.cleanup()

    def reject(self, manifest=None, status=None):
        with patch.object(exporter, "OUTPUT", self.output), patch.object(
                exporter.json, "loads", side_effect=[self.data, manifest or self.manifest,
                                                     status or self.status]):
            with self.assertRaises(ValueError):
                exporter.main()
        self.assertFalse(self.output.exists())

    def test_source_gate_cannot_be_overridden(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["public_visual_allowed"] = True
        self.reject(manifest=manifest)

    def test_unknown_current_gate_rejected(self):
        status = copy.deepcopy(self.status)
        status["fabrication_allowed"] = None
        self.reject(status=status)

    def test_missing_current_gate_rejected(self):
        status = copy.deepcopy(self.status)
        del status["public_visual_allowed"]
        self.reject(status=status)

    def test_changed_geometry_source_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["source_board_sha256"] = "changed"
        self.reject(manifest=manifest)

    def test_existing_review_not_overwritten(self):
        self.output.write_bytes(b"retained")
        with patch.object(exporter, "OUTPUT", self.output), self.assertRaises(ValueError):
            exporter.main()
        self.assertEqual(self.output.read_bytes(), b"retained")

    def test_output_cannot_enter_public_directory(self):
        output = exporter.ROOT.parent / "source-public-site/public/models/forbidden-pcb.glb"
        with patch.object(exporter, "OUTPUT", output), self.assertRaises(ValueError):
            exporter.main()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ExportGuards))
    if not result.wasSuccessful():
        raise RuntimeError("PCB web review guard tests failed")
