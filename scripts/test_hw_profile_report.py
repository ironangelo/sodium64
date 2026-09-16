#!/usr/bin/env python3

import struct
import unittest

import hw_profile_report as hw


def make_capture(*, complete=1, apu_clock=21, samples=1234):
    size = 0x8000
    snapshot_offset = 0x100
    profile_size = 0x40
    words = [0] * hw.HEADER_WORDS
    words[0] = hw.HW_MAGIC
    words[1] = hw.HW_VERSION
    words[2] = 2
    words[3] = 5
    words[4] = samples
    words[5] = 65521
    words[6] = profile_size
    words[7] = snapshot_offset
    words[8:13] = [48, 49, 47, 48, 48]
    words[13] = 0
    words[14] = apu_clock
    words[15] = 4
    words[16] = 8
    words[17] = 0
    words[18] = 1
    words[19] = 0
    words[20] = 0
    words[21] = 0x0D98
    words[22] = complete

    blob = bytearray(size)
    struct.pack_into(">32I", blob, 0, *words)
    struct.pack_into(">I", blob, snapshot_offset, hw.PROFILE_MAGIC)
    struct.pack_into(">I", blob, snapshot_offset + 4, 1)
    return bytes(blob)


class HardwareProfileReportTests(unittest.TestCase):
    def test_parses_strict_capture_and_extracts_snapshot(self):
        capture, snapshot = hw.parse_capture(make_capture())
        self.assertEqual(capture.capture_format, "canonical big-endian")
        self.assertEqual(capture.frame_budgets, (48, 49, 47, 48, 48))
        self.assertEqual(capture.sample_count, 1234)
        self.assertEqual(capture.apu_clock, 21)
        self.assertEqual(capture.sp_pc, 0x0D98)
        self.assertEqual(len(snapshot), 0x40)
        self.assertEqual(struct.unpack_from(">I", snapshot, 0)[0], hw.PROFILE_MAGIC)

    def test_normalizes_word_swapped_save(self):
        canonical = make_capture()
        swapped = b"".join(
            canonical[offset : offset + 4][::-1]
            for offset in range(0, len(canonical), 4)
        )
        capture, snapshot = hw.parse_capture(swapped)
        self.assertEqual(capture.capture_format, "32-bit word-swapped")
        self.assertEqual(capture.frame_budgets[-1], 48)
        self.assertEqual(struct.unpack_from(">I", snapshot, 0)[0], hw.PROFILE_MAGIC)

    def test_running_rsp_pc_is_not_interpreted(self):
        blob = bytearray(make_capture())
        struct.pack_into(">I", blob, 18 * 4, 0)  # SP_STATUS: running
        capture, _ = hw.parse_capture(bytes(blob))
        self.assertFalse(capture.sp_pc_meaningful)
        self.assertIsNone(capture.sp_pc)

    def test_rejects_partial_capture(self):
        with self.assertRaisesRegex(ValueError, "not marked complete"):
            hw.parse_capture(make_capture(complete=0))

    def test_rejects_underclocked_apu(self):
        with self.assertRaisesRegex(ValueError, "apu_clock=21"):
            hw.parse_capture(make_capture(apu_clock=42))

    def test_rejects_low_sample_density(self):
        with self.assertRaisesRegex(ValueError, "statistical samples"):
            hw.parse_capture(make_capture(samples=100))


if __name__ == "__main__":
    unittest.main()
