#!/usr/bin/env python3
"""Compiled idempotent CGRAM writes and eight-lane math admission.

Device side effects and independent winner/window masks are the authorities.
No game bytes, guest timing changes or N64 throughput claims.
"""
import argparse,json,struct
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_v4 import execute as cpu_run
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols

EXIT=0xdead0000
def put(m,a,v,n=4):
    a&=0x1fffffff
    for i,b in enumerate((v&((1<<(8*n))-1)).to_bytes(n,'big')):m[a+i]=b
def get(m,a,n=4):
    a&=0x1fffffff
    return int.from_bytes(bytes(m.get(a+i,0) for i in range(n)),'big')

def gate(text,base,pc,exits,mask):
    r=[0]*32;pending=None;vcc=0
    for step in range(20):
        if pc in exits:return pc
        w=struct.unpack_from('>I',text,pc-base)[0]
        op=w>>26;rs=w>>21&31;rt=w>>16&31;imm=w&65535
        si=imm if imm<32768 else imm-65536;target=None
        if op==18 and rs&16:
            assert w&63==0x22 and w>>11&31==7 and rt==31,'expected VNE exact mask,zero'
            vcc=sum(int(lane!=0)<<i for i,lane in enumerate(mask))
        elif op==18 and rs==2:
            assert w>>11&31==1,'expected CFC2 VCC'
            r[rt]=vcc
        elif op==12:r[rt]=r[rs]&imm
        elif op==14:r[rt]=r[rs]^imm
        elif op==4:
            if r[rs]==r[rt]:target=pc+4+(si<<2)
        elif w==0:pass
        else:raise AssertionError(('unexpected gate instruction',hex(pc),hex(w)))
        assert pending is None or target is None
        pc=pending if pending is not None else pc+4;pending=target
    raise AssertionError('gate did not terminate')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cpu',type=Path);ap.add_argument('math_rsp',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    image,s=load_elf(a.cpu);same=0;changed=0
    for index in range(256):
      for value in (0,1,0x4210,0x7fff):
       for blank,done in ((0,0),(0x80,0),(0,1)):
        for equal in (False,True):
            m=image.copy();old=value if equal else value^31
            put(m,s['cgram']+2*index,old,2);put(m,s['cgadd'],2*index,2)
            put(m,s['dpal_dirty'],1,1);put(m,s['sect_status'],0xabcd,2)
            put(m,s['hvbjoy'],blank,1);put(m,s['frame_done'],done,1)
            put(m,s['hcomp_cgram_event_count'],2,2)
            cursor=0xa03e8000;put(m,s['hcomp_cgram_event_ptr'],cursor)
            put(m,cursor,0xdeadbeef);put(m,s['hcomp_cgram_event_overflow'],0,1)
            r=[0]*32;r[5]=value&255;r[31]=EXIT
            cpu_run(m,s['write_cgdata'],r,{},stop=EXIT)
            assert get(m,s['cgadd'],2)==2*index+1 and get(m,s['cg_lsb'],1)==value&255
            r=[0]*32;r[5]=value>>8;r[31]=EXIT
            # Distinct palette0 commits tail-call its ordinary fill update.
            # The changed producer is tested up to that existing continuation.
            stop=s['update_fill'] if index==0 and not equal else EXIT
            cpu_run(m,s['write_cgdata'],r,{},stop=stop)
            assert get(m,s['cgadd'],2)==2*index+2 and get(m,s['cgram']+2*index,2)==value
            active=not equal and not blank and not done
            assert get(m,s['dpal_dirty'],1)==(1 if equal else 3)
            assert get(m,s['hcomp_cgram_event_count'],2)==2+active
            assert get(m,s['hcomp_cgram_event_ptr'])==cursor+4*active
            assert get(m,s['sect_status'],2)==(0x100 if active else 0xabcd)
            raw=((value&31)<<11)|((value&0x3e0)<<1)|((value&0x7c00)>>9)|1
            assert get(m,cursor)==((raw<<16)|(index*8) if active else 0xdeadbeef)
            if equal:same+=1
            else:changed+=1
    base,text=read_text(a.math_rsp);base&=0xfff
    ms={n:addr&0xfff for addr,n in elf_symbols(a.math_rsp)}
    start=ms['hcomp_vector_math_test'];normal=ms['hcomp_vector_math_active'];skip=ms['hcomp_vector_output']
    masks=0
    for eligible in range(256):
      for allowed in (0,1,3,0x55,0xaa,0x80,0xff):
        mask=[0xffff if eligible&allowed&(1<<i) else 0 for i in range(8)]
        dest=gate(text,base,start,{normal,skip},mask)
        assert dest==(normal if eligible&allowed else skip),(eligible,allowed,dest)
        masks+=1
    report=dict(passed=True,identical_cgram_commits=same,changed_cgram_commits=changed,
                vector_winner_window_masks=masks,commercial_data=False,native_timing=False)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('REDUNDANT_WORK PASS',json.dumps(report))

if __name__=='__main__':main()
