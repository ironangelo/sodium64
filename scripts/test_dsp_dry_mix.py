#!/usr/bin/env python3
"""Execute linked dry-mix arithmetic and sample routing; synthetic inputs only."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU, signed


def s16(value):
    return (value+32768) % 65536-32768


def clamp(value):
    return max(-32768, min(32767, value))


def voice_reference(half, env, left, right, accum):
    # Independent arithmetic: full selected signal, envelope truncation,
    # even output, signed channel coefficients, ordered per-voice clipping.
    output = (s16(half*2)*env // 2048) & ~1
    return (clamp(accum[0]+output*left//128),
            clamp(accum[1]+output*right//128))


def output_reference(accum, left, right, mute):
    return (0,0) if mute else (s16(accum[0]*left//128), s16(accum[1]*right//128))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args()
    memory,symbols=load_elf(args.elf);cpu=CPU(memory)
    assert 'dsp_dry_voice_begin' in symbols and 'dsp_dry_output_begin' in symbols
    def put(name,value,size=4,offset=0):cpu.write(symbols[name]+offset,value,size)
    def result():return (signed(cpu.regs[13],32),signed(cpu.regs[12],32))
    def voice(half,env,left,right,accum,number=0):
        put('envelopes',env,2,16*number)
        put('dsp_regs',left,1,16*number);put('dsp_regs',right,1,16*number+1)
        put('dsp_pointer',0,2)
        cpu.pattern();cpu.regs[8]=half&0xffffffffffffffff
        cpu.regs[24]=16*number;cpu.regs[14]=number
        cpu.regs[13]=accum[0]&0xffffffffffffffff;cpu.regs[12]=accum[1]&0xffffffffffffffff
        before=cpu.regs.copy();cpu.memory_writes.clear();cpu.cp_writes.clear();steps=cpu.steps
        cpu.execute(symbols['dsp_dry_voice_begin'],stop=symbols['dsp_dry_voice_end'])
        assert not cpu.memory_writes and not cpu.cp_writes
        assert all(cpu.regs[i]==before[i] for i in range(32) if i not in (1,8,9,10,11,12,13,15,25))
        return result(),cpu.steps-steps-1
    def output(accum,left,right,mute):
        put('dsp_regs',left,1,12);put('dsp_regs',right,1,28);put('dsp_regs',64 if mute else 0,1,108)
        cpu.pattern();cpu.regs[13]=accum[0]&0xffffffffffffffff;cpu.regs[12]=accum[1]&0xffffffffffffffff
        before=cpu.regs.copy();cpu.memory_writes.clear();cpu.cp_writes.clear();steps=cpu.steps
        cpu.execute(symbols['dsp_dry_output_begin'],stop=symbols['dsp_dry_output_end'])
        assert not cpu.memory_writes and not cpu.cp_writes
        assert all(cpu.regs[i]==before[i] for i in range(32) if i not in (1,8,9,10,12,13))
        return result(),cpu.steps-steps-1
    halves=(-16384,-8193,-1,0,1,8191,16383,32767)
    sums=(-32768,-32767,-1024,-1,0,1,1024,32767)
    voice_cases=0;maximum_voice=0
    for env in range(2048):
        for number in range(8):
            half=halves[(env+number)&7]
            left=((env*37+number*19)&255)-128
            right=left if env&1 else ((env*53+number*71)&255)-128
            accum=(sums[(env>>3)&7],sums[(env>>6)&7])
            actual,steps=voice(half,env,left,right,accum,number)
            assert actual==voice_reference(half,env,left,right,accum),(env,number,actual)
            voice_cases+=1;maximum_voice=max(maximum_voice,steps)
    output_cases=0;maximum_output=0
    for raw in range(256):
        left=raw-128;right=((raw*73)&255)-128
        for a in sums:
            for b in sums:
                for mute in (False,True):
                    actual,steps=output((a,b),left,right,mute)
                    assert actual==output_reference((a,b),left,right,mute)
                    output_cases+=1;maximum_output=max(maximum_output,steps)
    # Execute the actual scheduler, voice selection, sample load and stereo
    # packing, not only isolated arithmetic. Pitch0 avoids an unrelated decode.
    complete_samples=0;maximum_sample=0
    for mask in (0,1,2,3,0x55,0x80,0xfe,0xff):
        for mute in (False,True):
            for seed in range(8):
                put('enabled',mask,1);put('dsp_timer',100,2);put('noise_step',0xffff,2)
                put('dsp_pointer',0x200,2);put('dsp_regs',0,1,61)
                accum=(0,0)
                for number in range(8):
                    env=(seed*251+number*67)&2047;half=halves[(seed+number)&7]
                    left=((seed*43+number*13)&255)-128;right=((seed*29+number*37)&255)-128
                    put('envelopes',env,2,number*16);put('next_steps',0xffff,2,number*16)
                    put('counters',0,2,number*16);put('cached_vols',0x6fff7eee,4,number*16)
                    if 'dsp_pitches' in symbols:put('dsp_pitches',0,2,number*16)
                    put('dsp_regs',0,2,number*16+2)
                    put('dsp_regs',left,1,number*16);put('dsp_regs',right,1,number*16+1)
                    for index in range(4):put('cur_samples',half,2,number*8+index*2)
                    if mask>>number&1:accum=voice_reference(half,env,left,right,accum)
                master=(127-seed*17,-128+seed*23)
                put('dsp_regs',master[0],1,12);put('dsp_regs',master[1],1,28);put('dsp_regs',64 if mute else 0,1,108)
                cpu.pattern();cpu.regs[7]=100000;cpu.cp_writes.clear();steps=cpu.steps
                cpu.execute(symbols['dsp_sample'],stop=symbols['apu_execute'],max_steps=3000)
                expected=output_reference(accum,*master,mute)
                packed=(expected[0]&65535)<<16 | (expected[1]&65535)
                assert cpu.read(symbols['dsp_buffer']+0x200)==packed
                assert cpu.read(symbols['dsp_pointer'],2)==0x204
                if 'dsp_dry_skip_vol_cache' in symbols:
                    for number in range(8):
                        assert cpu.read(symbols['cached_vols']+number*16)==0x6fff7eee
                assert not cpu.cp_writes
                maximum_sample=max(maximum_sample,cpu.steps-steps-1);complete_samples+=1
    # Negative mutations affect observable arithmetic or mute, not just labels.
    mutations=[
        ('envelope_scale','dsp_dry_voice_begin','dsp_dry_voice_end',lambda w:w==((8<<16)|(8<<11)|(11<<6)|3),lambda w:(w&~(31<<6))|(10<<6),lambda:voice(1000,1025,63,127,(0,0))[0],voice_reference(1000,1025,63,127,(0,0))),
        ('even_envelope_output','dsp_dry_voice_begin','dsp_dry_voice_end',lambda w:w==((8<<16)|(8<<11)|(1<<6)|3),lambda w:w&~(31<<6),lambda:voice(1,2047,127,127,(0,0))[0],voice_reference(1,2047,127,127,(0,0))),
        ('signed_channel_volume','dsp_dry_voice_begin','dsp_dry_voice_end',lambda w:w>>26==32 and w>>16&31==10,lambda w:(w&0x3ffffff)|(36<<26),lambda:voice(-1000,2047,-128,64,(0,0))[0],voice_reference(-1000,2047,-128,64,(0,0))),
        ('voice_saturation','dsp_dry_voice_begin','dsp_dry_voice_end',lambda w:w>>26==14 and w>>16&31==13 and w&65535==32767,lambda w:(w&~65535)|32766,lambda:voice(-16384,2047,-128,64,(32767,0))[0],voice_reference(-16384,2047,-128,64,(32767,0))),
        ('signed_master_volume','dsp_dry_output_begin','dsp_dry_output_end',lambda w:w>>26==32 and w>>16&31==8,lambda w:(w&0x3ffffff)|(36<<26),lambda:output((8192,-8192),-1,64,False)[0],output_reference((8192,-8192),-1,64,False)),
        ('master_scale','dsp_dry_output_begin','dsp_dry_output_end',lambda w:w==((13<<16)|(13<<11)|(7<<6)|3),lambda w:(w&~(31<<6))|(8<<6),lambda:output((32767,-8192),64,64,False)[0],output_reference((32767,-8192),64,64,False)),
        ('mute','dsp_dry_output_begin','dsp_dry_output_end',lambda w:w>>26==12 and w&65535==64,lambda w:w&~65535,lambda:output((32767,-8192),64,64,True)[0],(0,0))]
    rejected=[]
    for name,start,end,predicate,transform,run,expected in mutations:
        pcs=[pc for pc in range(symbols[start],symbols[end],4) if predicate(cpu.read(pc))]
        assert len(pcs)==1,(name,len(pcs));pc=pcs[0];old=cpu.read(pc);cpu.write(pc,transform(old))
        assert run()!=expected,'mutation escaped: '+name
        cpu.write(pc,old);rejected.append(name)
    # The real register dispatcher must immediately feed the next dry sample,
    # with no legacy cache update or other DSP write.
    volume_writes=0
    if 'dsp_dry_skip_vol_cache' in symbols:
        for number in range(8):
            for channel in (0,1):
                for raw in range(256):
                    address=number*16+channel
                    put('dsp_addr',address,1);put('cached_vols',0x12345678,4,number*16)
                    cpu.pattern();cpu.regs[5]=raw;cpu.memory_writes.clear()
                    cpu.execute(symbols['write_dspdata'])
                    assert cpu.memory_writes==[((symbols['dsp_regs']+address)&0x1fffffff,1,raw)]
                    assert cpu.read(symbols['cached_vols']+number*16)==0x12345678
                    volume_writes+=1
    proof={'passed':True,'voice_cases':voice_cases,'output_cases':output_cases,
           'actual_scheduler_samples':complete_samples,'negative_mutations_rejected':rejected,
           'actual_uncached_volume_writes':volume_writes,
           'maximum_voice_instructions':maximum_voice,'maximum_output_instructions':maximum_output,
           'maximum_scheduler_sample_instructions':maximum_sample,
           'memory_and_unrelated_registers_preserved_by_arithmetic':True,
           'reference':'Snes9x1.63 envelope/voice_output and zero-echo master contribution',
           'compiled_primary_method_executed_here':False,'full_DSP_or_DAC_fidelity_claim':False,
           'commercial_data':False,'elf_sha256':hashlib.sha256(args.elf.read_bytes()).hexdigest()}
    if args.json_output:args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()
