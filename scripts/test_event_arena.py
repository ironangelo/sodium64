#!/usr/bin/env python3
"""Negative owner controls and ROM-cache eviction across the new wrap boundary."""
import unittest
import shutil
import tempfile
from pathlib import Path
from check_event_arena import layout, prove_disjoint, selected_macros

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
        macros=selected_macros(ROOT/'src/defines.h')
        capacity=macros.name('ROM_CACHE_SLOTS')
        cache_end=macros.name('ROM_CACHE_END')&0x1fffffff
        slots = [None]*capacity
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
            self.assertLessEqual(0x200000 + pointer*8192 + 8192, cache_end)
            pointer = 0 if pointer == capacity-1 else pointer+1
            misses += 1
            self.assertEqual(len(mapped), len(set(x for x in slots if x is not None)))
        self.assertGreater(misses, capacity*4)

    def test_trace_preprocessor_selects_relocated_arena(self):
        owners=layout(ROOT/'src/defines.h',diagnostic_trace=True)
        prove_disjoint(owners)
        self.assertEqual(owners['HCOMP_CGRAM_BASE_QUEUE1'][0],0xd2000)
        self.assertEqual(owners['HCOMP_CGRAM_EVENT_QUEUE1'][1],0xeae00)
        self.assertLessEqual(owners['HCOMP_CGRAM_EVENT_QUEUE1'][1],owners['HCOMP_RAW_PALETTE_QUEUE1'][0])

    def test_profile_sampler_avoids_boot_clear(self):
        owners=layout(ROOT/'src/defines.h',profile=True)
        # Real profile candidate's linked extent exceeded the old C2000
        # boundary. Retaining that boundary would erase sampler/runtime data.
        owners['ELF:profile_runtime']=(0xe000,0xc2b10)
        prove_disjoint(owners)
        owners['HCOMP_CGRAM_BASE_QUEUE1']=(0xc2000,0xc2200)
        with self.assertRaisesRegex(AssertionError,'overlaps'):
            prove_disjoint(owners)

    def test_brr_observer_arena_owns_growth_without_overlap(self):
        owners=layout(ROOT/'src/defines.h',diagnostic_trace=True,brr_observer=True)
        self.assertEqual(owners['HCOMP_CGRAM_BASE_QUEUE1'][0],0xd4000)
        self.assertEqual(owners['HCOMP_CGRAM_EVENT_QUEUE1'][1],0xece00)
        self.assertLessEqual(owners['HCOMP_CGRAM_EVENT_QUEUE1'][1],owners['HCOMP_RAW_PALETTE_QUEUE1'][0])
        owners['ELF:synthetic_observer_growth']=(0xe000,0xd2100)
        prove_disjoint(owners)
        owners['HCOMP_CGRAM_BASE_QUEUE1']=(0xd2000,0xd2200)
        with self.assertRaisesRegex(AssertionError,'overlaps'):
            prove_disjoint(owners)

    def test_brr_observer_cannot_select_normal_layout(self):
        with self.assertRaisesRegex(ValueError,'requires --diagnostic-trace'):
            layout(ROOT/'src/defines.h',brr_observer=True)

    def test_host_preprocessor_preserves_all_conditional_owners(self):
        compiler=shutil.which('gcc') or shutil.which('clang') or shutil.which('cc')
        self.assertIsNotNone(compiler,'host CI requires a C preprocessor')
        for selection in ({'diagnostic_trace':True},{'profile':True},
                          {'diagnostic_trace':True,'brr_observer':True}):
            expected=layout(ROOT/'src/defines.h',**selection)
            actual=layout(ROOT/'src/defines.h',cc=compiler,**selection)
            self.assertEqual(actual,expected)
            prove_disjoint(actual)

    def test_host_preprocessor_rejects_unknown_include(self):
        compiler=shutil.which('gcc') or shutil.which('clang') or shutil.which('cc')
        self.assertIsNotNone(compiler,'host CI requires a C preprocessor')
        with tempfile.TemporaryDirectory() as temporary:
            header=Path(temporary)/'defines.h'
            header.write_text((ROOT/'src/defines.h').read_text()+'\n#include <unknown_arena_dependency.h>\n')
            with self.assertRaisesRegex(ValueError,'permits only'):
                layout(header,diagnostic_trace=True,cc=compiler)


if __name__ == '__main__':
    unittest.main()
