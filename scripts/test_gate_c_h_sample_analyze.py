#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("gate_c_h_sample_analyze.py")
spec = importlib.util.spec_from_file_location("gate_c_h_sample_analyze", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def capture_for(records, *, probe=True, precision=8, frame_counter=60):
    return {
        "records": records,
        "probe_bytes": list(range(224)) if probe else [0] * 224,
        "precision_set": precision,
        "frame_counter": frame_counter,
    }


class GateCHSampleAnalyzeTests(unittest.TestCase):
    def test_exact_per_line_state_falsifies_sampling_loss(self) -> None:
        records = [
            {"index": i, "wh0": i, "wh1": 255, "end_line": i + 1}
            for i in range(224)
        ]
        records[-1]["end_line"] = 224
        result = mod.analyze_capture(capture_for(records))
        self.assertEqual(
            result["classification"],
            "H_SAMPLE_FALSIFIED_ALL_DISTINCT_WH0_PRESERVED",
        )
        self.assertEqual(result["unique_wh0_count"], 224)
        self.assertEqual(result["missing_wh0_count"], 0)

    def test_coalesced_queue_confirms_sampling_loss(self) -> None:
        values = [223, 0] + list(range(4, 224, 4))
        records = []
        for i, value in enumerate(values):
            end_line = min(224, 1 + i * 4)
            records.append(
                {"index": i, "wh0": value, "wh1": 255, "end_line": end_line}
            )
        records[-1]["end_line"] = 224
        result = mod.analyze_capture(capture_for(records))
        self.assertEqual(
            result["classification"],
            "H_SAMPLE_CONFIRMED_SECTION_COALESCING",
        )
        self.assertLess(result["unique_wh0_count"], 224)
        self.assertGreater(result["missing_wh0_count"], 0)
        self.assertGreaterEqual(result["max_wh0_forward_step"], 4)

    def test_bad_probe_is_indeterminate_not_sampling_evidence(self) -> None:
        records = [{"index": 0, "wh0": 0, "wh1": 255, "end_line": 224}]
        result = mod.analyze_capture(capture_for(records, probe=False))
        self.assertEqual(
            result["classification"],
            "INDETERMINATE_HDMA_SOURCE_SEQUENCE",
        )


if __name__ == "__main__":
    unittest.main()
