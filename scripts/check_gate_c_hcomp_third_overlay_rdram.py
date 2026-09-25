#!/usr/bin/env python3
"""Classify first-hand triple-overlay coexistence from RDRAM-only evidence."""

from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path

MAILBOX_SENTINEL=bytes.fromhex("DEADBEEFCAFEBABE")
EXPECTED_GUEST=bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))

def swap32(data:bytes)->bytes:
    if len(data)%4: raise ValueError("word_swap32 requires multiple of 4")
    return b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))

def candidates(data:bytes):
    yield "identity",data
    if len(data)%4==0: yield "word_swap32",swap32(data)

def classify(root:Path)->dict:
    mb=(root/"mailbox.bin").read_bytes()
    guest=(root/"guest-state.bin").read_bytes()
    if len(mb)!=8 or len(guest)!=8:
        return {"passed":False,"reason":"evidence size mismatch","mailbox_bytes":len(mb),"guest_bytes":len(guest)}

    mailbox_pass=None
    mailbox_norm=None
    for mode,data in candidates(mb):
        if data[0]==0x00 and data[1]==0x51 and data!=MAILBOX_SENTINEL:
            mailbox_pass=mode; mailbox_norm=data; break
    if mailbox_pass is None:
        return {
          "passed":False,
          "reason":"RDRAM marker mailbox does not prove Mode7+H-COMP entry",
          "mailbox_raw":mb.hex(),
          "seed_sentinel":MAILBOX_SENTINEL.hex(),
        }

    guest_pass=None
    for mode,data in candidates(guest):
        if data==EXPECTED_GUEST:
            guest_pass=mode; break
    if guest_pass is None:
        return {
          "passed":False,
          "reason":"guest Mode1->7->1 discriminator incomplete",
          "mailbox_normalization":mailbox_pass,
          "mailbox_normalized":mailbox_norm.hex(),
          "guest_raw":guest.hex(),
        }

    return {
      "classification":"HCOMP_THIRD_OVERLAY_RDRAM_FIRST_HAND_VALIDATED",
      "passed":True,
      "mailbox_normalization":mailbox_pass,
      "mailbox_raw":mb.hex(),
      "mailbox_normalized":mailbox_norm.hex(),
      "mode7_entry_marker":"0x00",
      "hcomp_entry_marker":"0x51",
      "guest_normalization":guest_pass,
      "guest_expected":EXPECTED_GUEST.hex(),
      "semantic_scope":"three fixed-slot payloads execute/coexist in one first handoff; no compositor-output or cadence claim",
    }

def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        canonical=bytes((0x00,0x51,0,0,0,0,0,0))
        (p/"mailbox.bin").write_bytes(canonical)
        (p/"guest-state.bin").write_bytes(EXPECTED_GUEST)
        assert classify(p)["passed"]
        (p/"mailbox.bin").write_bytes(swap32(canonical))
        (p/"guest-state.bin").write_bytes(swap32(EXPECTED_GUEST))
        assert classify(p)["passed"]
        (p/"mailbox.bin").write_bytes(MAILBOX_SENTINEL)
        assert not classify(p)["passed"]

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test(); print("third-overlay RDRAM classifier self-test: PASS"); return 0
    if args.evidence is None: ap.error("evidence directory required")
    result=classify(args.evidence)
    text=json.dumps(result,indent=2,sort_keys=True)
    print(text)
    if args.output: args.output.write_text(text+"\n")
    return 0 if result.get("passed") else 1

if __name__=="__main__":
    raise SystemExit(main())
