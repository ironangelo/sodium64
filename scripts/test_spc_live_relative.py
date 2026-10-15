#!/usr/bin/env python3
"""DBNZ writes its own later displacement: real JIT bus, branch and wrap proof."""
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
    assert 'apu_dbnz_runtime_relative' in symbols
    for pc in (0x100,0xfffe):
        address=0x102 if pc==0x100 else 0
        operand=2 if pc==0x100 else 0
        for value in (0,1,2,0x7f,0x80,0x81,0xfe,0xff):
            changed=(value-1)&255
            next_pc=(pc+3)&65535
            if changed:next_pc=(next_pc+(changed if changed<128 else changed-256))&65535
            for initial_flags in (0x20,0x6d,0xff):
                flags=initial_flags if pc==0x100 else initial_flags&~0x20
                for clock in (1,21,255):
                    for pointer in (0xa01c0000,0xa01fffc0):
                        def tags(cpu,s,pc=pc):
                            header=cpu.read(s['jit_lookup']+pc*4)
                            return dict(first=cpu.read(header,2),last=cpu.read(header+2,2))
                        result=run(base,symbols,bytes((0x6e,operand,value)),test_pc=pc,clock=clock,
                            jit_pointer=pointer,observe_data=True,flags=flags,memory_values=((address,value),),
                            expect_recompile=True,extra_outcome=tags)
                        observed=[(event['kind'],event['address'],event['elapsed_master_cycles']//clock)for event in result['events']]
                        expected=[('read',address,3),('write',address,4),('read',address,5)]
                        registers=dict(apu_accum=0x11,apu_reg_x=4,apu_reg_y=6,apu_stack=0x7f,apu_flags=flags)
                        expected_tags=dict(first=(pc>>6)*4,last=(((pc+3)&65535)>>6)*4)
                        assert observed==expected,(pc,value,result)
                        assert result['total_cycles']==(7 if changed else 5),(pc,value,result)
                        assert result['outcome']['PC']==next_pc,(pc,value,result,next_pc)
                        assert result['outcome']['registers']==registers,(pc,value,result)
                        assert result['outcome']['memory'][hex(address)]==changed,(pc,value,result)
                        assert result['outcome']['extra']==expected_tags,(pc,value,result)
                        results.append(dict(source_PC=pc,initial=value,flags=flags,clock=clock,
                            requested_JIT_pointer=hex(pointer),observed=observed,total=result['total_cycles'],
                            outcome=result['outcome'],tagged_recompile_exact=result['tagged_recompile_exact'],
                            reset_exercised=result['reset_exercised']))
    rejected=[]
    if args.mutations:
        memory=base.copy()
        begin=symbols['apu_dbnz_runtime_relative'];end=symbols['apu_bra']
        wanted=0x0c000000|((symbols['jit_dummy_pc']>>2)&0x3ffffff)
        matches=[at for at in range(begin,end,4)
            if int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')==wanted]
        assert len(matches)==1,matches
        memory.update(((matches[0]+i)&0x1fffffff,0)for i in range(4))
        result=run(memory,symbols,bytes.fromhex('6e0200'),test_pc=0x100,flags=0x20,
            observe_data=True,memory_values=((0x102,0),),expect_recompile=True)
        assert result['total_cycles']!=7 or result['outcome']['PC']!=0x102,result
        rejected.append('omit_runtime_relative_read')
        def omit_sign(cpu,s,pc):
            begin=cpu.read(s['jit_lookup']+pc*4)+12
            end=(cpu.read(s['jit_pointer'])-0x20000000)&0xffffffff
            matches=[at for at in range(begin,end,4)if cpu.read(at)==0x00021603] # SRA V0,V0,24
            assert len(matches)==1,matches
            cpu.write(matches[0],0)
            cpu.before_instruction[s['jit_lookup_published']]=lambda c:omit_sign(c,s,pc)
        result=run(base,symbols,bytes.fromhex('6e0200'),test_pc=0x100,flags=0x20,
            observe_data=True,memory_values=((0x102,0),),expect_recompile=True,jit_mutation=omit_sign)
        assert result['total_cycles']==7 and result['outcome']['PC']!=0x102,result
        rejected.append('omit_runtime_displacement_sign_extension')
    proof=dict(passed=True,cases=results,rejected_linked_or_emitted_mutations=rejected,
        ELF_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),real_native_JIT_and_guest_write=True,
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        absolute_DSP_epoch_implemented=False,full_instruction_fetch_coherence_proved=False,
        native_performance_claim=False,commercial_data=False)
    print('SPC_LIVE_RELATIVE cases='+str(len(results))+' resets='+str(sum(case['reset_exercised']for case in results))+
        ' rejected_mutants='+str(len(rejected)))
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
