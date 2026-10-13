#!/usr/bin/env python3
"""Execute the actual short rebind binary with poisoned register/flag state.

Numeric fixtures only. Tests the diagnostic program, not renderer liveness or
hardware timing. Native continuation decides whether this context is sufficient.
"""
import argparse,json,random,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_hcomp_sub_presence import section
from native_diag_report import elf_symbols

def execute(code,data,queue,seed):
    rng=random.Random(seed)
    r=[0]+[rng.getrandbits(32) for _ in range(31)]
    v=[[rng.randrange(65536) for _ in range(8)] for _ in range(32)]
    acc=[rng.randrange(1,1<<48) for _ in range(8)]
    flags=[0xffff,0xffff,0xff]
    d=bytearray(data);struct.pack_into('>I',d,0,queue);before=bytes(d)
    for pc in range(0,len(code),4):
        w=struct.unpack_from('>I',code,pc)[0]
        op,rs,rt,rd,fn,vd=w>>26,w>>21&31,w>>16&31,w>>11&31,w&63,w>>6&31
        if op==0 and fn==37:r[rd]=r[rs]|r[rt]
        elif op==0 and fn==13:
            assert r==[0]*29+[queue,0,0],'scalar continuation context'
            constants=[list(struct.unpack_from('>8H',d,0xf70+16*i)) for i in range(9)]
            assert v==[[0]*8 for _ in range(23)]+constants,'vector continuation constants'
            assert flags==[0,0,0] and acc==[0]*8,'flag/accumulator residue'
            assert bytes(d)==before,'program mutated DMEM'
            return pc//4+1
        elif op==18 and rs==6:
            assert rd<3 and not (w&2047),'unsupported CTC2 mode'
            flags[rd]=r[rt]&([65535,65535,255][rd])
        elif op==18 and rs==16:
            if fn==0x2c:v[vd]=[a^b for a,b in zip(v[rd],v[rt])]
            elif fn==4: # VMUDL: unsigned product high16, 48-bit ACC = result
                acc=[(a*b)>>16 for a,b in zip(v[rd],v[rt])];v[vd]=acc.copy()
            else:raise AssertionError(('unexpected vector operation',hex(w)))
        elif op==50:
            assert w>>11&31==4 and w>>7&15==0,'unaligned vector mode'
            offset=w&127;offset=offset if offset<64 else offset-128
            address=(r[rs]+offset*16)&4095
            assert not address&15
            v[rt]=list(struct.unpack_from('>8H',d,address))
        elif op==35:
            imm=w&65535;imm=imm if imm<32768 else imm-65536
            address=(r[rs]+imm)&4095
            assert not address&3
            r[rt]=struct.unpack_from('>I',d,address)[0]
        else:raise AssertionError(('unexpected instruction/RCP write',pc,hex(w)))
        r[0]=0
    raise AssertionError('rebind did not BREAK')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args();_,code=read_text(a.build/'src/rsp_scene_rebind.elf')
    assert len(code)<4096 and len(code)%4==0
    base,halt=read_text(a.build/'src/rsp_hcomp.elf')
    assert struct.unpack_from('>III',halt,0xa40013c0-base)==(0x40882000,0x0900040f,0), 'canonical HALT/jump/delay slot ownership'
    main_symbols={n:p for p,n in elf_symbols(a.build/'src/rsp_main.elf')}
    assert main_symbols['draw_frame']&4095==0x3c,'normal restart entry moved'
    data=section(a.build/'src/rsp_main.elf','.data');cases=0;steps=set()
    for queue in (0,4):
        for seed in range(16):steps.add(execute(code,data,queue,seed));cases+=1
    mutations=[]
    words=list(struct.unpack('>'+str(len(code)//4)+'I',code))
    for name,index in [('missing_queue',next(i for i,w in enumerate(words) if w>>26==35)),
                       ('missing_constant',next(i for i,w in enumerate(words) if w>>26==50)),
                       ('missing_flags',next(i for i,w in enumerate(words) if w>>26==18 and w>>21&31==6)),
                       ('missing_accumulator',next(i for i,w in enumerate(words) if w>>26==18 and w&63==4))]:
        changed=words.copy();changed[index]=0x00000825 # OR at,zero,zero; accepted harmless substitute
        try:execute(struct.pack('>'+str(len(changed))+'I',*changed),data,4,9)
        except AssertionError:mutations.append(name)
        else:raise AssertionError('escaped mutation '+name)
    result=dict(passed=True,actual_binary_cases=cases,executed_instructions=list(steps),
                mutations_rejected=mutations,GPR_vector_flags_ACC_reconstructed=True,
                DMEM_unchanged=True,no_DMA_DP_AI_or_guest_work=True,
                hardware_mocked=True,renderer_liveness_proved=False,native_acceptance=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
