#!/usr/bin/env python3
"""Directed architectural commit and cycle debt of the real JIT source guard."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--mutations',action='store_true')
    args=parser.parse_args();base,symbols=load_elf(args.elf);results=[]
    def registers(a=0x11,x=4,y=6,sp=0x7f,p=0x20):
        return dict(apu_accum=a,apu_reg_x=x,apu_reg_y=y,apu_stack=sp,apu_flags=p)
    for version in (0,0x12345678,0x7ffffffe,0x80000000,0xffffffff):
        for flags in (0x20,0x6d,0xff):
            memory=base.copy();at=(symbols['jit_tags']+4*4)&0x1fffffff
            memory.update((at+i,b)for i,b in enumerate(version.to_bytes(4,'big')))
            result=run(memory,symbols,bytes.fromhex('e800cd05c6e8112f00'),test_pc=0x100,
                observe_data=True,flags=flags,memory_values=((0x105,0xe8),(0xffdc,0),(0xffdd,6)),
                expect_recompile=True,stop_guest_pcs=(0x600,))
            expected=[dict(PC=0x105,total_cycles=8,registers=registers(a=0,x=5,p=flags&0x7d)),
                dict(PC=0x600,total_cycles=18,registers=registers(a=0,x=5,sp=0x7d,p=flags&0x7d))]
            assert result['native_boundaries']==expected,(version,flags,result,expected)
            results.append(dict(name='opcode_redecode',tag_version=version,flags=flags,
                native_boundaries=result['native_boundaries'],total=result['total_cycles'],
                tagged_recompile_exact=result['tagged_recompile_exact']))
    cases=[
        ('push_trailing_idle',0x140,'2d8d352f00',0xa5,((0x17f,0xa7),),0x145,
            [dict(PC=0x141,total_cycles=4,registers=registers(sp=0x7e,p=0xa5)),
             dict(PC=0x145,total_cycles=10,registers=registers(y=0x35,sp=0x7e,p=0x25))],{0x17f:0x11}),
        ('INC_queued_NZ',0x140,'ab7f8d352f00',0xa5,((0x17f,0xff),),0x146,
            [dict(PC=0x142,total_cycles=4,registers=registers(p=0x27)),
             dict(PC=0x146,total_cycles=10,registers=registers(y=0x35,p=0x25))],{0x17f:0}),
        ('dirty_SP',0x100,'e800cd06bdc6e8112f00',0x20,((0x106,0xe8),(0xffdc,0),(0xffdd,6)),0x600,
            [dict(PC=0x106,total_cycles=10,registers=registers(a=0,x=6,sp=6)),
             dict(PC=0x600,total_cycles=20,registers=registers(a=0,x=6,sp=4))],{0x106:1}),
        ('dirty_Y',0x100,'e800cd078d80c6e8112f00',0x20,((0x107,0xe8),(0xffdc,0),(0xffdd,6)),0x600,
            [dict(PC=0x107,total_cycles=10,registers=registers(a=0,x=7,y=0x80,p=0xa0)),
             dict(PC=0x600,total_cycles=20,registers=registers(a=0,x=7,y=0x80,sp=0x7d,p=0xa0))],{0x107:0}),
    ]
    for name,pc,code,flags,values,stop,expected,expected_memory in cases:
        result=run(base,symbols,bytes.fromhex(code),test_pc=pc,observe_data=True,flags=flags,
            memory_values=values,expect_recompile=True,stop_guest_pcs=(stop,))
        assert result['native_boundaries']==expected,(name,result,expected)
        assert all(result['outcome']['memory'][hex(at)]==value for at,value in expected_memory.items()),(name,result)
        results.append(dict(name=name,native_boundaries=result['native_boundaries'],outcome=result['outcome'],
            tagged_recompile_exact=result['tagged_recompile_exact']))
    rejected=[]
    if args.mutations:
        for kind in ('omit_guard_prefix','omit_guard_NZ','omit_guard_SP_commit'):
            memory=base.copy()
            if kind=='omit_guard_prefix':
                begin=symbols['jit_guard_opcode'];end=symbols['guard_clock_ready'];wanted=0xaca90000
            elif kind=='omit_guard_NZ':
                begin=symbols['jit_guard_opcode'];end=symbols['guard_clock_ready']
                wanted=0x0c000000|((symbols['update_nz']>>2)&0x3ffffff)
            else:
                begin=symbols['apu_code_changed'];end=begin+64;wanted_opcode=0x28
                matches=[at for at in range(begin,end,4)
                    if (int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')>>26)==wanted_opcode
                    and ((int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')>>16)&31)==18]
            if kind!='omit_guard_SP_commit':
                matches=[at for at in range(begin,end,4)
                    if int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')==wanted]
            assert len(matches)==1,(kind,matches)
            memory.update(((matches[0]+i)&0x1fffffff,0)for i in range(4))
            selected=cases[1] if kind=='omit_guard_NZ' else cases[0]
            name,pc,code,flags,values,stop,expected,expected_memory=selected
            result=run(memory,symbols,bytes.fromhex(code),test_pc=pc,observe_data=True,flags=flags,
                memory_values=values,expect_recompile=True,stop_guest_pcs=(stop,))
            assert result['native_boundaries']!=expected,(kind,result)
            rejected.append(kind)
    # A boundary guard cannot repair an operand modified inside the current
    # instruction: DBNZ writes its own displacement before fetching it.
    within=run(base,symbols,bytes.fromhex('6e0200'),test_pc=0x100,observe_data=True,
        flags=0x20,memory_values=((0x102,0),),expect_recompile=True)
    within_exact=within['outcome']['PC']==0x102 and within['total_cycles']==7
    assert not within_exact,'Within-instruction fetch changed; qualify the new path'
    proof=dict(passed=True,cases=results,rejected_linked_instruction_mutations=rejected,
        within_instruction_counterexample=dict(exact=within_exact,outcome=within['outcome'],
            total=within['total_cycles'],expected_PC=0x102,expected_total=7),
        ELF_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),real_native_JIT_and_APU_reentry=True,
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        full_SCPU_scheduler_timing_proved=False,full_instruction_fetch_coherence_proved=False,
        absolute_DSP_epoch_implemented=False,native_performance_claim=False,commercial_data=False)
    print('SPC_OPCODE_GUARD cases='+str(len(results))+' rejected_mutants='+str(len(rejected)))
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
