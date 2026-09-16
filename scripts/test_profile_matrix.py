#!/usr/bin/env python3
"""Host-side tests for the workload profile matrix reporter."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import profile_matrix  # noqa: E402


class ProfileMatrixTests(unittest.TestCase):
    def write_summary(self, name: str, samples: int, subsystems: dict[str, int]) -> Path:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        path = directory / f"{name}.json"
        path.write_text(
            json.dumps({"meta": {"valid_samples": samples}, "subsystems": subsystems}),
            encoding="utf-8",
        )
        return path

    def test_matrix_contains_percentages_and_other_bucket(self) -> None:
        path = self.write_summary(
            "cpu-alu",
            10,
            {
                "S-CPU interpreter": 6,
                "APU JIT generated": 2,
                "runtime/unknown": 2,
            },
        )
        text = profile_matrix.render_matrix([path])
        self.assertIn("cpu-alu", text)
        self.assertIn("60.0%", text)
        self.assertIn("20.0%", text)

    def test_zero_sample_summary_renders_without_division(self) -> None:
        path = self.write_summary("empty", 0, {})
        text = profile_matrix.render_matrix([path])
        self.assertIn("| empty | 0 |", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
