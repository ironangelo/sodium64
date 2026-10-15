"""Original four-color 16x16 OBJs across short raster sections."""
CASES=tuple(f'obj-rows-{top}-{mirror}' for top in (0,31) for mirror in ('none','x','y','xy'))

def build_rows(case):
    from make_hcomp_fullheight import build,set_store,hook_call
    from make_gate_c_hcomp_cgwsel_source import finalize_checksum
    from make_gate_c_hcomp_main_sub_lifetime import Assembler,lda_sta_abs,dma_to_vram
    _,_,top,mirror=case.split('-');top=int(top)
    rom=bytearray(build('short'));set_store(rom,0x212c,1,0x11)
    a=Assembler()
    for address,value in ((0x2102,0),(0x2103,0)):lda_sta_abs(a,value,address)
    a.emit(0xa2,0x80,0);a.label('hide')
    for value in (0,240,0,0):lda_sta_abs(a,value,0x2104)
    a.emit(0xca);a.branch(0xd0,'hide')
    lda_sta_abs(a,0,0x2102);lda_sta_abs(a,0,0x2103)
    attr=0x30|(0x40 if 'x' in mirror else 0)|(0x80 if 'y' in mirror else 0)
    for value in (96,top,0,attr):lda_sta_abs(a,value,0x2104)
    lda_sta_abs(a,0,0x2102);lda_sta_abs(a,1,0x2103)
    for i in range(32):lda_sta_abs(a,2 if i==0 else 0,0x2104)
    lda_sta_abs(a,3,0x2101)
    lda_sta_abs(a,0x81,0x2121)
    for raw in (0x7c00,0x03e0,0x7c1f,0x03ff):
        for value in (raw&255,raw>>8):lda_sta_abs(a,value,0x2122)
    dma_to_vram(a,source=0xc800,vram_word=0x6000,length=18*32)
    a.emit(0x60);hook_call(rom,0x8300,a.finish())
    atlas=bytearray(18*32)
    for tile,index in ((0,1),(1,2),(16,3),(17,4)):
        for row in range(8):
            for plane in range(4):atlas[32*tile+16*(plane//2)+2*row+plane%2]=255 if index&(1<<plane) else 0
    rom[0x4800:0x4800+len(atlas)]=atlas
    rom[0x7fc0:0x7fd5]=('S64 '+case).encode()[:21].ljust(21,b' ')
    finalize_checksum(rom);return bytes(rom)

def expected_rows(case,x,y):
    _,_,top,mirror=case.split('-');top=int(top)
    if 96<=x<112 and top<=y<top+16:
        col=(x-96)//8;row=(y-top)//8
        if 'x' in mirror:col=1-col
        if 'y' in mirror:row=1-row
        return (0x003f,0x07c1,0xf83f,0xffc1)[2*row+col]
    return 0xf83f if 5<=y<13 or 37<=y<39 else 0x7bc1
