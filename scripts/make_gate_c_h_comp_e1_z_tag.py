#!/usr/bin/env python3
"""Generate the deterministic original SNES guest for Gate-C E1a Z-tag proof.

The 32 KiB LoROM renders BG1 in Mode 0 with one 2bpp checkerboard tile:
palette index 0 is transparent and palette index 1 is opaque black. CGRAM
color 0 is a visible red backdrop. The resulting frame therefore distinguishes
transparent holes from opaque-black texels without any commercial ROM.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROM_SIZE = 0x8000
HEADER = 0x7FC0
LOAD_ADDRESS = 0x8000
NMI_ADDRESS = 0x8200
NMI_OFFSET = NMI_ADDRESS - LOAD_ADDRESS
TILEMAP_ADDRESS = 0x9000
TILE_ADDRESS = 0x9800
TILEMAP_SIZE = 0x800
FRAME_COUNTER = 0x7E0000


class Assembler:
    def __init__(self) -> None:
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.rel8_fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        for value in values:
            if not 0 <= value <= 0xFF:
                raise ValueError(f"byte out of range: {value}")
            self.code.append(value)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.code)

    def branch(self, opcode: int, label: str) -> None:
        self.emit(opcode, 0)
        self.rel8_fixups.append((len(self.code) - 1, label))

    def pad_to(self, offset: int, value: int = 0xEA) -> None:
        if len(self.code) > offset:
            raise ValueError("cannot pad backwards")
        self.code.extend([value] * (offset - len(self.code)))

    def finish(self) -> bytes:
        for operand_index, label in self.rel8_fixups:
            delta = self.labels[label] - (operand_index + 1)
            if not -128 <= delta <= 127:
                raise ValueError(f"branch to {label} out of range: {delta}")
            self.code[operand_index] = delta & 0xFF
        return bytes(self.code)


def lda_sta_abs(a: Assembler, value: int, address: int) -> None:
    a.emit(0xA9, value, 0x8D, address & 0xFF, (address >> 8) & 0xFF)


def lda_sta_long(a: Assembler, value: int, address: int) -> None:
    a.emit(0xA9, value, 0x8F, address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF)


def lda_long(a: Assembler, address: int) -> None:
    a.emit(0xAF, address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF)


def sta_long(a: Assembler, address: int) -> None:
    a.emit(0x8F, address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF)


def dma_to_vram(a: Assembler, *, source: int, vram_word: int, length: int) -> None:
    lda_sta_abs(a, vram_word & 0xFF, 0x2116)
    lda_sta_abs(a, (vram_word >> 8) & 0xFF, 0x2117)
    lda_sta_abs(a, 0x01, 0x4300)
    lda_sta_abs(a, 0x18, 0x4301)
    lda_sta_abs(a, source & 0xFF, 0x4302)
    lda_sta_abs(a, (source >> 8) & 0xFF, 0x4303)
    lda_sta_abs(a, 0x00, 0x4304)
    lda_sta_abs(a, length & 0xFF, 0x4305)
    lda_sta_abs(a, (length >> 8) & 0xFF, 0x4306)
    lda_sta_abs(a, 0x01, 0x420B)


def build_program() -> bytes:
    a = Assembler()
    a.emit(0x78, 0x18, 0xFB, 0xD8)  # SEI; CLC; XCE; CLD
    a.emit(0xC2, 0x10)              # 16-bit X/Y
    a.emit(0xE2, 0x20)              # 8-bit A

    lda_sta_abs(a, 0x80, 0x2100)    # forced blank
    lda_sta_abs(a, 0x00, 0x2105)    # Mode 0
    lda_sta_abs(a, 0x00, 0x2107)    # BG1 tilemap at VRAM $0000
    lda_sta_abs(a, 0x01, 0x210B)    # BG1 tile data at VRAM $1000
    lda_sta_abs(a, 0x80, 0x2115)    # increment VRAM after high byte

    dma_to_vram(a, source=TILEMAP_ADDRESS, vram_word=0x0000, length=TILEMAP_SIZE)
    dma_to_vram(a, source=TILE_ADDRESS, vram_word=0x1000, length=16)

    # CGRAM 0: visible medium red backdrop. CGRAM 1: RGB black, but as a
    # non-zero palette index Sodium64 converts it to RGBA5551 alpha=1.
    lda_sta_abs(a, 0x00, 0x2121)
    lda_sta_abs(a, 0x10, 0x2122)    # color 0 low: BGR555 0x0010
    lda_sta_abs(a, 0x00, 0x2122)    # color 0 high
    lda_sta_abs(a, 0x00, 0x2122)    # color 1 low: black
    lda_sta_abs(a, 0x00, 0x2122)    # color 1 high

    lda_sta_abs(a, 0x01, 0x212C)    # TM: BG1 on main
    lda_sta_abs(a, 0x00, 0x212D)    # TS: no subscreen layers
    lda_sta_abs(a, 0x00, 0x2130)    # CGWSEL
    lda_sta_abs(a, 0x00, 0x2131)    # CGADSUB
    lda_sta_abs(a, 0x00, 0x2133)    # 224-line mode / centered 8px border

    lda_sta_long(a, 0x00, FRAME_COUNTER)
    lda_sta_abs(a, 0x0F, 0x2100)    # full brightness, display on
    lda_sta_abs(a, 0x80, 0x4200)    # NMI enable

    a.label("main_loop")
    a.emit(0xCB)                     # WAI
    a.branch(0x80, "main_loop")

    a.pad_to(NMI_OFFSET)
    a.label("nmi")
    a.emit(0x48)                     # PHA
    a.emit(0xAD, 0x10, 0x42)        # acknowledge NMI
    lda_long(a, FRAME_COUNTER)
    a.emit(0x1A)                     # INC A
    sta_long(a, FRAME_COUNTER)
    a.emit(0x68, 0x40)              # PLA; RTI

    program = a.finish()
    if a.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved")
    return program


def build_tilemap() -> bytes:
    return bytes(TILEMAP_SIZE)       # all entries tile 0


def build_tile() -> bytes:
    # 2bpp checkerboard. Plane 0 alternates bits; plane 1 stays zero.
    rows = []
    for y in range(8):
        rows.extend((0xAA if (y & 1) == 0 else 0x55, 0x00))
    return bytes(rows)


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset:offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    program = build_program()
    tilemap = build_tilemap()
    tile = build_tile()
    tilemap_offset = TILEMAP_ADDRESS - LOAD_ADDRESS
    tile_offset = TILE_ADDRESS - LOAD_ADDRESS

    if len(program) > tilemap_offset:
        raise ValueError("program overlaps tilemap")
    if tilemap_offset + len(tilemap) > tile_offset:
        raise ValueError("tilemap overlaps tile")
    if tile_offset + len(tile) >= HEADER:
        raise ValueError("tile overlaps header")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[:len(program)] = program
    rom[tilemap_offset:tilemap_offset + len(tilemap)] = tilemap
    rom[tile_offset:tile_offset + len(tile)] = tile

    rom[HEADER:HEADER + 21] = b"S64 E1 Z TAG".ljust(21, b" ")
    rom[0x7FD5] = 0x20               # LoROM
    rom[0x7FD6] = 0x00
    rom[0x7FD7] = 0x05
    rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    write_vector(rom, 0x7FEA, NMI_ADDRESS)
    write_vector(rom, 0x7FFA, NMI_ADDRESS)
    for offset in (0x7FF4, 0x7FF6, 0x7FF8, 0x7FFC, 0x7FFE):
        write_vector(rom, offset, LOAD_ADDRESS)

    rom[0x7FDC:0x7FE0] = bytes(4)
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    complement = checksum ^ 0xFFFF
    rom[0x7FDC:0x7FDE] = complement.to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")
    return bytes(rom)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = build_rom()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rom)
    print(f"wrote {len(rom)} bytes to {args.output}")
    print(f"sha256={hashlib.sha256(rom).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
