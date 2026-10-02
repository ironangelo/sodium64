#!/usr/bin/env python3
"""Original patterned Mode1 operands and an independent per-channel oracle."""
import random
from make_gate_c_hcomp_cgwsel_source import finalize_checksum, HOOK_OFFSET
from make_gate_c_hcomp_main_sub_lifetime import Assembler, lda_sta_abs

rng=random.Random(0x364)
PALETTE=[rng.randrange(0x8000) for _ in range(128)]
# Explicit endpoints expose packed-channel borrow and saturation errors.
PALETTE[1:4]=[0x7fff,0x0421,0x7c1f]
PALETTE[65:68]=[0,0x7fff,0x03e0]
MODES={'rgb-add':1,'rgb-half':0x41,'rgb-sub':0x81,'rgb-sub-half':0xc1,'rgb-main':0,'rgb-subscreen':0}


def build_rgb(case,base):
    rom=bytearray(base)
    for address,old,new in [(0x2105,0,1),(0x2131,0x41,MODES[case])]:
        pattern=bytes((0xa9,old,0x8d,address&255,address>>8))
        assert rom.count(pattern)==1
        at=rom.index(pattern);rom[at+1]=new
    if case=='rgb-subscreen':
        pattern=bytes((0xa9,1,0x8d,0x2c,0x21));assert rom.count(pattern)==1
        at=rom.index(pattern);rom[at+1]=2
    # Column palettes isolate channel math from vertical palette transitions.
    for map_at,sub in [(0x1000,False),(0x1800,True)]:
        data=b''.join(((x%16)|((4+x%4 if sub else x%4)<<10)).to_bytes(2,'little')
                      for y in range(32) for x in range(32))
        rom[map_at:map_at+len(data)]=data
    for tiles_at,sub in [(0x2000,False),(0x2400,True)]:
        data=bytearray()
        for tile in range(16):
            for y in range(8):
                indices=[1+((x*(2 if sub else 1)+tile+y)%3) for x in range(8)]
                data.extend(sum(((v>>p)&1)<<(7-x) for x,v in enumerate(indices)) for p in range(2))
            data.extend(bytes(16))
        rom[tiles_at:tiles_at+len(data)]=data
    rom[0x5000:0x5100]=b''.join(v.to_bytes(2,'little') for v in PALETTE)
    a=Assembler();lda_sta_abs(a,0,0x2121);a.emit(0xa2,0,0)
    a.label('palette');a.emit(0xbf,0,0xd0,0,0x8d,0x22,0x21,0xe8,0xe0,0,1)
    a.branch(0xd0,'palette');a.emit(0x60)
    body=a.finish();rom[0x300:0x300+len(body)]=body
    assert rom[HOOK_OFFSET]==0xa9
    rom[HOOK_OFFSET+10:HOOK_OFFSET+16]=bytes((0x20,0,0x83,0x60,0xea,0xea))
    rom[0x7fc0:0x7fd5]=('S64 '+case).encode().ljust(21,b' ')
    finalize_checksum(rom);return bytes(rom)


def expected_rgb(case,x,y):
    # Visible SNES line starts at BGVOFS+1 in the retained renderer contract.
    row=(y+1)//8;line=(y+1)%8;column=x//8;pixel=x%8;tile=column%16
    main=PALETTE[(column%4)*16+1+(pixel+tile+line)%3]
    sub=PALETTE[(4+column%4)*16+1+(pixel*2+tile+line)%3]
    if case in ('rgb-main','rgb-subscreen'):
        raw=main if case=='rgb-main' else sub
        return ((raw&31)<<11)|(((raw>>5)&31)<<6)|(((raw>>10)&31)<<1)|1
    out=[]
    for shift in (0,5,10):
        a=(main>>shift)&31;b=(sub>>shift)&31
        if 'sub' in case:v=max(0,a-b)
        else:v=a+b
        if case in ('rgb-half','rgb-sub-half'):v//=2
        out.append(min(v,31))
    return (out[0]<<11)|(out[1]<<6)|(out[2]<<1)|1
