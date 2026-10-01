#!/usr/bin/env python3
"""Small original full-height/short-section/OBJ/SRAM guests; no commercial data."""
import argparse
from pathlib import Path
from make_gate_c_hcomp_transparent_sub import build_mode
from make_gate_c_hcomp_cgwsel_source import hits, finalize_checksum, HOOK_OFFSET
from make_gate_c_hcomp_main_sub_lifetime import Assembler, lda_sta_abs, dma_to_vram
from make_gate_c_hcomp_color_window import build_case, WINDOW_HOOK_OFFSET

CASES = ('half', 'add', 'sub', 'sub-half', 'bg2', 'window', 'short',
         'blank', 'obj-low', 'obj-high', 'sram')


def set_store(rom, address, old, new, count=1):
    pattern = bytes((0xa9, old, 0x8d, address & 255, address >> 8))
    locations = hits(rom, pattern)
    assert len(locations) == count, (hex(address), locations)
    for i in locations: rom[i+1] = new


def hook_call(rom, address, body):
    offset = address-0x8000
    assert offset >= 0x240 and offset+len(body) < 0x1000
    rom[offset:offset+len(body)] = body
    # Existing source hook becomes a call to the original fixed/CGWSEL setup
    # plus the requested setup. The caller and frozen NMI address are retained.
    assert rom[HOOK_OFFSET] == 0xa9
    rom[HOOK_OFFSET+10:HOOK_OFFSET+16] = bytes((0x20,address&255,address>>8,0x60,0xea,0xea))


def build(case):
    rom = bytearray(build_case('both-inside') if case == 'window' else build_mode('sub-present-half'))
    if case not in ('short', 'blank'):
        set_store(rom, 0x420c, 1, 0)
    if case in ('add', 'sub', 'sub-half'):
        set_store(rom, 0x2131, 0x41, {'add':1,'sub':0x81,'sub-half':0xc1}[case])
    if case == 'bg2':
        set_store(rom, 0x212c, 1, 2)
        set_store(rom, 0x212d, 2, 1, count=2)
        set_store(rom, 0x2131, 0x41, 0x42)
    if case == 'window':
        # W1[32,95] XOR W2[64,191]; both clip/prevent inside selected pixels.
        settings = ((0xa2,0x2130),(0x9f,0x2132),(0xa0,0x2125),
                    (32,0x2126),(95,0x2127),(64,0x2128),(191,0x2129),(8,0x212b))
        body = bytes(v for value,address in settings for v in (0xa9,value,0x8d,address&255,address>>8))+b'\x60'
        rom[WINDOW_HOOK_OFFSET:WINDOW_HOOK_OFFSET+len(body)] = body
    if case in ('short','blank'):
        # Non-multiples of8, including a2-row section; state changes only through HDMA.
        rows = [2 if y < 5 or 13 <= y < 37 or y >= 39 else 0 for y in range(224)]
        if case == 'blank':
            rows = [0x80 if 13 <= y < 37 else 0x0f for y in range(224)]
            set_store(rom, 0x4301, 0x2d, 0)
            # NMI restore affects INIDISP instead of TS, retaining stable startup geometry.
            matches = hits(rom, bytes((0xa9,2,0x8d,0x2d,0x21)))
            assert len(matches) == 2
            i=matches[1];rom[i:i+5]=bytes((0xa9,0x0f,0x8d,0,0x21))
        table=bytearray()
        for at in range(0,224,127):
            part=rows[at:at+127];table.append(0x80|len(part));table.extend(part)
        table.append(0);rom[0x3000:0x3000+len(table)]=table
    if case in ('obj-low','obj-high'):
        a=Assembler()
        # Hide128objects first; one opaque8x8sprite atx32,y17 then overlays BG1.
        for address,value in ((0x2102,0),(0x2103,0)):
            lda_sta_abs(a,value,address)
        a.emit(0xa2,0x80,0)
        a.label('hide')
        for value in (0,0xf0,0,0):lda_sta_abs(a,value,0x2104)
        a.emit(0xca);a.branch(0xd0,'hide')
        lda_sta_abs(a,0,0x2102);lda_sta_abs(a,0,0x2103)
        for value in (32,17,0,0x30 if case=='obj-low' else 0x38):lda_sta_abs(a,value,0x2104)
        lda_sta_abs(a,3,0x2101) # OBJ char base$6000 words, outside BG character sets.
        lda_sta_abs(a,0x81 if case=='obj-low' else 0xc1,0x2121)
        for value in (0,0x7c):lda_sta_abs(a,value,0x2122) # opaque blue OBJ
        dma_to_vram(a,source=0xc800,vram_word=0x6000,length=32)
        lda_sta_abs(a,0x11,0x212c);lda_sta_abs(a,0x51,0x2131)
        a.emit(0x60);hook_call(rom,0x8300,a.finish())
        rom[0x4800:0x4820]=bytes((0xff,0))*8+bytes(16)
    if case == 'sram':
        rom[0x7fd6]=2;rom[0x7fd8]=5
        a=Assembler()
        # Echo the imported byte into a different SRAM address. The ordinary
        # PI save provides coherent first-hand load+write evidence, avoiding
        # a debugger read of CPU-private cached WRAM as acceptance authority.
        a.emit(0xaf,0x10,0,0x70,0x8f,0x08,0,0x70)
        for index,value in enumerate(b'S64GAME!'):
            a.emit(0xa9,value,0x8f,index,0,0x70)
        a.emit(0x60);hook_call(rom,0x8300,a.finish())
    rom[0x7fc0:0x7fd5]=('S64 FULL '+case).encode().ljust(21,b' ')
    finalize_checksum(rom)
    return bytes(rom)


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case',choices=CASES,required=True)
    ap.add_argument('output',type=Path)
    args=ap.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(build(args.case))
