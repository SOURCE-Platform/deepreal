"""Regression checks for the private source-derived NXP package proposal."""

import copy
import json
import unittest
from pathlib import Path

import audit_nxp_package_evidence as evidence
from build_pcb_nxp_candidate import verify_scope, PACKAGES
from build_pcb_fit_candidate import top_level_blocks
from build_pcb_model_candidate import reference


ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / "tmp/assembly-corrections-2026-10-14"


class NxpPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal = WORK / "nxp-proposal-04"
        cls.report = json.loads((cls.proposal / "nxp-package-evidence.json").read_text())
        cls.before = json.loads((ROOT / "tmp/pcb-package-fit-2026-10-13/package-02/engineering-layout-export.json").read_text())
        cls.after = json.loads((WORK / "package-07/engineering-layout-export.json").read_text())

    def test_manufacturer_source_and_artifact_hashes(self):
        evidence.checked_sources(WORK / "sources")
        for name, sha in self.report["artifacts_sha256"].items():
            self.assertEqual(evidence.digest(self.proposal / name), sha)

    def test_embedded_548_ball_map_reproduces(self):
        balls, content = evidence.ball_map(WORK / "sources/imx95iec-official-cn.pdf")
        self.assertEqual(balls, self.report["U1"]["balls"])
        self.assertEqual(len(balls), 548)
        self.assertEqual(content, (self.proposal / "imx95-15mm-embedded-ballmap.xlsx").read_bytes())

    def test_af22_conflict_is_not_silently_resolved(self):
        ball = next(b for b in self.report["U1"]["balls"] if b["number"] == "AF22")
        self.assertEqual(ball["function"], "UNRESOLVED_AF22")
        self.assertEqual(ball["coordinate_list_function"], "VDD_EARC_1P8")
        self.assertEqual(ball["board_grid_function"], "VDD_AUD_1P8")
        self.assertEqual(self.report["U1"]["independent_function_matches"], 547)

    def test_correct_revisions_not_similarly_named_packages(self):
        self.assertEqual(self.report["U1"]["package"], "SOT2251-1")
        self.assertEqual(self.report["U6_U7"]["package"], "SOT2283-1")
        self.assertIn("NOT the selected", self.report["U1"]["rejected_package"])

    def test_16_vendor_copper_contours_reproduce(self):
        groups, basis = evidence.copper_loops(WORK / "sources/sot2283-1-official-cn.pdf")
        self.assertEqual(groups, self.report["U6_U7"]["copper_groups"])
        self.assertEqual(basis, self.report["U6_U7"]["copper_vector_basis"])
        self.assertEqual(len(groups), 16)
        self.assertEqual({frozenset(g["numbers"]) for g in groups}, evidence.EXPECTED_GROUPS)

    def test_aliases_connect_only_identical_vendor_functions(self):
        for group in self.report["U6_U7"]["copper_groups"]:
            functions = {evidence.PF_FUNCTIONS[n] for n in group["numbers"]}
            self.assertEqual(len(functions), 1)
            for number in group["numbers"]:
                self.assertTrue(evidence.inside(evidence.pf_positions()[number], group["polygon_mm"]))

    def test_scope_population_and_local_alias_nets_only(self):
        verify_scope(self.before, self.after)
        self.assertEqual(len(self.after["pads"]), 2626)
        self.assertEqual(len([p for p in self.after["pads"] if p["ref"] not in PACKAGES]), 2030)

    def test_other_root_blocks_remain_byte_identical(self):
        source = ROOT / "tmp/pcb-package-fit-2026-10-13/package-02/deepreal-main-pcba-mech-fit-04.kicad_pcb"
        target = WORK / "package-07/deepreal-main-pcba-mech-fit-05.kicad_pcb"
        def retained(path):
            return [b for _, _, b in top_level_blocks(path.read_text())[0]
                    if not b.startswith("(footprint ") or reference(b) not in PACKAGES]
        self.assertEqual(retained(source), retained(target))

    def test_repeat_pcb_bytes_identical(self):
        first = WORK / "package-07/deepreal-main-pcba-mech-fit-05.kicad_pcb"
        repeat = WORK / "package-08/deepreal-main-pcba-mech-fit-05.kicad_pcb"
        self.assertEqual(first.read_bytes(), repeat.read_bytes())

    def test_other_component_change_rejected(self):
        bad = copy.deepcopy(self.after)
        next(c for c in bad["components"] if c["ref"] == "D2")["rotation_deg"] += 1
        with self.assertRaisesRegex(ValueError, "unscoped component"):
            verify_scope(self.before, bad)

    def test_duplicate_ball_rejected(self):
        bad = copy.deepcopy(self.after)
        pads = [p for p in bad["pads"] if p["ref"] == "U1"]
        pads[1]["number"] = pads[0]["number"]
        with self.assertRaisesRegex(ValueError, "package pad count"):
            verify_scope(self.before, bad)

    def test_invented_net_rejected(self):
        bad = copy.deepcopy(self.after)
        next(p for p in bad["pads"] if p["ref"] == "U1")["net"] = "GUESSED"
        with self.assertRaisesRegex(ValueError, "invented net"):
            verify_scope(self.before, bad)

    def test_no_invented_paste_and_release_locks_closed(self):
        for path in (self.proposal / "DeepReal_Evidence.pretty").glob("*.kicad_mod"):
            self.assertNotIn('"F.Paste"', path.read_text())
        self.assertFalse(self.report["U1"]["land_proposal"]["vendor_land_definition_verified"])
        self.assertFalse(self.report["U6_U7"]["mask_pattern_verified"])
        for record in (self.report, self.after["metadata"]):
            for flag in ("fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed"):
                self.assertIs(record[flag], False)

    def test_only_22_source_defined_local_alias_pads_have_nets(self):
        assigned = [p for p in self.after["pads"] if p["net"]]
        self.assertEqual(len(assigned), 22)
        self.assertEqual({p["net"] for p in assigned},
                         {"PACKAGE_U6_PGND", "PACKAGE_U6_LX", "PACKAGE_U7_PGND", "PACKAGE_U7_LX"})
        bad = copy.deepcopy(self.after)
        next(p for p in bad["pads"] if p["net"] == "PACKAGE_U6_PGND")["net"] = "PACKAGE_U7_PGND"
        with self.assertRaisesRegex(ValueError, "invented net"):
            verify_scope(self.before, bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
