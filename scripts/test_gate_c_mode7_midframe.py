#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import unittest

import make_gate_c_mode7_midframe as diag


class GateCMode7MidframeTests(unittest.TestCase):
    def test_rom_is_deterministic_valid_32k_lorom(self) -> None:
        a = diag.build_rom()
        b = diag.build_rom()
        self.assertEqual(a, b)
        self.assertEqual(len(a), 0x8000)
        self.assertEqual(a[0x7FD5], 0x20)
        self.assertEqual(hashlib.sha256(a).digest(), hashlib.sha256(b).digest())

    def test_native_and_emulation_interrupt_vectors_target_handlers(self) -> None:
        rom = diag.build_rom()

        def word(offset: int) -> int:
            return int.from_bytes(rom[offset : offset + 2], "little")

        self.assertEqual(word(0x7FEA), diag.NMI_ADDRESS)
        self.assertEqual(word(0x7FEE), diag.IRQ_ADDRESS)
        self.assertEqual(word(0x7FFA), diag.NMI_ADDRESS)
        self.assertEqual(word(0x7FFC), diag.LOAD_ADDRESS)
        self.assertEqual(word(0x7FFE), diag.IRQ_ADDRESS)

    def test_program_requests_exactly_one_mode7_interval(self) -> None:
        program = diag.build_program()
        mode7 = bytes((0xA9, diag.TREATMENT_MODE, 0x8D, 0x05, 0x21))
        mode1 = bytes((0xA9, diag.CONTROL_MODE, 0x8D, 0x05, 0x21))
        self.assertEqual(program.count(mode7), 1)
        self.assertGreaterEqual(program.count(mode1), 2)

    def test_vcount_irq_chain_uses_two_visible_lines(self) -> None:
        program = diag.build_program()
        irq1_low = bytes((0xA9, diag.IRQ1_LINE & 0xFF, 0x8D, 0x09, 0x42))
        irq2_low = bytes((0xA9, diag.IRQ2_LINE & 0xFF, 0x8D, 0x09, 0x42))
        enable = bytes((0xA9, 0xA0, 0x8D, 0x00, 0x42))
        nmi_only = bytes((0xA9, 0x80, 0x8D, 0x00, 0x42))
        self.assertEqual(program.count(irq1_low), 1)
        self.assertEqual(program.count(irq2_low), 1)
        self.assertEqual(program.count(enable), 1)
        self.assertGreaterEqual(program.count(nmi_only), 2)

    def test_same_frame_evidence_slots_are_distinct(self) -> None:
        program = diag.build_program()
        irq1_frame_store = bytes((0x8F, 0x05, 0x00, 0x7E))
        irq2_frame_store = bytes((0x8F, 0x06, 0x00, 0x7E))
        post_phase = bytes((0xA9, diag.POSTTEST_PHASE, 0x8F, 0x01, 0x00, 0x7E))
        # Each slot is zero-initialized once, then written once by its IRQ.
        self.assertEqual(program.count(irq1_frame_store), 2)
        self.assertEqual(program.count(irq2_frame_store), 2)
        self.assertEqual(program.count(post_phase), 1)

    def test_pretest_hold_is_long_enough_for_fresh_control_capture(self) -> None:
        self.assertGreaterEqual(diag.PRETEST_FRAMES, 20)
        self.assertLess(diag.IRQ1_LINE, diag.IRQ2_LINE)
        self.assertLess(diag.IRQ2_LINE, 224)


if __name__ == "__main__":
    unittest.main()
