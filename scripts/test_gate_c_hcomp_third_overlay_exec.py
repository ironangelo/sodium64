#!/usr/bin/env python3
"""Validate the proof-only zero-growth three-overlay implementation."""

from __future__ import annotations
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

EXPECTED={
 "draw_frame":0xA400103C,
 "next_frame":0xA4001A88,
 "dma_read":0xA4001F40,
 "overlay_load_mode7":0xA4001F78,
 "overlay_load_slot":0xA4001F7C,
 "overlay_load_main":0xA4001F90,
 "draw_bg":0xA40013A8,
 "draw_mode7_entry":0xA4001788,
 "draw_obj":0xA4001790,
}

def insns(text:str)->list[str]:
    out=[]
    for raw in text.splitlines():
        line=raw.split("//",1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"):
            continue
        out.append(line)
    return out

def section(src:str,start:str,end:str)->str:
    i=src.index(start); j=src.index(end,i)
    return src[i:j]

def lit_define(src:str,name:str)->int:
    m=re.search(rf"^#define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\s*$",src,re.M)
    if not m: raise AssertionError(f"missing {name}")
    return int(m.group(1),16)

def text_size(path:Path)->int:
    s=path.read_text()
    m=re.search(r"^\s*\.text\s+0xa4001000\s+0x([0-9a-fA-F]+)\b",s,re.M)
    if not m: raise AssertionError(f"{path}: no text size")
    return int(m.group(1),16)

def symbols(path:Path)->dict[str,int]:
    out={}
    for line in path.read_text().splitlines():
        p=line.split()
        if len(p)>=8 and p[0].rstrip(":").isdigit():
            try: out[p[-1]]=int(p[1],16)
            except ValueError: pass
    return out

def source_contract()->None:
    defs=(ROOT/"src/defines.h").read_text()
    assert lit_define(defs,"OVERLAY_MODE7_SRC")==0xE8C
    assert lit_define(defs,"OVERLAY_MAIN_SRC")==0xE90
    assert lit_define(defs,"OVERLAY_HCOMP_SRC")==0xE94
    assert lit_define(defs,"HCOMP_RAW_PALETTE_PTRS")==0xE98
    assert lit_define(defs,"HCOMP_OVERLAY_PROOF_MODE7")==0xF10
    assert lit_define(defs,"HCOMP_OVERLAY_PROOF_HCOMP")==0xF11
    assert lit_define(defs,"VEC_DATA")==0xF70

    main=(ROOT/"src/main.S").read_text()
    for a in (
      "rsp_mode7_text_start","DMEM(OVERLAY_MODE7_SRC)",
      "rsp_main_text_start","DMEM(OVERLAY_MAIN_SRC)",
      "rsp_hcomp_text_start","DMEM(OVERLAY_HCOMP_SRC)",
      "DMEM(HCOMP_OVERLAY_PROOF_MODE7)","DMEM(HCOMP_OVERLAY_PROOF_HCOMP)",
    ):
      if a not in main: raise AssertionError(f"CPU publication missing {a}")

    for name in ("rsp_main.S","rsp_mode7.S"):
      src=(ROOT/"src"/name).read_text()
      ordered=[
        "overlay_mode7_src: .word 0",
        "overlay_main_src: .word 0",
        "overlay_hcomp_src: .word 0",
        "hcomp_raw_palette_ptrs: .word 0, 0",
      ]
      pos=[src.index(a) for a in ordered]
      if pos!=sorted(pos): raise AssertionError(f"{name}: pointer order drift")

      nf=insns(section(src,"next_frame:","\n\nclear_cache:"))
      if nf != [
        "lw a1, OVERLAY_HCOMP_SRC",
        "li t9, 0x13B0",
        "b overlay_load_slot",
        "xori sp, sp, 4",
      ]: raise AssertionError(f"{name}: next_frame drift {nf}")

      loader=insns(section(src,"overlay_load_mode7:","\noverlay_load_main:"))
      if loader != [
        "lw a1, OVERLAY_MODE7_SRC",
        "li a0, 0x13A8",
        "jal dma_read",
        "li a2, 0x3E7",
        "jr t9",
        "nop",
      ]: raise AssertionError(f"{name}: indirect loader drift {loader}")

    reg=(ROOT/"src/rsp_main.S").read_text()
    stub=insns(section(reg,"draw_mode7_entry:","\n\ndraw_obj:"))
    if stub != ["b overlay_load_mode7","li t9, 0x1788"]:
        raise AssertionError(f"regular Mode7 fault drift {stub}")

    m7=(ROOT/"src/rsp_mode7.S").read_text()
    entry=insns(section(m7,"draw_mode7_entry:","\n\ndraw_obj:"))
    if entry != ["b draw_mode7_impl","sb zero, HCOMP_OVERLAY_PROOF_MODE7"]:
        raise AssertionError(f"Mode7 entry marker drift {entry}")

    h=(ROOT/"src/rsp_hcomp.S").read_text()
    for a in (
      ".byte 0:0x3A8",
      "draw_bg:",
      "j 0xA4001F90",
      "hcomp_entry:",
      "sb t0, HCOMP_OVERLAY_PROOF_HCOMP",
      "mtc0 t0, COP0_SP_STATUS",
      "j 0xA400103C",
      "draw_mode7_entry:",
      "j 0xA4001F78",
      "li t9, 0x1788",
    ):
      if a not in h: raise AssertionError(f"H-COMP proof payload missing {a}")

def binary_contract(maps:list[Path],symfiles:list[Path])->None:
    if len(maps)!=3 or len(symfiles)!=3: raise AssertionError("need main/mode7/hcomp maps+symbols")
    reg,m7,hmap=maps
    rs,m7s,hs=map(symbols,symfiles)

    if text_size(reg)!=0x1000 or text_size(m7)!=0x1000:
      raise AssertionError("renderer resident text no longer 0x1000")
    if text_size(hmap)!=0x790:
      raise AssertionError(f"H-COMP payload text size {text_size(hmap):#x} != 0x790")

    for label,syms in (("regular",rs),("mode7",m7s)):
      for k,v in EXPECTED.items():
        if k=="overlay_load_slot":
          if syms.get(k)!=v: raise AssertionError(f"{label} {k}={syms.get(k)} != {v:#x}")
        elif syms.get(k)!=v:
          raise AssertionError(f"{label} {k}={syms.get(k)} != {v:#x}")

    if hs.get("draw_bg")!=0xA40013A8: raise AssertionError("HCOMP draw_bg moved")
    if hs.get("hcomp_entry")!=0xA40013B0: raise AssertionError("HCOMP entry moved")
    if hs.get("draw_mode7_entry")!=0xA4001788: raise AssertionError("HCOMP Mode7 entry moved")

def main()->int:
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--maps",nargs=3,type=Path)
    ap.add_argument("--symbols",nargs=3,type=Path)
    args=ap.parse_args()
    source_contract()
    if args.maps or args.symbols:
      if not args.maps or not args.symbols: ap.error("maps+symbols together")
      binary_contract(args.maps,args.symbols)
    print("HCOMP_THIRD_OVERLAY_EXEC_CONTRACT_VALIDATED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
