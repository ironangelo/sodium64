#!/usr/bin/env python3
"""Validate diagnostic RSP selection/DMA of the published raw palette queue."""
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
MAGIC=0x48524157
PTRS={0:0xA00EF000,4:0xA00EF800}
RED=(0xF801).to_bytes(2,"big")*4
GREEN=(0x07C1).to_bytes(2,"big")*4
BLUE=(0x003F).to_bytes(2,"big")*4
WHITE=(0xFFFF).to_bytes(2,"big")*4

def swap32(data:bytes)->bytes:
    if len(data)%4: raise ValueError("dump length must be divisible by 4")
    return b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))

def classify(path:Path)->dict[str,object]:
    raw=path.read_bytes()
    if len(raw)<48: raise ValueError("diagnostic mailbox dump must contain at least 48 bytes")
    first=None
    for mode in ("identity","word_swap32"):
        data=raw[:48] if mode=="identity" else swap32(raw[:48])
        ptr=int.from_bytes(data[0:4],"big"); slot=int.from_bytes(data[4:8],"big")
        magic=int.from_bytes(data[8:12],"big"); reserved=int.from_bytes(data[12:16],"big")
        e1,e2,e3=data[16:24],data[24:32],data[32:40]
        phase="red" if e1==RED else "green" if e1==GREEN else None
        expected=PTRS.get(slot)
        passed=bool(expected is not None and ptr==expected and magic==MAGIC and reserved==0 and phase is not None and e2==BLUE and e3==WHITE)
        result={"classification":"RSP_RAW_PALETTE_DMA_VALIDATED" if passed else "RSP_RAW_PALETTE_DMA_FAILED","passed":passed,"dump_normalization":mode,"slot":slot,"selected_pointer":f"0x{ptr:08X}","expected_pointer":None if expected is None else f"0x{expected:08X}","phase":phase,"magic":f"0x{magic:08X}","fixed_blue_ok":e2==BLUE,"fixed_white_ok":e3==WHITE}
        if passed:return result
        if first is None:first=result
    assert first is not None
    return first

def self_test()->None:
    def sample(slot:int,phase:bytes)->bytes:
        b=bytearray(48); b[0:4]=PTRS[slot].to_bytes(4,"big"); b[4:8]=slot.to_bytes(4,"big"); b[8:12]=MAGIC.to_bytes(4,"big"); b[16:24]=phase; b[24:32]=BLUE; b[32:40]=WHITE; return bytes(b)
    with tempfile.TemporaryDirectory() as td_s:
        p=Path(td_s)/"d.bin"; p.write_bytes(sample(0,RED)); assert classify(p)["passed"]
        p.write_bytes(swap32(sample(4,GREEN))); r=classify(p); assert r["passed"] and r["dump_normalization"]=="word_swap32"
        bad=bytearray(sample(0,RED)); bad[3]^=1; p.write_bytes(bad); assert not classify(p)["passed"]

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("dump",type=Path,nargs="?"); ap.add_argument("--self-test",action="store_true"); ap.add_argument("--output",type=Path); args=ap.parse_args()
    if args.self_test: self_test(); print("RSP raw-palette DMA classifier self-test: PASS"); return 0
    if args.dump is None: ap.error("dump is required unless --self-test is used")
    result=classify(args.dump); text=json.dumps(result,indent=2,sort_keys=True); print(text)
    if args.output: args.output.write_text(text+"\n",encoding="utf-8")
    return 0 if result["passed"] else 1
if __name__=="__main__": raise SystemExit(main())
