#!/usr/bin/env python3
"""Generate a deterministic Gate-C H-COMP BG main/sub diagnostic SNES ROM.

The original 32 KiB LoROM renders one opaque 2bpp BG1 tile across the screen and
enables BG1 on both main and sub screens. The tile uses a moderate red palette
entry so correct color math has an unambiguous relational oracle:

  phase 0x01: raw / math disabled (CGADSUB=0x00)
  phase 0x02: BG1 ADD main+sub (CGADSUB=0x01)
  phase 0x03: BG1 HALF-ADD main+sub (CGADSUB=0x41)

CGWSEL=0x02 selects the real subscreen BG/OBJ operand. With the same non-zero
BG1 pixel on main and sub, correct SNES semantics require RAW == HALF-ADD while
ADD is brighter. Current Sodium64 source ignores BG1/half color-math bits and
collapses shared main/sub layers, so all three framebuffers are predicted equal.
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
PHASE_MIRROR = 0x7E0001
PHASE_AGE = 0x7E0002
PHASE_RAW = 0x01
PHASE_ADD = 0x02
PHASE_HALF = 0x03
PHASE_FRAMES = 40


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
            raise ValueError(
                f"cannot pad backwards from 0x{len(self.code):X} to 0x{offset:X}"
            )
        while len(self.code) < offset:
            self.emit(value)

    def finish(self) -> bytes:
        for operand_index, label in self.rel8_fixups:
            if label not in self.labels:
                raise ValueError(f"unknown branch label: {label}")
            delta = self.labels[label] - (operand_index + 1)
            if not -128 <= delta <= 127:
                raise ValueError(f"branch to {label} out of rel8 range: {delta}")
            self.code[operand_index] = delta & 0xFF
        return bytes(self.code)


def emit_lda_sta_abs(asm: Assembler, value: int, address: int) -> None:
    asm.emit(0xA9, value, 0x8D, address & 0xFF, (address >> 8) & 0xFF)


def emit_lda_sta_long(asm: Assembler, value: int, address: int) -> None:
    asm.emit(
        0xA9,
        value,
        0x8F,
        address & 0xFF,
        (address >> 8) & 0xFF,
        (address >> 16) & 0xFF,
    )


def emit_lda_long(asm: Assembler, address: int) -> None:
    asm.emit(
        0xAF,
        address & 0xFF,
        (address >> 8) & 0xFF,
        (address >> 16) & 0xFF,
    )


def emit_sta_long(asm: Assembler, address: int) -> None:
    asm.emit(
        0x8F,
        address & 0xFF,
        (address >> 8) & 0xFF,
        (address >> 16) & 0xFF,
    )


def emit_dma_to_vram(
    asm: Assembler,
    *,
    source: int,
    vram_word: int,
    length: int,
) -> None:
    # VMAIN already configured for increment-after-high; channel 0 mode1 streams
    # alternating low/high bytes to $2118/$2119.
    emit_lda_sta_abs(asm, vram_word & 0xFF, 0x2116)
    emit_lda_sta_abs(asm, (vram_word >> 8) & 0xFF, 0x2117)
    emit_lda_sta_abs(asm, 0x01, 0x4300)
    emit_lda_sta_abs(asm, 0x18, 0x4301)
    emit_lda_sta_abs(asm, source & 0xFF, 0x4302)
    emit_lda_sta_abs(asm, (source >> 8) & 0xFF, 0x4303)
    emit_lda_sta_abs(asm, 0x00, 0x4304)
    emit_lda_sta_abs(asm, length & 0xFF, 0x4305)
    emit_lda_sta_abs(asm, (length >> 8) & 0xFF, 0x4306)
    emit_lda_sta_abs(asm, 0x01, 0x420B)


def build_program() -> bytes:
    asm = Assembler()

    # Native mode, 16-bit X/Y, 8-bit accumulator.
    asm.emit(0x78, 0x18, 0xFB, 0xD8)
    asm.emit(0xC2, 0x10)
    asm.emit(0xE2, 0x20)

    emit_lda_sta_abs(asm, 0x80, 0x2100)  # forced blank
    emit_lda_sta_abs(asm, 0x00, 0x2105)  # Mode 0: BG1 is 2bpp
    emit_lda_sta_abs(asm, 0x00, 0x2107)  # BG1SC tilemap at VRAM $0000
    emit_lda_sta_abs(asm, 0x01, 0x210B)  # BG1 tile data at VRAM $1000
    emit_lda_sta_abs(asm, 0x80, 0x2115)  # VMAIN increment after high byte

    emit_dma_to_vram(
        asm,
        source=TILEMAP_ADDRESS,
        vram_word=0x0000,
        length=TILEMAP_SIZE,
    )
    emit_dma_to_vram(
        asm,
        source=TILE_ADDRESS,
        vram_word=0x1000,
        length=16,
    )

    # Palette entry 1 = moderate red (BGR555 0x0008).
    emit_lda_sta_abs(asm, 0x01, 0x2121)
    emit_lda_sta_abs(asm, 0x08, 0x2122)
    emit_lda_sta_abs(asm, 0x00, 0x2122)

    # BG1 is visible on both main and sub screens. CGWSEL bit1 selects the real
    # subscreen BG/OBJ pixel as the color-math operand.
    emit_lda_sta_abs(asm, 0x01, 0x212C)  # TM BG1
    emit_lda_sta_abs(asm, 0x01, 0x212D)  # TS BG1
    emit_lda_sta_abs(asm, 0x02, 0x2130)  # CGWSEL subscreen operand
    emit_lda_sta_abs(asm, 0x00, 0x2131)  # start raw

    emit_lda_sta_long(asm, 0x00, FRAME_COUNTER)
    emit_lda_sta_long(asm, PHASE_RAW, PHASE_MIRROR)
    emit_lda_sta_long(asm, 0x00, PHASE_AGE)

    emit_lda_sta_abs(asm, 0x0F, 0x2100)  # brightness 15
    emit_lda_sta_abs(asm, 0x80, 0x4200)  # NMI enable

    asm.label("main_loop")
    asm.emit(0xCB)  # WAI
    asm.branch(0x80, "main_loop")

    asm.pad_to(NMI_OFFSET)
    asm.label("nmi")
    asm.emit(0x48)  # PHA
    asm.emit(0xAD, 0x10, 0x42)  # acknowledge NMI

    emit_lda_long(asm, FRAME_COUNTER)
    asm.emit(0x1A)
    emit_sta_long(asm, FRAME_COUNTER)

    emit_lda_long(asm, PHASE_AGE)
    asm.emit(0x1A)
    emit_sta_long(asm, PHASE_AGE)
    asm.emit(0xC9, PHASE_FRAMES)
    asm.branch(0xD0, "nmi_done")

    emit_lda_sta_long(asm, 0x00, PHASE_AGE)
    emit_lda_long(asm, PHASE_MIRROR)
    asm.emit(0xC9, PHASE_RAW)
    asm.branch(0xF0, "set_add")
    asm.emit(0xC9, PHASE_ADD)
    asm.branch(0xF0, "set_half")

    asm.label("set_raw")
    emit_lda_sta_long(asm, PHASE_RAW, PHASE_MIRROR)
    emit_lda_sta_abs(asm, 0x00, 0x2131)
    asm.branch(0x80, "nmi_done")

    asm.label("set_add")
    emit_lda_sta_long(asm, PHASE_ADD, PHASE_MIRROR)
    emit_lda_sta_abs(asm, 0x01, 0x2131)
    asm.branch(0x80, "nmi_done")

    asm.label("set_half")
    emit_lda_sta_long(asm, PHASE_HALF, PHASE_MIRROR)
    emit_lda_sta_abs(asm, 0x41, 0x2131)

    asm.label("nmi_done")
    asm.emit(0x68, 0x40)  # PLA; RTI

    program = asm.finish()
    if asm.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved away from fixed vector")
    return program


def build_tilemap() -> bytes:
    # 32x32 entries, all tile 0 / palette 0 / low priority.
    return bytes(TILEMAP_SIZE)


def build_tile() -> bytes:
    # 2bpp tile with every pixel palette index 1: plane0=1s, plane1=0s.
    return bytes([value for _ in range(8) for value in (0xFF, 0x00)])


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    program = build_program()
    tilemap = build_tilemap()
    tile = build_tile()

    tilemap_offset = TILEMAP_ADDRESS - LOAD_ADDRESS
    tile_offset = TILE_ADDRESS - LOAD_ADDRESS
    if len(program) > tilemap_offset:
        raise ValueError("program overlaps tilemap")
    if tilemap_offset + len(tilemap) > tile_offset:
        raise ValueError("tilemap overlaps tile data")
    if tile_offset + len(tile) >= HEADER:
        raise ValueError("tile data overlaps LoROM header")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[: len(program)] = program
    rom[tilemap_offset : tilemap_offset + len(tilemap)] = tilemap
    rom[tile_offset : tile_offset + len(tile)] = tile

    title = b"S64 GATEC HCOMP BG"
    rom[HEADER : HEADER + 21] = title.ljust(21, b" ")
    rom[0x7FD5] = 0x20
    rom[0x7FD6] = 0x00
    rom[0x7FD7] = 0x05
    rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    write_vector(rom, 0x7FEA, NMI_ADDRESS)
    for offset in (0x7FF4, 0x7FF6, 0x7FF8, 0x7FFC, 0x7FFE):
        write_vector(rom, offset, LOAD_ADDRESS)
    write_vector(rom, 0x7FFA, NMI_ADDRESS)

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
