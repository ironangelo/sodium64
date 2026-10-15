#!/usr/bin/env python3
"""Execute compiled Mode7 span setup/continuation against independent pixel truth.

Checks both screen masks, all selectors/logics, inclusive endpoints, preserved
affine state and restored scissor. Original register data only, no timing claim.
"""
import argparse,importlib.util,json,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('direct_vm',ROOT/'docs/gate-c-a3/test_hcomp_direct_backdrop.py')
vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('main',type=Path);ap.add_argument('window',type=Path)
    ap.add_argument('--output',type=Path);args=ap.parse_args()
    _,resident=read_text(args.main);base,window=read_text(args.window)
    assert len(resident)==4096 and len(window)==1000 and base&4095==0x3a8
    code=bytearray(resident);code[0x3a8:0x790]=window
    data=vm.section(args.main,'.data');cases=0;spans=0
    bounds_cases=((0,255,0,255),(32,95,64,191),(255,255,0,0),
                  (200,100,250,2),(0,0,255,255),(80,80,80,80),(2,254,3,253))
    for selector in range(16):
     for logic in range(4):
      for bounds in bounds_cases:
       for screen in (0,1):
        for masks in range(4):
         d=bytearray(data);d[0xec8]=screen
         d[0xbbb]=masks&1;d[0xbbc]=(masks>>1)&1
         struct.pack_into('>H',d,0xba4,selector)
         d[0xbb5]=logic;d[0xbae:0xbb2]=bytes(bounds)
         # Resolve RDP_FILL from actual data command offsets, frozen by ABI.
         fill=next(a for a in range(0,4096,8) if vm.word(d,a)==0x33000000)
         vm.put(d,fill+8,0x2d000000|(12<<14)|(21<<2))
         vm.put(d,fill+12,(268<<14)|(232<<2))
         vm.put(d,0xea4,0x80110000)
         before=d[0xb80:0xbc0];protected=d[0x840:0xa60]
         r=[0x13500000+i for i in range(32)];r[0]=0;r[9]=1
         frozen={i:r[i] for i in (*range(16,24),26,27,28,29)}
         active=bool((masks>>screen)&1)
         wanted={x for x in range(256) if not active or not vm.selected(x,selector,logic,bounds)}
         seen=set();pc=0x788
         while True:
          # Visible spans exit to the loader; final/empty restores and exits to
          # resident next_layer. Stop at either without running unrelated work.
          stop=0xf7c if pc==0x788 and wanted or pc==0x780 and d[0xe8b]+2<2*d[0xe8a] else 0x370
          commands=vm.run(code,d,pc,r,stop=stop)
          scissors=[v for v in commands if v>>56==0x2d]
          assert len(scissors)==1
          command=scissors[0];x0=(command>>44)&4095;y0=(command>>32)&4095
          x1=(command>>12)&4095;y1=command&4095
          assert y0==21*4 and y1==232*4
          assert d[0xb80:0xbc0]==before and d[0x840:0xa60]==protected
          assert all(r[i]==v for i,v in frozen.items())
          if stop==0x370:
           assert (x0,x1)==(12*4,268*4),'Mode7 leaves a narrow scissor for OBJ'
           break
          assert r[25]==0x1788 and r[5]==0x80110000 and r[9]==1
          points=set(range(x0//4-12,x1//4-12))
          assert points and not points&seen and points<=wanted
          seen|=points;spans+=1;pc=0x780
         assert seen==wanted,(selector,logic,bounds,screen,masks,seen^wanted)
         cases+=1
    result=dict(passed=True,cases=cases,spans=spans,compiled_execution=True,
                both_screens=True,all_selectors_logics=True,native_fps_authority=False)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('MODE7_WINDOWS PASS '+json.dumps(result))

if __name__=='__main__':main()
