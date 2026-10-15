"""Original solid affine guests isolate Mode7 windows, screens and raster cuts.

The 64KiB LoROM contains independently authored constant Mode7 graphics.
No commercial code, pixel data, saves or extracted state are used.
"""
CASES=('mode7-full','mode7-window','mode7-edge','mode7-empty','mode7-invert',
       'mode7-xor','mode7-unmasked','mode7-rotate','mode7-raster',
       'mode7-general-half','mode7-sub-window')
CASES += ('mode7-pattern','mode7-pattern-rotate','mode7-pattern-zoom')

def controls(case):
    cg=0x41 if case in ('mode7-general-half','mode7-sub-window') else 0x20
    sel=2 if case=='mode7-sub-window' else 0
    ts=1 if case=='mode7-sub-window' else 0
    return sel,cg,ts,1

def window(case,y):
    if case=='mode7-raster':
        return (2,0,(255,0,0,0)) if y<96 else (2,0,(48,207,0,0)) if y<160 else (2,0,(0,255,0,0))
    return {'mode7-full':(2,0,(0,255,0,0)),
            'mode7-edge':(2,0,(255,255,0,0)),
            'mode7-empty':(2,0,(200,100,0,0)),
            'mode7-invert':(3,0,(32,191,0,0)),
            'mode7-xor':(10,2,(32,95,64,191))}.get(case,(2,0,(32,191,0,0)))

def build_mode7(case):
    from make_hcomp_fullheight import build,set_store,hook_call
    from make_gate_c_hcomp_cgwsel_source import finalize_checksum
    rom=bytearray(build('half'))
    sel,cg,ts,tm=controls(case)
    set_store(rom,0x2131,0x41,cg)
    set_store(rom,0x212d,2,ts,count=2)
    selector,logic,bounds=window(case,0)
    settings=[(7,0x2105),(0,0x211a),(tm,0x212c),(sel,0x2130),
              (1,0x212f) if case=='mode7-sub-window' else (0,0x212f),
              (0 if case in ('mode7-unmasked','mode7-sub-window') else 1,0x212e),
              (selector,0x2123),(logic,0x212a),(0,0x2125),(0,0x212b),
              *((v,0x2126+i) for i,v in enumerate(bounds)),
              (0,0x2121),(0,0x2122),(0,0x2122),
              (1,0x2121),(31,0x2122),(0,0x2122),
              (2,0x2121),(0xe0,0x2122),(3,0x2122),
              (0x9f,0x2132)]
    matrix=(0,256,-256,0) if case in ('mode7-rotate','mode7-pattern-rotate') else (512,0,0,512) if case=='mode7-pattern-zoom' else (256,0,0,256)
    for address,value in zip(range(0x211b,0x211f),matrix):
        settings.extend(((value&255,address),(value>>8&255,address)))
    for address in (0x210d,0x210e,0x211f,0x2120):
        settings.extend(((0,address),(0,address)))
    # DMA bank01's original interleaved map/texel bytes into VRAM.
    settings.extend(((0x80,0x2115),(0,0x2116),(0,0x2117),(1,0x4300),
                     (0x18,0x4301),(0,0x4302),(0x80,0x4303),(1,0x4304),
                     (0,0x4305),(0x80,0x4306),(1,0x420b)))
    body=bytes(v for value,address in settings for v in (0xa9,value,0x8d,address&255,address>>8))+b'\x60'
    hook_call(rom,0x8300,body)
    if case=='mode7-raster':
        # Startup configures HDMA after the hook. Patch those actual later
        # writes so channel0 delivers paired WH1 bounds, rather than TS.
        set_store(rom,0x4300,0,1)
        set_store(rom,0x4301,0x2d,0x26)
        set_store(rom,0x420c,0,1)
        table=bytearray()
        for first,count in ((0,127),(127,97)):
            table.append(0x80|count)
            for y in range(first,first+count):table.extend(window(case,y)[2][:2])
        table.append(0);rom[0x3000:0x3000+len(table)]=table
    rom.extend(bytes(v for pixel in range(16384) for v in (0,1+(pixel//8)%2 if case.startswith('mode7-pattern') else 1)))
    rom[0x7fd7]=6
    rom[0x7fc0:0x7fd5]=('S64 '+case).encode()[:21].ljust(21,b' ')
    finalize_checksum(rom)
    return bytes(rom)

def expected_mode7(case,x,y):
    selector,logic,(l1,r1,l2,r2)=window(case,y)
    one=(l1<=x<=r1)^bool(selector&1) if selector&2 else False
    two=(l2<=x<=r2)^bool(selector&4) if selector&8 else False
    selected=(one or two,one and two,one!=two,one==two)[logic] if selector&10==10 else one if selector&2 else two if selector&8 else False
    if case=='mode7-sub-window':return 0xf83f if selected else 0xf801
    visible=case=='mode7-unmasked' or not selected
    if case=='mode7-general-half':return 0x781f if visible else 1
    if case.startswith('mode7-pattern') and visible:
        row=-x if case=='mode7-pattern-rotate' else 2*(y+1) if case=='mode7-pattern-zoom' else y+1
        return 0x07c1 if row&1 else 0xf801
    return 0xf801 if visible else 0x003f
