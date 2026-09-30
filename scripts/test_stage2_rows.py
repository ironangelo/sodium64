#!/usr/bin/env python3
"""Reject lower-frame holes even when the composed upper band passes."""
import struct
import unittest
from pathlib import Path
from capture_stage2_publication import classify_frame
from make_gate_c_stage1 import window
from test_gate_c_hcomp_main_sub_exec_clean import insns, section


def reference(phase):
    words = [0] * (280 * 240)
    left, right = window(phase)
    for y in range(8, 16):
        for x in range(256):
            words[y*280+12+x] = 1 if left <= x <= right else 0x7bc1
    for y in range(16, 232):
        words[y*280+12:y*280+268] = [0xf801] * 256
    return words


class Rows(unittest.TestCase):
    def test_complete_reference_all_phases(self):
        for phase in range(256):
            result = classify_frame(struct.pack('>67200H', *reference(phase)))
            self.assertTrue(result['passed'], phase)
            self.assertEqual(result['band']['phases'], [phase])
            self.assertEqual(result['lower']['pixels'], 216*256)

    def test_original_blue_stripe_fails_with_passing_band(self):
        words = reference(161)
        for y in range(31, 71):
            words[y*280+12:y*280+268] = [0x003f] * 256
        result = classify_frame(struct.pack('>67200H', *words))
        self.assertTrue(result['band']['passed'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['lower']['bad_rows'], list(range(31, 71)))
        self.assertEqual(result['lower']['differing_pixels'], 10240)

    def test_lower_edges_and_single_pixel_holes(self):
        for y, x in [(16, 12), (231, 267), (100, 127)]:
            words = reference(32)
            words[y*280+x] = 0x003f
            result = classify_frame(struct.pack('>67200H', *words))
            self.assertFalse(result['passed'])
            self.assertEqual(result['lower']['differing_pixels'], 1)
            self.assertEqual(result['lower']['bad_rows'], [y])

    def test_exact_geometry_required(self):
        with self.assertRaises(ValueError):
            classify_frame(bytes(8960))

    def test_row_index_lifetime(self):
        src = (Path(__file__).resolve().parents[1]/'src/rsp_main.S').read_text()
        row = insns(section(src, 'draw_row:', 'bg_windows:'))
        recover = row.index('srl t3, s2, 1')
        lookup = row.index('lbu t2, BGXSC(t3)')
        mask = row.index('lbu t2, SHIFT_TABLE(t3)')
        self.assertLess(recover, lookup)
        self.assertLess(lookup, mask)
        # No write to the recovered index before the second use. DMA only
        # writes t0, so it is safe even on the load_screen branch/call paths.
        self.assertFalse(any(i.split(',')[0].endswith(' t3')
                             for i in row[recover+1:mask]))
        dma = insns(section(src, 'dma_read:', 'rdp_send:'))
        self.assertFalse(any(i.split(',')[0].endswith(' t3') for i in dma))
        self.assertNotIn('srl t2, s2, 1', row)
        self.assertIn('blt s1, k1, draw_row', section(src, 'finish_row:', 'skip_decode:'))


if __name__ == '__main__':
    unittest.main()
