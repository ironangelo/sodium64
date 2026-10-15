#!/usr/bin/env python3
"""Execute actual native BRR trace hooks, including ring/count wrap."""
import argparse,hashlib,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path);p.add_argument('--json-output',type=Path)
    a=p.parse_args();memory,s=load_elf(a.elf);cpu=CPU(memory)
    cases=0;maximum=0
    for voice in range(8):
        for slot in (0,31):
            for completed in (0,42,0xffffffff):
                cpu.write(s['dsp_brr_next'],slot);cpu.write(s['dsp_brr_count'],completed)
                cpu.write(s['cur_addrs']+16*voice,0x203,2)
                cpu.write(s['apu_ram']+0x203,0xfb,1)
                cpu.write(s['cur_samples']+8*voice,0x1234fedc)
                cpu.pattern();cpu.regs[14]=voice;cpu.regs[24]=16*voice+(s['mode_funcs'] if 'dsp_voice_base' in s else 0)
                cpu.regs[3]=(s['cur_samples']+8*voice)&0xffffffff
                cpu.regs[16]=0x9abc
                initial=cpu.regs.copy();hi,lo=cpu.hi,cpu.lo
                cpu.memory_writes.clear();cpu.cp_writes.clear()
                before=cpu.steps
                cpu.execute(s['dsp_brr_trace_begin'],stop=s['dsp_brr_trace_input_done'])
                record=s['dsp_brr_records']+16*slot
                assert cpu.read(record)==(voice<<24)|0xfb9abc
                assert cpu.read(record+4)==0x1234fedc
                expected={((record+i)&0x1fffffff) for i in range(8)}
                actual={base+i for base,n,v in cpu.memory_writes for i in range(n)}
                assert actual==expected
                assert all(cpu.regs[i]==initial[i] for i in range(32) if i not in (1,8,11,15))
                assert (cpu.hi,cpu.lo)==(hi,lo) and not cpu.cp_writes
                cpu.write(s['cur_samples']+8*voice,0x98765432)
                cpu.write(s['cur_samples']+8*voice+4,0xfedcba98)
                cpu.pattern();cpu.regs[3]=(s['cur_samples']+8*voice)&0xffffffff
                initial=cpu.regs.copy();cpu.memory_writes.clear()
                cpu.execute(s['dsp_brr_trace_end'],stop=s['dsp_brr_trace_output_done'])
                assert cpu.read(record+8)==0x98765432 and cpu.read(record+12)==0xfedcba98
                assert cpu.read(s['dsp_brr_next'])==(slot+1)&31
                assert cpu.read(s['dsp_brr_count'])==(completed+1)&0xffffffff
                owned={((record+8+i)&0x1fffffff) for i in range(8)}
                for name in ('dsp_brr_next','dsp_brr_count'):
                    owned.update((s[name]+i)&0x1fffffff for i in range(4))
                actual={base+i for base,n,v in cpu.memory_writes for i in range(n)}
                assert actual==owned
                assert all(cpu.regs[i]==initial[i] for i in range(32) if i not in (1,8,11,15))
                assert (cpu.hi,cpu.lo)==(hi,lo) and not cpu.cp_writes
                maximum=max(maximum,cpu.steps-before-2);cases+=1
    proof=dict(passed=True,compiled_hook_pairs=cases,maximum_pair_instructions=maximum,
               only_trace_slot_and_counter_writes=True,pcm_ai_and_guest_state_untouched=True,
               unrelated_gprs_hi_lo_cp0_preserved=True,ring_and_count_wrap=True,
               physical_fidelity_claim=False,elf_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest())
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2),flush=True)
if __name__=='__main__':main()
