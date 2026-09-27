#!/usr/bin/env python3
"""Static/binary contract for the clean-lineage executable third-overlay proof."""
from pathlib import Path
import argparse,re

ROOT=Path(__file__).resolve().parents[1]

def insns(text):
    out=[]
    for raw in text.splitlines():
        line=raw.split("//",1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"): continue
        out.append(line)
    return out

def section(src,start,end):
    i=src.index(start); j=src.index(end,i); return src[i:j]

def lit(src,name):
    m=re.search(rf"^#define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\s*$",src,re.M)
    if not m: raise AssertionError(f"missing {name}")
    return int(m.group(1),16)

def syms(path):
    out={}
    for line in path.read_text().splitlines():
        p=line.split()
        if len(p)>=8 and p[0].rstrip(":").isdigit():
            try: out[p[-1]]=int(p[1],16)
            except ValueError: pass
    return out

def text_size(path):
    s=path.read_text()
    m=re.search(r"^\s*\.text\s+0xa4001000\s+0x([0-9A-Fa-f]+)\b",s,re.M)
    if not m: raise AssertionError(f"{path}: .text missing")
    return int(m.group(1),16)

def source_contract():
    d=(ROOT/"src/defines.h").read_text()
    expect={"OVERLAY_MODE7_SRC":0xE8C,"OVERLAY_MAIN_SRC":0xE90,
            "OVERLAY_HCOMP_SRC":0xE94,"HCOMP_RAW_PALETTE_PTRS":0xE98,
            "HCOMP_CGRAM_EVENT_CURSOR":0xEA0,"HCOMP_CGRAM_PAIR_SCRATCH":0xEA8,
            "HCOMP_CGRAM_WRITE_SCRATCH":0xEB0,"HCOMP_OVERLAY_PROOF_MODE7":0xF10,
            "HCOMP_OVERLAY_PROOF_HCOMP":0xF11,"VEC_DATA":0xF70}
    for k,v in expect.items():
        if lit(d,k)!=v: raise AssertionError(f"{k} drift")
    if not (0xE8C+4==0xE90 and 0xE90+4==0xE94 and 0xE94+4==0xE98 and 0xE98+8==0xEA0):
        raise AssertionError("DMEM pointer packing broken")

    main=(ROOT/"src/main.S").read_text()
    for a in ("rsp_mode7_text_start","DMEM(OVERLAY_MODE7_SRC)",
              "rsp_main_text_start","DMEM(OVERLAY_MAIN_SRC)",
              "rsp_hcomp_text_start","DMEM(OVERLAY_HCOMP_SRC)",
              "DMEM(HCOMP_OVERLAY_PROOF_MODE7)","DMEM(HCOMP_OVERLAY_PROOF_HCOMP)"):
        if a not in main: raise AssertionError(f"CPU publication missing {a}")

    for name in ("rsp_main.S","rsp_mode7.S"):
        src=(ROOT/"src"/name).read_text()
        order=["overlay_mode7_src: .word 0","overlay_main_src: .word 0",
               "overlay_hcomp_src: .word 0","hcomp_raw_palette_ptrs: .word 0, 0"]
        pos=[src.index(x) for x in order]
        if pos!=sorted(pos): raise AssertionError(f"{name}: DMEM pointer order drift")
        nf=insns(section(src,"next_frame:","\n\nclear_cache:"))
        if nf!=["lw a1, OVERLAY_HCOMP_SRC","li t9, 0x13B0","b overlay_load_slot","xori sp, sp, 4"]:
            raise AssertionError(f"{name}: next_frame drift {nf}")
        ld=insns(section(src,"overlay_load_mode7:","\noverlay_load_main:"))
        if ld!=["lw a1, OVERLAY_MODE7_SRC","li a0, 0x13A8","jal dma_read","li a2, 0x3E7","jr t9","nop"]:
            raise AssertionError(f"{name}: loader drift {ld}")
        # PR #18 replay must remain in resident suffix.
        for a in ("hcomp_cgram_pair_ready:","HCOMP_CGRAM_EVENT_CURSOR",
                  "HCOMP_CGRAM_WRITE_SCRATCH","HCOMP_RAW_PALETTE_PTRS(sp)"):
            if a not in src: raise AssertionError(f"{name}: PR18 replay anchor lost {a}")

    reg=(ROOT/"src/rsp_main.S").read_text()
    if insns(section(reg,"draw_mode7_entry:","\n\ndraw_obj:"))!=["b overlay_load_mode7","li t9, 0x1788"]:
        raise AssertionError("regular Mode7 fault stub drift")
    m7=(ROOT/"src/rsp_mode7.S").read_text()
    if insns(section(m7,"draw_mode7_entry:","\n\ndraw_obj:"))!=["b draw_mode7_impl","sb zero, HCOMP_OVERLAY_PROOF_MODE7"]:
        raise AssertionError("true Mode7 marker drift")

    h=(ROOT/"src/rsp_hcomp.S").read_text()
    for a in (".byte 0:0x3A8","draw_bg:","j 0xA4001F90","hcomp_entry:",
              "sb t0, HCOMP_OVERLAY_PROOF_HCOMP","mtc0 t0, COP0_SP_STATUS",
              "j 0xA400103C",".byte 0:0x3C0","draw_mode7_entry:",
              "j 0xA4001F78","li t9, 0x1788"):
        if a not in h: raise AssertionError(f"HCOMP payload missing {a}")

def binary_contract(maps,symbols):
    if len(maps)!=3 or len(symbols)!=3: raise AssertionError("need three maps/symbol tables")
    rm,r7m,hm=maps
    rs,r7s,hs=[syms(p) for p in symbols]
    if text_size(rm)!=0x1000 or text_size(r7m)!=0x1000:
        raise AssertionError("resident renderer IMEM grew")
    if text_size(hm)!=0x790:
        raise AssertionError(f"HCOMP proof payload size {text_size(hm):#x} != 0x790")
    fixed={"draw_frame":0xA400103C,"dma_read":0xA4001F40,
           "overlay_load_mode7":0xA4001F78,"overlay_load_slot":0xA4001F7C,
           "overlay_load_main":0xA4001F90,"draw_bg":0xA40013A8,
           "draw_mode7_entry":0xA4001788,"draw_obj":0xA4001790}
    for label,s in (("regular",rs),("mode7",r7s)):
        for k,v in fixed.items():
            if s.get(k)!=v: raise AssertionError(f"{label}: {k}={s.get(k)} expected {v:#x}")
    if rs.get("next_frame")!=r7s.get("next_frame"):
        raise AssertionError("renderer next_frame addresses diverged")
    if hs.get("draw_bg")!=0xA40013A8 or hs.get("hcomp_entry")!=0xA40013B0 or hs.get("draw_mode7_entry")!=0xA4001788:
        raise AssertionError("HCOMP fixed-slot entry drift")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--maps",nargs=3,type=Path)
    ap.add_argument("--symbols",nargs=3,type=Path)
    a=ap.parse_args()
    source_contract()
    if a.maps or a.symbols:
        if not a.maps or not a.symbols: ap.error("maps+symbols together")
        binary_contract(a.maps,a.symbols)
    print("HCOMP_THIRD_OVERLAY_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("runtime_scope=coexistence_only")
    print("hcomp_arithmetic=DISABLED")
    print("pr18_replay=REQUIRED_INTACT")
    return 0
if __name__=="__main__": raise SystemExit(main())
