#!/usr/bin/env python3
"""Compiled CPU cache publication must visit every VRAM line once in order.

The expected bus-visible cache operation sequence is independent of loop
grouping. No guest data, cache simulation shortcut or native timing claim.
"""
import argparse,json,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    base,code=read_text(a.elf);syms={n:v for v,n in elf_symbols(a.elf)}
    pc=syms['vram_flush_begin'];stop=syms['vram_flush_end'];pending=None
    regs=[0x13500000+i for i in range(32)];regs[0]=0;before=regs[:]
    seen=[];instructions=0
    while pc!=stop:
        assert instructions<20000
        word=struct.unpack_from('>I',code,pc-base)[0]
        op=word>>26;rs=word>>21&31;rt=word>>16&31;rd=word>>11&31
        imm=word&65535;si=imm if imm<32768 else imm-65536;target=None
        if op==15:regs[rt]=imm<<16
        elif op in (8,9):regs[rt]=regs[rs]+si
        elif op==13:regs[rt]=regs[rs]|imm
        elif op==0 and word&63 in (32,33):regs[rd]=regs[rs]+regs[rt]
        elif op==5:
            if regs[rs]!=regs[rt]:target=pc+4+(si<<2)
        elif op==47:seen.append((rt,(regs[rs]+si)&0xffffffff))
        else:raise AssertionError((hex(pc),hex(word)))
        assert pending is None or target is None
        regs[:]=[v&0xffffffff for v in regs];regs[0]=0
        pc=pending if pending is not None else pc+4;pending=target;instructions+=1
    assert seen==[(0x19,syms['vram']+i) for i in range(0,65536,16)]
    assert all(regs[i]==before[i] for i in range(32) if i not in (1,8,9))
    assert regs[8]==syms['vram']+65536
    result=dict(passed=True,cache_lines=len(seen),exact_address_order=True,
                operation='Hit_Writeback_D',instructions=instructions,
                old_loop_body_instructions=8192,new_loop_body_instructions=5120,
                native_fps_authority=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('VRAM_FLUSH PASS '+json.dumps(result))

if __name__=='__main__':main()
