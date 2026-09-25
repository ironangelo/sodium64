#!/usr/bin/env python3
"""Static contract for proof-only triple-overlay RSP->RDRAM marker publication."""

from __future__ import annotations
import argparse,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAILBOX=0xA00F0000
MAILBOX_SIZE=8
RAW_Q2=0xA00EF800
RAW_Q_SIZE=0x800
LOWEST_COLOR_IMAGE=0xA00F1180

def source_contract()->None:
    s=(ROOT/"src/rsp_hcomp.S").read_text()
    anchors=(
      "li t0, 0x51",
      "sb t0, HCOMP_OVERLAY_PROOF_HCOMP",
      "li a0, HCOMP_OVERLAY_PROOF_MODE7",
      "li a1, 0xA00F0000",
      "jal 0xA4001F08",
      "li a2, 0x7",
      "mtc0 t0, COP0_SP_STATUS",
      ".byte 0:0x3AC",
    )
    for a in anchors:
        if a not in s: raise AssertionError(f"missing RDRAM proof anchor {a!r}")
    if not (RAW_Q2+RAW_Q_SIZE==MAILBOX):
        raise AssertionError("mailbox no longer begins immediately after raw Q2")
    if MAILBOX+MAILBOX_SIZE>LOWEST_COLOR_IMAGE:
        raise AssertionError("mailbox overlaps validated lowest color-image bound")

def parse_symbols(path:Path)->dict[str,int]:
    out={}
    for line in path.read_text().splitlines():
        p=line.split()
        if len(p)>=8 and re.fullmatch(r"[0-9A-Fa-f]+",p[1]):
            out[p[-1]]=int(p[1],16)
    return out

def map_text_size(path:Path)->int:
    text=path.read_text()
    m=re.search(r"\.text\s+0xa4001000\s+(0x[0-9a-fA-F]+)",text)
    if not m:
        m=re.search(r"\.text\s+0x[0-9a-fA-F]+\s+(0x[0-9a-fA-F]+)",text)
    if not m: raise AssertionError(f"cannot parse .text size from {path}")
    return int(m.group(1),16)

def binary_contract(maps:list[Path],symbols:list[Path])->None:
    sm,sv,sh=(parse_symbols(p) for p in symbols)
    mm,mv,mh=maps
    if map_text_size(mm)!=0x1000 or map_text_size(mv)!=0x1000:
        raise AssertionError("renderer resident text no longer exactly 0x1000")
    if map_text_size(mh)!=0x790:
        raise AssertionError("H-COMP payload no longer exactly 0x790")
    expected_h={"draw_bg":0xA40013A8,"hcomp_entry":0xA40013B0,"draw_mode7_entry":0xA4001788}
    for k,v in expected_h.items():
        if sh.get(k)!=v: raise AssertionError(f"H-COMP {k} drift: {sh.get(k)} != {v:#x}")
    for name,sym in (("main",sm),("mode7",sv)):
        if sym.get("dma_write")!=0xA4001F08:
            raise AssertionError(f"{name} dma_write drift: {sym.get('dma_write')}")
        if sym.get("draw_frame")!=0xA400103C:
            raise AssertionError(f"{name} draw_frame drift")
    if sm.get("dma_write")!=sv.get("dma_write"):
        raise AssertionError("regular/Mode7 common dma_write address diverged")

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--maps",nargs=3,type=Path)
    ap.add_argument("--symbols",nargs=3,type=Path)
    args=ap.parse_args()
    source_contract()
    if bool(args.maps)!=bool(args.symbols): ap.error("--maps and --symbols must be paired")
    if args.maps: binary_contract(args.maps,args.symbols)
    print("HCOMP_THIRD_OVERLAY_RDRAM_PROOF_CONTRACT_VALIDATED")
    print("mailbox=A00F0000")
    print("mailbox_bytes=8")
    print("resident_imem_growth=0")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
