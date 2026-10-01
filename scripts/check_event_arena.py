#!/usr/bin/env python3
"""Prove complete simultaneous RDRAM owners, including four-byte event slots."""
import argparse
import json
from pathlib import Path
from check_runtime_arena import allocated_sections
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros


def layout(defines):
    ev = parse_macros(Path(defines).resolve().parents[1])
    value = lambda name: ev.name(name) & 0x1fffffff
    owners = {}
    for queue in (1, 2):
        for kind, size in [('BASE', 0x200), ('SIDEBAND', 0x500),
                           ('EVENT', ev.name('HCOMP_CGRAM_EVENT_CAPACITY') * 4)]:
            name = f'HCOMP_CGRAM_{kind}_QUEUE{queue}'
            start = value(name)
            owners[name] = (start, start + size)
        name = f'HCOMP_RAW_PALETTE_QUEUE{queue}'
        start = value(name)
        owners[name] = (start, start + 0x800)
    for name, start, size in [('main_winner', 0xe2000, 0x1180),
                              ('sub_color', 0xe4000, 0x1180),
                              ('preserved_ts', 0xe6000, 0x1180),
                              ('consumed_section', 0xf0000, 16)]:
        owners[name] = (start, start + size)
    chain = ['FRAMEBUFFER1', 'FRAMEBUFFER2', 'FRAMEBUFFER3', 'MODE7_TEXTURE',
             'VRAM_BUFFER', 'PALETTE_QUEUE1', 'PALETTE_QUEUE2', 'OAM_QUEUE1',
             'OAM_QUEUE2', 'DIRTY_QUEUE1', 'DIRTY_QUEUE2', 'SECTION_QUEUE1',
             'SECTION_QUEUE2', 'OBJECT_CACHE', 'TILE_STATS_OBJ', 'TILE_STATS_BG',
             'TILE_CACHE_OBJ', 'TILE_CACHE_BG', 'JIT_BUFFER', 'ROM_BUFFER',
             'ROM_CACHE_END']
    for first, last in zip(chain, chain[1:]):
        owners[first] = (value(first), value(last))
    assert ev.name('HCOMP_CGRAM_EVENT_CAPACITY') == 0x6000
    assert ev.name('HCOMP_CGRAM_EVENT_BYTES') == 0x18000
    assert ev.name('ROM_CACHE_SLOTS') == 244
    assert value('ROM_CACHE_END') == value('HCOMP_CGRAM_EVENT_QUEUE2') == 0x3e8000
    assert owners['HCOMP_CGRAM_EVENT_QUEUE2'][1] == 0x400000
    assert owners['HCOMP_CGRAM_EVENT_QUEUE1'][1] == 0xdae00
    return owners


def prove_disjoint(owners):
    intervals = sorted((a, b, name) for name, (a, b) in owners.items())
    for a, b, name in intervals:
        assert 0 <= a < b <= 0x400000, (name, a, b)
        if not name.startswith('ELF:'):
            assert a % 8 == b % 8 == 0, (name, 'DMA alignment')
    for (a, b, name), (c, d, other) in zip(intervals, intervals[1:]):
        assert b <= c, f'{name} [{a:#x},{b:#x}) overlaps {other} [{c:#x},{d:#x})'
    return intervals


def check(defines, elf=None):
    owners = layout(defines)
    if elf:
        for name, a, b in allocated_sections(elf):
            owners['ELF:' + name] = (a, b)
        # Boot clearing itself is a write owner, sharing only the fixed lower
        # renderer region. It must never touch loaded runtime/JIT/ROM pages.
        ev = parse_macros(Path(defines).resolve().parents[1])
        lo = ev.name('HCOMP_CGRAM_BASE_QUEUE1') & 0x1fffffff
        hi = ev.name('JIT_BUFFER') & 0x1fffffff
        for name, a, b in allocated_sections(elf):
            assert not (a < hi and b > lo), (name, 'boot clear overlap')
    intervals = prove_disjoint(owners)
    # The last DMA8 read at the declared record cap remains entirely in slot.
    for q in (1, 2):
        a, b = owners[f'HCOMP_CGRAM_EVENT_QUEUE{q}']
        assert a + ((0x6000 * 4 - 1) & ~7) + 8 == b
    return {name: {'start': a, 'end': b, 'bytes': b-a} for a, b, name in intervals}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--defines', type=Path, default=Path('src/defines.h'))
    ap.add_argument('--elf', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = check(args.defines, args.elf)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('EVENT_ARENA_FULL_EXTENTS PASS', len(result), 'owners; cap=24576; ROM slots=244')
