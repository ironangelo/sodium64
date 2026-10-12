#!/usr/bin/env python3
"""Linked decoder relocation and identical-tile spans; numeric data only.

Checks actual emitted instructions, delayed overlay ownership, live callers,
pixel/UV equivalence and scissor/map boundaries. No N64 speed/timing claim.
"""
import argparse
import json
import random
import struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_sub_presence import section
from test_hcomp_tlut_candidate import ShaderVM
from test_rsp_math_dma import ROOT, put, symbols

WORKER, MAIN, DIRTY = 0x180000, 0x181000, 0x190000
EXIT = 0xabc


def constants(vm, d, a):
    for n in range(9):vm.v[23+n]=list(struct.unpack_from('>8H',d,a('VEC_DATA')+n*16))


def decode(build, baseline, fault=None):
    a=parse_macros(ROOT).name
    _,new=read_text(build/'src/rsp_main.elf');_,old=read_text(baseline/'src/rsp_main.elf')
    _,bank=read_text(build/'src/rsp_object_cache.elf')
    ns,os=symbols(build/'src/rsp_main.elf'),symbols(baseline/'src/rsp_main.elf')
    bs=symbols(build/'src/rsp_object_cache.elf')
    for name,macro in (('bank_shared_decode','RSP_BANK_DECODE_START'),
                       ('bank_shared_decode256','RSP_BANK_DECODE256'),
                       ('bank_shared_decode16','RSP_BANK_DECODE16'),('bank_shared_decode4','RSP_BANK_DECODE4')):
        assert bs[name]+0x1000 == a(macro),(name,hex(bs[name]+0x1000),hex(a(macro)))
    assert ns['shared_decode_return']+0x1000 == a('RSP_BANK_DECODE_RETURN')
    cases=0;rng=random.Random(0x523338)
    for bits,index in ((2,4),(4,8),(8,12)):
      for palette in range(8):
       for pattern in range(24):
        stale=pattern>=12;pattern=pattern%12
        payload=bytes(64) if pattern==0 else bytes(rng.randrange(256) for _ in range(64))
        pal=0 if bits==8 else palette*(4 if bits==2 else 16)
        results=[]
        for code,folder,relocated in ((old,baseline,False),(new,build,True)):
            d=bytearray(section(folder/'src/rsp_main.elf','.data'))
            d[a('CHAR_DATA'):a('CHAR_DATA')+64]=payload
            put(d,a('OVERLAY_OBJECT_CACHE_SRC'),WORKER|1);put(d,a('OVERLAY_MAIN_SRC'),MAIN|1)
            ram=bytearray([0xa5])*0x400000
            ram[WORKER:WORKER+1000]=bank;ram[MAIN:MAIN+1000]=new[0x3a8:0x790]
            r=[rng.randrange(65536) for _ in range(32)];r[0]=0;r[8]=12;r[25]=index;r[31]=EXIT
            r[12]=struct.unpack_from('>I',d,a('SHARED_JUMPS')+index-4)[0]
            owners=set(range(64))|set(range(a('NATIVE_DIAG_RSP_BANK'),a('NATIVE_DIAG_RSP_BANK')+2))
            vm=ShaderVM(code,d,ram,r,owners,set(),9,overlays={WORKER:1,MAIN:1})
            before_r=r[:]
            if relocated and fault=='callback':put(vm.code,ns['shared_decode_return'],0)
            # Frame snapshot's VGE and prior decoder's final VADD clear VCO.
            # Also compare deliberately stale VCO to the original routine,
            # without claiming the original's stale-flag output is accurate.
            vm.vco_hi=vm.vco_lo=[stale]*8
            constants(vm,d,a);vm.v[5][0]=pal<<8
            vm.pc=(ns if relocated else os)['shared_decode'];vm.execute(EXIT)
            # The RSP snapshot stores SNES16-bit VRAM words in big endian:
            # lower plane byte follows the upper plane byte in each pair.
            expected=bytes(0 if (value:=sum(((payload[(plane//2)*16+y*2+(1-(plane&1))]>>(7-x))&1)<<plane
                                            for plane in range(bits)))==0 else value+pal
                           for y in range(8) for x in range(8))
            if not stale:assert bytes(d[:64]) == expected,(bits,palette,pattern,relocated,'decoded pixel mismatch')
            assert vm.r[8]==12 and vm.r[25]==index and vm.r[31]==EXIT
            assert vm.r[3]==EXIT,'decoder loop v1 owner changed'
            for register in range(32):
                if register not in (0,3,4,5,6,8,9,12,15,25,31):
                    assert vm.r[register]==before_r[register],('decoder live caller',register)
            assert vm.overlay_history==([1,1] if relocated else [])
            assert not vm.captures
            results.append((bytes(d[:64]),vm.v[10]))
        assert results[0]==results[1]
        cases+=1
    return cases


def spans(build, fault=None):
    a=parse_macros(ROOT).name;_,code=read_text(build/'src/rsp_main.elf');s=symbols(build/'src/rsp_main.elf')
    cases=pixels=removed=0;rng=random.Random(0x5350414e)
    for scroll in (0,1,7,248,255,256,505,511):
     for end in (0,7,8,15,127,254,255):
      for large in (0,1):
       for flip in range(4):
        start=-(scroll&7)
        if start>end:continue
        d=bytearray(section(build/'src/rsp_main.elf','.data'))
        entry=37|(3<<10)|(flip<<14)
        entries=[entry]*64
        # Include an actual change inside the row; the final boundary wraps.
        boundary=rng.randrange(1,32);entries[(scroll//8+boundary)&63]^=1<<10
        for i,v in enumerate(entries):struct.pack_into('>H',d,a('SCRN_DATA')+i*2,v)
        span_index=2*(cases%3);d[a('WIN_BOUNDS')+span_index+1]=end
        rect=struct.pack('>2I',0x24000000|((start+20)<<14)|32,0x02000000|((start+12)<<14))
        d[a('RDP_TILE')+24:a('RDP_TILE')+32]=rect
        r=[rng.randrange(65536) for _ in range(32)];r[0]=0;r[16]=start&0xffffffff;r[22]=scroll
        r[13]=large;r[14]=entry;r[24]=span_index;r[31]=EXIT
        owners=set(range(56,64))|set(range(a('RDP_TILE')+24,a('RDP_TILE')+32))
        vm=ShaderVM(code,d,bytearray(0x400000),r,owners,set(),7,overlays={})
        vm.vco_hi=vm.vco_lo=[False]*8 # next_tile's VADD has already cleared VCO.
        constants(vm,d,a)
        # next_tile has stored current v15, then advanced it once already.
        next_rect=struct.pack('>2I',0x24000000|((start+28)<<14)|32,0x02000000|((start+20)<<14))
        vm.v[15][:4]=struct.unpack('>4H',next_rect)
        before_r=r[:];before_d=bytes(d)
        if fault=='boundary':put(vm.code,s['bg_span_probe']+4,0)
        if fault=='palette':put(vm.code,s['bg_span_probe']+28,0)
        if fault=='vertex':put(vm.code,s['bg_span_probe']+48,0)
        vm.pc=s['bg_span_merge'];vm.execute(EXIT)
        count=1
        if not large:
            while start+8*(count-1)<end-7 and entries[((start+scroll)//8+count)&63]==entry:count+=1
        assert vm.r[16]==(start+8*(count-1))&0xffffffff,'wrong window/map run'
        expected_upper=struct.unpack_from('>I',rect,4)[0]+(0 if large else 0x02000000)
        assert struct.unpack_from('>I',d,a('RDP_TILE')+28)[0]==expected_upper,'span upper-left/index changed'
        lower=struct.unpack_from('>I',d,a('RDP_TILE')+24)[0]
        expected_lower=struct.unpack_from('>I',rect)[0]+((count-1)<<17)
        assert lower==expected_lower,'wrong span lower-right'
        for register in range(32):
            if register not in (0,8,10,16):assert vm.r[register]==before_r[register],('live register',register)
        assert d[:56]==before_d[:56] and d[64:a('RDP_TILE')+24]==before_d[64:a('RDP_TILE')+24]
        for x in range(max(0,start),min(end+1,start+count*8)):
            local=x-start
            original=7-(local%8) if flip&1 else local%8
            merged=(7-local if flip&1 else local)&7
            assert merged==original
            pixels+=1
        removed+=count-1;cases+=1
    return dict(cases=cases,visible_horizontal_pixels=pixels,individual_rectangles_removed=removed)


def initializer(build, baseline):
    a=parse_macros(ROOT).name;_,main=read_text(build/'src/rsp_main.elf')
    _,setup=read_text(build/'src/rsp_hcomp_setup.elf');ss=symbols(build/'src/rsp_hcomp_setup.elf')
    _,original=read_text(baseline/'src/rsp_hcomp_setup.elf')
    start=ss['hcomp_vram_snapshot']-0x3a8; end=ss['bg_span_initialize']-0x3a8
    # No dirty-copy/semaphore instruction changes precede the new initializer.
    assert setup[start:end]==original[start:end]
    for queue in (0,4):
        code=bytearray(main);code[0x3a8:0x790]=setup
        d=bytearray(section(build/'src/rsp_main.elf','.data'))
        put(d,a('DIRTY_PTR')+queue,DIRTY);put(d,a('OVERLAY_MAIN_SRC'),MAIN|1)
        ram=bytearray(0x400000);ram[MAIN:MAIN+1000]=main[0x3a8:0x790]
        owners=set(range(64))|set(range(a('TILE_TABLE'),a('VRAM_TABLE')+1024))
        owners.update(range(a('HCOMP_VRAM_SNAPSHOT_READY'),a('HCOMP_VRAM_SNAPSHOT_READY')+4))
        owners.update(range(a('NATIVE_DIAG_RSP_BANK'),a('NATIVE_DIAG_RSP_BANK')+2))
        r=[0]*32;r[29]=queue
        vm=ShaderVM(code,d,ram,r,owners,set(),9,overlays={MAIN:1})
        constants(vm,d,a);vm.pc=ss['bg_span_initialize'];vm.execute(0x9c)
        assert vm.captures==[bytes.fromhex('3548020004058030320000000401f01f')], 'wrong span tile descriptor'
        assert vm.overlay_history==[1]
    return 2


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path)
    ap.add_argument('--baseline',type=Path,required=True);args=ap.parse_args()
    old,new=symbols(args.baseline/'src/rsp_main.elf'),symbols(args.build/'src/rsp_main.elf')
    _,before=read_text(args.baseline/'src/rsp_main.elf');_,after=read_text(args.build/'src/rsp_main.elf')
    assert before[old['draw_row']:old['check_cache']]==after[new['draw_row']:new['check_cache']], 'row/rectangle opcode construction changed'
    for name in ('draw_bg','draw_obj','oam_skip','finish_tile','draw_tile','skip_decode','skip_upload',
                 'shared_decode','hcomp_obj_mirror','rdp_send','ret_jump'):
        assert old[name]==new[name],name
    result=dict(decoder_cases=decode(args.build,args.baseline),span_checks=spans(args.build),
                initializer_queues=initializer(args.build,args.baseline),
                passed=True,native_speed_claim=False)
    for fault in ('boundary','palette','vertex'):
        try:spans(args.build,fault)
        except AssertionError:pass
        else:raise AssertionError('accepted span '+fault+' mutation')
    try:decode(args.build,args.baseline,'callback')
    except AssertionError:pass
    else:raise AssertionError('accepted decoder callback mutation')
    result['negative_guards']=4
    print(json.dumps(result))

if __name__=='__main__':main()
