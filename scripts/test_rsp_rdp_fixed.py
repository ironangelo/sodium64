#!/usr/bin/env python3
"""Linked fixed RDP admission, window scissors, ownership and restoration.

Numeric inputs only. RDP equations are checked independently in RGB5; this
does not emulate performance or replace real-console pixel readback.
"""
import argparse
import json
import random
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_packed_math import reference, rgba
from test_hcomp_sub_presence import section
from test_native_diag_arm import load_elf, execute as cpu_execute
from test_rsp_math_dma import ROOT, put
from test_rsp_rdp_half import ReturnVM

RDP, FALLBACK, PHASE = 0x190000, 0x1a0000, 0x180000


def channel(a,b,subtract):
    # RDP's unusual signed extension/clamp matches the primary combiner
    # implementation, and was independently measured by fixed-ENV probe7.
    def ext(v):return v-512 if v&0x180==0x180 else v
    def clamp(v):return v&255 if v>>7<2 else 255 if v>>7==2 else 0
    tex=(a<<3)|(a>>2);env=b<<3
    value=((((tex-env if subtract else tex)*255)+((0 if subtract else env)<<8)+128)>>8)&511
    value=((ext(value)*256+128)>>8)&511
    return clamp(value)>>3


def binding(cpu):
    image,s = load_elf(cpu);original=image.copy()
    addr=parse_macros(ROOT).name
    r=[0]*32;r[8]=s['rsp_hcomp_math_text_start']|5
    cpu_execute(image,s['hcomp_fixed_window_cpu_bind'],r,{},s['hcomp_rdp_cpu_bind_end'])
    def read(a):return int.from_bytes(bytes(image[(a+i)&0x1fffffff] for i in range(4)),'big')
    owned=set()
    for bank,prior in (('fixed_window','math'),('rdp_fixed','fixed_window'),('rdp','rdp_fixed')):
        text,data=[s['rsp_hcomp_'+bank+'_'+k+'_start'] for k in ('text','data')]
        assert data-text==1000
        assert read(data)==s['rsp_hcomp_'+prior+'_text_start']|5
        owned.update(range(data&0x1fffffff,(data&0x1fffffff)+4))
    assert s['rsp_hcomp_rdp_fixed_data_end']-s['rsp_hcomp_rdp_fixed_data_start']==168
    assert r[9]&0xe0000000==0xa0000000
    top=(0xa4000000+addr('OVERLAY_HCOMP_MATH_SRC'))&0x1fffffff
    assert read(top)==s['rsp_hcomp_rdp_text_start']|5
    owned.update(range(top,top+4))
    assert all(image[k]==v for k,v in original.items() if k not in owned)
    return 'rdp_half,rdp_fixed,fixed_window,original_math'


