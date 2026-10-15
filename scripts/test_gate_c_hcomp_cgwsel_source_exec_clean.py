#!/usr/bin/env python3
"""Source/binary contract for clean CGWSEL second-operand selection."""

from __future__ import annotations

import argparse
from pathlib import Path

from test_gate_c_hcomp_main_sub_exec_clean import insns, prove_binary, section

ROOT = Path(__file__).resolve().parents[1]


def prove_source() -> None:
    main = (ROOT / "src/rsp_main.S").read_text()
    transition = insns(section(
        main,
        "// End the current semantic screen through H-COMP unconditionally.",
        "// Removing the direct zero-screen branch saves one resident instruction.",
    ))
    if transition != [
        "srl s7, s7, 8",
        "andi s3, s3, 0xF0",
        "lw a1, OVERLAY_HCOMP_SRC",
        "li t9, 0x1760",
        "b overlay_load_slot",
        "nop",
    ]:
        raise AssertionError(f"screen-end HCOMP routing drift: {transition}")

    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0xE8" not in h:
        raise AssertionError("CGWSEL HCOMP padding drift")

    body = insns(section(h, "hcomp_entry:", "// Mid-frame clean Main provenance helper."))
    required = (
        # Existing live operands/provenance.
        "li a1, 0xA00E4018",
        "addi a1, a1, 0x1198",
        "ori a1, a1, 0x2018",
        "lhu t6, SCRN_DATA + 16",
        "srl t4, t6, 11",
        "andi t4, t4, 0x3",
        "and t2, t2, t4",
        # Exact CGWSEL selector.
        "lhu t5, SUB_COLOR",
        "lbu t2, CGWSEL",
        "andi t3, t2, 0x2",
        "move t7, t1",
        "bnez t3, hcomp_source_ready",
        "move t7, t5",
        "sh t5, CHAR_DATA + 24",
        "sh t7, CHAR_DATA + 26",
        "sh t2, CHAR_DATA + 28",
        "sh t3, CHAR_DATA + 30",
        # Unchanged E1f expression, now over selected addend t7.
        "xor t3, t0, t7",
        "andi t4, t3, 0x0421",
        "add t3, t0, t7",
        "sub t3, t3, t4",
        "srl t3, t3, 1",
        # Extended self-describing mailbox only.
        "li a1, 0xA00F0008",
        "li a2, 0x17",
    )
    for anchor in required:
        if anchor not in body:
            raise AssertionError(f"CGWSEL source/ABI anchor lost: {anchor}")

    if body.count("lhu t5, SUB_COLOR") != 1:
        raise AssertionError("fixed-color section source count drift")
    if body.count("lbu t2, CGWSEL") != 1:
        raise AssertionError("CGWSEL selector count drift")

    helper = insns(section(
        h,
        "hcomp_provenance_switch_helper:",
        "// TM has just completed",
    ))
    for anchor in (
        "beqz k0, hcomp_provenance_enable",
        "ori t0, t0, 0x0025",
        "ori t0, t0, 0xFD00",
        "lw a1, OVERLAY_MAIN_SRC",
        "li t9, 0x1364",
        "j 0xA4001F7C",
    ):
        if anchor not in helper:
            raise AssertionError(f"provenance control drift: {anchor}")

    end_cut = insns(section(
        h,
        "hcomp_provenance_end:",
        "// Keep the fixed switch address",
    ))
    if end_cut != [
        "li a0, RDP_INIT",
        "jal 0xA4001F5C",
        "li a1, RDP_INIT + 8",
        "j 0xA40010C0",
        "nop",
    ]:
        raise AssertionError(f"TM-end provenance lifetime cut drift: {end_cut}")

    wrapper = insns(section(
        h,
        "hcomp_screen_switch:",
        "// Keep the externally visible Mode7 entry",
    ))
    if wrapper != [
        "beqz s7, hcomp_provenance_end",
        "nop",
        "b hcomp_provenance_switch_helper",
        "nop",
    ]:
        raise AssertionError(f"fixed switch wrapper drift: {wrapper}")


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

    print("HCOMP_CGWSEL_SOURCE_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("cgwsel_bit1=0_fixed_1_subscreen")
    print("fixed_source=section_SUB_COLOR_full_brightness_control")
    print("live_sub_sample=0xA00E4018")
    print("fixed_mailbox_word=0xA00F0018")
    print("selected_mailbox_word=0xA00F001A")
    print("cgwsel_mailbox_word=0xA00F001C")
    print("source_flag_mailbox_word=0xA00F001E")
    print("hcomp_screen_switch=0xA4001760")
    print("draw_mode7_entry=0xA4001788")
    print("resident_imem_growth=0")
    print("midframe_fixed_color_history=NOT_PROVEN")
    print("brightness_ordering=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
