#!/usr/bin/env python3
"""Compiled resident admission versus the existing full bank, original states."""
import argparse,ast,json,operator,re,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_hcomp_aligned_targets import execute

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('main',type=Path)
    ap.add_argument('phase',type=Path);ap.add_argument('fast',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    mb,mt=read_text(a.main);pb,pt=read_text(a.phase);fb,ft=read_text(a.fast)
    sy=lambda p:{n:v&0xfff for v,n in elf_symbols(p)}
    ms,ps,fs=sy(a.main),sy(a.phase),sy(a.fast)
    assert len(mt)==4096 and len(pt)==len(ft)==1000
    assert ms['hcomp_resident_backdrop_admit']==0x22c
    assert ms['hcomp_cgram_consume']==0x2ac
    assert ms['fill_main']==0x2a4 and ms['fill_backdrop']==0x2cc
    assert ps['hcomp_band_start']==0x40c and ps['hcomp_band_entry']==0x780
    defs=dict(re.findall(r'^#define (\w+) ([^\n]+)',(Path(__file__).resolve().parents[1]/'src/defines.h').read_text(),re.M))
    def val(n):
        if isinstance(n,ast.Constant):return n.value
        if isinstance(n,ast.Name):return val(ast.parse(defs[n.id],mode='eval').body)
        if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub)):
            return (operator.add if isinstance(n.op,ast.Add) else operator.sub)(val(n.left),val(n.right))
        raise AssertionError(ast.dump(n))
    addr=lambda n:val(ast.parse(defs[n],mode='eval').body)
    def put(d,n,v):
        sizes={'MAIN_COLOR':2,'SUB_COLOR':2,'HCOMP_DIAG_COMPOSE_LIMIT':4}
        size=sizes.get(n,1);d[addr(n):addr(n)+size]=v.to_bytes(size,'big')
    base={'STAT_FLAGS':0,'CGADSUB':0x20,'CGWSEL':0x12,'MAIN_COLOR':0,'SUB_COLOR':0x1234,'TS':2,'HCOMP_DIAG_COMPOSE_LIMIT':0}
    cases=[]
    for n in ('STAT_FLAGS','CGADSUB','CGWSEL'):
        cases.extend(dict(base,**{n:v}) for v in range(256))
    for color in (0,1,2,0x7bc1,0xffff):
        for ts in range(256):
            for stat in (0,1,0x3f,0x40,0x80,0xc0):cases.append(dict(base,SUB_COLOR=color,TS=ts,STAT_FLAGS=stat))
    for n in ('MAIN_COLOR','HCOMP_DIAG_COMPOSE_LIMIT'):
        cases.extend(dict(base,**{n:v}) for v in (1,2,255,256,65535))
    admitted=delegated=0
    for i,c in enumerate(cases):
        original=bytearray((j*7+3)&255 for j in range(4096))
        for n,v in c.items():put(original,n,v)
        d=original.copy();regs=[0]*32;regs[26]=i%220;regs[27]=min(224,regs[26]+1+i%4);regs[29]=0 if i&1 else 4;regs[25]=0x1780
        # Executing the real HCOMP dispatch must reach this resident helper.
        execute(pt,pb&0xfff,d,ps['hcomp_band_begin'],{ms['hcomp_resident_backdrop_admit']},regs)
        entry=d.copy();before=regs.copy()
        execute(mt,mb&0xfff,d,ms['hcomp_resident_backdrop_admit'],{ps['hcomp_band_start'],ms['overlay_load_slot']},regs)
        chosen=c['STAT_FLAGS']&0xc0==0 and c['CGADSUB']==0x20 and c['CGWSEL']==0x12 and c['MAIN_COLOR']==0 and c['HCOMP_DIAG_COMPOSE_LIMIT']==0 and (c['SUB_COLOR']&0xfffe!=0 or c['TS']&0x1f!=0)
        if chosen:
            legacy=entry.copy();lr=before.copy()
            execute(ft,fb&0xfff,legacy,fs['hcomp_fast_admit'],{ms['overlay_load_slot']},lr)
            assert d==legacy,('resident/full state differs',c)
            assert int.from_bytes(d[addr('HCOMP_BAND_RAW'):addr('HCOMP_BAND_RAW')+4],'big')==2
            assert regs[26:28]==before[26:28] and regs[29]==before[29] and regs[25]==before[25]
            admitted+=1
        else:
            assert d==entry,('fallback modified state',c)
            assert regs[25]==0x13b0 # Existing full admitter entry, unchanged.
            assert regs[5]==int.from_bytes(entry[addr('OVERLAY_HCOMP_FAST_SRC'):addr('OVERLAY_HCOMP_FAST_SRC')+4],'big')
            delegated+=1
    proof=dict(passed=True,cases=len(cases),admitted=admitted,delegated=delegated,
               full_admitter_state_equivalence=True,fallback_preserves_state=True,
               fixed_entries=True,avoided_slot_dma_bytes_per_admitted_section=2000,native_fps_authority=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
    print('HCOMP_RESIDENT_ADMIT PASS',json.dumps(proof))

if __name__=='__main__':main()
