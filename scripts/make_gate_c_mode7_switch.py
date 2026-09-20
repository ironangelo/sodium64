#!/usr/bin/env python3
"""Generate a Gate-C whole-frame BGMODE 1<->7 overlay diagnostic.

Original/homebrew-only ROM. It isolates the real renderer fault-overlay
mechanism without yet testing mid-frame BGMODE switching or Mode7 fidelity.

The guest alternates complete frames in two 60-frame phases:
- control:   BGMODE=$01
- treatment: BGMODE=$07

WRAM $7E0000 is the NMI frame counter and $7E0001 mirrors the active BGMODE.
BG1 remains enabled on main screen. The regular phase renders a deterministic
solid BG; Mode7 graphics content is intentionally not a semantic oracle here.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from make_gate_c_obj_window import (
    Assembler,
    emit_dma_from_rom,
    emit_lda_sta_abs,
    emit_vmadd,
    write_vector,
)

ROM_SIZE = 0x8000
HEADER = 0x7FC0
LOAD_ADDRESS = 0x8000
NMI_ADDRESS = 0x8200
NMI_OFFSET = NMI_ADDRESS - LOAD_ADDRESS

BG_TILE_ADDRESS = 0x9000
BG_MAP_ADDRESS = 0x9040
PALETTE_ADDRESS = 0x9840

CONTROL_MODE = 0x01
TREATMENT_MODE = 0x07
PHASE_FRAMES = 60


def build_program() -> bytes:
    asm = Assembler()

    asm.emit(0x78, 0x18, 0xFB, 0xD8)  # SEI; CLC; XCE; CLD
    asm.emit(0xC2, 0x10)              # REP #$10
    asm.emit(0xE2, 0x20)              # SEP #$20

    for value, address in (
        (0x80, 0x2100),  # forced blank
        (CONTROL_MODE, 0x2105),
        (0x04, 0x2107),  # BG1 tilemap at word $0800
        (0x01, 0x210B),  # BG1 chars at word $1000
        (0x80, 0x2115),
    ):
        emit_lda_sta_abs(asm, value, address)

    emit_vmadd(asm, 0x1000)
    emit_dma_from_rom(
        asm, channel=0, mode=1, bbus=0x18, source=BG_TILE_ADDRESS, size=0x20
    )
    emit_vmadd(asm, 0x0800)
    emit_dma_from_rom(
        asm, channel=0, mode=1, bbus=0x18, source=BG_MAP_ADDRESS, size=0x800
    )

    emit_lda_sta_abs(asm, 0x00, 0x2121)
    emit_dma_from_rom(
        asm, channel=0, mode=0, bbus=0x22, source=PALETTE_ADDRESS, size=0x200
    )

    for value, address in (
        (0x01, 0x212C),  # BG1 main screen
        (0x00, 0x212D),
        (0x00, 0x212E),
        (0x00, 0x212F),
        (0x00, 0x2130),
        (0x00, 0x2131),
    ):
        emit_lda_sta_abs(asm, value, address)

    # Debugger-visible guest state.
    asm.emit(0xA9, 0x00, 0x8F, 0x00, 0x00, 0x7E)
    asm.emit(0xA9, CONTROL_MODE, 0x8F, 0x01, 0x00, 0x7E)

    emit_lda_sta_abs(asm, 0x0F, 0x2100)
    emit_lda_sta_abs(asm, 0x80, 0x4200)  # NMI only

    asm.label("main_loop")
    asm.emit(0xCB)
    asm.branch(0x80, "main_loop")

    asm.pad_to(NMI_OFFSET)
    asm.label("nmi")
    asm.emit(0x48)
    asm.emit(0xAD, 0x10, 0x42)          # acknowledge NMI
    asm.emit(0xAF, 0x00, 0x00, 0x7E)  # frame counter
    asm.emit(0x1A)
    asm.emit(0x8F, 0x00, 0x00, 0x7E)
    asm.emit(0xC9, PHASE_FRAMES)
    asm.branch(0xD0, "check_wrap")

    emit_lda_sta_abs(asm, TREATMENT_MODE, 0x2105)
    asm.emit(0xA9, TREATMENT_MODE, 0x8F, 0x01, 0x00, 0x7E)
    asm.branch(0x80, "nmi_done")

    asm.label("check_wrap")
    asm.emit(0xC9, PHASE_FRAMES * 2)
    asm.branch(0xD0, "nmi_done")

    asm.emit(0xA9, 0x00, 0x8F, 0x00, 0x00, 0x7E)
    emit_lda_sta_abs(asm, CONTROL_MODE, 0x2105)
    asm.emit(0xA9, CONTROL_MODE, 0x8F, 0x01, 0x00, 0x7E)

    asm.label("nmi_done")
    asm.emit(0x68, 0x40)

    program = asm.finish()
    if asm.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved away from fixed vector")
    return program


def build_assets() -> tuple[bytes, bytes, bytes]:
    tile = bytes([0xFF, 0x00] * 8 + [0x00] * 16)
    bg_map = bytes(0x800)
    palette = bytearray(0x200)
    palette[2:4] = (0x03E0).to_bytes(2, "little")
    return tile, bg_map, bytes(palette)


def build_rom() -> bytes:
    program = build_program()
    if len(program) >= BG_TILE_ADDRESS - LOAD_ADDRESS:
        raise ValueError("program overlaps asset region")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[: len(program)] = program
    for address, data in zip(
        (BG_TILE_ADDRESS, BG_MAP_ADDRESS, PALETTE_ADDRESS),
        build_assets(),
        strict=True,
    ):
        offset = address - LOAD_ADDRESS
        rom[offset : offset + len(data)] = data

    rom[HEADER : HEADER + 21] = b"S64 GATEC MODE1 MODE7".ljust(21, b" ")
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
    rom[0x7FDC:0x7FDE] = (checksum ^ 0xFFFF).to_bytes(2, "little")
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
