#!/usr/bin/env python3
"""Execute compiled admission, window masking and section geometry.

Independent per-pixel truth and inclusive/exclusive rectangle boundaries,
not a source-string or mirrored-algorithm test. Original data only. RDP list
collection checks full scissor/combiner restoration and forbids proof Z enable.
"""
import argparse
import json
import random
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_hcomp_aligned_targets import execute as run_geometry

def section(path, name):
    b=Path(path).read_bytes();h=struct.unpack_from('>16sHHIIIIIHHHHHH',b)
    secs=[struct.unpack_from('>IIIIIIIIII',b,h[6]+i*h[11]) for i in range(h[12])]
    st=secs[h[13]];names=b[st[4]:st[4]+st[5]]
    s=next(s for s in secs if names[s[0]:].split(b'\0',1)[0].decode()==name)
    return b[s[4]:s[4]+s[5]]

def word(d,a):return struct.unpack_from('>I',d,a)[0]
def put(d,a,v):struct.pack_into('>I',d,a,v&0xffffffff)
def signed(v):return v if v<0x80000000 else v-0x100000000

def run(code,d,pc,regs,stop=0xf7c):
    pending=None;lists=[]
    for step in range(12000):
        if pc==stop:return lists
        if pc==0xf5c:
            assert pending is None
            a,b=regs[4:6];assert 0<=a<b<=4096 and a%8==b%8==0
            lists.extend(struct.unpack_from('>Q',d,n)[0] for n in range(a,b,8))
            regs[8]=b;pc=regs[31];continue
        w=struct.unpack_from('>I',code,pc)[0]
        op=w>>26;rs=w>>21&31;rt=w>>16&31;rd=w>>11&31;imm=w&65535
        si=imm if imm<32768 else imm-65536;target=None
        if op==0:
            fn=w&63;sh=w>>6&31
            if fn==0:regs[rd]=regs[rt]<<sh
            elif fn==2:regs[rd]=regs[rt]>>sh
            elif fn==8:target=regs[rs]&0xfff
            elif fn in (32,33):regs[rd]=regs[rs]+regs[rt]
            elif fn in (34,35):regs[rd]=regs[rs]-regs[rt]
            elif fn==36:regs[rd]=regs[rs]&regs[rt]
            elif fn==37:regs[rd]=regs[rs]|regs[rt]
            elif fn==38:regs[rd]=regs[rs]^regs[rt]
            elif fn==42:regs[rd]=int(signed(regs[rs])<signed(regs[rt]))
            elif fn==43:regs[rd]=int(regs[rs]<regs[rt])
            else:raise AssertionError((hex(pc),hex(w)))
        elif op in (2,3):
            if op==3:regs[31]=pc+8
            target=w<<2&0xfff
        elif op in (1,4,5):
            take=(signed(regs[rs])<0 if rt==0 else signed(regs[rs])>=0) if op==1 else (regs[rs]==regs[rt] if op==4 else regs[rs]!=regs[rt])
            if take:target=(pc+4+(si<<2))&0xfff
        elif op in (8,9):regs[rt]=regs[rs]+si
        elif op==11:regs[rt]=int(regs[rs]<(si&0xffffffff))
        elif op==12:regs[rt]=regs[rs]&imm
        elif op==13:regs[rt]=regs[rs]|imm
        elif op==14:regs[rt]=regs[rs]^imm
        elif op==15:regs[rt]=imm<<16
        elif op in (32,35,36,37,40,41,43):
            a=(regs[rs]+si)&0xfff;n={32:1,35:4,36:1,37:2,40:1,41:2,43:4}[op]
            assert a+n<=4096
            if op<40:
                v=int.from_bytes(d[a:a+n],'big');regs[rt]=v-256 if op==32 and v>=128 else v
            else:d[a:a+n]=(regs[rt]&((1<<(8*n))-1)).to_bytes(n,'big')
        else:raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None,'control in delay slot'
        regs[:]=[v&0xffffffff for v in regs];regs[0]=0
        pc=pending if pending is not None else pc+4;pending=target
    raise AssertionError('compiled routine did not terminate')

