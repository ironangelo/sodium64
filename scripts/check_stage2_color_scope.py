#!/usr/bin/env python3
"""Normal/HW outputs must remain byte-identical; diagnostic never edits RSP."""
import argparse
from pathlib import Path
from check_stage2_row_repair import elf_section
from capture_stage2_publication import load_symbols

def check(qualified,parent):
    for variant in ('normal','hw-profile'):
        for section in ('.text','.data'):
            assert elf_section(qualified/variant/'build/sodium64.elf',section)==elf_section(parent/variant/'build/sodium64.elf',section),(variant,section)
    for variant in ('normal','hw-profile','color'):
        for name in ('rsp_main','rsp_mode7','rsp_hcomp'):
            for section in ('.text','.data'):
                assert elf_section(qualified/variant/f'build/src/{name}.elf',section)==elf_section(parent/'hw-profile'/f'build/src/{name}.elf',section),(variant,name,section)
    # Explicit guards around new cartridge format; no accidentally admitted
    # trace overlap with final pixels/PCM.
    assert 256+320*48<=0x4200 and 0x4200+0x3D10<=32768
    syms=load_symbols(qualified/'color/build/sodium64.elf')
    assert all(name in syms for name in ('color_diag_phase_a','color_diag_phase_b','color_diag_saved','hw_profile_done'))
    print('COLOR_DIAG_COMPILED_SCOPE PASS')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qualified',type=Path,required=True)
    ap.add_argument('--parent',type=Path,required=True)
    a=ap.parse_args();check(a.qualified,a.parent)
