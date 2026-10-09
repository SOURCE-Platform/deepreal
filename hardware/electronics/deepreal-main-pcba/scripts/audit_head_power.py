#!/usr/bin/env python3
"""Keep partial sensor electrical evidence distinct from a complete head budget."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
HEAD = PROJECT.parent / "deepreal-optical-head"
REPO = PROJECT.parents[2]
REQUIRED_LOADS = {
    "rgb_assembly_run_startup_and_autofocus",
    "ir_60fps_current_profiles_and_startup_maximum",
    "regulator_topologies_efficiency_quiescent_and_inrush",
    "projector_driver_input_pulse_recharge_and_schedule",
    "clock_logic_identity_sensing_and_interlock",
    "flex_and_contact_drop_sharing_and_fault_derating",
    "both_heads_simultaneous_supply_transients",
}


def calculate(evidence):
    if set(evidence["unresolved_head_loads"]) != REQUIRED_LOADS:
        raise ValueError("Missing or unexpected head load categories")
    rails = evidence["rail_peak_currents"]
    expected = {"VDD25", "VDD18", "VDD13A", "VDD13D", "VDD13P"}
    if len(rails) != 5 or {r["rail"] for r in rails} != expected:
        raise ValueError("Expected five separately accounted sensor supply domains")
    if any(r["nominal_v"] <= 0 or r["peak_ma"] < 0 for r in rails):
        raise ValueError("Invalid rail voltage or peak current")
    if evidence["startup"]["minimum_source_capability_ma"] < 350:
        raise ValueError("Standard startup source capability is below 350mA")
    if evidence["published_typical_example"]["valid_as_deepreal_60fps_maximum"]:
        raise ValueError("A typical 30fps figure cannot qualify the 60fps maximum")
    opened = [k for k, v in evidence["unresolved_head_loads"].items() if v is None]
    if opened and (evidence["head_input_peak_current_a"] is not None or
                   evidence["head_input_average_power_w"] is not None):
        raise ValueError("Unknown loads cannot be silently omitted from head totals")
    return {
        "sensor_sum_of_table_peak_rail_powers_w": round(sum(
            r["nominal_v"]*r["peak_ma"]/1000 for r in rails), 6),
        "sensor_sum_of_table_peak_currents_ma": round(sum(r["peak_ma"] for r in rails), 6),
        "interpretation": "Arithmetic sum at nominal rails; not measured simultaneous peaks, not a continuous rating, excludes conversion losses and every other head load.",
        "startup_supply_minimum_ma": evidence["startup"]["minimum_source_capability_ma"],
        "head_input_peak_current_a": evidence["head_input_peak_current_a"],
        "head_input_average_power_w": evidence["head_input_average_power_w"],
        "open_load_evidence": opened,
        "head_power_status": "BLOCKED" if opened else "REVIEW_REQUIRED"
    }


def read_rows(path, key):
    with path.open() as stream:
        return {row[key]: row for row in csv.DictReader(stream)}


def check_clock_contract(evidence, main_nets, head_nets, allocation):
    frequency = evidence["reference_clock"]["frequency_mhz"]
    expected = "{}MHz".format(frequency)
    if frequency != 38.4:
        raise ValueError("Mira clock differs from reviewed datasheet baseline")
    if "SENSOR_24MHZ" in main_nets:
        raise ValueError("Obsolete shared RGB/IR 24MHz clock remains")
    if main_nets["IR_REFERENCE_CLOCK"]["Nominal"] != expected:
        raise ValueError("Main-board IR clock contract disagrees with sensor")
    if head_nets["IR_MCLK"]["Nominal"] != expected:
        raise ValueError("Head IR clock contract disagrees with sensor")
    if expected not in allocation["IR_clock"]["Electrical_rule"]:
        raise ValueError("Flex IR clock contract disagrees with sensor")
    if any(row["State"] == "DEFINED" for row in (
            main_nets["IR_REFERENCE_CLOCK"], head_nets["IR_MCLK"])):
        raise ValueError("Unselected clock topology must not claim circuit closure")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    evidence_path = HEAD/"power-clock-evidence.json"
    evidence = json.loads(evidence_path.read_text())
    source = evidence["source"]
    if hashlib.sha256((REPO/source["file"]).read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError("Sensor source hash mismatch")
    files = [PROJECT/"net-registry.csv", HEAD/"net-registry.csv",
             PROJECT/"connector-allocation.csv"]
    check_clock_contract(evidence, read_rows(files[0], "Net_or_group"),
                         read_rows(files[1], "Net_or_group"),
                         read_rows(files[2], "Group"))
    report = calculate(evidence)
    report.update({
        "schema": "deepreal.head-power-audit.v1",
        "source_document_sha256": source["sha256"],
        "source_files_sha256": {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [evidence_path]+files},
        "clock_contract_check": "PASS_FREQUENCY_CONSISTENCY_ONLY",
        "clock_implementation": evidence["reference_clock"]["implementation"],
        "fabrication_allowed": False, "public_visual_allowed": False})
    output = PROJECT/"generated-review"/"head-power-audit.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))
    if args.require_ready:
        raise RuntimeError("Head power is not approved; load profiles and circuit design remain open")


if __name__ == "__main__":
    main()
