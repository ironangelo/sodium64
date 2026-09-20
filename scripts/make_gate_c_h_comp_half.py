#!/usr/bin/env python3
"""Generate original Gate-C H-COMP full-add vs half-add diagnostic SNES ROM.

No commercial data is used. The display is deliberately flat so one variable is
isolated: CGADSUB bit 6 (half color math).

Mode 1 setup:
- BG2 only on main screen, solid RGB5 (16, 0, 0).
- BG1 only on sub screen, solid RGB5 (0, 16, 0).
- CGWSEL=$02 selects the subscreen as the second color-math operand.
- No OBJ, windows, HDMA, or visible raster IRQ changes.

Two 120-frame phases differ only in CGADSUB:
- control   $02: add BG2 + subscreen at full intensity => RGB5 (16,16,0)
- treatment $42: same addition with half bit           => RGB5 (8,8,0)

WRAM $7E0001 mirrors the active CGADSUB phase for debugger synchronization.
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

TILE_ADDRESS = 0x9000
BG1_MAP_ADDRESS = 0x9040
BG2_MAP_ADDRESS = 0x9840
PALETTE_ADDRESS = 0xA040

CONTROL_CGADSUB = 0x02
TREATMENT_CGADSUB = 0x42
PHASE_FRAMES = 120

MAIN_RGB5 = (16, 0, 0)
SUB_RGB5 = (0, 16, 0)
CONTROL_RGB5 = (16, 16, 0)
TREATMENT_RGB5 = (8, 8, 0)


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
        self.code.extend(bytes([value]) * (offset - len(self.code)))

    def finish(self) -> bytes:
        for operand_index, label in self.rel8_fixups:
            if label not in self.labels:
                raise ValueError(f"unknown branch label: {label}")
            delta = self.labels[label] - (operand_index + 1)
            if not -128 <= delta <= 127:
                raise ValueError(f"branch to {label} out of range: {delta}")
            self.code[operand_index] = delta & 0xFF
        return bytes(self.code)


def emit_lda_sta_abs(asm: Assembler, value: int, address: int) -> None:
    asm.emit(0xA9, value, 0x8D, address & 0xFF, (address >> 8) & 0xFF)


def emit_vmadd(asm: Assembler, word_address: int) -> None:
    emit_lda_sta_abs(asm, word_address & 0xFF, 0x2116)
    emit_lda_sta_abs(asm, (word_address >> 8) & 0xFF, 0x2117)


def emit_dma_from_rom(
    asm: Assembler, *, channel: int, mode: int, bbus: int, source: int, size: int
) -> None:
    base = 0x4300 + channel * 0x10
    for value, address in (
        (mode, base + 0),
        (bbus, base + 1),
        (source & 0xFF, base + 2),
        ((source >> 8) & 0xFF, base + 3),
        (0x00, base + 4),
        (size & 0xFF, base + 5),
        ((size >> 8) & 0xFF, base + 6),
        (1 << channel, 0x420B),
    ):
        emit_lda_sta_abs(asm, value, address)


def rgb5_word(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return r | (g << 5) | (b << 10)


def build_program() -> bytes:
    asm = Assembler()
    asm.emit(0x78, 0x18, 0xFB, 0xD8)  # SEI; CLC; XCE; CLD
    asm.emit(0xC2, 0x10)              # REP #$10 (X/Y 16-bit)
    asm.emit(0xE2, 0x20)              # SEP #$20 (A 8-bit)

    for value, address in (
        (0x80, 0x2100),  # forced blank
        (0x01, 0x2105),  # Mode 1
        (0x04, 0x2107),  # BG1 map VRAM word $0800
        (0x08, 0x2108),  # BG2 map VRAM word $1000
        (0x32, 0x210B),  # BG1 chars $2000; BG2 chars $3000
        (0x80, 0x2115),  # VRAM increment after high byte
    ):
        emit_lda_sta_abs(asm, value, address)

    # Identical opaque color-index-1 tile for BG1 and BG2.
    for word_address in (0x2000, 0x3000):
        emit_vmadd(asm, word_address)
        emit_dma_from_rom(
            asm, channel=0, mode=1, bbus=0x18, source=TILE_ADDRESS, size=0x20
        )

    emit_vmadd(asm, 0x0800)
    emit_dma_from_rom(
        asm, channel=0, mode=1, bbus=0x18, source=BG1_MAP_ADDRESS, size=0x800
    )
    emit_vmadd(asm, 0x1000)
    emit_dma_from_rom(
        asm, channel=0, mode=1, bbus=0x18, source=BG2_MAP_ADDRESS, size=0x800
    )

    emit_lda_sta_abs(asm, 0x00, 0x2121)
    emit_dma_from_rom(
        asm, channel=0, mode=0, bbus=0x22, source=PALETTE_ADDRESS, size=0x200
    )

    for value, address in (
        (0x00, 0x2123),  # no BG windows
        (0x00, 0x2124),
        (0x00, 0x2125),
        (0x02, 0x212C),  # TM: BG2 main only
        (0x01, 0x212D),  # TS: BG1 sub only
        (0x00, 0x212E),  # TMW disabled
        (0x00, 0x212F),  # TSW disabled
        (0x02, 0x2130),  # CGWSEL: use subscreen operand
        (CONTROL_CGADSUB, 0x2131),
    ):
        emit_lda_sta_abs(asm, value, address)

    # Debugger-visible frame counter + phase mirror.
    asm.emit(0xA9, 0x00, 0x8F, 0x00, 0x00, 0x7E)
    asm.emit(0xA9, CONTROL_CGADSUB, 0x8F, 0x01, 0x00, 0x7E)

    emit_lda_sta_abs(asm, 0x0F, 0x2100)
    emit_lda_sta_abs(asm, 0x80, 0x4200)  # NMI enable only

    asm.label("main_loop")
    asm.emit(0xCB)
    asm.branch(0x80, "main_loop")

    asm.pad_to(NMI_OFFSET)
    asm.label("nmi")
    asm.emit(0x48)                      # PHA
    asm.emit(0xAD, 0x10, 0x42)         # acknowledge NMI
    asm.emit(0xAF, 0x00, 0x00, 0x7E)  # frame counter
    asm.emit(0x1A)
    asm.emit(0x8F, 0x00, 0x00, 0x7E)
    asm.emit(0xC9, PHASE_FRAMES)
    asm.branch(0xD0, "check_wrap")

    emit_lda_sta_abs(asm, TREATMENT_CGADSUB, 0x2131)
    asm.emit(0xA9, TREATMENT_CGADSUB, 0x8F, 0x01, 0x00, 0x7E)
    asm.branch(0x80, "nmi_done")

    asm.label("check_wrap")
    asm.emit(0xC9, PHASE_FRAMES * 2)
    asm.branch(0xD0, "nmi_done")
    asm.emit(0xA9, 0x00, 0x8F, 0x00, 0x00, 0x7E)
    emit_lda_sta_abs(asm, CONTROL_CGADSUB, 0x2131)
    asm.emit(0xA9, CONTROL_CGADSUB, 0x8F, 0x01, 0x00, 0x7E)

    asm.label("nmi_done")
    asm.emit(0x68, 0x40)  # PLA; RTI

    program = asm.finish()
    if asm.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved")
    return program


def build_assets() -> tuple[bytes, bytes, bytes, bytes]:
    tile = bytes([0xFF, 0x00] * 8 + [0x00] * 16)

    bg1_map = bytes(0x800)
    bg2_map = bytearray(0x800)
    # 4bpp palette 1, tile 0: map word $0400.
    for offset in range(0, len(bg2_map), 2):
        bg2_map[offset : offset + 2] = (0x0400).to_bytes(2, "little")

    palette = bytearray(0x200)
    palette[2:4] = rgb5_word(SUB_RGB5).to_bytes(2, "little")       # BG1 palette0 color1
    palette[34:36] = rgb5_word(MAIN_RGB5).to_bytes(2, "little")   # BG2 palette1 color1
    return tile, bg1_map, bytes(bg2_map), bytes(palette)


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    program = build_program()
    if len(program) >= TILE_ADDRESS - LOAD_ADDRESS:
        raise ValueError("program overlaps assets")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[: len(program)] = program
    for address, data in zip(
        (TILE_ADDRESS, BG1_MAP_ADDRESS, BG2_MAP_ADDRESS, PALETTE_ADDRESS),
        build_assets(),
        strict=True,
    ):
        offset = address - LOAD_ADDRESS
        rom[offset : offset + len(data)] = data

    title = b"S64 GATEC HALF MATH"
    rom[HEADER : HEADER + 21] = title.ljust(21, b" ")
    rom[0x7FD5] = 0x20
    rom[0x7FD6] = 0x00
    rom[0x7FD7] = 0x05
    rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    write_vector(rom, 0x7FE4, 0x9000)
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
