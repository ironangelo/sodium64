#!/usr/bin/env python3
"""Source/binary contract for clean Main BG provenance over live H-COMP gating."""

from __future__ import annotations

import argparse
from pathlib import Path

from test_gate_c_hcomp_main_sub_exec_clean import insns, prove_binary, section

ROOT = Path(__file__).resolve().parents[1]


def prove_source() -> None:
    main = (ROOT / "src/rsp_main.S").read_text()

    params = insns(section(
        main,
        "// Set parameters based on the BG type. LAYER_CHART already stores",
        "// Clean Main provenance proof:",
    ))
    if params != [
        "andi t9, t0, 0xC",
        "srl s4, t9, 2",
        "addi s4, s4, 3",
    ]:
        raise AssertionError(f"BG parameter compaction drift: {params}")

    dispatch = insns(section(
        main,
        "// Clean Main provenance proof:",
        "// Check if the BG type or character base changed",
    ))
    if dispatch != [
        "sll a0, t3, 3",
        "addi a0, a0, RDP_FRAME + 8",
        "jal rdp_send",
        "addi a1, a0, 8",
    ]:
        raise AssertionError(f"winner-depth dispatch drift: {dispatch}")

    row_base = insns(section(
        main,
        "// Get the base screen address for the BG. t3 is still the real BG index:",
        "// Apply the vertical base offset if past the bounds of the first screen",
    ))
    if row_base[:2] != [
        "lbu t2, BGXSC(t3)",
        "li a0, SCRN_DATA",
    ]:
        raise AssertionError(f"t3-preserving row setup drift: {row_base[:3]}")
    if "srl t3, s2, 1" in row_base:
        raise AssertionError("redundant BG-index recovery returned")

    win = insns(section(main, "bg_windows:", "next_segment:"))
    if win != [
        "jal calc_bg_window_spans",
        "li t8, 0",
        "lbu t0, WIN_COUNT",
        "beqz t0, finish_row",
        "nop",
    ]:
        raise AssertionError(f"size-neutral window scheduling drift: {win}")

    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0x148" not in h:
        raise AssertionError("HCOMP provenance padding drift")

    entry = insns(section(h, "hcomp_entry:", "// Mid-frame clean Main provenance helper."))
    for anchor in (
        "lui a1, 0xA00E",
        "ori a1, a1, 0x2018",
        "lhu t6, SCRN_DATA + 16",
        "srl t4, t6, 11",
        "andi t4, t4, 0x3",
        "and t2, t2, t4",
        "sh t6, CHAR_DATA + 16",
        "sh t4, CHAR_DATA + 18",
        "li a2, 0xF",
        "ori t5, t5, 0x0001",
        "lui t5, 0x3D10",
        "lui t5, 0x3300",
    ):
        if anchor not in entry:
            raise AssertionError(f"HCOMP entry provenance/restore anchor lost: {anchor}")

    helper = insns(section(
        h,
        "hcomp_provenance_switch_helper:",
        "// Keep the fixed switch address",
    ))
    required = (
        "sw t0, RDP_FRAME + 4",
        "beqz k0, hcomp_provenance_enable",
        "ori t0, t0, 0x0001",
        "ori t0, t0, 0x0025",
        "lui t0, 0x3E00",
        "ori t0, t0, 0xFD00",
        "lui t0, 0x2E00",
        "lui t1, 0x1800",
        "sw t0, RDP_FRAME + 16",
        "lui t1, 0x2800",
        "lw a1, OVERLAY_MAIN_SRC",
        "li t9, 0x1364",
        "j 0xA4001F7C",
    )
    for anchor in required:
        if anchor not in helper:
            raise AssertionError(f"HCOMP switch-helper anchor lost: {anchor}")

    wrapper = insns(section(
        h,
        "hcomp_screen_switch:",
        "// Keep the externally visible Mode7 entry",
    ))
    if wrapper != [
        "b hcomp_provenance_switch_helper",
        "nop",
    ]:
        raise AssertionError(f"fixed provenance switch wrapper drift: {wrapper}")


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

    print("HCOMP_MAIN_PROVENANCE_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("main_winner_transport=primitive_z")
    print("winner_bg1_stored_z=0x0C00")
    print("winner_bg2_stored_z=0x1400")
    print("winner_mask_rule=stored_z>>11")
    print("provenance_logical_base=0xA00E2000")
    print("provenance_sample=0xA00E2018")
    print("set_z_image_base=0x000DFD00")
    print("provenance_lifetime=section0_only")
    print("draw_bg=0xA40013A8")
    print("hcomp_screen_switch=0xA4001760")
    print("draw_mode7_entry=0xA4001788")
    print("resident_imem_growth=0")
    print("semantic_provenance=NOT_YET_REVALIDATED_AFTER_BOUNDS_REPAIR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
