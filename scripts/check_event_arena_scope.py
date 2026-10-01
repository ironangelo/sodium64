#!/usr/bin/env python3
"""Inspect emitted ROM wrap and preserve every RSP section/dispatch address."""
import argparse
import struct
from pathlib import Path
from check_stage2_row_repair import elf_section
from capture_stage2_publication import load_symbols
from check_event_arena import check


def scope(qualified, parent):
    for variant in ('normal', 'hw-profile', 'color'):
        cpu = qualified/variant/'build/sodium64.elf'
        check(Path('src/defines.h'), cpu)
        syms = load_symbols(cpu)
        base, code = elf_section(cpu, '.text')
        start = syms['tlbl_rom']-base
        end = syms['tlbl_io']-base
        words = struct.unpack('>'+str((end-start)//4)+'I', code[start:end])
        # li k1,243; bne k0,k1,+2; addi k1,k0,1 (delay); move k1,zero
        matches = [i for i in range(len(words)-3)
                   if words[i:i+3] == (0x241b00f3, 0x175b0002, 0x235b0001)]
        assert len(matches) == 1, (variant, 'emitted wrap', matches)
        i = matches[0]
        assert words[i+3] in (0x0000d821, 0x0000d825), hex(words[i+3])
        assert syms['rom_cache_advance'] == base+start+(i+4)*4
        for name in ('rsp_main', 'rsp_mode7', 'rsp_hcomp'):
            current = qualified/variant/f'build/src/{name}.elf'
            old = parent/variant/f'build/src/{name}.elf'
            for section in ('.text', '.data'):
                assert elf_section(current, section) == elf_section(old, section), (variant, name, section)
        _, data = elf_section(cpu, '.data')
        dbase, _ = elf_section(cpu, '.data')
        q2 = struct.unpack_from('>I', data, syms['hcomp_cgram_event_queues']-dbase+4)[0]
        assert q2 == 0xa03e8000, (variant, hex(q2))
    print('EVENT_ARENA_COMPILED_SCOPE PASS; unchanged all RSP sections; actual CPU wrap and Q2 pointer')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qualified', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    args = ap.parse_args()
    scope(args.qualified, args.parent)
