#!/usr/bin/env python3
"""Host-side tests for the Sodium64 statistical profiler snapshot decoder."""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import profile_report  # noqa: E402


MAGIC_ADDRESS = 0x80001000
BUFFER_ADDRESS = MAGIC_ADDRESS + profile_report.HEADER_SIZE
CAPACITY = 4
BUFFER_END = BUFFER_ADDRESS + CAPACITY * 4


def make_snapshot(
    *,
    sample_count: int,
    write_index: int,
    ring: list[int],
    last_epc: int,
    word_swapped: bool = False,
) -> bytes:
    assert len(ring) == CAPACITY
    write_ptr = BUFFER_ADDRESS + write_index * 4
    header = struct.pack(
        ">8I",
        profile_report.MAGIC,
        1,
        65521,
        CAPACITY,
        write_ptr,
        sample_count,
        last_epc,
        0,
    )
    blob = header + b"".join(struct.pack(">I", value) for value in ring)
    if word_swapped:
        blob = b"".join(blob[offset : offset + 4][::-1] for offset in range(0, len(blob), 4))
    return blob


class SnapshotDecoderTests(unittest.TestCase):
    def decode(self, blob: bytes):
        return profile_report.reconstruct_samples(
            blob,
            MAGIC_ADDRESS,
            BUFFER_ADDRESS,
            BUFFER_END,
        )

    def test_canonical_snapshot_before_wrap(self) -> None:
        blob = make_snapshot(
            sample_count=3,
            write_index=3,
            ring=[0x80000100, 0x80000200, 0x80000300, 0],
            last_epc=0x80000300,
        )
        meta, samples = self.decode(blob)
        self.assertEqual(meta["snapshot_format"], "canonical big-endian")
        self.assertEqual(meta["sample_count"], 3)
        self.assertEqual(samples, [0x80000100, 0x80000200, 0x80000300])

    def test_word_swapped_snapshot_is_normalized(self) -> None:
        blob = make_snapshot(
            sample_count=3,
            write_index=3,
            ring=[0x80000100, 0x80000200, 0x80000300, 0],
            last_epc=0x80000300,
            word_swapped=True,
        )
        meta, samples = self.decode(blob)
        self.assertEqual(meta["snapshot_format"], "32-bit word-swapped")
        self.assertEqual(meta["last_epc"], 0x80000300)
        self.assertEqual(samples, [0x80000100, 0x80000200, 0x80000300])

    def test_wrapped_ring_is_returned_oldest_to_newest(self) -> None:
        # After six writes to a four-entry ring, index 2 is the next write slot.
        # Physical ring: [sample5, sample6, sample3, sample4].
        blob = make_snapshot(
            sample_count=6,
            write_index=2,
            ring=[0x80000500, 0x80000600, 0x80000300, 0x80000400],
            last_epc=0x80000600,
        )
        meta, samples = self.decode(blob)
        self.assertEqual(meta["valid_samples"], 4)
        self.assertEqual(
            samples,
            [0x80000300, 0x80000400, 0x80000500, 0x80000600],
        )

    def test_invalid_magic_is_rejected(self) -> None:
        blob = bytearray(
            make_snapshot(
                sample_count=0,
                write_index=0,
                ring=[0, 0, 0, 0],
                last_epc=0,
            )
        )
        blob[0:4] = b"NOPE"
        with self.assertRaisesRegex(ValueError, "bad profiler magic"):
            self.decode(bytes(blob))


class LinkerMapClassificationTests(unittest.TestCase):
    def make_map(self) -> Path:
        text = """
Discarded input sections
 .text          0x00000000      0x100 build/src/cpu.o

Linker script and memory map
 .boot          0x80000400       0x10 build/src/main.o
 .text          0x80000420      0x200 build/src/apu.o
 .text          0x80001000      0x300 build/src/cpu.o
 .text          0x80002000      0x100 build/src/ppu.o
 .text          0x80003000       0x80 build/src/dma.o
"""
        handle = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_map_parser_ignores_discarded_zero_address_ranges(self) -> None:
        starts, ranges = profile_report.load_text_ranges(self.make_map())
        self.assertEqual(starts, [0x80000400, 0x80000420, 0x80001000, 0x80002000, 0x80003000])
        self.assertEqual(profile_report.object_for_pc(0x80001020, starts, ranges), "cpu.o")
        self.assertIsNone(profile_report.object_for_pc(0x80004000, starts, ranges))

    def test_subsystem_classification_prioritizes_waits_and_jit(self) -> None:
        self.assertEqual(
            profile_report.subsystem_for_sample(0x80002020, "rsp_wait+0x4", "ppu.o"),
            "RSP wait",
        )
        self.assertEqual(
            profile_report.subsystem_for_sample(0x801C0100, "[APU JIT generated code]", None),
            "APU JIT generated",
        )
        self.assertEqual(
            profile_report.subsystem_for_sample(0x80001020, "cpu_execute+0x20", "cpu.o"),
            "S-CPU interpreter",
        )
        self.assertEqual(
            profile_report.subsystem_for_sample(0x80003020, "trigger_dma+0x20", "dma.o"),
            "DMA/HDMA",
        )

    def test_vram_semaphore_guard_is_not_mislabeled_as_ppu_work(self) -> None:
        for symbolicated in (
            "write_vmdatal",
            "write_vmdatal+0x4",
            "write_vmdatal+0xC",
            "write_vmdatah",
            "write_vmdatah+0x8",
        ):
            with self.subTest(symbolicated=symbolicated):
                self.assertEqual(
                    profile_report.subsystem_for_sample(0x80002000, symbolicated, "ppu.o"),
                    "RSP/VRAM semaphore wait",
                )

        # Once the four-instruction spin guard has been passed, these routines
        # are performing actual PPU/VRAM work and should stay in the PPU bucket.
        self.assertEqual(
            profile_report.subsystem_for_sample(0x80002010, "write_vmdatal+0x10", "ppu.o"),
            "PPU/events/frame prep",
        )
        self.assertEqual(
            profile_report.subsystem_for_sample(0x80002014, "write_vmdatah+0x14", "ppu.o"),
            "PPU/events/frame prep",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
