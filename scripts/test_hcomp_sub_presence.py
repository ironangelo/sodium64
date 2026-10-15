#!/usr/bin/env python3
"""Compiled general Sub/Main Z ownership, unchanged completion fence and bases.

Original geometry/control inputs only. Models RDP command adoption and bounded
busy status, not raster timing, native cadence or complete RDP pixel behavior.
"""
import argparse
import json
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_aligned_targets import execute

ROOT=Path(__file__).resolve().parents[1]

def section(path,name):
    data=path.read_bytes()
    assert data[:6]==b'\x7fELF\x01\x02'
    h=struct.unpack_from('>16sHHIIIIIHHHHHH',data)
    sec=[struct.unpack_from('>IIIIIIIIII',data,h[6]+i*h[11]) for i in range(h[12])]
    strings=sec[h[13]]
    names=data[strings[4]:strings[4]+strings[5]]
    for s in sec:
        if names[s[0]:].split(b'\0',1)[0].decode()==name:
            return data[s[4]:s[4]+s[5]]
    raise AssertionError('missing '+name)

def put(d,a,value):struct.pack_into('>I',d,a,value&0xffffffff)
def get(d,a):return struct.unpack_from('>I',d,a)[0]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('main',type=Path);ap.add_argument('phase',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    base,phase=read_text(a.phase);base&=0xfff
    ps={n:addr&0xfff for addr,n in elf_symbols(a.phase)}
    dmem=section(a.main,'.data');assert len(dmem)==4096 and len(phase)==1000
    ev=parse_macros(ROOT);addr=ev.name
    presence=addr('HCOMP_PRESENCE_ORIGIN')&0x1fffffff
    winner=addr('HCOMP_WINNER_ORIGIN')&0x1fffffff
    sub=addr('HCOMP_SUB_ORIGIN')&0x1fffffff
    proof=addr('HCOMP_PROOF_RDP_CMDS')
    assert ps['hcomp_screen_switch']==0x760 and ps['hcomp_copy_return']==0x770
    assert get(dmem,proof+16)==0x3e000000
    cases=fences=0
    for y in range(8,248):
     for rows in sorted({1,min(8,248-y),min(224,248-y),248-y}):
      for queue in (0,4):
       for ts in (0,1,16,31):
        d=bytearray(dmem)
        put(d,addr('FB_OFFSET')+queue,8)
        put(d,addr('FRAMEBUFFER')+queue,0xa00f4000)
        put(d,addr('HCOMP_BAND_RAW'),0)
        put(d,addr('HCOMP_OBJ_ADAPTIVE'),0)
        put(d,addr('HCOMP_DIAG_COMPOSE_LIMIT'),0)
        d[addr('TM')]=31;d[addr('HCOMP_EFFECTIVE_TS')]=ts;d[addr('STAT_FLAGS')]=0
        r=[0]*32;r[26]=y-8;r[27]=y-8+rows;r[29]=queue
        execute(phase,base,d,ps['hcomp_band_bounds_ready'],{ps['hcomp_band_targets_ready']},r)
        pad=(y*16)&63
        sub_z=presence-y*560-pad
        main_z=winner-y*560-pad
        assert get(d,proof+20)==sub_z and sub_z%64==main_z%64==0
        origins=[get(d,addr('HCOMP_BAND_BASES')+4*i)&0x1fffffff for i in range(3)]
        assert origins==[sub+24-pad,winner+24-pad,presence+24-pad]
        commands=[];complete=False;reads=0
        def send(mem,regs):
            nonlocal complete
            start,end=regs[4],regs[5]
            assert 0<=start<end<=4096 and start%8==end%8==0
            for offset in range(start,end,8):
                high,low=struct.unpack_from('>II',mem,offset)
                opcode=high>>24
                commands.append((opcode,low))
                if opcode==0x3e:
                    if low==main_z and ts:assert complete,'Main target changed before Sub retirement'
                    assert low in (sub_z,main_z)
        def status(register):
            nonlocal reads,complete
            assert register==11
            reads+=1
            complete=reads>=3
            return 0 if complete else 0x70
        hooks={0xf5c:send}
        # Compact begin establishes Sub PRESENCE; the TS=0 branch must still
        # switch to Main WINNER before its very first backdrop/color draw.
        execute(phase,base,d,ps['hcomp_compact_band'],{ps['hcomp_fill_target']},r,hooks=hooks)
        assert commands[2]==(0x3e,sub_z)
        if ts:
            assert get(d,proof+20)==sub_z and d[addr('HCOMP_SCREEN')]==0
            execute(phase,base,d,ps['hcomp_screen_end'],{ps['hcomp_fill_target']},r,hooks=hooks,cop0=status)
            assert reads==3 and any(op==0x29 for op,_ in commands)
            assert commands[-1]==(0x3e,main_z)
            fences+=1
        else:
            assert commands[-1]==(0x3e,main_z) and reads==0
        assert get(d,proof+20)==main_z and d[addr('HCOMP_SCREEN')]==1
        assert [low for opcode,low in commands if opcode==0x3e]==[sub_z,main_z]
        assert r[23]==31
        # Check framebuffer pixels against independent stride equations, not
        # just aligned base pointers, including borders and final short row.
        for row in (0,rows-1):
         for x in (0,12,139,267,279):
            assert sub_z+2*((y+row)*280+x)==origins[2]-24+2*(row*280+x)
            assert main_z+2*((y+row)*280+x)==origins[1]-24+2*(row*280+x)
        cases+=1
    # Raw/direct policies continue to bypass all general Z setup/transitions.
    bypass=0
    for policy in (1,2):
     for ts in (0,1,31):
        d=bytearray(dmem);put(d,addr('HCOMP_BAND_RAW'),policy)
        put(d,addr('FRAMEBUFFER'),0xa00f4000)
        d[addr('TM')]=31;d[addr('HCOMP_EFFECTIVE_TS')]=ts
        r=[0]*32;commands=[]
        def raw_send(mem,regs):
            for offset in range(regs[4],regs[5],8):commands.append(get(mem,offset)>>24)
        execute(phase,base,d,ps['hcomp_dispatch_policy'],{ps['hcomp_fill_target']},r,hooks={0xf5c:raw_send})
        assert 0x3e not in commands
        bypass+=1
    report=dict(passed=True,geometry_transitions=cases,sub_fences=fences,
                raw_direct_bypasses=bypass,presence_copy_dma_calls=0,
                complete_rdp_pixels=False,native_timing_authority=False,private_inputs=False)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('HCOMP_SUB_PRESENCE_DATAFLOW PASS',json.dumps(report))

if __name__=='__main__':main()
