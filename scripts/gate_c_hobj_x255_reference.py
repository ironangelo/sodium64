#!/usr/bin/env python3
"""Analyze direct-SNES screenshots for inverted-W1 [255,255] OBJ semantics."""
from __future__ import annotations
import argparse, json
from collections import deque
from pathlib import Path
from PIL import Image

def comps(mask,w,h,min_area=1):
    seen=bytearray(len(mask)); out=[]
    for s,on in enumerate(mask):
        if not on or seen[s]: continue
        q=deque([s]); seen[s]=1; area=0; x0=w; x1=-1; y0=h; y1=-1
        while q:
            i=q.popleft(); y,x=divmod(i,w); area+=1
            x0=min(x0,x); x1=max(x1,x); y0=min(y0,y); y1=max(y1,y)
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=nx<w and 0<=ny<h:
                    j=ny*w+nx
                    if mask[j] and not seen[j]:
                        seen[j]=1; q.append(j)
        if area>=min_area:
            out.append({"area":area,"x0":x0,"x1":x1,"y0":y0,"y1":y1,
                        "width":x1-x0+1,"height":y1-y0+1})
    return out

def analyze(path):
    im=Image.open(path).convert("RGB"); w,h=im.size; pix=list(im.getdata())
    blue=[b>=120 and r<=130 and g<=130 and b>r*1.25 and b>g*1.25 for r,g,b in pix]
    red=[r>=130 and g<=130 and b<=130 and r>g*1.35 and r>b*1.35 for r,g,b in pix]
    bc=comps(blue,w,h,400)
    if not bc: return {"path":str(path),"status":"NO_BLUE_VIEWPORT","red_pixels":0}
    vp=max(bc,key=lambda c:c["area"])
    total=0
    for i,on in enumerate(red):
        if not on: continue
        y,x=divmod(i,w)
        if vp["x0"]-8<=x<=vp["x1"]+8 and vp["y0"]-8<=y<=vp["y1"]+8:
            total+=1
    rc=[c for c in comps(red,w,h,1)
        if vp["x0"]-8<=((c["x0"]+c["x1"])/2)<=vp["x1"]+8
        and vp["y0"]-8<=((c["y0"]+c["y1"])/2)<=vp["y1"]+8]
    return {"path":str(path),"status":"OK","viewport":vp,"red_pixels":total,"red_components":rc}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("frames",nargs="+",type=Path); ap.add_argument("--output",type=Path)
    a=ap.parse_args(); frames=[analyze(p) for p in sorted(a.frames)]
    positives=[f["red_pixels"] for f in frames if f.get("status")=="OK" and f["red_pixels"]>0]
    cls="REFERENCE_INDETERMINATE"
    if positives:
        hi=max(positives); lo=min(positives)
        # Control has two full sprites; treatment has one surviving 1px column.
        if hi>=8*lo and lo>0:
            cls="REFERENCE_X255_SINGLETON_CONFIRMED"
    out={"classification":cls,"positive_red_counts":positives,"frames":frames}
    txt=json.dumps(out,indent=2,sort_keys=True); print(txt)
    if a.output: a.output.write_text(txt+"\n")
if __name__=="__main__": main()
