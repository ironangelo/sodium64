#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "make_gate_c_h_comp_half", HERE / "make_gate_c_h_comp_half.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class HCompHalfGeneratorTests(unittest.TestCase):
    def test_rom_is_deterministic_32k_lorom(self) -> None:
        a = mod.build_rom()
        b = mod.build_rom()
        self.assertEqual(a, b)
        self.assertEqual(len(a), 0x8000)
        self.assertEqual(a[0x7FC0:0x7FC0+19], b"S64 GATEC HALF MATH")
        self.assertEqual(a[0x7FD5], 0x20)
        self.assertEqual(int.from_bytes(a[0x7FFA:0x7FFC], "little"), mod.NMI_ADDRESS)
        self.assertEqual(hashlib.sha256(a).hexdigest(), hashlib.sha256(b).hexdigest())

    def test_assets_encode_independent_main_and_sub_colors(self) -> None:
        _, bg1, bg2, palette = mod.build_assets()
        self.assertEqual(bg1[:2], b"\x00\x00")
        self.assertEqual(bg2[:2], b"\x00\x04")
        self.assertEqual(
            int.from_bytes(palette[2:4], "little"),
            mod.rgb5_word(mod.SUB_RGB5),
        )
        self.assertEqual(
            int.from_bytes(palette[34:36], "little"),
            mod.rgb5_word(mod.MAIN_RGB5),
        )

    def test_expected_math_is_even_and_non_saturating(self) -> None:
        self.assertEqual(mod.CONTROL_RGB5, (16, 16, 0))
        self.assertEqual(mod.TREATMENT_RGB5, (8, 8, 0))
        self.assertTrue(all(0 <= x <= 31 for x in mod.CONTROL_RGB5))
        self.assertTrue(all(x % 2 == 0 for x in mod.CONTROL_RGB5))


if __name__ == "__main__":
    unittest.main()
