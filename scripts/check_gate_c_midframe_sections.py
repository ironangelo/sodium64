#!/usr/bin/env python3
"""Classify enabled Mode7 empty/out-of-bounds mid-frame section state.

This proof is intentionally read-only with respect to Sodium64 runtime.  It
examines both fixed section queues after the boot-first 2-line Mode7 guest has
completed and asks whether the CPU actually queued Mode1 -> Mode7 -> Mode1.

For the guest's V-IRQs at lines 80 and 82:
- BGMODE7 is written during line 80, after that line's section check.
- line 81 therefore closes the previous Mode1 section at split=80 and snapshots
  the new Mode7 state.
- BGMODE1 is written during line 82.
- line 83 closes the Mode7 section at split=82 and snapshots Mode1.
- vblank begins at line 225, so final make_section closes Mode1 at split=224.
"""

from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path

SECTION_SIZE=0x40
M7X_OFFSET=0x20
M7Y_OFFSET=0x22
M7SEL_OFFSET=0x33
TM_OFFSET=0x3A
BG_MODE_OFFSET=0x3D
STAT_FLAGS_OFFSET=0x3E
SPLIT_LINE_OFFSET=0x3F
QUEUE_CAPTURE_BYTES=0x200
EXPECTED_MODES=(1,7,1)
EXPECTED_TM=(1,1,1)
EXPECTED_M7SEL=0x80
EXPECTED_M7X=0x0FFF
EXPECTED_M7Y=0x0FFF
EXPECTED_SPLITS=(80,82,224)
EXPECTED_GUEST=bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))

ROOT=Path(__file__).resolve().parents[1]

def swap32(data:bytes)->bytes:
    if len(data)%4:
        raise ValueError("word_swap32 requires a multiple of four bytes")
    return b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))

def candidates(data:bytes):
    yield "identity",data
    if len(data)%4==0:
        yield "word_swap32",swap32(data)

def source_contract()->None:
    defs=(ROOT/"src/defines.h").read_text()
    ppu=(ROOT/"src/ppu.S").read_text()
    rsp=(ROOT/"src/rsp_main.S").read_text()
    rsp7=(ROOT/"src/rsp_mode7.S").read_text()

    anchors_defs=(
      "#define SECTION_SIZE 0x40",
      "#define M7X (M7D + 0x2)",
      "#define M7Y (M7X + 0x2)",
      "#define M7SEL (OBSEL + 0x1)",
      "#define TM (TS + 0x1)",
      "#define BG_MODE (TMW + 0x1)",
      "#define STAT_FLAGS (BG_MODE + 0x1)",
      "#define SPLIT_LINE (STAT_FLAGS + 0x1)",
      "#define SECTION_QUEUE2 (OBJECT_CACHE - 0x5000)",
      "#define SECTION_QUEUE1 (SECTION_QUEUE2 - 0x5000)",
    )
    for a in anchors_defs:
        if a not in defs:
            raise AssertionError(f"section ABI drift: {a}")

    # Pin the exact CPU production semantics this dynamic oracle relies on.
    for a in (
      "write_bgmode:",
      "bne t1, t0, update_window_frame",
      "write_m7sel:",
      "write_m7x:",
      "write_m7y:",
      "update_window_frame:",
      "li t0, 0x100",
      "sh t0, sect_status",
      "bne t0, 0x100, skip_section",
      "jal make_section",
      "make_section:",
      "addi a0, a0, -1",
      "sb a0, (t1)",
      "section_init:",
      "addi t2, t0, SECTION_SIZE",
    ):
        if a not in ppu:
            raise AssertionError(f"CPU section-production anchor drift: {a}")

    # Pin shared consumer dispatch in the regular resident image.
    for a in (
      "next_section:",
      "li a0, BGHOFS",
      "lw a1, SECTION_PTR(sp)",
      "li a2, SECTION_SIZE - 1",
      "lbu s3, BG_MODE",
      "andi s3, s3, 0xF",
      "beq t0, t1, draw_mode7_entry",
    ):
        if a not in rsp:
            raise AssertionError(f"RSP section-consumer anchor drift: {a}")

    # The OOB fast path lives only in the true Mode7 overlay payload.
    mode7_anchors=(
      "draw_mode7_impl:",
      "check_wrap:",
      "andi t6, t0, 0xC0",
      "bne t6, t1, set_texels",
      "lw t1, MODE7_MASK",
      "bnez t0, finish_tile7",
      "set_texels:",
      "entry_row:",
    )
    for a in mode7_anchors:
        if a not in rsp7:
            raise AssertionError(f"Mode7 fast-path anchor drift: {a}")
    if not (
        rsp7.index("check_wrap:")
        < rsp7.index("set_texels:")
        < rsp7.index("entry_row:")
    ):
        raise AssertionError("Mode7 OOB early-out ordering drift")

