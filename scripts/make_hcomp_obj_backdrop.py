#!/usr/bin/env python3
"""Original Mode0/OBJ backdrop guests; no commercial state or graphics."""
CASES=('fast-mode0-bit','fast-obj-low','fast-obj-low-inside','fast-obj-low-outside',
       'fast-obj-above','fast-obj-disabled','fast-obj-high-visible','fast-obj-high-wrap',
       'fast-obj-high-late','fast-obj-high-multiple','fast-obj-sections')

def controls(case):
    return (0x13 if case=='fast-obj-low-inside' else 0x23 if case=='fast-obj-low-outside' else 3,
            0x20 if case=='fast-mode0-bit' else 0x30,2,
            1 if case in ('fast-mode0-bit','fast-obj-disabled') else 0x11)

def policy(case):return 0 if case=='fast-obj-high-late' else 2

def objects(case):
    # Tuples are original SNES X,Y,tile,attributes,large. Blue palette0 is
    # math-forbidden; blue palette4 must add the green Sub operand.
    low=(96,17,0,0x30,False)
    high=(96,17,0,0x38,False)
    if case=='fast-mode0-bit':return ()
    if case=='fast-obj-above':return (low,(112,240,0,0x38,True))
    if case=='fast-obj-disabled':return (high,)
    if case=='fast-obj-high-visible':return (high,)
    if case=='fast-obj-high-wrap':return ((96,252,0,0x38,False),)
    if case=='fast-obj-high-late':return ((96,220,0,0x38,False),)
    if case in ('fast-obj-high-multiple','fast-obj-sections'):
        return ((96,49,0,0x38,False),(96,114,0,0x38,False),(96,122,0,0x38,False))
    return (low,)

def build_obj(case):
    from make_hcomp_fullheight import build,set_store,hook_call
    from make_gate_c_hcomp_main_sub_lifetime import Assembler,lda_sta_abs,dma_to_vram
    from make_gate_c_hcomp_cgwsel_source import finalize_checksum
    rom=bytearray(build('half'));sel,cg,ts,tm=controls(case)
    set_store(rom,0x2131,0x41,cg);set_store(rom,0x212c,1,tm)
    a=Assembler()
    for address,value in ((0x2102,0),(0x2103,0)):lda_sta_abs(a,value,address)
    a.emit(0xa2,0x80,0);a.label('hide')
    for value in (0,240,0,0):lda_sta_abs(a,value,0x2104)
    a.emit(0xca);a.branch(0xd0,'hide')
    lda_sta_abs(a,0,0x2102);lda_sta_abs(a,0,0x2103)
    sprites=objects(case)
    for x,y,tile,attr,large in sprites:
        for value in (x,y,tile,attr):lda_sta_abs(a,value,0x2104)
    # Explicitly deliver every high OAM byte; no initial RAM assumption.
    lda_sta_abs(a,0,0x2102);lda_sta_abs(a,1,0x2103)
    high=bytearray(32)
    for index,(_,_,_,_,large) in enumerate(sprites):
        high[index//4]|=int(large)<<((index%4)*2+1)
    for value in high:lda_sta_abs(a,value,0x2104)
    lda_sta_abs(a,3,0x2101) # OBJ chars$6000 words, small8/large16.
    for palette in (0x81,0xc1):
        lda_sta_abs(a,palette,0x2121)
        for value in (0,0x7c):lda_sta_abs(a,value,0x2122)
    dma_to_vram(a,source=0xc800,vram_word=0x6000,length=32)
    settings=((0,0x2121),(0,0x2122),(0,0x2122),(sel,0x2130),
              (0x20,0x2125),(0,0x212b),(96,0x2126),(191,0x2127))
    for value,address in settings:lda_sta_abs(a,value,address)
    a.emit(0x60);hook_call(rom,0x8300,a.finish())
    rom[0x4800:0x4820]=bytes((255,0))*8+bytes(16)
    # Red opaque Main atx0..63, transparent Main over green Sub elsewhere.
    for tile in range(32):
        rom[0x2000+16*tile:0x2010+16*tile]=bytes((255 if tile<8 else 0,0))*8
    # Deliver an unchanged high-OAM byte each NMI, just as a normal sprite
    # upload does. This proves the tested cache was rebuilt with current
    # OBSEL/Y-wrap settings; the scalar suite separately rejects stale caches.
    # Keep the original NMI body, counter and vector at$8200 intact.
    end=rom.index(bytes((0x68,0x40)),0x200,0x240)
    rom[end:end+5]=bytes((0x20,0x00,0x86,0x68,0x40))
    refresh=Assembler()
    for value,address in ((0,0x2102),(1,0x2103),(high[0],0x2104)):
        lda_sta_abs(refresh,value,address)
    refresh.emit(0x60)
    rom[0x600:0x600+len(refresh.code)]=refresh.finish()
    if case=='fast-obj-sections':
        # Later HDMA epochs reuse OAM without another upload, changing TS
        # away and back at non-eight-row boundaries. Independent oracle below.
        set_store(rom,0x420c,0,1)
        table=bytes((40,2,17,0,127,2,40,2,0))
        rom[0x3000:0x3000+len(table)]=table
    rom[0x7fc0:0x7fd5]=('S64 '+case).encode()[:21].ljust(21,b' ')
    finalize_checksum(rom);assert len(rom)==32768
    return bytes(rom)

def expected_obj(case,x,y):
    # Independent palette eligibility and saturated component addition.
    # Palette0: blue remains blue; palette4: blue+green becomes cyan.
    if case not in ('fast-mode0-bit','fast-obj-disabled') and 96<=x<104:
        if case=='fast-obj-high-wrap':
            if 0<=y<4:return (31<<6)|(31<<1)|1
        elif case=='fast-obj-high-late' and 220<=y<224:return (31<<6)|(31<<1)|1
        elif case in ('fast-obj-high-multiple','fast-obj-sections') and (49<=y<57 or 114<=y<130):
            return (0 if case=='fast-obj-sections' and 40<=y<57 else 31<<6)|(31<<1)|1
        elif case not in ('fast-obj-high-late','fast-obj-high-multiple','fast-obj-sections') and 17<=y<25:
            return ((31<<6) if case=='fast-obj-high-visible' else 0)|(31<<1)|1
    if x<64:return (31<<11)|1
    selected=96<=x<=191
    allowed=selected if case=='fast-obj-low-inside' else not selected if case=='fast-obj-low-outside' else True
    if allowed and case=='fast-obj-sections' and 40<=y<57:
        return (31<<1)|1 # Absent Sub uses the explicitly delivered fixed blue.
    return (31<<6)|1 if allowed else 1
