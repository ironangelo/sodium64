#!/usr/bin/env python3
"""Generate the four clean BG1/BG2 winner x CGADSUB-bit provenance guests."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from make_gate_c_hcomp_main_sub_lifetime import (
    HDMA_TS_TABLE_ADDRESS,
    LOAD_ADDRESS,
    build_rom,
)

CHECKSUM = slice(0x7FDC, 0x7FE0)
TM_BG1 = bytes((0xA9, 0x01, 0x8D, 0x2C, 0x21))
TS_BG2 = bytes((0xA9, 0x02, 0x8D, 0x2D, 0x21))
CGAD_BG1 = bytes((0xA9, 0x01, 0x8D, 0x31, 0x21))
HDMA_OFFSET = HDMA_TS_TABLE_ADDRESS - LOAD_ADDRESS


def hits(data: bytes | bytearray, pattern: bytes) -> list[int]:
    return [
        i for i in range(len(data))
        if data.startswith(pattern, i)
    ]


def finalize_checksum(rom: bytearray) -> None:
    rom[CHECKSUM] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    rom[0x7FDC:0x7FDE] = (checksum ^ 0xFFFF).to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")


def build_variant(*, winner: int, cgadsub: int) -> bytes:
    if winner not in (1, 2):
        raise ValueError("winner must be BG1(1) or BG2(2)")
    if cgadsub not in (1, 2):
        raise ValueError("cgadsub must select BG1(1) or BG2(2)")

    base = build_rom()
    rom = bytearray(base)

    tm_hits = hits(base, TM_BG1)
    ts_hits = hits(base, TS_BG2)
    cg_hits = hits(base, CGAD_BG1)
    if len(tm_hits) != 1:
        raise ValueError(f"expected one TM=BG1 setup, found {tm_hits!r}")
    if len(ts_hits) != 2:
        raise ValueError(f"expected initial+NMI TS=BG2 setup, found {ts_hits!r}")
    if len(cg_hits) != 1:
        raise ValueError(f"expected one CGADSUB=BG1 setup, found {cg_hits!r}")

    main_mask = winner
    sub_mask = 2 if winner == 1 else 1

    rom[tm_hits[0] + 1] = main_mask
    for p in ts_hits:
        rom[p + 1] = sub_mask
    rom[cg_hits[0] + 1] = cgadsub

    # build_hdma_ts_table starts with one repeat-every-line block. Its first
    # eight payload bytes are the initial Sub mask; remaining visible lines
    # are zero. Keep timing/table structure byte-identical.
    if rom[HDMA_OFFSET] != 0xFF:
        raise ValueError(f"unexpected first HDMA block header {rom[HDMA_OFFSET]:#x}")
    if bytes(rom[HDMA_OFFSET + 1:HDMA_OFFSET + 9]) != bytes((0x02,)) * 8:
        raise ValueError("unexpected base HDMA first-eight TS payload")
    rom[HDMA_OFFSET + 1:HDMA_OFFSET + 9] = bytes((sub_mask,)) * 8

    finalize_checksum(rom)

    # Freeze the baseline identity and the exact semantic edit surface.
    if winner == 1 and cgadsub == 1 and bytes(rom) != base:
        raise ValueError("BG1/BG1 baseline must remain byte-identical")

    allowed = {
        tm_hits[0] + 1,
        *(p + 1 for p in ts_hits),
        cg_hits[0] + 1,
        *range(HDMA_OFFSET + 1, HDMA_OFFSET + 9),
    }
    diffs = {
        i for i, (a, b) in enumerate(zip(base, rom))
        if a != b and not (CHECKSUM.start <= i < CHECKSUM.stop)
    }
    if not diffs <= allowed:
        raise ValueError(f"unexpected semantic guest diffs: {sorted(diffs - allowed)!r}")

    return bytes(rom)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", type=Path)
    ap.add_argument("--winner", type=int, choices=(1, 2), required=True)
    ap.add_argument("--cgadsub", type=int, choices=(1, 2), required=True)
    args = ap.parse_args()

    data = build_variant(winner=args.winner, cgadsub=args.cgadsub)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"winner=BG{args.winner}")
    print(f"cgadsub=0x{args.cgadsub:02X}")
    print(f"size={len(data)}")
    print("sha256=" + hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
