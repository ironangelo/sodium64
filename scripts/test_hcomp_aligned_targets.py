#!/usr/bin/env python3
"""Execute band bases and downstream consumers from compiled RSP banks.

Original geometry only; no game ROM/state/pixels or native timing claims.
Independent pixel-address equations reject aligned bases with stale DMA origins.
"""
import argparse
import ast
import operator
import re
import struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
ROOT = Path(__file__).resolve().parents[1]

def constants():
    defs = dict(re.findall(r'^#define (\w+) ([^\n]+)', (ROOT/'src/defines.h').read_text(), re.M))
    def ev(node):
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.Name): return resolve(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            return (operator.add if isinstance(node.op, ast.Add) else operator.sub)(ev(node.left), ev(node.right))
        raise AssertionError(ast.dump(node))
    def resolve(name): return ev(ast.parse(defs[name], mode='eval').body)
    return {n:resolve(n) for n in ('FB_OFFSET','RDP_FILL','RDP_FRAME','HCOMP_PROOF_RDP_CMDS',
        'HCOMP_BAND_BASES','HCOMP_BAND_ROWS','HCOMP_BAND_Y','STAT_FLAGS','CGADSUB','HCOMP_DIAG_COMPOSE_LIMIT')}

def signed(n): return n if n < 0x80000000 else n-0x100000000

def execute(text, base, dmem, pc, exits, regs):
    pending = None
    for _ in range(4000):
        if pc in exits: return regs
        w = struct.unpack_from('>I', text, pc-base)[0]
        op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31
        imm=w&65535; si=imm if imm<32768 else imm-65536; target=None
        if op == 0:
            fn=w&63; sh=(w>>6)&31
            if fn==0: regs[rd]=regs[rt]<<sh
            elif fn==2: regs[rd]=regs[rt]>>sh
            elif fn==8: target=regs[rs]&0xfff
            elif fn in (32,33): regs[rd]=regs[rs]+regs[rt]
            elif fn in (34,35): regs[rd]=regs[rs]-regs[rt]
            elif fn==36: regs[rd]=regs[rs]&regs[rt]
            elif fn==37: regs[rd]=regs[rs]|regs[rt]
            elif fn==42: regs[rd]=int(signed(regs[rs])<signed(regs[rt]))
            elif fn==43: regs[rd]=int(regs[rs]<regs[rt])
            else: raise AssertionError((hex(pc),hex(w)))
        elif op in (2,3):
            if op==3: regs[31]=pc+8
            target=(w<<2)&0xfff
        elif op in (1,4,5):
            take=(signed(regs[rs])<0 if rt==0 else signed(regs[rs])>=0) if op==1 else ((regs[rs]==regs[rt]) if op==4 else (regs[rs]!=regs[rt]))
            if take: target=(pc+4+(si<<2))&0xfff
        elif op in (8,9): regs[rt]=regs[rs]+si
        elif op==11: regs[rt]=int(regs[rs]<(si&0xffffffff))
        elif op==12: regs[rt]=regs[rs]&imm
        elif op==13: regs[rt]=regs[rs]|imm
        elif op==14: regs[rt]=regs[rs]^imm
        elif op==15: regs[rt]=imm<<16
        elif op in (32,35,36,37,40,41,43):
            address=(regs[rs]+si)&0xfff
            size={32:1,35:4,36:1,37:2,40:1,41:2,43:4}[op]
            assert address+size<=4096
            if op<40:
                val=int.from_bytes(dmem[address:address+size],'big')
                regs[rt]=val-256 if op==32 and val>=128 else val
            else: dmem[address:address+size]=(regs[rt]&((1<<(8*size))-1)).to_bytes(size,'big')
        else: raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None, 'control in delay slot'
        regs[:]=[v&0xffffffff for v in regs]; regs[0]=0
        pc=pending if pending is not None else pc+4
        pending=target
    raise AssertionError('address setup did not terminate')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase',type=Path);ap.add_argument('math',type=Path);ap.add_argument('setup',type=Path)
    args=ap.parse_args()
    pb,phase=read_text(args.phase);mb,math=read_text(args.math)
    pb&=0xfff;mb&=0xfff
    sb,setup=read_text(args.setup);sb&=0xfff
    ss={n:a&0xfff for a,n in elf_symbols(args.setup)}
    ev=parse_macros(ROOT)
    arenas=[ev.name(n)&0x1fffffff for n in ('HCOMP_SUB_ORIGIN','HCOMP_WINNER_ORIGIN','HCOMP_PRESENCE_ORIGIN')]
    ps={n:a&0xfff for a,n in elf_symbols(args.phase)}
    ms={n:a&0xfff for a,n in elf_symbols(args.math)}
    assert len(phase)==len(math)==1000
    assert (ps['hcomp_screen_switch'],ps['hcomp_math_return'],ps['hcomp_band_entry'])==(0x760,0x778,0x780)
    a=constants();cases=0
    def word(d,n): return struct.unpack_from('>I',d,n)[0]
    for y in range(8,248):
        for rows in sorted(set((1, min(8,248-y), min(9,248-y), min(224,248-y),248-y))):
            for queue in (0,4):
                d=bytearray([0xa5])*4096
                struct.pack_into('>I',d,a['FB_OFFSET']+queue,8)
                d[a['STAT_FLAGS']]=0;d[a['CGADSUB']]=1
                struct.pack_into('>I',d,a['HCOMP_DIAG_COMPOSE_LIMIT'],0)
                regs=[0]*32;regs[26]=y-8;regs[27]=y-8+rows;regs[29]=queue
                exitpc=ps.get('hcomp_band_targets_ready',ps['hcomp_compact_band'])
                execute(phase,pb,d,ps['hcomp_band_bounds_ready'],{exitpc},regs)
                z=word(d,a['HCOMP_PROOF_RDP_CMDS']+20)
                sub=word(d,a['RDP_FRAME']+4)
                assert z%64==sub%64==0, ('unaligned',y,rows,hex(z),hex(sub))
                origins=[word(d,a['HCOMP_BAND_BASES']+4*i) for i in range(3)]
                assert origins[0]-origins[1]==0x21000 and origins[2]-origins[1]==0x42000
                assert word(d,a['HCOMP_BAND_Y'])==y and word(d,a['HCOMP_BAND_ROWS'])==rows
                assert struct.unpack_from('>H',d,a['RDP_FILL']+10)[0]==y*4
                assert struct.unpack_from('>H',d,a['RDP_FILL']+14)[0]==(y+rows)*4
                for r in (0,rows-1):
                    for x in (0,12,139,267,279):
                        assert z+2*((y+r)*280+x)==(origins[1]&0x1fffffff)-24+2*(r*280+x)
                        assert sub+2*((y+r)*280+x)==(origins[0]&0x1fffffff)-24+2*(r*280+x)
                for i,bank in enumerate(arenas):
                    lo=(origins[i]&0x1fffffff)-24
                    assert bank-64<=lo and lo+rows*560<=bank+0x20f00
                copy=execute(setup,sb,d,ss['hcomp_setup_copy'],{ss['hcomp_copy_ts']},[0]*32)
                assert copy[14]==origins[1]-24 and copy[15]==origins[2]-24
                assert copy[7]==rows*560
                consumer=execute(math,mb,d,ms['hcomp_math_sources'],{ms['hcomp_row']},[0]*32)
                assert consumer[17:20]==origins and consumer[23]==rows
                cases+=1
    print(f'HCOMP_ALIGNED_TARGETS PASS cases={cases} all_y=8..247 rows=1..240 queues=both consumers=executed native_timing=false')

if __name__=='__main__': main()

