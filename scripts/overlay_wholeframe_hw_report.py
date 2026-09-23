#!/usr/bin/env python3
"""Decode Sodium64 PR#13 whole-frame overlay hardware capture (OVM2)."""

from __future__ import annotations
import argparse, json, struct
from dataclasses import asdict, dataclass
from pathlib import Path

MAGIC=0x5336344F
VERSION=1
TEST_ID=0x4F564D32
RECORD_SIZE=0x80
END=0x454E4421
MODE7_WORD=0x1000024E
REGULAR_WORD=0x91670E64

OF_PASS=0x1
OF_TREAT_GUEST=0x2
OF_TREAT_BG=0x4
OF_TREAT_SP=0x8
OF_TREAT_DMA=0x10
OF_TREAT_SLOT=0x20
OF_TREAT_FB=0x40
OF_RETURN_GUEST=0x80
OF_RETURN_BG=0x100
OF_RETURN_SP=0x200
OF_RETURN_DMA=0x400
OF_RETURN_SLOT=0x800
OF_RETURN_FB=0x1000
OF_REQUIRED=0x1FFE

@dataclass(frozen=True)
class Capture:
    capture_format:str; version:int; test_id:int; complete:int; flags:int; stage:int
    t_counter:int; t_guest_mode:int; t_bg_mode:int; t_sp_status:int
    t_dma_full:int; t_dma_busy:int; t_slot:int; t_framebuffer:int; t_dp_status:int
    r_counter:int; r_guest_mode:int; r_bg_mode:int; r_sp_status:int
    r_dma_full:int; r_dma_busy:int; r_slot:int; r_framebuffer:int; r_dp_status:int
    expected_mode7:int; expected_regular:int; checksum:int; record_size:int; end_marker:int
    @property
    def passed(self): return bool(self.flags & OF_PASS)

def normalize(blob:bytes):
    if len(blob)<RECORD_SIZE: raise ValueError(f"save is only {len(blob)} bytes")
    if struct.unpack_from(">I",blob,0)[0]==MAGIC: return blob,"canonical big-endian"
    if len(blob)%4==0 and struct.unpack_from("<I",blob,0)[0]==MAGIC:
        return b"".join(blob[i:i+4][::-1] for i in range(0,len(blob),4)),"32-bit word-swapped"
    raise ValueError("bad S64O magic")

def valid_fb(value:int)->bool:
    return value in (0xA00F2300,0xA0113000,0xA0133D00)

def parse(blob:bytes)->Capture:
    blob,fmt=normalize(blob)
    w=struct.unpack_from(">32I",blob,0)
    c=Capture(fmt,w[1],w[2],w[3],w[4],w[5],*w[6:29])
    if c.version!=VERSION or c.test_id!=TEST_ID: raise ValueError("wrong OVM2 version/test id")
    if c.complete!=1 or c.stage!=2: raise ValueError("incomplete OVM2 capture")
    if c.record_size!=RECORD_SIZE or c.end_marker!=END: raise ValueError("bad OVM2 size/end marker")
    if c.expected_mode7!=MODE7_WORD or c.expected_regular!=REGULAR_WORD:
        raise ValueError("unexpected build-exact slot signatures")
    checksum=0
    for i,word in enumerate(w):
        if i!=26: checksum ^= word
    if checksum!=c.checksum: raise ValueError(f"checksum mismatch stored=0x{c.checksum:08X} computed=0x{checksum:08X}")

    expected=0
    if c.t_counter>=70 and c.t_guest_mode==7: expected|=OF_TREAT_GUEST
    if c.t_bg_mode==7: expected|=OF_TREAT_BG
    if c.t_sp_status&1: expected|=OF_TREAT_SP
    if c.t_dma_full==0 and c.t_dma_busy==0: expected|=OF_TREAT_DMA
    if c.t_slot==MODE7_WORD: expected|=OF_TREAT_SLOT
    if valid_fb(c.t_framebuffer): expected|=OF_TREAT_FB
    if c.r_counter>=5 and c.r_guest_mode==1: expected|=OF_RETURN_GUEST
    if c.r_bg_mode==1: expected|=OF_RETURN_BG
    if c.r_sp_status&1: expected|=OF_RETURN_SP
    if c.r_dma_full==0 and c.r_dma_busy==0: expected|=OF_RETURN_DMA
    if c.r_slot==REGULAR_WORD: expected|=OF_RETURN_SLOT
    if valid_fb(c.r_framebuffer): expected|=OF_RETURN_FB
    if (c.flags&OF_REQUIRED)!=expected:
        raise ValueError(f"flags disagree: recorded=0x{c.flags&OF_REQUIRED:X} recomputed=0x{expected:X}")
    if c.passed != (expected==OF_REQUIRED): raise ValueError("PASS flag inconsistent with evidence")
    return c

def render(c:Capture)->str:
    return (
      "Sodium64 real-N64 PR#13 whole-frame overlay capture\n"
      f"  save format:       {c.capture_format}\n"
      f"  test/version:      OVM2 / {c.version}\n"
      f"  result:            {'PASS' if c.passed else 'FAIL'}\n"
      f"  treatment:         counter={c.t_counter} guest_mode={c.t_guest_mode} bg_mode={c.t_bg_mode}\n"
      f"  treatment SP:      status=0x{c.t_sp_status:08X} dma_full={c.t_dma_full} dma_busy={c.t_dma_busy}\n"
      f"  treatment slot:    0x{c.t_slot:08X} (expected Mode7 0x{MODE7_WORD:08X})\n"
      f"  treatment FB/DP:   0x{c.t_framebuffer:08X} / 0x{c.t_dp_status:08X}\n"
      f"  return:            counter={c.r_counter} guest_mode={c.r_guest_mode} bg_mode={c.r_bg_mode}\n"
      f"  return SP:         status=0x{c.r_sp_status:08X} dma_full={c.r_dma_full} dma_busy={c.r_dma_busy}\n"
      f"  return slot:       0x{c.r_slot:08X} (expected regular 0x{REGULAR_WORD:08X})\n"
      f"  return FB/DP:      0x{c.r_framebuffer:08X} / 0x{c.r_dp_status:08X}\n"
    )

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("save",type=Path); ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    c=parse(args.save.read_bytes())
    print(json.dumps(asdict(c)|{"passed":c.passed},indent=2) if args.json else render(c),end="" if not args.json else "\n")
    return 0 if c.passed else 2

if __name__=="__main__":
    try: raise SystemExit(main())
    except (OSError,ValueError,struct.error) as exc: raise SystemExit(f"error: {exc}")
