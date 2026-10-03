#!/usr/bin/env python3
"""Original patterned BG-window guests; no commercial content."""
from make_gate_c_hcomp_cgwsel_source import finalize_checksum
from make_gate_c_hcomp_main_sub_lifetime import Assembler, lda_sta_abs
from make_hcomp_color_grid import PALETTE, expected_rgb

CASES=('span-seek-narrow','span-seek-split','span-seek-scroll',
       'span-seek-raster','span-seek-math','span-seek-priority')

def bounds(case,y):
    if case=='span-seek-split': return 61,62,2
    if case=='span-seek-raster': return 93+y%32,100+y%32,3
    return 93,148,3

def build_seek(case):
    from make_hcomp_fullheight import build,set_store
    assert case in CASES
    rom=bytearray(build('rgb-add' if case=='span-seek-math' else 'rgb-main'))
    # Extend the existing original palette-load hook, preserving its loop.
    a=Assembler()
    l,r,selector=bounds(case,0)
    for address,value in ((0x2123,selector),(0x2126,l),(0x2127,r),
                          (0x212e,0),(0x212f,1)):
        lda_sta_abs(a,value,address)
    if case=='span-seek-scroll':
        lda_sta_abs(a,3,0x210d); lda_sta_abs(a,0,0x210d)
    a.emit(0x60)
    old=bytes((0xa2,0,0,0xbf,0,0xd0,0,0x8d,0x22,0x21,0xe8,0xe0,0,1))
    at=rom.find(old); assert 0x300<=at<0x380
    end=at+len(old)+2 # BNE back to palette loop, then RTS
    assert rom[end]==0x60
    body=a.finish(); assert end+len(body)<0x400
    rom[end:end+len(body)]=body
    if case=='span-seek-priority':
        for y in range(32):
            for x in range(32):
                at=0x1000+2*(y*32+x)
                entry=int.from_bytes(rom[at:at+2],'little') | ((x&1)<<13)
                rom[at:at+2]=entry.to_bytes(2,'little')
    if case=='span-seek-raster':
        # Configure the actual later startup stores, so they cannot undo
        # mode1's two-byte WH0/WH1 HDMA target after the palette hook runs.
        set_store(rom,0x4300,0,1); set_store(rom,0x4301,0x2d,0x26)
        set_store(rom,0x420c,0,1)
        table=bytearray()
        for at in range(0,224,127):
            rows=range(at,min(at+127,224)); table.append(0x80|len(rows))
            for y in rows: table.extend(bounds(case,y)[:2])
        table.append(0); rom[0x3000:0x3000+len(table)]=table
    rom[0x7fc0:0x7fd5]=('S64 '+case).encode()[:21].ljust(21,b' ')
    finalize_checksum(rom); return bytes(rom)

def expected_seek(case,x,y):
    l,r,selector=bounds(case,y)
    visible=(l<=x<=r) if selector==3 else not l<=x<=r
    if not visible:
        # The original patterned palette deliberately has nonzero entry0.
        # Backdrop is not math-eligible in these guests.
        raw=PALETTE[0]
        return ((raw&31)<<11)|(((raw>>5)&31)<<6)|(((raw>>10)&31)<<1)|1
    return expected_rgb('rgb-add' if case=='span-seek-math' else 'rgb-main',
                        x+(3 if case=='span-seek-scroll' else 0),y)
