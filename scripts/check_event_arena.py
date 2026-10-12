#!/usr/bin/env python3
"""Prove complete simultaneous RDRAM owners, including four-byte event slots."""
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from check_runtime_arena import allocated_sections
from test_gate_c_cgram_rsp_consumer_clean_contract import MacroEval, parse_macros


def selected_macros(defines, diagnostic_trace=False, cc=None, profile=False, brr_observer=False, mix_observer=False, full_dsp_probe=False):
    if (brr_observer or mix_observer or full_dsp_probe) and not diagnostic_trace:
        raise ValueError('extended observer arena requires --diagnostic-trace')
    if not diagnostic_trace and not profile:
        # Preserve the original normal-profile check and its dependency-free API.
        return parse_macros(Path(defines).resolve().parents[1])
    compiler = cc or os.environ.get('N64_CC') or shutil.which('mips64-elf-gcc')
    if not compiler:
        root = os.environ.get('N64_INST') or ('C:/n64-toolchain' if os.name=='nt' else None)
        candidate = Path(root)/'bin'/('mips64-elf-gcc.exe' if os.name=='nt' else 'mips64-elf-gcc') if root else None
        if candidate and candidate.is_file():compiler = str(candidate)
    if not compiler:
        # Host CI runs before libdragon installs an N64 SDK. These owners are
        # integer preprocessor expressions, independent of MIPS aliases.
        compiler = shutil.which('gcc') or shutil.which('clang') or shutil.which('cc')
    if not compiler:raise ValueError('arena selection requires an available C preprocessor')
    include = Path(compiler).resolve().parents[1]/'mips64-elf/include'
    selected = []
    if diagnostic_trace: selected.append('-DSODIUM64_NATIVE_DIAG_TRACE=1')
    if profile: selected.append('-DSODIUM64_PROFILE=1')
    if brr_observer: selected.append('-DSODIUM64_BRR_OBSERVER=1')
    if mix_observer: selected.append('-DSODIUM64_MIX_OBSERVER=1')
    if full_dsp_probe: selected.append('-DSODIUM64_FULL_DSP_PROBE=1')
    command=[compiler, '-E', '-dM', '-x', 'assembler-with-cpp', *selected]
    source=None
    if 'mips' in Path(compiler).name and (include/'regdef.h').is_file():
        command+=['-I',str(include),str(Path(defines).resolve())]
    else:
        source=Path(defines).read_text()
        includes=re.findall(r'^\s*#\s*include[^\n]*',source,re.M)
        if [line.strip() for line in includes]!=['#include <regdef.h>']:
            raise ValueError('host arena preprocessing permits only the MIPS regdef.h alias include')
        source=re.sub(r'^\s*#\s*include\s+<regdef\.h>[^\n]*','',source,count=1,flags=re.M)
        command+=['-']
    result = subprocess.run(command,input=source,check=True,capture_output=True,text=True)
    macros = dict(re.findall(r'^#define ([A-Za-z_][A-Za-z_0-9]*) (.+)$', result.stdout, re.M))
    if diagnostic_trace: assert 'SODIUM64_NATIVE_DIAG_TRACE' in macros
    if profile: assert 'SODIUM64_PROFILE' in macros
    return MacroEval(macros)


def layout(defines, diagnostic_trace=False, cc=None, profile=False, brr_observer=False, mix_observer=False, full_dsp_probe=False):
    ev = selected_macros(defines, diagnostic_trace, cc, profile, brr_observer, mix_observer, full_dsp_probe)
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
    for name, owner in [('main_winner','HCOMP_WINNER_ARENA'),
                        ('sub_color','HCOMP_SUB_ARENA'),
                        ('preserved_ts','HCOMP_PRESENCE_ARENA')]:
        start=value(owner)
        owners[name]=(start,start+ev.name('HCOMP_SURFACE_BYTES'))
    for queue in (1,2):
        name=f'HCOMP_ROW_FIXED_QUEUE{queue}'
        start=value(name);owners[name]=(start,start+512)
    owners['consumed_section']=(0xf0000,0xf0010)
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
    assert ev.name('ROM_CACHE_SLOTS') == 194
    assert value('ROM_CACHE_END') == value('HCOMP_WINNER_ARENA') == 0x384000
    assert owners['HCOMP_CGRAM_EVENT_QUEUE2'][1] == 0x400000
    assert owners['HCOMP_CGRAM_EVENT_QUEUE1'][1] == value('HCOMP_CGRAM_BASE_QUEUE1') + 0x18e00
    if full_dsp_probe:
        assert value('HCOMP_CGRAM_BASE_QUEUE1') == 0xd6000
        assert value('HCOMP_RAW_PALETTE_QUEUE1')-owners['HCOMP_CGRAM_EVENT_QUEUE1'][1] == 0x200
    elif brr_observer or mix_observer:
        assert value('HCOMP_CGRAM_BASE_QUEUE1') == 0xd4000
    elif not diagnostic_trace and not profile:
        assert value('HCOMP_CGRAM_BASE_QUEUE1') == 0xc2000
    else:
        assert value('HCOMP_CGRAM_BASE_QUEUE1') == 0xd2000
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


def check(defines, elf=None, diagnostic_trace=False, cc=None, profile=False, brr_observer=False, mix_observer=False, full_dsp_probe=False):
    owners = layout(defines, diagnostic_trace, cc, profile, brr_observer, mix_observer, full_dsp_probe)
    if elf:
        sections=list(allocated_sections(elf))
        for name, a, b in sections:
            owners['ELF:' + name] = (a, b)
        # Boot clearing itself is a write owner, sharing only the fixed lower
        # renderer region. It must never touch loaded runtime/JIT/ROM pages.
        ev = selected_macros(defines, diagnostic_trace, cc, profile, brr_observer, mix_observer, full_dsp_probe)
        clear_ranges=[('clear_vram','HCOMP_CGRAM_BASE_QUEUE1','JIT_BUFFER'),
                      ('clear_hcomp_surfaces','HCOMP_WINNER_ARENA','HCOMP_CGRAM_EVENT_QUEUE2')]
        for clear, first, last in clear_ranges:
            lo=ev.name(first)&0x1fffffff;hi=ev.name(last)&0x1fffffff
            assert lo<hi, (clear,'invalid clear extent')
            for name, a, b in sections:
                assert not (a < hi and b > lo), (name, clear, 'boot clear overlap')
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
    ap.add_argument('--diagnostic-trace', action='store_true',
                    help='preprocess the actual trace CPU/RSP layout, including conditional arenas')
    ap.add_argument('--cc', help='N64 or host C preprocessor for conditional arena selection')
    ap.add_argument('--profile', action='store_true')
    ap.add_argument('--brr-observer', action='store_true')
    ap.add_argument('--mix-observer', action='store_true')
    ap.add_argument('--full-dsp-probe', action='store_true')
    args = ap.parse_args()
    result = check(args.defines, args.elf, args.diagnostic_trace, args.cc, args.profile, args.brr_observer, args.mix_observer, args.full_dsp_probe)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('EVENT_ARENA_FULL_EXTENTS PASS', len(result), 'owners; cap=24576; ROM slots=194',
          'profile=trace' if args.diagnostic_trace else ('profile=sampler' if args.profile else 'profile=normal'))

