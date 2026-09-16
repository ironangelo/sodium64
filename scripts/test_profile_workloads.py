#!/usr/bin/env python3
"""Host-side tests for deterministic SNES profiling workload ROMs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_profile_workloads as workloads  # noqa: E402


class ProfileWorkloadTests(unittest.TestCase):
    def test_every_workload_builds_as_valid_32k_lorom(self) -> None:
        for name in workloads.WORKLOADS:
            with self.subTest(name=name):
                rom = workloads.build_rom(name)
                self.assertEqual(len(rom), workloads.ROM_SIZE)
                self.assertEqual(rom[0x7FD5], 0x20)
                self.assertEqual(rom[0x7FD6], 0x00)
                self.assertEqual(rom[0x7FD7], 0x05)
                self.assertEqual(int.from_bytes(rom[0x7FFC:0x7FFE], "little"), 0x8000)

                complement = int.from_bytes(rom[0x7FDC:0x7FDE], "little")
                checksum = int.from_bytes(rom[0x7FDE:0x7FE0], "little")
                self.assertEqual(complement ^ checksum, 0xFFFF)
                self.assertEqual(sum(rom) & 0xFFFF, checksum)

    def test_workloads_are_distinct(self) -> None:
        programs = {name: workloads.WORKLOADS[name]() for name in workloads.WORKLOADS}
        self.assertEqual(len(set(programs.values())), len(programs))

    def test_all_relative_branches_resolve(self) -> None:
        # Calling every builder exercises Assembler.finish(), which raises if a
        # label is missing or a branch displacement falls outside rel8 range.
        for name, builder in workloads.WORKLOADS.items():
            with self.subTest(name=name):
                self.assertGreater(len(builder()), 0)

    def test_gameplay_balanced_has_fixed_native_nmi_vector(self) -> None:
        rom = workloads.build_rom("gameplay-balanced")
        native_nmi = int.from_bytes(rom[0x7FEA:0x7FEC], "little")
        emulation_nmi = int.from_bytes(rom[0x7FFA:0x7FFC], "little")
        self.assertEqual(native_nmi, workloads.GAMEPLAY_NMI_ADDRESS)
        self.assertEqual(emulation_nmi, workloads.GAMEPLAY_NMI_ADDRESS)

        handler_offset = workloads.GAMEPLAY_NMI_ADDRESS - workloads.LOAD_ADDRESS
        self.assertEqual(rom[handler_offset : handler_offset + 3], bytes([0x48, 0xDA, 0x5A]))

    def test_gameplay_balanced_uses_wait_for_interrupt_frame_pacing(self) -> None:
        program = workloads.workload_gameplay_balanced()
        # The measured loop should sleep between frames instead of continuously
        # burning S-CPU time like the synthetic cpu-alu/wram stress controls.
        self.assertIn(0xCB, program[: workloads.GAMEPLAY_NMI_OFFSET])  # WAI
        # NMI handler returns with RTI.
        self.assertEqual(program[-1], 0x40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
