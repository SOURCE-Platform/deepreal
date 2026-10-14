import json
from pathlib import Path
import tempfile
import unittest

from pcb_candidate_review_data import checked_inputs, digest


class PrivateReviewGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.input = self.root / "tmp/input"
        self.input.mkdir(parents=True)
        self.output = self.root / "tmp/output"
        status = self.root / "hardware/electronics/deepreal-main-pcba/design-status.json"
        status.parent.mkdir(parents=True)
        status.write_text("{}")
        board = self.input / "candidate.kicad_pcb"
        board.write_text("private candidate")
        glb = self.input / "candidate.glb"
        glb.write_bytes(b"private geometry")
        locks = dict(fabrication_allowed=False, public_visual_allowed=False, viewer_integration_allowed=False)
        self.layout = {
            "metadata": {**locks, "design_revision": "MECH-FIT-03", "is_canonical": False,
                         "fixed_origin_mm": [65, 34], "source_board": board.name,
                         "source_board_sha256": digest(board), "source_status_sha256": digest(status)},
            "components": [{"ref": "U1"}], "pads": [], "tracks": [], "vias": [], "zones": [],
        }
        self.manifest = {
            **locks, "schema": "deepreal.private-candidate-native.v1", "origin_mm": [65, 34],
            "source_board_sha256": digest(board), "source_status_sha256": digest(status),
            "glb": glb.name, "glb_sha256": digest(glb), "native_model_refs": [],
            "missing_model_refs": ["U1"], "pad_or_hole_only_refs": [], "model_sources": [],
        }
        self.save()

    def save(self):
        path = self.input / "engineering-layout-export.json"
        path.write_text(json.dumps(self.layout))
        self.manifest["source_export_sha256"] = digest(path)
        (self.input / "native-review-manifest.json").write_text(json.dumps(self.manifest))

    def check(self):
        return checked_inputs(self.input, self.output, self.root)

    def test_blocked_candidate_can_only_have_private_review(self):
        self.check()

    def test_existing_or_external_output_rejected(self):
        self.output.mkdir()
        with self.assertRaises(ValueError):
            self.check()
        with self.assertRaises(ValueError):
            checked_inputs(self.input, self.root / "public", self.root)

    def test_missing_and_true_release_locks_rejected(self):
        for value in (None, True):
            self.manifest["viewer_integration_allowed"] = value
            self.save()
            with self.assertRaises(ValueError):
                self.check()

    def test_changed_status_geometry_or_board_rejected(self):
        for name in ("candidate.glb", "candidate.kicad_pcb"):
            path = self.input / name
            original = path.read_bytes()
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                self.check()
            path.write_bytes(original)
        status = self.root / "hardware/electronics/deepreal-main-pcba/design-status.json"
        status.write_text('{"changed":true}')
        with self.assertRaises(ValueError):
            self.check()

    def test_datum_and_population_mutations_rejected(self):
        self.manifest["origin_mm"] = [71.25, 34]
        self.save()
        with self.assertRaises(ValueError):
            self.check()
        self.manifest["origin_mm"] = [65, 34]
        self.manifest["native_model_refs"] = ["U1"]
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_connected_or_canonical_classification_rejected(self):
        self.layout["pads"] = [{"net": "invented"}]
        self.save()
        with self.assertRaises(ValueError):
            self.check()
        self.layout["pads"] = []
        self.layout["metadata"]["is_canonical"] = True
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_model_library_changes_rejected(self):
        path = self.root / "model.step"
        path.write_text("original")
        self.manifest["model_sources"] = [{"resolved": str(path), "sha256": digest(path)}]
        self.save()
        self.check()
        path.write_text("changed")
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
