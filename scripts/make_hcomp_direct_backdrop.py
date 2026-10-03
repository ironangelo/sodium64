#!/usr/bin/env python3
"""Original direct-composition raster guests and independent pixel oracle."""
CASES = ('fast-always','fast-inside','fast-outside','fast-xor','fast-edge','fast-empty',
         'fast-invert','fast-sub-empty','fast-short','fast-iris-rows',
         'fast-identity-never','fast-identity-fixed-add','fast-identity-fixed-sub',
         'fast-identity-sub-empty-half','fast-identity-sub-empty-subhalf')

def identity_controls(case):
    return {'fast-identity-never':(0x32,0xff,2),
            'fast-identity-fixed-add':(0x10,0x3f,2),
            'fast-identity-fixed-sub':(0x20,0xbf,2),
            'fast-identity-sub-empty-half':(0x12,0x7f,0),
            'fast-identity-sub-empty-subhalf':(0x22,0xff,0)}[case]

def setup(case):
    selector,logic,bounds=2,0,(96,191,0,0)
    if case=='fast-xor':selector,logic,bounds=10,2,(32,95,64,191)
    if case=='fast-edge':bounds=(255,255,0,0)
    if case=='fast-empty':bounds=(200,100,0,0)
    if case=='fast-invert':selector=3
    return selector,logic,bounds

def build_direct(case):
    from make_hcomp_fullheight import build, set_store, hook_call
    from make_gate_c_hcomp_cgwsel_source import finalize_checksum
    rom=bytearray(build('short' if case=='fast-short' else 'half'))
    identity=case.startswith('fast-identity-')
    set_store(rom,0x2131,0x41,0x20)
    if case=='fast-sub-empty':set_store(rom,0x212d,2,0,count=2)
    selector,logic,bounds=setup(case)
    settings=((0,0x2121),(0,0x2122),(0,0x2122),
              (2 if case=='fast-always' else 0x22 if case=='fast-outside' else 0x12,0x2130),
              (selector<<4,0x2125),(logic<<2,0x212b),
              *((v,0x2126+i) for i,v in enumerate(bounds)))
    if identity:
        sel,cg,ts=identity_controls(case)
        # Nonzero Main backdrop and mixed opaque/transparent Main distinguish
        # identity from the black direct-backdrop specialization. Sub is green,
        # with zero fixed fallback; all eligible winner bits are enabled.
        settings=((sel,0x2130),(cg,0x2131),(ts,0x212d),(0xe0,0x2132),
                  (0,0x2121),(0x45,0x2122),(0x22,0x2122),
                  (selector<<4,0x2125),(logic<<2,0x212b),
                  *((v,0x2126+i) for i,v in enumerate(bounds)))
    body=bytes(v for value,address in settings for v in (0xa9,value,0x8d,address&255,address>>8))+b'\x60'
    hook_call(rom,0x8300,body)
    # Opaque red Main strip, with genuine transparent Main elsewhere. Green
    # Sub and fixed blue distinguish presence/fallback and window prevention.
    for tile in range(32):
        rom[0x2000+16*tile:0x2010+16*tile]=bytes((255 if tile<8 else 0,0))*8
    if case=='fast-iris-rows':
        # HDMA mode1 delivers both inclusive WH1 bounds every scanline.
        set_store(rom,0x4300,0,1)
        set_store(rom,0x4301,0x2d,0x26)
        set_store(rom,0x420c,0,1)
        table=bytearray()
        for first,count in ((0,127),(127,97)):
            table.append(0x80|count)
            for y in range(first,first+count):
                left=min(126,y//2);table.extend((left,255-left))
        table.append(0);rom[0x3000:0x3000+len(table)]=table
    rom[0x7fc0:0x7fd5]=('S64 '+case).encode()[:21].ljust(21,b' ')
    finalize_checksum(rom)
    return bytes(rom)

def expected_direct(case,x,y):
    if x<64:return 0xf801
    if case.startswith('fast-identity-'):
        # Main CGRAM color0 = 0x2245: independent SNES BGR555 -> RGBA5551.
        return (5<<11)|(18<<6)|(8<<1)|1
    selector,logic,(l1,r1,l2,r2)=setup(case)
    if case=='fast-iris-rows':l1=min(126,y//2);r1=255-l1
    one=(l1<=x<=r1) != bool(selector&1) if selector&2 else False
    two=(l2<=x<=r2) != bool(selector&4) if selector&8 else False
    if selector&10==10:
        selected=(one or two,one and two,one != two,one == two)[logic]
    else:selected=one if selector&2 else two if selector&8 else False
    allowed=not selected if case=='fast-outside' else selected
    if case!='fast-always' and not allowed:return 1
    present=case!='fast-sub-empty' and not (case=='fast-short' and (5<=y<13 or 37<=y<39))
    return 0x07c1 if present else 0x003f