def run(build,c,number,fault=False):
    addr=parse_macros(ROOT).name
    _,maincode=read_text(build/'src/rsp_main.elf')
    _,rdpcode=read_text(build/'src/rsp_hcomp_rdp_fixed.elf')
    _,fallback=read_text(build/'src/rsp_hcomp_fixed_window.elf')
    _,phase=read_text(build/'src/rsp_hcomp.elf')
    data=section(build/'src/rsp_hcomp_rdp_fixed.elf','.data')
    assert len(rdpcode)==1000 and len(data)==168
    rows,y,cgws,cad,ts,limit=[c.get(k,v) for k,v in
                            (('rows',33),('y',9),('cgws',0x10),('cad',0xa3),('ts',0),('limit',0))]
    fixed=c.get('fixed',(5,5,5));mask=c.get('mask','spans')
    admitted=(not cgws&0xc1 and not cad&0x40 and cgws&0xf2 and
              not (cgws&2 and ts) and not limit and max(fixed)<=16)
    queue=(number&1)*4;framebuffer=0xf2300
    main=framebuffer+(y-8)*560+24
    zbase=(addr('HCOMP_WINNER_ORIGIN')&0x1fffffff)-(y*560+(y*16&63))
    winner=zbase+y*560+24
    d=bytearray(section(build/'src/rsp_main.elf','.data'))
    rng=random.Random(0x524650+number)
    masks=[0xffff if (mask=='all' or mask=='spans' and (x in (0,255) or 17<=x<94 or 128<=x<196) or
                     mask=='random' and rng.randrange(2)) else 0 for x in range(256)]
    for x,m in enumerate(masks):struct.pack_into('>H',d,addr('TILE_TABLE')+512+x*2,m)
    put(d,addr('FRAMEBUFFER')+queue,framebuffer)
    put(d,addr('HCOMP_PROOF_RDP_CMDS')+20,zbase)
    put(d,addr('HCOMP_BAND_Y'),y);put(d,addr('HCOMP_BAND_ROWS'),rows)
    put(d,addr('HCOMP_DIAG_COMPOSE_LIMIT'),limit)
    put(d,addr('OVERLAY_HCOMP_SRC'),PHASE|3)
    put(d,addr('OVERLAY_HCOMP_MATH_SRC'),0x1b0000|5)
    d[addr('HCOMP_EFFECTIVE_TS')]=ts
    struct.pack_into('>H',d,addr('SUB_COLOR'),fixed[0]<<11|fixed[1]<<6|fixed[2]<<1)
    ram=bytearray([0xa5])*0x400000
    ram[RDP:RDP+1000]=rdpcode
    struct.pack_into('>II',ram,RDP+1000,FALLBACK|5,0)
    ram[RDP+1008:RDP+1168]=data[8:]
    ram[FALLBACK:FALLBACK+1000]=fallback;ram[PHASE:PHASE+1000]=phase
    expected=[];initial=[]
    for row in range(rows):
        line=[];original=[]
        for x in range(256):
            a=rng.randrange(32768);tag=0xc00 if (x+row)%3 else 0x400
            struct.pack_into('>H',ram,main+row*560+x*2,rgba(a))
            struct.pack_into('>H',ram,winner+row*560+x*2,tag)
            original.append(rgba(a))
            operand=(fixed[0]<<10)|(fixed[1]<<5)|fixed[2]
            line.append(reference(a,operand,bool(cad&0x80),False) if tag==0xc00 and masks[x] else rgba(a))
        expected.append(line);initial.append(original)
    before,dbefore=bytes(ram),bytes(d)
    regs=[0]*32;regs[2],regs[3],regs[5],regs[16],regs[26],regs[27],regs[29]=cgws,cad,RDP,main,y-8,y-8+rows,queue
    code=bytearray(maincode);code[0x3a8:0x790]=rdpcode
    if fault:
        from test_rsp_math_dma import symbols
        pc=symbols(build/'src/rsp_hcomp_rdp_fixed.elf')['hcomp_rdp_fixed_restore_wait']+8
        assert int.from_bytes(code[pc:pc+4],'big')>>26==5
        put(code,pc,0) # Must not enter Phase before the GPU source retires.
    owners=set(range(addr('TILE_TABLE'),addr('TILE_TABLE')+160))
    owners.update(range(addr('SCRN_DATA'),addr('SCRN_DATA')+8))
    owners.update(range(addr('NATIVE_DIAG_RSP_BANK'),addr('NATIVE_DIAG_RSP_BANK')+2))
    class FencedVM(ReturnVM):
        def queue_dma(self,write,length):
            if self.spaddr&0x1000 and self.ramaddr&0x1fffffff==PHASE:
                assert self.lease is None,'GPU source not retired before Phase'
            return super().queue_dma(write,length)
    vm=FencedVM(code,d,ram,regs,owners,set(),number%7+7,
                overlays={FALLBACK:5,PHASE:3},stop_bank=3 if admitted else 5,
                lease=(main,main+rows*560) if admitted else None)
    vm.pc=0x3b0
    steps=vm.execute(0x778 if admitted else 0x3b0,require_phase=True)
    assert vm.r[26:28]==regs[26:28] and ram==before
    assert d[addr('TILE_TABLE')+512:addr('TILE_TABLE')+1024]==dbefore[addr('TILE_TABLE')+512:addr('TILE_TABLE')+1024]
    assert d[addr('VRAM_TABLE'):addr('SCRN_DATA')]==dbefore[addr('VRAM_TABLE'):addr('SCRN_DATA')]
    if not admitted:
        assert vm.overlay_history==[5] and vm.r[2:4]==[cgws,cad] and vm.r[16]==main
        assert not vm.captures
        return dict(admitted=False,policy=c)
    assert vm.overlay_history==[3] and vm.v[20]==[0]*8
    seen=set();output=[line[:] for line in initial]
    state=[0]*20;setups=sizes=tiles=0
    for packet in vm.captures[:-4]:
        if len(packet)==96:
            assert not setups and not sizes and not tiles
            state[:12]=struct.unpack('>12Q',packet);setups+=1
            continue
        if len(packet)==8:
            assert setups==1 and sizes<(rows+63)//64
            state[12]=struct.unpack('>Q',packet)[0];sizes+=1
            continue
        assert len(packet)==56 and setups==1 and sizes
        state[13:]=struct.unpack('>7Q',packet);tiles+=1
        # Reconstitute the same semantic command state used by the native v1
        # fixture; invariant state is established once, TileSize once per row.
        w=state[:11]+[state[13],state[14],state[15],state[11],state[12]]+state[16:]
        assert w[0]==w[13]==w[19]==0x2700000000000000
        assert w[1]==0x2f100cf000000214 and w[2]&0x1fffffff==framebuffer-4480
        assert w[3]==0x3a000000ffffffff
        assert w[4]==0x3b000000000000ff | (fixed[0]<<27) | (fixed[1]<<19) | (fixed[2]<<11)
        cc=w[5]
        assert ((cc>>52&15),(cc>>28&15),(cc>>47&31),(cc>>15&7))==(1,5 if cad&0x80 else 8,10,7 if cad&0x80 else 5)
        assert cc>>32&31==16 and cc>>6&7==0 and cc&7==6
        assert w[6]&0x1fffffff==zbase and w[7]==0x2e00000010000000
        assert w[8]==0x2800000000000000 and w[9]&0x1fffffff==main
        assert w[10]==0x3510100007080200 and w[11]==0x2600000000000000
        assert w[14]==0x3510100000080200
        assert w[18]==0x0000000004000400
        x0=(w[12]>>44&4095)//4;ly=(w[12]>>32&4095)//4
        x1=(w[12]>>12&4095)//4;ly1=(w[12]&4095)//4
        assert x0%32==0 and 0<=x0<=224 and x1==x0+31
        height=ly1-ly+1
        assert ly%64==0 and height==min(64,rows-ly) and height*32*2<=4096
        assert w[15]==0x320000000007c000 | ((height-1)*4)
        sx=(w[16]>>44&4095)//4-12;ex=(w[16]>>12&4095)//4-12
        assert 0<=sx<ex<=256 and ((w[16]>>32&4095)//4,w[16]&4095)==(y,(y+rows)*4)
        assert w[17]==(0x2400000000000000 | ((x0+44)*4<<44) |
                      ((y+ly+height)*4<<32) | ((x0+12)*4<<12) | ((y+ly)*4))
        for row in range(ly,ly+height):
            for x in range(max(sx,x0),min(ex,x0+32)):
                assert masks[x] and (row,x) not in seen
                seen.add((row,x))
                tag=struct.unpack_from('>H',before,winner+row*560+x*2)[0]
                if tag==0xc00:
                    a=initial[row][x]>>1
                    cs=[channel(a>>shift&31,f,bool(cad&0x80)) for shift,f in zip((10,5,0),fixed)]
                    output[row][x]=cs[0]<<11|cs[1]<<6|cs[2]<<1|1
    assert setups==1 and sizes==(rows+63)//64
    assert len(seen)==rows*sum(bool(m) for m in masks) and output==expected
    restore=[(addr('RDP_INIT'),addr('RDP_INIT')+64),
             (addr('RDP_FRAME')+8,addr('RDP_FILL')+8),
             (addr('RDP_FILL')+40,addr('RDP_FILL')+56),
             (addr('HCOMP_TEXTURE_FENCE'),addr('HCOMP_TEXTURE_FENCE')+8)]
    assert vm.captures[-4:]==[dbefore[a:b] for a,b in restore]
    assert len(vm.transfers)==2 and not any(t['write'] for t in vm.transfers)
    return dict(admitted=True,policy=c,pixels=rows*256,drawn_pixels=len(seen),tiles=tiles,
                setup_submissions=setups,size_submissions=sizes,
                rdp_commands=12+sizes+7*tiles+sum(len(p)//8 for p in vm.captures[-4:]),instructions=steps)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path)
    ap.add_argument('--cpu',required=True,type=Path);ap.add_argument('--baseline',required=True,type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    chain=binding(a.cpu)
    for name in ('rsp_main','rsp_hcomp','rsp_hcomp_math','rsp_hcomp_rdp','rsp_hcomp_fixed_window','rsp_hcomp_setup','rsp_hcomp_tlut'):
        assert read_text(a.build/'src'/f'{name}.elf')[1]==read_text(a.baseline/'src'/f'{name}.elf')[1],name
    for subtract in (False,True):
        for b in range(17):
            for x in range(32):assert channel(x,b,subtract)==(max(x-b,0) if subtract else min(x+b,31))
    cases=[dict(rows=r,mask=m,cad=c) for r,m in ((1,'spans'),(64,'spans'),(65,'spans'),(224,'all'),(33,'random'),(12,'none')) for c in (0x23,0xa3)]
    cases += [dict(fixed=f) for f in ((0,16,1),(16,16,16),(17,0,0),(0,17,0),(0,0,17),(31,31,31))]
    cases += [dict(cgws=w) for w in (0,1,0x41,0xc2,0x12,0x20,2)]
    cases += [dict(cad=0xe3),dict(cgws=0x12,ts=1),dict(limit=8)]
    results=[run(a.build,c,i) for i,c in enumerate(cases)]
    try:run(a.build,dict(rows=3),0,fault=True)
    except AssertionError as e:assert 'GPU source not retired before Phase' in str(e),str(e)
    else:raise AssertionError('Guard accepted premature GPU source reuse')
    r=dict(passed=True,cases=len(cases),pixels=sum(c.get('pixels',0) for c in results),
           cpu_binding=chain,old_banks_byte_exact=True,negative_guards=1,commercial_data=False,hardware_fps_claim=False,results=results)
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='results'}))


if __name__=='__main__':main()
