#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "gate_c_h_comp_half_analyze_fb", HERE / "gate_c_h_comp_half_analyze_fb.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def frame(rgb: tuple[int, int, int]) -> bytes:
    r, g, b = rgb
    word = (r << 11) | (g << 6) | (b << 1) | 1
    px = word.to_bytes(2, "big")
    return px * (mod.WIDTH * mod.HEIGHT)


class HalfAnalyzerTests(unittest.TestCase):
    def classify(self, c, t):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            cp = root / "c.bin"
            tp = root / "t.bin"
            cp.write_bytes(frame(c))
            tp.write_bytes(frame(t))
            return mod.analyze(cp, tp)["classification"]

    def test_exact_expected_falsifies_half_defect(self):
        self.assertEqual(
            self.classify((16,16,0), (8,8,0)),
            "H_COMP_HALF_FALSIFIED_EXACT_SODIUM64_MATH",
        )

    def test_same_output_supports_missing_half(self):
        self.assertEqual(
            self.classify((16,0,0), (16,0,0)),
            "H_COMP_HALF_SUPPORTED_NO_HALF_EFFECT",
        )

    def test_wrong_changed_output_is_still_arithmetic_defect(self):
        self.assertEqual(
            self.classify((16,0,0), (0,16,0)),
            "H_COMP_HALF_SUPPORTED_WRONG_ARITHMETIC",
        )


if __name__ == "__main__":
    unittest.main()
