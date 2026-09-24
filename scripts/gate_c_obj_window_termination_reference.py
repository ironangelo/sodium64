#!/usr/bin/env python3
"""Analyze direct-SNES screenshots for normal-W1 OBJ semantics."""
from __future__ import annotations
import argparse, json
from collections import deque
from pathlib import Path
from PIL import Image

def comps(mask,w,h,min_area):
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
                    if mask[j] and not seen[j]: seen[j]=1; q.append(j)
        if area>=min_area:
            out.append({"area":area,"x0":x0,"x1":x1,"y0":y0,"y1":y1,
                        "cx":(x0+x1)/2,"cy":(y0+y1)/2})
    return out

def analyze(path):
    im=Image.open(path).convert("RGB"); w,h=im.size; pix=list(im.getdata())
    blue=[b>=130 and r<=120 and g<=120 and b>r*1.4 and b>g*1.4 for r,g,b in pix]
    red=[r>=140 and g<=120 and b<=120 and r>g*1.5 and r>b*1.5 for r,g,b in pix]
    bc=comps(blue,w,h,500)
    if not bc: return {"path":str(path),"status":"NO_BLUE_VIEWPORT"}
    vp=max(bc,key=lambda c:c["area"])
    rc=comps(red,w,h,4)
    inside=[c for c in rc if vp["x0"]-5<=c["cx"]<=vp["x1"]+5 and vp["y0"]-5<=c["cy"]<=vp["y1"]+5]
    return {"path":str(path),"status":"OK","viewport":vp,"red_components":inside,
            "red_component_count":len(inside)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("frames",nargs="+",type=Path); ap.add_argument("--output",type=Path)
    a=ap.parse_args(); frames=[analyze(p) for p in sorted(a.frames)]
    counts=[f["red_component_count"] for f in frames if f.get("status")=="OK"]
    # Adjacent center sprites merge into one component: control=3 groups, treatment=2.
    cls="REFERENCE_NORMAL_W1_CONFIRMED" if 3 in counts and 2 in counts else "REFERENCE_INDETERMINATE"
    out={"classification":cls,"counts":counts,"frames":frames}
    txt=json.dumps(out,indent=2,sort_keys=True); print(txt)
    if a.output: a.output.write_text(txt+"\n")
if __name__=="__main__": main()
