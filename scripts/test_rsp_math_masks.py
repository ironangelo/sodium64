#!/usr/bin/env python3
"""Compiled mask scanner classifications, complete rows and delayed DMA.

Expected wide/narrow decisions are stipulated by constructed input cases.
The pixel oracle is independent scalar math; Setup outputs are seeded, and
no RDP rasterization, hardware timing or ordinary framebuffer claim is made.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_hcomp_eligibility_tags import emission
from test_hcomp_packed_math import TAGS
from test_hcomp_sub_presence import section
from test_rsp_math_dma import put, run_case, symbols


def load(path):
    base,code = read_text(path)
    return base&0xfff,code,symbols(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('main',type=Path);ap.add_argument('math',type=Path);ap.add_argument('phase',type=Path)
    ap.add_argument('--baseline',type=Path,required=True,help='tags Math with scanner disabled')
    ap.add_argument('--output',type=Path)
    a = ap.parse_args()
    mb,mc,ms = load(a.main)
    math = load(a.math)
    pb,pc,ps = load(a.phase)
    baseline = load(a.baseline)
    initial = section(a.main,'.data')
    assert mb==0 and pb==math[0]==baseline[0]==0x3a8
    assert len(mc)==len(initial)==4096 and len(pc)==len(math[1])==len(baseline[1])==1000
    assert 'hcomp_mask_scan' in math[2] and 'hcomp_mask_scan' not in baseline[2]
    assert math[2]['hcomp_screen_switch']==baseline[2]['hcomp_screen_switch']==0x760
    assert math[2]['draw_mode7_entry']==baseline[2]['draw_mode7_entry']==0x788
    def core(image):
        base,code,syms = image
        return code[syms['hcomp_channels_start']-base:syms['hcomp_vector_output']+4-base]
    assert core(math)==core(baseline), 'RGB555 kernel changed'
    for name,current in (('rsp_main.elf',mc),('rsp_hcomp.elf',pc)):
        assert load(a.baseline.parent/name)[1]==current, ('non-Math bank changed',name)
    main_image,phase = (mc,initial,ms),(pc,ps)
    staged = {}
    def stage(cg,tags):
        key = cg&0x3f
        if key not in staged:
            staged[key] = [emission(mc,ms,initial,key,1,kind) for kind in range(7)]
        return [staged[key][TAGS.index(tag)] for tag in tags]
    results,baseline_results = [],[]
    def check(name,clip,allow,wide,c=(1,0,0x52,1,0x7f),compare=False,image=math):
        masks = None if clip is None else (clip,allow)
        result = run_case(main_image,image,phase,c,len(results),winner_stage=stage,
                          masks=masks,expected_wide=wide)
        result['case'] = name
        results.append(result)
        if compare:
            original_wide = not c[2]&0xf0
            old = run_case(main_image,baseline,phase,c,len(results)-1,winner_stage=stage,
                           masks=masks,expected_wide=original_wide)
            old['case'] = name
            baseline_results.append(old)
    # Each combination is an independent accepted policy, including zero
    # constants; CGWSEL F0 is nonzero in every scanned case.
    pairs = [(0,0,0xf2),(0,0xffff,0xc2),(0xffff,0,0x32),(0xffff,0xffff,0x52)]
    for clip,allow,cgwsel in pairs:
        check(f'uniform_{clip:04x}_{allow:04x}',[clip]*256,[allow]*256,True,
              (3,7,cgwsel,1,0xff),compare=True)
    # Reject a divergent halfword at every vector/lane of each input array.
    # That includes x0 and x255 and permits no sampled-uniformity shortcut.
    for array in range(2):
        for x in range(256):
            masks = [[0xffff]*256,[0xffff]*256]
            masks[array][x] = 0
            check(f'vary_array{array}_x{x}',*masks,False,
                  compare=x in (0,7,8,247,248,255))
    # Equal arrays can still contain invalid mask constants; inspect lane0
    # independently. Invalid tails exercise comparison after valid lane0.
    invalid = 0
    for array in range(2):
        for value in (1,0x7fff,0xfffe):
            for all_lanes in (False,True):
                masks = [[0xffff]*256,[0xffff]*256]
                if all_lanes: masks[array] = [value]*256
                else: masks[array][255] = value
                check(f'invalid_array{array}_{value:04x}_'+('flat' if all_lanes else 'tail'),
                      *masks,False,compare=True)
                invalid += 1
    # F0==0 must retain the pre-existing path; F2==0's upper half contains
    # varying row colors, never a second mask array. Both queues and absent
    # Sub remain covered by the actual row/DMA fixture.
    for c in ((7,121,0,0,0x7f),(3,7,2,0,0xff),(3,0,2,1,0x3f)):
        check('flat_existing_'+str(c[2])+'_'+str(c[3]),None,None,True,c,compare=True)
    # One full-height promoted band checks scan-once lifetime, row stepping
    # and scratch reuse well beyond the first output batch.
    check('uniform_full_height',[0xffff]*256,[0xffff]*256,True,(240,0,0x52,31,0x7f),compare=True)
    negatives = 0
    scan = math[2]['hcomp_mask_scan']-math[0]
    for fault,offset,clip,allow,message in (
        ('incoming_vco',scan-4,[0xffff]*256,[0xffff]*256,'DMA row/batch ABI'),
        ('invalid_first_lane',None,[1]*256,[0xffff]*256,'DMA overwrote DMEM owner'),
        ('ignored_last_divergence',scan+32,[0xffff]*255+[0],[0xffff]*256,'DMA overwrote DMEM owner')):
        changed = bytearray(math[1])
        if offset is None:
            for index in range(0,scan,4):
                word = struct.unpack_from('>I',changed,index)[0]
                if word>>26==5:
                    offset = index;break
            assert offset is not None
        word = struct.unpack_from('>I',changed,offset)[0]
        assert word&63==0x23 if fault=='incoming_vco' else word>>26==5
        put(changed,offset,0)
        try:
            run_case(main_image,(math[0],changed,math[2]),phase,(1,0,0x52,1,0x7f),0,
                     winner_stage=stage,masks=(clip,allow),expected_wide=fault=='incoming_vco')
        except AssertionError as e: assert message in str(e), (fault,str(e))
        else: raise AssertionError(('scanner guard accepted linked fault',fault))
        negatives += 1
    report = dict(passed=True,fixture_abi_version=1,mask_scan=True,control=False,
                  cases=len(results),uniform_pairs=4,individual_divergences=512,
                  invalid_mask_cases=invalid,full_height_rows=240,
                  baseline_cases=len(baseline_results),negative_guards=negatives,
                  incoming_vco_all_ones=True,kernel_byte_identical=True,other_banks_byte_identical=True,
                  full_row_scalar_oracle=True,delayed_dma_ownership=True,phase_slot_restored=True,
                  scope='linked_math_mask_scan_with_explicit_seeded_masks_and_independent_pixel_oracle',
                  hardware_mocked=True,rdp_rasterization_authority=False,native_timing_authority=False,
                  private_data=False,case_results=results,baseline_case_results=baseline_results,
                  elf_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (a.main,a.math,a.phase,a.baseline)})
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('RSP_MATH_MASK_SCAN PASS',json.dumps({k:v for k,v in report.items()
          if k not in ('case_results','baseline_case_results','elf_sha256')}))


if __name__ == '__main__': main()
