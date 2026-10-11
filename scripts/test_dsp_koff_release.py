#!/usr/bin/env python3
"""Linked KOFF latch, per-sample release, real DSP/APU callers; synthetic data."""
import argparse, hashlib, json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU, signed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--legacy-elf',type=Path,required=True)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args()
    memory,s=load_elf(args.elf);cpu=CPU(memory)
    assert 'release_mode' in s
    def put(name,value,n=4,offset=0):cpu.write(s[name]+offset,value,n)
    def read(name,n=4,offset=0):return cpu.read(s[name]+offset,n)
    def addresses(name,offset,n):return {(s[name]+offset+i)&0x1fffffff for i in range(n)}
    def touched():return {a+i for a,n,value in cpu.memory_writes for i in range(n)}
    def initialize(timer=19):
        put('enabled',255,1);put('dsp_timer',timer,2)
        for voice in range(8):
            put('mode_funcs',s['attack_mode'],offset=16*voice)
            put('next_steps',0x4567,2,16*voice)
            put('envelopes',257+voice,2,16*voice)
            put('cached_vols',0x12345678,offset=16*voice)
    def write_mask(mask,entry='write_dspdata'):
        put('dsp_addr',0x5c,1);cpu.pattern();cpu.regs[5]=mask
        if entry=='apu_write8':cpu.regs[4]=0xf3;cpu.regs[19]=1000
        initial=cpu.regs.copy()
        cpu.memory_writes.clear();cpu.cp_writes.clear()
        cpu.execute(s[entry])
        assert all(cpu.regs[i]==initial[i] for i in range(32)
                   if i not in (1,8,9,10,11,14,15,19))
    masks=0
    for mask in range(256):
        timer=0 if mask&1 else 19
        initialize(timer)
        enabled=(mask*73+91)&255;put('enabled',enabled,1)
        write_mask(mask)
        owned=addresses('dsp_regs',0x5c,1)
        for voice in range(8):
            selected=bool(mask&(1<<voice));offset=16*voice
            assert read('mode_funcs',offset=offset)==s['release_mode' if selected else 'attack_mode']
            assert read('next_steps',2,offset)==((timer-1)%0x7800 if selected else 0x4567)
            assert read('envelopes',2,offset)==257+voice
            assert read('cached_vols',offset=offset)==0x12345678
            if selected:owned|=addresses('mode_funcs',offset,4)|addresses('next_steps',offset,2)
        assert read('enabled',1)==enabled and touched()==owned
        assert not cpu.cp_writes
        masks+=1

    envelope_cases=0;maximum=0
    for voice in range(8):
        for envelope in range(2048):
            offset=16*voice;timer=(envelope*37)%0x7800
            put('envelopes',envelope,2,offset);put('enabled',255,1)
            put('dsp_regs',0xa5,1,offset);put('dsp_regs',0x4b,1,offset+1)
            cpu.pattern();cpu.regs[14]=voice;cpu.regs[24]=offset
            cpu.regs[28]=timer;cpu.regs[29]=255
            initial=cpu.regs.copy();cpu.memory_writes.clear();cpu.cp_writes.clear()
            observed='dsp_release_steps' in s
            cache_unused='dsp_dry_skip_vol_cache' in s
            cached_before=read('cached_vols',offset=offset)
            if observed:
                if envelope==0:put('dsp_release_steps',0xffffffff)
                before_steps=read('dsp_release_steps')
            before=cpu.steps;cpu.execute(s['release_mode']);maximum=max(maximum,cpu.steps-before-1)
            expected=max(0,envelope-8)
            assert read('envelopes',2,offset)==expected
            assert read('next_steps',2,offset)==(timer-1)%0x7800
            if cache_unused:
                assert read('cached_vols',offset=offset)==cached_before
            else:
                assert signed(read('cached_vols',2,offset),16)==-91*(expected>>4)
                assert signed(read('cached_vols',2,offset+2),16)==75*(expected>>4)
            assert read('enabled',1)==(255&~(1<<voice) if not expected else 255)
            owned=addresses('envelopes',offset,2)|addresses('next_steps',offset,2)
            if not cache_unused:owned|=addresses('cached_vols',offset,4)
            if not expected:owned|=addresses('enabled',0,1)
            if observed:
                owned|=addresses('dsp_release_steps',0,4)|addresses('dsp_release_last',0,4)
                assert read('dsp_release_steps')==(before_steps+1)&0xffffffff
                assert read('dsp_release_last')==(voice<<24)|(envelope<<12)|expected
            assert touched()==owned
            assert all(cpu.regs[i]==initial[i] for i in range(32) if i not in (1,8,9,10,11,29))
            assert not cpu.cp_writes
            envelope_cases+=1

    # Execute the actual sample scheduler repeatedly, including timer wrap.
    sample_calls=0
    for voice in range(8):
        initialize(0);put('enabled',1<<voice,1);put('envelopes',2047,2,16*voice)
        put('audio_set',4,1);put('noise_step',0xffff,2);put('dsp_pointer',0,2)
        put('dsp_regs',0,1,0x3d)
        if 'dsp_pitches' in s:put('dsp_pitches',0,2,16*voice)
        put('dsp_regs',0,1,16*voice+2);put('dsp_regs',0,1,16*voice+3)
        put('counters',0,2,16*voice)
        put('cur_samples',10000,2,8*voice+6)
        write_mask(1<<voice)
        for sample in range(1,259):
            cpu.pattern();cpu.execute(s['dsp_sample'],stop=s['apu_execute'])
            expected=max(0,2047-8*sample)
            assert read('envelopes',2,16*voice)==expected
            assert read('enabled',1)==(1<<voice if expected else 0)
            assert read('dsp_timer',2)==(-sample)%0x7800
            sample_calls+=1

    # ADSR writes during release cannot resurrect attack/gain.
    protected_writes=0
    for voice in range(8):
        for value in (0,0x7f,0x80,0xff):
            initialize();write_mask(1<<voice)
            put('dsp_addr',16*voice+5,1)
            cpu.pattern();cpu.regs[5]=value;cpu.memory_writes.clear()
            cpu.execute(s['write_dspdata'])
            assert read('mode_funcs',offset=16*voice)==s['release_mode']
            assert touched()==addresses('dsp_regs',16*voice+5,1)
            protected_writes+=1

    # Actual KON state reset and dispatch, stopping before unchanged legacy
    # rate scheduling (its DIV instruction is outside this scalar VM).
    restarts=0
    for voice in range(8):
        for adsr in (0,0x8f):
            initialize();write_mask(1<<voice);put('enabled',0,1)
            put('dsp_regs',0x20,1,0x5d);put('dsp_regs',0,1,16*voice+4)
            put('apu_ram',0x0040,2,0x2000)
            put('dsp_regs',adsr,1,16*voice+5);put('dsp_regs',3,1,16*voice+7)
            put('dsp_addr',0x4c,1);cpu.pattern();cpu.regs[5]=1<<voice
            cpu.execute(s['write_dspdata'],stop=s['attack_time' if adsr else 'gain_time'])
            assert read('enabled',1)==1<<voice
            assert read('mode_funcs',offset=16*voice)==s['attack_mode' if adsr else 'gain_mode']
            assert read('cur_addrs',2,16*voice)==0x4000
            assert read('envelopes',2,16*voice)==0
            restarts+=1

    # Production APU port handling still owns tag changes and cycle debit.
    caller_cases=0
    for mask in (0,1,2,4,8,16,32,64,128,255):
        initialize();put('apu_clock',21,1);put('jit_tags',0x12345678,offset=12)
        write_mask(mask,'apu_write8')
        assert cpu.regs[19]==979 and read('jit_tags',offset=12)==0x12345679
        assert read('apu_ram',1,0xf3)==mask and read('dsp_regs',1,0x5c)==mask
        assert read('enabled',1)==255
        caller_cases+=1
    invalid=0
    for addr in range(128,256):
        put('dsp_addr',addr,1);cpu.pattern();cpu.regs[5]=255
        cpu.memory_writes.clear();cpu.execute(s['write_dspdata']);assert not cpu.memory_writes
        invalid+=1

    # Known legacy failure: KOFF immediately removes selected active voices.
    legacy,ls=load_elf(args.legacy_elf);old=CPU(legacy)
    old.write(ls['enabled'],255,1);old.write(ls['dsp_addr'],0x5c,1)
    old.pattern();old.regs[5]=0x55;old.execute(ls['write_dspdata'])
    assert old.read(ls['enabled'],1)==0xaa
    initialize();write_mask(0x55);assert read('enabled',1)==255

    mutations=[]
    for name,imm,replacement,env,timer in (
            ('release_decrement',0xfff8,0xfff9,2047,5),
            ('release_timer_wrap',0x7800,0x7801,24,0)):
        matches=[pc for pc in range(s['release_mode'],s['read_dspaddr'],4)
                 if cpu.read(pc)>>26==9 and cpu.read(pc)&65535==imm]
        assert len(matches)==1
        pc=matches[0];original=cpu.read(pc);cpu.write(pc,(original&~65535)|replacement)
        put('envelopes',env,2);cpu.pattern();cpu.regs[14]=0;cpu.regs[24]=0
        cpu.regs[28]=timer;cpu.regs[29]=255;cpu.execute(s['release_mode'])
        assert read('envelopes',2)!=max(0,env-8) or read('next_steps',2)!=(timer-1)%0x7800
        cpu.write(pc,original);mutations.append(name)
    result=dict(passed=True,koff_masks=masks,release_voice_cases=envelope_cases,
                actual_dsp_sample_calls=sample_calls,protected_adsr_writes=protected_writes,
                actual_kon_restarts=restarts,
                actual_apu_port_callers=caller_cases,invalid_addresses=invalid,
                maximum_release_handler_instructions=maximum,negative_mutations_rejected=mutations,
                no_immediate_koff_voice_disable=True,per_sample_release_and_timer_wrap=True,
                arithmetic_reference='Snes9x1.63 SPC_DSP::run_envelope release branch',
                kon_delay_and_every_other_sample_latching_qualified=False,
                full_envelope_mixing_or_dac_fidelity_claim=False,commercial_data=False,
                elf_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest())
    if args.json_output:args.json_output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
