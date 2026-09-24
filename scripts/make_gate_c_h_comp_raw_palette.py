#!/usr/bin/env python3
"""Generate the deterministic SNES guest for the H-COMP raw-palette proof."""

from __future__ import annotations

import argparse
from pathlib import Path

ROM_SIZE = 0x8000
HEADER = 0x7FC0


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def emit_lda_sta(program: bytearray, value: int, address: int) -> None:
    program += bytes([0xA9, value & 0xFF, 0x8D, address & 0xFF, address >> 8])


def build_rom() -> bytes:
    rom = bytearray([0xEA]) * ROM_SIZE
    program = bytearray([0x78, 0x18, 0xFB])  # SEI; CLC; XCE

    # INIDISP=7 => Sodium64 coefficient 8. Leave force blank clear.
    emit_lda_sta(program, 0x07, 0x2100)

    # Start at CGRAM index 1. Then write four exact RGB555 colors:
    # 1 red=0x001F, 2 green=0x03E0, 3 blue=0x7C00, 4 white=0x7FFF.
    emit_lda_sta(program, 0x01, 0x2121)
    for lo, hi in ((0x1F, 0x00), (0xE0, 0x03), (0x00, 0x7C), (0xFF, 0x7F)):
        emit_lda_sta(program, lo, 0x2122)
        emit_lda_sta(program, hi, 0x2122)

    program += bytes([0x80, 0xFE])  # BRA -2
    rom[: len(program)] = program

    title = b"S64 RAW PAL PROOF"
    rom[HEADER : HEADER + 21] = title.ljust(21, b" ")
    rom[0x7FD5] = 0x20
    rom[0x7FD6] = 0x00
    rom[0x7FD7] = 0x05
    rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    write_vector(rom, 0x7FE4, 0x9000)
    for offset in (0x7FF4, 0x7FF6, 0x7FF8, 0x7FFA, 0x7FFC, 0x7FFE):
        write_vector(rom, offset, 0x8000)

    rom[0x7FDC:0x7FE0] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    complement = checksum ^ 0xFFFF
    rom[0x7FDC:0x7FDE] = complement.to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")
    return bytes(rom)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = build_rom()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"wrote {len(data)} bytes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
