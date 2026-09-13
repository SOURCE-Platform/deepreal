#!/usr/bin/env python3
"""Calculate active-pixel camera payload and candidate output margin."""

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT / "camera-bandwidth.json"


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    factor = 1.0 + data["engineering_margin"]
    heads = data["simultaneous_heads"]
    per_head = 0.0
    print("CAMERA PAYLOAD")
    for stream in data["streams_per_head"]:
        payload = (stream["width"] * stream["height"]
                   * stream["frames_per_second"] * stream["bits_per_pixel"]
                   / 1_000_000_000.0)
        per_head += payload
        sensor_lane = payload * factor / stream["sensor_lanes"]
        print("  {}: {:.3f} Gbit/s active; {:.3f} Gbit/s/lane with margin".format(
            stream["name"], payload, sensor_lane))
    aggregate = per_head * heads * factor
    print("  all heads with {:.0f}% margin: {:.3f} Gbit/s".format(
        data["engineering_margin"] * 100, aggregate))
    for candidate in data["candidate_outputs"]:
        per_output = aggregate / candidate["output_count"]
        lane_rate = per_output / candidate["lanes_per_output"]
        limit = candidate["maximum_lane_rate_gbps"]
        if lane_rate > limit:
            raise RuntimeError(candidate["name"] + " exceeds output lane limit")
        print("  {}: {:.3f} Gbit/s/lane ({:.0f}% of limit)".format(
            candidate["name"], lane_rate, lane_rate / limit * 100))
    print("PASS: arithmetic output bandwidth gate; protocol and compile gates remain")


if __name__ == "__main__":
    main()
