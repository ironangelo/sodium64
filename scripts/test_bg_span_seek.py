#!/usr/bin/env python3
"""Execute compiled BG span seek; compare tile coverage to independent pixels.

No guest data or native timing authority. Also checks negative movement when
two visible spans share an 8-pixel tile, and all preserved renderer state.
"""
import argparse
import importlib.util
import json
import struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('direct_vm', ROOT/'docs/gate-c-a3/test_hcomp_direct_backdrop.py')
vm = importlib.util.module_from_spec(spec); spec.loader.exec_module(vm)

def seek(code, data, start, regs, vector):
    pc = start; pending = None
    for steps in range(40):
        if pc == 0xfee:
            return steps
        w = struct.unpack_from('>I', code, pc)[0]
        op=w>>26; rs=w>>21&31; rt=w>>16&31; rd=w>>11&31
        imm=w&65535; si=imm if imm<32768 else imm-65536; target=None
        if op==0:
            fn=w&63; sh=w>>6&31
            if fn==0: regs[rd]=regs[rt]<<sh
            elif fn==8: target=regs[rs]&4095
            elif fn in (32,33): regs[rd]=regs[rs]+regs[rt]
            elif fn in (34,35): regs[rd]=regs[rs]-regs[rt]
            elif fn==37: regs[rd]=regs[rs]|regs[rt]
            else: raise AssertionError((hex(pc),hex(w)))
        elif op==4:
            if regs[rs]==regs[rt]: target=pc+4+(si<<2)
        elif op==12: regs[rt]=regs[rs]&imm
        elif op in (35,36,43):
            address=(regs[rs]+si)&4095
            if op==35: regs[rt]=vm.word(data,address)
            elif op==36: regs[rt]=data[address]
            else: vm.put(data,address,regs[rt])
        elif op in (50,58):
            # Actual LDV/SDV encoding: unsigned 7-bit offset scaled by8,
            # signed before adding base; element0, vector15 are fixed here.
            kind=w>>11&31; element=w>>7&15; offset=w&127
            assert kind==3 and element==0 and rt==15
            offset=offset if offset<64 else offset-128
            address=(regs[rs]+offset*8)&4095
            if op==50: vector[:8]=data[address:address+8]
            else: data[address:address+8]=vector[:8]
        else: raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None
        regs[:]=[v&0xffffffff for v in regs]; regs[0]=0
        pc=pending if pending is not None else pc+4; pending=target
    raise AssertionError('seek did not return')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('elf',type=Path); ap.add_argument('--output',type=Path)
    args=ap.parse_args(); _,code=read_text(args.elf)
    syms={name:address&4095 for address,name in elf_symbols(args.elf)}
    data=vm.section(args.elf,'.data')
    assert len(code)==len(data)==4096
    assert syms['draw_bg']==0x3a8 and syms['draw_mode7_entry']==0x788
    assert syms['calc_bg_window_spans']==0xcc0 and syms['rdp_send']==0xf5c
    # Discover command/scratch addresses from compiled helper, not source.
    start=syms['bg_span_seek']
    first=vm.word(code,start); assert first>>26==36 and (first>>16)&31==8
    bounds=first&65535
    fill=next(a for a in range(0,4096,8) if vm.word(data,a)==0x33000000)
    tile=fill+72
    # The ABI tile list follows the window pair; locate real TexRect words.
    tile=next(a-24 for a in range(0,4096,8) if vm.word(data,a)==0x24000000)
    cases=0; maximum_steps=0
    def run(left,scroll,current,index=0):
        nonlocal cases,maximum_steps
        d=bytearray(data); d[bounds+index]=left
        upper=0x02000000|((current+12)<<14)|(37*4)
        lower=upper+0x22020020
        v=bytearray(struct.pack('>II',lower,upper)+bytes(range(8)))
        r=[0x13500000+i for i in range(32)]
        r[0]=0; r[2]=tile+24; r[16]=current&0xffffffff; r[22]=scroll
        r[24]=index; r[31]=0xfee
        before=list(r); memory=bytes(d); tail=bytes(v[8:])
        steps=seek(code,d,start,r,v); maximum_steps=max(maximum_steps,steps)
        wanted=next(x for x in range(-7,257) if (x+scroll)%8==0 and x<=left<x+8)
        assert vm.signed(r[16])==wanted,(left,scroll,current,r[16],wanted)
        got_lower,got_upper=struct.unpack('>II',v[:8])
        assert got_upper==0x02000000|((wanted+12)<<14)|(37*4)
        assert got_lower==got_upper+0x22020020
        assert bytes(v[8:])==tail
        assert all(r[i]==before[i] for i in range(32) if i not in (8,9,16))
        assert d[:tile+24]==memory[:tile+24] and d[tile+32:]==memory[tile+32:]
        cases+=1; return wanted
    for scroll in range(8):
        for left in range(256):
            for current in range(-scroll,257,8):
                run(left,scroll,current,2 if left&1 else 0)
    coverage=0; rewind=0; saved=0
    for scroll in range(8):
        for intervals in (((0,60),(63,255)),((93,148),),((255,255),),
                          ((1,2),(4,5),(7,8)),((0,0),(255,255))):
            current=-scroll; seen=set()
            for left,right in intervals:
                old=current; current=run(left,scroll,current)
                rewind+=current<old; saved+=max(0,(current-old)//8)
                while current<=right:
                    seen.update(x for x in range(current,current+8) if left<=x<=right)
                    current+=8
            assert seen=={x for x in range(256) if any(l<=x<=r for l,r in intervals)}
            coverage+=1
    early=0; hidden=0
    bounds_cases=((0,255,0,255),(32,95,64,191),(255,255,0,0),
                  (200,100,250,2),(0,0,255,255),(80,80,80,80),(2,254,3,253))
    for index in range(4):
     for selector in range(16):
      for logic in range(4):
       for bounds_tuple in bounds_cases:
        for screen in (0,1):
         for masks in range(4):
          d=bytearray(data);d[0xec8]=screen
          d[0xbbb]=(1<<index) if masks&1 else 0
          d[0xbbc]=(1<<index) if masks&2 else 0
          struct.pack_into('>H',d,0xba4,selector<<(index*4))
          d[0xbb5]=logic<<(index*2);d[0xbae:0xbb2]=bytes(bounds_tuple)
          r=[0x13500000+i for i in range(32)];r[0]=0
          r[4]=0xf50+index*8;r[5]=r[4]+8;r[7]=1<<index
          r[18]=index*2;r[31]=0xbee
          frozen={i:r[i] for i in (2,7,*range(16,24),25,26,27,28,29)}
          protected=d[0x840:0xa60]+d[0xb80:0xbc0]
          active=bool((masks>>screen)&1)
          wanted={x for x in range(256) if not active or not vm.selected(x,selector,logic,bounds_tuple)}
          stop=0xf5c if wanted else 0x370
          vm.run(code,d,syms['bg_window_depth'],r,stop=stop)
          assert all(r[i]==value for i,value in frozen.items())
          assert d[0x840:0xa60]+d[0xb80:0xbc0]==protected
          if wanted:
           assert r[4:6]==[0xf50+index*8,0xf58+index*8] and r[31]==0xbee
          else: hidden+=1
          if active:
           seen={x for n in range(d[0xe8a]) for x in range(d[0xe84+2*n],d[0xe85+2*n]+1)}
           assert seen==wanted
          early+=1
    result=dict(passed=True,compiled_cases=cases,coverage_cases=coverage,
                shared_tile_rewinds=rewind,hidden_tile_iterations_avoided=saved,
                early_window_cases=early,fully_hidden_layer_cases=hidden,
                maximum_helper_instructions=maximum_steps,
                preserved_cache_dirty_priority_texture_identity=True,
                native_fps_authority=False)
    if args.output: args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('BG_SPAN_SEEK PASS '+json.dumps(result))

if __name__=='__main__': main()
