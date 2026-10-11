#!/usr/bin/env python3
"""Execute the actual compiled per-block AI observer; synthetic hardware only."""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_v4 import execute, sx

FIELDS=('dsp_audio_blocks','dsp_audio_idle','dsp_audio_full',
        'dsp_audio_gap_max','dsp_audio_last_count')
MASK=0xffffffff

def put(memory,address,value):
    address &= 0x1fffffff
    memory.update((address+i,b) for i,b in enumerate((value&MASK).to_bytes(4,'big')))

def get(memory,address):
    address &= 0x1fffffff
    return int.from_bytes(bytes(memory.get(address+i,0) for i in range(4)),'big')

def run(base,symbols,status,state,now,mutation=False):
    memory=base.copy()
    for name,value in zip(FIELDS,state):put(memory,symbols[name],value)
    put(memory,0xa450000c,status)
    if mutation:
        # Wrong bit shift confuses FULL with BUSY; must fail the numeric oracle.
        candidates=[pc for pc in range(symbols['dsp_audio_observe_begin'],symbols['dsp_audio_observe_end'],4)
                    if get(memory,pc)>>26==0 and get(memory,pc)&63==2 and get(memory,pc)>>6&31==31]
        assert len(candidates)==1
        pc=candidates[0]
        word=get(memory,pc)
        assert word>>26==0 and word&63==2 and word>>6&31==31
        put(memory,pc,(word&~(31<<6))|(30<<6))
    before=memory.copy()
    regs=[sx(0x13570000+i*37) for i in range(32)]
    regs[0]=0;regs[8]=sx(0xa4500000)
    initial=regs.copy()
    steps=execute(memory,symbols['dsp_audio_observe_begin'],regs,{9:now},
                  stop=symbols['dsp_audio_observe_end'])
    actual=tuple(get(memory,symbols[n]) for n in FIELDS)
    blocks,idle,full,maximum,last=state
    expected=((blocks+1)&MASK,(idle+int(not status&0x40000000))&MASK,
              (full+int(bool(status&0x80000000)))&MASK,
              max(maximum,(now-last)&MASK) if blocks else maximum,now)
    owned={((symbols[n]&0x1fffffff)+i) for n in FIELDS for i in range(4)}
    assert all(memory.get(k,0)==before.get(k,0) for k in memory.keys()|before.keys() if k not in owned)
    assert all(regs[i]==initial[i] for i in range(32) if i not in (9,10,11,12))
    return actual,expected,steps

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path);parser.add_argument('--json-output',type=Path)
    args=parser.parse_args();base,symbols=load_elf(args.elf)
    states=[((0,0,0,0,0),100),((5,2,3,200,10),100),
            ((5,2,3,20,0xfffffff0),0x20),
            ((0xffffffff,0xffffffff,0xffffffff,0,0),0x80000001)]
    cases=0;maximum_steps=0
    for status in (0,0x40000000,0x80000000,0xc0000000):
        for state,now in states:
            actual,expected,steps=run(base,symbols,status,state,now)
            assert actual==expected,(hex(status),state,actual,expected)
            cases+=1;maximum_steps=max(maximum_steps,steps)
    actual,expected,_=run(base,symbols,0x40000000,(5,0,0,0,0),100,mutation=True)
    assert actual!=expected,'FULL/BUSY mutation escaped independent arithmetic oracle'
    initialized=base.copy();registers=[0]*32
    execute(initialized,symbols['dsp_audio_ai_init_begin'],registers,{},
            stop=symbols['dsp_audio_ai_init_end'],terminal_rcp=True)
    rate=get(base,symbols['dsp_audio_dac_rate'])
    assert get(initialized,0xa4500010)==rate==1526
    assert get(initialized,0xa4500008)==1 and get(initialized,0xa4500014)==15
    init_owned={address+i for address in (0x4500008,0x4500010,0x4500014) for i in range(4)}
    assert all(initialized.get(k,0)==base.get(k,0) for k in initialized.keys()|base.keys() if k not in init_owned)
    proof=dict(passed=True,compiled_cases=cases,negative_mutations_rejected=1,
               maximum_instructions=maximum_steps,only_owned_counter_writes=True,
               pcm_and_ai_registers_untouched=True,hardware_mocked=True,
               ai_rate_matches_compiled_initialization=True,programmed_dac_rate=rate,
               physical_acceptance=False,elf_sha256=hashlib.sha256(args.elf.read_bytes()).hexdigest())
    if args.json_output:args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
