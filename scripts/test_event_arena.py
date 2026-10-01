#!/usr/bin/env python3
"""Negative owner controls and ROM-cache eviction across the new wrap boundary."""
import unittest
from pathlib import Path
from check_event_arena import layout, prove_disjoint

ROOT = Path(__file__).resolve().parents[1]


class EventArenaTests(unittest.TestCase):
    def test_full_slot_writes_and_dma8(self):
        owners = layout(ROOT/'src/defines.h')
        prove_disjoint(owners)
        # Exercise every legal record destination and aligned DMA pair, not
        # only the documented legal worst case of 20780 records.
        for queue in (1, 2):
            a, b = owners[f'HCOMP_CGRAM_EVENT_QUEUE{queue}']
            for i in range(0x6000):
                self.assertLessEqual(a + i*4 + 4, b)
                self.assertLessEqual(a + (i//2)*8 + 8, b)

    def test_old_overlap_rejected(self):
        owners = layout(ROOT/'src/defines.h')
        owners['HCOMP_CGRAM_EVENT_QUEUE2'] = (0xd7000, 0xef000)
        with self.assertRaisesRegex(AssertionError, 'overlaps'):
            prove_disjoint(owners)

    def test_old_rom_cache_end_rejected(self):
        owners = layout(ROOT/'src/defines.h')
        owners['ROM_BUFFER'] = (0x200000, 0x400000)
        with self.assertRaisesRegex(AssertionError, 'overlaps'):
            prove_disjoint(owners)

    def test_wrap_eviction_and_reload(self):
        slots = [None]*244
        mapped = {}
        pointer = 0
        misses = 0
        references = list(range(512)) + list(range(511, -1, -1)) + list(range(512))
        for page in references:
            if page in mapped:
                self.assertEqual(slots[mapped[page]], page)
                continue
            old = slots[pointer]
            if old is not None:
                del mapped[old]
            slots[pointer] = page
            mapped[page] = pointer
            self.assertLessEqual(0x200000 + pointer*8192 + 8192, 0x3e8000)
            pointer = 0 if pointer == 243 else pointer+1
            misses += 1
            self.assertEqual(len(mapped), len(set(x for x in slots if x is not None)))
        self.assertGreater(misses, 244*4)


if __name__ == '__main__':
    unittest.main()
