#!/usr/bin/env python3
"""Execute all four linked BRR filters against independent integer arithmetic.

The oracle follows the Snes9x1.63 SPC_DSP decode_brr contract. It uses raw,
original synthetic nibbles and half-scaled history; it is not a DAC model.
"""
import argparse,hashlib,json,random
from pathlib import Path
from linked_cpu_regression import CPU, load_elf, signed

def reference(nibbles,shift,filter,p1,p2):
    result=[]
    for nibble in nibbles:
        value=(nibble<<shift)//2 if shift<=12 else (-2048 if nibble<0 else 0)
        full_previous=p1*2
        if filter==1:
            value+=full_previous//2 + (-full_previous)//32
        elif filter==2:
            value+=full_previous-p2+p2//16+(-3*full_previous)//64
        elif filter==3:
            value+=full_previous-p2+(-13*full_previous)//128+(3*p2)//16
        value=max(-32768,min(32767,value))
        half=signed(value*2,16)//2
        result.append(half);p1,p2=half,p1
    return result

def cases():
    result=[]
    for shift in range(16):
        for filter in range(4):
            for nibble in range(-8,8):
                for p1,p2 in ((0,0),(1,-1),(-1,1),(16383,-16384),(-16384,16383)):
                    result.append(([nibble]*4,shift,filter,p1,p2))
    rng=random.Random(0xb22)
    for _ in range(2048):
        result.append(([rng.randrange(-8,8) for _ in range(4)],rng.randrange(16),
                       rng.randrange(4),rng.randrange(-16384,16384),rng.randrange(-16384,16384)))
    return result

def run(cpu,s,case,voice=0):
    ns,shift,filter,p1,p2=case
    packed=sum((n&15)<<(12-4*i) for i,n in enumerate(ns))
    cpu.write(s['apu_ram']+0x200,(shift<<4)|(filter<<2),1)
    cpu.write(s['apu_ram']+0x201,packed,2)
    buffer=s['cur_samples']+8*voice
    for offset,value in ((0,p1),(2,p2),(4,0),(6,0)):cpu.write(buffer+offset,value,2)
    cpu.pattern();cpu.regs[8]=0x200;cpu.regs[10]=0
    cpu.regs[14]=voice;cpu.regs[24]=16*voice+(s['mode_funcs'] if 'dsp_voice_base' in s else 0)
    initial=cpu.regs.copy();hi,lo=cpu.hi,cpu.lo
    observed='dsp_brr_records' in s
    if observed:
        next_slot=cpu.read(s['dsp_brr_next']);completed=cpu.read(s['dsp_brr_count'])
    cpu.memory_writes.clear();cpu.cp_writes.clear()
    before=cpu.steps
    cpu.execute(s['decode_samples'],stop=s['mix_sample'],max_steps=500)
    owned={(buffer+i)&0x1fffffff for i in range(8)}
    owned.update((s['cur_addrs']+16*voice+i)&0x1fffffff for i in range(2))
    if observed:
        record=s['dsp_brr_records']+16*next_slot
        owned.update((record+i)&0x1fffffff for i in range(16))
        for name in ('dsp_brr_next','dsp_brr_count'):
            owned.update((s[name]+i)&0x1fffffff for i in range(4))
    touched={a+i for a,n,v in cpu.memory_writes for i in range(n)}
    assert touched==owned,('decoder wrote outside voice state',touched^owned)
    clobbers={1,3,8,9,11,15,16,17,25}
    assert all(cpu.regs[i]==initial[i] for i in range(32) if i not in clobbers)
    assert (cpu.hi,cpu.lo)==(hi,lo) and not cpu.cp_writes
    out=[signed(cpu.read(buffer+i,2),16) for i in (6,4,2,0)]
    if observed:
        assert cpu.read(record)==(voice<<24)|(((shift<<4)|(filter<<2))<<16)|packed
        assert cpu.read(record+4)==((p1&65535)<<16)|(p2&65535)
        assert [signed(cpu.read(record+8+2*i,2),16) for i in range(4)]==out[::-1]
        assert cpu.read(s['dsp_brr_next'])==(next_slot+1)&31
        assert cpu.read(s['dsp_brr_count'])==(completed+1)&0xffffffff
    return out,cpu.steps-before-1

