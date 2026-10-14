"""Mutation tests for the new private guard, without touching retained inputs."""

import json
import tempfile
import unittest
from pathlib import Path

from pcb_candidate_review_data import ROOT, digest
from pcb_package_review_data import checked_inputs


class PackageReviewGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / "tmp/candidate"
        self.directory.mkdir(parents=True)
        original = ROOT / "tmp/pcb-package-fit-2026-10-13/package-02"
        self.layout = json.loads((original / "engineering-layout-export.json").read_text())
        self.manifest = json.loads((original / "native-review-manifest.json").read_text())
        self.audit = json.loads((original / "package-audit.json").read_text())
        meta = self.layout["metadata"]
        self.board = self.directory / meta["source_board"]
        self.board.write_bytes(b"private test board")
        self.glb = self.directory / self.manifest["glb"]
        self.glb.write_bytes(b"private test transport")
        status = self.root / "hardware/electronics/deepreal-main-pcba/design-status.json"
        status.parent.mkdir(parents=True)
        status.write_bytes(b"private test status")
        meta["source_board_sha256"] = self.manifest["source_board_sha256"] = \
            self.audit["source_board_sha256"] = digest(self.board)
        meta["source_status_sha256"] = self.manifest["source_status_sha256"] = digest(status)
        self.manifest["glb_sha256"] = digest(self.glb)
        for filename, key, sha_key in (("evidence.pdf", "datasheet", "datasheet_sha256"),
                                       ("footprint.kicad_mod", "library_footprint", "library_sha256")):
            path = self.directory / filename
            path.write_bytes(b"private test evidence")
            self.audit["D2"][key], self.audit["D2"][sha_key] = str(path), digest(path)
        model = self.directory / "test-model.step"
        model.write_bytes(b"private test model")
        self.manifest["model_sources"] = [{"resolved": str(model), "sha256": digest(model)}]
        self.output = self.root / "tmp/new-output"
        self.save()

    def save(self):
        for filename, document in (("engineering-layout-export.json", self.layout),
                                    ("package-audit.json", self.audit)):
            (self.directory / filename).write_text(json.dumps(document))
        self.manifest["source_export_sha256"] = digest(self.directory / "engineering-layout-export.json")
        self.manifest["package_audit_sha256"] = digest(self.directory / "package-audit.json")
        (self.directory / "native-review-manifest.json").write_text(json.dumps(self.manifest))

    def check(self):
        return checked_inputs(self.directory, self.output, self.root)

    def test_current_source_bound_guard_passes(self):
        data, _ = self.check()
        self.assertEqual(len(data["components"]), 238)
        self.assertEqual(len(data["pads"]), 2412)

    def test_release_flags_cannot_be_missing_or_true(self):
        for document in (self.layout["metadata"], self.manifest, self.audit):
            for name in ("fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed"):
                for value in (True, None):
                    document[name] = value
                    self.save()
                    with self.assertRaises(ValueError):
                        self.check()
                document[name] = False

    def test_stale_board_and_transport_rejected(self):
        for path in (self.board, self.glb):
            previous = path.read_bytes()
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                self.check()
            path.write_bytes(previous)

    def test_datum_revision_and_scope_rejected(self):
        for document, key, value in ((self.layout["metadata"], "fixed_origin_mm", [71.25, 34]),
                                     (self.manifest, "revision", "MECH-FIT-03"),
                                     (self.audit, "changed_footprint_refs", ["D2", "U1"])):
            previous = document[key]
            document[key] = value
            self.save()
            with self.assertRaises(ValueError):
                self.check()
            document[key] = previous

    def test_path_escape_rejected(self):
        self.layout["metadata"]["source_board"] = "../outside.kicad_pcb"
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_population_classification_rejected(self):
        self.manifest["missing_model_refs"].append(self.manifest["native_model_refs"][0])
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_new_connectivity_rejected(self):
        self.layout["pads"][0]["net"] = "NEW_NET"
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_evidence_and_library_mutation_rejected(self):
        paths = [Path(self.audit["D2"]["datasheet"]),
                 Path(self.audit["D2"]["library_footprint"]),
                 Path(self.manifest["model_sources"][0]["resolved"])]
        for path in paths:
            previous = path.read_bytes()
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                self.check()
            path.write_bytes(previous)


if __name__ == "__main__":
    unittest.main()
