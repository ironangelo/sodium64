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

    # Green visible-window rectangle, approximately matching the diagnostic.
    for y in range(8, 232):
        for x in range(76, 204):
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
    def test_classifies_three_to_three_as_supported(self) -> None:
        boxes = [(28, 104, 8, 8), (108, 104, 8, 8), (236, 104, 8, 8)]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = root / "c.bin"
            t = root / "t.bin"
            c.write_bytes(make_frame(boxes))
            t.write_bytes(make_frame(boxes))
            ca = analyze.analyze(c)
            ta = analyze.analyze(t)
            self.assertEqual(
                analyze.classify(ca, ta),
                "H_OBJ_SUPPORTED_SODIUM64_IGNORES_OBJ_WINDOW",
            )

    def test_classifies_three_to_one_as_falsified(self) -> None:
        control = [(28, 104, 8, 8), (108, 104, 8, 8), (236, 104, 8, 8)]
        treatment = [(108, 104, 8, 8)]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = root / "c.bin"
            t = root / "t.bin"
            c.write_bytes(make_frame(control))
            t.write_bytes(make_frame(treatment))
            ca = analyze.analyze(c)
            ta = analyze.analyze(t)
            self.assertEqual(
                analyze.classify(ca, ta),
                "H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
