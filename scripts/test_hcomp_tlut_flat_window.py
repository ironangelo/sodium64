#!/usr/bin/env python3
"""Compiled section-uniform COLOR admission against independent x-by-x truth."""
import argparse, json, struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_tlut_candidate import link_images, ShaderVM, generation, class_bindings
from test_hcomp_tlut_transform import ROOM
from test_rsp_math_dma import ROOT, put, symbols

class Stops:
    def __init__(self,*pcs): self.pcs=set(pcs)
    def __eq__(self,pc): return pc in self.pcs

def selected(x,sel,logic,edges):
    enabled=[]
    for index in (0,1):
        if sel & (2 << (index*2)):
            inside=edges[index*2]<=x<=edges[index*2+1]
            enabled.append(inside ^ bool(sel & (1 << (index*2))))
    if not enabled: return False
    if len(enabled)==1: return enabled[0]
    a,b=enabled
    return (a or b, a and b, a != b, a == b)[logic]

def decision(images,cgwsel,sel,logic,edges,fault=None):
    code,initial,_,_,_,ts,_=images
    addr=parse_macros(ROOT).name
    d=bytearray(initial)
    d[addr('CGWSEL')]=cgwsel
    d[addr('STAT_FLAGS')]=0
    d[addr('WOBJSEL')]=(sel<<4)|9
    d[addr('WOBJLOG')]=(logic<<2)|2
    d[addr('WHX'):addr('WHX')+4]=bytes(edges)
    put(d,addr('HCOMP_DIAG_COMPOSE_LIMIT'),0)
    before=bytes(d)
    r=[0]*32;r[26]=32;r[27]=72
    owners=set(range(addr('WIN_BOUNDS'),addr('WIN_BOUNDS')+6))|{addr('WIN_COUNT')}
    vm=ShaderVM(code,d,bytearray(1),r,owners,set(),2,overlays={})
    if fault=='hole': put(vm.code,ts['hcomp_tlut_flat_span_check'],0)
    vm.pc=ts['hcomp_tlut_probe']
    steps=vm.execute(Stops(ts['hcomp_tlut_window_ready'],ts['hcomp_tlut_reject']),max_steps=4000)
    assert r[26:28]==[32,72]
    assert all(d[i]==before[i] for i in range(4096) if i not in owners)
    mode=(cgwsel>>4)&3
    allow=[mode==0 or (mode==1 and selected(x,sel,logic,edges)) or
           (mode==2 and not selected(x,sel,logic,edges)) for x in range(256)]
    expected=not cgwsel&0xc1 and all(allow)
    actual=vm.pc==ts['hcomp_tlut_window_ready']
    assert actual==expected, ('COLOR hole admitted',cgwsel,sel,logic,edges,actual,expected)
    return actual,steps

