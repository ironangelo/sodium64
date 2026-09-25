#!/usr/bin/env python3
"""L0 contract for the first CGRAM-history -> H-COMP arithmetic bridge.

This is intentionally host-only.  It proves a diagnostic architecture that can
exercise the already validated DMA8 historical-CGRAM replay and the already
hardware-validated E4d ADD+half arithmetic without growing resident IMEM.

The proposed runtime experiment is deliberately NOT the production compositor:
for a Mode-1-only deterministic guest, temporarily use the existing Mode7
renderer slot as a diagnostic arithmetic overlay.  The probe reads raw palette
entries 0..3 from the currently handed queue, applies the E4d vector ADD+half
core lane-wise, writes its 16-byte result into proof-only raw entries 4..5,
restores the regular renderer overlay, and resumes the section.

No runtime source is changed by this contract.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

FIXED_SLOT_START = 0x13A8
FIXED_SLOT_END = 0x1790
FIXED_SLOT_BYTES = FIXED_SLOT_END - FIXED_SLOT_START

# Consumer scratch occupies EA0..EB7.  The old E4d carry vectors at EA0/EB0
# are therefore no longer stable operands.  F10..F6F is existing padding
# before fixed VEC_DATA=F70, so the proof experiment can replace 32 bytes of
# that padding with private copies without changing DMEM size or VEC_DATA.
BRIDGE_CARRYLO = 0xF10
BRIDGE_CARRYHI = 0xF20
VEC_DATA = 0xF70
CONSUMER_SCRATCH_END = 0xEB8

# The proof overlay uses the exact arithmetic instruction sequence from the
# hardware-validated E4d color path, but only for one 8-lane vector.
# 40 instructions in the probe + 2-instruction slot-entry trampoline.
PROBE_INSTRUCTIONS = (
    "li a0, SCRN_DATA",
    "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
    "jal dma_read",
    "li a2, 0xF",
    "li a0, CHAR_DATA",
    "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
    "addi a1, a1, 0x10",
    "jal dma_read",
    "li a2, 0xF",
    "li t9, hcomp_bridge_carrylo",
    "lqv v17, carrylo",
    "lqv v18, carryhi",
    "li t9, hcomp_vec_half",
    "lqv v19, half",
    "lqv v20, alpha-one",
    "li t0, SCRN_DATA",
    "li t1, CHAR_DATA",
    "lqv v00, main",
    "lqv v01, sub",
    "vmudl v00, v00, v24[8]",
    "vmudl v01, v01, v24[8]",
    "vxor v03, v00, v01",
    "vand v03, v03, v17",
    "vaddc v04, v00, v01",
    "vsubc v05, v04, v03",
    "vand v05, v05, v18",
    "vsubc v04, v04, v05",
    "vmudl v06, v05, v24[12]",
    "vsubc v05, v05, v06",
    "vor v04, v04, v05",
    "vand v04, v04, v19",
    "vor v04, v04, v20",
    "sqv v04, SCRN_DATA",
    "li a0, SCRN_DATA",
    "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
    "addi a1, a1, 0x20",
    "jal dma_write",
    "li a2, 0xF",
    "b overlay_load_main",
    "nop",
)
ENTRY_TRAMPOLINE_INSTRUCTIONS = 2

# Existing first-handoff dynamic authority.
INPUT_RGB555 = {
    0: 0x2AAA,
    1: 0x4567,
    2: 0x7FFF,
    3: 0x1357,
}


def rgb555_to_rgba5551(value: int) -> int:
    value &= 0x7FFF
    return (
        ((value & 0x001F) << 11)
        | ((value & 0x03E0) << 1)
        | ((value & 0x7C00) >> 9)
        | 1
    )


def half_add_rgb555(a: int, b: int) -> int:
    """SNES ADD+half semantic target, component-wise and saturation-first."""
    out = 0
    for shift in (0, 5, 10):
        ca = (a >> shift) & 0x1F
        cb = (b >> shift) & 0x1F
        c = min(ca + cb, 0x1F) >> 1
        out |= c << shift
    return out


def prove_semantics() -> dict[str, int]:
    # Exhaust every possible component pair.  RGB channels are independent.
    for a in range(32):
        for b in range(32):
            want = min(a + b, 31) >> 1
            packed = half_add_rgb555(a, b) & 0x1F
            if packed != want:
                raise AssertionError((a, b, packed, want))

    # Pin the semantic model to the real-N64 E4d authority colors:
    # half(red) -> 0x7801, half(blue) -> 0x001F,
    # half(red + green) -> 0x7BC1.
    red = 0x001F
    green = 0x03E0
    blue = 0x7C00
    if rgb555_to_rgba5551(half_add_rgb555(red, 0)) != 0x7801:
        raise AssertionError("E4d red authority point drift")
    if rgb555_to_rgba5551(half_add_rgb555(blue, 0)) != 0x001F:
        raise AssertionError("E4d blue authority point drift")
    if rgb555_to_rgba5551(half_add_rgb555(red, green)) != 0x7BC1:
        raise AssertionError("E4d yellow authority point drift")

    # The diagnostic loads raw entries0/1 as lanes0..3/4..7 and entries2/3
    # as the corresponding second operands.  Because each raw entry is four
    # identical halfwords, the 16-byte output becomes entry4 + entry5.
    out4 = rgb555_to_rgba5551(
        half_add_rgb555(INPUT_RGB555[0], INPUT_RGB555[2])
    )
    out5 = rgb555_to_rgba5551(
        half_add_rgb555(INPUT_RGB555[1], INPUT_RGB555[3])
    )
    if out4 != 0x7BDF or out5 != 0x7BD5:
        raise AssertionError(
            f"bridge discriminator drift: got 0x{out4:04X}/0x{out5:04X}"
        )
    return {"entry4": out4, "entry5": out5}


def define_value(text: str, name: str) -> int:
    m = re.search(rf"^#define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\s*$", text, re.M)
    if not m:
        raise AssertionError(f"missing literal define {name}")
    return int(m.group(1), 16)


def prove_current_runtime_contract(path: Path) -> None:
    src = path.read_text()
    name = path.name

    for anchor in (
        "b hcomp_cgram_consume\n    move k0, k1",
        "hcomp_cgram_pair_ready:",
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "jal dma_write\n    li a2, 0x7",
        "hcomp_cgram_marker:",
        "b hcomp_cgram_return\n    lbu k1, SPLIT_LINE",
        "overlay_load_mode7:",
        "lw a1, OVERLAY_MODE7_SRC",
        "li a0, 0x13A8",
        "li a2, 0x3E7",
        "overlay_load_main:",
        "lw a1, OVERLAY_MAIN_SRC",
        "b draw_bg",
    ):
        if anchor not in src:
            raise AssertionError(f"{name}: runtime anchor drift: {anchor!r}")

    # Current E4d vector constants still occupy EA0..F0F in the DMEM image,
    # but consumer scratch overwrites EA0..EB7 at runtime.  Half/alpha remain
    # stable at EC0/ED0 and F10..F6F remains explicit padding.
    for anchor in (
        "hcomp_vec_carrylo:",
        "hcomp_vec_carryhi:",
        "hcomp_vec_half:",
        "hcomp_vec_one:",
        "hcomp_vec_shr11:",
        ".byte 0:0x60",
        "vec_data:",
    ):
        if anchor not in src:
            raise AssertionError(f"{name}: DMEM layout anchor drift: {anchor!r}")

    if "hcomp_vector_band_probe:" in src:
        raise AssertionError(f"{name}: retired unsafe scaffold unexpectedly returned")


def prove_layout_contract() -> None:
    defs = (ROOT / "src/defines.h").read_text()
    if define_value(defs, "HCOMP_CGRAM_EVENT_CURSOR") != 0xEA0:
        raise AssertionError("event cursor moved")
    if define_value(defs, "HCOMP_CGRAM_PAIR_SCRATCH") != 0xEA8:
        raise AssertionError("pair scratch moved")
    if define_value(defs, "HCOMP_CGRAM_WRITE_SCRATCH") != 0xEB0:
        raise AssertionError("write scratch moved")
    if define_value(defs, "HCOMP_RAW_PALETTE_PTRS") != 0xE98:
        raise AssertionError("raw palette pointer ABI moved")
    if define_value(defs, "VEC_DATA") != VEC_DATA:
        raise AssertionError("VEC_DATA moved")

    if not (CONSUMER_SCRATCH_END <= BRIDGE_CARRYLO < BRIDGE_CARRYHI < VEC_DATA):
        raise AssertionError("bridge constants do not live after consumer scratch")
    if BRIDGE_CARRYLO + 0x10 > BRIDGE_CARRYHI:
        raise AssertionError("carry vectors overlap")
    if BRIDGE_CARRYHI + 0x10 > VEC_DATA:
        raise AssertionError("carry vectors escape F10..F6F padding")

    probe_bytes = (len(PROBE_INSTRUCTIONS) + ENTRY_TRAMPOLINE_INSTRUCTIONS) * 4
    if probe_bytes != 168:
        raise AssertionError(f"planned probe size drift: {probe_bytes}")
    if probe_bytes > FIXED_SLOT_BYTES:
        raise AssertionError("diagnostic arithmetic probe no longer fits renderer slot")

    # This experiment must consume overlay capacity only: no resident IMEM growth.
    if FIXED_SLOT_BYTES != 0x3E8:
        raise AssertionError("fixed renderer slot size drift")


def main() -> int:
    prove_layout_contract()
    prove_current_runtime_contract(ROOT / "src/rsp_main.S")
    prove_current_runtime_contract(ROOT / "src/rsp_mode7.S")
    result = prove_semantics()
    print(
        "CGRAM_HCOMP_BRIDGE_CONTRACT_VALIDATED "
        f"slot={FIXED_SLOT_BYTES}B probe=168B "
        f"entry4=0x{result['entry4']:04X} entry5=0x{result['entry5']:04X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
