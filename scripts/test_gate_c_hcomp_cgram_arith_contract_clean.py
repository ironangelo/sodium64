#!/usr/bin/env python3
"""L0 contract for the clean PR#18 CGRAM -> H-COMP arithmetic bridge.

Host-only: this branch intentionally changes no Sodium64 runtime source.

The smallest next discriminator combines three already-established facts without
importing the cumulative experimental compositor:
  * PR #18 replays historical CGRAM into an aligned RGBA5551 raw shadow.
  * the clean third-overlay proof can provide a zero-resident-growth H-COMP slot.
  * E1f established exact raw-RGB555 half-add semantics.

The planned executable child will read two operand pairs from the handed raw
shadow, losslessly decode RGBA5551 back to canonical SNES RGB555, apply the E1f
packed half-add identity, publish only an 8-byte proof mailbox, then toggle the
RSP queue slot and halt. It is a bridge proof, not a production compositor.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

SLOT_START = 0x13A8
HCOMP_ENTRY = 0x13B0
MODE7_ENTRY = 0x1788
SLOT_END = 0x1790
SLOT_BYTES = SLOT_END - SLOT_START

PROPOSED_MODE7_SRC = 0xE8C
PROPOSED_MAIN_SRC = 0xE90
PROPOSED_HCOMP_SRC = 0xE94
RAW_PTRS = 0xE98
EVENT_CURSOR = 0xEA0
PAIR_SCRATCH = 0xEA8
WRITE_SCRATCH = 0xEB0
VEC_DATA = 0xF70

# Exact resident suffix addresses measured by the already-validated clean
# executable third-overlay proof. The proposed resident edits are equal-length.
DMA_WRITE = 0xA4001F08
DMA_READ = 0xA4001F40
DRAW_FRAME = 0xA400103C
PROOF_MAILBOX = 0xA00F0000

# Two planned dynamic pairs. Pair 0 rejects the obsolete saturate-then-half
# oracle; pair 1 rejects a naive packed (a+b)>>1 that leaks carries across
# RGB555 channel boundaries.
DYNAMIC_PAIRS = (
    (0x7FFF, 0x7FFF, 0x7FFF),
    (0x001F, 0x0020, 0x000F),
)

# Planned fixed-slot body. Labels/comments are excluded deliberately: every
# string below is one RSP instruction and therefore four bytes.
BRIDGE_INSTRUCTIONS = (
    "li a0, SCRN_DATA",
    "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
    f"jal 0x{DMA_READ:08X}",
    "li a2, 0x1F",
    "li s0, SCRN_DATA",
    "li s1, CHAR_DATA",
    "li s2, 2",
    "sw zero, 4(s1)",
    # pair loop
    "lhu t0, 0(s0)",
    "lhu t1, 8(s0)",
    # RGBA5551 -> RGB555, operand A
    "srl t2, t0, 11",
    "andi t3, t0, 0x07C0",
    "srl t3, t3, 1",
    "or t2, t2, t3",
    "andi t3, t0, 0x003E",
    "sll t3, t3, 9",
    "or t0, t2, t3",
    # RGBA5551 -> RGB555, operand B
    "srl t4, t1, 11",
    "andi t5, t1, 0x07C0",
    "srl t5, t5, 1",
    "or t4, t4, t5",
    "andi t5, t1, 0x003E",
    "sll t5, t5, 9",
    "or t1, t4, t5",
    # authoritative E1f packed half-add
    "xor t2, t0, t1",
    "andi t2, t2, 0x0421",
    "add t3, t0, t1",
    "sub t3, t3, t2",
    "srl t3, t3, 1",
    "sh t3, 0(s1)",
    "addi s0, s0, 16",
    "addi s1, s1, 2",
    "addi s2, s2, -1",
    "bnez s2, hcomp_pair_loop",
    "nop",
    # proof-only publication
    "li a0, CHAR_DATA",
    f"li a1, 0x{PROOF_MAILBOX:08X}",
    f"jal 0x{DMA_WRITE:08X}",
    "li a2, 0x7",
    # Preserve current-slot ownership through arithmetic; toggle only at halt.
    "xori sp, sp, 4",
    "li t0, 0x2",
    "mtc0 t0, COP0_SP_STATUS",
    f"j 0x{DRAW_FRAME:08X}",
    "nop",
)

FAULT_INSTRUCTIONS = 4  # draw_bg fault + draw_mode7 fault, two each.


def literal_define(text: str, name: str) -> int:
    m = re.search(rf"^#define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\s*$", text, re.M)
    if not m:
        raise AssertionError(f"missing literal define {name}")
    return int(m.group(1), 16)


def rgb555_to_rgba5551(value: int) -> int:
    value &= 0x7FFF
    return (
        ((value & 0x001F) << 11)
        | ((value & 0x03E0) << 1)
        | ((value & 0x7C00) >> 9)
        | 1
    )


def rgba5551_to_rgb555(value: int) -> int:
    return (
        ((value >> 11) & 0x1F)
        | ((value & 0x07C0) >> 1)
        | ((value & 0x003E) << 9)
    )


def e1f_half_add(a: int, b: int) -> int:
    a &= 0x7FFF
    b &= 0x7FFF
    return (a + b - ((a ^ b) & 0x0421)) >> 1


def channel_reference(a: int, b: int) -> int:
    out = 0
    for shift in (0, 5, 10):
        out |= ((((a >> shift) & 31) + ((b >> shift) & 31)) >> 1) << shift
    return out


def obsolete_saturate_then_half(a: int, b: int) -> int:
    out = 0
    for shift in (0, 5, 10):
        c = min(((a >> shift) & 31) + ((b >> shift) & 31), 31) >> 1
        out |= c << shift
    return out


def prove_representation_boundary() -> None:
    # PR #18's N64 packing is a pure bit permutation plus constant alpha.
    for rgb in range(0x8000):
        packed = rgb555_to_rgba5551(rgb)
        if not (packed & 1):
            raise AssertionError(f"alpha lost for 0x{rgb:04X}")
        got = rgba5551_to_rgb555(packed)
        if got != rgb:
            raise AssertionError(f"roundtrip 0x{rgb:04X} -> 0x{packed:04X} -> 0x{got:04X}")

    # Decode path must discard alpha rather than treating it as SNES blue data.
    if rgba5551_to_rgb555(0x0001) != 0:
        raise AssertionError("alpha leaked into RGB555")


def prove_e1f_semantics() -> None:
    # Exhaust each independent 5-bit channel pair against the reference.
    for shift in (0, 5, 10):
        for a in range(32):
            for b in range(32):
                x = a << shift
                y = b << shift
                got = e1f_half_add(x, y)
                want = channel_reference(x, y)
                if got != want:
                    raise AssertionError((shift, a, b, got, want))

    # Cross-channel and high-sum discriminator points.
    for a, b, want in (
        *DYNAMIC_PAIRS,
        (0x4210, 0x2108, 0x318C),
        (0x2AAA, 0x7FFF, 0x5354),
    ):
        got = e1f_half_add(a, b)
        ref = channel_reference(a, b)
        if got != want or got != ref:
            raise AssertionError(
                f"E1f discriminator 0x{a:04X}+0x{b:04X}: got 0x{got:04X}, "
                f"want/ref 0x{want:04X}/0x{ref:04X}"
            )

    # This is the precise semantic reason the old bridge oracle is superseded.
    if obsolete_saturate_then_half(0x7FFF, 0x7FFF) == e1f_half_add(0x7FFF, 0x7FFF):
        raise AssertionError("obsolete saturating half-add was not discriminated")


def prove_integrated_pr18_contract() -> None:
    defs = (ROOT / "src/defines.h").read_text()
    ppu = (ROOT / "src/ppu.S").read_text()
    rsp = (ROOT / "src/rsp_main.S").read_text()

    expected = {
        "OVERLAY_MAIN_SRC": 0xE90,
        "OVERLAY_MODE7_SRC": 0xE94,
        "HCOMP_RAW_PALETTE_PTRS": RAW_PTRS,
        "HCOMP_CGRAM_EVENT_CURSOR": EVENT_CURSOR,
        "HCOMP_CGRAM_PAIR_SCRATCH": PAIR_SCRATCH,
        "HCOMP_CGRAM_WRITE_SCRATCH": WRITE_SCRATCH,
        "VEC_DATA": VEC_DATA,
    }
    for name, want in expected.items():
        got = literal_define(defs, name)
        if got != want:
            raise AssertionError(f"current master {name}=0x{got:X}, expected 0x{want:X}")

    # Frame base keeps canonical RGB555 while the aligned shadow is RGBA5551.
    for anchor in (
        "hcomp_cgram_base_queues:",
        "hcomp_raw_pal_queues:",
        "andi t3, t3, 0x7FFF",
        "sh t3, 0(t1)",
        "ori t6, t6, 0x1",
        "sw t6, 0(t5)",
        "sw t6, 4(t5)",
    ):
        if anchor not in ppu:
            raise AssertionError(f"PR18 base representation anchor drift: {anchor!r}")

    # Active CGDATA records carry RGBA5551 + destination offset, not a second
    # canonical RGB555 sideband.
    cg = ppu[ppu.index("write_cgdata:"):ppu.index(".align 5\nwrite_w12sel:")]
    for anchor in (
        "ori t3, t3, 0x1",
        "sll t3, t3, 16",
        "sll t4, t0, 2",
        "or t3, t3, t4",
        "sw t3, 0(t4)",
    ):
        if anchor not in cg:
            raise AssertionError(f"typed CGDATA encoding drift: {anchor!r}")
    if "hcomp_cgram_sideband_ptr" in cg:
        raise AssertionError("CGDATA unexpectedly gained a canonical RGB555 sideband writer")

    if ppu.count("hcomp_cgram_sideband_ptr") != 2:
        raise AssertionError("sideband pointer lifecycle changed; re-audit representation contract")

    # Integrated RSP replay consumes high16 payload and materializes 8-byte
    # duplicated RGBA5551 entries in the raw shadow.
    tail = rsp[rsp.index("hcomp_cgram_pair_ready:"):]
    for anchor in (
        "srl t7, t8, 16",
        "sll t0, t7, 16",
        "or t7, t7, t0",
        "sw t7, HCOMP_CGRAM_WRITE_SCRATCH",
        "sw t7, HCOMP_CGRAM_WRITE_SCRATCH + 4",
        "andi t0, t8, 0x7F8",
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "jal dma_write",
        "li a2, 0x7",
    ):
        if anchor not in tail:
            raise AssertionError(f"PR18 replay anchor drift: {anchor!r}")


def prove_clean_overlay_and_slot_ownership() -> None:
    # Reuse the already-validated current-lineage pointer packing; do not grow
    # resident IMEM or overlap PR #18 scratch.
    if not (
        PROPOSED_MODE7_SRC + 4 == PROPOSED_MAIN_SRC
        and PROPOSED_MAIN_SRC + 4 == PROPOSED_HCOMP_SRC
        and PROPOSED_HCOMP_SRC + 4 == RAW_PTRS
        and RAW_PTRS + 8 == EVENT_CURSOR
        and EVENT_CURSOR < PAIR_SCRATCH < WRITE_SCRATCH < VEC_DATA
    ):
        raise AssertionError("clean third-overlay packing overlaps PR18 state")

    if SLOT_BYTES != 1000 or HCOMP_ENTRY != SLOT_START + 8 or MODE7_ENTRY != SLOT_END - 8:
        raise AssertionError("fixed renderer slot ABI drift")

    active_instructions = len(BRIDGE_INSTRUCTIONS) + FAULT_INSTRUCTIONS
    active_bytes = active_instructions * 4
    if len(BRIDGE_INSTRUCTIONS) != 44:
        raise AssertionError(f"planned bridge instruction count drift: {len(BRIDGE_INSTRUCTIONS)}")
    if active_bytes != 192 or active_bytes > SLOT_BYTES:
        raise AssertionError(f"planned active payload {active_bytes}B does not match 192B contract")

    # Queue slot is still the just-rendered frame while arithmetic runs.
    # Unlike the coexistence-only proof, the resident frame-end delay slot must
    # NOT toggle sp before H-COMP reads HCOMP_RAW_PALETTE_PTRS(sp). The overlay
    # performs xori sp,sp,4 only after publishing the proof result, immediately
    # before HALT. This preserves CPU/RSP ping-pong semantics with no resident
    # instruction growth.
    current = (ROOT / "src/rsp_main.S").read_text()
    nf = current[current.index("next_frame:"):current.index("\n\nclear_cache:")]
    if "xori sp, sp, 4" not in nf:
        raise AssertionError("current queue-toggle contract drift")

    proposed_next_frame = (
        "lw a1, OVERLAY_HCOMP_SRC",
        "li t9, 0x13B0",
        "b overlay_load_slot",
        "nop",
    )
    if len(proposed_next_frame) != 4:
        raise AssertionError("proposed frame-end resident footprint grew")
    if BRIDGE_INSTRUCTIONS[-5:] != (
        "xori sp, sp, 4",
        "li t0, 0x2",
        "mtc0 t0, COP0_SP_STATUS",
        f"j 0x{DRAW_FRAME:08X}",
        "nop",
    ):
        raise AssertionError("planned queue toggle/HALT ordering drift")


def main() -> int:
    prove_representation_boundary()
    prove_e1f_semantics()
    prove_integrated_pr18_contract()
    prove_clean_overlay_and_slot_ownership()

    print("HCOMP_CGRAM_ARITH_CLEAN_L0_VALIDATED")
    print("runtime_delta=0")
    print("bridge_input=current_slot_PR18_RGBA5551_shadow")
    print("adapter=lossless_RGBA5551_to_RGB555_exhaustive_32768")
    print("arithmetic=E1f_exact_half_add")
    print("dynamic_pair0=7FFF+7FFF->7FFF")
    print("dynamic_pair1=001F+0020->000F")
    print("planned_active_slot_bytes=192")
    print("resident_imem_growth_proposed=0")
    print("queue_toggle=after_arithmetic_before_HALT")
    print("main_sub_provenance=NOT_PROVEN")
    print("color_math_gating=NOT_PROVEN")
    print("final_pixels=NOT_PROVEN")
    print("production_completeness=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
