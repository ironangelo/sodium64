#!/usr/bin/env python3
"""Source/binary contract for clean transparent-Sub fallback and HALF suppression."""

from __future__ import annotations

import argparse
from pathlib import Path

from test_gate_c_hcomp_main_sub_exec_clean import insns, prove_binary, section

ROOT = Path(__file__).resolve().parents[1]


def prove_source() -> None:
    defines = (ROOT / "src/defines.h").read_text()
    if "#define HCOMP_PROOF_RDP_CMDS 0xF30" not in defines:
        raise AssertionError("bounded proof RDP table address drift")
    if "#define HCOMP_PROOF_BG_DEPTH_CMDS (HCOMP_PROOF_RDP_CMDS + 0x18)" not in defines:
        raise AssertionError("BG depth command base drift")

    main = (ROOT / "src/rsp_main.S").read_text()
    fill = insns(section(
        main,
        "fill_backdrop:",
        "// Run the RDP to fill the segment",
    ))
    if "ori t0, t0, 0xFF" not in fill:
        raise AssertionError("rejected alpha0 backdrop experiment was not reverted")
    if "hcomp_proof_rdp_cmds:" not in main:
        raise AssertionError("bounded proof command table missing")
    for cmd in (
        ".dword 0x2F0088FF00040025",
        ".dword 0x3E000000000DFD00",
        ".dword 0x2E00000008000000",
        ".dword 0x2E00000018000000",
        ".dword 0x2E00000028000000",
    ):
        if cmd not in main:
            raise AssertionError(f"bounded proof command missing: {cmd}")

    frame = insns(section(main, "draw_frame:", "next_section:"))
    frame_required = (
        "li a0, RDP_FRAME",
        "jal rdp_send",
        "li a1, RDP_FILL",
        "li a0, HCOMP_PROOF_RDP_CMDS",
        "jal rdp_send",
        "li a1, HCOMP_PROOF_BG_DEPTH_CMDS",
        "li k1, 0",
    )
    cursor = -1
    for anchor in frame_required:
        try:
            cursor = frame.index(anchor, cursor + 1)
        except ValueError as exc:
            raise AssertionError(f"same-frame TS-Z setup missing/reordered {anchor!r}") from exc

    switch = insns(section(main, "next_layer:", "// Fixed renderer overlay begins"))
    if "b overlay_load_slot" not in switch or "li t9, 0x1760" not in switch:
        raise AssertionError("H-COMP switch delay-slot compaction drift")

    draw = insns(section(main, "draw_bg:", "// Check if the BG type or character base changed"))
    for anchor in (
        "sll a0, t3, 3",
        "addi a0, a0, HCOMP_PROOF_BG_DEPTH_CMDS",
        "jal rdp_send",
        "addi a1, a0, 8",
    ):
        if anchor not in draw:
            raise AssertionError(f"static depth selection drift: {anchor}")

    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0x80" not in h:
        raise AssertionError("transparent-Sub HCOMP padding drift")
    if "0xA00E6000" in h or "0xA00E6000" in main:
        raise AssertionError("unexpected new per-pixel surface introduced")

    body = insns(section(h, "hcomp_entry:", "// Mid-frame clean Main provenance helper."))
    required = (
        "lhu t1, SCRN_DATA",
        "lhu t9, CHAR_DATA + 32",
        "li t4, 0x0400",
        "xor t4, t9, t4",
        "sltu t4, zero, t4",
        "sh t4, CHAR_DATA + 34",
        "move t9, t4",
        "lhu t5, SUB_COLOR",
        "lbu t2, CGWSEL",
        "andi t3, t2, 0x2",
        "beqz t3, hcomp_source_fixed",
        "bnez t9, hcomp_source_sub",
        "move t7, t5",
        "li t9, 2",
        "move t7, t1",
        "li t9, 1",
        "move t9, zero",
        "lbu t8, CGADSUB",
        "andi t4, t8, 0x40",
        "beqz t4, hcomp_math_add_full",
        "li t5, 2",
        "beq t9, t5, hcomp_math_add_full",
        "ori t9, t9, 0x0100",
        "beq t9, t4, hcomp_math_done",
        "sh t9, CHAR_DATA + 30",
        "li a1, 0xA00F0008",
        "li a2, 0x1B",
    )
    cursor = -1
    for anchor in required:
        try:
            cursor = body.index(anchor, cursor + 1)
        except ValueError as exc:
            raise AssertionError(f"transparent-Sub sequence missing/reordered {anchor!r}") from exc

    helper = insns(section(
        h,
        "hcomp_provenance_switch_helper:",
        "// TM has just completed",
    ))
    helper_required = (
        "bnez k0, hcomp_sub_presence_saved",
        "li a0, CHAR_DATA + 32",
        "lui a1, 0xA00E",
        "ori a1, a1, 0x2018",
        "jal 0xA4001F40",
        "li a2, 0x7",
        "lw t0, FRAMEBUFFER(sp)",
        "sw t0, RDP_FRAME + 4",
        "jal 0xA4001F5C",
        "lw a1, OVERLAY_MAIN_SRC",
        "li t9, 0x1370",
        "j 0xA4001F7C",
    )
    cursor = -1
    for anchor in helper_required:
        try:
            cursor = helper.index(anchor, cursor + 1)
        except ValueError as exc:
            raise AssertionError(f"TS->TM preservation sequence missing/reordered {anchor!r}") from exc

    if body.count("li t9, 2") != 1:
        raise AssertionError("transparent fallback source code drift")
    if body.count("sh t9, CHAR_DATA + 30") != 1:
        raise AssertionError("source/HALF evidence store drift")

    # Parent semantics that must remain upstream/downstream of the new case.
    for anchor in (
        "lhu t6, SCRN_DATA + 16",
        "srl t4, t6, 11",
        "andi t4, t4, 0x3",
        "and t2, t8, t4",
        "andi t4, t8, 0x80",
        "bnez t4, hcomp_math_sub",
        "andi t4, t4, 0x8420",
        "andi t3, t3, 0x7BDE",
    ):
        if anchor not in body:
            raise AssertionError(f"validated CGADSUB path drift: {anchor}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs=3, type=Path)
    ap.add_argument("--symbols", nargs=3, type=Path)
    args = ap.parse_args()

    prove_source()
    if args.maps or args.symbols:
        if not args.maps or not args.symbols:
            ap.error("--maps and --symbols must be supplied together")
        prove_binary(args.maps, args.symbols)

    print("HCOMP_TRANSPARENT_SUB_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("coverage_carrier=reused_compact_Z16_TS_winner_tag")
    print("source_code_0=direct_fixed")
    print("source_code_1=live_sub")
    print("source_code_2=transparent_sub_fixed_fallback")
    print("source_flags_bit8=half_effective")
    print("new_per_pixel_surface=0")
    print("hcomp_screen_switch=0xA4001760")
    print("draw_mode7_entry=0xA4001788")
    print("resident_imem_growth=0")
    print("windows_clip_prevent=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
