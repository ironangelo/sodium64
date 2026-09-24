#!/usr/bin/env python3
"""Generate Gate-C inverted-W1 OBJ singleton-endpoint diagnostic SNES ROM.

This ROM contains no commercial game data. It isolates the integrated H-OBJ
endpoint/sentinel ambiguity at the legal rightmost SNES pixel.

Visible setup:
- Mode 1, OBJ only on the main screen.
- W1 = [255,255].
- OBJ selects inverted W1.
- One left 8x8 control sprite at x=16 and one edge sprite at x=248..255.
- Backdrop is blue.
- No BG, subscreen, color math, HDMA, IRQ, or W2.

The ROM alternates two 120-frame phases:
- control:   TMW=$00 (OBJ window disabled)
- treatment: TMW=$10 (OBJ window enabled)

Expected SNES behavior:
- control: both 8x8 red sprites are visible.
- treatment: the left sprite is masked and the edge sprite retains exactly
  its x=255 column. The [255,255] interval is a legal one-pixel interval.

The integrated candidate currently treats a next-lower value of 255 as an
end-of-list sentinel before drawing that legal singleton span, predicting no
red treatment pixels at the right edge. This diagnostic isolates that endpoint
contract only; it does not test W2/combine, color math, Mode7 window semantics,
or general compositor correctness.
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

BG_TILE_ADDRESS = 0x9000
OBJ_TILE_ADDRESS = 0x9020
BG_MAP_ADDRESS = 0x9040
PALETTE_ADDRESS = 0x9840
OAM_ADDRESS = 0x9A40

CONTROL_TMW = 0x00
TREATMENT_TMW = 0x10
WINDOW_LEFT = 255
WINDOW_RIGHT = 255
PHASE_FRAMES = 120

PHASE_COUNTER_WRAM = 0x7E0000
PHASE_VALUE_WRAM = 0x7E0001


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


def emit_vmadd(asm: Assembler, word_address: int) -> None:
    emit_lda_sta_abs(asm, word_address & 0xFF, 0x2116)
    emit_lda_sta_abs(asm, (word_address >> 8) & 0xFF, 0x2117)


def emit_dma_from_rom(
    asm: Assembler,
    *,
    channel: int,
    mode: int,
    bbus: int,
    source: int,
    size: int,
) -> None:
    if not 0 <= channel <= 7:
        raise ValueError("DMA channel must be 0..7")
    base = 0x4300 + channel * 0x10
    for value, address in (
        (mode, base + 0),
        (bbus, base + 1),
        (source & 0xFF, base + 2),
        ((source >> 8) & 0xFF, base + 3),
        (0x00, base + 4),  # source bank $00, where this 32 KiB LoROM is mapped
        (size & 0xFF, base + 5),
        ((size >> 8) & 0xFF, base + 6),
        (1 << channel, 0x420B),
    ):
        emit_lda_sta_abs(asm, value, address)


def build_program() -> bytes:
    asm = Assembler()

    # Reset starts in emulation mode. Enter native mode, keep X/Y 16-bit and A 8-bit.
    asm.emit(0x78, 0x18, 0xFB, 0xD8)  # SEI; CLC; XCE; CLD
    asm.emit(0xC2, 0x10)              # REP #$10
    asm.emit(0xE2, 0x20)              # SEP #$20

    # Static display setup under forced blank.
    for value, address in (
        (0x80, 0x2100),  # INIDISP forced blank
        (0x01, 0x2105),  # Mode 1
        (0x04, 0x2107),  # BG1 tilemap at VRAM word $0800
        (0x01, 0x210B),  # BG1 character data at VRAM word $1000
        (0x00, 0x2101),  # OBJ base 0, 8x8/16x16 size pair
        (0x80, 0x2115),  # increment VRAM after high-byte writes
    ):
        emit_lda_sta_abs(asm, value, address)

    # One opaque 4bpp tile for BG1 and one for OBJ, plus a zero tilemap.
    emit_vmadd(asm, 0x1000)
    emit_dma_from_rom(
        asm, channel=0, mode=1, bbus=0x18, source=BG_TILE_ADDRESS, size=0x20
    )
    emit_vmadd(asm, 0x0000)
    emit_dma_from_rom(
        asm, channel=0, mode=1, bbus=0x18, source=OBJ_TILE_ADDRESS, size=0x20
    )
    emit_vmadd(asm, 0x0800)
    emit_dma_from_rom(
        asm, channel=0, mode=1, bbus=0x18, source=BG_MAP_ADDRESS, size=0x800
    )

    # Deterministic palette and OAM.
    emit_lda_sta_abs(asm, 0x00, 0x2121)
    emit_dma_from_rom(
        asm, channel=0, mode=0, bbus=0x22, source=PALETTE_ADDRESS, size=0x200
    )
    emit_lda_sta_abs(asm, 0x00, 0x2102)
    emit_lda_sta_abs(asm, 0x00, 0x2103)
    emit_dma_from_rom(
        asm, channel=0, mode=0, bbus=0x04, source=OAM_ADDRESS, size=0x220
    )

    # Isolated W1 configuration. W2, color math, subscreen and HDMA stay disabled.
    for value, address in (
        (0x00, 0x2123),          # W12SEL: BG windows disabled
        (0x00, 0x2124),          # W34SEL disabled
        (0x03, 0x2125),          # WOBJSEL: OBJ uses inverted W1
        (WINDOW_LEFT, 0x2126),   # WH0
        (WINDOW_RIGHT, 0x2127),  # WH1
        (0x00, 0x2128),          # WH2
        (0x00, 0x2129),          # WH3
        (0x10, 0x212C),          # TM: OBJ only on main screen
        (0x00, 0x212D),          # TS: no subscreen layers
        (CONTROL_TMW, 0x212E),   # TMW phase starts with OBJ window disabled
        (0x00, 0x212F),          # TSW disabled
        (0x00, 0x2130),          # CGWSEL: color window/math disabled
        (0x00, 0x2131),          # CGADSUB: color math disabled
    ):
        emit_lda_sta_abs(asm, value, address)

    # Debugger-visible phase state. These WRAM writes have no rendering effect.
    asm.emit(0xA9, 0x00, 0x8F, 0x00, 0x00, 0x7E)
    asm.emit(0xA9, CONTROL_TMW, 0x8F, 0x01, 0x00, 0x7E)

    # Enable display and NMI. IRQ and HDMA remain disabled.
    emit_lda_sta_abs(asm, 0x0F, 0x2100)
    emit_lda_sta_abs(asm, 0x80, 0x4200)

    asm.label("main_loop")
    asm.emit(0xCB)                 # WAI
    asm.branch(0x80, "main_loop") # BRA main_loop

    # Fixed NMI handler lets CI synchronize on guest frame phase.
    asm.pad_to(NMI_OFFSET)
    asm.label("nmi")
    asm.emit(0x48)                  # PHA
    asm.emit(0xAD, 0x10, 0x42)     # LDA $4210, acknowledge NMI
    asm.emit(0xAF, 0x00, 0x00, 0x7E)  # LDA phase counter
    asm.emit(0x1A)                  # INC A
    asm.emit(0x8F, 0x00, 0x00, 0x7E)  # STA phase counter
    asm.emit(0xC9, PHASE_FRAMES)    # CMP #120
    asm.branch(0xD0, "check_wrap")

    emit_lda_sta_abs(asm, TREATMENT_TMW, 0x212E)
    asm.emit(0xA9, TREATMENT_TMW, 0x8F, 0x01, 0x00, 0x7E)
    asm.branch(0x80, "nmi_done")

    asm.label("check_wrap")
    asm.emit(0xC9, PHASE_FRAMES * 2)  # CMP #240
    asm.branch(0xD0, "nmi_done")

    asm.emit(0xA9, 0x00, 0x8F, 0x00, 0x00, 0x7E)
    emit_lda_sta_abs(asm, CONTROL_TMW, 0x212E)
    asm.emit(0xA9, CONTROL_TMW, 0x8F, 0x01, 0x00, 0x7E)

    asm.label("nmi_done")
    asm.emit(0x68, 0x40)            # PLA; RTI

    program = asm.finish()
    if asm.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved away from fixed vector")
    return program


def build_assets() -> tuple[bytes, bytes, bytes, bytes, bytes]:
    # 4bpp solid color-index-1 tile: plane 0 set, planes 1..3 clear.
    solid_tile = bytes([0xFF, 0x00] * 8 + [0x00] * 16)
    bg_map = bytes(0x800)  # 32x32 tilemap, every entry selects tile 0/palette 0

    palette = bytearray(0x200)
    palette[0:2] = (0x7C00).to_bytes(2, "little")      # backdrop = blue
    palette[2:4] = (0x03E0).to_bytes(2, "little")      # unused BG color 1 = green
    palette[0x102:0x104] = (0x001F).to_bytes(2, "little")  # OBJ color 1 = red

    oam = bytearray(0x220)
    for index in range(128):
        offset = index * 4
        oam[offset + 1] = 0xF0  # hide every sprite below visible 224-line field

    for index, x in enumerate((16, 248)):
        offset = index * 4
        oam[offset + 0] = x
        oam[offset + 1] = 96
        oam[offset + 2] = 0
        oam[offset + 3] = 0

    # High OAM table is already zero: X high bit clear and small-size selection.
    return solid_tile, solid_tile, bg_map, bytes(palette), bytes(oam)


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    program = build_program()
    if len(program) >= BG_TILE_ADDRESS - LOAD_ADDRESS:
        raise ValueError("program overlaps diagnostic asset region")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[: len(program)] = program

    for address, data in zip(
        (BG_TILE_ADDRESS, OBJ_TILE_ADDRESS, BG_MAP_ADDRESS, PALETTE_ADDRESS, OAM_ADDRESS),
        build_assets(),
        strict=True,
    ):
        offset = address - LOAD_ADDRESS
        rom[offset : offset + len(data)] = data

    title = b"S64 HOBJ X255 PROOF"
    rom[HEADER : HEADER + 21] = title.ljust(21, b" ")
    rom[0x7FD5] = 0x20  # LoROM, slow ROM
    rom[0x7FD6] = 0x00  # ROM only
    rom[0x7FD7] = 0x05  # 32 KiB
    rom[0x7FD8] = 0x00  # no SRAM
    rom[0x7FD9] = 0x01  # NTSC
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    # Keep native COP distinct for Sodium64's header detector.
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
