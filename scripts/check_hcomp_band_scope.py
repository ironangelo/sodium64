#!/usr/bin/env python3
"""Compiled memory/dispatch budget for the full-height fixed-slot HCOMP path."""
import argparse
from pathlib import Path
from capture_stage2_publication import load_symbols
from check_stage2_row_repair import elf_section
from check_event_arena import check


def validate(qualified):
    expected = dict(draw_bg=0xa40013a8, draw_mode7_entry=0xa4001788,
                    calc_window_spans=0xa4001ce4, dma_write=0xa4001f08,
                    dma_read=0xa4001f40, rdp_send=0xa4001f5c,
                    overlay_load_slot=0xa4001f7c, overlay_load_main=0xa4001f90)
    for variant in ('normal', 'hw-profile', 'color'):
        build = qualified/variant/'build'
        cpu = build/'sodium64.elf'
        check(Path('src/defines.h'), cpu)
        main, mode7 = [build/f'src/{name}.elf' for name in ('rsp_main','rsp_mode7')]
        for path in (main, mode7):
            base, text = elf_section(path, '.text')
            assert base == 0xa4001000 and len(text) == 4096
            symbols = load_symbols(path)
            assert all(symbols[n] == a for n, a in expected.items()), path
        _, regular = elf_section(main, '.text')
        _, rotated = elf_section(mode7, '.text')
        assert regular[0xce4:0xe8c] == rotated[0xce4:0xe8c]
        assert regular[0xf08:0xfac] == rotated[0xf08:0xfac]
        db, data = elf_section(main, '.data')
        assert db == 0xa4000000 and len(data) == 4096
        assert data[0xed8:0xee0] == bytes((32,1,2,4,8,0,16,0))
        assert data[0xee0:0xef0].hex() == '2e000000580000002e00000068000000'
        cs = load_symbols(cpu)
        cpu_db, cpu_data = elf_section(cpu, '.data')
        for name in ('rsp_hcomp', 'rsp_hcomp_math'):
            path = build/f'src/{name}.elf'
            base, text = elf_section(path, '.text')
            assert base == 0xa40013a8 and len(text) == 1000
            symbols = load_symbols(path)
            assert symbols['hcomp_entry'] == 0xa40013b0
            assert symbols['hcomp_screen_switch'] == 0xa4001760
            assert symbols['draw_mode7_entry'] == 0xa4001788
            offset = cs[name+'_text_start']-cpu_db
            assert cpu_data[offset:offset+1000] == text
        flags = [n for n in cs if n.startswith(('color_diag_', 'hw_profile_', 'profile_'))]
        if variant == 'normal':
            assert not flags, flags
        if variant == 'color':
            assert 'color_diag_init' in cs and 'hw_profile_done' in cs
    print('HCOMP_BAND_COMPILED_SCOPE PASS; IMEM4096, two1000B images, fixed ABI, 4MiB owners')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qualified', type=Path, required=True)
    args = ap.parse_args()
    validate(args.qualified)
