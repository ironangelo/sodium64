#!/usr/bin/env python3
"""Generate the deterministic active-CGRAM guest for the clean H-COMP E1f proof."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROM_SIZE = 0x8000
HEADER = 0x7FC0
BASE = 0x8000

# These four writes are the only non-zero CGRAM operands. They occur in the
# first active frame after Sodium64 has captured the zero frame base.
OPERANDS = (
    (0, 0x7FFF),
    (1, 0x7FFF),
    (2, 0x001F),
    (3, 0x0020),
)


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset:offset + 2] = address.to_bytes(2, "little")


class Program:
    def __init__(self) -> None:
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.abs_fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.data += bytes(v & 0xFF for v in values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.data)

    def jmp(self, target: str) -> None:
        self.emit(0x4C, 0, 0)
        self.abs_fixups.append((len(self.data) - 2, target))

    def finish(self) -> bytes:
        for pos, target in self.abs_fixups:
            if target not in self.labels:
                raise ValueError(f"unknown label: {target}")
            self.data[pos:pos + 2] = (BASE + self.labels[target]).to_bytes(2, "little")
        return bytes(self.data)


def lda_imm(p: Program, value: int) -> None:
    p.emit(0xA9, value)


def sta_abs(p: Program, address: int) -> None:
    p.emit(0x8D, address & 0xFF, address >> 8)


def set_cgadd(p: Program, index: int) -> None:
    lda_imm(p, index)
    sta_abs(p, 0x2121)


def write_cgram(p: Program, value: int) -> None:
    lda_imm(p, value & 0xFF)
    sta_abs(p, 0x2122)
    lda_imm(p, (value >> 8) & 0x7F)
    sta_abs(p, 0x2122)


def build_rom() -> bytes:
    rom = bytearray([0xEA]) * ROM_SIZE
    p = Program()

    p.emit(0x78, 0xD8)       # SEI; CLD
    p.emit(0xE2, 0x30)       # SEP #$30 (8-bit A/X)

    # Sodium64 startup has already run section_init and emitted the bootstrap
    # fixed-color marker. These writes therefore exercise PR #18's active-frame
    # typed CGRAM history rather than merely appearing in the next frame base.
    for index, value in OPERANDS:
        set_cgadd(p, index)
        write_cgram(p, value)

    p.label("spin")
    p.jmp("spin")

    program = p.finish()
    if len(program) >= 0x400:
        raise ValueError(f"program unexpectedly large: {len(program)}")
    rom[:len(program)] = program

    rom[HEADER:HEADER + 21] = b"S64 HCOMP E1F DYN".ljust(21, b" ")
    rom[0x7FD5] = 0x20
    rom[0x7FD6] = 0x00
    rom[0x7FD7] = 0x05
    rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    write_vector(rom, 0x7FE4, BASE)
    for offset in (0x7FF4, 0x7FF6, 0x7FF8, 0x7FFA, 0x7FFC, 0x7FFE):
        write_vector(rom, offset, BASE)

    rom[0x7FDC:0x7FE0] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    rom[0x7FDC:0x7FDE] = (checksum ^ 0xFFFF).to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")
    return bytes(rom)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    data = build_rom()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"wrote {len(data)} bytes to {args.output}")
    print("sha256=" + hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
