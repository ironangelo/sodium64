#!/usr/bin/env python3
"""Real bus reads of implied SPC instructions; preserve frozen JIT outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--require-exact',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();base,symbols=load_elf(args.elf)
    baseline=load_elf(args.baseline) if args.baseline else None
    operations=(('NOP',0,2),('MOV_A_X',0x7d,2),('MOV_X_A',0x5d,2),
        ('MOV_A_Y',0xdd,2),('MOV_Y_A',0xfd,2),('MOV_X_SP',0x9d,2),('MOV_SP_X',0xbd,2),
        ('ASL_A',0x1c,2),('LSR_A',0x5c,2),('ROL_A',0x3c,2),('ROR_A',0x7c,2),
        ('DEC_A',0x9c,2),('DEC_X',0x1d,2),('DEC_Y',0xdc,2),
        ('INC_A',0xbc,2),('INC_X',0x3d,2),('INC_Y',0xfc,2),
        ('CLRP',0x20,2),('SETP',0x40,2),('EI',0xa0,3),('DI',0xc0,3),
        ('CLRC',0x60,2),('SETC',0x80,2),('NOTC',0xed,3),('CLRV',0xe0,2),
        ('XCN',0x9f,5),('DAA',0xdf,3),('DAS',0xbe,3),('MUL',0xcf,9),('DIV',0x9e,12),
        ('SLEEP',0xef,3),('STOP',0xff,3))
    results=[]
    for name,opcode,cycles in operations:
        for flags in (0,0xff,0x25):
            for prefix in (b'',bytes.fromhex('e880')):
                halted=opcode in (0xef,0xff)
                code=prefix+bytes((opcode,))+(b'' if halted else bytes.fromhex('2f00'))
                kwargs=dict(observe_data=True,test_pc=0x400,flags=flags,
                    extra_outcome=lambda cpu,s:dict(halt=cpu.read(s['apu_halt'],1)))
                result=run(base,symbols,code,**kwargs)
                expected=[('read',0x401+len(prefix),2+(2 if prefix else 0))]
                observed=[(event['kind'],event['address'],event['elapsed_master_cycles']//21)for event in result['events']]
                expected_total=cycles+(2 if prefix else 0)+(0 if halted else 4)
                same_outcome=None
                if baseline:
                    control=run(*baseline,code,**kwargs)
                    same_outcome=result['outcome']==control['outcome'] and result['total_cycles']==control['total_cycles']
                exact=observed==expected and result['total_cycles']==expected_total and same_outcome is not False
                item=dict(name=name,flags=flags,queued_NZ_prefix=bool(prefix),exact=exact,
                    observed=observed,expected=expected,total=result['total_cycles'],expected_total=expected_total,
                    outcome=result['outcome'],frozen_outcome_preserved=same_outcome,
                    cached_replay_exact=result['cached_replay_exact'])
                results.append(item)
                if args.require_exact:assert exact,item
    proof=dict(passed=all(item['exact']for item in results),cases=results,
        ELF_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),
        baseline_ELF_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest() if args.baseline else None,
        baseline_outcomes_are_regression_controls_not_exhaustive_semantic_oracle=True,
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        full_256_opcode_bus_accuracy_proved=False,native_performance_claim=False,commercial_data=False)
    print('SPC_IMPLIED cases='+str(len(results))+' exact='+str(sum(item['exact']for item in results))+
          ' frozen_outcomes_checked='+str(sum(item['frozen_outcome_preserved'] is not None for item in results)))
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
