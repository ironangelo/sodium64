#!/usr/bin/env python3
"""Execute fixed-window row DMA, arithmetic, fallback and memory restoration.

Synthetic inputs only; real-console readback and cadence remain separate.
"""
import argparse
import json
import random
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_packed_math import reference, rgba, seeds
from test_hcomp_sub_presence import section
from test_native_diag_arm import load_elf, execute as cpu_execute
from test_rsp_math_dma import ROOT, put
from test_rsp_rdp_half import ReturnVM

FIXED, MATH, PHASE = 0x190000, 0x1a0000, 0x180000


def binding(cpu):
    image, syms = load_elf(cpu)
    original = image.copy()
    addr = parse_macros(ROOT).name
    regs = [0]*32
    regs[8] = syms['rsp_hcomp_math_text_start'] | 5
    start = syms['hcomp_fixed_window_cpu_bind']
    end = syms['hcomp_rdp_cpu_bind_end']
    cpu_execute(image, start, regs, {}, end)
    def read(a): return int.from_bytes(bytes(image[(a+i)&0x1fffffff] for i in range(4)), 'big')
    allowed = set()
    for bank, fallback in (('fixed_window','rsp_hcomp_math_text_start'),
                           ('rdp','rsp_hcomp_fixed_window_text_start')):
        text, data = [syms['rsp_hcomp_'+bank+'_'+s+'_start'] for s in ('text','data')]
        assert data-text == 1000
        assert read(data) == syms[fallback] | 5
        allowed.update(range(data&0x1fffffff,(data&0x1fffffff)+4))
    assert regs[9]&0xe0000000 == 0xa0000000
    top = (0xa4000000+addr('OVERLAY_HCOMP_MATH_SRC'))&0x1fffffff
    assert read(top) == syms['rsp_hcomp_rdp_text_start'] | 5
    allowed.update(range(top,top+4))
    assert all(image[k]==v for k,v in original.items() if k not in allowed)
    return dict(chain='rdp_half,fixed_window,original_math',uncached=True)


