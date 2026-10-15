#!/usr/bin/env python3
"""Source/binary contract for clean CGADSUB add/subtract/half mode selection."""

from __future__ import annotations

import argparse
from pathlib import Path

from test_gate_c_hcomp_main_sub_exec_clean import insns, prove_binary, section

ROOT = Path(__file__).resolve().parents[1]


def prove_source() -> None:
    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0x5C" not in h:
        raise AssertionError("CGADSUB-mode HCOMP padding drift")

    body = insns(section(h, "hcomp_entry:", "// Mid-frame clean Main provenance helper."))
    required = (
        "lbu t2, CGWSEL",
        "andi t3, t2, 0x2",
        "move t7, t1",
        "lhu t6, SCRN_DATA + 16",
        "srl t4, t6, 11",
        "andi t4, t4, 0x3",
        "lbu t8, CGADSUB",
        "and t2, t8, t4",
        "sltu t2, zero, t2",
        "andi t4, t8, 0x80",
        "bnez t4, hcomp_math_sub",
        "andi t4, t8, 0x40",
        "bnez t4, hcomp_math_add_half",
        "andi t4, t4, 0x8420",
        "or t3, t3, t4",
        "xor t3, t0, t7",
        "andi t4, t3, 0x0421",
        "srl t3, t3, 1",
        "ori t4, zero, 0x8420",
        "andi t4, t4, 0x8420",
        "and t3, t3, t4",
        "andi t5, t8, 0x40",
        "andi t3, t3, 0x7BDE",
        "sh t3, CHAR_DATA + 12",
        "li a1, 0xA00F0008",
        "li a2, 0x17",
    )
    cursor = -1
    for anchor in required:
        try:
            cursor = body.index(anchor, cursor + 1)
        except ValueError as exc:
            raise AssertionError(f"CGADSUB mode sequence missing/reordered {anchor!r}") from exc

    if body.count("lbu t8, CGADSUB") != 1:
        raise AssertionError("CGADSUB operation carrier count drift")
    if "lbu t2, CGADSUB" in body:
        raise AssertionError("old fixed-half gate load survived")

    # Source selector and evidence ABI must remain unchanged.
    for anchor in (
        "lhu t5, SUB_COLOR", "move t7, t1", "bnez t3, hcomp_source_ready",
        "sh t5, CHAR_DATA + 24", "sh t7, CHAR_DATA + 26",
        "sh t2, CHAR_DATA + 28", "sh t3, CHAR_DATA + 30",
    ):
        if anchor not in body:
            raise AssertionError(f"CGWSEL control drift: {anchor}")

    # Validate the exact packed RGB555 formulas against useful edge vectors.
    def add_full(x: int, y: int) -> int:
        s = x + y
        carry = (s - ((x ^ y) & 0x0421)) & 0x8420
        return (s - carry) | (carry - (carry >> 5))

    def add_half(x: int, y: int) -> int:
        return (x + y - ((x ^ y) & 0x0421)) >> 1

    def sub_full(x: int, y: int) -> int:
        d = x - y + 0x8420
        borrow = (d - ((x ^ y) & 0x8420)) & 0x8420
        return (d - borrow) & (borrow - (borrow >> 5))

    def sub_half(x: int, y: int) -> int:
        return (sub_full(x, y) & 0x7BDE) >> 1

    vectors = (
        (0x001F, 0x03E0, (0x03FF, 0x01EF, 0x001F, 0x000F)),
        (0x7FFF, 0x7FFF, (0x7FFF, 0x7FFF, 0x0000, 0x0000)),
        (0x0000, 0x7FFF, (0x7FFF, 0x3DEF, 0x0000, 0x0000)),
    )
    for x, y, expected in vectors:
        got = (add_full(x, y), add_half(x, y), sub_full(x, y), sub_half(x, y))
        if got != expected:
            raise AssertionError(f"packed arithmetic vector drift {x:#x},{y:#x}: {got!r}")


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
    print("HCOMP_CGADSUB_MODES_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("cgadsub_bit7=0_add_1_subtract")
    print("cgadsub_bit6=0_full_1_half")
    print("cgwsel=0x02_live_sub_control")
    print("hcomp_screen_switch=0xA4001760")
    print("draw_mode7_entry=0xA4001788")
    print("resident_imem_growth=0")
    print("transparent_sub_half_suppression=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
