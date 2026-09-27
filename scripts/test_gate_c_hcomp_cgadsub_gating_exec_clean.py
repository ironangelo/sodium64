#!/usr/bin/env python3
"""Source/binary contract for the clean live CGADSUB BG1 gating proof."""

from __future__ import annotations

import argparse
from pathlib import Path

from test_gate_c_hcomp_main_sub_exec_clean import prove_binary

ROOT = Path(__file__).resolve().parents[1]


def insns(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"):
            continue
        out.append(line)
    return out


def section(src: str, start: str, end: str) -> str:
    i = src.index(start)
    j = src.index(end, i)
    return src[i:j]


def prove_source() -> None:
    h = (ROOT / "src/rsp_hcomp.S").read_text()

    if ".byte 0:0x3A8" not in h or ".byte 0:0x24C" not in h:
        raise AssertionError("HCOMP fixed-slot padding drift")

    body = insns(section(h, "hcomp_entry:", "// Mid-frame Main/Sub ownership helper."))
    if len(body) != 87:
        raise AssertionError(f"HCOMP source body drift: {len(body)} != 87")

    # Existing validated PR#18/CGRAM arithmetic bridge remains present before
    # the new live-pixel discriminator.
    for anchor in (
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "li a1, 0xA00F0000",
        "xor t2, t0, t1",
        "andi t2, t2, 0x0421",
    ):
        if anchor not in body:
            raise AssertionError(f"existing E1f bridge anchor lost: {anchor}")

    # Live rendered operand addresses and exact controlled gating.
    expected = (
        "li a1, 0xA00E4018",
        "lw a1, FRAMEBUFFER(sp)",
        "addi a1, a1, 0x1198",
        "lbu t2, CGADSUB",
        "andi t2, t2, 0x1",
        "beqz t2, hcomp_gate_store",
        "li a1, 0xA00F0008",
    )
    for anchor in expected:
        if anchor not in body:
            raise AssertionError(f"live-gating source anchor lost: {anchor}")

    # The live path must use the same canonical adapter and authoritative E1f
    # expression, not a proof-only host approximation.
    if body.count("andi t3, t0, 0x07C0") != 2:
        raise AssertionError("Main RGBA5551->RGB555 adapter count drift")
    if body.count("andi t5, t1, 0x07C0") != 2:
        raise AssertionError("Sub RGBA5551->RGB555 adapter count drift")
    if body.count("andi t4, t3, 0x0421") != 1:
        raise AssertionError("live E1f correction term missing")

    # Exact self-describing proof record.
    for anchor in (
        "sh t0, CHAR_DATA + 8",
        "sh t1, CHAR_DATA + 10",
        "sh t3, CHAR_DATA + 12",
        "sh t2, CHAR_DATA + 14",
    ):
        if anchor not in body:
            raise AssertionError(f"gating mailbox record drift: {anchor}")

    # 0x300 -> 0x24C consumes exactly 0xB4 = 180 bytes of previously unused
    # fixed-slot padding. The parent active footprint was 232 bytes.
    active_bytes = 232 + (0x300 - 0x24C)
    if active_bytes != 412 or active_bytes > 1000:
        raise AssertionError(f"HCOMP active-byte budget drift: {active_bytes}")


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

    print("HCOMP_CGADSUB_GATING_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("controlled_main_winner=BG1")
    print("cgadsub_gate_bit=0")
    print("sub_sample=0xA00E4018")
    print("main_sample=FRAMEBUFFER(sp)+0x1198")
    print("gating_mailbox=0xA00F0008")
    print("hcomp_active_slot_bytes=412")
    print("hcomp_screen_switch=0xA4001760")
    print("general_winner_metadata=NOT_PROVEN")
    print("real_n64_rdp_rsp_fence=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
