#!/usr/bin/env python3
"""Execute JIT lookup publication and sparse reset with original PCs.

Every callable/stale lookup must be zero after reset. Empty groups start and
remain zero. Tags, guest cycle debit, compiler input and adjacent owners survive.
"""
import argparse,json,random
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_v4 import execute,sx
from test_hcomp_redundant_work import put,get

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cpu',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
    image,s=load_elf(a.cpu);lookup=s['jit_lookup']&0x1fffffff
    flags=s['jit_lookup_live_groups']&0x1fffffff;rng=random.Random(0x700)
    publication=0;resets=0;bounds=[]
    for group in range(512):
      for low in (0,1,127):
        pc=128*group+low;m=image.copy();put(m,s['jit_pointer'],0xa01c0100)
        r=[sx(0x34560000+i) for i in range(32)];r[0]=0;r[16]=pc;r[5]=0xa01c0200
        before=r.copy()
        execute(m,s['jit_publish_lookup'],r,{},stop=s['jit_lookup_published'])
        assert get(m,lookup+4*pc)==0x801c0100
        assert get(m,flags+group,1)==1
        assert get(m,s['jit_pointer'])==0xa01c0200
        assert all(r[i]==before[i] for i in set(range(32))-{1,8,9,10,11,12})
        publication+=1
    sets=[set(),{0},{511},{0,511},set(range(512))]
    sets.extend(set(rng.sample(range(512),n)) for n in (1,4,16,32,128,256) for _ in range(4))
    for touched in sets:
        m=image.copy();table=bytearray(0x40000)
        for group in touched:
            table[512*group:512*(group+1)]=bytes(rng.randrange(1,256) for _ in range(512))
        m.update((lookup+i,b) for i,b in enumerate(table))
        m.update((flags+i,int(i in touched)) for i in range(512))
        left=bytes((i*17+3)&255 for i in range(32));right=bytes((i*13+5)&255 for i in range(32))
        m.update((lookup-32+i,b) for i,b in enumerate(left));m.update((flags+512+i,b) for i,b in enumerate(right))
        put(m,s['jit_pointer'],0xa01ffff0);put(m,s['jit_block_cycles'],25)
        r=[sx(0x23450000+i) for i in range(32)];r[0]=0;before=r.copy()
        steps=execute(m,s['reset_buffer'],r,{},stop=s['compile_block'])
        assert bytes(m[lookup+i] for i in range(0x40000))==bytes(0x40000)
        assert bytes(m[flags+i] for i in range(512))==bytes(512)
        assert bytes(m[lookup-32+i] for i in range(32))==left
        assert bytes(m[flags+512+i] for i in range(32))==right
        assert get(m,s['jit_pointer'])==0xa01c0000 and get(m,s['jit_block_cycles'])==25
        assert all(r[i]==before[i] for i in set(range(32))-{1,8,9,10,11,12})
        bounds.append(dict(groups=len(touched),lookup_bytes_required=len(touched)*512,compiled_instructions=steps))
        # Repeat reset after no publication: all owners must remain correct.
        steps2=execute(m,s['reset_buffer'],r,{},stop=s['compile_block'])
        assert steps2<4000 and bytes(m[lookup+i] for i in range(0x40000))==bytes(0x40000)
        resets+=2
    result=dict(passed=True,publication_cases=publication,reset_cases=resets,
                work_examples=bounds[:5],commercial_data=False,native_throughput_claimed=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('SPARSE_JIT_RESET PASS',json.dumps(result))

if __name__=='__main__':main()
