#!/usr/bin/env python3
"""Host-side tests for the Sodium64 statistical profiler snapshot decoder."""

from __future__ import annotations

import struct
import sys
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
