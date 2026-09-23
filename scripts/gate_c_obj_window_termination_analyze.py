#!/usr/bin/env python3
"""Analyze Sodium64 framebuffer for the normal-W1 OBJ termination proof."""
from __future__ import annotations
import argparse, json
from pathlib import Path

WIDTH=280
HEIGHT=240
EXPECTED_BYTES=WIDTH*HEIGHT*2
Y0,Y1=95,105
ROIS={
    "left": (27,37),
    "middle": (131,149),
    "right": (235,245),
}

def red_count(blob: bytes, x0:int,x1:int)->int:
    if len(blob)!=EXPECTED_BYTES:
        raise ValueError(f"expected {EXPECTED_BYTES} bytes, got {len(blob)}")
    n=0
    for y in range(Y0,Y1):
        for x in range(x0,x1):
            i=(y*WIDTH+x)*2
            v=(blob[i]<<8)|blob[i+1]
            r=(v>>11)&31; g=(v>>6)&31; b=(v>>1)&31
            if r>=24 and g<=7 and b<=7:
                n+=1
    return n

def analyze(path:Path):
    b=path.read_bytes()
    return {name:red_count(b,*roi) for name,roi in ROIS.items()}

def present(n:int)->bool:
    return n>=8

def classify(c,t):
    cp={k:present(v) for k,v in c.items()}
    tp={k:present(v) for k,v in t.items()}
    if cp != {"left":True,"middle":True,"right":True}:
        return f"INDETERMINATE_CONTROL_{cp}"
    if tp["left"] and (not tp["middle"]) and tp["right"]:
        return "HOBJ_NORMAL_W1_BOUNDED_PASS"
    if tp["left"] and tp["middle"] and tp["right"]:
        return "HOBJ_NORMAL_W1_LEAK_REPRODUCED"
    return f"HOBJ_NORMAL_W1_OTHER_{tp}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path); ap.add_argument("treatment",type=Path)
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    c=analyze(a.control); t=analyze(a.treatment)
    out={"control":c,"treatment":t,"classification":classify(c,t)}
    txt=json.dumps(out,indent=2,sort_keys=True)
    print(txt)
    if a.output:
        a.output.write_text(txt+"\n")
if __name__=="__main__": main()
