#!/usr/bin/env python3
"""Actual native JIT word bus order, direct-page wrap and carry/borrow results."""
import argparse,hashlib,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--require-exact',action='store_true')
    p.add_argument('--mutations',action='store_true')
    a=p.parse_args();base,s=load_elf(a.elf);results=[]
    cases=[
      ('MOVW_read','baff2ffc',9,[('read',0x1ff,3),('read',0x100,5)],(0x35,0x12),{},dict(apu_accum=0x35,apu_reg_y=0x12,apu_flags=0x20)),
      ('MOVW_write','daff2ffc',9,[('read',0x1ff,3),('write',0x1ff,4),('write',0x100,5)],(0,0),{'0x1ff':0x11,'0x100':6},dict(apu_flags=0x20)),
      ('ADDW','7aff2ffc',9,[('read',0x1ff,3),('read',0x100,5)],(0x35,0x12),{},dict(apu_accum=0x46,apu_reg_y=0x18,apu_flags=0x20)),
      ('SUBW','9aff2ffc',9,[('read',0x1ff,3),('read',0x100,5)],(0x35,0x12),{},dict(apu_accum=0xdc,apu_reg_y=0xf3,apu_flags=0xa8)),
      ('CMPW','5aff2ffc',8,[('read',0x1ff,3),('read',0x100,4)],(0x35,0x12),{},dict(apu_accum=0x11,apu_reg_y=6,apu_flags=0xa0)),
      ('INCW_carry_wrap','3aff2ffc',10,[('read',0x1ff,3),('write',0x1ff,4),('read',0x100,5),('write',0x100,6)],(255,255),{'0x1ff':0,'0x100':0},dict(apu_flags=0x22)),
      ('DECW_borrow_wrap','1aff2ffc',10,[('read',0x1ff,3),('write',0x1ff,4),('read',0x100,5),('write',0x100,6)],(0,0),{'0x1ff':255,'0x100':255},dict(apu_flags=0xa0)),
    ]
    for adjust,opcode in ((1,'3a'),(-1,'1a')):
        for value in (0,1,0xff,0x100,0x7fff,0x8000,0xfffe,0xffff):
            result=(value+adjust)&65535
            psw=0x20|(2 if not result else 0)|(0x80 if result&0x8000 else 0)
            cases.append(('word_modify_'+str(adjust)+'_'+hex(value),opcode+'ff2ffc',10,
                [('read',0x1ff,3),('write',0x1ff,4),('read',0x100,5),('write',0x100,6)],
                (value&255,value>>8),{'0x1ff':result&255,'0x100':result>>8},dict(apu_flags=psw)))
    for name,code,total,expected,values,memory,registers in cases:
        r=run(base,s,bytes.fromhex(code),observe_data=True,memory_values=((0x1ff,values[0]),(0x100,values[1]),(0x200,0xa7)),flags=0x20,test_pc=0x400)
        observed=[(v['kind'],v['address'],v['elapsed_master_cycles']//21)for v in r['events']]
        exact=observed==expected and r['total_cycles']==total
        exact=exact and all(r['outcome']['memory'][k]==v for k,v in memory.items())
        exact=exact and r['outcome']['memory']['0x200']==0xa7
        exact=exact and all(r['outcome']['registers'][k]==v for k,v in registers.items())
        item=dict(name=name,exact=exact,observed=observed,expected=expected,total=r['total_cycles'],outcome=r['outcome'],expected_memory=memory,expected_registers=registers)
        results.append(item);print(name+(' EXACT 'if exact else ' OPEN ')+json.dumps(item))
        if a.require_exact:assert exact,item
    rejected=[]
    if a.mutations:
        def mutate(c,s,pc,kind):
            begin=c.read(s['jit_lookup']+pc*4)+12;end=c.read(s['jit_pointer'])
            # Cached/uncached aliases share the physical instruction owner.
            wanted=0x308400ff if kind=='omit_page_mask' else 0x0c000000|((s['apu_write8']>>2)&0x3ffffff)
            matches=[at for at in range(begin,(end-0x20000000)&0xffffffff,4)if c.read(at)==wanted]
            assert matches,kind;c.write(matches[0],0)
        for name,code in (('omit_page_mask','baff2ffc'),('omit_low_write','3aff2ffc')):
            r=run(base,s,bytes.fromhex(code),observe_data=True,memory_values=((0x1ff,255),(0x100,255),(0x200,0xa7)),flags=0x20,test_pc=0x400,
                  jit_mutation=lambda c,s,pc,name=name:mutate(c,s,pc,name))
            if name=='omit_page_mask':assert r['outcome']['registers']['apu_reg_y']!=255
            else:assert len(r['events'])!=4 or r['total_cycles']!=10
            rejected.append(name)
    proof=dict(passed=all(x['exact']for x in results),cases=results,
        rejected_emitted_instruction_mutations=rejected,
        ELF_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest(),
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        native_performance_claim=False,full_256_opcode_bus_accuracy_proved=False,commercial_data=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
