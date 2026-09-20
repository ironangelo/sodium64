#!/usr/bin/env python3
"""Host-side tests for Gate-C OBJ-window framebuffer analysis."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_c_obj_window_analyze_fb as analyze  # noqa: E402


def make_frame(red_boxes: list[tuple[int, int, int, int]]) -> bytes:
    pixels = [0] * (analyze.WIDTH * analyze.HEIGHT)

    for y in range(0, 224):
        for x in range(77, 204):
            pixels[y * analyze.WIDTH + x] = 0x07C1

    for x0, y0, width, height in red_boxes:
        for y in range(y0, y0 + height):
            for x in range(x0, x0 + width):
                pixels[y * analyze.WIDTH + x] = 0xF801

    raw = bytearray()
    for value in pixels:
        raw.extend(value.to_bytes(2, "big"))
    return bytes(raw)


class GateCObjWindowAnalyzeTests(unittest.TestCase):
    OUTER = [(28, 96, 8, 8), (236, 96, 8, 8)]

    def test_classifies_outer_two_to_two_as_supported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = root / "c.bin"
            t = root / "t.bin"
            c.write_bytes(make_frame(self.OUTER))
            t.write_bytes(make_frame(self.OUTER))
            self.assertEqual(
                analyze.classify(analyze.analyze(c), analyze.analyze(t)),
                "H_OBJ_SUPPORTED_SODIUM64_IGNORES_OBJ_WINDOW",
            )

    def test_classifies_outer_two_to_zero_as_falsified(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = root / "c.bin"
            t = root / "t.bin"
            c.write_bytes(make_frame(self.OUTER))
            t.write_bytes(make_frame([]))
            self.assertEqual(
                analyze.classify(analyze.analyze(c), analyze.analyze(t)),
                "H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ",
            )

    def test_one_outer_probe_is_indeterminate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = root / "c.bin"
            t = root / "t.bin"
            c.write_bytes(make_frame(self.OUTER))
            t.write_bytes(make_frame([self.OUTER[0]]))
            self.assertTrue(
                analyze.classify(analyze.analyze(c), analyze.analyze(t)).startswith(
                    "INDETERMINATE"
                )
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
