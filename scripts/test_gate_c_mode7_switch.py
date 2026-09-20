#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import unittest

import make_gate_c_mode7_switch as diag


class GateCMode7SwitchTests(unittest.TestCase):
    def test_rom_is_deterministic_valid_32k_lorom(self) -> None:
        a = diag.build_rom()
        b = diag.build_rom()
        self.assertEqual(a, b)
        self.assertEqual(len(a), 0x8000)
        self.assertEqual(a[0x7FD5], 0x20)
        self.assertEqual(hashlib.sha256(a).digest(), hashlib.sha256(b).digest())

    def test_program_contains_only_requested_bgmode_phase_values(self) -> None:
        program = diag.build_program()
        write_mode1 = bytes((0xA9, diag.CONTROL_MODE, 0x8D, 0x05, 0x21))
        write_mode7 = bytes((0xA9, diag.TREATMENT_MODE, 0x8D, 0x05, 0x21))
        self.assertGreaterEqual(program.count(write_mode1), 2)
        self.assertEqual(program.count(write_mode7), 1)

    def test_phase_mirror_encodes_mode1_and_mode7(self) -> None:
        program = diag.build_program()
        mode1 = bytes((0xA9, diag.CONTROL_MODE, 0x8F, 0x01, 0x00, 0x7E))
        mode7 = bytes((0xA9, diag.TREATMENT_MODE, 0x8F, 0x01, 0x00, 0x7E))
        self.assertGreaterEqual(program.count(mode1), 2)
        self.assertEqual(program.count(mode7), 1)


if __name__ == "__main__":
    unittest.main()
