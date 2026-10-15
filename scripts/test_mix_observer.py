#!/usr/bin/env python3
"""Execute linked selected-sample init/input/commit hooks and ownership gates."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path);parser.add_argument('--json-output',type=Path)
    args=parser.parse_args();memory,s=load_elf(args.elf);cpu=CPU(memory)
    cases=0;selected_extra=0;ordinary_extra=0
    def span(name,offset,n):return {(s[name]+offset+i)&0x1fffffff for i in range(n)}
    def touched():return {address+i for address,n,value in cpu.memory_writes for i in range(n)}
    def execute(first,last,allowed):
        initial=cpu.regs.copy();hi,lo=cpu.hi,cpu.lo
        cpu.memory_writes.clear();cpu.cp_writes.clear();steps=cpu.steps
        cpu.execute(s[first],stop=s[last])
        assert all(cpu.regs[i]==initial[i] for i in range(32) if i not in allowed)
        assert (cpu.hi,cpu.lo)==(hi,lo) and not cpu.cp_writes
        return cpu.steps-steps-1
    for pointer in (0,4,0xff8,0xffc,0x1000,0x1ff8,0x1ffc):
        selected=pointer in (0xffc,0x1ffc)
        cpu.write(s['dsp_pointer'],pointer,2);cpu.write(s['dsp_mix_ready'],1)
        for offset in range(0,64,4):cpu.write(s['dsp_mix_records']+offset,0x12345678)
        cpu.pattern();cpu.regs[29]=0xa5
        init_steps=execute('dsp_mix_init_begin','dsp_mix_init_end',{1,8,9})
        expected=span('dsp_mix_records',0,64)|span('dsp_mix_ready',0,4)|span('dsp_mix_enabled',0,4) if selected else set()
        assert touched()==expected
        assert cpu.read(s['dsp_mix_ready'])==(0 if selected else 1)
        if selected:
            assert cpu.blob(s['dsp_mix_records'],64)==bytes(64)
            assert cpu.read(s['dsp_mix_enabled'])==0xa5
        cases+=1
        input_steps=0
        for voice in range(8):
            cpu.pattern();cpu.regs[8]=(-32000+voice*7000)&0xffffffffffffffff
            cpu.regs[9]=voice*251;cpu.regs[10]=(-128+voice*37)&0xffffffffffffffff
            cpu.regs[11]=(127-voice*29)&0xffffffffffffffff;cpu.regs[14]=voice
            initial=cpu.regs.copy()
            steps=execute('dsp_mix_input_begin','dsp_mix_input_end',{1,15,25});input_steps+=steps
            assert touched()==(span('dsp_mix_records',voice*8,6) if selected else set())
            if selected:
                record=cpu.blob(s['dsp_mix_records']+voice*8,8)
                assert record[:2]==(initial[8]&65535).to_bytes(2,'big')
                assert record[2:4]==(initial[9]&65535).to_bytes(2,'big')
                assert record[4:6]==bytes((initial[10]&255,initial[11]&255)) and record[6:]==b'\0\0'
            cases+=1
        for completed in (0,41,0xffffffff):
            cpu.write(s['dsp_mix_count'],completed)
            cpu.write(s['dsp_regs']+12,0x80,1);cpu.write(s['dsp_regs']+28,0x7f,1);cpu.write(s['dsp_regs']+108,0xd3,1)
            cpu.pattern();cpu.regs[8]=0x7fed8123;cpu.regs[9]=pointer
            steps=execute('dsp_mix_commit_begin','dsp_mix_commit_end',{1,10,11,15,25})
            expected=set()
            if selected:
                for name in ('dsp_mix_parameters','dsp_mix_output','dsp_mix_ring_offset','dsp_mix_count','dsp_mix_ready'):expected|=span(name,0,4)
                assert cpu.read(s['dsp_mix_parameters'])==0x807f00d3
                assert cpu.read(s['dsp_mix_output'])==0x7fed8123
                assert cpu.read(s['dsp_mix_ring_offset'])==pointer
                assert cpu.read(s['dsp_mix_count'])==(completed+1)&0xffffffff
                assert cpu.read(s['dsp_mix_ready'])==1
            else:assert cpu.read(s['dsp_mix_count'])==completed
            assert touched()==expected;cases+=1
            total=init_steps+input_steps+steps
            if selected:selected_extra=max(selected_extra,total)
            else:ordinary_extra=max(ordinary_extra,total)
    proof={'passed':True,'hook_cases':cases,'selected_sample_hook_instructions':selected_extra,
           'ordinary_eight_voice_sample_hook_instructions':ordinary_extra,
           'counter_wrap_and_both_ring_halves':True,'only_observer_owned_writes':True,
           'unrelated_gprs_HI_LO_CP0_preserved':True,'physical_acceptance':False,
           'elf_sha256':hashlib.sha256(args.elf.read_bytes()).hexdigest()}
    if args.json_output:args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()
