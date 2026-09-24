#!/usr/bin/env python3
"""Validate diagnostic RSP raw-palette selection/DMA with guarded mailboxes."""

from __future__ import annotations
import argparse
import json
from pathlib import Path

PRE = [0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00]
POST = [0x0FF1CE00, 0x13579BDF, 0x2468ACE0, 0x55AA33CC]
RED = 0xF801F801
GREEN = 0x07C107C1
BLUE = 0x003F003F

def swap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("word_swap32 needs a multiple of 4 bytes")
    return b"".join(data[i:i+4][::-1] for i in range(0, len(data), 4))

def words(data: bytes) -> list[int]:
    if len(data) % 4:
        raise ValueError("word data must be aligned")
    return [int.from_bytes(data[i:i+4], "big") for i in range(0, len(data), 4)]

def phase(raw: bytes) -> str | None:
    w = words(raw)
    if len(w) != 4 or w[0] != w[1] or w[2] != BLUE or w[3] != BLUE:
        return None
    if w[0] == RED:
        return "red"
    if w[0] == GREEN:
        return "green"
    return None

def classify(raw1: bytes, raw2: bytes, mailbox: bytes) -> dict[str, object]:
    if len(raw1) != 16 or len(raw2) != 16 or len(mailbox) != 64:
        raise ValueError("expected raw dumps 16B each and mailbox 64B")
    first = None
    for mode in ("identity", "word_swap32"):
        norm = (lambda x: x) if mode == "identity" else swap32
        q1, q2, mb = norm(raw1), norm(raw2), norm(mailbox)
        mw = words(mb)
        p1, p2 = phase(q1), phase(q2)
        checks = {
            "preguard": mw[0:4] == PRE,
            "postguard": mw[12:16] == POST,
            "slot0_matches_raw_q1": mb[16:32] == q1,
            "slot1_matches_raw_q2": mb[32:48] == q2,
            "raw_phases_valid_and_opposite": p1 in ("red","green") and p2 in ("red","green") and p1 != p2,
        }
        passed = all(checks.values())
        result = {
            "classification": "RAW_PALETTE_RSP_SELECTION_DMA_VALIDATED" if passed else "RAW_PALETTE_RSP_SELECTION_DMA_FAILED",
            "passed": passed,
            "dump_normalization": mode,
            "raw_q1_phase": p1,
            "raw_q2_phase": p2,
            "checks": checks,
            "mailbox_words": [f"0x{x:08X}" for x in mw],
        }
        if passed:
            return result
        if first is None:
            first = result
    assert first is not None
    return first

def self_test() -> None:
    q1 = b"".join(x.to_bytes(4,"big") for x in [RED,RED,BLUE,BLUE])
    q2 = b"".join(x.to_bytes(4,"big") for x in [GREEN,GREEN,BLUE,BLUE])
    mb = b"".join(x.to_bytes(4,"big") for x in PRE) + q1 + q2 + b"".join(x.to_bytes(4,"big") for x in POST)
    assert classify(q1,q2,mb)["passed"]
    got=classify(swap32(q1),swap32(q2),swap32(mb))
    assert got["passed"] and got["dump_normalization"]=="word_swap32"
    bad=bytearray(mb); bad[-1]^=1
    assert not classify(q1,q2,bytes(bad))["passed"]
    assert not classify(q2,q1,mb)["passed"]
    print("raw-palette RSP selection/DMA classifier self-test: PASS")

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw_q1",type=Path,nargs="?")
    ap.add_argument("raw_q2",type=Path,nargs="?")
    ap.add_argument("mailbox",type=Path,nargs="?")
    ap.add_argument("--output",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if None in (args.raw_q1,args.raw_q2,args.mailbox):
        ap.error("raw_q1 raw_q2 mailbox are required")
    result=classify(args.raw_q1.read_bytes(),args.raw_q2.read_bytes(),args.mailbox.read_bytes())
    rendered=json.dumps(result,indent=2,sort_keys=True)+"\n"
    print(rendered,end="")
    if args.output:
        args.output.write_text(rendered,encoding="utf-8")
    return 0 if result["passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())
