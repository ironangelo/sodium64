#!/usr/bin/env python3
"""Real-JIT PC and effective-address edges of the 16-bit SPC address space."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--require-exact',action='store_true')
    parser.add_argument('--mutations',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();base,symbols=load_elf(args.elf)
    cases=[
        ('BRA_wrap',0xfffe,'2f00',4,0,[],(),0,{}),
        ('BRA_negative',0,'2f80',4,0xff82,[],(),0,{}),
        ('BNE_wrap_taken',0xfffe,'d000',4,0,[],(),0,{}),
        ('BNE_wrap_fallthrough',0xfffe,'d000',2,0,[],(),2,{}),
        ('BNE_negative',0,'d080',4,0xff82,[],(),0,{}),
        ('NOP_wrap',0xffff,'00',2,0,[('read',0,2)],(),0,{}),
        ('MOV_imm_operand_wrap',0xffff,'e8352f00',2,1,[],(),0,dict(apu_accum=0x35)),
        ('PCALL_operand_wrap',0xffff,'4f34',6,0xff34,[('write',0x17f,4),('write',0x17e,5)],
            ((0x17f,0xa5),(0x17e,0xa5)),0,dict(apu_stack=0x7d)),
        ('CALL_return_wrap',0xfffd,'3f0006',8,0x600,[('write',0x17f,5),('write',0x17e,6)],
            ((0x17f,0xa5),(0x17e,0xa5)),0,dict(apu_stack=0x7d)),
        ('JMP_pointer_wrap',0x400,'1ffbff',6,0x600,[('read',0xffff,5),('read',0,6)],
            ((0xffff,0),(0,6)),0,{}),
        ('absolute_X_wrap',0x400,'f5fcff2f00',9,0x405,[('read',0,5)],((0,0x35),),0,dict(apu_accum=0x35)),
        ('absolute_Y_wrap',0x400,'f6faff2f00',9,0x405,[('read',0,5)],((0,0x35),),0,dict(apu_accum=0x35)),
        ('indirect_Y_wrap',0x400,'f7402f00',10,0x404,[('read',0x40,4),('read',0x41,5),('read',0,6)],
            ((0x40,0xfa),(0x41,0xff),(0,0x35)),0,dict(apu_accum=0x35)),
        ('NOP_sequence_wrap',0xfffe,'0000',4,0,[('read',0xffff,2),('read',0,4)],(),0,{}),
        ('MOV_imm_end_wrap',0xfffe,'e835',2,0,[],(),0,dict(apu_accum=0x35)),
        ('absolute_X_write_wrap',0x400,'d5fcff2f00',10,0x405,[('read',0,5),('write',0,6)],((0,0x35),),0,{}),
        ('absolute_Y_write_wrap',0x400,'d6faff2f00',10,0x405,[('read',0,5),('write',0,6)],((0,0x35),),0,{}),
        ('indirect_Y_write_wrap',0x400,'d7402f00',11,0x404,[('read',0x40,3),('read',0x41,4),('read',0,6),('write',0,7)],
            ((0x40,0xfa),(0x41,0xff),(0,0x35)),0,{}),
    ]
    for name,op,mask,when_set in (
        ('BPL',0x10,0x80,False),('BMI',0x30,0x80,True),('BVC',0x50,0x40,False),
        ('BVS',0x70,0x40,True),('BCC',0x90,1,False),('BCS',0xb0,1,True),('BEQ',0xf0,2,True)):
        for taken in (False,True):
            flags=mask if taken==when_set else 0
            cases.append((name+'_wrap_'+str(taken),0xfffe,bytes((op,0)).hex(),4 if taken else 2,0,[],(),flags,{}))
        cases.append((name+'_negative',0,bytes((op,0x80)).hex(),4,0xff82,[],(),mask if when_set else 0,{}))
    for name,code,total,events,values,changed in (
        ('BBC_negative','134080',7,[('read',0x40,3)],((0x40,0),),{}),
        ('BBS_negative','034080',7,[('read',0x40,3)],((0x40,1),),{}),
        ('CBNE_negative','2e4080',7,[('read',0x40,3)],((0x40,0x12),),{}),
        ('CBNE_X_negative','de3c80',8,[('read',0x40,4)],((0x40,0x12),),{}),
        ('DBNZ_dp_negative','6e4080',7,[('read',0x40,3),('write',0x40,4)],((0x40,2),),{}),
        ('DBNZ_Y_negative','fe80',6,[('read',1,2)],(),dict(apu_reg_y=5))):
        cases.append((name,0,code,total,0xff83 if len(bytes.fromhex(code))==3 else 0xff82,events,values,0,changed))
    results=[]
    for name,pc,code,total,next_pc,expected,values,flags,changed in cases:
        if name in ('MOV_imm_operand_wrap','MOV_imm_end_wrap') and 'apu_imm_runtime_fetch' in symbols:
            expected=[('read',(pc+1)&65535,2)]
        registers=dict(apu_accum=0x11,apu_reg_x=4,apu_reg_y=6,apu_stack=0x7f,apu_flags=flags)
        registers.update(changed)
        try:
            def tags(cpu,s):
                header=cpu.read(s['jit_lookup']+pc*4)
                return dict(first=cpu.read(header,2),last=cpu.read(header+2,2))
            result=run(base,symbols,bytes.fromhex(code),test_pc=pc,observe_data=True,
                memory_values=values,flags=flags,extra_outcome=tags)
            observed=[(event['kind'],event['address'],event['elapsed_master_cycles']//21)for event in result['events']]
            source_end=1 if name=='MOV_imm_operand_wrap' else (pc+len(bytes.fromhex(code)))&65535
            expected_tags=dict(first=(pc>>6)*4,last=(source_end>>6)*4)
            expected_memory=dict(values)
            if name=='PCALL_operand_wrap':expected_memory.update({0x17f:0,0x17e:1})
            elif name=='CALL_return_wrap':expected_memory.update({0x17f:0,0x17e:0})
            elif name=='DBNZ_dp_negative':expected_memory[0x40]=1
            elif '_write_wrap' in name:expected_memory[0]=0x11
            exact=(observed==expected and result['total_cycles']==total
                and result['outcome']['PC']==next_pc and result['outcome']['registers']==registers
                and result['outcome']['extra']==expected_tags
                and all(result['outcome']['memory'][hex(address)]==value for address,value in expected_memory.items()))
            item=dict(name=name,exact=exact,observed=observed,expected=expected,
                total=result['total_cycles'],expected_total=total,outcome=result['outcome'],
                expected_PC=next_pc,expected_registers=registers,expected_tag_offsets=expected_tags,
                expected_memory=expected_memory,
                cached_replay_exact=result['cached_replay_exact'])
        except Exception as error:
            if args.require_exact:raise
            item=dict(name=name,exact=False,error=type(error).__name__+': '+str(error)[:1000])
        results.append(item)
        if not item['exact']:print('OPEN '+json.dumps(item))
        if args.require_exact:assert item['exact'],item
    rejected=[]
    if args.mutations:
        assert args.require_exact
        for kind in ('omit_fetch_PC_wrap','omit_wrap_block_boundary'):
            memory=base.copy()
            if kind=='omit_fetch_PC_wrap':
                begin=symbols['jit_read8'];end=symbols['jit_charge_cycles']
                wanted=0x3084ffff
                matches=[at for at in range(begin,end,4)
                    if int.from_bytes(bytes(memory[(at+i)&0x1fffffff]for i in range(4)),'big')==wanted]
                assert len(matches)==1;at=matches[0]
            else:at=symbols['finish_opcode']+4 # BNE after the wrap-test SLTU
            memory.update(((at+i)&0x1fffffff,0)for i in range(4))
            result=run(memory,symbols,b'\x00',test_pc=0xffff,observe_data=True)
            assert result['total_cycles']!=2 or result['outcome']['PC']!=0,(kind,result)
            rejected.append(kind)
        def omit_pointer_wrap(cpu,s,pc):
            begin=cpu.read(s['jit_lookup']+pc*4)+12
            end=(cpu.read(s['jit_pointer'])-0x20000000)&0xffffffff
            matches=[at for at in range(begin,end,4)if cpu.read(at)==0x3084ffff]
            assert len(matches)==2 # first effective address and second pointer-byte address
            cpu.write(matches[-1],0)
        result=run(base,symbols,bytes.fromhex('1ffbff'),test_pc=0x400,observe_data=True,
            memory_values=((0xffff,0),(0,6)),jit_mutation=omit_pointer_wrap)
        assert result['events'][-1]['address']!=0 or result['outcome']['PC']!=0x600
        rejected.append('omit_pointer_byte_wrap')
    proof=dict(passed=all(item['exact']for item in results),cases=results,
        rejected_linked_or_emitted_mutations=rejected,
        ELF_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        full_256_opcode_bus_accuracy_proved=False,native_performance_claim=False,commercial_data=False)
    print('SPC_BUS_WRAP cases='+str(len(results))+' exact='+str(sum(item['exact']for item in results))+' rejected_mutants='+str(len(rejected)))
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
