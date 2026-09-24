#!/usr/bin/env python3
"""Generate a deterministic SNES guest that alternates CGRAM entry 1 each VBlank."""

from __future__ import annotations
import argparse
from pathlib import Path

ROM_SIZE = 0x8000
HEADER = 0x7FC0

def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset:offset+2] = address.to_bytes(2, "little")

class Program:
    def __init__(self) -> None:
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.data += bytes(values)

    def label(self, name: str) -> None:
        self.labels[name] = len(self.data)

    def rel8(self, opcode: int, target: str) -> None:
        self.emit(opcode, 0)
        self.fixups.append((len(self.data) - 1, target))

    def finish(self) -> bytes:
        for pos, target in self.fixups:
            if target not in self.labels:
                raise ValueError(f"unknown label: {target}")
            delta = self.labels[target] - (pos + 1)
            if not -128 <= delta <= 127:
                raise ValueError(f"branch out of range: {target} ({delta})")
            self.data[pos] = delta & 0xFF
        return bytes(self.data)

def lda_imm(p: Program, value: int) -> None:
    p.emit(0xA9, value & 0xFF)

def lda_abs(p: Program, address: int) -> None:
    p.emit(0xAD, address & 0xFF, address >> 8)

def sta_abs(p: Program, address: int) -> None:
    p.emit(0x8D, address & 0xFF, address >> 8)

def write_cgram_byte(p: Program, value: int) -> None:
    lda_imm(p, value)
    sta_abs(p, 0x2122)

def build_rom() -> bytes:
    rom = bytearray([0xEA]) * ROM_SIZE
    p = Program()
    p.emit(0x78, 0xD8)  # SEI; CLD

    # INIDISP=7 => Sodium64 coefficient 8.
    lda_imm(p, 0x07)
    sta_abs(p, 0x2100)

    # phase byte = 0 (red phase)
    lda_imm(p, 0x00)
    p.emit(0x85, 0x00)  # STA $00

    # Initialize entries 1..3: red, blue, white.
    lda_imm(p, 0x01)
    sta_abs(p, 0x2121)
    for lo, hi in ((0x1F, 0x00), (0x00, 0x7C), (0xFF, 0x7F)):
        write_cgram_byte(p, lo)
        write_cgram_byte(p, hi)

    p.label("frame_loop")
    # Wait until outside VBlank, then wait for the next VBlank edge.
    p.label("wait_clear")
    lda_abs(p, 0x4212)
    p.rel8(0x30, "wait_clear")  # BMI while VBlank bit is set
    p.label("wait_set")
    lda_abs(p, 0x4212)
    p.rel8(0x10, "wait_set")    # BPL while VBlank bit is clear

    # Toggle phase once per VBlank.
    p.emit(0xA5, 0x00)          # LDA $00
    p.emit(0x49, 0x01)          # EOR #$01
    p.emit(0x85, 0x00)          # STA $00

    # Rewrite entry 1 only. Entries 2/3 remain fixed completion markers.
    lda_imm(p, 0x01)
    sta_abs(p, 0x2121)
    p.emit(0xA5, 0x00)          # LDA $00
    p.rel8(0xF0, "write_red")   # BEQ red

    # Green = 0x03E0.
    write_cgram_byte(p, 0xE0)
    write_cgram_byte(p, 0x03)
    p.rel8(0x80, "frame_loop")

    p.label("write_red")
    write_cgram_byte(p, 0x1F)
    write_cgram_byte(p, 0x00)
    p.rel8(0x80, "frame_loop")

    program = p.finish()
    rom[:len(program)] = program

    title = b"S64 RAW OWNERSHIP"
    rom[HEADER:HEADER+21] = title.ljust(21, b" ")
    rom[0x7FD5] = 0x20
    rom[0x7FD6] = 0x00
    rom[0x7FD7] = 0x05
    rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    write_vector(rom, 0x7FE4, 0x8000)
    for offset in (0x7FF4, 0x7FF6, 0x7FF8, 0x7FFA, 0x7FFC, 0x7FFE):
        write_vector(rom, offset, 0x8000)

    rom[0x7FDC:0x7FE0] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    complement = checksum ^ 0xFFFF
    rom[0x7FDC:0x7FDE] = complement.to_bytes(2, "little")
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
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
