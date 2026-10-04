#!/usr/bin/env python3
"""Small original full-height/short-section/OBJ/SRAM guests; no commercial data."""
import argparse
from pathlib import Path
from make_gate_c_hcomp_transparent_sub import build_mode
from make_gate_c_hcomp_cgwsel_source import hits, finalize_checksum, HOOK_OFFSET
from make_gate_c_hcomp_main_sub_lifetime import Assembler, lda_sta_abs, dma_to_vram
from make_gate_c_hcomp_color_window import build_case, WINDOW_HOOK_OFFSET

CASES = ('fixed-half-raster', 'half', 'add', 'sub', 'sub-half', 'bg2', 'bg3', 'bg4', 'window', 'short',
         'blank', 'obj-low', 'obj-high', 'sram', 'layer-window', 'layer-edge', 'layer-xor', 'rgb-add', 'rgb-half', 'rgb-sub', 'rgb-sub-half', 'rgb-main', 'rgb-subscreen', 'rgb-row-add', 'rgb-row-half', 'rgb-row-sub', 'rgb-row-sub-half', 'rgb-row-subscreen')
from make_hcomp_direct_backdrop import CASES as DIRECT_CASES
CASES += DIRECT_CASES
from make_hcomp_obj_backdrop import CASES as OBJ_BACKDROP_CASES
CASES += OBJ_BACKDROP_CASES
from make_mode7_windows import CASES as MODE7_CASES
CASES += MODE7_CASES
from make_bg_span_seek import CASES as BG_SEEK_CASES
CASES += BG_SEEK_CASES


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
    if case == 'fixed-half-raster':
        rom=bytearray(build('short'))
        set_store(rom,0x2130,2,0)
        set_store(rom,0x4301,0x2d,0x32)
        body=bytes((0xa9,0xe0,0x8d,0x32,0x21,0x60))
        hook_call(rom,0x8300,body)
        rows=[0x80|(y&31) for y in range(223)]+[0x80]
        table=bytearray()
        for at in range(0,224,127):
            part=rows[at:at+127];table.append(0x80|len(part));table.extend(part)
        table.append(0);rom[0x3000:0x3000+len(table)]=table
        rom[0x7fc0:0x7fd5]=b'S64 FIXED HALF RASTER'.ljust(21,b' ')
        finalize_checksum(rom)
        return bytes(rom)
    if case in BG_SEEK_CASES:
        from make_bg_span_seek import build_seek
        return build_seek(case)
    if case in MODE7_CASES:
        from make_mode7_windows import build_mode7
        return build_mode7(case)
    if case in OBJ_BACKDROP_CASES:
        from make_hcomp_obj_backdrop import build_obj
        return build_obj(case)
    if case in DIRECT_CASES:
        from make_hcomp_direct_backdrop import build_direct
        return build_direct(case)
    if case.startswith("rgb-"):
        from make_hcomp_color_grid import build_rgb
        return build_rgb(case,build("half"))
    rom = bytearray(build_case('both-inside') if case == 'window' else build_mode('sub-present-half'))
    if case not in ('short', 'blank'):
        set_store(rom, 0x420c, 1, 0)
    if case in ('add', 'sub', 'sub-half'):
        set_store(rom, 0x2131, 0x41, {'add':1,'sub':0x81,'sub-half':0xc1}[case])
    if case == 'bg2':
        set_store(rom, 0x212c, 1, 2)
        set_store(rom, 0x212d, 2, 1, count=2)
        set_store(rom, 0x2131, 0x41, 0x42)
    if case in ('bg3','bg4'):
        mask=4 if case=='bg3' else 8
        set_store(rom,0x212c,1,mask)
        set_store(rom,0x2131,0x41,0x40|mask)
        # Mode0 BG3/4 reuse BG1's opaque red map and character set, with
        # BG2 green still owning Sub. Only Main winner/eligible bit changes.
        # BG1 character base is$1000 words (BGNBA nibble1). Keep a
        # native Mode0 red entry as well as the inherited renderer's red1.
        palette=65 if case=='bg3' else 97
        settings=((0x11,0x210c),(palette,0x2121),(0x1f,0x2122),(0,0x2122))
        body=bytes(v for value,address in settings for v in (0xa9,value,0x8d,address&255,address>>8))+b'\x60'
        hook_call(rom,0x8300,body)
    if case == 'window':
        # W1[32,95] XOR W2[64,191]; both clip/prevent inside selected pixels.
        settings = ((0xa2,0x2130),(0x9f,0x2132),(0xa0,0x2125),
                    (32,0x2126),(95,0x2127),(64,0x2128),(191,0x2129),(8,0x212b))
        body = bytes(v for value,address in settings for v in (0xa9,value,0x8d,address&255,address>>8))+b'\x60'
        rom[WINDOW_HOOK_OFFSET:WINDOW_HOOK_OFFSET+len(body)] = body
    if case in ('layer-window', 'layer-edge', 'layer-xor', 'rgb-add', 'rgb-half', 'rgb-sub', 'rgb-sub-half'):
        # Original layer-window regression: the helper clobbers the caller's
        # t8 span index. BG1 must use its returned visible spans, not DMEM+256.
        left, right = (255, 255) if case == 'layer-edge' else (32, 191)
        selector = 0xa if case == 'layer-xor' else 3
        settings = ((selector,0x2123),(left,0x2126),(right,0x2127),
                    (64,0x2128),(127,0x2129),(2 if case=='layer-xor' else 0,0x212a),
                    (1,0x212e),(0,0x212f))
        body = bytes(v for value,address in settings for v in (0xa9,value,0x8d,address&255,address>>8))+b'\x60'
        hook_call(rom,0x8300,body)
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
        # The source hook runs before the final startup CGADSUB write; update
        # that actual write so it cannot overwrite OBJ eligibility with BG1 only.
        set_store(rom,0x2131,0x41,0x51)
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

