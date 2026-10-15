#!/usr/bin/env python3
"""Compiled publication must preserve dirty handoff and palette pixels."""
import argparse,json,random,struct
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_v4 import execute as cpu_run
def run(m,pc,stop,r):
    pending=None;seen=[];lo=0
    def read(a,n):return int.from_bytes(bytes(m.get((a+i)&0x1fffffff,0) for i in range(n)),'big')
    def write(a,v,n):
        for i,b in enumerate((v&((1<<(n*8))-1)).to_bytes(n,'big')):m[(a+i)&0x1fffffff]=b
    for count in range(20000):
        if pc==stop:return seen,count
        w=read(pc,4);op=w>>26;rs=w>>21&31;rt=w>>16&31;rd=w>>11&31
        imm=w&65535;si=imm if imm<32768 else imm-65536;target=None
        if op==0:
            fn=w&63;sh=w>>6&31
            if fn==0:r[rd]=(r[rt]<<sh)&0xffffffff
            elif fn==2:r[rd]=(r[rt]&0xffffffff)>>sh
            elif fn==4:r[rd]=(r[rt]<<(r[rs]&31))&0xffffffff
            elif fn in (32,33):r[rd]=(r[rs]+r[rt])&0xffffffff
            elif fn==36:r[rd]=r[rs]&r[rt]
            elif fn==37:r[rd]=r[rs]|r[rt]
            elif fn==39:r[rd]=~(r[rs]|r[rt])&0xffffffffffffffff
            elif fn==24:lo=(r[rs]*r[rt])&0xffffffff
            elif fn==18:r[rd]=lo
            else:raise AssertionError((hex(pc),hex(w)))
        elif op in (8,9):r[rt]=(r[rs]+si)&0xffffffff
        elif op==12:r[rt]=r[rs]&imm
        elif op==13:r[rt]=r[rs]|imm
        elif op==15:r[rt]=imm<<16
        elif op in (4,5):
            if (r[rs]==r[rt])==(op==4):target=(pc+4+(si<<2))&0xffffffff
        elif op in (35,36,37,40,41,43,55,63):
            n={35:4,36:1,37:2,40:1,41:2,43:4,55:8,63:8}[op];addr=(r[rs]+si)&0xffffffff
            if op in (35,36,37,55):r[rt]=read(addr,n)
            else:write(addr,r[rt],n)
        elif op==47:seen.append((rt,(r[rs]+si)&0xffffffff))
        else:raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None
        r[0]=0;pc=pending if pending is not None else (pc+4)&0xffffffff;pending=target
    raise AssertionError('CPU handoff did not finish')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf');ap.add_argument('--output',type=Path);a=ap.parse_args()
    base,s=load_elf(a.elf)
    def put(m,addr,b):m.update(((addr+i)&0x1fffffff,c) for i,c in enumerate(b))
    def get(m,addr,n):return bytes(m.get((addr+i)&0x1fffffff,0) for i in range(n))
    rng=random.Random(0x6411);cases=[];dirty=s['vram_table'];vram=s['vram'];queue=0x80380000
    patterns=[bytes(1024),bytes([31])*1024]
    for i in (0,1,7,8,511,512,1016,1023):
        p=bytearray(1024);p[i]=31;patterns.append(bytes(p))
    patterns += [bytes(31 if rng.randrange(100)<density else 0 for _ in range(1024)) for density in (1,10,50)]
    vb=bytes((i*17+5)&255 for i in range(65536))
    for force in (0,1):
      for p in patterns:
       for slot in (0,4):
        m=base.copy();put(m,dirty,p);put(m,s['vram_publish_full'],bytes([force]));put(m,s['dirty_queues']+slot,queue.to_bytes(4,'big'));put(m,vram,vb)
        r=[0x13500000+i for i in range(32)];r[0]=0;r[13]=slot;before=r.copy()
        seen,instructions=run(m,s['vram_flush_begin'],s['vram_flush_end'],r)
        expected=[(0x19,vram+i) for i in range(0,65536,16) if force or any(p[(i//512)*8:(i//512)*8+8])]
        assert seen==expected
        assert get(m,queue,1024)==p and get(m,dirty,1024)==bytes(1024)
        assert get(m,vram,65536)==vb and get(m,s['vram_publish_full'],1)==b'\0'
        assert all(r[i]==before[i] for i in range(32) if i not in (1,3,8,9,10,11,14))
        cases.append(dict(force=force,lines=len(seen),instructions=instructions))
    palettes=0
    for brightness in range(17):
      for flags in range(4):
       for slot in (0,4):
        for previous in (brightness,(brightness+1)%17):
            m=base.copy();colors=[rng.randrange(32768) for _ in range(256)]
            put(m,s['cgram'],struct.pack('>256H',*colors));put(m,s['brightness'],bytes([brightness]))
            put(m,s['dpal_dirty'],bytes([flags]));put(m,s['dpal_brightness'],bytes([previous,previous]))
            put(m,s['pal_queues']+slot,queue.to_bytes(4,'big'));original=bytes([0xa5])*2048;put(m,queue,original)
            r=[0x13500000+i for i in range(32)];r[0]=0;r[13]=slot;before=r.copy()
            run(m,s['dpal_update_begin'],s['dpal_update_end'],r)
            convert=bool(flags&(1<<(slot//4))) or brightness!=previous;expected=bytearray(original)
            if convert:
                for i,c in enumerate(colors[1:],1):
                    rgb=[((c>>shift)&31)*brightness//16 for shift in (0,5,10)]
                    color=(rgb[0]<<11)|(rgb[1]<<6)|(rgb[2]<<1)|1
                    expected[i*8:i*8+8]=struct.pack('>HHHH',*[color]*4)
            assert get(m,queue,2048)==expected
            assert get(m,s['cgram'],512)==struct.pack('>256H',*colors)
            assert get(m,s['dpal_dirty'],1)==bytes([flags&~(1<<(slot//4)) if convert else flags])
            assert all(r[i]==before[i] for i in range(32) if i not in (1,3,8,9,10,11,14))
            palettes+=1
    for color in (0,1,255):
      for flags in range(4):
       for old in (b'\x00\x00',b'\x12\x34'):
        m=base.copy();put(m,s['dpal_dirty'],bytes([flags]));put(m,s['cg_lsb'],b'\x34');put(m,s['cgram']+color*2,old)
        # Closed-frame commits fold into the next base snapshot. Exercise the
        # actual equal-color return and changed-color tail rather than stopping
        # at a label that preceded A13's idempotent return.
        put(m,s['frame_done'],b'\x01')
        r=[0]*32;r[8]=color*2+1;r[5]=0x12;r[31]=0xdead0000
        stop=s['update_fill'] if color==0 and old!=b'\x12\x34' else 0xdead0000
        cpu_run(m,s['cg_high'],r,{},stop=stop)
        assert get(m,s['dpal_dirty'],1)==bytes([flags if old==b'\x12\x34' else 3])
        assert get(m,s['cgram']+color*2,2)==b'\x12\x34'
    assert max(c['instructions'] for c in cases)<6144 # Old dirty-copy + full writeback bodies.
    proof=dict(passed=True,publication_cases=len(cases),palette_cases=palettes,commit_cases=24,
               startup_all_lines=True,dirty_handoff_exact=True,clean_frame_cache_lines=0,
               palette_pixel_equivalence=True,independent_queue_validity=True,native_fps_authority=False,
               minimum_publication_instructions=min(c['instructions'] for c in cases),
               maximum_publication_instructions=max(c['instructions'] for c in cases))
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
    print('VRAM_PALETTE_PUBLICATION PASS',json.dumps(proof))
if __name__=='__main__':main()
