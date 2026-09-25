#!/usr/bin/env python3
"""Classify first-hand execution of the proof-only third H-COMP overlay."""

from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path

def swap32(data:bytes)->bytes:
    if len(data)%4: raise ValueError("word swap requires multiple of 4")
    return b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))

def normalize_candidates(data:bytes):
    yield "identity",data
    if len(data)%4==0: yield "word_swap32",swap32(data)

def guest_ok(data:bytes)->tuple[bool,dict]:
    if len(data)<7: return False,{}
    return (
      data[1]==0x33 and data[2]==2 and data[3]==1 and data[4]==1
      and data[5]==data[0] and data[6]==data[0],
      {"token":data[0],"phase":data[1],"irq_count":data[2],"mode":data[3],
       "done":data[4],"irq1_token":data[5],"irq2_token":data[6]}
    )

def classify(root:Path)->dict:
    proof=(root/"proof-dmem.bin").read_bytes()
    slot=(root/"slot.bin").read_bytes()
    want=(root/"expected-hcomp-slot.bin").read_bytes()
    guest=(root/"guest-state.bin").read_bytes()

    proof_pass=None
    for mode,data in normalize_candidates(proof):
      if len(data)>=2 and data[0]==0x00 and data[1]==0x51:
        proof_pass=(mode,data[:16]); break
    if not proof_pass:
      return {"passed":False,"reason":"proof markers not 00/51"}

    slot_pass=None
    for mode,data in normalize_candidates(slot):
      if data[:len(want)]==want:
        slot_pass=mode; break
    if not slot_pass:
      return {"passed":False,"reason":"resident slot != linked H-COMP slot"}

    guest_pass=None
    guest_report={}
    for mode,data in normalize_candidates(guest):
      ok,rep=guest_ok(data)
      if ok:
        guest_pass=mode; guest_report=rep; break
    if not guest_pass:
      return {"passed":False,"reason":"guest did not complete boot-first Mode1->7->1"}

    return {
      "classification":"HCOMP_THIRD_OVERLAY_FIRST_HAND_VALIDATED",
      "passed":True,
      "proof_normalization":proof_pass[0],
      "slot_normalization":slot_pass,
      "guest_normalization":guest_pass,
      "mode7_entry_marker":"0x00",
      "hcomp_entry_marker":"0x51",
      "hcomp_slot_bytes":len(want),
      "guest":guest_report,
    }

def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
      p=Path(td)
      (p/"proof-dmem.bin").write_bytes(bytes([0,0x51])+bytes(14))
      want=bytes((i*17)&0xFF for i in range(1000))
      (p/"expected-hcomp-slot.bin").write_bytes(want)
      (p/"slot.bin").write_bytes(want)
      (p/"guest-state.bin").write_bytes(bytes([7,0x33,2,1,1,7,7,0]))
      assert classify(p)["passed"]
      (p/"proof-dmem.bin").write_bytes(bytes([0xFF,0x51])+bytes(14))
      assert not classify(p)["passed"]

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
      self_test(); print("third-overlay dynamic classifier self-test: PASS"); return 0
    if args.evidence is None: ap.error("evidence required")
    result=classify(args.evidence)
    text=json.dumps(result,indent=2,sort_keys=True)
    print(text)
    if args.output: args.output.write_text(text+"\n")
    return 0 if result.get("passed") else 1

if __name__=="__main__":
    raise SystemExit(main())
