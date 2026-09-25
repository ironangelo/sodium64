#!/usr/bin/env python3
"""Calibrate pinned-Mupen debugger reads of RSP DMEM against known anchors."""

from __future__ import annotations
import argparse, json
from pathlib import Path

def bswap32(v:int)->int:
    return int.from_bytes(v.to_bytes(4,"big")[::-1],"big")

def read_word(path:Path)->int:
    s="".join(path.read_text().split())
    return int(s,16)

def candidate_modes(got:int,want:int)->list[str]:
    out=[]
    if got==want: out.append("identity")
    if got==bswap32(want): out.append("byte_swap32")
    return out

def normalize_dump(data:bytes)->tuple[str,bytes]:
    want=bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))
    if data==want:
        return "identity",data
    if len(data)%4==0:
        swapped=b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))
        if swapped==want:
            return "word_swap32",swapped
    return "unknown",data

def classify(root:Path)->dict:
    expected=json.loads((root/"expected.json").read_text())
    anchors={
      "mode7_ptr":("e8c-word.txt",int(expected["mode7_ptr"],16)),
      "main_ptr":("e90-word.txt",int(expected["main_ptr"],16)),
      "hcomp_ptr":("e94-word.txt",int(expected["hcomp_ptr"],16)),
      "raw_q1_ptr":("e98-word.txt",int(expected["raw_q1_ptr"],16)),
      "raw_q2_ptr":("e9c-word.txt",int(expected["raw_q2_ptr"],16)),
      "vec_f70":("f70-word.txt",int(expected["vec_f70"],16)),
    }
    report={}
    common=None
    matched=0
    for name,(fn,want) in anchors.items():
        got=read_word(root/fn)
        modes=candidate_modes(got,want)
        report[name]={"got":f"0x{got:08X}","want":f"0x{want:08X}","modes":modes}
        if modes:
            matched+=1
            s=set(modes)
            common=s if common is None else common & s

    wram_got=read_word(root/"wram-word.txt")
    wram_want=0x00330201
    wram_modes=candidate_modes(wram_got,wram_want)
    raw=(root/"guest-state.bin").read_bytes()
    dump_mode,dump_norm=normalize_dump(raw)
    guest_ok=dump_norm==bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))

    proof=read_word(root/"f10-word.txt")
    report["proof_f10"]={"got":f"0x{proof:08X}"}
    report["wram_mem"]={"got":f"0x{wram_got:08X}","want":f"0x{wram_want:08X}","modes":wram_modes}
    report["wram_dump"]={"raw_hex":raw.hex(),"normalization":dump_mode,"guest_ok":guest_ok}

    if matched==len(anchors) and common:
        classification="RSP_DEBUGGER_MEM_CALIBRATED"
        passed=True
        interpretation="known live RSP DMEM anchors are readable with a coherent transform"
    elif guest_ok and wram_modes and matched==0:
        classification="RSP_DEBUGGER_RSP_SPACE_LAB_LIMITATION"
        passed=True
        interpretation="RDRAM observation is coherent while every known RSP DMEM anchor is wrong"
    else:
        classification="RSP_DEBUGGER_MEM_CALIBRATION_INCONCLUSIVE"
        passed=False
        interpretation=f"{matched}/{len(anchors)} RSP anchors matched; do not interpret proof markers yet"

    return {
      "classification":classification,
      "passed":passed,
      "interpretation":interpretation,
      "rsp_anchor_matches":matched,
      "rsp_anchor_total":len(anchors),
      "common_rsp_modes":sorted(common) if common else [],
      "evidence":report,
    }

def self_test()->None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        exp={
          "mode7_ptr":"0x800BA248","main_ptr":"0x800B8248","hcomp_ptr":"0x800B7AB0",
          "raw_q1_ptr":"0xA00EF000","raw_q2_ptr":"0xA00EF800","vec_f70":"0x00020000",
        }
        (p/"expected.json").write_text(json.dumps(exp))
        for name,key in (("e8c","mode7_ptr"),("e90","main_ptr"),("e94","hcomp_ptr"),
                         ("e98","raw_q1_ptr"),("e9c","raw_q2_ptr"),("f70","vec_f70")):
            (p/f"{name}-word.txt").write_text(exp[key][2:]+"\n")
        (p/"f10-word.txt").write_text("00005100\n")
        (p/"wram-word.txt").write_text("00330201\n")
        (p/"guest-state.bin").write_bytes(bytes((0,0x33,2,1,1,0,0,0)))
        assert classify(p)["classification"]=="RSP_DEBUGGER_MEM_CALIBRATED"

        for name in ("e8c","e90","e94","e98","e9c","f70"):
            (p/f"{name}-word.txt").write_text("DEADBEEF\n")
        (p/"guest-state.bin").write_bytes(bytes((1,2,0x33,0,0,0,0,1)))
        assert classify(p)["classification"]=="RSP_DEBUGGER_RSP_SPACE_LAB_LIMITATION"

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test()
        print("RSP debugger memory calibration self-test: PASS")
        return 0
    if args.evidence is None: ap.error("evidence directory required")
    result=classify(args.evidence)
    text=json.dumps(result,indent=2,sort_keys=True)
    print(text)
    if args.output: args.output.write_text(text+"\n")
    return 0 if result["passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())
