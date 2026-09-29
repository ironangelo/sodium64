#!/usr/bin/env python3
"""Loaded-slot, carrier and decision contract for bounded color-window repair."""
from __future__ import annotations
import argparse
from pathlib import Path
from test_gate_c_hcomp_main_sub_exec_clean import insns, section, prove_binary, syms
from test_gate_c_hcomp_transparent_sub_exec_clean import prove_carriers
ROOT = Path(__file__).resolve().parents[1]


def prove_source() -> None:
    prove_carriers()
    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0x3A8" not in h or ".byte 0:0x04" not in h:
        raise AssertionError("owned overlay geometry drift")
    if "0xA00E6000" in h:
        raise AssertionError("new pixel surface")
    # The resident helper must be identical in both possible retained suffixes.
    helpers = [insns(section((ROOT / "src" / name).read_text(),
                            "calc_window_spans:", "multiply:"))
               for name in ("rsp_main.S", "rsp_mode7.S")]
    if helpers[0] != helpers[1]:
        raise AssertionError("regular/Mode7 resident helper differs")
    for op in helpers[0]:
        dest = op.split()[1].rstrip(',') if len(op.split()) > 1 else ''
        if dest in ('s0', 's1', 't9'):
            raise AssertionError("resident helper widens preserved-register contract")
    body = insns(section(h, "hcomp_entry:", "// Mid-frame clean Main provenance helper."))
    ordered = (
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)", "xor t2, t0, t1",
        "andi t2, t2, 0x0421", "li a1, 0xA00F0000",
        "lbu a0, WOBJSEL", "srl a0, a0, 4", "lbu a1, WOBJLOG",
        "andi a1, a1, 3", "jal 0xA4001CE4", "li a2, 1",
        "lbu s0, WIN_COUNT", "sltiu t0, t0, 1", "li t0, 0x35",
        "srl t2, t1, 4", "andi s1, s1, 1", "srl t1, t1, 6",
        "andi s0, s0, 1", "sh t0, CHAR_DATA + 38",
        "li a1, 0xA00E4018", "lhu t9, CHAR_DATA + 32",
        "li t4, 0x0400", "sh t4, CHAR_DATA + 34",
        "lbu t2, CGWSEL", "bnez t9, hcomp_source_ready", "li t9, 2",
        "sh t7, CHAR_DATA + 26", "lhu t6, SCRN_DATA + 16",
        "sh t4, CHAR_DATA + 18", "sh t0, CHAR_DATA + 36",
        "bnez s0, hcomp_main_ready", "move t0, zero",
        "and t2, t8, t4", "and t2, t2, s1",
        "beqz t2, hcomp_gate_store", "move t3, t0",
        "sltiu t4, t9, 2", "and t5, t5, s0", "or t9, t9, t5",
        "bnez t4, hcomp_math_sub", "andi t4, t9, 0x100",
        "andi t5, t9, 0x100", "andi t3, t3, 0x7BDE",
        "sh t0, CHAR_DATA + 8", "sh t2, CHAR_DATA + 14",
        "sh t9, CHAR_DATA + 30", "li a2, 0x1F",
        "xori sp, sp, 4", "j 0xA400103C",
    )
    cursor = -1
    for op in ordered:
        try: cursor = body.index(op, cursor + 1)
        except ValueError as exc: raise AssertionError(f"decision sequence drift: {op}") from exc
    # Guard against writes to retained decisions before effective HALF use.
    protected = body[body.index("sh t0, CHAR_DATA + 38") + 1:body.index("and t5, t5, s0")]
    if any(op.split()[0] in ('li', 'move', 'lbu', 'lhu', 'lw', 'andi', 'or', 'and', 'srl', 'sll', 'srlv', 'add', 'addi') and op.split()[1].rstrip(',') in ('s0', 's1') for op in protected if len(op.split()) > 1):
        raise AssertionError("window decisions clobbered across operand loading")
    # No layer-mask dependency: windows affect Main visibility and math alone.
    if any('TMW' in op or 'TSW' in op for op in body):
        raise AssertionError("color window incorrectly depends on layer masks")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs=3, type=Path)
    ap.add_argument("--symbols", nargs=3, type=Path)
    args = ap.parse_args(); prove_source()
    if args.maps or args.symbols:
        if not args.maps or not args.symbols: ap.error("maps and symbols required together")
        prove_binary(args.maps, args.symbols)
        for path in args.symbols[:2]:
            if syms(path).get("calc_window_spans") != 0xA4001CE4:
                raise AssertionError("retained helper entry drift")
    print("HCOMP_COLOR_WINDOW_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("scope=semantic_x0_sample_only")
    print("resident_imem_growth=0")
    print("new_per_pixel_surface=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
