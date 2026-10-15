#!/usr/bin/env python3
"""Observe real compiled SPC JIT bus timestamps with the existing MIPS VM."""
import argparse,json
from pathlib import Path
from test_native_diag_continuous import CPU,signed
from test_native_diag_arm import load_elf

def run(base,symbols,code,clock=21,jit_pointer=0xa01c0000):
    cpu=CPU(base.copy());s=symbols;start=1000000;events=[]
    cpu.regs[16]=0x200;cpu.regs[19]=start;cpu.regs[7]=0
    cpu.write(s['apu_count'],0x200,2);cpu.write(s['apu_clock'],clock,1)
    cpu.write(s['apu_flags'],0,1);cpu.write(s['apu_accum'],0x11,1)
    cpu.write(s['apu_reg_x'],4,1);cpu.write(s['apu_reg_y'],6,1)
    cpu.write(s['apu_stack'],0x7f,1);cpu.write(s['apu_halt'],0,1)
    cpu.write(s['apu_map']+0x3ff,0,1)
    cpu.write(s['dsp_addr'],0x2d,1);cpu.write(s['dsp_regs']+0x2d,0x55,1)
    cpu.write(s['jit_pointer'],jit_pointer)
    for i,b in enumerate(code):cpu.write(s['apu_ram']+0x200+i,b,1)
    observe_callbacks={}
    for name,kind in [('read_dspdata','read'),('write_dspdata','write')]:
        pc=s[name]
        def observe(c,pc=pc,kind=kind):
            events.append(dict(kind=kind,elapsed_master_cycles=start-signed(c.regs[19],32),
                               data=c.regs[5]&255 if kind=='write' else None))
            c.before_instruction[pc]=observe_callbacks[pc]
        observe_callbacks[pc]=observe;cpu.before_instruction[pc]=observe
    cpu.execute(s['compile_block'],stop=s['cpu_execute'])
    total=(start-signed(cpu.regs[19],32))//clock
    pointer=cpu.read(s['jit_lookup']+0x200*4);first=list(events)
    cpu.write(s['apu_count'],0x200,2);cpu.regs[19]=start;cpu.regs[7]=0;events.clear()
    cpu.execute(s['apu_execute'],stop=s['cpu_execute'])
    assert cpu.read(s['jit_lookup']+0x200*4)==pointer
    assert events==first and (start-signed(cpu.regs[19],32))//clock==total
    assert all(0x1c0000<=(at&0x1fffffff)<0x200000 for op,at in cpu.cache_ops)
    return dict(events=first,total_cycles=total,cached_replay_exact=True,clock=clock,
                requested_JIT_pointer=hex(jit_pointer),published_header=hex(pointer),
                reset_exercised=jit_pointer>0xa01c0000 and (pointer&0x1fffffff)<0x1fff80)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--ordered',action='store_true')
    p.add_argument('--mutations',action='store_true')
    a=p.parse_args();base,s=load_elf(a.elf)
    cases=[('mov_a_dp','e4f32ffc',7,[('read',3)]),
           ('nop_nop_mov_a_dp','0000e4f32ffa',11,[('read',7)]),
           ('mov_dp_a','c4f32ffc',8,[('read',3),('write',4)]),
           ('mov_dp_imm','8f33f32ffb',9,[('read',4),('write',5)])]
    results=[]
    for name,code,total,expected in cases:
        for clock in (1,21,42,255):
            for pointer in (0xa01c0000,0xa01fff80):
                r=run(base,s,bytes.fromhex(code),clock,pointer);assert r['total_cycles']==total,(name,r)
                observed=[(x['kind'],x['elapsed_master_cycles']//clock)for x in r['events']]
                if a.ordered:assert observed==expected,(name,'bus timestamp/order mismatch',r)
                else:assert observed!=expected,(name,'baseline unexpectedly exact',r)
                r.update(name=name,expected_bus_end_cycles=expected,observed_bus_end_cycles=observed)
                results.append(r)
    print('SPC_BUS_CLOCK PASS cases='+str(len(results))+' cached_replay=exact resets='+str(sum(x['reset_exercised']for x in results)))
    for r in results:
        if r['clock']==21 and r['requested_JIT_pointer']=='0xa01c0000':print(r['name'],json.dumps(r['observed_bus_end_cycles']))
    rejected=[]
    if a.mutations:
        assert a.ordered
        for name in ('omit_prefix','retain_debited_prefix'):
            memory=base.copy();pc=s['emit_jal_guest_bus']&0x1fffffff
            if name=='omit_prefix':
                word=int.from_bytes(bytes(memory[pc+i]for i in range(4)),'big')
                word=0x10000000|(word&65535) # always take the real skip branch
            else:
                pc=(s['emit_jal_clock_ready']-4)&0x1fffffff
                word=0 # omit MOVE S2,ZERO in the bounds-branch delay slot
            memory.update((pc+i,v)for i,v in enumerate(word.to_bytes(4,'big')))
            r=run(memory,s,bytes.fromhex('c4f32ffc'))
            observed=[(x['kind'],x['elapsed_master_cycles']//21)for x in r['events']]
            assert observed!=[('read',3),('write',4)]or r['total_cycles']!=8
            rejected.append(name)
    proof=dict(passed=True,status='IMPLEMENTED directed bus-clock prefix' if a.ordered else 'REJECTED direct mid-block S3 as DSP timestamp',
        actual_linked_JIT_compiler_and_emitted_code=True,existing_MIPS_VM_used=True,
        cases=results,aggregate_cycle_totals_and_cached_replay_preserved=True,
        rejected_linked_instruction_mutations=rejected,
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        runtime_timing_bridge_implemented=False,full_256_opcode_bus_accuracy_proved=False,
        native_performance_claim=False,commercial_data=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
