#!/usr/bin/env python3
"""Regression checks for partial power evidence and clock-contract consistency."""

import copy
import json
import unittest

from audit_head_power import HEAD, PROJECT, calculate, check_clock_contract, read_rows


class HeadPowerTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads((HEAD/"power-clock-evidence.json").read_text())
        self.main = read_rows(PROJECT/"net-registry.csv", "Net_or_group")
        self.head = read_rows(HEAD/"net-registry.csv", "Net_or_group")
        self.flex = read_rows(PROJECT/"connector-allocation.csv", "Group")

    def test_partial_sum_does_not_approve_whole_head(self):
        result = calculate(self.evidence)
        self.assertEqual(result["sensor_sum_of_table_peak_rail_powers_w"], 0.51423)
        self.assertEqual(result["sensor_sum_of_table_peak_currents_ma"], 237.6)
        self.assertEqual(result["startup_supply_minimum_ma"], 350)
        self.assertIsNone(result["head_input_peak_current_a"])
        self.assertEqual(result["head_power_status"], "BLOCKED")

    def test_startup_must_not_use_run_current(self):
        self.evidence["startup"]["minimum_source_capability_ma"] = 168
        with self.assertRaisesRegex(ValueError, "startup"):
            calculate(self.evidence)

    def test_typical_30fps_is_not_60fps_maximum(self):
        self.evidence["published_typical_example"]["valid_as_deepreal_60fps_maximum"] = True
        with self.assertRaisesRegex(ValueError, "30fps"):
            calculate(self.evidence)

    def test_missing_loads_cannot_be_dropped_from_total(self):
        self.evidence["head_input_peak_current_a"] = 0.35
        with self.assertRaisesRegex(ValueError, "Unknown loads"):
            calculate(self.evidence)

    def test_missing_supply_domain_is_rejected(self):
        self.evidence["rail_peak_currents"].pop()
        with self.assertRaisesRegex(ValueError, "five"):
            calculate(self.evidence)

    def test_missing_load_category_is_rejected(self):
        self.evidence["unresolved_head_loads"].pop("rgb_assembly_run_startup_and_autofocus")
        with self.assertRaisesRegex(ValueError, "categories"):
            calculate(self.evidence)

    def test_current_clock_contracts_agree(self):
        check_clock_contract(self.evidence, self.main, self.head, self.flex)

    def test_shared_24mhz_source_is_rejected(self):
        self.main["SENSOR_24MHZ"] = copy.deepcopy(self.main["RGB_REFERENCE_CLOCK"])
        with self.assertRaisesRegex(ValueError, "shared"):
            check_clock_contract(self.evidence, self.main, self.head, self.flex)

    def test_head_clock_regression_is_rejected(self):
        self.head["IR_MCLK"]["Nominal"] = "24MHz"
        with self.assertRaisesRegex(ValueError, "Head IR clock"):
            check_clock_contract(self.evidence, self.main, self.head, self.flex)

    def test_flex_clock_regression_is_rejected(self):
        self.flex["IR_clock"]["Electrical_rule"] = "24MHz source-terminated"
        with self.assertRaisesRegex(ValueError, "Flex IR clock"):
            check_clock_contract(self.evidence, self.main, self.head, self.flex)

    def test_clock_circuit_cannot_claim_completion(self):
        self.main["IR_REFERENCE_CLOCK"]["State"] = "DEFINED"
        with self.assertRaisesRegex(ValueError, "closure"):
            check_clock_contract(self.evidence, self.main, self.head, self.flex)


if __name__ == "__main__":
    unittest.main()
