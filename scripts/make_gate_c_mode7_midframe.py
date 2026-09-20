#!/usr/bin/env python3
"""Generate a Gate-C visible mid-frame Mode1->Mode7->Mode1 overlay diagnostic.

Original/homebrew-only ROM. It validates one architecture question:
can Sodium64's demand-driven RSP renderer fault overlay switch from the regular
renderer to Mode7 and back to regular within one visible SNES frame?

The guest holds Mode1 for PRETEST_FRAMES NMIs so the debugger can capture a
stable pre-test state. At that NMI it enables a V-count IRQ for line 80.
IRQ #1 writes BGMODE=7 and reprograms VTIME to line 160. IRQ #2 writes
BGMODE=1, disables further V-IRQ, and enters a permanent post-test phase.

WRAM evidence:
  $7E0000 NMI frame counter
  $7E0001 phase: 0x01 pre-test, 0x33 post-test
  $7E0002 IRQ count
  $7E0003 current BGMODE mirror
  $7E0004 test-done flag
  $7E0005 NMI counter observed by IRQ #1
  $7E0006 NMI counter observed by IRQ #2

If IRQ #1/#2 record the same NMI counter, both BGMODE transitions happened
between the same two V-blanks. Pixel fidelity is intentionally not an oracle.
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
from make_gate_c_mode7_switch import build_assets

ROM_SIZE = 0x8000
HEADER = 0x7FC0
LOAD_ADDRESS = 0x8000
NMI_ADDRESS = 0x8200
IRQ_ADDRESS = 0x8300
NMI_OFFSET = NMI_ADDRESS - LOAD_ADDRESS
IRQ_OFFSET = IRQ_ADDRESS - LOAD_ADDRESS

BG_TILE_ADDRESS = 0x9000
BG_MAP_ADDRESS = 0x9040
PALETTE_ADDRESS = 0x9840

CONTROL_MODE = 0x01
TREATMENT_MODE = 0x07
PRETEST_PHASE = 0x01
POSTTEST_PHASE = 0x33
PRETEST_FRAMES = 30
IRQ1_LINE = 80
IRQ2_LINE = 160


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


def build_program() -> bytes:
    asm = Assembler()

    # Reset begins in emulation mode. Enter native mode, X/Y 16-bit, A 8-bit.
    asm.emit(0x78, 0x18, 0xFB, 0xD8)  # SEI; CLC; XCE; CLD
    asm.emit(0xC2, 0x10)              # REP #$10
    asm.emit(0xE2, 0x20)              # SEP #$20

    # Deterministic visible Mode1 setup under forced blank.
    for value, address in (
        (0x80, 0x2100),
        (CONTROL_MODE, 0x2105),
        (0x04, 0x2107),
        (0x01, 0x210B),
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

    # Zero debugger-visible state, then publish pre-test phase/mode.
    for address in range(0x7E0000, 0x7E0007):
        emit_lda_sta_long(asm, 0x00, address)
    emit_lda_sta_long(asm, PRETEST_PHASE, 0x7E0001)
    emit_lda_sta_long(asm, CONTROL_MODE, 0x7E0003)

    emit_lda_sta_abs(asm, 0x0F, 0x2100)
    emit_lda_sta_abs(asm, 0x80, 0x4200)  # NMI only during pre-test hold
    asm.emit(0x58)                       # CLI: permit the later V-count IRQ

    asm.label("main_loop")
    asm.emit(0xCB)                       # WAI
    asm.branch(0x80, "main_loop")

    # NMI: count frames. At exactly PRETEST_FRAMES arm V-IRQ line 80 once.
    asm.pad_to(NMI_OFFSET)
    asm.label("nmi")
    asm.emit(0x48)                       # PHA
    asm.emit(0xAD, 0x10, 0x42)         # acknowledge RDNMI
    emit_lda_long(asm, 0x7E0000)
    asm.emit(0x1A)                       # INC A
    emit_sta_long(asm, 0x7E0000)
    asm.emit(0xC9, PRETEST_FRAMES)
    asm.branch(0xD0, "nmi_done")
    emit_lda_long(asm, 0x7E0004)
    asm.branch(0xD0, "nmi_done")

    emit_lda_sta_abs(asm, IRQ1_LINE & 0xFF, 0x4209)
    emit_lda_sta_abs(asm, (IRQ1_LINE >> 8) & 0x01, 0x420A)
    emit_lda_sta_abs(asm, 0xA0, 0x4200)  # NMI + V-IRQ

    asm.label("nmi_done")
    asm.emit(0x68, 0x40)                 # PLA; RTI

    # IRQ chain: line 80 -> Mode7, then line 160 -> Mode1 and stop V-IRQ.
    asm.pad_to(IRQ_OFFSET)
    asm.label("irq")
    asm.emit(0x48)                       # PHA
    asm.emit(0xAD, 0x11, 0x42)         # read/clear TIMEUP
    emit_lda_long(asm, 0x7E0002)
    asm.emit(0x1A)                       # IRQ count++
    emit_sta_long(asm, 0x7E0002)
    asm.emit(0xC9, 0x01)
    asm.branch(0xD0, "irq_second")

    # IRQ #1, same visible frame: record frame identity and demand Mode7.
    emit_lda_long(asm, 0x7E0000)
    emit_sta_long(asm, 0x7E0005)
    emit_lda_sta_abs(asm, TREATMENT_MODE, 0x2105)
    emit_lda_sta_long(asm, TREATMENT_MODE, 0x7E0003)
    emit_lda_sta_abs(asm, IRQ2_LINE & 0xFF, 0x4209)
    emit_lda_sta_abs(asm, (IRQ2_LINE >> 8) & 0x01, 0x420A)
    asm.branch(0x80, "irq_done")

    asm.label("irq_second")
    asm.emit(0xC9, 0x02)
    asm.branch(0xD0, "irq_done")

    # IRQ #2: same frame if the NMI counter is unchanged. Return to regular.
    emit_lda_long(asm, 0x7E0000)
    emit_sta_long(asm, 0x7E0006)
    emit_lda_sta_abs(asm, CONTROL_MODE, 0x2105)
    emit_lda_sta_long(asm, CONTROL_MODE, 0x7E0003)
    emit_lda_sta_abs(asm, 0x80, 0x4200)  # disable V-IRQ; leave NMI enabled
    emit_lda_sta_long(asm, POSTTEST_PHASE, 0x7E0001)
    emit_lda_sta_long(asm, 0x01, 0x7E0004)

    asm.label("irq_done")
    asm.emit(0x68, 0x40)                 # PLA; RTI

    program = asm.finish()
    if asm.labels["nmi"] != NMI_OFFSET:
        raise ValueError("NMI handler moved away from fixed vector")
    if asm.labels["irq"] != IRQ_OFFSET:
        raise ValueError("IRQ handler moved away from fixed vector")
    return program


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

    rom[HEADER : HEADER + 21] = b"S64 GATEC MIDFRAME M7".ljust(21, b" ")
    rom[0x7FD5] = 0x20
    rom[0x7FD6] = 0x00
    rom[0x7FD7] = 0x05
    rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01
    rom[0x7FDA] = 0x33
    rom[0x7FDB] = 0x00

    # Native-mode vectors are authoritative after CLC/XCE; mirror emulation
    # NMI/IRQ vectors as a guard against accidental mode changes.
    write_vector(rom, 0x7FEA, NMI_ADDRESS)
    write_vector(rom, 0x7FEE, IRQ_ADDRESS)
    write_vector(rom, 0x7FFA, NMI_ADDRESS)
    write_vector(rom, 0x7FFC, LOAD_ADDRESS)
    write_vector(rom, 0x7FFE, IRQ_ADDRESS)

    # Keep unused vectors deterministic and harmless.
    for offset in (0x7FE4, 0x7FE6, 0x7FE8, 0x7FF4, 0x7FF6, 0x7FF8):
        write_vector(rom, offset, LOAD_ADDRESS)

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
