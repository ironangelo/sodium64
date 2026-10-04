#!/usr/bin/env python3
"""Execute compiled merge, branch and OBJ-row decisions with original states.

Expected values come from source-byte ownership and independent interval
intersection / 65C816 bank equations. No commercial game bytes or FPS claims.
"""
import argparse, json, random, struct
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_v4 import execute, sx
from test_hcomp_aligned_targets import execute as rsp_execute
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols

EXIT=0xdead0000

def put(m,address,value,size=4):
    address&=0x1fffffff
    for i,b in enumerate((value&((1<<(size*8))-1)).to_bytes(size,'big')):
        m[address+i]=b

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cpu',type=Path);ap.add_argument('main_rsp',type=Path);ap.add_argument('mode7_rsp',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    image,s=load_elf(a.cpu)
    rng=random.Random(0x6516);cases=dict(epoch=0,branches=0,obj_rows=0,apu_reset=0)
    # Execute the entire compiled JIT reset. Every lookup pointer is invalidated,
    # adjacent owners and scheduler registers survive, and compilation resumes.
    lookup=s['jit_lookup']&0x1fffffff;end=s['jit_pointer']&0x1fffffff
    assert end-lookup==0x40000 and lookup%8==0 and end%8==0
    m=image.copy()
    payload=bytes((i*43+7)&255 for i in range(end-lookup))
    m.update((lookup+i,b) for i,b in enumerate(payload))
    left=bytes((i*17+3)&255 for i in range(64));right=bytes((i*11+5)&255 for i in range(64))
    m.update((lookup-64+i,b) for i,b in enumerate(left))
    m.update((end+4+i,b) for i,b in enumerate(right));put(m,end,0x801dffe0)
    regs=[sx(0x12340000+i) for i in range(32)];regs[0]=0;before=regs.copy()
    steps=execute(m,s['reset_buffer'],regs,{},stop=s['compile_block'])
    assert bytes(m.get(lookup+i,0) for i in range(end-lookup))==bytes(end-lookup)
    assert bytes(m[lookup-64+i] for i in range(64))==left
    assert bytes(m[end+4+i] for i in range(64))==right
    assert int.from_bytes(bytes(m[end+i] for i in range(4)),'big')==0xa01c0000
    assert all(regs[i]==before[i] for i in set(range(32))-{8,9})
    assert steps<50000,('lookup reset instruction bound',steps)
    cases['apu_reset']+=1
    current=s['bghofs'];previous=0xa0140000
    # Stop before either path performs queue/OAM publication.
    for changed in [None,*range(64),'cgram','dirty','sub2','first','nonuniform','not_half']:
        m=image.copy();packet=bytearray(rng.randrange(256) for _ in range(64))
        packet[0x37]=0;packet[0x38]=0x42;packet[0x3e]=0
        old=bytearray(packet);old[0x3e]=0x40;old[0x3f]=37
        if isinstance(changed,int):packet[changed]^=1
        elif changed=='dirty':packet[0x3e]|=0x40
        elif changed=='sub2':packet[0x26:0x28]=b'\x12\x34'
        elif changed=='nonuniform':packet[0x37]=0x10
        elif changed=='not_half':packet[0x38]=2
        for i,b in enumerate(packet):put(m,current+i,b,1)
        for i,b in enumerate(old):put(m,previous+i,b,1)
        put(m,s['section_ptr'],previous+64)
        put(m,s['queue_id'],0,1)
        put(m,s['sect_queues'],previous+64 if changed=='first' else previous-64)
        put(m,s['hcomp_cgram_event_count'],3 if changed=='cgram' else 2,2)
        put(m,s['hcomp_last_section_count'],2,2)
        regs=[sx(0x11110000+i) for i in range(32)];regs[0]=0;regs[31]=EXIT
        before=regs.copy()
        sentinel=s['hcomp_new_section'];put(m,sentinel,0x03e00008);put(m,sentinel+4,0x24020001)
        regs=before.copy();regs[2]=0
        execute(m,s['section_init'],regs,{},stop=EXIT)
        allowed=(changed is None or changed in (0x26,0x27,0x3f,'sub2'))
        assert bool(regs[2])==(not allowed),(changed,regs[2],allowed)
        assert all(regs[i]==before[i] for i in (12,13,14,23,31)),('caller ownership',changed)
        cases['epoch']+=1
    # Branches read the signed displacement and retain the bank of PC+2.
    for name in ('cpu_bra','cpu_bne','cpu_bmi','cpu_bpl','cpu_bcc','cpu_bcs','cpu_bvc','cpu_bvs'):
        flags={'cpu_bra':0,'cpu_bne':0,'cpu_bmi':0x80,'cpu_bpl':0,'cpu_bcc':0,'cpu_bcs':1,'cpu_bvc':0,'cpu_bvs':0x40}[name]
        for bank in (0,1,0x7e,0xff):
            for low in (0,1,0x7fff,0xff7f,0xfffe,0xffff):
                for disp in (-128,-127,-4,-1,0,1,127):
                    m=image.copy();pc=(bank<<16)|low
                    put(m,pc+1,disp,1)
                    regs=[0]*32;regs[20]=flags;regs[21]=1000;regs[23]=pc
                    execute(m,s[name],regs,{},stop=s['cpu_execute'])
                    base=(pc+2)&0xffffffff
                    want=(base&0xffff0000)|((base+disp)&0xffff)
                    assert regs[23]&0xffffffff==want,(name,hex(pc),disp,hex(regs[23]),hex(want))
                    assert regs[21]==992,(name,'guest read cycle count',regs[21])
                    cases['branches']+=1
    from test_hcomp_aligned_targets import constants
    offset=constants()['FB_OFFSET']
    for path in (a.main_rsp,a.mode7_rsp):
        base,text=read_text(path);base&=0xfff
        syms={n:addr&0xfff for addr,n in elf_symbols(path)}
        assert syms['hcomp_obj_row_clip']==0xca4
        for start in (0,1,7,8,17,63,127,223,239):
            for rows in (1,2,7,8,31):
                end=min(start+rows,240)
                for y in range(-16,257,3):
                    d=bytearray(4096);struct.pack_into('>I',d,offset,16)
                    regs=[0]*32;regs[8]=int(y<end);regs[26]=start;regs[27]=end;regs[30]=y&0xffffffff;regs[31]=0xabc
                    rsp_execute(text,base,d,syms['hcomp_obj_row_clip'],{0xabc,syms['hcomp_obj_row_done']},regs)
                    overlap=y<end and y+8>start
                    assert (regs[14]==0x02000000)==overlap,(path,start,end,y)
                    assert (regs[26],regs[27],regs[30])==(start,end,y&0xffffffff)
                    if overlap:assert regs[15]==16
                    cases['obj_rows']+=1
    report=dict(passed=True,cases=cases,commercial_data=False,native_timing=False)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('RENDERER_BATCHING PASS',json.dumps(report))

if __name__=='__main__':main()
