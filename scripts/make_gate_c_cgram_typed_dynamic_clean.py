#!/usr/bin/env python3
"""Generate an original LoROM for dynamic DMA8 CGRAM producer validation."""

from __future__ import annotations
import argparse
from pathlib import Path

ROM_SIZE = 0x8000
HEADER = 0x7FC0
BASE = 0x8000


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset:offset + 2] = address.to_bytes(2, "little")


class Program:
    def __init__(self) -> None:
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.rel_fixups: list[tuple[int, str]] = []
        self.abs_fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.data += bytes(v & 0xFF for v in values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.data)

    def rel8(self, opcode: int, target: str) -> None:
        self.emit(opcode, 0)
        self.rel_fixups.append((len(self.data) - 1, target))

    def jmp(self, target: str) -> None:
        self.emit(0x4C, 0, 0)
        self.abs_fixups.append((len(self.data) - 2, target))

    def finish(self) -> bytes:
        for pos, target in self.rel_fixups:
            if target not in self.labels:
                raise ValueError(f"unknown label: {target}")
            delta = self.labels[target] - (pos + 1)
            if not -128 <= delta <= 127:
                raise ValueError(f"branch out of range: {target} ({delta})")
            self.data[pos] = delta & 0xFF
        for pos, target in self.abs_fixups:
            if target not in self.labels:
                raise ValueError(f"unknown label: {target}")
            address = BASE + self.labels[target]
            self.data[pos:pos + 2] = address.to_bytes(2, "little")
        return bytes(self.data)


def lda_imm(p: Program, value: int) -> None:
    p.emit(0xA9, value)


def lda_abs(p: Program, address: int) -> None:
    p.emit(0xAD, address & 0xFF, address >> 8)


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


def write_coldata(p: Program, value: int) -> None:
    lda_imm(p, value)
    sta_abs(p, 0x2132)


def write_phase_a(p: Program) -> None:
    # Base A: e0=red, e1=green, e2=blue; fixed RGB=3.
    set_cgadd(p, 0)
    for value in (0x001F, 0x03E0, 0x7C00):
        write_cgram(p, value)
    write_coldata(p, 0xE3)


def write_phase_b(p: Program) -> None:
    # Base B: e0=green, e1=red, e2=white; fixed RGB=5.
    set_cgadd(p, 0)
    for value in (0x03E0, 0x001F, 0x7FFF):
        write_cgram(p, value)
    write_coldata(p, 0xE5)


def write_active_events(p: Program) -> None:
    # Four exact commits. Repeated index1 and entry0 are deliberate.
    for index, value in ((1, 0x1234), (1, 0x4567), (0, 0x2AAA), (2, 0x7FFF)):
        set_cgadd(p, index)
        write_cgram(p, value)
    # Raw fixed color becomes RGB=7 after the active writes.
    write_coldata(p, 0xE7)


def build_rom() -> bytes:
    rom = bytearray([0xEA]) * ROM_SIZE
    p = Program()

    p.emit(0x78, 0xD8)       # SEI; CLD
    p.emit(0xE2, 0x30)       # SEP #$30 (8-bit A/X)
    p.emit(0x64, 0x00)       # STZ $00 phase
    lda_imm(p, 0x0F)         # display on, full brightness
    sta_abs(p, 0x2100)

    p.label("frame_loop")
    # Normalize to an outside-VBlank observation before waiting for the edge.
    p.label("wait_clear")
    lda_abs(p, 0x4212)
    p.rel8(0x30, "wait_clear")  # BMI while VBlank is set

    p.label("wait_set")
    lda_abs(p, 0x4212)
    p.rel8(0x10, "wait_set")    # BPL while VBlank is clear

    # Toggle a WRAM phase byte once per VBlank.
    p.emit(0xA5, 0x00)       # LDA $00
    p.emit(0x49, 0x01)       # EOR #$01
    p.emit(0x85, 0x00)       # STA $00
    p.rel8(0xF0, "phase_a")   # BEQ phase A

    write_phase_b(p)
    p.jmp("after_vblank")

    p.label("phase_a")
    write_phase_a(p)

    p.label("after_vblank")
    # Wait for vblank_end; the producer snapshots the phase base there.
    p.label("wait_active")
    lda_abs(p, 0x4212)
    p.rel8(0x30, "wait_active")

    write_active_events(p)
    p.jmp("frame_loop")

    program = p.finish()
    if len(program) >= 0x700:
        raise ValueError(f"program unexpectedly large: {len(program)}")
    rom[:len(program)] = program

    title = b"S64 CGRAM EPOCH DYN"
    rom[HEADER:HEADER + 21] = title.ljust(21, b" ")
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
