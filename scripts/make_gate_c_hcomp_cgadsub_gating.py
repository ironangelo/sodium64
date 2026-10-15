#!/usr/bin/env python3
"""Generate disabled/enabled CGADSUB variants of the validated Main/Sub guest."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from make_gate_c_hcomp_main_sub_lifetime import build_rom

CHECKSUM = slice(0x7FDC, 0x7FE0)
CGADSUB_ENABLED = bytes((0xA9, 0x01, 0x8D, 0x31, 0x21))


def finalize_checksum(rom: bytearray) -> None:
    rom[CHECKSUM] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    rom[0x7FDC:0x7FDE] = (checksum ^ 0xFFFF).to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")


def build_variant(cgadsub: int) -> bytes:
    if cgadsub not in (0, 1):
        raise ValueError("cgadsub must be 0 or 1")

    base = build_rom()
    rom = bytearray(base)
    hits = [i for i in range(len(rom)) if rom.startswith(CGADSUB_ENABLED, i)]
    if len(hits) != 1:
        raise ValueError(f"expected one CGADSUB immediate pattern, found {hits!r}")

    pos = hits[0]
    rom[pos + 1] = cgadsub
    finalize_checksum(rom)

    if cgadsub == 1 and bytes(rom) != base:
        raise ValueError("enabled variant must remain byte-identical to validated guest")

    # Disabled must differ semantically only at the immediate payload after
    # excluding the four checksum/complement bytes.
    if cgadsub == 0:
        diffs = [
            i for i, (a, b) in enumerate(zip(base, rom))
            if a != b and not (CHECKSUM.start <= i < CHECKSUM.stop)
        ]
        if diffs != [pos + 1]:
            raise ValueError(f"unexpected disabled-guest semantic diffs: {diffs!r}")

    return bytes(rom)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", type=Path)
    ap.add_argument("--cgadsub", type=int, choices=(0, 1), required=True)
    args = ap.parse_args()

    data = build_variant(args.cgadsub)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"cgadsub={args.cgadsub}")
    print(f"size={len(data)}")
    print("sha256=" + hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
