#!/usr/bin/env python3
"""Classify whether the first Mode7 rdp_send returns using native texture slots.

The proof does not change RSP code. The first zero-fill Mode7 tile writes
MODE7_TEXTURE+0, then calls rdp_send. Under the workload's zero M7A/M7C,
t7=4, so finish_tile7 advances s0 by 16 and the second tile writes the
existing alternating destination MODE7_TEXTURE+0x1000. Therefore overwrite
of slot1 proves the first rdp_send returned and loop progression reached the
second tile's texture DMA.
"""

from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SLOT0_SENTINEL=bytes.fromhex("1122334455667788")
SLOT1_SENTINEL=bytes.fromhex("99AABBCCDDEEFF00")
MAILBOX_SENTINEL=bytes.fromhex("DEADBEEFCAFEBABE")
EXPECTED_GUEST=bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))

def swap32(data:bytes)->bytes:
    if len(data)%4:
        raise ValueError("word_swap32 requires multiple of four")
    return b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))

def candidates(data:bytes):
    yield "identity",data
    if len(data)%4==0:
        yield "word_swap32",swap32(data)

def match(raw:bytes,target:bytes):
    for mode,data in candidates(raw):
        if data==target:
            return mode
    return None

def marker(raw:bytes):
    for mode,data in candidates(raw):
        if len(data)==8 and data[:2]==bytes((0x00,0x51)) and data!=MAILBOX_SENTINEL:
            return mode,data
    return None

def source_contract()->None:
    main=(ROOT/"src/main.S").read_text()
    ppu=(ROOT/"src/ppu.S").read_text()
    mode7=(ROOT/"src/rsp_mode7.S").read_text()
    guest=(ROOT/"scripts/make_gate_c_hcomp_third_overlay_boot.py").read_text()

    slot0="""    li t0, MODE7_TEXTURE
    li t1, 0x11223344
    sw t1, 0(t0)
    li t1, 0x55667788
    sw t1, 4(t0)"""
    slot1="""    li t0, MODE7_TEXTURE + 0x1000
    li t1, 0x99AABBCC
    sw t1, 0(t0)
    li t1, 0xDDEEFF00
    sw t1, 4(t0)"""
    if main.count(slot0)!=1 or main.count(slot1)!=1:
        raise AssertionError("texture slot sentinel block drift")
    if not (
        main.index(slot0) < main.index(slot1)
        < main.index("sw zero, 0xA4080000 // SP_PC")
    ):
        raise AssertionError("texture slot seed ordering drift")

    # This workload deliberately leaves Mode7 A/C at reset zero.
    if "0x211B" in guest or "0x211D" in guest:
        raise AssertionError("guest now programs M7A/M7C; t7=4 proof invalid")
    for a in ("m7a: .hword 0","m7c: .hword 0"):
        if a not in ppu:
            raise AssertionError(f"Mode7 reset-matrix drift: {a}")

    # Pin the exact path that makes slot1 a post-rdp_send observation.
    anchors=(
      "addi t0, s2, 0x100",
      "sltiu t0, t0, 0x200",
      "addi t1, s5, 0x100",
      "sltiu t1, t1, 0x200",
      "and t0, t0, t1",
      "addi t7, t0, 3 // Width shift",
      "draw_row7:",
      "li s0, 0",
      "li a1, MODE7_TEXTURE",
      "andi t0, s0, 0x18",
      "sll t0, t0, 8",
      "jal dma_write",
      "jal rdp_send",
      "finish_tile7:",
      "lbu t0, SHIFT_TABLE(t7)",
      "add s0, s0, t0",
      "blt s0, 256, next_tile7",
    )
    for a in anchors:
        if a not in mode7:
            raise AssertionError(f"Mode7 progression anchor drift: {a}")

    first=mode7.index("// DMA the texture to alternating RDRAM locations")
    finish=mode7.index("finish_tile7:",first)
    block=mode7[first:finish]
    ps=[block.index(a) for a in ("li a1, MODE7_TEXTURE","jal dma_write","jal rdp_send")]
    if ps!=sorted(ps):
        raise AssertionError("texture DMA / rdp_send order drift")

    ft=mode7.index("finish_tile7:")
    nt=mode7.index("next_tile7:")
    if not (nt < first < ft):
        # Source order is next_tile7 -> DMA/RDP -> finish_tile7.
        raise AssertionError("Mode7 tile-loop source order drift")

    # SHIFT_TABLE index4 must still be 0x10, so t7=4 advances s0 0 -> 16.
    if "shift_table: .byte 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80" not in mode7:
        raise AssertionError("SHIFT_TABLE drift")

