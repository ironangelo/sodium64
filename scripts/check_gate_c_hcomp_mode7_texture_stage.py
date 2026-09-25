#!/usr/bin/env python3
"""Classify Mode7 post-map progression from ordinary RDRAM evidence.

The proof seeds the first MODE7_TEXTURE destination after CPU boot clearing.
No RSP instrumentation is added. The existing Mode7 renderer must overwrite
that destination only after its map stage, character DMA/vector decode and
texture DMA have completed; rdp_send follows immediately afterward.
"""

from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEXTURE_SENTINEL=bytes.fromhex("1122334455667788")
MAILBOX_SENTINEL=bytes.fromhex("DEADBEEFCAFEBABE")
EXPECTED_GUEST=bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))
MODE7_TEXTURE_KSEG1=0xA0154A00
MODE7_TEXTURE_KSEG0=0x80154A00

def swap32(data:bytes)->bytes:
    if len(data)%4:
        raise ValueError("word_swap32 requires multiple of four")
    return b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))

def candidates(data:bytes):
    yield "identity",data
    if len(data)%4==0:
        yield "word_swap32",swap32(data)

def match_mode(raw:bytes,target:bytes):
    for mode,data in candidates(raw):
        if data==target:
            return mode
    return None

def marker_mode(raw:bytes):
    for mode,data in candidates(raw):
        if len(data)==8 and data[:2]==bytes((0x00,0x51)) and data!=MAILBOX_SENTINEL:
            return mode,data
    return None

def source_contract()->None:
    defs=(ROOT/"src/defines.h").read_text()
    main=(ROOT/"src/main.S").read_text()
    mode7=(ROOT/"src/rsp_mode7.S").read_text()

    for a in (
      "#define ROM_BUFFER 0xA0200000",
      "#define JIT_BUFFER (ROM_BUFFER - 0x40000)",
      "#define TILE_CACHE_BG (JIT_BUFFER - 0x40000)",
      "#define TILE_CACHE_OBJ (TILE_CACHE_BG - 0x8000)",
      "#define TILE_STATS_BG (TILE_CACHE_OBJ - 0x1000)",
      "#define TILE_STATS_OBJ (TILE_STATS_BG - 0x200)",
      "#define OBJECT_CACHE (TILE_STATS_OBJ - 0x800)",
      "#define SECTION_QUEUE2 (OBJECT_CACHE - 0x5000)",
      "#define SECTION_QUEUE1 (SECTION_QUEUE2 - 0x5000)",
      "#define DIRTY_QUEUE2 (SECTION_QUEUE1 - 0x400)",
      "#define DIRTY_QUEUE1 (DIRTY_QUEUE2 - 0x400)",
      "#define OAM_QUEUE2 (DIRTY_QUEUE1 - 0x2200)",
      "#define OAM_QUEUE1 (OAM_QUEUE2 - 0x2200)",
      "#define PALETTE_QUEUE2 (OAM_QUEUE1 - 0x800)",
      "#define PALETTE_QUEUE1 (PALETTE_QUEUE2 - 0x800)",
      "#define VRAM_BUFFER (PALETTE_QUEUE1 - 0x10000)",
      "#define MODE7_TEXTURE (VRAM_BUFFER - 0x2000)",
    ):
        if a not in defs:
            raise AssertionError(f"MODE7_TEXTURE layout drift: {a}")

    # Recompute the exact fixed address independently of the workflow literal.
    x=0xA0200000
    for d in (0x40000,0x40000,0x8000,0x1000,0x200,0x800,
              0x5000,0x5000,0x400,0x400,0x2200,0x2200,0x800,0x800,
              0x10000,0x2000):
        x-=d
    if x!=MODE7_TEXTURE_KSEG1 or x-0x20000000!=MODE7_TEXTURE_KSEG0:
        raise AssertionError(f"MODE7_TEXTURE address mismatch: {x:#x}")

    seed_block="""    li t0, MODE7_TEXTURE
    li t1, 0x11223344
    sw t1, 0(t0)
    li t1, 0x55667788
    sw t1, 4(t0)"""
    if main.count(seed_block)!=1:
        raise AssertionError("texture sentinel block missing or duplicated")
    seed_pos=main.index(seed_block)
    if not (
        main.index("DMEM(HCOMP_RAW_PALETTE_PTRS + 4)") < seed_pos
        < main.index("sw zero, 0xA4080000 // SP_PC")
    ):
        raise AssertionError("texture sentinel is not post-init/pre-RSP")

    if mode7.count("li a1, MODE7_TEXTURE")!=1:
        raise AssertionError("MODE7_TEXTURE RSP writer is no longer unique")
    block_start=mode7.index("// DMA the texture to alternating RDRAM locations")
    block_end=mode7.index("finish_tile7:",block_start)
    block=mode7[block_start:block_end]
    anchors=("li a0, TEXTURE","li a1, MODE7_TEXTURE","jal dma_write","jal rdp_send")
    ps=[block.index(a) for a in anchors]
    if ps!=sorted(ps):
        raise AssertionError("Mode7 texture DMA / RDP ordering drift")