def selected(x,selector,logic,bounds):
    l1,r1,l2,r2=bounds
    one=(l1<=x<=r1)^bool(selector&1) if selector&2 else False
    two=(l2<=x<=r2)^bool(selector&4) if selector&8 else False
    if selector&10==10:return (one or two,one and two,one!=two,one==two)[logic]
    return one if selector&2 else two if selector&8 else False

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('main','phase','fast'):ap.add_argument(n,type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    mb,m=read_text(a.main);fb,f=read_text(a.fast);pb,p=read_text(a.phase)
    assert mb&0xfff==0 and fb&0xfff==pb&0xfff==0x3a8
    assert len(m)==4096 and len(f)==len(p)==1000
    code=bytearray(m);code[0x3a8:0x790]=f
    data=section(a.main,'.data');assert len(data)==4096
    fs={n:v&0xfff for v,n in elf_symbols(a.fast)}
    ps={n:v&0xfff for v,n in elf_symbols(a.phase)}
    assert ps['hcomp_policy_return']==0x768 and fs['hcomp_fast_screen_switch']==0x760
    admission=0
    for cg in range(256):
        for sel in range(256):
            d=bytearray(data);d[0xbb8]=cg;d[0xbb7]=sel;d[0xba8:0xbaa]=bytes(2)
            d[0xbbe]=0;d[0xba6:0xba8]=b'\x00\x3e';put(d,0xecc,0)
            r=[0xdead0000+i for i in range(32)];r[0]=0;r[26:30]=[13,224,0xcafe,4]
            run(code,d,0x3b0,r)
            expected=1 if sel&0xc0==0 and (cg&63==0 or sel&0x30==0x30) else 2 if cg==0x20 and sel in (2,0x12) else 0
            assert word(d,0xef0)==expected,(cg,sel,word(d,0xef0),expected)
            assert r[26:30]==[13,224,0xcafe,4] and r[25]==0x1768
            admission+=1
    for flags,color,diag in ((0x80,0,0),(0,1,0),(0,0xffff,0),(0,0,8)):
        d=bytearray(data);d[0xbb8]=0x20;d[0xbb7]=0x12;d[0xbbe]=flags
        d[0xba6:0xba8]=b'\x00\x3e'
        d[0xba8:0xbaa]=color.to_bytes(2,'big');put(d,0xecc,diag)
        run(code,d,0x3b0,[0]*32)
        assert word(d,0xef0)==(1 if flags&128 else 0)
    # Nonblack Main, eligible BG/OBJ winners, zero fixed operand, clipped
    # counterexamples and absent-Sub HALF suppression. Independent arithmetic
    # identities are the expected policy; all other states remain general.
    neutral_cases=0
    for cg in (1,2,4,8,16,32,63,65,95,127,129,191,193,255):
        for sel in range(256):
            for ts in (0,1,16,31):
                for fixed in (0,1,2,0x8000):
                    d=bytearray(data);d[0xbb8]=cg;d[0xbb7]=sel;d[0xbb9]=ts
                    d[0xba6:0xba8]=fixed.to_bytes(2,'big');d[0xba8:0xbaa]=b'\xab\xca'
                    d[0xbbe]=0;put(d,0xecc,0)
                    run(code,d,0x3b0,[0]*32)
                    identity=(sel&0x30==0x30 or fixed&0xfffe==0 and
                              (sel&2 and ts==0 or sel&2==0 and cg&64==0))
                    assert word(d,0xef0)==int(sel&0xc0==0 and identity),(cg,sel,ts,fixed,word(d,0xef0))
                    neutral_cases+=1
    masks=0
    randoms=random.Random(9126)
    all_bounds=[(0,255,0,0),(255,255,0,0),(0,0,255,255),(200,100,0,0),
                (126,130,0,0),(1,2,5,6),(32,95,64,191),(32,191,64,127)]
    all_bounds += [tuple(randoms.randrange(256) for _ in range(4)) for _ in range(128)]
    for bounds in all_bounds:
        for selector in range(16):
            for logic in range(4):
                d=bytearray(data);d[0xbb7]=0x12;d[0xbb4]=selector<<4;d[0xbb6]=logic<<2
                d[0xbae:0xbb2]=bytes(bounds);d[0xe84:0xe8b]=b'\xff'*7
                y,end=13,231
                # Poison the prior Sub scissor; the fast bank must restore the
                # exact whole section from RDP_FILL before black spans/Main.
                put(d,0xca0,0x2d100034);put(d,0xca4,0x00420038)
                struct.pack_into('>HH',d,0xc6a,y*4,0x43)
                struct.pack_into('>H',d,0xc6e,end*4)
                put(d,0xc80,0x36000000|(268<<14)|end*4)
                put(d,0xc84,(12<<14)|y*4)
                r=[0]*32;r[26:30]=[5,223,0xcafe,4];r[23]=0x15
                lists=run(code,d,0x760,r)
                painted=[False]*256
                for command in lists:
                    if command>>56==0x36:
                        hi=(command>>32&0x00ffc000)>>14;lo=(command&0x00ffc000)>>14
                        assert command>>32&0x3fff==end*4 and command&0x3fff==y*4
                        assert 12<=lo<hi<=268
                        for x in range(lo-12,hi-12):painted[x]=True
                assert painted==[not selected(x,selector,logic,bounds) for x in range(256)],(selector,logic,bounds)
                assert not any(c>>56==0x2f and c&0x20 for c in lists),'proof Z enabled'
                assert lists[-2]==0x3c080e10001c8241,'texture combiner not restored'
                assert lists[-1]==int.from_bytes(d[0xc68:0xc70],'big'),'whole scissor not restored'
                assert r[26:30]==[5,223,0xcafe,4] and r[23]==0x15 and r[25]==0x1370
                assert d[0xec8]==1 and d[0xbb7]==0x12
                masks+=1
    geometry=0
    for y in range(8,248):
        for rows in sorted({1,min(8,248-y),min(9,248-y),min(17,248-y),248-y}):
            for policy in (0,1,2):
                d=bytearray(data);put(d,0xbc8,8);put(d,0xebc,y-8+rows);put(d,0xef0,policy)
                r=[0]*32;r[26]=y-8;r[27]=0xdead
                run_geometry(p,pb&0xfff,d,0x768,{ps['hcomp_band_targets_ready']},r)
                want=min(rows,8) if policy==0 else rows
                assert word(d,0xec4)==want and r[27]==y-8+want
                geometry+=1
    result=dict(passed=True,admission_cases=admission+4,compiled_window_mask_cases=masks,
                identity_admission_cases=neutral_cases,
                section_geometry_cases=geometry,pixel_truth_width=256,compact_alignment='separate compiled suite',
                native_timing_authority=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('DIRECT_BACKDROP_COMPILED PASS',json.dumps(result))

if __name__=='__main__':main()
