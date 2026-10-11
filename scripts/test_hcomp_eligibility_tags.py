#!/usr/bin/env python3
"""Linked Main/Sub tag emission, delayed command fetch and staged Math rows.

The primitive/stored-depth pairs are the original renderer contract, not an
RDP rasterizer or hardware proof. Original numeric pixels; Setup is seeded.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_packed_math import TAGS, ENABLES, seeds
from test_hcomp_sub_presence import section
from test_rsp_math_dma import MathVM, ROOT, put, run_case, symbols

CALLER, STOP = 0x790, 0x794
LUT = bytes((0x20,1,2,4,8,0,0x10))
COMPRESSED_CONTRACT = {0x0800:0x0400,0x1800:0x0c00}


class DepthVM(MathVM):
    def __init__(self, code, dmem, regs, owners, delay, stale_current):
        super().__init__(code,dmem,bytearray(),regs,seeds(),delay,owners)
        self.rdp_start,self.current = 0,0
        self.pending_fetch,self.captures = None,[]
        self.stale_current,self.fetch_polls = stale_current,0

    def check_dmem(self,address,size,write=False):
        super().check_dmem(address,size,write)
        if write and self.pending_fetch:
            start,end = self.pending_fetch['start'],self.pending_fetch['end']
            assert not (address < end and start < address+size), 'SCRN reused before command fetch'

    def cop0_write(self,register,value):
        if register == 8:
            assert self.pending_fetch is None
            self.rdp_start = value
        elif register == 9:
            assert self.pending_fetch is None and value-self.rdp_start == 8
            assert 0 <= self.rdp_start < value <= 4096 and value%8 == 0
            self.pending_fetch = dict(start=self.rdp_start,end=value,remaining=self.delay)
            # A previous identical END can equal CURRENT while a new START
            # is still pending; the pending-pointer latch must prevent reuse.
            self.current = value if self.stale_current else self.rdp_start
        else: super().cop0_write(register,value)

    def cop0_read(self,register):
        if register == 10: return self.current
        if register != 11: return super().cop0_read(register)
        self.fetch_polls += 1
        if not self.pending_fetch: return 0
        p = self.pending_fetch
        p['remaining'] -= 1
        if not p['remaining']:
            self.captures.append(bytes(self.dmem[p['start']:p['end']]))
            self.current = p['end']
            self.pending_fetch = None
            return 0
        # In the non-stale case a cleared latch before the final CURRENT
        # advance still requires the second fetch predicate to hold.
        return 0 if not self.stale_current and p['remaining']==1 else 0x400


def commands(addr):
    return [addr('HCOMP_PROOF_RDP_CMDS')+24]+[
        addr('HCOMP_PROOF_BG_DEPTH_CMDS')+i*8 for i in range(4)]+[
        addr('HCOMP_OBJ_DEPTH_CMDS')+i*8 for i in range(2)]


def emission(code,syms,initial,cg,screen,kind,policy=0,fault=None):
    addr = parse_macros(ROOT).name
    d = bytearray(initial)
    d[addr('CGADSUB')],d[addr('HCOMP_SCREEN')] = cg,screen
    put(d,addr('HCOMP_BAND_RAW'),policy)
    command = commands(addr)[kind]
    original = bytes(d[command:command+8])
    assert original == struct.pack('>II',0x2e000000,(kind*0x1000+0x800)<<16)
    before = bytes(d)
    regs = [0xa5000000+i for i in range(32)]
    regs[0],regs[4],regs[5],regs[9],regs[31] = 0,command,command+8,0x90000800^(cg<<16),CALLER
    prior = regs[:]
    scratch = addr('SCRN_DATA')
    vm = DepthVM(code,d,regs,set(range(scratch,scratch+8)),2+kind%3,stale_current=not kind&1)
    vm.pc = syms['hcomp_depth_send']
    # A caller's real SW after the tail call exercises scratch reuse after
    # adoption. It is synthetic harness code, not a production source edit.
    put(vm.code,CALLER,(43<<26)|(10<<16)|scratch)
    if fault == 'pending_latch':
        vm.stale_current = True
        put(vm.code,syms['rdp_fetch_wait']+8,0)
    elif fault == 'current':
        vm.stale_current = False
        put(vm.code,syms['rdp_fetch_wait']+16,0)
    vm.execute(STOP,max_steps=200)
    assert vm.pending_fetch is None
    assert all(regs[i]==prior[i] for i in range(32) if i not in (4,5,8)), ('unowned GPR / t1 OAM clobbered',kind,cg,screen)
    assert all(d[i]==before[i] for i in range(4096) if not scratch <= i < scratch+8), 'DMEM owner changed'
    if policy:
        assert not vm.captures and regs[4:6]==prior[4:6]
        return None
    expected = original if screen==0 else struct.pack('>II',0x2e000000,
                    0x18000000 if ENABLES[kind]&cg else 0x08000000)
    assert vm.captures == [expected], ('primitive tag contract',kind,cg,screen,vm.captures,expected)
    assert regs[4:6] == ([command,command+8] if screen==0 else [scratch,scratch+8])
    assert vm.fetch_polls >= 2
    if screen == 0: return TAGS[kind]
    primitive = struct.unpack_from('>I',vm.captures[0],4)[0]>>16
    return COMPRESSED_CONTRACT[primitive]


def phase_backdrop(code,syms,phase_code,phase_symbols,initial,cg,screen,policy):
    addr = parse_macros(ROOT).name
    d = bytearray(initial)
    d[addr('CGADSUB')],d[addr('HCOMP_SCREEN')] = cg,screen
    put(d,addr('HCOMP_BAND_RAW'),policy)
    before = bytes(d)
    entry = phase_symbols['hcomp_backdrop_color']
    linked_call = struct.unpack_from('>I',phase_code,entry+4-0x3a8)[0]
    assert linked_call>>26 == 3 and (linked_call<<2)&0xfff == syms['hcomp_depth_send'], 'backdrop bypassed tag gate'
    linked = bytearray(code)
    linked[0x3a8:0x790] = phase_code
    regs = [0xa5000000+i for i in range(32)]
    regs[0],regs[9],regs[16] = 0,0x90000800,0x1357
    prior = regs[:]
    scratch = addr('SCRN_DATA')
    vm = DepthVM(linked,d,regs,set(range(scratch,scratch+8)),3,False)
    vm.pc = entry
    vm.execute(entry+12,max_steps=200)
    assert vm.pending_fetch is None
    assert all(regs[i]==prior[i] for i in range(32) if i not in (4,5,8,31)), 'Phase backdrop clobbered owner GPR'
    assert regs[31] == entry+12
    assert all(d[i]==before[i] for i in range(4096) if not scratch <= i < scratch+8), 'Phase backdrop changed DMEM owner'
    expected = [] if policy else [struct.pack('>II',0x2e000000,
        0x08000000 if not screen or not cg&0x20 else 0x18000000)]
    assert vm.captures == expected, ('Phase backdrop tag',cg,screen,policy,vm.captures)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('main',type=Path);ap.add_argument('mode7',type=Path)
    ap.add_argument('math',type=Path);ap.add_argument('phase',type=Path)
    ap.add_argument('--baseline',type=Path,help='wide Math with original class tags')
    ap.add_argument('--output',type=Path)
    a = ap.parse_args()
    addr = parse_macros(ROOT).name
    mb,mc = read_text(a.main);ob,oc = read_text(a.mode7)
    ms,os = symbols(a.main),symbols(a.mode7)
    initial = section(a.main,'.data')
    assert mb&0xfff == ob&0xfff == 0 and len(mc)==len(oc)==len(initial)==4096
    helper = ms['hcomp_eligibility_depth_send']
    assert helper == os['hcomp_eligibility_depth_send'] == 0x48
    assert mc[helper:helper+76] == oc[helper:helper+76], 'Main/Mode7 helpers differ'
    assert initial[0xf0c:0xf13] == LUT
    assert ms['hcomp_tag_enable_lut'] == 0xf0c
    assert all(s['hcomp_depth_send']==0xc4c and s['rdp_send']==0xf5c and s['ret_jump']==0xf70
               for s in (ms,os)), 'fixed resident entries moved'
    # Original immutable commands retain alpha-test/primitive Z update and
    # no Z compare. The predicate is about winners, not depth ordering.
    modes = struct.unpack_from('>II',initial,addr('HCOMP_PROOF_RDP_CMDS')+8)
    assert modes == (0x2f0088ff,0x00040025) and not modes[1]&0x10
    staged = {}
    emitted = 0
    for cg in range(64):
        for screen in (0,1):
            for kind in range(7):
                stored = emission(mc,ms,initial,cg,screen,kind)
                if screen: staged[cg,kind] = stored
                emitted += 1
    mode7 = 0
    for cg in (0,0x3f,0xc0,0xff):
        for screen in (0,1):
            for kind in range(7):
                emission(oc,os,initial,cg,screen,kind)
                mode7 += 1
    bypass = 0
    for policy in (1,2):
        for screen in (0,1):
            for kind in range(7):
                emission(mc,ms,initial,0xff,screen,kind,policy)
                bypass += 1
    negatives = 0
    for fault in ('pending_latch','current'):
        try: emission(mc,ms,initial,0x3f,1,0,fault=fault)
        except AssertionError as e: assert 'SCRN reused before command fetch' in str(e), str(e)
        else: raise AssertionError(('fetch guard did not reject compiled fault',fault))
        negatives += 1
    def load_math(path):
        base,code = read_text(path)
        assert base&0xfff == 0x3a8 and len(code)==1000
        return base&0xfff,code,symbols(path)
    math = load_math(a.math)
    pb,pc = read_text(a.phase)
    assert pb&0xfff == 0x3a8 and len(pc)==1000
    main_image,phase = (mc,initial,ms),(pc,symbols(a.phase))
    backdrop_cases = 0
    for cg in (0,0x20,0x3f,0xff):
        for screen in (0,1):
            for policy in (0,1,2):
                phase_backdrop(mc,ms,pc,phase[1],initial,cg,screen,policy)
                backdrop_cases += 1
    def stage(cg,tags): return [staged[cg&0x3f,TAGS.index(tag)] for tag in tags]
    # Full rows exercise the new one-compare gate with unchanged scalar RGB
    # policy. Binary tags come from actual compiled emission above; Sub stays
    # in its original presence encoding. No new exhaustive vector corpus.
    cases = [(1,0,2,1,0x3f),(3,7,2,31,0x7f),(7,123,2,1,0xbf),
             (1,239,2,1,0xff),(224,0,2,31,0x7f),(3,1,0,0,0x7f),
             (240,0,0,0,0xff),(3,121,2,0,0x7f),(3,0,0x12,1,0x3f),
             (7,127,0xa2,31,0x7f),(1,239,0xf0,0,0xbf),(3,11,0x82,1,0xf5),
             (1,0,0,0,0)]
    rows = [run_case(main_image,math,phase,c,i,winner_stage=stage) for i,c in enumerate(cases)]
    # Invert the linked binary-tag comparison; exact pixel oracle must fail.
    changed = bytearray(math[1]);anchor = math[2]['hcomp_math_mask_ready']+8-math[0]
    word = struct.unpack_from('>I',changed,anchor)[0]
    assert word&63 == 0x21
    put(changed,anchor,(word&~63)|0x22)
    try: run_case(main_image,(math[0],changed,math[2]),phase,cases[0],0,winner_stage=stage)
    except AssertionError as e: assert 'complete row / RDRAM owner changed' in str(e), str(e)
    else: raise AssertionError('pixel oracle accepted inverted binary gate')
    negatives += 1
    report = dict(passed=True,fixture_abi_version=1,eligibility_tags=True,
                  main_emission_cases=emitted,mode7_smoke_cases=mode7,raw_direct_bypasses=bypass,
                  helpers_byte_identical=True,phase_backdrop_cases=backdrop_cases,
                  fixed_resident_entries=True,depth_pairs_source='original_renderer_fixture_contract',
                  primitive_stored_pairs={'0800':'0400','1800':'0C00'},z_compare_disabled=True,
                  sub_commands_unchanged=True,t1_oam_preserved=True,fetch_before_scratch_reuse=True,
                  negative_guards=negatives,math_cases=len(rows),math_rows=sum(c[0] for c in cases),
                  math_pixels=sum(c[0] for c in cases)*256,math_case_results=rows,
                  scope='compiled_emission_fetch_and_staged_math_with_seeded_setup',
                  hardware_mocked=True,rdp_rasterization_authority=False,native_timing_authority=False,
                  private_data=False,elf_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in (a.main,a.mode7,a.math,a.phase)})
    if a.baseline:
        baseline = load_math(a.baseline)
        report['baseline_math_case_results'] = [run_case(main_image,baseline,phase,c,i)
                                               for i,c in enumerate(cases)]
        report['elf_sha256'][str(a.baseline)] = hashlib.sha256(a.baseline.read_bytes()).hexdigest()
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('HCOMP_ELIGIBILITY_TAGS PASS',json.dumps({k:v for k,v in report.items()
          if k not in ('math_case_results','baseline_math_case_results','elf_sha256')}))


if __name__ == '__main__': main()
