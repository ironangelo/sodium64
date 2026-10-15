#!/usr/bin/env python3
"""Real SPC writes to a future immediate operand in the same native JIT block."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--require-immediates',action='store_true')
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();base,symbols=load_elf(args.elf);results=[]
    baseline=load_elf(args.baseline) if args.baseline else None
    expected_events=[('read',0x101,2),('read',0x103,4),('read',0x105,6),
        ('read',0x106,7),('write',0x106,8),('read',0x106,10)]
    for name,opcode,changed in (
        ('MOV_A',0xe8,dict(apu_accum=0x35)),('MOV_X',0xcd,dict(apu_reg_x=0x35)),
        ('MOV_Y',0x8d,dict(apu_reg_y=0x35)),('AND_A',0x28,dict(apu_accum=0x35)),
        ('EOR_A',0x48,dict(apu_accum=0,apu_flags=0x22)),
        ('CMP_A',0x68,dict(apu_flags=0x23))):
        code=bytes.fromhex('e835cd06c6')+bytes((opcode,0x11,0x2f,0))
        result=run(base,symbols,code,test_pc=0x100,observe_data=True,flags=0x20,
            memory_values=((0x106,0x11),),expect_recompile=True)
        expected_registers=dict(apu_accum=0x35,apu_reg_x=6,apu_reg_y=6,apu_stack=0x7f,apu_flags=0x20)
        expected_registers.update(changed)
        events=[(event['kind'],event['address'],event['elapsed_master_cycles']//21)for event in result['events']]
        exact=(events==expected_events and result['total_cycles']==14 and result['outcome']['PC']==0x109
            and result['outcome']['memory']['0x106']==0x35 and result['outcome']['registers']==expected_registers)
        item=dict(name=name,exact=exact,observed=events,expected=expected_events,
            total=result['total_cycles'],expected_total=14,outcome=result['outcome'],
            expected_registers=expected_registers,tagged_recompile_exact=result['tagged_recompile_exact'])
        results.append(item)
        print(name+(' EXACT' if exact else ' OPEN '+json.dumps(item)))
        if args.require_immediates:assert exact,item
    # Deliberate remaining limit: the producer changes a future opcode into NOP,
    # then the following byte is TCALL1. Operand reads alone cannot re-decode it.
    result=run(base,symbols,bytes.fromhex('e800cd05c6e8112f00'),test_pc=0x100,
        observe_data=True,flags=0x20,memory_values=((0x105,0xe8),(0xffdc,0),(0xffdd,6)),expect_recompile=True)
    opcode_exact=result['outcome']['PC']==0x600 and result['total_cycles']==18 and result['outcome']['registers']['apu_stack']==0x7d
    steady=[]
    if baseline:
        for opcode in (0x08,0x28,0x48,0x68,0x88,0xa8,0xc8,0xe8,0xcd,0x8d,0xad):
            for value in (0,1,0x80,0xff):
                for flags in (0,0x49,0xa5):
                    code=bytes((opcode,value,0x2f,0))
                    current=run(base,symbols,code,test_pc=0x400,observe_data=True,flags=flags)
                    control=run(*baseline,code,test_pc=0x400,observe_data=True,flags=flags)
                    events=[(event['kind'],event['address'],event['elapsed_master_cycles']//21)for event in current['events']]
                    exact=(events==[('read',0x401,2)] and current['total_cycles']==control['total_cycles']==6
                        and current['outcome']==control['outcome'])
                    item=dict(opcode=opcode,operand=value,flags=flags,exact=exact,
                        observed=events,total=current['total_cycles'],outcome=current['outcome'])
                    steady.append(item)
                    if args.require_immediates:assert exact,item
    proof=dict(passed_directed_immediate_cases=all(item['exact']for item in results),cases=results,
        steady_immediate_regression_cases=steady,
        baseline_outcomes_are_regression_controls_not_exhaustive_semantic_oracle=True,
        baseline_ELF_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest() if args.baseline else None,
        opcode_counterexample=dict(exact=opcode_exact,outcome=result['outcome'],total=result['total_cycles'],
            expected_PC=0x600,expected_total=18,expected_stack=0x7d),
        ELF_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),
        real_guest_write_and_real_native_JIT=True,simulated_DSP_echo=False,
        absolute_epoch_implemented=False,full_instruction_fetch_coherence_proved=False,
        native_performance_claim=False,commercial_data=False)
    if args.require_immediates:assert not opcode_exact,'Opcode guard changed; requalify this directed limit'
    print('SPC_LIVE_IMMEDIATE producer_cases='+str(len(results))+' steady_cases='+str(len(steady))+' opcode_guard='+str(opcode_exact))
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
