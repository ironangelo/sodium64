#!/usr/bin/env python3
"""Execute the linked eight-lane Gaussian primitive against independent floors.

Only the existing directed RSP instruction model is used, not N64 timing or
native acceptance. Vector semantics match pinned ares9408cb43 SISD source.
"""
import argparse,hashlib,itertools,json,random,re,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_scene_rsp_context import execute,state,signed

def oracle(samples,f,gauss):
    coefficients=(gauss[255-f],gauss[511-f],gauss[256+f],gauss[f])
    p=[x*g//2048 for x,g in zip(samples,coefficients)]
    first=signed(sum(p[:3])&65535,16)
    return max(-32768,min(32767,first+p[3]))&~1

def packet(code,cases,gauss,seed):
    assert len(cases)==8
    d=bytearray((i*31+97)&255 for i in range(4096))
    for tap in range(4):
        struct.pack_into('>8H',d,tap*32,*(s[tap]&65535 for s,_ in cases))
        coefficients=[(gauss[255-f],gauss[511-f],gauss[256+f],gauss[f])[tap]<<5 for _,f in cases]
        struct.pack_into('>8H',d,tap*32+16,*coefficients)
    struct.pack_into('>8H',d,128,*([65534]*8));before=bytes(d)
    r,v,acc,flags=state(seed);count=execute(code,d,r,v,acc,flags)
    expected=[oracle(s,f,gauss)&65535 for s,f in cases]
    actual=list(struct.unpack_from('>8H',d,144))
    assert actual==expected,('Gaussian mismatch',cases,actual,expected)
    assert d[:144]==before[:144] and d[160:]==before[160:],'DMEM owner escaped'
    return count

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];text=(root/'third_party/snes_spc/SPC_DSP.cpp').read_text()
    table=re.search(r'gauss\s*\[\s*512\s*\]\s*=\s*\{(.*?)\}',text,re.S);assert table
    gauss=list(map(int,re.findall(r'\d+',table[1])));assert len(gauss)==512 and max(gauss)==1305
    _,code=read_text(a.elf);assert len(code)%4==0 and len(code)<=4096
    words=list(struct.unpack('>'+str(len(code)//4)+'I',code))
    assert sum(w>>26==18 and w>>21&31>=16 and w&63==5 for w in words)==4
    assert not any(w>>26==16 for w in words),'kernel owns no RCP control register'
    edges=(-32768,-32767,-1,0,1,32766,32767);batch=[];cases=0;packets=0;counts=set()
    for f in range(256):
        for samples in itertools.product(edges,repeat=4):
            batch.append((samples,f));cases+=1
            if len(batch)==8:counts.add(packet(code,batch,gauss,packets));packets+=1;batch=[]
    if batch:
        batch+=(batch[:1]*(8-len(batch)));counts.add(packet(code,batch,gauss,packets));packets+=1
    rng=random.Random(0x56a550);random_cases=0;directed=[]
    for n in range(8192):
        current=[(tuple(rng.randrange(-32768,32768) for _ in range(4)),rng.randrange(256)) for _ in range(8)]
        if len(directed)<64:directed.append(current)
        counts.add(packet(code,current,gauss,n+100000));random_cases+=8
    changes=[]
    multiply=next(i for i,w in enumerate(words) if w>>26==18 and w>>21&31>=16 and w&63==5)
    add=next(i for i,w in enumerate(words) if w>>26==18 and w>>21&31>=16 and w&63==20)
    clear=next(i for i,w in enumerate(words) if w>>26==18 and w>>21&31==6)
    store=next(i for i,w in enumerate(words) if w>>26==58)
    for name,index,replacement in [('wrong_unsigned_product',multiply,(words[multiply]&~63)|6),
        ('premature_saturation',add,(words[add]&~63)|16),('missing_carry_clear',clear,0),
        ('missing_result_store',store,0)]:
        changed=words.copy();changed[index]=replacement;blob=struct.pack('>'+str(len(changed))+'I',*changed)
        caught=False
        for current in directed:
            try:packet(blob,current,gauss,333)
            except AssertionError:caught=True;break
        assert caught,'escaped mutation '+name;changes.append(name)
    proof=dict(passed=True,linked_kernel_bytes=len(code),directed_lane_cases=cases,
        random_lane_cases=random_cases,directed_packets=packets,linked_instructions_per_packet=sorted(counts),
        all256_fractions_and_signed_sample_edges=True,per_tap_floor_first_three_wrap_final_saturation_and_even_mask=True,
        all_entry_vector_ACC_flags_randomized=True,output_owner_bytes=16,all_other_DMEM_bytes_unchanged=True,
        negative_mutations_rejected=changes,kernel_sha256=hashlib.sha256(code).hexdigest(),
        native_RSP_DMA_renderer_sharing_or_performance_tested=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))
if __name__=='__main__':main()
