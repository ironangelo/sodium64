#!/usr/bin/env python3
"""Independent full-scheduler stereo oracle for due GAIN envelopes."""
import argparse,hashlib,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU
from test_dsp_dry_mix import voice_reference,output_reference

def envelope_after(env,gain):
    if gain<128:return gain*16
    mode=gain&96
    if mode==0:return max(0,env-32)
    if mode==32:return max(0,env-1-(env-1)//256)
    if mode==64:return min(2047,env+32)
    return min(2047,env+(32 if env<1536 else 8))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--expect-bug',action='store_true');p.add_argument('--json-output',type=Path)
    a=p.parse_args();memory,s=load_elf(a.elf);c=CPU(memory);c.enforce_hilo_spacing=True
    def put(name,value,size=4,offset=0):c.write(s[name]+offset,value,size)
    cases=0;different=0
    for due_voice in range(8):
        for gain in range(256):
            put('enabled',255,1);put('audio_set',4,1);put('dsp_timer',100,2)
            put('dsp_pointer',0x200,2);put('noise_step',65535,2)
            put('dsp_regs',0,1,61);put('dsp_regs',96,1,12);put('dsp_regs',96,1,28);put('dsp_regs',0,1,108)
            expected_env=envelope_after(1024,gain)
            accum=(0,0)
            for voice in range(8):
                put('envelopes',1024,2,16*voice);put('mode_funcs',s['gain_mode'],4,16*voice)
                put('next_steps',99 if voice==due_voice else 65535,2,16*voice)
                put('dsp_regs',gain if voice==due_voice else 64,1,16*voice+7)
                put('dsp_regs',64,1,16*voice);put('dsp_regs',64,1,16*voice+1)
                put('counters',0,2,16*voice);put('dsp_pitches',0,2,16*voice)
                for index in range(4):put('cur_samples',1000,2,8*voice+2*index)
                accum=voice_reference(1000,expected_env if voice==due_voice else 1024,64,64,accum)
            expected=output_reference(accum,96,96,False)
            c.pattern();c.memory_writes.clear();c.cp_writes.clear()
            c.execute(s['dsp_sample'],stop=s['apu_execute'])
            assert c.read(s['envelopes']+16*due_voice,2)==expected_env
            word=c.read(s['dsp_buffer']+0x200)
            packed=(expected[0]&65535)<<16 | (expected[1]&65535)
            mismatch=word!=packed
            if not a.expect_bug:assert not mismatch,(due_voice,gain,hex(word),hex(packed))
            if a.expect_bug:assert mismatch==(due_voice!=0)
            different+=mismatch;cases+=1
            assert not c.cp_writes
    caller_cases=0
    if not a.expect_bug:
        for voice in range(8):
            for gain in range(256):
                offset=16*voice
                put('dsp_regs',gain,1,offset+7);put('dsp_addr',offset+5,1)
                put('mode_funcs',s['attack_mode'],4,offset);put('envelopes',1024,2,offset)
                put('dsp_timer',100,2);put('apu_clock',21,1);put('jit_tags',0x12345678,4,12)
                c.pattern();c.regs[4]=0xf3;c.regs[5]=0;c.regs[19]=1000
                c.cp_writes.clear();c.execute(s['apu_write8'])
                assert c.regs[19]==979 and c.read(s['jit_tags']+12)==0x12345679
                assert c.read(s['apu_ram']+0xf3,1)==0
                assert c.read(s['dsp_regs']+offset+5,1)==0
                assert c.read(s['mode_funcs']+offset)==s['gain_mode']
                assert c.read(s['envelopes']+offset,2)==(gain*16 if gain<128 else 1024)
                if gain<128:assert c.read(s['next_steps']+offset,2)==65535
                assert not c.cp_writes
                caller_cases+=1
    proof={'passed':True,'actual_scheduler_samples':cases,'due_voices':8,'GAIN_values':256,
           'actual_APU_ADSR_to_GAIN_writes':caller_cases,'APU_debit_and_dirty_tag_preserved':not a.expect_bug,
           'direct_and_four_custom_envelope_modes':True,'independent_expected_stereo':True,
           'stereo_mismatches':different,'old_bug_expected':a.expect_bug,
           'Gaussian_echo_register_timing_and_waveform_not_qualified':True,'commercial_data':False,
           'elf_sha256':hashlib.sha256(a.elf.read_bytes()).hexdigest()}
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
