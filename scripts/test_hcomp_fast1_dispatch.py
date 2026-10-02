#!/usr/bin/env python3
"""Execute FAST1 admission and the resident window helper from compiled RSP ELF.

Original states only. Poison shared BG/OBJ span scratch, then compare dispatch
to a separate per-pixel color-window oracle. This is instruction/semantic
evidence, never real-RCP timing or a full renderer image test.
"""
import argparse
import ast
import operator
import re
import struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols

ROOT = Path(__file__).resolve().parents[1]

def addresses():
    defs = dict(re.findall(r'^#define (\w+) ([^\n]+)', (ROOT/'src/defines.h').read_text(), re.M))
    def evaluate(node):
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.Name): return resolve(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            fn = operator.add if isinstance(node.op, ast.Add) else operator.sub
            return fn(evaluate(node.left), evaluate(node.right))
        raise AssertionError(ast.dump(node))
    def resolve(name): return evaluate(ast.parse(defs[name], mode='eval').body)
    return {n:resolve(n) for n in ('WOBJSEL','WOBJLOG','WHX','CGWSEL','MAIN_COLOR',
                                'WIN_COUNT','WIN_BOUNDS','FRAMEBUFFER','RDP_FRAME',
                                'HCOMP_BAND_RAW','HCOMP_SCREEN')}

def selected(x, selector, logic, bounds):
    lo1,hi1,lo2,hi2=bounds
    one=(lo1<=x<=hi1) ^ bool(selector&1) if selector&2 else False
    two=(lo2<=x<=hi2) ^ bool(selector&4) if selector&8 else False
    enabled=selector&10
    if enabled==2: return one
    if enabled==8: return two
    if enabled==0: return False
    return (one or two, one and two, one != two, one == two)[logic]

def signed(x): return x if x<0x80000000 else x-0x100000000

def execute(imem, dmem, entry, exits, regs):
    pc=entry; pending=None
    for step in range(4000):
        if pc in exits: return pc,regs
        w=struct.unpack_from('>I',imem,pc&0xfff)[0]
        op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31;rd=(w>>11)&31
        imm=w&0xffff;si=imm if imm<0x8000 else imm-0x10000
        target=None
        if op==0:
            fn=w&63;sh=(w>>6)&31
            if fn==0: regs[rd]=regs[rt]<<sh
            elif fn==2: regs[rd]=regs[rt]>>sh
            elif fn==8: target=regs[rs]&0xfff
            elif fn in (32,33): regs[rd]=regs[rs]+regs[rt]
            elif fn in (34,35): regs[rd]=regs[rs]-regs[rt]
            elif fn==36: regs[rd]=regs[rs]&regs[rt]
            elif fn==37: regs[rd]=regs[rs]|regs[rt]
            elif fn==38: regs[rd]=regs[rs]^regs[rt]
            elif fn==43: regs[rd]=int(regs[rs]<regs[rt])
            else: raise AssertionError((hex(pc),hex(w)))
        elif op in (2,3):
            if op==3: regs[31]=pc+8
            target=(w<<2)&0xfff
        elif op in (4,5):
            take=(regs[rs]==regs[rt]) if op==4 else (regs[rs]!=regs[rt])
            if take: target=(pc+4+(si<<2))&0xfff
        elif op in (8,9): regs[rt]=regs[rs]+si
        elif op==11: regs[rt]=int(regs[rs]<(si&0xffffffff))
        elif op==12: regs[rt]=regs[rs]&imm
        elif op==13: regs[rt]=regs[rs]|imm
        elif op==14: regs[rt]=regs[rs]^imm
        elif op==15: regs[rt]=imm<<16
        elif op in (35,36,37,40,41,43):
            addr=(regs[rs]+si)&0xfff
            size={35:4,36:1,37:2,40:1,41:2,43:4}[op]
            assert addr+size<=4096
            if op<40: regs[rt]=int.from_bytes(dmem[addr:addr+size],'big')
            else: dmem[addr:addr+size]=(regs[rt]&((1<<(8*size))-1)).to_bytes(size,'big')
        else: raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None,'control in branch delay slot'
        regs[:]=[v&0xffffffff for v in regs]; regs[0]=0
        pc=pending if pending is not None else (pc+4)&0xfff
        pending=target
    raise AssertionError('FAST1 dispatcher did not terminate')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase',type=Path); ap.add_argument('resident',type=Path)
    args=ap.parse_args()
    base,phase=read_text(args.phase);_,resident=read_text(args.resident)
    assert len(phase)==1000 and len(resident)==4096
    imem=bytearray(resident);offset=base&0xfff;imem[offset:offset+len(phase)]=phase
    syms={n:a&0xfff for a,n in elf_symbols(args.phase)}
    resident_syms={n:a&0xfff for a,n in elf_symbols(args.resident)}
    assert resident_syms['calc_window_spans']==0xce4
    assert syms['hcomp_screen_switch']==0x760
    assert syms['hcomp_math_return']==0x778
    assert syms['hcomp_band_entry']==0x780
    exits={syms['hcomp_compact_band'],syms['hcomp_screen_masks']}
    addr=addresses(); cases=0
    bounds_cases=[(0,255,0,255),(1,254,0,255),(0,254,255,255),(255,255,0,0),
                  (200,100,0,255),(0,0,255,255),(32,127,128,223),(1,2,5,6)]
    scratch_cases=[(0,0,0),(1,0,255),(1,32,127),(3,255,255)]
    for bounds in bounds_cases:
        for selector in range(16):
            for logic in range(4):
                want=all(selected(x,selector,logic,bounds) for x in range(256))
                for count,lo,hi in scratch_cases:
                    dmem=bytearray(4096)
                    dmem[addr['WOBJSEL']]=selector<<4|0xf
                    dmem[addr['WOBJLOG']]=logic<<2|3
                    dmem[addr['WHX']:addr['WHX']+4]=bytes(bounds)
                    dmem[addr['CGWSEL']]=0x12
                    dmem[addr['WIN_COUNT']]=count
                    dmem[addr['WIN_BOUNDS']:addr['WIN_BOUNDS']+2]=bytes((lo,hi))
                    fb=0xA0300000
                    struct.pack_into('>I',dmem,addr['FRAMEBUFFER'],fb)
                    regs=[0]*32;regs[26]=125;regs[27]=126;regs[29]=0
                    end,regs=execute(imem,dmem,syms['hcomp_fast1_probe'],exits,regs)
                    got=end==syms['hcomp_screen_masks']
                    assert got==want,(bounds,selector,logic,count,lo,hi,got,want)
                    assert (regs[26],regs[27],regs[29])==(125,126,0)
                    assert struct.unpack_from('>I',dmem,addr['HCOMP_BAND_RAW'])[0]==(2 if want else 0)
                    if want:
                        assert struct.unpack_from('>I',dmem,addr['RDP_FRAME']+4)[0]==fb-4480
                    cases+=1
    # Changing either prerequisite must reject even with poisoned full spans.
    for cg,color in ((0x02,0),(0x13,0),(0x12,2),(0x12,0xfffe)):
        dmem=bytearray(4096);dmem[addr['CGWSEL']]=cg
        struct.pack_into('>H',dmem,addr['MAIN_COLOR'],color)
        dmem[addr['WIN_COUNT']]=1;dmem[addr['WIN_BOUNDS']+1]=255
        end,_=execute(imem,dmem,syms['hcomp_fast1_probe'],exits,[0]*32)
        assert end==syms['hcomp_compact_band'];cases+=1
    # Main transition overlays existing pixels and changes only screen identity.
    dmem=bytearray([0xa5])*4096;before=bytes(dmem)
    execute(imem,dmem,syms['hcomp_fast1_main'],{syms['hcomp_render_screen']},[0]*32)
    expected=bytearray(before);expected[addr['HCOMP_SCREEN']]=1
    assert dmem==expected,'Main transition clears or redirects the target'
    print(f'HCOMP_FAST1_COMPILED_DISPATCH PASS cases={cases} stale_scratch=covered fixed_entries=preserved native_timing=false')

if __name__=='__main__': main()
