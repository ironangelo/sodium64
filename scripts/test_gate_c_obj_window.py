#!/usr/bin/env python3
"""Host-side tests for the Gate-C OBJ-window diagnostic ROM."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_gate_c_obj_window as diag  # noqa: E402


EXPECTED_SHA256 = "b91fdcd4a4ec7c4dce3b49946e054e4847f86bad03f8da56083c6757b13f6f77"


class GateCObjWindowDiagnosticTests(unittest.TestCase):
    def test_rom_is_deterministic_valid_32k_lorom(self) -> None:
        rom = diag.build_rom()
        self.assertEqual(len(rom), diag.ROM_SIZE)
        self.assertEqual(hashlib.sha256(rom).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(rom[0x7FD5], 0x20)
        self.assertEqual(rom[0x7FD6], 0x00)
        self.assertEqual(rom[0x7FD7], 0x05)
        self.assertEqual(int.from_bytes(rom[0x7FFC:0x7FFE], "little"), diag.LOAD_ADDRESS)
        self.assertEqual(int.from_bytes(rom[0x7FEA:0x7FEC], "little"), diag.NMI_ADDRESS)
        self.assertEqual(int.from_bytes(rom[0x7FFA:0x7FFC], "little"), diag.NMI_ADDRESS)

        complement = int.from_bytes(rom[0x7FDC:0x7FDE], "little")
        checksum = int.from_bytes(rom[0x7FDE:0x7FE0], "little")
        self.assertEqual(complement ^ checksum, 0xFFFF)
        self.assertEqual(sum(rom) & 0xFFFF, checksum)

    def test_visual_assets_have_three_known_obj_probes(self) -> None:
        bg_tile, obj_tile, bg_map, palette, oam = diag.build_assets()
        self.assertEqual(bg_tile, obj_tile)
        self.assertEqual(bg_tile, bytes([0xFF, 0x00] * 8 + [0x00] * 16))
        self.assertEqual(bg_map, bytes(0x800))
        self.assertEqual(int.from_bytes(palette[2:4], "little"), 0x03E0)
        self.assertEqual(int.from_bytes(palette[0x102:0x104], "little"), 0x001F)

        for index, x in enumerate((16, 96, 224)):
            offset = index * 4
            self.assertEqual(oam[offset : offset + 4], bytes([x, 96, 0, 0]))
        self.assertTrue(all(oam[index * 4 + 1] == 0xF0 for index in range(3, 128)))
        self.assertEqual(oam[0x200:], bytes(0x20))

    def test_program_encodes_only_requested_window_features(self) -> None:
        program = diag.build_program()

        def lda_sta(value: int, address: int) -> bytes:
            return bytes([0xA9, value, 0x8D, address & 0xFF, address >> 8])

        for value, address in (
            (0x03, 0x2123),                  # W12SEL inverted W1
            (0x00, 0x2124),                  # W34SEL off
            (0x03, 0x2125),                  # WOBJSEL inverted W1
            (diag.WINDOW_LEFT, 0x2126),
            (diag.WINDOW_RIGHT, 0x2127),
            (0x11, 0x212C),                  # TM BG1+OBJ
            (0x00, 0x212D),                  # TS
            (diag.CONTROL_TMW, 0x212E),
            (0x00, 0x212F),                  # TSW
            (0x00, 0x2130),                  # CGWSEL
            (0x00, 0x2131),                  # CGADSUB
            (0x80, 0x4200),                  # NMI only, no H/V IRQ
        ):
            self.assertIn(lda_sta(value, address), program)

        # No write to HDMAEN ($420C): the diagnostic deliberately excludes HDMA.
        self.assertNotIn(bytes([0x8D, 0x0C, 0x42]), program)

    def test_nmi_switches_exactly_between_control_and_treatment_tmw(self) -> None:
        program = diag.build_program()
        nmi = program[diag.NMI_OFFSET:]

        control_write = bytes([0xA9, diag.CONTROL_TMW, 0x8D, 0x2E, 0x21])
        treatment_write = bytes([0xA9, diag.TREATMENT_TMW, 0x8D, 0x2E, 0x21])

        self.assertEqual(nmi.count(control_write), 1)
        self.assertEqual(nmi.count(treatment_write), 1)
        self.assertIn(bytes([0xC9, diag.PHASE_FRAMES]), nmi)
        self.assertIn(bytes([0xC9, diag.PHASE_FRAMES * 2]), nmi)

        # The phase mirror lets CI synchronize without changing any PPU state.
        self.assertIn(
            bytes([0xA9, diag.CONTROL_TMW, 0x8F, 0x01, 0x00, 0x7E]),
            nmi,
        )
        self.assertIn(
            bytes([0xA9, diag.TREATMENT_TMW, 0x8F, 0x01, 0x00, 0x7E]),
            nmi,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
