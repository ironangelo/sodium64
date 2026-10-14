#!/usr/bin/env python3
"""Linked BRR primitive versus pinned scalar arithmetic; no N64 timing claim."""
import argparse,hashlib,itertools,json,random,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_scene_rsp_context import execute,state,signed

CONSTANTS=(0,1,65535,32768,0xf000,2,3,63488,62464,58880,4096,12288)
def oracle(word,header,p1,p2):
    out=[];shift=header>>4;kind=header&12
    for n in range(4):
        nib=signed((word>>(12-4*n))&15,4)
        s=(nib<<shift)>>1
        if shift>=13:s=-2048 if s<0 else 0
        half=p2>>1
        if kind>=8:
            s+=p1-half
            if kind==8:s+=(half>>4)+((-3*p1)>>6)
            else:s+=((-13*p1)>>7)+((3*half)>>4)
        elif kind:s+=(p1>>1)+((-p1)>>5)
        s=signed((max(-32768,min(32767,s))*2)&65535,16)
        out.append(s);p2,p1=p1,s
    return out

def packet(code,cases,seed):
    assert len(cases)==8
    d=bytearray((i*31+97)&255 for i in range(4096))
    vectors=[[],[],[],[],[],[]]
    for word,header,p1,p2 in cases:
        shift=header>>4
        for vector,value in zip(vectors,(word,p1&65535,p2&65535,
            1<<(shift+3) if shift<=12 else 1,1 if shift<=12 else 2048,(header>>2)&3)):
            vector.append(value)
    for i,vector in enumerate(vectors):struct.pack_into('>8H',d,i*16,*vector)
    for i,value in enumerate(CONSTANTS):struct.pack_into('>8H',d,96+i*16,*([value]*8))
    before=bytes(d);r,v,acc,flags=state(seed)
    steps=execute(code,d,r,v,acc,flags)
    expected=[oracle(*case) for case in cases]
    for n in range(4):
        actual=[signed(x,16) for x in struct.unpack_from('>8H',d,0x120+n*16)]
        assert actual==[e[n] for e in expected],('BRR mismatch',n,cases,actual,expected)
    assert d[:0x120]==before[:0x120] and d[0x160:]==before[0x160:],'output owner escaped'
    return steps

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    _,code=read_text(a.elf);assert len(code)==444
    words=list(struct.unpack('>111I',code));counts=set();batch=[];directed=packets=0
    edges=(-32768,-32767,-1,0,1,32766,32767)
    patterns=(0x0000,0xffff,0x7777,0x8888,0x87f0,0x0123,0xfedc)
    for shift,kind,p1,p2,word in itertools.product(range(16),range(4),edges,edges,patterns):
        batch.append((word,shift*16+kind*4,p1,p2));directed+=1
        if len(batch)==8:counts.add(packet(code,batch,packets));packets+=1;batch=[]
    if batch:counts.add(packet(code,batch+batch[:1]*(8-len(batch)),packets));packets+=1
    # Every encoded four-nybble word, rotating independent ranges/filters and
    # odd/extreme histories; then mixed random lane packets.
    for base in range(0,65536,8):
        cases=[(base+i,((base+i)&15)*16+(((base+i)>>4)&3)*4,
                edges[(base//8+i)%7],edges[(base//16+i*3)%7]) for i in range(8)]
        counts.add(packet(code,cases,base+100000))
    rng=random.Random(0x58b44);negative_packets=[]
    for n in range(8192):
        cases=[(rng.randrange(65536),rng.randrange(256),rng.randrange(-32768,32768),rng.randrange(-32768,32768)) for _ in range(8)]
        if n<128:negative_packets.append(cases)
        counts.add(packet(code,cases,n+200000))
    def find(fn,vs=None):return next(i for i,w in enumerate(words) if w>>26==18 and w>>21&31>=16 and w&63==fn and (vs is None or w>>11&31==vs))
    mutate=[('wrong_raw_unsigned_product',find(5,28),lambda w:(w&~63)|6),
        ('wrong_filter1_coefficient',find(39,13),lambda w:(w&~(31<<11))|(14<<11)),
        ('missing_odd_history_half',find(15,25),lambda w:0),
        ('premature_ACC_reset',find(15,26),lambda w:(w&~63)|7),
        ('wrong_second_history',find(40,1),lambda w:(w&~((31<<11)|(31<<16)))|(31<<11)|(31<<16)),
        ('missing_nybble_shift',find(20,0),lambda w:0)]
    rejected=[]
    for name,index,change in mutate:
        altered=words.copy();altered[index]=change(altered[index]);binary=struct.pack('>111I',*altered)
        for cases in negative_packets:
            try:packet(binary,cases,999)
            except AssertionError:rejected.append(name);break
        else:raise AssertionError('escaped mutation '+name)
    assert counts=={111}
    proof=dict(passed=True,linked_kernel_bytes=444,instructions_per32_samples=111,
        directed_lane_groups=directed,all65536_encoded_words=True,random_lane_groups=65536,
        all16_ranges_all4_filters_signed_odd_histories=True,all_entry_vectors_ACC_flags_randomized=True,
        output_owner_bytes=64,all_other4096_DMEM_bytes_unchanged=True,negative_mutations_rejected=rejected,
        kernel_sha256=hashlib.sha256(code).hexdigest(),native_RSP_transport_or_performance_tested=False,commercial_data=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))
if __name__=='__main__':main()
