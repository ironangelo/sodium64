#!/usr/bin/env python3
"""Generate the original Gate-C H-COMP add/subtract diagnostic SNES ROM.

No commercial game data is used. The guest renders only the backdrop and cycles
three stable phases:
  0x01: color math disabled
  0x02: backdrop ADD with fixed color
  0x03: backdrop SUBTRACT with the same fixed color

Backdrop color is full red and fixed color is full blue. On real SNES semantics,
ADD and SUBTRACT must produce different visible colors. Sodium64's current RSP
source only consumes CGADSUB bit 0x20, so identical ADD/SUBTRACT framebuffers
would dynamically confirm the demonstrated source omission.
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

FRAME_COUNTER = 0x7E0000
PHASE_MIRROR = 0x7E0001
PHASE_AGE = 0x7E0002
PHASE_DISABLED = 0x01
PHASE_ADD = 0x02
PHASE_SUB = 0x03
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


def emit_sta_long(asm: Assembler, address: int) -> None:
    asm.emit(
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


def build_program() -> bytes:
    asm = Assembler()

    # Native mode, 16-bit X/Y, 8-bit accumulator.
    asm.emit(0x78, 0x18, 0xFB, 0xD8)
    asm.emit(0xC2, 0x10)
    asm.emit(0xE2, 0x20)

    # Force blank while establishing deterministic backdrop/fixed colors.
    emit_lda_sta_abs(asm, 0x80, 0x2100)

    # CGRAM color 0 = full red (BGR555 0x001F).
    emit_lda_sta_abs(asm, 0x00, 0x2121)
    emit_lda_sta_abs(asm, 0x1F, 0x2122)
    emit_lda_sta_abs(asm, 0x00, 0x2122)

    # Fixed color = full blue. COLDATA bit7 selects blue, low5 = intensity.
    emit_lda_sta_abs(asm, 0x9F, 0x2132)

    # No BG/OBJ layers. CGWSEL=0 selects the fixed-color operand and no math
    # window restriction. Start with color math disabled.
    emit_lda_sta_abs(asm, 0x00, 0x212C)
    emit_lda_sta_abs(asm, 0x00, 0x212D)
    emit_lda_sta_abs(asm, 0x00, 0x2130)
    emit_lda_sta_abs(asm, 0x00, 0x2131)

    emit_lda_sta_long(asm, 0x00, FRAME_COUNTER)
    emit_lda_sta_long(asm, PHASE_DISABLED, PHASE_MIRROR)
    emit_lda_sta_long(asm, 0x00, PHASE_AGE)

    # Full brightness + NMI enable.
    emit_lda_sta_abs(asm, 0x0F, 0x2100)
    emit_lda_sta_abs(asm, 0x80, 0x4200)

    asm.label("main_loop")
    asm.emit(0xCB)  # WAI
    asm.branch(0x80, "main_loop")  # BRA

    asm.pad_to(NMI_OFFSET)
    asm.label("nmi")
    asm.emit(0x48)  # PHA
    asm.emit(0xAD, 0x10, 0x42)  # LDA $4210, acknowledge NMI

    # Increment global guest-frame counter.
    emit_lda_long(asm, FRAME_COUNTER)
    asm.emit(0x1A)  # INC A
    emit_sta_long(asm, FRAME_COUNTER)

    # Hold each phase long enough for a fresh displayed framebuffer capture.
    emit_lda_long(asm, PHASE_AGE)
    asm.emit(0x1A)
    emit_sta_long(asm, PHASE_AGE)
    asm.emit(0xC9, PHASE_FRAMES)  # CMP #PHASE_FRAMES
    asm.branch(0xD0, "nmi_done")  # BNE

    emit_lda_sta_long(asm, 0x00, PHASE_AGE)
    emit_lda_long(asm, PHASE_MIRROR)
    asm.emit(0xC9, PHASE_DISABLED)
    asm.branch(0xF0, "set_add")  # BEQ
    asm.emit(0xC9, PHASE_ADD)
    asm.branch(0xF0, "set_sub")  # BEQ

    asm.label("set_disabled")
    emit_lda_sta_long(asm, PHASE_DISABLED, PHASE_MIRROR)
    emit_lda_sta_abs(asm, 0x00, 0x2131)
    asm.branch(0x80, "nmi_done")

    asm.label("set_add")
    emit_lda_sta_long(asm, PHASE_ADD, PHASE_MIRROR)
    emit_lda_sta_abs(asm, 0x20, 0x2131)
    asm.branch(0x80, "nmi_done")

    asm.label("set_sub")
    emit_lda_sta_long(asm, PHASE_SUB, PHASE_MIRROR)
    emit_lda_sta_abs(asm, 0xA0, 0x2131)

    asm.label("nmi_done")
    asm.emit(0x68, 0x40)  # PLA; RTI

    program = asm.finish()
    if asm.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved away from fixed vector")
    return program


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    program = build_program()
    if len(program) >= HEADER:
        raise ValueError("program overlaps LoROM header")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[: len(program)] = program

    title = b"S64 GATEC H COMP"
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
