#!/usr/bin/env python3
"""Directed real-JIT branch and bit bus sequences, outcomes and cache replay."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run


def cases(live_relative=False):
    result=[]
    def add(name,code,total,events,flags=0x24,values=(),memory=None,registers=None,pc=None,y=6):
        expected_registers=dict(apu_accum=0x11,apu_reg_x=4,apu_reg_y=y,apu_stack=0x7f,apu_flags=flags)
        expected_registers.update(registers or {})
        expected_memory=dict(values);expected_memory.update(memory or {})
        result.append(dict(name=name,code=code.hex(),total=total,events=events,flags=flags,
            values=values,memory=expected_memory,registers=expected_registers,
            PC=0x400+len(code) if pc is None else pc,y=y))

    for name,op,mask,when_set in (
        ('BPL',0x10,0x80,False),('BMI',0x30,0x80,True),
        ('BVC',0x50,0x40,False),('BVS',0x70,0x40,True),
        ('BCC',0x90,1,False),('BCS',0xb0,1,True),
        ('BNE',0xd0,2,False),('BEQ',0xf0,2,True)):
        for taken in (False,True):
            flags=0x24|(mask if taken==when_set else 0)
            displacement=5 if taken else 0x80
            add(name+'_'+str(taken),bytes((op,displacement)),4 if taken else 2,[],
                flags=flags,pc=0x407 if taken else 0x402)
    for displacement in (5,0x80):
        signed=displacement if displacement<128 else displacement-256
        add('BRA_'+str(signed),bytes((0x2f,displacement)),4,[],pc=0x402+signed)
    for bit in range(8):
        mask=1<<bit
        for is_bbs in (False,True):
            for taken in (False,True):
                value=mask if taken==is_bbs else 0
                op=(3 if is_bbs else 0x13)+bit*32
                add(('BBS' if is_bbs else 'BBC')+str(bit)+'_'+str(taken),bytes((op,0x40,5)),
                    7 if taken else 5,[('read',0x140,3)],values=((0x140,value),),pc=0x408 if taken else 0x403)
    for indexed in (False,True):
        for taken in (False,True):
            add('CBNE_'+str(indexed)+'_'+str(taken),bytes((0xde if indexed else 0x2e,0x3c if indexed else 0x40,5)),
                (6 if indexed else 5)+(2 if taken else 0),[('read',0x140,4 if indexed else 3)],
                values=((0x140,0x12 if taken else 0x11),),pc=0x408 if taken else 0x403)
    for value in (0,1,2):
        changed=(value-1)&255;taken=changed!=0
        add('DBNZ_dp_'+str(value),bytes((0x6e,0x40,5)),7 if taken else 5,
            [('read',0x140,3),('write',0x140,4)]+([('read',0x402,5)] if live_relative else []),values=((0x140,value),),
            memory={0x140:changed},pc=0x408 if taken else 0x403)
        add('DBNZ_Y_'+str(value),bytes((0xfe,5)),6 if taken else 4,[('read',0x401,2)],
            registers=dict(apu_reg_y=changed),pc=0x407 if taken else 0x402,y=value)

    for bit in (0,7):
        mask=1<<bit;operand=0x345|(bit<<13)
        for mode,op in enumerate((0x0a,0x2a,0x4a,0x6a,0x8a,0xaa,0xca,0xea)):
            for carry in (0,1):
                for value in (0xa5,0x5a):
                    selected=bool(value&mask);new_carry=carry;changed=value
                    if mode==0:new_carry=carry|selected
                    elif mode==1:new_carry=carry|(not selected)
                    elif mode==2:new_carry=carry&selected
                    elif mode==3:new_carry=carry&(not selected)
                    elif mode==4:new_carry=carry^selected
                    elif mode==5:new_carry=int(selected)
                    elif mode==6:changed=(value&~mask)|(carry<<bit)
                    else:changed=value^mask
                    cycles=(5,5,4,4,5,4,6,5)[mode]
                    events=[('read',0x345,4)]
                    if mode>=6:events.append(('write',0x345,cycles))
                    add('absolute_bit_'+str((mode,bit,carry,value)),bytes((op,operand&255,operand>>8,0x2f,0)),
                        cycles+4,events,flags=0x24|carry,values=((0x345,value),),
                        memory={0x345:changed},registers=dict(apu_flags=0x24|int(new_carry)))
    for bit in range(8):
        for setting in (False,True):
            for value in (0,0xa5):
                changed=value|(1<<bit) if setting else value&~(1<<bit)
                add('direct_bit_'+str((bit,setting,value)),bytes(((2 if setting else 0x12)+bit*32,0x40,0x2f,0)),8,
                    [('read',0x140,3),('write',0x140,4)],values=((0x140,value),),memory={0x140:changed})
    for setting in (False,True):
        for value in (0x11,0x12,0x80,0xff):
            comparison=(0x11-value)&255
            flags=0x25|(0x80 if comparison&128 else 0)|(2 if comparison==0 else 0)
            changed=value|0x11 if setting else value&~0x11
            add('test_bits_'+str((setting,value)),bytes((0x0e if setting else 0x4e,0x45,3,0x2f,0)),10,
                [('read',0x345,4),('read',0x345,5),('write',0x345,6)],flags=0x25,
                values=((0x345,value),),memory={0x345:changed},registers=dict(apu_flags=flags))
    for increment in (False,True):
        for writing in (False,True):
            op=(0xaf if writing else 0xbf) if increment else (0xc6 if writing else 0xe6)
            events=[('read',0x401,2)]
            if not increment or not writing:events.append(('read',0x104,3))
            if writing:events.append(('write',0x104,4))
            changed_registers=dict(apu_reg_x=5 if increment else 4)
            if not writing:changed_registers['apu_accum']=0x35
            add('X_indirect_'+str((increment,writing)),bytes((op,0x2f,0)),
                (4 if increment or writing else 3)+4,events,values=((0x104,0x35),),
                memory={0x104:0x11 if writing else 0x35},registers=changed_registers)
    add('OR_X_Y',bytes.fromhex('192f00'),9,
        [('read',0x401,2),('read',0x106,3),('read',0x104,4),('write',0x104,5)],
        values=((0x104,0x12),(0x106,0x34)),memory={0x104:0x36})
    add('CMP_X_Y',bytes.fromhex('792f00'),9,
        [('read',0x401,2),('read',0x106,3),('read',0x104,4)],
        values=((0x104,0x12),(0x106,0x34)),registers=dict(apu_flags=0xa4))
    add('CMP_dp_dp',bytes.fromhex('6940412f00'),10,
        [('read',0x140,3),('read',0x141,5)],values=((0x140,0x33),(0x141,0x11)),registers=dict(apu_flags=0xa4))
    add('CMP_dp_imm',bytes.fromhex('7833402f00'),9,
        [('read',0x140,4)],values=((0x140,0x11),),registers=dict(apu_flags=0xa4))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--require-exact',action='store_true')
    args=parser.parse_args();base,symbols=load_elf(args.elf);results=[]
    for case in cases('apu_dbnz_runtime_relative' in symbols):
        y=case['y']
        result=run(base,symbols,bytes.fromhex(case['code']),observe_data=True,
            memory_values=case['values'],flags=case['flags'],test_pc=0x400,
            extra_setup=lambda cpu,s,y=y:cpu.write(s['apu_reg_y'],y,1))
        observed=[(event['kind'],event['address'],event['elapsed_master_cycles']//21)for event in result['events']]
        exact=(observed==case['events'] and result['total_cycles']==case['total']
            and result['outcome']['PC']==case['PC'] and result['outcome']['registers']==case['registers']
            and all(result['outcome']['memory'][hex(address)]==value for address,value in case['memory'].items()))
        item=dict(name=case['name'],exact=exact,observed=observed,expected=case['events'],
            total=result['total_cycles'],expected_total=case['total'],outcome=result['outcome'],
            expected_PC=case['PC'],expected_registers=case['registers'],expected_memory=case['memory'],
            cached_replay_exact=result['cached_replay_exact'])
        results.append(item)
        if not exact:print('OPEN '+json.dumps(item))
        if args.require_exact:assert exact,item
    proof=dict(passed=all(item['exact']for item in results),cases=results,
        ELF_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        full_256_opcode_bus_accuracy_proved=False,native_performance_claim=False,commercial_data=False)
    print('SPC_BRANCH_BIT cases='+str(len(results))+' exact='+str(sum(item['exact']for item in results)))
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