def records(data:bytes,count:int=8)->list[dict]:
    if len(data)<count*SECTION_SIZE:
        raise ValueError("section queue capture too short")
    out=[]
    for i in range(count):
        r=data[i*SECTION_SIZE:(i+1)*SECTION_SIZE]
        out.append({
          "index":i,
          "mode":r[BG_MODE_OFFSET]&0x0F,
          "tm":r[TM_OFFSET],
          "m7sel":r[M7SEL_OFFSET],
          "m7x":int.from_bytes(r[M7X_OFFSET:M7X_OFFSET+2],"big"),
          "m7y":int.from_bytes(r[M7Y_OFFSET:M7Y_OFFSET+2],"big"),
          "raw_bg_mode":r[BG_MODE_OFFSET],
          "stat_flags":r[STAT_FLAGS_OFFSET],
          "split":r[SPLIT_LINE_OFFSET],
          "nonzero":sum(1 for b in r if b),
        })
    return out

def find_signature(rs:list[dict]):
    for i in range(0,len(rs)-2):
        trip=rs[i:i+3]
        if (
            tuple(r["mode"] for r in trip)==EXPECTED_MODES
            and tuple(r["tm"] for r in trip)==EXPECTED_TM
            and all(r["m7sel"]==EXPECTED_M7SEL for r in trip)
            and all(r["m7x"]==EXPECTED_M7X for r in trip)
            and all(r["m7y"]==EXPECTED_M7Y for r in trip)
            and tuple(r["split"] for r in trip)==EXPECTED_SPLITS
        ):
            return i,trip
    return None

def normalize_guest(raw:bytes):
    for mode,data in candidates(raw):
        if data==EXPECTED_GUEST:
            return mode,data
    return None

def classify(root:Path)->dict:
    source_contract()
    guest=(root/"guest-state.bin").read_bytes()
    g=normalize_guest(guest)
    if g is None:
        return {
          "passed":False,
          "reason":"guest Mode1->7->1 discriminator incomplete",
          "guest_raw":guest.hex(),
        }

    reports={}
    winners=[]
    for qname in ("q1","q2"):
        raw=(root/f"section-{qname}.bin").read_bytes()
        if len(raw)!=QUEUE_CAPTURE_BYTES:
            return {
              "passed":False,
              "reason":f"{qname} capture size mismatch",
              "bytes":len(raw),
            }
        best=None
        for norm,data in candidates(raw):
            rs=records(data)
            sig=find_signature(rs)
            report={"normalization":norm,"records":rs}
            if sig is not None:
                report["signature_start"]=sig[0]
                report["signature_records"]=sig[1]
                best=report
                winners.append(qname)
                break
            if best is None:
                best=report
        reports[qname]=best

    if len(winners)!=1:
        return {
          "passed":False,
          "reason":"expected unique Mode1->Mode7->Mode1 section signature not found",
          "guest_normalization":g[0],
          "queues":reports,
          "matching_queues":winners,
        }

    q=winners[0]
    return {
      "classification":"MIDFRAME_MODE7_EMPTY_OOB_SECTION_PRODUCTION_VALIDATED",
      "passed":True,
      "guest_normalization":g[0],
      "matching_queue":q,
      "expected_modes":list(EXPECTED_MODES),
      "expected_tm":list(EXPECTED_TM),
      "expected_m7sel":EXPECTED_M7SEL,
      "expected_m7x":EXPECTED_M7X,
      "expected_m7y":EXPECTED_M7Y,
      "expected_splits":list(EXPECTED_SPLITS),
      "queue":reports[q],
      "semantic_scope":"CPU queued exact enabled Mode7 empty/OOB state; RSP heavy-path reachability remains a separate question",
    }

def synthetic_queue()->bytes:
    q=bytearray(QUEUE_CAPTURE_BYTES)
    for i,(mode,tm,split) in enumerate(zip(EXPECTED_MODES,EXPECTED_TM,EXPECTED_SPLITS,strict=True)):
        off=i*SECTION_SIZE
        q[off+BG_MODE_OFFSET]=mode
        q[off+TM_OFFSET]=tm
        q[off+M7SEL_OFFSET]=EXPECTED_M7SEL
        q[off+M7X_OFFSET:off+M7X_OFFSET+2]=EXPECTED_M7X.to_bytes(2,"big")
        q[off+M7Y_OFFSET:off+M7Y_OFFSET+2]=EXPECTED_M7Y.to_bytes(2,"big")
        q[off+STAT_FLAGS_OFFSET]=0x40 if i==0 else 0
        q[off+SPLIT_LINE_OFFSET]=split
    return bytes(q)

def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        q=synthetic_queue()
        (p/"section-q1.bin").write_bytes(q)
        (p/"section-q2.bin").write_bytes(bytes(QUEUE_CAPTURE_BYTES))
        (p/"guest-state.bin").write_bytes(EXPECTED_GUEST)
        assert classify(p)["passed"]

        (p/"section-q1.bin").write_bytes(swap32(q))
        (p/"guest-state.bin").write_bytes(swap32(EXPECTED_GUEST))
        assert classify(p)["passed"]

        bad=bytearray(q)
        bad[SECTION_SIZE+BG_MODE_OFFSET]=1
        (p/"section-q1.bin").write_bytes(bytes(bad))
        assert not classify(p)["passed"]

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test()
        print("mid-frame section classifier self-test: PASS")
        return 0
    if args.evidence is None:
        ap.error("evidence directory required")
    result=classify(args.evidence)
    text=json.dumps(result,indent=2,sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text+"\n")
    return 0 if result.get("passed") else 1

if __name__=="__main__":
    raise SystemExit(main())
