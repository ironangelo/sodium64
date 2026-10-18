#!/usr/bin/env python3
"""Check selected compositor owners and actual ELF extents; no native claim."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

from linked_cpu_regression import load_elf
from test_gate_c_cgram_rsp_consumer_clean_contract import MacroEval


def allocated_sections(path):
    data = Path(path).read_bytes()
    assert data[:4] == b'\x7fELF' and data[4] in (1, 2)
    endian = '>' if data[5] == 2 else '<'
    hfmt, sfmt = ('16sHHIIIIIHHHHHH', 'IIIIIIIIII') if data[4] == 1 else ('16sHHIQQQIHHHHHH', 'IIQQQQIIQQ')
    header = struct.unpack_from(endian + hfmt, data)
    sections = [struct.unpack_from(endian + sfmt, data, header[6] + i*header[11]) for i in range(header[12])]
    strings = sections[header[13]]
    names = data[strings[4]:strings[4]+strings[5]]
    for section in sections:
        if section[2] & 2 and section[5]:
            name = names[section[0]:].split(b'\0', 1)[0].decode()
            start = section[3] & 0x1fffffff
            yield name, start, start + section[5]


def prove(owners, limit):
    intervals = sorted((a, b, name) for name, (a, b) in owners.items())
    for a, b, name in intervals:
        assert 0 <= a < b <= limit, (name, 'extent', a, b)
        if not name.startswith('ELF:'):
            assert a % 8 == b % 8 == 0, (name, 'DMA alignment')
    for (a, b, name), (c, d, other) in zip(intervals, intervals[1:]):
        assert b <= c, (name, 'overlap', other)
    return intervals


def read_macros(defines, compiler=None):
    compiler = compiler or shutil.which('mips64-elf-gcc')
    if not compiler:
        prefix = Path(os.environ.get('N64_INST', 'C:/n64-toolchain'))
        compiler = str(prefix/'bin'/('mips64-elf-gcc.exe' if os.name == 'nt' else 'mips64-elf-gcc'))
    include = Path(compiler).resolve().parents[1]/'mips64-elf/include'
    result = subprocess.run([compiler, '-E', '-dM', '-x', 'assembler-with-cpp',
        '-DSODIUM64_FAITHFUL_RENDERER=1', '-I'+str(include), str(Path(defines).resolve())],
        check=True, capture_output=True, text=True)
    return MacroEval(dict(re.findall(r'^#define (\w+) (.+)$', result.stdout, re.M)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--defines', type=Path, default=Path('src/defines.h'))
    parser.add_argument('--cc')
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    macros = read_macros(args.defines, args.cc)
    value = lambda name: macros.name(name) & 0x1fffffff
    owners = {}
    for queue in (1, 2):
        for kind, size in (('BASE', 512), ('SIDEBAND', 1280), ('EVENT', 98304)):
            name = f'HCOMP_CGRAM_{kind}_QUEUE{queue}'
            start = value(name); owners[name] = (start, start+size)
        name = f'HCOMP_RAW_PALETTE_QUEUE{queue}'
        start = value(name); owners[name] = (start, start+2048)
        name = f'HCOMP_ROW_FIXED_QUEUE{queue}'
        start = value(name); owners[name] = (start, start+512)
    for name in ('HCOMP_WINNER_ARENA', 'HCOMP_SUB_ARENA', 'HCOMP_PRESENCE_ARENA'):
        start = value(name); owners[name] = (start, start+macros.name('HCOMP_SURFACE_BYTES'))
    owners['consumed_section'] = (0xf0000, 0xf0010)
    chain = ('FRAMEBUFFER1', 'FRAMEBUFFER2', 'FRAMEBUFFER3', 'MODE7_TEXTURE',
        'VRAM_BUFFER', 'PALETTE_QUEUE1', 'PALETTE_QUEUE2', 'OAM_QUEUE1', 'OAM_QUEUE2',
        'DIRTY_QUEUE1', 'DIRTY_QUEUE2', 'SECTION_QUEUE1', 'SECTION_QUEUE2',
        'OBJECT_CACHE', 'TILE_STATS_OBJ', 'TILE_STATS_BG', 'TILE_CACHE_OBJ',
        'TILE_CACHE_BG', 'JIT_BUFFER', 'ROM_BUFFER', 'ROM_CACHE_END')
    for first, last in zip(chain, chain[1:]):
        owners[first] = (value(first), value(last))
    assert macros.name('HCOMP_CGRAM_EVENT_CAPACITY') == 24576
    assert macros.name('HCOMP_CGRAM_EVENT_BYTES') == 98304
    assert macros.name('ROM_CACHE_SLOTS') == 194
    assert value('ROM_CACHE_END') == value('HCOMP_WINNER_ARENA') == 0x384000
    assert value('HCOMP_CGRAM_BASE_QUEUE1') == 0xd2000
    assert owners['HCOMP_CGRAM_EVENT_QUEUE2'][1] == 0x400000
    for queue in (1, 2):
        start, end = owners[f'HCOMP_CGRAM_EVENT_QUEUE{queue}']
        assert start+((24576*4-1)&~7)+8 == end
    sections = list(allocated_sections(args.elf))
    for name, start, end in sections:
        owners['ELF:'+name] = (start, end)
    for first, last in (('HCOMP_CGRAM_BASE_QUEUE1','JIT_BUFFER'),
                        ('HCOMP_WINNER_ARENA','HCOMP_CGRAM_EVENT_QUEUE2')):
        start, end = value(first), value(last)
        assert start < end
        assert all(not (a < end and b > start) for _, a, b in sections), 'boot clear reaches linked code'
    low = prove(owners, 0x400000)
    _, symbols = load_elf(args.elf)
    assert symbols['renderer_cgram_owner_begin'] == value('HCOMP_CGRAM_BASE_QUEUE1')
    assert symbols['__bss_end'] <= 0x80000000+symbols['renderer_cgram_owner_begin']
    if 'profile_magic' in symbols:
        owners['profiler_guarded_lease'] = (0x448000, 0x44d000)
    if 'remote_boot_ram_bytes' in symbols:
        owners['USB_guarded_lease'] = (0x440000, 0x442000)
    prove(owners, 0x7f0000)
    rejected = []
    for name, extent in (('old_static_clear', (0xbe200, 0x1c0000)),
                         ('ROM_cache_into_surfaces', (value('ROM_BUFFER'), 0x386000)),
                         ('Q2_DMA_overrun', (value('HCOMP_CGRAM_EVENT_QUEUE2'), 0x400008))):
        changed = dict(owners)
        if name == 'ROM_cache_into_surfaces':
            changed['ROM_BUFFER'] = extent
        elif name == 'Q2_DMA_overrun':
            changed['HCOMP_CGRAM_EVENT_QUEUE2'] = extent
        else:
            changed[name] = extent
        try:
            prove(changed, 0x7f0000)
            if name == 'Q2_DMA_overrun':
                assert changed['HCOMP_CGRAM_EVENT_QUEUE2'][1] == 0x400000
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError(('owner fault escaped', name))
    report = {'passed': True, 'lower_owners_including_ELF': len(low),
        'total_owners_including_diagnostic_lease': len(owners),
        'first_CGRAM_owner': value('HCOMP_CGRAM_BASE_QUEUE1'),
        'faults_rejected': rejected, 'physical_acceptance': False,
        'scope': 'Preprocessed owner plan, real ELF extents and DMA bounds; boot and ISR execution are separate.',
        'owners': {name: list(extent) for name, extent in owners.items()}}
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: val for key, val in report.items() if key != 'owners'}))


if __name__ == '__main__':
    main()