def classify(root:Path)->dict:
    source_contract()
    tex=(root/"mode7-texture.bin").read_bytes()
    mb=(root/"mailbox.bin").read_bytes()
    guest=(root/"guest-state.bin").read_bytes()
    if len(tex)!=8 or len(mb)!=8 or len(guest)!=8:
        return {
          "passed":False,"reason":"evidence size mismatch",
          "texture_bytes":len(tex),"mailbox_bytes":len(mb),"guest_bytes":len(guest),
        }

    guest_mode=match_mode(guest,EXPECTED_GUEST)
    if guest_mode is None:
        return {
          "passed":False,
          "reason":"guest Mode1->7->1 discriminator incomplete",
          "guest_raw":guest.hex(),
        }

    texture_seed_mode=match_mode(tex,TEXTURE_SENTINEL)
    texture_dma_observed=texture_seed_mode is None

    mailbox_seed_mode=match_mode(mb,MAILBOX_SENTINEL)
    marker=marker_mode(mb)
    if marker is not None:
        mailbox_state="hcomp_marker"
        mailbox_mode=marker[0]
        mailbox_normalized=marker[1].hex()
    elif mailbox_seed_mode is not None:
        mailbox_state="sentinel"
        mailbox_mode=mailbox_seed_mode
        mailbox_normalized=MAILBOX_SENTINEL.hex()
    else:
        return {
          "passed":False,
          "reason":"mailbox is neither sentinel nor valid Mode7/H-COMP marker",
          "mailbox_raw":mb.hex(),
          "texture_raw":tex.hex(),
          "guest_normalization":guest_mode,
        }

    if texture_dma_observed and mailbox_state=="sentinel":
        classification="MODE7_TEXTURE_DMA_COMPLETED_HCOMP_NOT_REACHED"
        meaning="char DMA/decode plus texture DMA progressed; remaining blocker is rdp_send/DP wait or later tile/row/layer progression"
    elif texture_dma_observed and mailbox_state=="hcomp_marker":
        classification="MODE7_TEXTURE_DMA_AND_HCOMP_REACHED"
        meaning="post-map heavy path progressed through texture DMA and later frame-end H-COMP"
    elif not texture_dma_observed and mailbox_state=="sentinel":
        classification="MODE7_TEXTURE_DMA_NOT_REACHED"
        meaning="progress stopped before the first texture DMA; localize in entry-row/char DMA/decode or texture-DMA issue"
    else:
        return {
          "passed":False,
          "reason":"contradictory stage evidence: H-COMP marker with untouched texture sentinel",
          "texture_raw":tex.hex(),
          "mailbox_raw":mb.hex(),
          "guest_normalization":guest_mode,
        }

    return {
      "classification":classification,
      "passed":True,
      "texture_dma_observed":texture_dma_observed,
      "texture_raw":tex.hex(),
      "texture_seed_normalization":texture_seed_mode,
      "texture_seed":TEXTURE_SENTINEL.hex(),
      "mailbox_state":mailbox_state,
      "mailbox_normalization":mailbox_mode,
      "mailbox_raw":mb.hex(),
      "mailbox_normalized":mailbox_normalized,
      "guest_normalization":guest_mode,
      "guest_expected":EXPECTED_GUEST.hex(),
      "meaning":meaning,
      "semantic_scope":"diagnostic localization in pinned Mupen; not real-N64 timing/performance authority",
    }

def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        (p/"guest-state.bin").write_bytes(EXPECTED_GUEST)
        (p/"mailbox.bin").write_bytes(MAILBOX_SENTINEL)

        (p/"mode7-texture.bin").write_bytes(TEXTURE_SENTINEL)
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_TEXTURE_DMA_NOT_REACHED"

        (p/"mode7-texture.bin").write_bytes(bytes(8))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_TEXTURE_DMA_COMPLETED_HCOMP_NOT_REACHED"

        marker=bytes((0x00,0x51,0,0,0,0,0,0))
        (p/"mailbox.bin").write_bytes(swap32(marker))
        (p/"mode7-texture.bin").write_bytes(bytes(8))
        (p/"guest-state.bin").write_bytes(swap32(EXPECTED_GUEST))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_TEXTURE_DMA_AND_HCOMP_REACHED"

        (p/"mode7-texture.bin").write_bytes(swap32(TEXTURE_SENTINEL))
        r=classify(p)
        assert not r["passed"]

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test()
        print("Mode7 texture-stage classifier self-test: PASS")
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
