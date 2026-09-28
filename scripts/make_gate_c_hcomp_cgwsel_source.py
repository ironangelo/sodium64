#!/usr/bin/env python3
"""Generate clean CGWSEL fixed-vs-Sub second-operand discriminator guests."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from make_gate_c_hcomp_main_sub_lifetime import build_rom

CHECKSUM = slice(0x7FDC, 0x7FE0)
CGWSEL_SETUP = bytes((0xA9, 0x00, 0x8D, 0x30, 0x21))
HOOK_OFFSET = 0x01F0
HOOK_ADDRESS = 0x81F0
NMI_OFFSET = 0x0200


def hits(data: bytes | bytearray, pattern: bytes) -> list[int]:
    return [i for i in range(len(data)) if data.startswith(pattern, i)]


def finalize_checksum(rom: bytearray) -> None:
    rom[CHECKSUM] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    rom[0x7FDC:0x7FDE] = (checksum ^ 0xFFFF).to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")


def build_variant(cgwsel: int) -> bytes:
    if cgwsel not in (0x00, 0x02):
        raise ValueError("cgwsel must be 0x00(fixed) or 0x02(subscreen)")

    base = build_rom()
    rom = bytearray(base)

    setup_hits = hits(base, CGWSEL_SETUP)
    if len(setup_hits) != 1:
        raise ValueError(f"expected one CGWSEL setup, found {setup_hits!r}")
    setup = setup_hits[0]

    # Preserve every following startup/NMI address. Replace the original 5-B
    # CGWSEL write with a same-size call + two NOPs, then use eleven bytes of
    # already-unused padding immediately before the frozen NMI at $8200.
    if bytes(base[HOOK_OFFSET:NMI_OFFSET]) != bytes((0xEA,)) * (NMI_OFFSET - HOOK_OFFSET):
        raise ValueError("proof hook padding is not untouched NOP space")
    rom[setup:setup + 5] = bytes((0x20, HOOK_ADDRESS & 0xFF, HOOK_ADDRESS >> 8, 0xEA, 0xEA))

    # LDA #CGWSEL ; STA $2130 ; LDA #$9F ; STA $2132 ; RTS
    # $9F updates only fixed-color blue to intensity31, yielding RGB555 0x7C00.
    hook = bytes((
        0xA9, cgwsel, 0x8D, 0x30, 0x21,
        0xA9, 0x9F,    0x8D, 0x32, 0x21,
        0x60,
    ))
    rom[HOOK_OFFSET:HOOK_OFFSET + len(hook)] = hook
    finalize_checksum(rom)

    allowed = {
        *range(setup, setup + 5),
        *range(HOOK_OFFSET, HOOK_OFFSET + len(hook)),
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
    ap.add_argument("--cgwsel", type=lambda x: int(x, 0), choices=(0, 2), required=True)
    args = ap.parse_args()

    data = build_variant(args.cgwsel)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"cgwsel=0x{args.cgwsel:02X}")
    print("fixed_rgb555=0x7C00")
    print(f"size={len(data)}")
    print("sha256=" + hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