def setup_mask(images,setup_path,cgwsel,sel,logic,edges):
    """Execute the original linked Setup mask producer, not shader logic."""
    addr=parse_macros(ROOT).name
    code=bytearray(images[2]);code[0x3a8:0x790]=read_text(setup_path)[1]
    d=bytearray(images[1]);d[addr('CGWSEL')]=cgwsel|2
    d[addr('WOBJSEL')]=sel<<4;d[addr('WOBJLOG')]=logic<<2
    d[addr('WHX'):addr('WHX')+4]=bytes(edges)
    owners=set(range(addr('WIN_BOUNDS'),addr('WIN_BOUNDS')+6))|{addr('WIN_COUNT')}
    owners.update(range(addr('SCRN_DATA'),addr('SCRN_DATA')+16))
    owners.update(range(addr('TILE_TABLE'),addr('TILE_TABLE')+1024))
    r=[0]*32;r[26]=32;r[27]=72
    vm=ShaderVM(code,d,bytearray(0x100000),r,owners,set(range(0xf0000,0xf0010)),2,overlays={})
    s=symbols(setup_path);vm.pc=s['hcomp_setup_entry']
    vm.execute(s['hcomp_vector_constants'],max_steps=20000)
    actual=[struct.unpack_from('>H',d,addr('TILE_TABLE')+512+x*2)[0]==65535 for x in range(256)]
    mode=(cgwsel>>4)&3
    expected=[mode==0 or (mode==1 and selected(x,sel,logic,edges)) or
              (mode==2 and not selected(x,sel,logic,edges)) for x in range(256)]
    assert actual==expected, ('baseline Setup COLOR truth differs',cgwsel,sel,logic,edges)
    return 256

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build',type=Path);ap.add_argument('--baseline',required=True,type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    main_path=a.build/'src/rsp_main.elf'
    images=link_images(main_path,a.build/'src/rsp_hcomp_tlut.elf',a.build/'src/rsp_hcomp.elf')
    assert symbols(main_path)['calc_window_spans']==0xce4
    names=['rsp_main','rsp_hcomp','rsp_hcomp_math','rsp_hcomp_rdp',
           'rsp_hcomp_fixed_window','rsp_hcomp_rdp_fixed','rsp_hcomp_setup','rsp_mode7','rsp_mode7_window']
    optional='rsp_object_cache'
    assert (a.build/'src'/f'{optional}.elf').exists()==(a.baseline/'src'/f'{optional}.elf').exists()
    if (a.build/'src'/f'{optional}.elf').exists(): names.append(optional)
    for name in names:
        assert read_text(a.build/'src'/f'{name}.elf')[1]==read_text(a.baseline/'src'/f'{name}.elf')[1], name
    edges_list=[(0,255,0,255),(255,0,255,0),(0,0,255,255),(255,255,0,0),
                (1,254,20,220),(24,224,48,216),(48,216,24,224),
                (200,20,30,60),(30,60,200,20),(0,128,127,255)]
    count=admitted=steps_max=0
    for sel in range(16):
        for logic in range(4):
            for edges in edges_list:
                for cgwsel in (0,0x10,0x20,0x30,0x50,0x81,0x12):
                    yes,steps=decision(images,cgwsel,sel,logic,edges)
                    count+=1;admitted+=yes;steps_max=max(steps_max,steps)
    setup_pixels=0
    for sel in (0,2,3,10,11,15):
        for logic in range(4):
            for edges in edges_list:
                for cgwsel in (0,0x10,0x20,0x30):
                    setup_pixels+=setup_mask(images,a.baseline/'src/rsp_hcomp_setup.elf',cgwsel,sel,logic,edges)
    palette=[0]+[((i*977)&0x7fff)<<1|1 for i in range(1,256)]
    cases=[]
    for sel,logic,edges,cgwsel in ((3,0,(0,255,0,255),0x20),
                                 (2,0,(0,255,0,255),0x10),
                                 (2,0,(255,0,0,255),0x20),
                                 (0,3,(24,224,48,216),0x20)):
        for slot in (0,4):
            for mode in (0x33,0xf3):
                policy=dict(ROOM,cgwsel=cgwsel,cgadsub=mode,main=0x4cd2)
                cases.append(generation(images,palette,policy,slot,7,lease_table=2,
                                        windows=(sel,logic,edges)))
    rejects=[]
    for sel,logic,edges,cgwsel in ((2,0,(24,224,48,216),0x10),
                                 (2,0,(24,224,48,216),0x20),
                                 (15,0,(24,224,48,216),0x10),
                                 (0,0,(0,255,0,255),0x10)):
        rejects.append(generation(images,palette,dict(ROOM,cgwsel=cgwsel,main=0x4cd2),0,7,
                                  admitted=False,windows=(sel,logic,edges)))
    windows=(11,0,(255,0,255,0))
    bindings=[class_bindings(images,main_path,palette,dict(ROOM,cgwsel=0x10,main=0x4cd2),slot,windows)
              for slot in (0,4)]
    try: decision(images,0x10,2,0,(1,255,0,0),fault='hole')
    except AssertionError as error: assert 'COLOR hole admitted' in str(error)
    else: raise AssertionError('accepted a shader on a one-pixel COLOR hole')
    result=dict(passed=True,policies=count,uniform_admitted=admitted,
                truth_pixels=count*256,generation_cases=len(cases),reject_cases=len(rejects),
                binding_cases=bindings,negative_guards=1,untouched_banks=len(names),
                max_admission_instructions=steps_max,native_fps_claim=False)
    result['original_setup_mask_pixels']=setup_pixels
    if a.output:a.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

if __name__=='__main__':main()
