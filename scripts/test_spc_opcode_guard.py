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
    parser.add_argument('--require-live-relative',action='store_true')
    parser.add_argument('--guard-mode',choices=('eager','lazy'),default='eager')
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
        ('queued_NZ_flags_not_loaded',0x140,'e8802d8d352f00',0x25,((0x17f,0xa7),),0x147,
            [dict(PC=0x143,total_cycles=6,registers=registers(a=0x80,sp=0x7e,p=0xa5)),
             dict(PC=0x147,total_cycles=12,registers=registers(a=0x80,y=0x35,sp=0x7e,p=0x25))],{0x17f:0x80}),
        ('queued_NZ_live_carry',0x140,'68112d8d352f00',0xa4,((0x17f,0xa7),),0x147,
            [dict(PC=0x143,total_cycles=6,registers=registers(sp=0x7e,p=0x27)),
             dict(PC=0x147,total_cycles=12,registers=registers(y=0x35,sp=0x7e,p=0x25))],{0x17f:0x11}),
    ]
    for name,pc,code,flags,values,stop,expected,expected_memory in cases:
        result=run(base,symbols,bytes.fromhex(code),test_pc=pc,observe_data=True,flags=flags,
            memory_values=values,expect_recompile=True,stop_guest_pcs=(stop,))
        assert result['native_boundaries']==expected,(name,result,expected)
        assert all(result['outcome']['memory'][hex(at)]==value for at,value in expected_memory.items()),(name,result)
        results.append(dict(name=name,native_boundaries=result['native_boundaries'],outcome=result['outcome'],
            tagged_recompile_exact=result['tagged_recompile_exact']))
    # Publish a synthetic source-tag update after a flag/read-only instruction.
    # It changes no opcode, register or guest clock, and is not a DSP-core test.
    def publish_at_boundary(cpu,s,pc):
        if cpu.regs[16]&65535==pc:
            begin=cpu.read(s['jit_lookup']+pc*4)+12
            end=(cpu.read(s['jit_pointer'])-0x20000000)&0xffffffff
            wanted=0x34040000|(pc+1)
            sites=[at for at in range(begin,end,4)if cpu.read(at)==wanted and cpu.read(at-4)>>26==4]
            assert len(sites)==1,sites
            load=sites[0]-16;assert cpu.read(load)>>26==0x23
            def publish(c):
                tag=s['jit_tags']+(pc>>6)*4
                c.write(tag,(c.read(tag)+1)&0xffffffff)
            cpu.before_instruction[load]=publish
        cpu.before_instruction[s['jit_lookup_published']]=lambda c:publish_at_boundary(c,s,pc)
    publisher_cases=[
        ('SF_only_CLRC',0x60,0x25,(),registers(p=0x24),registers(y=0x35,p=0x24),2,8),
        ('SF_only_SETP',0x40,0,(),registers(p=0x20),registers(y=0x35,p=0x20),2,8),
        ('SF_only_CLRV',0xe0,0xff,(),registers(p=0xb7),registers(y=0x35,p=0x35),2,8),
        ('no_dirty_registers',0,0xa5,(),registers(p=0xa5),registers(y=0x35,p=0x25),2,8),
        ('POP_A_no_NZ',0xae,0x25,((0x180,0x80),),registers(a=0x80,sp=0x80,p=0x25),registers(a=0x80,y=0x35,sp=0x80,p=0x25),4,10),
        ('POP_X_no_NZ',0xce,0x25,((0x180,0x80),),registers(x=0x80,sp=0x80,p=0x25),registers(x=0x80,y=0x35,sp=0x80,p=0x25),4,10),
        ('POP_Y_no_NZ',0xee,0x25,((0x180,0x80),),registers(y=0x80,sp=0x80,p=0x25),registers(y=0x35,sp=0x80,p=0x25),4,10),
    ]
    for name,op,flags,values,first,last,first_cycles,total in publisher_cases:
        result=run(base,symbols,bytes((op,0x8d,0x35,0x2f,0)),test_pc=0x100,observe_data=True,
            flags=flags,memory_values=values,expect_recompile=True,stop_guest_pcs=(0x105,),jit_mutation=publish_at_boundary)
        expected=[dict(PC=0x101,total_cycles=first_cycles,registers=first),
            dict(PC=0x105,total_cycles=total,registers=last)]
        assert result['native_boundaries']==expected,(name,result,expected)
        results.append(dict(name=name,synthetic_boundary_tag_publication=True,
            native_boundaries=result['native_boundaries'],tagged_recompile_exact=result['tagged_recompile_exact']))
    rejected=[]
    if args.mutations:
        for kind in ('omit_guard_prefix','omit_guard_NZ','omit_guard_SP_commit'):
            memory=base.copy()
            lazy=args.guard_mode=='lazy'
            if kind=='omit_guard_prefix':
                begin=symbols['jit_guard_opcode_lazy' if lazy else 'jit_guard_opcode']
                end=symbols['lazy_guard_clock_ready' if lazy else 'guard_clock_ready'];wanted=0xaca90000
            elif kind=='omit_guard_NZ':
                if lazy:
                    begin=symbols['lazy_nz_store'];end=begin+16
                    matches=[at for at in range(begin,end,4)
                        if (int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')>>26)==0x28
                        and ((int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')>>16)&31)==9]
                else:
                    begin=symbols['jit_guard_opcode'];end=symbols['guard_clock_ready']
                    wanted=0x0c000000|((symbols['update_nz']>>2)&0x3ffffff)
            else:
                begin=symbols['apu_code_changed_lazy' if lazy else 'apu_code_changed']
                end=symbols['apu_code_changed_lazy_end'] if lazy else begin+64;wanted_opcode=0x28
                matches=[at for at in range(begin,end,4)
                    if (int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')>>26)==wanted_opcode
                    and ((int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')>>16)&31)==18]
            if kind=='omit_guard_prefix' or (kind=='omit_guard_NZ' and not lazy):
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
    if args.require_live_relative:assert within_exact,within
    else:assert not within_exact,'Within-instruction fetch changed; qualify the new path'
    proof=dict(passed=True,guard_mode=args.guard_mode,cases=results,rejected_linked_instruction_mutations=rejected,
        within_instruction_counterexample=dict(exact=within_exact,outcome=within['outcome'],
            total=within['total_cycles'],expected_PC=0x102,expected_total=7),
        ELF_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),real_native_JIT_and_APU_reentry=True,
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        full_SCPU_scheduler_timing_proved=False,full_instruction_fetch_coherence_proved=False,
        absolute_DSP_epoch_implemented=False,native_performance_claim=False,commercial_data=False)
    print('SPC_OPCODE_GUARD cases='+str(len(results))+' rejected_mutants='+str(len(rejected)))
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
