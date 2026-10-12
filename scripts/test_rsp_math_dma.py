#!/usr/bin/env python3
"""Execute the linked Math bank, resident DMA helpers and Phase restoration.

Original numeric pixels only. Setup outputs are seeded independently; the
oracle compares complete rows and guarded memory, not hardware/RDP timing.
"""
import argparse
import hashlib
import json
import random
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_packed_math import TAGS, ENABLES, reference, rgba, seeds, vector_instruction
from test_hcomp_sub_presence import section
from test_rsp_sparse_vram import RspVM

ROOT = Path(__file__).resolve().parents[1]
PHASE_BANK = 0x180000


class MathVM(RspVM):
    """Reuse the delayed-DMA ownership model and packed vector decoder."""
    def __init__(self, code, dmem, ram, regs, vectors, delay, owners):
        super().__init__(code, dmem, ram, regs, vectors, delay, b'')
        self.owners = owners
        self.sp_status = (self.sp_status & ~(7 << 11)) | (5 << 11)
        self.initial_sp_status = self.sp_status
        self.phase_loaded = False

    def check_dmem(self, address, size, write=False):
        super().check_dmem(address, size, write)
        if write:
            assert all(i in self.owners for i in range(address, address+size)), (
                'DMEM owner write', hex(self.pc), hex(address), size)

    def poll_dma(self):
        if self.dma is None: return 0
        self.dma['polls'] -= 1
        if self.dma['polls']: return 1
        pending = self.dma
        target = self.code if pending['imem'] else self.dmem
        sp, ram, size = pending['sp'], pending['ram'], pending['size']
        if pending['write']:
            self.ram[ram:ram+size] = target[sp:sp+size]
        else:
            if not pending['imem']:
                assert all(i in self.owners for i in range(sp, sp+size)), 'DMA overwrote DMEM owner'
            target[sp:sp+size] = self.ram[ram:ram+size]
        self.transfers.append({k:v for k,v in pending.items() if k != 'polls'})
        if pending['imem']:
            assert ram == PHASE_BANK and sp == 0x3a8 and size == 1000
            self.phase_loaded = True
            if self.signal_profile:
                assert self.sp_status & (7 << 11) == 0
                self.completed_overlay_bank = 3
        self.dma = None
        return 0

    def cop0_read(self, register):
        assert register in (6,11)
        return self.poll_dma() if register == 6 else 0

    def cop0_write(self, register, value):
        if register == 0: self.spaddr = value
        elif register == 1: self.ramaddr = value
        elif register in (2,3): self.queue_dma(register==3,value)
        elif register == 4: self.write_status(value)
        else: raise AssertionError(('COP0 write',register))

    def execute(self, stop, max_steps=1500000, require_phase=False):
        for steps in range(max_steps):
            # Math and Phase deliberately share this overlay slot. An address
            # reached in Math is not the Phase stop until its DMA has retired.
            if self.pc == stop and (not require_phase or self.phase_loaded):
                assert self.branch is None and self.dma is None, 'Phase reached before DMA retirement'
                return steps
            if self.dma and self.dma['imem']:
                p = self.dma
                assert not p['sp'] <= self.pc < p['sp']+p['size'], 'executing overwritten slot'
            w = struct.unpack_from('>I', self.code, self.pc)[0]
            op, rs, rt, rd = w>>26, w>>21&31, w>>16&31, w>>11&31
            fn, sh, imm = w&63, w>>6&31, w&65535
            si = imm if imm < 32768 else imm-65536
            target = None
            if op == 0:
                if fn == 0: self.r[rd] = self.r[rt] << sh
                elif fn == 2: self.r[rd] = self.r[rt] >> sh
                elif fn == 3:
                    value = self.r[rt] if self.r[rt] < 0x80000000 else self.r[rt]-0x100000000
                    self.r[rd] = value >> sh
                elif fn == 4: self.r[rd] = self.r[rt] << (self.r[rs]&31)
                elif fn == 6: self.r[rd] = self.r[rt] >> (self.r[rs]&31)
                elif fn == 7:
                    value = self.r[rt] if self.r[rt] < 0x80000000 else self.r[rt]-0x100000000
                    self.r[rd] = value >> (self.r[rs]&31)
                elif fn == 8: target = self.r[rs] & 0xfff
                elif fn in (32,33): self.r[rd] = self.r[rs]+self.r[rt]
                elif fn in (34,35): self.r[rd] = self.r[rs]-self.r[rt]
                elif fn == 36: self.r[rd] = self.r[rs]&self.r[rt]
                elif fn == 37: self.r[rd] = self.r[rs]|self.r[rt]
                elif fn == 38: self.r[rd] = self.r[rs]^self.r[rt]
                elif fn == 42:
                    a = self.r[rs] if self.r[rs] < 0x80000000 else self.r[rs]-0x100000000
                    b = self.r[rt] if self.r[rt] < 0x80000000 else self.r[rt]-0x100000000
                    self.r[rd] = int(a<b)
                elif fn == 43: self.r[rd] = int(self.r[rs]<self.r[rt])
                else: raise AssertionError(('scalar', hex(self.pc), hex(w)))
            elif op in (2,3):
                if op == 3: self.r[31] = self.pc+8
                target = (w<<2)&0xfff
            elif op == 1:
                assert rt in (0,1), 'unsupported REGIMM fixture branch'
                negative = bool(self.r[rs]&0x80000000)
                if negative == (rt==0): target = (self.pc+4+(si<<2))&0xfff
            elif op in (4,5):
                if (self.r[rs]==self.r[rt]) == (op==4): target = (self.pc+4+(si<<2))&0xfff
            elif op in (6,7):
                value = self.r[rs] if self.r[rs] < 0x80000000 else self.r[rs]-0x100000000
                if (value<=0) == (op==6): target = (self.pc+4+(si<<2))&0xfff
            elif op in (8,9): self.r[rt] = self.r[rs]+si
            elif op == 10:
                value = self.r[rs] if self.r[rs] < 0x80000000 else self.r[rs]-0x100000000
                self.r[rt] = int(value<si)
            elif op == 11: self.r[rt] = int(self.r[rs]<(si&0xffffffff))
            elif op == 12: self.r[rt] = self.r[rs]&imm
            elif op == 13: self.r[rt] = self.r[rs]|imm
            elif op == 14: self.r[rt] = self.r[rs]^imm
            elif op == 15: self.r[rt] = imm<<16
            elif op in (32,33,35,36,37,40,41,43):
                address = (self.r[rs]+si)&0xfff
                size = {32:1,33:2,35:4,36:1,37:2,40:1,41:2,43:4}[op]
                self.check_dmem(address,size,op>=40)
                if op < 40:
                    self.r[rt] = int.from_bytes(self.dmem[address:address+size],'big',signed=op in (32,33))
                else: self.dmem[address:address+size] = (self.r[rt]&((1<<(size*8))-1)).to_bytes(size,'big')
            elif op in (50,58):
                element, operation, offset = w>>7&15, w>>11&31, w&127
                offset = offset if offset < 64 else offset-128
                assert operation in (3,4,6), ('unsupported vector memory operation',operation)
                size = 16 if operation == 4 else 8
                address = (self.r[rs]+offset*size)&0xfff
                if operation == 6:
                    # Decoder LPV/SPV e0: eight consecutive packed bytes into
                    # the upper byte of each lane; no untested element modes.
                    assert element == 0
                    addresses=[(address&~7)+((address&7)+i&15) for i in range(8)]
                    for p in addresses:self.check_dmem(p,1,op==58)
                    if op == 50:self.v[rt]=[self.dmem[p]<<8 for p in addresses]
                    else:
                        for i,p in enumerate(addresses):self.dmem[p]=self.v[rt][i]>>8
                else:
                    assert address%size == 0 and (element in (0,8) if size==8 else element==0)
                    self.check_dmem(address,size,op==58)
                    lane = element//2
                    if op == 50:
                        self.v[rt][lane:lane+size//2] = struct.unpack_from('>'+str(size//2)+'H',self.dmem,address)
                    else:
                        struct.pack_into('>'+str(size//2)+'H',self.dmem,address,*self.v[rt][lane:lane+size//2])
            elif op == 18:
                if rs == 0:
                    element = w>>7&15
                    assert not element&1, 'unaligned MFC2 fixture element'
                    value = self.v[rd][element//2]
                    self.r[rt] = value if value < 0x8000 else value-0x10000
                else:
                    self.vco_lo,self.vco_hi,self.vcc = vector_instruction(
                        w,self.r,self.v,self.vco_lo,self.vco_hi,self.vcc)
            elif op == 16:
                if rs == 0: self.r[rt] = self.cop0_read(rd)
                elif rs == 4: self.cop0_write(rd,self.r[rt])
                else: raise AssertionError(('COP0',rs))
            else: raise AssertionError(('instruction',hex(self.pc),hex(w)))
            assert self.branch is None or target is None, 'control in delay slot'
            self.r[:] = [value&0xffffffff for value in self.r]
            self.r[0] = 0
            self.pc,self.branch = (self.branch if self.branch is not None else self.pc+4),target
        raise AssertionError('Math band did not finish')


def symbols(path): return {name:value&0xfff for value,name in elf_symbols(path)}
def put(d,address,value): struct.pack_into('>I',d,address,value&0xffffffff)
def halves(d,address,values): struct.pack_into('>'+str(len(values))+'H',d,address,*values)


def run_case(main, math, phase, c, case_id, control=False, fault=None, winner_stage=None,
             masks=None, expected_wide=None):
    addr = parse_macros(ROOT).name
    main_code, initial_dmem, main_symbols = main
    math_base, math_code, math_symbols = math
    phase_code, phase_symbols = phase
    rows,y,cgwsel,ts,cgadsub = c
    assert 0 <= y < 240 and 1 <= rows <= 240-y
    uniform, row_fixed = not cgwsel&0xf0, not cgwsel&0xf2
    wide = uniform and not control if expected_wide is None else expected_wide
    has_sub = bool(cgwsel&2 and ts)
    queue, pad = (case_id&1)*4, ((y+8)*16)&63
    framebuffer = 0x0f2300
    origins = [addr(name)&0x1fffffff for name in
               ('HCOMP_SUB_ORIGIN','HCOMP_WINNER_ORIGIN','HCOMP_PRESENCE_ORIGIN')]
    starts = [framebuffer+y*560+24]+[origin+24-pad for origin in origins]
    fixed_ptr = addr('HCOMP_ROW_FIXED_QUEUE1' if queue==0 else 'HCOMP_ROW_FIXED_QUEUE2')&0x1fffffff
    d = bytearray(initial_dmem)
    # Poison scratch and immutable owners separately; Setup's real outputs
    # below replace only the mask/row-color table and section parameters.
    d[:] = bytes((i*37+11)&255 for i in range(4096))
    rng = random.Random(0x364000+case_id)
    ram = bytearray([0xa5])*0x400000
    fixed_rows = [rgba((i*977+0x421)&0x7fff) for i in range(256)]
    halves(ram,fixed_ptr,fixed_rows)
    fixed = (0x1234+case_id*31)&0x7fff
    selected = [x in (0,1,127,128,254,255) or 61<=x<=93 for x in range(256)]
    def allowed(selector, inside):
        return (True,inside,not inside,False)[selector]
    clip = [0xffff if allowed(cgwsel>>6,inside) else 0 for inside in selected]
    allow = [0xffff if allowed(cgwsel>>4&3,inside) else 0 for inside in selected]
    if masks is not None:
        clip,allow = map(list,masks)
        assert len(clip)==len(allow)==256 and not row_fixed
    halves(d,addr('TILE_TABLE'),clip)
    if row_fixed: halves(d,addr('TILE_TABLE')+512,fixed_rows)
    else: halves(d,addr('TILE_TABLE')+512,allow)
    put(d,addr('OVERLAY_HCOMP_SRC'),PHASE_BANK|3)
    put(d,addr('HCOMP_ROW_FIXED_SRC'),fixed_ptr)
    for i,origin in enumerate(starts[1:]): put(d,addr('HCOMP_BAND_BASES')+4*i,origin)
    put(d,addr('HCOMP_BAND_ROWS'),rows)
    d[addr('HCOMP_EFFECTIVE_TS')] = ts
    # Resident signal loader needs its immutable halfwords even with poisoned
    # OAM/VRAM/stats. The non-signal loader owns only its epoch halfword.
    masks = addr('NATIVE_DIAG_SIGNAL_MASKS')
    d[masks:masks+16] = initial_dmem[masks:masks+16]
    struct.pack_into('>H',d,addr('NATIVE_DIAG_RSP_BANK'),0x1235)
    ram[PHASE_BANK:PHASE_BANK+1000] = phase_code
    expected_rows = []
    for row in range(rows):
        main_pixels = [rng.randrange(32768) for _ in range(256)]
        sub_pixels = [rng.randrange(32768) for _ in range(256)]
        main_pixels[0],main_pixels[255] = (row*31)&0x7fff,0x7fff
        sub_pixels[0],sub_pixels[255] = 0x7fff,(row*0x421)&0x7fff
        tags = [TAGS[(x+row)%len(TAGS)] for x in range(256)]
        absent = [(x+row)%5==0 for x in range(256)]
        stored_tags = winner_stage(cgadsub,tags) if winner_stage else tags
        for start,values in zip(starts,(list(map(rgba,main_pixels)),list(map(rgba,sub_pixels)),
                                       stored_tags,[0x400 if a else 0xc00 for a in absent])):
            halves(ram,start+row*560,values)
        actual_fixed = fixed_rows[y+row]>>1 if row_fixed else fixed
        result = []
        for x in range(256):
            color = (rgba(main_pixels[x])&clip[x])>>1
            eligible = bool(ENABLES[TAGS.index(tags[x])]&cgadsub and allow[x])
            operand = sub_pixels[x] if has_sub and not absent[x] else actual_fixed
            half = bool(cgadsub&0x40 and clip[x] and not (cgwsel&2 and (not ts or absent[x])))
            result.append(reference(color,operand,bool(cgadsub&0x80),half) if eligible else rgba(color))
        expected_rows.append(result)
    expected_ram = ram.copy()
    for row,values in enumerate(expected_rows): halves(expected_ram,starts[0]+row*560,values)
    before_dmem = bytes(d)
    regs = [0xcafe0000+i for i in range(32)]
    regs[0],regs[2],regs[3],regs[16],regs[26],regs[29] = 0,cgwsel,cgadsub,starts[0],y,queue
    vectors = seeds()
    vectors[22] = [rgba(fixed)]*8
    vectors[20][:6] = [tag if bit&cgadsub else 0 for tag,bit in
                       zip((0xc00,0x1400,0x1c00,0x2800,0x5000,0x400),(1,2,4,8,0x10,0x20))]
    for i in range(23,31): vectors[i] = [rng.randrange(65536) for _ in range(8)]
    constants = [v[:] for v in vectors[23:32]]
    owned = set(range(addr('SCRN_DATA'),addr('SCRN_DATA')+256))
    if wide: owned.update(range(addr('TILE_TABLE'),addr('VRAM_TABLE')))
    owned.update(range(addr('NATIVE_DIAG_RSP_BANK'),addr('NATIVE_DIAG_RSP_BANK')+2))
    code = bytearray(main_code)
    code[math_base:math_base+len(math_code)] = math_code
    vm = MathVM(code,d,ram,regs,vectors,case_id%3+2,owned)
    vm.pc = math_symbols['hcomp_math_sources']
    if fault == 'dma_wait': put(vm.code,main_symbols['dma_wait']+4,0)
    elif fault == 'owner':
        for pc in range(math_symbols['hcomp_math_sources'],math_symbols['hcomp_row'],4):
            w = struct.unpack_from('>I',vm.code,pc)[0]
            if w>>26 == 35 and w&65535 == addr('HCOMP_BAND_BASES'):
                put(vm.code,pc,(w&0x03ffffff)|(43<<26));break
        else: raise AssertionError('owner mutation anchor missing')
    steps = vm.execute(phase_symbols['hcomp_band_done'],require_phase=True)
    assert vm.ram == expected_ram, ('complete row / RDRAM owner changed',c)
    assert all(d[i] == before_dmem[i] for i in range(4096) if i not in owned), 'DMEM owner changed'
    assert vectors[23:32] == constants and vectors[20] == [0]*8
    assert regs[29] == queue and regs[16] == starts[0]+rows*560
    assert vm.code == main_code[:math_base]+phase_code+main_code[math_base+1000:], 'Phase slot not restored exactly'
    overlays = [t for t in vm.transfers if t['imem']]
    assert len(overlays) == 1 and overlays[0]['ram'] == PHASE_BANK
    if vm.signal_profile:
        assert vm.signal_writes == [0,3] and vm.sp_status>>11&7 == 3
        assert vm.sp_status & ~(7<<11) == vm.initial_sp_status & ~(7<<11)
    else: assert struct.unpack_from('>H',d,addr('NATIVE_DIAG_RSP_BANK'))[0] == 0x1243
    data = [t for t in vm.transfers if not t['imem']]
    batch = 256 if wide else 64
    expected = []
    for row in range(rows):
        if row_fixed and not control:
            expected.append((False,(fixed_ptr+2*(y+row))&~7,8,addr('SCRN_DATA')))
        for offset in range(0,512,batch):
            scratch = addr('TILE_TABLE') if batch==256 else addr('SCRN_DATA')
            expected.extend((False,starts[i]+row*560+offset,batch,scratch+lane*batch)
                            for i,lane in ((0,0),(2,2)))
            if has_sub:
                expected.extend((False,starts[i]+row*560+offset,batch,scratch+lane*batch)
                                for i,lane in ((1,1),(3,3)))
            expected.append((True,starts[0]+row*560+offset,batch,scratch))
    assert [(t['write'],t['ram'],t['size'],t['sp']) for t in data] == expected, ('DMA row/batch ABI',c)
    return dict(rows=rows,y=y,cgwsel=cgwsel,ts=ts,cgadsub=cgadsub,batch_pixels=batch//2,
                data_dma_calls=len(data),data_dma_bytes=sum(t['size'] for t in data),
                fixed_row_dma_calls=rows if row_fixed and not control else 0,instructions=steps)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('main',type=Path);ap.add_argument('math',type=Path);ap.add_argument('phase',type=Path)
    ap.add_argument('--control',action='store_true',help='expect historical 32px uniform bank')
    ap.add_argument('--baseline',type=Path,help='also execute the historical Math bank')
    ap.add_argument('--output',type=Path)
    a = ap.parse_args()
    main_base,main_code = read_text(a.main)
    phase_base,phase_code = read_text(a.phase)
    assert main_base&0xfff == 0 and phase_base&0xfff == 0x3a8
    assert len(main_code) == 4096 and len(phase_code) == 1000
    main_image = main_code,section(a.main,'.data'),symbols(a.main)
    phase_image = phase_code,symbols(a.phase)
    def load_math(path):
        base,code = read_text(path)
        assert base&0xfff == 0x3a8 and len(code) == 1000
        return base&0xfff,code,symbols(path)
    math_image = load_math(a.math)
    cases = [(1,0,2,1,0x3f),(3,7,2,31,0x7f),(7,123,2,1,0xbf),(1,239,2,1,0xff),
             (224,0,2,31,0x7f),(1,0,0,0,0x3f),(3,1,0,0,0x7f),(7,121,0,0,0xbf),
             (240,0,0,0,0xff),(3,121,2,0,0x7f),(1,239,1,0,0x7f),
             (3,0,0x12,1,0x3f),(7,127,0xa2,31,0x7f),(1,239,0xf0,0,0xbf),
             (3,11,0x82,1,0xf5),(1,0,0,0,0)]
    results = [run_case(main_image,math_image,phase_image,c,i,a.control) for i,c in enumerate(cases)]
    negatives = 0
    for fault,message in (('dma_wait','DMA'),('owner','DMEM owner write')):
        try: run_case(main_image,math_image,phase_image,cases[0],0,a.control,fault)
        except AssertionError as e:
            assert message in str(e), (fault,str(e))
            negatives += 1
        else: raise AssertionError(('guard did not reject linked fault',fault))
    report = dict(passed=True,fixture_abi_version=2,control=a.control,
                  scope='linked_math_dma_and_phase_return_with_seeded_setup_outputs',
                  diagnostic_banks=dict(math=5,phase=3),
                  cases=len(results),rows=sum(c[0] for c in cases),
                  pixels=sum(c[0] for c in cases)*256,negative_guards=negatives,
                  delayed_dma=True,complete_row_scalar_oracle=True,dmem_rdram_owners=True,
                  phase_slot_restored=True,vector_constants_preserved=True,
                  setup_outputs_seeded=True,hardware_mocked=True,native_timing_authority=False,
                  ordinary_rdp_frame_authority=False,private_data=False,case_results=results,
                  elf_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.main,a.math,a.phase)})
    if a.baseline:
        baseline = load_math(a.baseline)
        report['baseline_case_results'] = [run_case(main_image,baseline,phase_image,c,i,True)
                                           for i,c in enumerate(cases)]
        report['elf_sha256'][str(a.baseline)] = hashlib.sha256(a.baseline.read_bytes()).hexdigest()
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('RSP_MATH_DMA_ROW PASS',json.dumps({k:v for k,v in report.items() if k not in ('case_results','baseline_case_results','elf_sha256')}))


if __name__ == '__main__': main()
