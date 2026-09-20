#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("make_gate_c_h_sample.py")
spec = importlib.util.spec_from_file_location("make_gate_c_h_sample", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

EXPECTED_ROM_SHA256 = "347e177ceef12a04b51b7e6958bb81b09d741acf4db8edb5aea2bea8fa82af8e"


class GateCHSampleGeneratorTests(unittest.TestCase):
    def test_hdma_table_covers_every_visible_line_once(self) -> None:
        table = mod.build_hdma_table()
        self.assertEqual(len(table), 227)
        self.assertEqual(table[0], 0xFF)
        self.assertEqual(table[1:128], bytes(range(127)))
        self.assertEqual(table[128], 0xE1)
        self.assertEqual(table[129:226], bytes(range(127, 224)))
        self.assertEqual(table[226], 0)

    def test_rom_is_deterministic_and_embeds_both_source_tables(self) -> None:
        rom = mod.build_rom()
        self.assertEqual(len(rom), 0x8000)
        self.assertEqual(hashlib.sha256(rom).hexdigest(), EXPECTED_ROM_SHA256)
        table = mod.build_hdma_table()
        for address in (
            mod.HDMA_WINDOW_TABLE_ADDRESS,
            mod.HDMA_PROBE_TABLE_ADDRESS,
        ):
            offset = address - mod.LOAD_ADDRESS
            self.assertEqual(rom[offset : offset + len(table)], table)

    def test_nmi_vector_and_title_are_present(self) -> None:
        rom = mod.build_rom()
        self.assertEqual(int.from_bytes(rom[0x7FFA:0x7FFC], "little"), mod.NMI_ADDRESS)
        self.assertTrue(rom[mod.HEADER : mod.HEADER + 21].startswith(b"S64 GATEC H SAMPLE"))


if __name__ == "__main__":
    unittest.main()
