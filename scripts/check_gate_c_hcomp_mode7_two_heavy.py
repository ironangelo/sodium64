#!/usr/bin/env python3
"""Classify execution of the exact-two-heavy-tile Mode7 discriminator."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import check_gate_c_midframe_sections as sections

ROOT=Path(__file__).resolve().parents[1]
SLOT0_SENTINEL=bytes.fromhex("1122334455667788")
SLOT1_SENTINEL=bytes.fromhex("99AABBCCDDEEFF00")
MAILBOX_SENTINEL=bytes.fromhex("DEADBEEFCAFEBABE")
EXPECTED_GUEST=bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))


def swap32(data:bytes)->bytes:
    if len(data)%4:
        raise ValueError("word_swap32 requires a multiple of four bytes")
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
    sections.source_contract()
    main=(ROOT/"src/main.S").read_text()
    mode7=(ROOT/"src/rsp_mode7.S").read_text()

    slot0="""    li t0, MODE7_TEXTURE
    li t1, 0x11223344
    sw t1, 0(t0)
    li t1, 0x55667788
    sw t1, 4(t0)"""
    slot1="""    li t0, MODE7_TEXTURE + 0x800
    li t1, 0x99AABBCC
    sw t1, 0(t0)
    li t1, 0xDDEEFF00
    sw t1, 4(t0)"""
    if main.count(slot0)!=1 or main.count(slot1)!=1:
        raise AssertionError("two-heavy texture sentinel block drift")
    if "MODE7_TEXTURE + 0x1000" in main:
        raise AssertionError("stale t7=4 second-slot sentinel remains in CPU proof setup")
    if not (
        main.index(slot0) < main.index(slot1)
        < main.index("sw zero, 0xA4080000 // SP_PC")
    ):
        raise AssertionError("two-heavy texture sentinel ordering drift")

    if (
        sections.EXPECTED_M7SEL!=0x80
        or sections.EXPECTED_M7A!=0x4000
        or any((sections.EXPECTED_M7B,sections.EXPECTED_M7C,sections.EXPECTED_M7D,
                sections.EXPECTED_M7X,sections.EXPECTED_M7Y))
    ):
        raise AssertionError("section-state authority no longer describes two-heavy guest")

    # Pin exact native texture-address selection and post-tile progression.
    anchors=(
      "draw_row7:",
      "li s0, 0",
      "check_wrap:",
      "bnez t0, finish_tile7",
      "set_texels:",
      "li a1, MODE7_TEXTURE",
      "andi t0, s0, 0x18",
      "sll t0, t0, 8",
      "add a1, a1, t0",
      "jal dma_write",
      "jal rdp_send",
      "finish_tile7:",
      "lbu t0, SHIFT_TABLE(t7)",
      "sll t1, s2, t7",
      "add s0, s0, t0",
      "add t8, t8, t1",
      "blt s0, 256, next_tile7",
    )
    for anchor in anchors:
        if anchor not in mode7:
            raise AssertionError(f"two-heavy execution anchor drift: {anchor!r}")

    # t7=3 => s0 0->8. The existing destination expression therefore maps
    # the two heavy tiles to +0 and +0x800. Tile2 (s0=16 => +0x1000) is
    # source/model-proved by sections.source_contract() to fast-out pre-DMA.
    offsets=tuple(((s0&0x18)<<8) for s0 in (0,8,16))
    if offsets!=(0x000,0x800,0x1000):
        raise AssertionError(f"texture destination model drift: {offsets}")

    first=mode7.index("// DMA the texture to alternating RDRAM locations")
    finish=mode7.index("finish_tile7:",first)
    block=mode7[first:finish]
    pos=[block.index(a) for a in ("li a1, MODE7_TEXTURE","jal dma_write","jal rdp_send")]
    if pos!=sorted(pos):
        raise AssertionError("texture DMA / rdp_send ordering drift")


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

    sentinel_mode=match(mb,MAILBOX_SENTINEL)
    mk=marker(mb)
    if mk is not None:
        mailbox="hcomp_marker"; mailbox_mode=mk[0]; mailbox_norm=mk[1].hex()
    elif sentinel_mode is not None:
        mailbox="sentinel"; mailbox_mode=sentinel_mode; mailbox_norm=MAILBOX_SENTINEL.hex()
    else:
        return {"passed":False,"reason":"mailbox invalid","mailbox_raw":mb.hex()}

    if not slot0_changed and not slot1_changed and mailbox=="sentinel":
        classification="MODE7_TWO_HEAVY_FIRST_TEXTURE_NOT_OBSERVED"
        meaning="bounded workload did not reach even tile0 texture DMA; prior stage authority did not reproduce"
    elif slot0_changed and not slot1_changed and mailbox=="sentinel":
        classification="MODE7_TWO_HEAVY_SECOND_TEXTURE_NOT_OBSERVED"
        meaning="tile0 texture DMA completed but tile1 texture DMA was not observed"
    elif slot0_changed and slot1_changed and mailbox=="sentinel":
        classification="MODE7_TWO_HEAVY_COMPLETED_HCOMP_NOT_REACHED"
        meaning="both heavy tiles completed texture DMA, but row/layer/frame-end did not reach H-COMP in the observation"
    elif slot0_changed and slot1_changed and mailbox=="hcomp_marker":
        classification="MODE7_TWO_HEAVY_COMPLETED_HCOMP_REACHED"
        meaning="both heavy tiles completed and the bounded row/layer returned through frame-end H-COMP"
    else:
        return {
          "passed":False,
          "reason":"contradictory two-heavy stage evidence",
          "slot0_changed":slot0_changed,
          "slot1_changed":slot1_changed,
          "mailbox_state":mailbox,
          "slot0_raw":s0.hex(),
          "slot1_raw":s1.hex(),
          "mailbox_raw":mb.hex(),
        }

    return {
      "passed":True,
      "classification":classification,
      "meaning":meaning,
      "slot0_changed":slot0_changed,
      "slot0_raw":s0.hex(),
      "slot0_seed":SLOT0_SENTINEL.hex(),
      "slot0_offset":"0x000",
      "slot1_changed":slot1_changed,
      "slot1_raw":s1.hex(),
      "slot1_seed":SLOT1_SENTINEL.hex(),
      "slot1_offset":"0x800",
      "mailbox_state":mailbox,
      "mailbox_normalization":mailbox_mode,
      "mailbox_normalized":mailbox_norm,
      "guest_normalization":gm,
      "queued_state_authority":"MIDFRAME_MODE7_TWO_HEAVY_SECTION_PRODUCTION_VALIDATED",
      "semantic_scope":"pinned-Mupen bounded-work stage localization only; not real-N64 timing/performance authority",
    }


def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        (p/"guest-state.bin").write_bytes(EXPECTED_GUEST)
        (p/"mailbox.bin").write_bytes(MAILBOX_SENTINEL)

        (p/"mode7-texture-slot0.bin").write_bytes(SLOT0_SENTINEL)
        (p/"mode7-texture-slot1.bin").write_bytes(SLOT1_SENTINEL)
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_TWO_HEAVY_FIRST_TEXTURE_NOT_OBSERVED"

        (p/"mode7-texture-slot0.bin").write_bytes(bytes(8))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_TWO_HEAVY_SECOND_TEXTURE_NOT_OBSERVED"

        (p/"mode7-texture-slot1.bin").write_bytes(bytes(8))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_TWO_HEAVY_COMPLETED_HCOMP_NOT_REACHED"

        marker_bytes=bytes((0x00,0x51,0,0,0,0,0,0))
        (p/"mailbox.bin").write_bytes(swap32(marker_bytes))
        (p/"guest-state.bin").write_bytes(swap32(EXPECTED_GUEST))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_TWO_HEAVY_COMPLETED_HCOMP_REACHED"


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test()
        print("Mode7 two-heavy execution classifier self-test: PASS")
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