def classify(root:Path)->dict:
    source_contract()
    s0=(root/"mode7-texture-slot0.bin").read_bytes()
    s1=(root/"mode7-texture-slot1.bin").read_bytes()
    mb=(root/"mailbox.bin").read_bytes()
    guest=(root/"guest-state.bin").read_bytes()
    if any(len(x)!=8 for x in (s0,s1,mb,guest)):
        return {"passed":False,"reason":"evidence size mismatch"}

    gm=match(guest,EXPECTED_GUEST)
    if gm is None:
        return {"passed":False,"reason":"guest discriminator incomplete","guest_raw":guest.hex()}

    slot0_changed=match(s0,SLOT0_SENTINEL) is None
    slot1_changed=match(s1,SLOT1_SENTINEL) is None
    mm=match(mb,MAILBOX_SENTINEL)
    mk=marker(mb)
    if mk is not None:
        mailbox="hcomp_marker"; mailbox_mode=mk[0]; mailbox_norm=mk[1].hex()
    elif mm is not None:
        mailbox="sentinel"; mailbox_mode=mm; mailbox_norm=MAILBOX_SENTINEL.hex()
    else:
        return {"passed":False,"reason":"mailbox invalid","mailbox_raw":mb.hex()}

    if not slot0_changed:
        classification="MODE7_FIRST_TEXTURE_DMA_NOT_OBSERVED"
        meaning="first texture DMA did not overwrite its seed; this contradicts the prior validated stage and should be treated as lab instability"
    elif slot1_changed and mailbox=="sentinel":
        classification="MODE7_FIRST_RDP_SEND_RETURNED_HCOMP_NOT_REACHED"
        meaning="first rdp_send returned and second tile texture DMA completed; remaining blocker is later repeated RDP/tile-row-layer progression"
    elif not slot1_changed and mailbox=="sentinel":
        classification="MODE7_FIRST_RDP_SEND_NOT_PROVEN_RETURNED"
        meaning="first texture DMA completed but second alternating slot was untouched; localize at first rdp_send/DP wait or immediate post-return progression"
    elif slot1_changed and mailbox=="hcomp_marker":
        classification="MODE7_RDP_RETURN_AND_HCOMP_REACHED"
        meaning="first rdp_send returned, second tile progressed, and frame-end H-COMP was reached"
    else:
        return {
          "passed":False,
          "reason":"contradictory stage evidence",
          "slot0_raw":s0.hex(),"slot1_raw":s1.hex(),"mailbox_raw":mb.hex(),
        }

    return {
      "classification":classification,
      "passed":True,
      "slot0_changed":slot0_changed,
      "slot0_raw":s0.hex(),
      "slot0_seed":SLOT0_SENTINEL.hex(),
      "slot1_changed":slot1_changed,
      "slot1_raw":s1.hex(),
      "slot1_seed":SLOT1_SENTINEL.hex(),
      "mailbox_state":mailbox,
      "mailbox_normalization":mailbox_mode,
      "mailbox_normalized":mailbox_norm,
      "guest_normalization":gm,
      "meaning":meaning,
      "semantic_scope":"pinned-Mupen stage localization only; not real-N64 timing/performance authority",
    }

def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        (p/"guest-state.bin").write_bytes(EXPECTED_GUEST)
        (p/"mailbox.bin").write_bytes(MAILBOX_SENTINEL)

        (p/"mode7-texture-slot0.bin").write_bytes(bytes(8))
        (p/"mode7-texture-slot1.bin").write_bytes(SLOT1_SENTINEL)
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_FIRST_RDP_SEND_NOT_PROVEN_RETURNED"

        (p/"mode7-texture-slot1.bin").write_bytes(bytes(8))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_FIRST_RDP_SEND_RETURNED_HCOMP_NOT_REACHED"

        mk=bytes((0x00,0x51,0,0,0,0,0,0))
        (p/"mailbox.bin").write_bytes(swap32(mk))
        (p/"guest-state.bin").write_bytes(swap32(EXPECTED_GUEST))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_RDP_RETURN_AND_HCOMP_REACHED"

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test()
        print("Mode7 rdp-return classifier self-test: PASS")
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
