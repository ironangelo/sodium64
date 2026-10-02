#!/usr/bin/env python3
"""Diagnostic execution of a compiled arithmetic bank with independent operands.

Seeds original colors/tags and an inert CPU loop after a natural boot fence.
This is kernel correctness evidence, not an ordinary game or cadence test.
"""
import argparse,json,random,struct,socket,itertools
from pathlib import Path
from capture_stage2_publication import load_symbols
from capture_gate_c_stage1_ares import set_breakpoint,require_fenced_boundary
from check_rsp_branch_delay_slots import read_text
from gdb_rsp_dump import connect_with_retry,ARES_N64_GUEST_SIGNALS,validate_stop

TAGS=[0x400,0xc00,0x1400,0x1c00,0x2800,0x3800,0x5000]
ELIGIBILITY={0x400:0x20,0xc00:1,0x1400:2,0x1c00:4,0x2800:8,0x3800:0,0x5000:0x10}
FB=0xa00f2300

def rgba(ch):return (ch[0]<<11)|(ch[1]<<6)|(ch[2]<<1)|1

def write(c,addr,data):
    # ares uses CPU SD for exactly eight bytes; RCP registers/DMEM do not
    # implement the RDRAM dualword behavior. Issue word writes for that size.
    chunk=4 if 0xa4000000<=addr and len(data)==8 else 1024
    for i in range(0,len(data),chunk):c.write_memory(addr+i,data[i:i+chunk])

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--port',type=int,required=True)
    ap.add_argument('--boot-elf',type=Path,required=True);ap.add_argument('--kernel-elf',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--rows',type=int,default=1)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    assert 1<=a.rows<=8
    base,bank=read_text(a.kernel_elf);bank=bytearray(bank)
    end=load_symbols(a.kernel_elf)['hcomp_return_phase']-base
    bank[end:end+12]=struct.pack('>III',0x0000000d,0,0) # halt instead of phase-bank return
    c=connect_with_retry('127.0.0.1',a.port,30,60);rng=random.Random(0x364123)
    checked=0;cases=[]
    try:
        c.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        c.request('qSupported:multiprocess+;swbreak+;hwbreak+');c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS)==b'OK'
        stop=load_symbols(a.boot_elf)['frame_wait']+0x14
        set_breakpoint(c,stop,True);validate_stop(c.request('c'),'kernel boot fence')
        require_fenced_boundary(c,stage='kernel boot');set_breakpoint(c,stop,False)
        # ares ignores PC register writes while a breakpoint PC override is
        # active. Retire one CPU instruction before installing the inert loop.
        validate_stop(c.request('s'),'kernel leave breakpoint override')
        c.write_memory(0xa4040010,(2).to_bytes(4,'big'))
        write(c,0xa00de000,struct.pack('>IIIII',0x40806000,0,0,0x1000ffff,0))
        assert c.request('P25=ffffffffa00de000')==b'OK'
        assert c.request('p25')==b'ffffffffa00de000'
        write(c,base,bank)
        assert c.read_memory(base,len(bank),1024)==bank
        for mode,clip,prevent,source,enables in itertools.product((0,0x40,0x80,0xc0),range(4),range(4),(0,2),(0,0x15,0x2a,0x3f)):
            count=a.rows*256;fixed=tuple(rng.randrange(32) for _ in range(3))
            main=[tuple(rng.randrange(32) for _ in range(3)) for _ in range(count)]
            sub=[tuple(rng.randrange(32) for _ in range(3)) for _ in range(count)]
            mz=[TAGS[i%7] for i in range(count)];sz=[0x400 if i%3==0 else 0xc00 for i in range(count)]
            def surface(values):
                return b''.join(bytes(24)+struct.pack('>256H',*values[y*256:(y+1)*256])+bytes(24) for y in range(a.rows))
            write(c,FB,surface([rgba(x) for x in main]));write(c,0xa00e4000,surface([rgba(x) for x in sub]))
            write(c,0xa00e2000,surface(mz));write(c,0xa00e6000,surface(sz))
            # Aligned writes avoid ares' rounded-down partial RCP reads.
            d=bytearray(c.read_memory(0xa4000000,4096,1024))
            d[0xba6:0xba8]=rgba(fixed).to_bytes(2,'big')
            d[0xbae:0xbb2]=bytes((32,95,64,191));d[0xbb4]=0xa0;d[0xbb6]=8
            d[0xbb7]=(clip<<6)|(prevent<<4)|source;d[0xbb8]=mode|enables
            d[0xc00:0xc08]=struct.pack('>II',FB,FB)
            d[0xec0:0xec8]=struct.pack('>II',8,a.rows)
            write(c,0xa4000b80,bytes(d[0xb80:0xbc0]));write(c,0xa4000c00,bytes(d[0xc00:0xc08]))
            write(c,0xa4000ec0,bytes(d[0xec0:0xec8]))
            c.write_memory(0xa4080000,(base+8).to_bytes(4,'big'))
            assert int.from_bytes(c.read_memory(0xa4080000,4,4),'big')==((base+8)&0xfff)
            c.write_memory(0xa4040010,(0x8d).to_bytes(4,'big'))
            if not checked:
                print('launch bank',hex(base),hex(end),c.read_memory(base+end,12,12).hex(),flush=True)
            assert c.continue_then_interrupt(.2)==b'S05'
            status=int.from_bytes(c.read_memory(0xa4040010,4,4),'big')
            if not status&1:
                (a.output/'failure-dmem.bin').write_bytes(c.read_memory(0xa4000000,4096,1024))
                (a.output/'failure-cpu.txt').write_bytes(c.request('g'))
                c.write_memory(0xa4040010,(2).to_bytes(4,'big'))
                registers=c.read_memory(0xa4040000,32,32)
                pc=c.read_memory(0xa4080000,4,4)
                print('halted diagnostic',pc.hex(),registers.hex(),flush=True)
                imem=c.read_memory(base,len(bank),1024)
                print('bank still owned',imem==bank,imem[end:end+12].hex(),flush=True)
                (a.output/'failure-imem.bin').write_bytes(imem)
            assert status&1,('kernel did not halt',hex(status),c.request('p25'))
            got=c.read_memory(FB,280*a.rows*2,1024);values=struct.unpack('>'+str(280*a.rows)+'H',got)
            for i in range(count):
                x=i%256;selected=(32<=x<=95)!=(64<=x<=191)
                clipped=clip==3 or (clip==1 and not selected) or (clip==2 and selected)
                blocked=prevent==3 or (prevent==1 and not selected) or (prevent==2 and selected)
                color=(0,0,0) if clipped else main[i]
                if ELIGIBILITY[mz[i]]&enables and not blocked:
                    operand=sub[i] if source and sz[i]!=0x400 else fixed
                    half=bool(mode&0x40) and not clipped and not (source and sz[i]==0x400)
                    color=tuple(min(31,(max(0,v-b) if mode&0x80 else v+b)//(2 if half else 1)) for v,b in zip(color,operand))
                want=rgba(color);actual=values[(i//256)*280+x+12]
                assert actual==want,dict(mode=hex(mode),clip=clip,prevent=prevent,source=source,index=i,got=hex(actual),expected=hex(want),main=main[i],sub=sub[i],fixed=fixed,main_tag=hex(mz[i]),sub_tag=hex(sz[i]))
            checked+=count;cases.append(dict(mode=mode,clip=clip,prevent=prevent,source=source,enables=enables))
        result=dict(passed=True,cases=len(cases),checked_pixels=checked,rows=a.rows,
                    diagnostic_operand_and_cpu_writes=True,ordinary_game_authority=False,native_cadence_authority=False)
        (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('HCOMP_KERNEL PASS',json.dumps(result),flush=True)
    finally:c.close()

if __name__=='__main__':main()
