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
    rng=random.Random(0x6516);cases=dict(epoch=0,branches=0,obj_rows=0,apu_reset=0,rom_cache=0,row_input=0,hdma_row_phase=0)
    for queue in (0xa03e7000,0xa03e7200):
        for line in (0,*range(1,242),255,65535):
            m=image.copy();lo=(queue-64)&0x1fffffff
            original=bytes([0xa5])*640
            m.update((lo+i,b) for i,b in enumerate(original))
            put(m,s['cur_line'],line,2);put(m,s['sub_color'],0xbeee,2)
            put(m,s['hcomp_row_fixed_ptr'],queue)
            execute(m,s['hcomp_record_row_input'],[0]*32,{},stop=s['hcomp_row_fixed_recorded'])
            want=bytearray(original)
            if 1<=line<=240:want[64+2*(line-1):66+2*(line-1)]=b'\xbe\xee'
            assert bytes(m[lo+i] for i in range(640))==want,('row producer bounds',hex(queue),line)
            cases['row_input']+=1
    # Independently execute the existing HDMA scheduler and COLdata writer.
    # Vblank end reloads HDMA and runs line 0 before any displayed row: table
    # entry y therefore becomes the fixed operand of displayed row y. This
    # proves the fixture's expected phase without using its rendered pixels.
    from make_hcomp_fullheight import build
    table=build('fixed-half-raster')[0x3000:0x3100]
    row_values=[y&31 for y in range(223)]+[0]
    for queue in (0xa03e7000,0xa03e7200):
        m=image.copy();table_address=0x00600000
        m.update((table_address+i,b) for i,b in enumerate(table))
        put(m,s['hdma_mask'],1,1);put(m,s['end_mask'],0,1)
        put(m,s['ntrlx'],1,1);put(m,s['dmapx'],0,1)
        put(m,s['bbadx'],0x32,1);put(m,s['a2abx'],table_address)
        put(m,s['write_iomap']+0x32*4,s['write_coldata'])
        put(m,s['brightness'],16,1);put(m,s['coldata'],0,2)
        put(m,s['sub_color'],0,2);put(m,s['hcomp_row_fixed_ptr'],queue)
        for line in range(225):
            put(m,s['cur_line'],line,2)
            execute(m,s['hcomp_record_row_input'],[0]*32,{},stop=s['hcomp_row_fixed_recorded'])
            if line:
                addr=(queue+2*(line-1))&0x1fffffff
                got=int.from_bytes(bytes(m[addr+i] for i in range(2)),'big')
                assert got==row_values[line-1]*2,('HDMA row phase',line-1,got,row_values[line-1]*2)
                cases['hdma_row_phase']+=1
            regs=[0]*32;regs[31]=EXIT
            execute(m,s['trigger_hdma'],regs,{},stop=EXIT)
        assert m[s['hdma_mask']&0x1fffffff]==0
    # The resized ROM pager must wrap at the new owner boundary. Execute its
    # compiled PI-address and slot transition; no cart DMA timing is simulated.
    for slot in range(194):
        m=image.copy();put(m,s['rom_pointer'],slot,1)
        put(m,s['rom_entries']+slot*4,0)
        regs=[0]*32;regs[27]=0x10123400
        execute(m,s['tlbl_rom'],regs,{},stop=s['set_entry'],terminal_rcp=True)
        dram=int.from_bytes(bytes(m[0x04600000+i] for i in range(4)),'big')
        assert dram==0x200000+slot*8192 and dram+8192<=0x384000
        assert m[s['rom_pointer']&0x1fffffff]==(slot+1)%194
        assert regs[27]&0xffffffff==((0x100+slot)<<7)|0x1b
        assert regs[26]==slot*4
        cases['rom_cache']+=1
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
    # AT is the pre-existing assembler scratch for the absolute pointer store.
    assert all(regs[i]==before[i] for i in set(range(32))-{1,8,9})
    assert steps<50000,('lookup reset instruction bound',steps)
    cases['apu_reset']+=1
    current=s['bghofs'];previous=0xa0140000
    # Stop before either path performs queue/OAM publication.
    for changed in [None,*range(64),'cgram','dirty','sub2','first','nonuniform','not_half','brightness']:
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
        put(m,s['brightness'],8 if changed=='brightness' else 16,1)
        put(m,s['hcomp_last_section_brightness'],16,1)
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
    for bank in (0,1,0x7e,0xff):
        for low in (0,1,0x7fff,0xff7f,0xfffd,0xfffe,0xffff):
            for disp in (-32768,-32767,-4,-1,0,1,32767):
                m=image.copy();pc=(bank<<16)|low
                put(m,pc+1,disp&255,1);put(m,pc+2,(disp>>8)&255,1)
                regs=[0]*32;regs[21]=1000;regs[23]=pc
                execute(m,s['cpu_brl'],regs,{},stop=s['cpu_execute'])
                base=(pc+3)&0xffffffff
                want=(base&0xffff0000)|((base+disp)&0xffff)
                assert regs[23]&0xffffffff==want,('cpu_brl',hex(pc),disp,hex(regs[23]),hex(want))
                assert regs[21]==984,('cpu_brl','guest read cycle count',regs[21])
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
