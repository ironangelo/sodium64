#!/usr/bin/env python3
"""Execute pitch-byte dispatch and cached loads; original synthetic DSP state only."""
import argparse, hashlib, json, random
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_v4 import execute, sx

class Tracked(dict):
    def __setitem__(self,key,value):
        self.writes.add(key)
        super().__setitem__(key,value)

def put(memory,address,value,n=1):
    address &= 0x1fffffff
    for i,b in enumerate((value & ((1<<(8*n))-1)).to_bytes(n,'big')):
        dict.__setitem__(memory,address+i,b)

def get(memory,address,n=1):
    address &= 0x1fffffff
    return int.from_bytes(bytes(memory.get(address+i,0) for i in range(n)),'big')

def registers():
    r=[sx(0x13570000+i*37) for i in range(32)]
    r[0]=0;r[31]=sx(0xdead0000)
    return r

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path);p.add_argument('--json-output',type=Path)
    p.add_argument('--reference-elf',type=Path,required=True)
    a=p.parse_args()
    base,s=load_elf(a.elf);memory=Tracked(base);memory.writes=set()
    assert 'dsp_pitches' in s and 'write_pitch' in s
    assert bytes(base[(s['dsp_pitches']&0x1fffffff)+i] for i in range(128))==bytes(128)
    # Execute the full writer: duplicate local write_iomap names need not be
    # resolved, and the actual DSP table dispatch is covered.
    write_cases=0;load_cases=0;invalid_cases=0
    def write(voice,which,value,old_lo,old_hi,expected):
        addr=16*voice+2+which
        put(memory,s['dsp_addr'],addr)
        put(memory,s['dsp_regs']+16*voice+2,old_lo)
        put(memory,s['dsp_regs']+16*voice+3,old_hi)
        put(memory,s['dsp_pitches']+16*voice,0xdead,2)
        r=registers();r[5]=value;initial=r.copy();memory.writes.clear()
        steps=execute(memory,s['write_dspdata'],r,{})
        assert get(memory,s['dsp_regs']+addr)==value
        assert get(memory,s['dsp_pitches']+16*voice,2)==expected
        owned={(s['dsp_regs']+addr)&0x1fffffff}
        owned.update(((s['dsp_pitches']+16*voice)&0x1fffffff)+i for i in range(2))
        assert memory.writes==owned,('unexpected write',memory.writes^owned)
        assert all(r[i]==initial[i] for i in range(32) if i not in (1,8,9,10))
        return steps
    maximum=0
    # Each byte's other-byte/value Cartesian product is exhausted. Rotating
    # voice indexing covers all dispatch slots while exercising the same code.
    for other in range(256):
        for value in range(256):
            voice=(other+value)&7
            maximum=max(maximum,write(voice,0,value,other^0x5a,other,
                                     ((other<<8)|value)&0x3fff))
            maximum=max(maximum,write(voice,1,value,other,other^0xa5,
                                     ((value<<8)|other)&0x3fff))
            write_cases+=2
    # Execute the preceding uncached conversion against the same full range;
    # compare the actual linked result to independent little-endian arithmetic.
    reference,rs=load_elf(a.reference_elf)
    assert 'dsp_pitches' not in rs
    put(reference,rs['dsp_addr'],2)
    reference_regs=registers();reference_regs[5]=0xff
    previous_write_steps=execute(reference,rs['write_dspdata'],reference_regs,{})
    assert previous_write_steps==15
    reference_cases=0
    for raw in range(65536):
        voice=raw&7
        put(reference,rs['dsp_regs']+16*voice+2,raw&255)
        put(reference,rs['dsp_regs']+16*voice+3,raw>>8)
        r=registers();r[24]=16*voice
        steps=execute(reference,rs['get_pitch'],r,{},stop=rs['get_pitch']+28)
        assert r[8]==raw&0x3fff and steps==7
        reference_cases+=1
    # All 65536 halfword inputs through all eight strided loads. Upper pitch
    # bits are excluded by writers, so direct cached load tests use that result.
    for voice in range(8):
        for raw in range(65536):
            expected=raw&0x3fff
            put(memory,s['dsp_pitches']+16*voice,expected,2)
            r=registers();r[24]=16*voice+(s['mode_funcs'] if 'dsp_voice_base' in s else 0);initial=r.copy();memory.writes.clear()
            steps=execute(memory,s['dsp_pitch_load_begin'],r,{},
                          stop=s['dsp_pitch_load_end'])
            assert r[8]==expected and not memory.writes
            assert all(r[i]==initial[i] for i in range(32) if i!=8)
            assert steps==(1 if 'dsp_voice_base' in s else 3)
            load_cases+=1
    # Invalid register addresses preserve raw registers and cache without a
    # write handler; read mirror behavior is unaffected.
    regs_start=s['dsp_regs']&0x1fffffff
    for address in range(128,256):
        put(memory,s['dsp_addr'],address);r=registers();r[5]=0xff
        memory.writes.clear();execute(memory,s['write_dspdata'],r,{})
        assert not memory.writes
        invalid_cases+=1
    # The production APU caller owns the memory tag and master-cycle debit;
    # the DSP handler must leave them intact after a write through port F3.
    caller_cases=0
    for voice in range(8):
        for which in range(2):
            address=16*voice+2+which
            put(memory,s['dsp_addr'],address)
            put(memory,s['apu_clock'],21)
            put(memory,s['jit_tags']+12,0x12345678,4)
            r=registers();r[4]=0xf3;r[5]=0xd7;r[19]=1000
            initial=r.copy();memory.writes.clear()
            execute(memory,s['apu_write8'],r,{})
            assert r[19]==979
            assert get(memory,s['jit_tags']+12,4)==0x12345679
            assert get(memory,s['apu_ram']+0xf3)==0xd7
            assert get(memory,s['dsp_regs']+address)==0xd7
            raw=get(memory,s['dsp_regs']+16*voice+2)|(get(memory,s['dsp_regs']+16*voice+3)<<8)
            assert get(memory,s['dsp_pitches']+16*voice,2)==raw&0x3fff
            assert all(r[i]==initial[i] for i in range(32) if i not in (1,8,9,10,19))
            owned={((s['apu_ram']+0xf3)&0x1fffffff),((s['dsp_regs']+address)&0x1fffffff)}
            owned.update(((s['jit_tags']+12)&0x1fffffff)+i for i in range(4))
            owned.update(((s['dsp_pitches']+16*voice)&0x1fffffff)+i for i in range(2))
            assert memory.writes==owned
            caller_cases+=1
    # Non-pitch regular writes must not touch any cached pitch.
    regular=(4,6,7,8,9,10,11,13,14,15)
    regular_cases=0
    for voice in range(8):
        for low in regular:
            addr=16*voice+low;put(memory,s['dsp_addr'],addr)
            r=registers();r[5]=0xa5;memory.writes.clear()
            execute(memory,s['write_dspdata'],r,{})
            assert memory.writes=={regs_start+addr}
            regular_cases+=1
    # The map has special KON/KOFF/FLG entries: they are outside regular above.
    # Repeat interleaved partial updates and a read, including high-bit masking.
    rng=random.Random(0x64d5)
    interleaved=0
    for _ in range(2048):
        voice=rng.randrange(8);lo=rng.randrange(256);hi=rng.randrange(256)
        write(voice,0,lo,0x45,hi,((hi<<8)|lo)&0x3fff)
        write(voice,1,hi,lo,0x78,((hi<<8)|lo)&0x3fff)
        r=registers();put(memory,s['dsp_addr'],16*voice+3|0x80)
        memory.writes.clear();execute(memory,s['read_dspdata'],r,{})
        assert r[2]==hi and not memory.writes
        interleaved+=1
    # Remove the high-bit mask from the actual writer: a bad high byte must
    # be detected by the independent numeric oracle.
    candidates=[pc for pc in range(s['write_pitch'],s['write_pitch']+64,4)
                if get(memory,pc,4)&0xffff==0x3fff and get(memory,pc,4)>>26==12]
    assert len(candidates)==1
    pc=candidates[0];original=get(memory,pc,4)
    put(memory,pc,(original&~0xffff)|0xffff,4)
    try:
        write(7,1,0xff,0xfe,0,0x3ffe)
    except AssertionError:
        mutation_rejected=True
    else:
        mutation_rejected=False
    put(memory,pc,original,4);assert mutation_rejected
    proof=dict(passed=True,compiled_write_cases=write_cases,compiled_load_cases=load_cases,
               uncached_reference_cases=reference_cases,compiled_apu_caller_cases=caller_cases,
               invalid_write_cases=invalid_cases,regular_write_cases=regular_cases,
               interleaved_cases=interleaved,negative_mutations_rejected=1,
               sample_pitch_load_instructions=1 if 'dsp_voice_base' in s else 3,previous_pitch_load_instructions=7,
               maximum_pitch_write_instructions=maximum,only_owned_writes=True,
               previous_pitch_write_instructions=previous_write_steps,
               unrelated_registers_preserved=True,raw_readback_preserved=True,
               cache_independent_of_sample_clock=True,commercial_data=False,
               physical_acceptance=False,elf_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest(),
               reference_elf_sha256=hashlib.sha256(a.reference_elf.read_bytes()).hexdigest())
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2),flush=True)

if __name__=='__main__':main()