def mutate(cpu,start,end,predicate,transform):
    candidates=[pc for pc in range(start,end,4) if predicate(cpu.read(pc))]
    assert len(candidates)==1,(hex(start),len(candidates))
    pc=candidates[0];old=cpu.read(pc);cpu.write(pc,transform(old))
    return pc,old

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path);parser.add_argument('--legacy-elf',type=Path)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args()
    memory,s=load_elf(args.elf);cpu=CPU(memory)
    if args.legacy_elf:
        legacy,ls=load_elf(args.legacy_elf);previous=CPU(legacy)
    assert 'brr_range_ready' in s and 'brr_clamped' in s
    if args.legacy_elf: assert 'brr_range_ready' not in ls
    data=cases();compiled=0;maximum=0;legacy_mismatch=[0]*4
    for case in data:
        expected=reference(*case)
        if args.legacy_elf:
            old,_=run(previous,ls,case)
            legacy_mismatch[case[2]]+=int(old!=expected)
        for voice in range(8):
            actual,steps=run(cpu,s,case,voice)
            assert actual==expected,(voice,case,actual,expected)
            compiled+=1;maximum=max(maximum,steps)
    if args.legacy_elf: assert legacy_mismatch==[321,1730,1778,1831]
    mutations=[
        ('signed_filter_floor',s['filter_1'],s['filter_2'],
         lambda w:w==((15<<16)|(15<<11)|35),lambda w:0,
         ([-8]*4,0,1,1,-1)),
        ('invalid_range_mask',s['decode_samples'],s['next_sample'],
         lambda w:w>>26==12 and w&0xffff==0x8888,lambda w:(w&~0xffff)|0xffff,
         ([1,4,-7,-1],13,0,0,0)),
        ('saturation',s['filter_end'],s['end_voice'],
         lambda w:w>>26==14 and w&0xffff==0x7fff,lambda w:(w&~0xffff)|0x7ffe,
         ([7]*4,12,2,16383,-16384)),
        ('signed_15bit_storage',s['filter_end'],s['end_voice'],
         lambda w:w>>26==0 and w&63==0 and w>>6&31==17,
         lambda w:(w&~(31<<6))|(16<<6),
         ([7]*4,12,1,16383,0))]
    rejected=[]
    for name,start,end,predicate,transform,case in mutations:
        pc,old=mutate(cpu,start,end,predicate,transform)
        actual,_=run(cpu,s,case,7)
        assert actual!=reference(*case),('mutation escaped independent oracle',name)
        cpu.write(pc,old);rejected.append(name)
    proof=dict(passed=True,compiled_voice_cases=compiled,synthetic_blocks=len(data),
               legacy_different_blocks_by_filter=legacy_mismatch,
               negative_mutations_rejected=rejected,maximum_decoder_instructions=maximum,
               only_voice_samples_and_current_address_written='dsp_brr_records' not in s,
               only_voice_state_and_optional_trace_owned_bytes_written=True,
               unrelated_gprs_hi_lo_cp0_preserved=True,
               range_filter_rounding_and_storage_match_reference=True,
               oracle_reference='Snes9x1.63 SPC_DSP decode_brr',
               external_cpp_reference_executed_here=False,
               native_trace_fields_checked='dsp_brr_records' in s,
               physical_audio_fidelity_claim=False,commercial_data=False,
               elf_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest(),
               legacy_elf_sha256=hashlib.sha256(args.legacy_elf.read_bytes()).hexdigest() if args.legacy_elf else None)
    if args.json_output:args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2),flush=True)

if __name__=='__main__':main()
