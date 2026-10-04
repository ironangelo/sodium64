#!/usr/bin/env python3
"""Compiled complete OBJ-row progression after drawing and culling.

Original geometries and tile indices only. The independent oracle enumerates
each object tile from its origin; a clipped row cannot change later tile X or
character selection. This includes both mirror directions and character wrap.
"""
import argparse, json, struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_hcomp_aligned_targets import execute, constants

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('main_rsp',type=Path);ap.add_argument('mode7_rsp',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args()
    cases=0;drawn=0;culled=0
    for path in (a.main_rsp,a.mode7_rsp):
        base,text=read_text(path);base&=0xfff
        s={n:addr&0xfff for addr,n in elf_symbols(path)}
        entry=s['next_objy'];returned=entry+8
        d=bytearray(4096);struct.pack_into('>I',d,constants()['FB_OFFSET'],8)
        for width in (8,16,32,64):
          for height in (8,16,32,64):
           for top in (-16,-4,0,3,17,111,217,239):
            for begin,end in ((0,1),(0,8),(3,5),(17,19),(110,113),(217,224),(0,224)):
             for xflip in (False,True):
              for yflip in (False,True):
               for character in (0,15,255,511):
                r=[0]*32;r[0]=0;r[16]=width;r[17]=height;r[20]=width
                r[2]=-width if xflip else width
                r[18]=96+width-8 if xflip else 96
                r[21]=character;r[28]=-8 if yflip else 8
                r[30]=top+height-8 if yflip else top
                r[26]=begin;r[27]=end
                x0=r[18];step=r[28]
                for row in range(height//8):
                    y=top+height-8+row*step if yflip else top+row*step
                    tile=(character+16*row)&511
                    assert (r[18]&0xffffffff,r[21]&511,r[30]&0xffffffff,r[17])==(x0,tile,y&0xffffffff,height-8*row),('row ownership before clip',path,width,height,top,begin,end,xflip,yflip,character,row,r[18],r[21])
                    r[8]=int(y<end);r[31]=returned
                    execute(text,base,d,s['hcomp_obj_row_clip'],{returned,entry,s['next_object']},r)
                    visible=y<end and y+8>begin
                    if visible:
                        assert r[14]==0x02000000 and r[15]==8
                        assert (r[18],r[21])==(x0,tile),('visible tile origin',path,row)
                        # Independent horizontal enumeration consumes all tiles.
                        # The compiled continuation must undo that displacement.
                        r[18]=(r[18]+(-width if xflip else width))&0xffffffff
                        r[21]=(r[21]+width//8)&511;r[16]=0
                        execute(text,base,d,s['hcomp_obj_row_done'],{entry,s['next_object']},r)
                        drawn+=1
                    else:culled+=1
                    assert (r[18],r[21],r[30],r[17])==(x0,(character+16*(row+1))&511,(y+step)&0xffffffff,height-8*(row+1)),('row ownership after clip',path,width,height,top,begin,end,xflip,yflip,character,row,visible,r[18],r[21])
                cases+=1
    result=dict(passed=True,objects=cases,drawn_rows=drawn,culled_rows=culled,commercial_data=False,native_timing=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('OBJ_ROW_PROGRESSION PASS',json.dumps(result))

if __name__=='__main__':main()
