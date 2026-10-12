#!/usr/bin/env python3
"""Independent timer modulus, linked handlers, owners and negative mutations."""
import argparse,hashlib,json,random
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU

RATES=(65535,2048,1536,1280,1024,768,640,512,384,320,256,192,160,128,96,80,
       64,48,40,32,24,20,16,12,10,8,6,5,4,3,2,1)
OFFSETS=(32768,0,1040,536,0,1040,536,0,1040,536,0,1040,536,0,1040,536,
         0,1040,536,0,1040,536,0,1040,536,0,1040,536,0,1040,0,0)

class CountingCPU(CPU):
    # These handlers never read code as data. The only read of this address
    # during execute is instruction fetch, including a real branch delay slot.
    divide_pc=None
    recording=False
    divides=0
    def read(self,address,size=4):
        if self.recording and size==4 and (address&0x1fffffff)==self.divide_pc:self.divides+=1
        return super().read(address,size)

def expected(timer,rate):
    base=(timer-1)%30720
    target=base-(base+OFFSETS[rate])%RATES[rate]
    if target<0:target+=30720
    return target&65535

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path);p.add_argument('--reference-elf',type=Path,required=True)
    p.add_argument('--json-output',type=Path);a=p.parse_args()
    models=[(CountingCPU(m),s) for m,s in (load_elf(a.reference_elf),load_elf(a.elf))]
    assert 'dsp_timer_fast' not in models[0][1] and 'dsp_timer_fast' in models[1][1]
    for c,s in models:
        assert 'dsp_dry_skip_vol_cache' in s
        assert [c.read(s['timer_rates']+4*i) for i in range(32)]==[(r<<16)|o for r,o in zip(RATES,OFFSETS)]
    exhaustive=0
    for rate,period in enumerate(RATES):
        mask=period-1
        for timer in range(30720):
            value=(timer-1)%30720+OFFSETS[rate]
            remainder=value&mask if not period&mask else value if value<period else value%period
            assert remainder==value%period
            exhaustive+=1
    rng=random.Random(0xd535)
    timers=sorted({0,1,2,3,19,511,512,1023,1024,1535,1536,2047,2048,30718,30719,
                   *[rng.randrange(30720) for _ in range(17)]})
    totals=[0,0];maxima=[0,0];compiled=0
    for c,s in models:
        sites=[pc for pc in range(s['update_step'],s['update_vols'],4)
               if c.read(pc)>>26==0 and c.read(pc)&63 in (26,27)]
        assert len(sites)==1
        c.divide_pc=sites[0]&0x1fffffff
    def run(c,s,timer,rate,voice):
        c.write(s['dsp_timer'],timer,2)
        c.pattern();c.regs[4]=rate*4;c.regs[14]=voice
        before=c.regs.copy();c.memory_writes.clear();c.cp_writes.clear()
        start=c.steps;c.enforce_hilo_spacing=True;c.recording=True
        try:c.execute(s['update_step'],max_steps=100)
        finally:c.recording=False
        field=s['noise_step'] if voice==8 else s['next_steps']+16*voice
        assert c.read(field,2)==expected(timer,rate),(timer,rate,voice,c.read(field,2),expected(timer,rate))
        assert {addr+i for addr,size,_ in c.memory_writes for i in range(size)}=={(field+i)&0x1fffffff for i in range(2)}
        assert all(c.regs[i]==before[i] for i in range(32) if i not in (1,4,8,9,10,11)),('new register clobber',timer,rate,voice)
        assert not c.cp_writes
        return c.steps-start-1
    for timer in timers:
        for rate in range(32):
            for voice in range(9):
                for i,(c,s) in enumerate(models):
                    steps=run(c,s,timer,rate,voice);totals[i]+=steps;maxima[i]=max(maxima[i],steps)
                compiled+=1
    compiled_divides=[c.divides for c,s in models]
    assert compiled_divides[0]==compiled and compiled_divides[1]<compiled
    c,s=models[1];mutations=[]
    for name,timer,rate,voice,transform in (
        ('dsp_timer_power2',19,31,7,lambda w:(w&~63)|37),
        ('dsp_timer_small_remainder',19,0,8,lambda w:(9<<26)|(11<<16)),
        ('dsp_timer_divide',1600,2,3,lambda w:(w&~((31<<21)|(31<<16)))|((w>>16&31)<<21)|((w>>21&31)<<16))):
        pc=s[name];old=c.read(pc);c.write(pc,transform(old));rejected=False
        try:run(c,s,timer,rate,voice)
        except AssertionError:rejected=True
        finally:c.write(pc,old)
        assert rejected,('mutation escaped',name);mutations.append(name)
    result=dict(passed=True,independent_all_legal_timer_rate_pairs=exhaustive,
        actual_paired_handler_cases=compiled,all32_linked_rate_offset_words=True,
        voice_and_noise_owners=9,only_selected_next_deadline_bytes_written=True,
        unrelated_GPR64_stereo_accumulators_CP0_preserved=True,
        HI_LO_are_handler_scratch_and_not_claimed_identical=True,
        instructions_total_reference_optimized=totals,maximum_handler_instructions=maxima,
        actual_divide_executions_reference_optimized=compiled_divides,
        negative_mutations_rejected=mutations,native_speed_or_complete_audio_claim=False,
        commercial_data=False,reference_ELF_sha256=hashlib.sha256(a.reference_elf.read_bytes()).hexdigest(),
        optimized_ELF_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest())
    if a.json_output:a.json_output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
