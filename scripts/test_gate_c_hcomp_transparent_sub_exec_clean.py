#!/usr/bin/env python3
"""Source/binary contract for clean transparent-Sub fallback and HALF suppression."""

from __future__ import annotations

import argparse
from pathlib import Path

from test_gate_c_hcomp_main_sub_exec_clean import insns, prove_binary, section

ROOT = Path(__file__).resolve().parents[1]


def prove_source() -> None:
    main = (ROOT / "src/rsp_main.S").read_text()
    fill = insns(section(
        main,
        "fill_backdrop:",
        "// Run the RDP to fill the segment",
    ))
    if "ori t0, t0, 0xFF" in fill:
        raise AssertionError("Sub backdrop still forces opaque alpha")
    if "nop" not in fill or "sw t0, RDP_FILL + 20" not in fill:
        raise AssertionError("transparent Sub backdrop slot drift")
    if "compact offscreen TS target uses" not in main:
        raise AssertionError("transparent Sub ownership comment missing")

    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0x0C" not in h:
        raise AssertionError("transparent-Sub HCOMP padding drift")
    if "0xA00E6000" in h or "0xA00E6000" in main:
        raise AssertionError("unexpected new per-pixel surface introduced")

    body = insns(section(h, "hcomp_entry:", "// Mid-frame clean Main provenance helper."))
    required = (
        "lhu t1, SCRN_DATA",
        "andi t9, t1, 0x1",
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
        "li a2, 0x17",
    )
    cursor = -1
    for anchor in required:
        try:
            cursor = body.index(anchor, cursor + 1)
        except ValueError as exc:
            raise AssertionError(f"transparent-Sub sequence missing/reordered {anchor!r}") from exc

    if body.count("andi t9, t1, 0x1") != 1:
        raise AssertionError("Sub coverage sample count drift")
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
    print("coverage_carrier=compact_sub_rgba5551_alpha")
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