def run(build, c, number, fault=None):
    macros = parse_macros(ROOT)
    macros.macros['HCOMP_CGRAM_ARENA'] = '0xA00D2000' # Native trace layout.
    addr = macros.name
    _, maincode = read_text(build/'src/rsp_main.elf')
    _, fixedcode = read_text(build/'src/rsp_hcomp_fixed_window.elf')
    _, mathcode = read_text(build/'src/rsp_hcomp_math.elf')
    _, phasecode = read_text(build/'src/rsp_hcomp.elf')
    assert len(fixedcode)==1000 and len(section(build/'src/rsp_hcomp_fixed_window.elf','.data'))==8
    rows, y, cgws, cad, ts = [c.get(k,v) for k,v in
                             (('rows',3),('y',8),('cgws',0x10),('cad',0xa3),('ts',0))]
    fixed, mask, limit = [c.get(k,v) for k,v in (('fixed',0x294a),('mask','spans'),('limit',0))]
    admitted = not cgws&0xc1 and not cad&0x40 and bool(cgws&0xf2) and not (cgws&2 and ts) and not limit
    d = bytearray(section(build/'src/rsp_main.elf','.data'))
    d[addr('TILE_TABLE'):addr('SCRN_DATA')] = bytes((i*37+11)&255 for i in range(addr('SCRN_DATA')-addr('TILE_TABLE')))
    rng = random.Random(977+number)
    allow = [0xffff if (mask=='all' or mask=='spans' and (x in (0,255) or 17<=x<=93 or 128<=x<=195) or
                       mask=='random' and rng.randrange(2)) else 0 for x in range(256)]
    for x,m in enumerate(allow):
        struct.pack_into('>H',d,addr('TILE_TABLE')+x*2,0xffff)
        struct.pack_into('>H',d,addr('TILE_TABLE')+512+x*2,m)
    main, winner = 0xf2318, (addr('HCOMP_WINNER_ORIGIN')&0x1fffffff)+24
    put(d,addr('HCOMP_BAND_BASES')+4,winner)
    put(d,addr('HCOMP_BAND_ROWS'),rows)
    put(d,addr('HCOMP_DIAG_COMPOSE_LIMIT'),limit)
    put(d,addr('OVERLAY_HCOMP_SRC'),PHASE|3)
    # Deliberately points at a different outer bank. Inner fallback must use
    # its loader-owned source, never re-read the outer descriptor.
    put(d,addr('OVERLAY_HCOMP_MATH_SRC'),0x1b0000|5)
    d[addr('HCOMP_EFFECTIVE_TS')] = ts
    ram = bytearray([0xa5])*0x400000
    ram[FIXED:FIXED+1000] = fixedcode
    struct.pack_into('>II',ram,FIXED+1000,MATH|5,0)
    ram[MATH:MATH+1000] = mathcode
    ram[PHASE:PHASE+1000] = phasecode
    expected = []
    for row in range(rows):
        result = []
        for x in range(256):
            a = (row*256+x)&32767 if mask=='all' else rng.randrange(32768)
            tag = 0xc00 if mask=='all' or (row+x)%3 else 0x400
            struct.pack_into('>H',ram,main+row*560+x*2,rgba(a))
            struct.pack_into('>H',ram,winner+row*560+x*2,tag)
            result.append(reference(a,fixed>>1,bool(cad&0x80),False) if tag==0xc00 and allow[x] else rgba(a))
        expected.append(result)
    before, dbefore = bytes(ram), bytes(d)
    regs = [0]*32
    regs[2],regs[3],regs[5],regs[16],regs[26],regs[27] = cgws,cad,FIXED,main,y,y+rows
    code = bytearray(maincode)
    code[0x3a8:0x790] = fixedcode
    if fault=='restoration':
        # Changing the restore DMA to a write must be caught by readback.
        from test_rsp_math_dma import symbols
        sym = symbols(build/'src/rsp_hcomp_fixed_window.elf')
        pc = sym['hcomp_fixed_window_restore']+12
        assert int.from_bytes(code[pc:pc+4],'big')>>26 == 3
        put(code,pc,0) # Skip the restore reader entirely.
    owners = set(range(addr('TILE_TABLE'),addr('VRAM_TABLE')+1024))
    owners.update(range(addr('SCRN_DATA'),addr('SCRN_DATA')+8))
    owners.update(range(addr('NATIVE_DIAG_RSP_BANK'),addr('NATIVE_DIAG_RSP_BANK')+2))
    backup = addr('HCOMP_CGRAM_SIDEBAND_QUEUE1')&0x1fffffff
    ram_owners = set(range(backup,backup+1024))
    for row in range(rows):ram_owners.update(range(main+row*560,main+row*560+512))
    class RestoringVM(ReturnVM):
        def queue_dma(self, write, length):
            if self.spaddr&0x1000:
                assert self.dmem[addr('VRAM_TABLE'):addr('SCRN_DATA')]==dbefore[addr('VRAM_TABLE'):addr('SCRN_DATA')], 'dirty cache/OAM restoration failed before overlay'
            return super().queue_dma(write,length)
    vm = RestoringVM(code,d,ram,regs,owners,ram_owners,number%5+2,
                  overlays={MATH:5,PHASE:3},stop_bank=3 if admitted else 5)
    vm.v = seeds()
    vm.v[22] = [fixed]*8
    protected = [v[:] for v in vm.v[23:32]]
    vm.pc = 0x3b0
    steps = vm.execute(0x778 if admitted else 0x3b0,require_phase=True)
    assert vm.r[26:28] == [y,y+rows]
    assert vm.v[23:32] == protected
    assert all(d[i]==dbefore[i] for i in range(4096) if i not in owners)
    assert d[addr('VRAM_TABLE'):addr('SCRN_DATA')] == dbefore[addr('VRAM_TABLE'):addr('SCRN_DATA')], 'dirty cache/OAM restoration failed'
    assert all(ram[i]==v for i,v in enumerate(before) if i not in ram_owners)
    data = [t for t in vm.transfers if not t['imem']]
    if not admitted:
        assert ram==before and vm.overlay_history==[5]
        assert vm.r[2:4]==[cgws,cad] and vm.r[16]==main
        assert len(data)==1 and data[0]['ram']==FIXED+1000 and data[0]['size']==8
        return dict(admitted=False,policy=c)
    assert vm.overlay_history==[3] and vm.v[20]==[0]*8
    assert ram[backup:backup+1024] == dbefore[addr('VRAM_TABLE'):addr('VRAM_TABLE')+1024]
    assert all(list(struct.unpack_from('>256H',ram,main+row*560))==values for row,values in enumerate(expected)), 'complete row arithmetic mismatch'
    transfers = [(True,backup,1024,addr('VRAM_TABLE'))]
    for row in range(rows):
        transfers.extend(((False,main+row*560,512,addr('TILE_TABLE')),
                          (False,winner+row*560,512,addr('TILE_TABLE')+512),
                          (True,main+row*560,512,addr('TILE_TABLE'))))
    transfers.append((False,backup,1024,addr('VRAM_TABLE')))
    assert [(t['write'],t['ram'],t['size'],t['sp']) for t in data] == transfers
    assert not vm.captures
    return dict(admitted=True,policy=c,pixels=rows*256,data_dma_calls=len(data),instructions=steps)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build',type=Path);ap.add_argument('--cpu',required=True,type=Path)
    ap.add_argument('--baseline',required=True,type=Path);ap.add_argument('--output',type=Path)
    a = ap.parse_args()
    chain = binding(a.cpu)
    for name in ('rsp_main','rsp_hcomp','rsp_hcomp_math','rsp_hcomp_rdp','rsp_hcomp_setup','rsp_hcomp_tlut'):
        assert read_text(a.build/'src'/f'{name}.elf')[1] == read_text(a.baseline/'src'/f'{name}.elf')[1], (name,'existing bank changed')
    cases = [dict(rows=128,mask='all',cad=c,fixed=f) for c in (0x23,0xa3) for f in (0,0x294a,0xffff)]
    cases += [dict(rows=r,mask=m,cgws=w) for r,m,w in ((1,'none',0x30),(33,'spans',0x10),(224,'random',0x20),(3,'spans',0x12),(2,'all',2))]
    cases += [dict(cgws=w) for w in (0,1,0x41,0x82,0xc2)]
    cases += [dict(cad=0xe3),dict(cgws=0x12,ts=1),dict(limit=8)]
    results = [run(a.build,c,i) for i,c in enumerate(cases)]
    try:run(a.build,dict(rows=3,mask='spans'),0,fault='restoration')
    except AssertionError as e:assert 'restoration failed before overlay' in str(e),str(e)
    else:raise AssertionError('Guard accepted missing cache restore')
    report = dict(passed=True,cases=len(cases),pixels=sum(r.get('pixels',0) for r in results),
                  cpu_binding=chain,old_banks_identical=True,negative_guards=1,commercial_data=False,hardware_fps_claim=False,results=results)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))


if __name__=='__main__':main()
