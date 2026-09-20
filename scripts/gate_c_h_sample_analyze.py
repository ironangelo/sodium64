#!/usr/bin/env python3
"""Analyze Gate-C H-SAMPLE section-queue evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VISIBLE_LINES = 224
EXPECTED_PRECISION_SET = 2 << 2
FINAL_END_LINE = 224


def analyze_capture(capture: dict[str, object]) -> dict[str, object]:
    records_all = list(capture.get("records", []))
    records: list[dict[str, int]] = []
    final_seen = False
    for raw in records_all:
        record = {
            "index": int(raw["index"]),
            "wh0": int(raw["wh0"]),
            "wh1": int(raw["wh1"]),
            "end_line": int(raw["end_line"]),
        }
        records.append(record)
        if record["end_line"] >= FINAL_END_LINE:
            final_seen = True
            break

    probe = [int(x) for x in capture.get("probe_bytes", [])]
    expected_probe = list(range(VISIBLE_LINES))
    probe_matches = probe == expected_probe
    probe_mismatches = [
        {"index": index, "expected": expected, "actual": actual}
        for index, (expected, actual) in enumerate(zip(expected_probe, probe))
        if actual != expected
    ]
    if len(probe) != len(expected_probe):
        for index in range(min(len(probe), len(expected_probe)), max(len(probe), len(expected_probe))):
            probe_mismatches.append({
                "index": index,
                "expected": expected_probe[index] if index < len(expected_probe) else None,
                "actual": probe[index] if index < len(probe) else None,
            })
    precision = int(capture.get("precision_set", -1))
    frame_counter = int(capture.get("frame_counter", 0))

    wh0_values = [record["wh0"] for record in records]
    unique_wh0 = sorted(set(wh0_values))
    unique_set = set(unique_wh0)
    missing_wh0 = [value for value in expected_probe if value not in unique_set]
    end_lines = [record["end_line"] for record in records]
    end_line_steps = [b - a for a, b in zip(end_lines, end_lines[1:]) if b >= a]
    wh0_forward_steps = []
    for a, b in zip(wh0_values, wh0_values[1:]):
        step = (b - a) & 0xFF
        if a == 223 and b == 0:
            continue
        wh0_forward_steps.append(step)

    if frame_counter < 2:
        classification = "INDETERMINATE_GUEST_NOT_WARM"
    elif precision != EXPECTED_PRECISION_SET:
        classification = "INDETERMINATE_WRONG_PRECISION"
    elif not probe_matches:
        classification = "INDETERMINATE_HDMA_SOURCE_SEQUENCE"
    elif not final_seen:
        classification = "INDETERMINATE_INCOMPLETE_SECTION_QUEUE"
    elif len(unique_wh0) == VISIBLE_LINES:
        classification = "H_SAMPLE_FALSIFIED_ALL_DISTINCT_WH0_PRESERVED"
    else:
        classification = "H_SAMPLE_CONFIRMED_SECTION_COALESCING"

    return {
        "classification": classification,
        "frame_counter": frame_counter,
        "precision_set": precision,
        "probe_matches_0_to_223": probe_matches,
        "probe_length": len(probe),
        "probe_mismatch_count": len(probe_mismatches),
        "probe_mismatches_first_32": probe_mismatches[:32],
        "probe_head_32": probe[:32],
        "probe_tail_32": probe[-32:] if probe else [],
        "final_section_seen": final_seen,
        "record_count": len(records),
        "unique_wh0_count": len(unique_wh0),
        "missing_wh0_count": len(missing_wh0),
        "missing_wh0": missing_wh0,
        "max_end_line_step": max(end_line_steps, default=0),
        "max_wh0_forward_step": max(wh0_forward_steps, default=0),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    result = analyze_capture(capture)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
