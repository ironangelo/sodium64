#!/usr/bin/env python3
"""Generate the deterministic original SNES guest for Gate-C E2b target switching.

The 32 KiB LoROM renders a controlled Mode-0 shared-layer baseline: BG1 is
fully opaque red and enabled on both main and sub screens. BG2 remains loaded
but disabled from both screen masks. A harmless direct-HDMA WH0 stream changes
only after the first
8 visible lines; windows are disabled, so the write exists solely to force the
already-validated urgent section boundary used by the E2b carrier.
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
BG1_TILEMAP_ADDRESS = 0x9000
BG2_TILEMAP_ADDRESS = 0x9800
BG1_TILE_ADDRESS = 0xA000
BG2_TILE_ADDRESS = 0xA020
HDMA_WINDOW_TABLE_ADDRESS = 0xB000
TILEMAP_SIZE = 0x800
VISIBLE_LINES = 224
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


def build_hdma_window_table() -> bytes:
    # Reuse the proven direct-HDMA form from H-SAMPLE: bit 7 set means one
    # source byte is transferred on every line in the block.
    values = bytes([0x00] * 8 + [0x01] * (VISIBLE_LINES - 8))
    table = bytearray()
    offset = 0
    while offset < len(values):
        count = min(127, len(values) - offset)
        table.append(0x80 | count)
        table.extend(values[offset:offset + count])
        offset += count
    table.append(0)
    return bytes(table)


def build_program() -> bytes:
    a = Assembler()
    a.emit(0x78, 0x18, 0xFB, 0xD8)  # SEI; CLC; XCE; CLD
    a.emit(0xC2, 0x10)              # 16-bit X/Y
    a.emit(0xE2, 0x20)              # 8-bit A

    lda_sta_abs(a, 0x80, 0x2100)    # forced blank
    lda_sta_abs(a, 0x00, 0x2105)    # Mode 0
    lda_sta_abs(a, 0x00, 0x2107)    # BG1 tilemap at VRAM $0000
    lda_sta_abs(a, 0x08, 0x2108)    # BG2 tilemap at VRAM $0800 (word address)
    lda_sta_abs(a, 0x21, 0x210B)    # BG1 chars $1000, BG2 chars $2000
    lda_sta_abs(a, 0x80, 0x2115)    # increment VRAM after high byte

    dma_to_vram(a, source=BG1_TILEMAP_ADDRESS, vram_word=0x0000, length=TILEMAP_SIZE)
    dma_to_vram(a, source=BG2_TILEMAP_ADDRESS, vram_word=0x0800, length=TILEMAP_SIZE)
    dma_to_vram(a, source=BG1_TILE_ADDRESS, vram_word=0x1000, length=32)
    dma_to_vram(a, source=BG2_TILE_ADDRESS, vram_word=0x2000, length=32)

    # CGRAM 0: black backdrop. CGRAM 1: full red for opaque BG1.
    # CGRAM 2: full green for opaque BG2.
    lda_sta_abs(a, 0x00, 0x2121)
    lda_sta_abs(a, 0x00, 0x2122)    # color 0 low: black
    lda_sta_abs(a, 0x00, 0x2122)    # color 0 high
    lda_sta_abs(a, 0x1F, 0x2122)    # color 1 low: red BGR555 0x001F
    lda_sta_abs(a, 0x00, 0x2122)    # color 1 high
    lda_sta_abs(a, 0xE0, 0x2122)    # color 2 low: green BGR555 0x03E0
    lda_sta_abs(a, 0x03, 0x2122)    # color 2 high

    lda_sta_abs(a, 0x01, 0x212C)    # TM: BG1 shared
    lda_sta_abs(a, 0x01, 0x212D)    # TS: BG1 shared
    lda_sta_abs(a, 0x00, 0x212E)    # TMW disabled
    lda_sta_abs(a, 0x00, 0x212F)    # TSW disabled
    lda_sta_abs(a, 0x00, 0x2130)    # CGWSEL
    lda_sta_abs(a, 0x00, 0x2131)    # CGADSUB
    lda_sta_abs(a, 0x00, 0x2133)    # 224-line mode / centered 8px border

    # Harmless WH0 HDMA creates one urgent section boundary after the first
    # 8 visible lines. Window enables remain zero, so WH0 cannot mask pixels.
    lda_sta_abs(a, 0x00, 0x2126)
    lda_sta_abs(a, 0x00, 0x4300)    # direct HDMA, mode 0
    lda_sta_abs(a, 0x26, 0x4301)    # WH0
    lda_sta_abs(a, HDMA_WINDOW_TABLE_ADDRESS & 0xFF, 0x4302)
    lda_sta_abs(a, (HDMA_WINDOW_TABLE_ADDRESS >> 8) & 0xFF, 0x4303)
    lda_sta_abs(a, 0x00, 0x4304)    # bank 00
    lda_sta_abs(a, 0x01, 0x420C)    # enable HDMA channel 0

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
    lda_sta_abs(a, 0x00, 0x2126)    # restore WH0 before next frame section_init
    lda_long(a, FRAME_COUNTER)
    a.emit(0x1A)                     # INC A
    sta_long(a, FRAME_COUNTER)
    a.emit(0x68, 0x40)              # PLA; RTI

    program = a.finish()
    if a.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved")
    return program


def build_tilemap() -> bytes:
    # Alternate character IDs 0/1. A 32-tile row has even width, so every row
    # starts at tile 0 and no horizontally adjacent entries are identical.
    return b"".join(
        (index & 1).to_bytes(2, "little")
        for index in range(TILEMAP_SIZE // 2)
    )


def build_bg1_tile() -> bytes:
    # 2bpp solid palette index 1: plane 0 set, plane 1 clear.
    return bytes((0xFF, 0x00) * 8)


def build_bg2_tile() -> bytes:
    # 2bpp solid palette index 2: plane 0 clear, plane 1 set.
    return bytes((0x00, 0xFF) * 8)


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset:offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    program = build_program()
    tilemap = build_tilemap()
    bg1_tiles = build_bg1_tile() * 2
    bg2_tiles = build_bg2_tile() * 2
    hdma_table = build_hdma_window_table()
    bg1_map_offset = BG1_TILEMAP_ADDRESS - LOAD_ADDRESS
    bg2_map_offset = BG2_TILEMAP_ADDRESS - LOAD_ADDRESS
    bg1_tile_offset = BG1_TILE_ADDRESS - LOAD_ADDRESS
    bg2_tile_offset = BG2_TILE_ADDRESS - LOAD_ADDRESS
    hdma_table_offset = HDMA_WINDOW_TABLE_ADDRESS - LOAD_ADDRESS

    if len(program) > bg1_map_offset:
        raise ValueError("program overlaps BG1 tilemap")
    if bg1_map_offset + len(tilemap) > bg2_map_offset:
        raise ValueError("BG1 tilemap overlaps BG2 tilemap")
    if bg2_map_offset + len(tilemap) > bg1_tile_offset:
        raise ValueError("BG2 tilemap overlaps BG1 tiles")
    if bg1_tile_offset + len(bg1_tiles) > bg2_tile_offset:
        raise ValueError("BG1 tiles overlap BG2 tiles")
    if bg2_tile_offset + len(bg2_tiles) > hdma_table_offset:
        raise ValueError("BG2 tiles overlap HDMA table")
    if hdma_table_offset + len(hdma_table) >= HEADER:
        raise ValueError("HDMA table overlaps header")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[:len(program)] = program
    rom[bg1_map_offset:bg1_map_offset + len(tilemap)] = tilemap
    rom[bg2_map_offset:bg2_map_offset + len(tilemap)] = tilemap
    rom[bg1_tile_offset:bg1_tile_offset + len(bg1_tiles)] = bg1_tiles
    rom[bg2_tile_offset:bg2_tile_offset + len(bg2_tiles)] = bg2_tiles
    rom[hdma_table_offset:hdma_table_offset + len(hdma_table)] = hdma_table

    rom[HEADER:HEADER + 21] = b"S64 E2C SHARED".ljust(21, b" ")
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
