#!/usr/bin/env python3
"""Execute the actual pause-only GAIN probe; prove restoration and ABI owners."""
import argparse,hashlib,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path);p.add_argument('--expect-clobber',action='store_true')
    p.add_argument('--json-output',type=Path);a=p.parse_args()
    memory,s=load_elf(a.elf);c=CPU(memory);c.enforce_hilo_spacing=True
    assert 'dsp_dry_skip_vol_cache' in s
    cases=0
    for voice in range(8):
        for gain in range(256):
            offset=16*voice
            for name,value,size in (('envelopes',(gain*17)&2047,2),('next_steps',gain*131,2),('cached_vols',0xf1234567,4)):
                c.write(s[name]+offset,value,size)
            c.write(s['dsp_regs']+offset+7,gain^255,1);c.write(s['dsp_timer'],(gain*997)%0x7800,2)
            before_regs=c.blob(s['dsp_regs'],128);before_voice=c.blob(s['mode_funcs'],128)
            c.pattern();c.regs[4]=voice;c.regs[5]=gain;c.regs[6]=0x80600000
            before=c.regs.copy();c.memory_writes.clear();c.cp_writes.clear()
            c.execute(s['remote_dsp_gain_probe'])
            assert c.regs[2]==1
            assert c.read(0x80600000)==0x1357
            assert c.read(0x80600004)==(offset if a.expect_clobber else 0x2468)
            assert c.blob(s['dsp_regs'],128)==before_regs and c.blob(s['mode_funcs'],128)==before_voice
            assert all(c.regs[i]==before[i] for i in (*range(16,24),28,29,30,31))
            assert not c.cp_writes
            owned=set(range(0x600000,0x600008))
            stack=(before[29]-64)&0x1fffffff;owned.update(range(stack,stack+64))
            owned.add((s['dsp_regs']+offset+7)&0x1fffffff)
            for name,size in (('cached_vols',4),('envelopes',2),('next_steps',2)):
                start=(s[name]+offset)&0x1fffffff;owned.update(range(start,start+size))
            touched={addr+i for addr,size,_ in c.memory_writes for i in range(size)}
            assert touched<=owned,('probe wrote outside owner',touched-owned)
            cases+=1
    for voice,gain in ((8,0),(0xffffffff,0),(0,256),(0,0xffffffff)):
        c.pattern();c.regs[4]=voice;c.regs[5]=gain;c.regs[6]=0x80600000
        c.memory_writes.clear();c.execute(s['remote_dsp_gain_probe'])
        assert c.regs[2]==0 and not c.memory_writes
    proof={'passed':True,'actual_probe_calls':cases,'invalid_inputs_rejected_without_writes':4,
           'DSP_registers_and_voice_state_restored':True,'callee_saved_GPR64_restored':True,
           'only_selected_fields_results_and_owned_stack_written':True,
           'accumulator_clobber_expected':a.expect_clobber,'not_native_waveform_or_performance':True,
           'commercial_data':False,'elf_sha256':hashlib.sha256(a.elf.read_bytes()).hexdigest()}
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
