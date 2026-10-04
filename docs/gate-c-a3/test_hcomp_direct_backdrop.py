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
            elif fn==6:regs[rd]=regs[rt]>>(regs[rs]&31)
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
    data=bytearray(section(a.main,'.data'));assert len(data)==4096
    data[0xbba]=31 # Existing exhaustive cases keep all latent enables visible.
    fs={n:v&0xfff for v,n in elf_symbols(a.fast)}
    ps={n:v&0xfff for v,n in elf_symbols(a.phase)}
    assert ps['hcomp_policy_return']==0x768 and fs['hcomp_fast_screen_switch']==0x760
    admission=0
    for cg in range(256):
        for sel in range(256):
            d=bytearray(data);d[0xbb8]=cg;d[0xbb7]=sel;d[0xba8:0xbaa]=bytes(2)
            d[0xbbe]=0x40;d[0xba6:0xba8]=b'\x00\x3e';put(d,0xecc,0)
            d[0x840:0xa60]=bytes(0x220) # Certified low-palette OBJ geometry.
            d[0xbbd]=0
            d[0xbb9]=0x13
            r=[0xdead0000+i for i in range(32)];r[0]=0;r[26:30]=[13,224,0xcafe,4]
            run(code,d,0x3b0,r)
            expected=1 if sel&0xc0==0 and (cg&63==0 or sel&0x30==0x30) else 2 if cg in (0x20,0x30) and sel in (0,1,2,3,0x10,0x11,0x12,0x13,0x20,0x21,0x22,0x23) else 0
            assert word(d,0xef0)==expected,(cg,sel,word(d,0xef0),expected)
            # Fixed operands never observe Sub. TS remains unmodified, while
            # effective TS is zero for every fixed policy, including general.
            assert d[0xbb9]==0x13 and d[0xec9]==(0x13 if sel&2 else 0)
            assert r[26:30]==[13,224,0xcafe,4] and r[25]==0x1768
            admission+=1
    # Derive expectations from visible winner sets, retaining HALF/subtract
    # and clipping counterexamples. Raw guest registers must not be modified.
    latent=0
    for tm in range(16):
      for cg in range(256):
       for sel in (0,2,0x10,0x12,0x20,0x22,0x32,0xc2):
        d=bytearray(data);d[0xbba]=tm;d[0xbb8]=cg;d[0xbb7]=sel
        d[0xbbd]=1;d[0xbbe]=0;d[0xba8:0xbaa]=bytes(2)
        d[0xba6:0xba8]=b'\x00\x3e';put(d,0xecc,0)
        run(code,d,0x3b0,[0]*32)
        eligible=bool(cg&0x20) or bool(cg&tm&15)
        backdrop_only=bool(cg&0x20) and not bool(cg&tm&15) and cg&0xc0==0
        expected=0 if sel&0xc0 else 1 if not eligible or sel&0x30==0x30 else 2 if backdrop_only else 0
        assert word(d,0xef0)==expected,('latent Main enables',tm,cg,sel,word(d,0xef0),expected)
        assert d[0xbb8]==cg and d[0xbba]==tm,'guest register mutation'
        latent+=1
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
    # Only Mode0 may disregard CGWSEL's direct-color bit. Test all priority,
    # tile-size and unused BG_MODE bits without modifying that register.
    mode_cases=0
    for mode in range(256):
      for sel in (0,1,2,3,0x10,0x11,0x12,0x13,0x20,0x21,0x22,0x23):
       for cg in (0x20,0x30):
        d=bytearray(data);d[0xbb7]=sel;d[0xbb8]=cg;d[0xbbd]=mode;d[0xbba]=0
        d[0xba8:0xbaa]=bytes(2);d[0xba6:0xba8]=b'\x00\x3e';d[0xbbe]=0;put(d,0xecc,0)
        run(code,d,0x3b0,[0]*32)
        assert word(d,0xef0)==(2 if not sel&1 or mode&7==0 else 0),(mode,sel,cg)
        assert d[0xbb7:0xbb9]==bytes((sel,cg)) and d[0xbbd]==mode
        mode_cases+=1
    # Independent SNES small/large heights, including rectangular OBJ sizes.
    # Compare compiled admission with the set of rows occupied by each OBJ.
    # A high-palette OBJ blocks its conservative vertical rows. Safe spans
    # must end before any future eligible row; X/opacity are never assumed.
    heights=((8,16),(8,32),(8,64),(16,32),(16,64),(32,64),(32,64),(32,32))
    obj_cases=0
    def obj_case(index,y,palette,size_mode,large,fb,queue=0,enabled=True,second=False,fresh=True):
        nonlocal obj_cases
        d=bytearray(data);d[0x840:0xa60]=bytes(0x220)
        d[0xbb2]=size_mode<<5;d[0xbb7]=3;d[0xbb8]=0x30;d[0xbbd]=0
        d[0xbba]=0x11 if enabled else 1;d[0xbbe]=0x40 if fresh else 0
        d[0xba8:0xbaa]=bytes(2);d[0xba6:0xba8]=b'\x00\x3e';put(d,0xecc,0)
        put(d,0xbc8,fb if queue==0 else 8);put(d,0xbcc,fb if queue==4 else 16)
        put(d,0x840+index*4,(y<<24)|(127<<16)|(palette<<9))
        d[0xa40+index//4]=int(large)<<((index%4)*2+1)
        if second:put(d,0x840+127*4,(10<<24)|(4<<9))
        before=d[0x840:0xa60];r=[0xdead0000+i for i in range(32)];r[0]=0;r[26:30]=[13,224,0xcafe,queue]
        run(code,d,0x3b0,r)
        first_row=y-256 if y>=256-2*fb else y
        quad_rows=range(first_row,first_row+heights[size_mode][int(large)])
        hazard=set(quad_rows) if palette>=4 else set()
        if second:hazard.update(range(10,18))
        want=0 if enabled and (13 in hazard or not fresh) else 2
        assert word(d,0xef0)==want,(index,y,palette,size_mode,large,fb,queue,enabled,second,fresh,word(d,0xef0),want)
        if want==2:
            end=min((row for row in hazard if 13<row<224),default=224) if enabled else 224
            assert word(d,0xf18)==end
        assert d[0x840:0xa60]==before and d[0xbb7:0xbb9]==b'\x03\x30'
        assert r[26:30]==[13,224,0xcafe,queue] and r[25]==0x1768
        obj_cases+=1
    for y in range(256):
      for mode in range(8):
       for large in (False,True):
        for fb in (0,8,16):
         obj_case((y*13+mode+7*large)%128,y,4,mode,large,fb)
    for index in range(128):
      for y in (0,240,248,255):
       for large in (False,True):
        for queue in (0,4):obj_case(index,y,4,0,large,8,queue)
    for palette in range(8):
      for y in (0,239,240,248,255):
       for mode in (0,6,7):
        for large in (False,True):
         for fb in (8,16):obj_case(63,y,palette,mode,large,fb)
    for palette in range(8):
      for enabled in (False,True):
       obj_case(0,240,palette,0,False,8,enabled=enabled,second=True)
    # Current OAM alone cannot certify a cache built with older size/Y-wrap.
    # Even low palettes or above-frame small quads stay general until rebuild.
    for palette in (0,4):
      for mode in range(8):
       for fb in (0,8,16):
        for enabled in (False,True):
         obj_case(0,240,palette,mode,False,fb,enabled=enabled,fresh=False)
    # Exercise compiled Fast and Phase together across arbitrary sections.
    # Independent sets of occupied rows certify complete coverage and that
    # no direct band can include even one potentially eligible OBJ pixel row.
    schedules=0
    rng=random.Random(43107)
    for trial in range(256):
        d=bytearray(data);d[0x840:0xa60]=bytes(0x220)
        fb=rng.choice((8,16));size=rng.randrange(8)
        d[0xbb2]=size<<5;d[0xbb7]=3;d[0xbb8]=0x20;d[0xbbd]=0;d[0xbba]=0x11
        d[0xbbe]=0x40;d[0xba6:0xba8]=b'\x00\x3e';d[0xba8:0xbaa]=bytes(2)
        put(d,0xbc8,fb);put(d,0xecc,0)
        hazards=set()
        for i in range(rng.randrange(1,16)):
            y=rng.randrange(256);large=rng.randrange(2);pal=rng.randrange(8)
            put(d,0x840+4*i,(y<<24)|(127<<16)|(pal<<9))
            d[0xa40+i//4]|=large<<((i%4)*2+1)
            top=y-256 if y>=256-2*fb else y
            if pal>=4:hazards.update(range(top,top+heights[size][large]))
        # A backdrop-only first epoch must still certify its rebuilt cache.
        r=[0]*32;r[27]=5;run(code,d,0x3b0,r)
        assert word(d,0xef4)==0x10000|(fb<<8)|(size<<5)
        d[0xbbe]=0;d[0xbb8]=0x30
        edges=sorted({0,224,*[rng.randrange(1,224) for _ in range(5)]})
        for begin,end in zip(edges,edges[1:]):
            put(d,0xebc,end);r=[0]*32;r[26]=begin;r[27]=end
            seen=[]
            while r[26]<end:
                start=r[26];run(code,d,0x740,r)
                policy=word(d,0xef0)
                run_geometry(p,pb&0xfff,d,0x768,{ps['hcomp_band_targets_ready']},r)
                stop=r[27];assert start<stop<=end
                rows=set(range(start,stop));seen.extend(range(start,stop))
                if policy==2:assert not rows&hazards,(trial,start,stop,sorted(rows&hazards))
                else:assert policy==0 and rows.issubset(hazards)
                # The actual Phase band-done must select the Fast resume entry
                # for adaptive bands without consuming a real section epoch.
                run_geometry(p,pb&0xfff,d,ps['hcomp_band_done'],{0xf5c},r)
                run_geometry(p,pb&0xfff,d,ps['hcomp_band_done']+24,{0xf7c},r)
                assert r[26]==stop and r[25]==0x1740
                schedules+=1
            assert seen==list(range(begin,end))
        # Geometry changes without a rebuild must fail closed, even if
        # current OAM appears harmless. A subsequent rebuild recertifies.
        for addr,value,n in ((0xbb2,(size^1)<<5,1),(0xbc8,fb^8,4)):
            prior=d[addr:addr+n];d[addr:addr+n]=value.to_bytes(n,'big')
            r=[0]*32;r[27]=224;run(code,d,0x3b0,r)
            assert word(d,0xef0)==0 and word(d,0xf1c)==0
            d[0xbbe]=0x40;run(code,d,0x3b0,r)
            assert word(d,0xf1c)==1
            d[addr:addr+n]=prior;d[0xbbe]=0x40;run(code,d,0x3b0,r);d[0xbbe]=0
    masks=0
    randoms=random.Random(9126)
    all_bounds=[(0,255,0,0),(255,255,0,0),(0,0,255,255),(200,100,0,0),
                (126,130,0,0),(1,2,5,6),(32,95,64,191),(32,191,64,127)]
    all_bounds += [tuple(randoms.randrange(256) for _ in range(4)) for _ in range(128)]
    for bounds in all_bounds:
        for selector in range(16):
            for logic in range(4):
              for mode in (0x12,0x22):
                d=bytearray(data);d[0xbb7]=mode;d[0xbb4]=selector<<4;d[0xbb6]=logic<<2
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
                assert painted==[selected(x,selector,logic,bounds) != (mode==0x12) for x in range(256)],(mode,selector,logic,bounds)
                assert not any(c>>56==0x2f and c&0x20 for c in lists),'proof Z enabled'
                assert lists[-2]==0x3c080e10001c8241,'texture combiner not restored'
                assert lists[-1]==int.from_bytes(d[0xc68:0xc70],'big'),'whole scissor not restored'
                assert r[26:30]==[5,223,0xcafe,4] and r[23]==0x15 and r[25]==0x1370
                assert d[0xec8]==1 and d[0xbb7]==mode
                masks+=1
    geometry=0
    for y in range(8,248):
        for rows in sorted({1,min(8,248-y),min(9,248-y),min(17,248-y),248-y}):
            for policy in (0,1,2):
                d=bytearray(data);put(d,0xbc8,8);put(d,0xebc,y-8+rows);put(d,0xf18,y-8+rows);put(d,0xef0,policy)
                r=[0]*32;r[26]=y-8;r[27]=0xdead
                run_geometry(p,pb&0xfff,d,0x768,{ps['hcomp_band_targets_ready']},r)
                want=rows
                assert word(d,0xec4)==want and r[27]==y-8+want
                geometry+=1
    result=dict(passed=True,admission_cases=admission+4,latent_main_enable_cases=latent,compiled_window_mask_cases=masks,
                identity_admission_cases=neutral_cases,
                mode0_control_cases=mode_cases,obj_eligibility_cases=obj_cases,
                adaptive_band_schedule_cases=schedules,
                section_geometry_cases=geometry,pixel_truth_width=256,compact_alignment='separate compiled suite',
                native_timing_authority=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('DIRECT_BACKDROP_COMPILED PASS',json.dumps(result))

if __name__=='__main__':main()
