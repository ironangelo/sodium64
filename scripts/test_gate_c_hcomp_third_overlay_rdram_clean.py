#!/usr/bin/env python3
"""Static/binary contract for clean triple-overlay RSP->RDRAM proof."""
from pathlib import Path
import argparse,re
ROOT=Path(__file__).resolve().parents[1]
MAILBOX=0xA00F0000; RAW_Q2=0xA00EF800; RAW_Q_SIZE=0x800; LOWEST_COLOR_IMAGE=0xA00F1180
def syms(p):
    o={}
    for line in p.read_text().splitlines():
        x=line.split()
        if len(x)>=8 and re.fullmatch(r"[0-9A-Fa-f]+",x[1]): o[x[-1]]=int(x[1],16)
    return o
def size(p):
    m=re.search(r"\.text\s+0xa4001000\s+(0x[0-9a-fA-F]+)",p.read_text())
    if not m: raise AssertionError("text size parse")
    return int(m.group(1),16)
def source():
    h=(ROOT/"src/rsp_hcomp.S").read_text()
    for a in ("li t0, 0x51","sb t0, HCOMP_OVERLAY_PROOF_HCOMP",
              "li a0, HCOMP_OVERLAY_PROOF_MODE7","li a1, 0xA00F0000",
              "jal 0xA4001F08","li a2, 0x7","mtc0 t0, COP0_SP_STATUS",".byte 0:0x3B0"):
        if a not in h: raise AssertionError(f"missing {a}")
    m=(ROOT/"src/main.S").read_text()
    seed=("li t0, 0xA00F0000","li t1, 0xDEADBEEF","sw t1, 0(t0)","li t1, 0xCAFEBABE","sw t1, 4(t0)")
    pos=[m.index(x) for x in seed]
    if pos!=sorted(pos): raise AssertionError("seed order")
    if not (m.index("DMEM(HCOMP_RAW_PALETTE_PTRS + 4)") < pos[0] < m.index("sw zero, 0xA4080000 // SP_PC")): raise AssertionError("seed phase")
    if RAW_Q2+RAW_Q_SIZE!=MAILBOX or MAILBOX+8>LOWEST_COLOR_IMAGE: raise AssertionError("mailbox geometry")
def binary(maps,symbols):
    sm,sv,sh=[syms(p) for p in symbols]
    if size(maps[0])!=0x1000 or size(maps[1])!=0x1000 or size(maps[2])!=0x790: raise AssertionError("text size")
    for n,s in (("main",sm),("mode7",sv)):
        if s.get("dma_write")!=0xA4001F08: raise AssertionError(f"{n} dma_write")
        if s.get("draw_frame")!=0xA400103C: raise AssertionError(f"{n} draw_frame")
    if sh.get("hcomp_entry")!=0xA40013B0 or sh.get("draw_mode7_entry")!=0xA4001788: raise AssertionError("HCOMP entry")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--maps",nargs=3,type=Path); ap.add_argument("--symbols",nargs=3,type=Path); a=ap.parse_args()
    source()
    if bool(a.maps)!=bool(a.symbols): ap.error("pair maps/symbols")
    if a.maps: binary(a.maps,a.symbols)
    print("HCOMP_THIRD_OVERLAY_RDRAM_CLEAN_CONTRACT_VALIDATED")
if __name__=="__main__": main()
