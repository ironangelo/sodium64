#!/usr/bin/env python3
"""Real-JIT stack/control bus sequences, wrap, PC and stack results."""
import argparse,hashlib,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--require-exact',action='store_true')
    p.add_argument('--mutations',action='store_true')
    a=p.parse_args();base,s=load_elf(a.elf);cases=[]
    for name,op,value in (('PUSH_A','2d',17),('PUSH_X','4d',4),('PUSH_Y','6d',6),('PUSH_P','0d',0)):
        cases.append((name,op+'2ffd',8,0x7f,[('read',0x401,2),('write',0x17f,3)],((0x17f,0xa5),),{0x17f:value},dict(apu_stack=0x7e),0x400))
    for name,op,reg in (('POP_A','ae','apu_accum'),('POP_X','ce','apu_reg_x'),('POP_Y','ee','apu_reg_y'),('POP_P','8e','apu_flags')):
        cases.append((name,op+'2ffd',8,0x7f,[('read',0x401,2),('read',0x180,4)],((0x180,0x35),),{},dict(apu_stack=0x80,**{reg:0x35}),0x400))
    cases += [
      ('CALL','3f0006',8,0x7f,[('write',0x17f,5),('write',0x17e,6)],((0x17f,0xa5),(0x17e,0xa5)),{0x17f:4,0x17e:3},dict(apu_stack=0x7d),0x600),
      ('PCALL','4f34',6,0x7f,[('write',0x17f,4),('write',0x17e,5)],((0x17f,0xa5),(0x17e,0xa5)),{0x17f:4,0x17e:2},dict(apu_stack=0x7d),0xff34),
      ('TCALL','01',8,0x7f,[('read',0x401,2),('write',0x17f,4),('write',0x17e,5),('read',0xffde,7),('read',0xffdf,8)],((0xffde,0),(0xffdf,6),(0x17f,0xa5),(0x17e,0xa5)),{0x17f:4,0x17e:1},dict(apu_stack=0x7d),0x600),
      ('RET','6f',5,0x7f,[('read',0x401,2),('read',0x180,4),('read',0x181,5)],((0x180,0),(0x181,6)),{},dict(apu_stack=0x81),0x600),
      ('RETI','7f',6,0x7f,[('read',0x401,2),('read',0x180,4),('read',0x181,5),('read',0x182,6)],((0x180,0x21),(0x181,0),(0x182,6)),{},dict(apu_stack=0x82,apu_flags=0x21),0x600),
      ('BRK','0f',8,0x7f,[('read',0x401,2),('write',0x17f,3),('write',0x17e,4),('write',0x17d,5),('read',0xffde,7),('read',0xffdf,8)],((0xffde,0),(0xffdf,6),(0x17f,0xa5),(0x17e,0xa5),(0x17d,0xa5)),{0x17f:4,0x17e:1,0x17d:0},dict(apu_stack=0x7c,apu_flags=0x10),0x600),
      ('CALL_wrap','3f0006',8,0,[('write',0x100,5),('write',0x1ff,6)],((0x100,0xa5),(0x1ff,0xa5),(0xff,0xa5)),{0x100:4,0x1ff:3,0xff:0xa5},dict(apu_stack=0xfe),0x600),
      ('RET_wrap','6f',5,0xfe,[('read',0x401,2),('read',0x1ff,4),('read',0x100,5)],((0x1ff,0),(0x100,6),(0x200,0xa5)),{0x200:0xa5},dict(apu_stack=0),0x600),
      ('RETI_wrap','7f',6,0xfd,[('read',0x401,2),('read',0x1fe,4),('read',0x1ff,5),('read',0x100,6)],((0x1fe,0x21),(0x1ff,0),(0x100,6),(0x200,0xa5)),{0x200:0xa5},dict(apu_stack=0,apu_flags=0x21),0x600),
      ('PCALL_wrap','4f34',6,0,[('write',0x100,4),('write',0x1ff,5)],((0x100,0xa5),(0x1ff,0xa5),(0xff,0xa5)),{0x100:4,0x1ff:2,0xff:0xa5},dict(apu_stack=0xfe),0xff34),
      ('TCALL_wrap','01',8,0,[('read',0x401,2),('write',0x100,4),('write',0x1ff,5),('read',0xffde,7),('read',0xffdf,8)],((0xffde,0),(0xffdf,6),(0x100,0xa5),(0x1ff,0xa5),(0xff,0xa5)),{0x100:4,0x1ff:1,0xff:0xa5},dict(apu_stack=0xfe),0x600),
      ('BRK_wrap_first','0f',8,0,[('read',0x401,2),('write',0x100,3),('write',0x1ff,4),('write',0x1fe,5),('read',0xffde,7),('read',0xffdf,8)],((0xffde,0),(0xffdf,6),(0x100,0xa5),(0x1ff,0xa5),(0x1fe,0xa5),(0xff,0xa5)),{0x100:4,0x1ff:1,0x1fe:0,0xff:0xa5},dict(apu_stack=0xfd,apu_flags=0x10),0x600),
      ('BRK_wrap_second','0f',8,1,[('read',0x401,2),('write',0x101,3),('write',0x100,4),('write',0x1ff,5),('read',0xffde,7),('read',0xffdf,8)],((0xffde,0),(0xffdf,6),(0x101,0xa5),(0x100,0xa5),(0x1ff,0xa5),(0xff,0xa5)),{0x101:4,0x100:1,0x1ff:0,0xff:0xa5},dict(apu_stack=0xfe,apu_flags=0x10),0x600),
    ]
    for vector in range(1,16):
        address=0xffde-vector*2;target=0x600+vector*2
        cases.append(('TCALL_'+str(vector),bytes((1+vector*16,)).hex(),8,0x7f,
            [('read',0x401,2),('write',0x17f,4),('write',0x17e,5),('read',address,7),('read',address+1,8)],
            ((address,target&255),(address+1,target>>8),(0x17f,0xa5),(0x17e,0xa5)),
            {0x17f:4,0x17e:1},dict(apu_stack=0x7d),target))
    results=[]
    for name,code,total,sp,expected,values,memory,registers,pc in cases:
        expected_registers=dict(apu_accum=0x11,apu_reg_x=4,apu_reg_y=6,apu_stack=sp,apu_flags=0)
        expected_registers.update(registers)
        for clock in (1,21,42,255):
            for pointer in (0xa01c0000,0xa01fff80):
                r=run(base,s,bytes.fromhex(code),clock=clock,jit_pointer=pointer,
                      observe_data=True,memory_values=values,stack=sp,test_pc=0x400)
                observed=[(v['kind'],v['address'],v['elapsed_master_cycles']//clock)for v in r['events']]
                exact=observed==expected and r['total_cycles']==total and r['outcome']['PC']==pc
                exact=exact and all(r['outcome']['memory'][hex(k)]==v for k,v in memory.items())
                exact=exact and r['outcome']['registers']==expected_registers
                item=dict(name=name,clock=clock,requested_JIT_pointer=hex(pointer),exact=exact,
                    observed=observed,expected=expected,total=r['total_cycles'],expected_total=total,
                    outcome=r['outcome'],expected_registers=expected_registers,
                    cached_replay_exact=r['cached_replay_exact'],reset_exercised=r['reset_exercised'])
                results.append(item)
                if a.require_exact:assert exact,item
        print(name+(' EXACT'if all(x['exact']for x in results if x['name']==name)else' OPEN'))
    rejected=[]
    if a.mutations:
        assert a.require_exact
        def mutate(c,s,pc,kind):
            begin=c.read(s['jit_lookup']+pc*4)+12
            end=(c.read(s['jit_pointer'])-0x20000000)&0xffffffff
            wanted=0x34040401 if kind=='wrong_dummy_PC' else 0x00882025 # ORI A0,0,$401 / OR A0,A0,T0
            matches=[at for at in range(begin,end,4)if c.read(at)==wanted]
            assert len(matches)==1,(kind,matches)
            c.write(matches[0],0x34040402 if kind=='wrong_dummy_PC' else 0)
        for kind,code,sp,values in (
            ('wrong_dummy_PC','2d2ffd',0x7f,((0x17f,0xa5),)),
            ('omit_stack_page_restore','3f0006',0,((0x100,0xa5),(0x1ff,0xa5),(0xff,0xa5)))):
            r=run(base,s,bytes.fromhex(code),observe_data=True,memory_values=values,stack=sp,test_pc=0x400,
                  jit_mutation=lambda c,s,pc,kind=kind:mutate(c,s,pc,kind))
            if kind=='wrong_dummy_PC':assert r['events'][0]['address']!=0x401
            else:assert r['outcome']['memory']['0x1ff']!=3
            rejected.append(kind)
    proof=dict(passed=all(x['exact']for x in results),cases=results,
        rejected_emitted_instruction_mutations=rejected,
        ELF_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest(),
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        full_256_opcode_bus_accuracy_proved=False,native_performance_claim=False,commercial_data=False)
    print('SPC_BUS_CONTROL cases='+str(len(results))+' resets='+str(sum(x['reset_exercised']for x in results))+' rejected_mutants='+str(len(rejected)))
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
