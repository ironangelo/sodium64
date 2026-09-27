#!/usr/bin/env python3
"""Classify clean triple-overlay coexistence from RDRAM-only evidence."""
from pathlib import Path
import argparse,json,tempfile
SENT=bytes.fromhex("DEADBEEFCAFEBABE")
GUEST=bytes((0,0x33,2,1,1,0,0,0))
def swap32(d): return b"".join(d[i:i+4][::-1] for i in range(0,len(d),4))
def cands(d):
    yield "identity",d
    if len(d)%4==0: yield "word_swap32",swap32(d)
def classify(root):
    mb=(root/"mailbox.bin").read_bytes(); g=(root/"guest-state.bin").read_bytes()
    if len(mb)!=8 or len(g)!=8: return {"passed":False,"reason":"size","mailbox_bytes":len(mb),"guest_bytes":len(g)}
    mp=None
    for mode,d in cands(mb):
        if d[:2]==bytes((0,0x51)) and d!=SENT: mp=(mode,d); break
    gp=None
    for mode,d in cands(g):
        if d==GUEST: gp=(mode,d); break
    if mp is None:
        return {"passed":False,"reason":"mailbox marker absent","mailbox_raw":mb.hex(),"seed":SENT.hex(),
                "guest_completed":gp is not None,"guest_raw":g.hex()}
    if gp is None:
        return {"passed":False,"reason":"guest incomplete","mailbox_normalization":mp[0],
                "mailbox_normalized":mp[1].hex(),"guest_raw":g.hex()}
    return {"classification":"HCOMP_THIRD_OVERLAY_RDRAM_CLEAN_FIRST_HAND_VALIDATED","passed":True,
            "mailbox_normalization":mp[0],"mailbox_raw":mb.hex(),"mailbox_normalized":mp[1].hex(),
            "guest_normalization":gp[0],"guest_expected":GUEST.hex(),
            "mode7_entry_marker":"0x00","hcomp_entry_marker":"0x51",
            "semantic_scope":"Main->Mode7->Main plus frame-end H-COMP coexistence; no pixel/cadence claim"}
def selftest():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td); good=bytes((0,0x51,0,0,0,0,0,0))
        (p/"mailbox.bin").write_bytes(swap32(good)); (p/"guest-state.bin").write_bytes(swap32(GUEST)); assert classify(p)["passed"]
        (p/"mailbox.bin").write_bytes(SENT); assert not classify(p)["passed"]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("evidence",type=Path,nargs="?"); ap.add_argument("--self-test",action="store_true"); ap.add_argument("--output",type=Path); a=ap.parse_args()
    if a.self_test: selftest(); print("RDRAM classifier self-test: PASS"); return
    if a.evidence is None: ap.error("evidence required")
    r=classify(a.evidence); t=json.dumps(r,indent=2,sort_keys=True); print(t)
    if a.output: a.output.write_text(t+"\n")
    raise SystemExit(0 if r.get("passed") else 1)
if __name__=="__main__": main()
