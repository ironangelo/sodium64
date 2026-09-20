#!/usr/bin/env python3
"""Generate the original Gate-C H-SAMPLE per-line HDMA diagnostic SNES ROM.

No commercial game data is used. The guest writes a distinct WH0 value on every
visible scanline through direct HDMA. Sodium64 should preserve every distinct
visible-line window state if its section producer/consumer is semantically exact.

The visual output is deliberately irrelevant to the primary oracle: CI reads the
completed Sodium64 section queue directly and compares queued WH0 snapshots with
this deterministic source sequence.
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
HDMA_WINDOW_TABLE_ADDRESS = 0x9000
HDMA_PROBE_TABLE_ADDRESS = 0x9200
VISIBLE_LINES = 224
FRAME_COUNTER_WRAM = 0x7E0000
PROBE_WRAM_OFFSET = 0x0100


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


def build_hdma_table() -> bytes:
    values = bytes(range(VISIBLE_LINES))
    table = bytearray()
    first = 127
    second = VISIBLE_LINES - first
    table.append(0x80 | first)
    table.extend(values[:first])
    table.append(0x80 | second)
    table.extend(values[first:])
    table.append(0)
    return bytes(table)


def build_program() -> bytes:
    asm = Assembler()

    asm.emit(0x78, 0x18, 0xFB, 0xD8)
    asm.emit(0xC2, 0x10)
    asm.emit(0xE2, 0x20)

    for value, address in (
        (0x80, 0x2100),
        (0x01, 0x2105),
        (0x03, 0x2123),
        (0x00, 0x2126),
        (0xFF, 0x2127),
        (0x01, 0x212C),
        (0x00, 0x212D),
        (0x01, 0x212E),
        (0x00, 0x212F),
        (0x00, 0x2130),
        (0x00, 0x2131),
    ):
        emit_lda_sta_abs(asm, value, address)

    # Channel 0 writes WH0. Channel 1 mirrors the same per-line source bytes
    # through WMDATA into WRAM $7E0100..$7E01DF as an independent transfer guard.
    for value, address in (
        (0x00, 0x2181),
        (0x01, 0x2182),
        (0x00, 0x2183),
        (0x00, 0x4300),
        (0x26, 0x4301),
        (HDMA_WINDOW_TABLE_ADDRESS & 0xFF, 0x4302),
        ((HDMA_WINDOW_TABLE_ADDRESS >> 8) & 0xFF, 0x4303),
        (0x00, 0x4304),
        (0x00, 0x4310),
        (0x80, 0x4311),
        (HDMA_PROBE_TABLE_ADDRESS & 0xFF, 0x4312),
        ((HDMA_PROBE_TABLE_ADDRESS >> 8) & 0xFF, 0x4313),
        (0x00, 0x4314),
    ):
        emit_lda_sta_abs(asm, value, address)

    asm.emit(0xA9, 0x00, 0x8F, 0x00, 0x00, 0x7E)
    emit_lda_sta_abs(asm, 0x03, 0x420C)
    emit_lda_sta_abs(asm, 0x0F, 0x2100)
    emit_lda_sta_abs(asm, 0x80, 0x4200)

    asm.label("main_loop")
    asm.emit(0xCB)
    asm.branch(0x80, "main_loop")

    asm.pad_to(NMI_OFFSET)
    asm.label("nmi")
    asm.emit(0x48)
    asm.emit(0xAD, 0x10, 0x42)
    asm.emit(0xAF, 0x00, 0x00, 0x7E)
    asm.emit(0x1A)
    asm.emit(0x8F, 0x00, 0x00, 0x7E)
    emit_lda_sta_abs(asm, 0x00, 0x2181)
    emit_lda_sta_abs(asm, 0x01, 0x2182)
    emit_lda_sta_abs(asm, 0x00, 0x2183)
    asm.emit(0x68, 0x40)

    program = asm.finish()
    if asm.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved away from fixed vector")
    return program


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    program = build_program()
    table = build_hdma_table()
    window_offset = HDMA_WINDOW_TABLE_ADDRESS - LOAD_ADDRESS
    probe_offset = HDMA_PROBE_TABLE_ADDRESS - LOAD_ADDRESS
    if len(program) > window_offset:
        raise ValueError("program overlaps HDMA table")
    if window_offset + len(table) > probe_offset:
        raise ValueError("HDMA window table overlaps probe table")
    if probe_offset + len(table) >= HEADER:
        raise ValueError("HDMA probe table overlaps LoROM header")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[: len(program)] = program
    rom[window_offset : window_offset + len(table)] = table
    rom[probe_offset : probe_offset + len(table)] = table

    title = b"S64 GATEC H SAMPLE"
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
