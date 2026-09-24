#!/usr/bin/env python3
"""Analyze Sodium64 framebuffer for the inverted-W1 x=255 OBJ proof."""
from __future__ import annotations
import argparse, json
from pathlib import Path

WIDTH=280
HEIGHT=240
EXPECTED_BYTES=WIDTH*HEIGHT*2
Y0,Y1=95,105
ROIS={
    "left": (26,38),
    "edge": (258,270),
}

def is_red(v:int)->bool:
    r=(v>>11)&31; g=(v>>6)&31; b=(v>>1)&31
    return r>=24 and g<=7 and b<=7

def analyze(path:Path):
    blob=path.read_bytes()
    if len(blob)!=EXPECTED_BYTES:
        raise ValueError(f"expected {EXPECTED_BYTES} bytes, got {len(blob)}")
    out={}
    for name,(x0,x1) in ROIS.items():
        count=0; cols=set()
        for y in range(Y0,Y1):
            for x in range(x0,x1):
                i=(y*WIDTH+x)*2
                v=(blob[i]<<8)|blob[i+1]
                if is_red(v):
                    count+=1; cols.add(x)
        out[name]={"red_pixels":count,"red_columns":sorted(cols),"column_count":len(cols)}
    return out

def classify(c,t):
    c_left=c["left"]; c_edge=c["edge"]; t_left=t["left"]; t_edge=t["edge"]
    if not (c_left["red_pixels"]>=48 and c_edge["red_pixels"]>=48 and c_edge["column_count"]>=7):
        return "INDETERMINATE_CONTROL"
    if t_left["red_pixels"]==0 and 4<=t_edge["red_pixels"]<=16 and t_edge["column_count"]==1:
        return "HOBJ_X255_SINGLETON_PASS"
    if t_left["red_pixels"]==0 and t_edge["red_pixels"]==0:
        return "HOBJ_X255_SINGLETON_DROPPED"
    return "HOBJ_X255_OTHER"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path); ap.add_argument("treatment",type=Path)
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    c=analyze(a.control); t=analyze(a.treatment)
    out={"control":c,"treatment":t,"classification":classify(c,t)}
    txt=json.dumps(out,indent=2,sort_keys=True)
    print(txt)
    if a.output: a.output.write_text(txt+"\n")
if __name__=="__main__": main()
