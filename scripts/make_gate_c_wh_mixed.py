#!/usr/bin/env python3
"""Generate original deterministic SNES ROMs for Sodium64 profiling.

The workloads contain no copyrighted game data. The first five deliberately
stress individual paths, while gameplay-balanced combines bounded work in a
frame-paced shape closer to an ordinary SNES game:

- idle: minimal native-mode branch loop;
- cpu-alu: arithmetic/branch-heavy 65C816 execution;
- wram: long-indexed WRAM reads and writes;
- ppu-registers: repeated CGRAM/scroll register updates;
- dma-vram: repeated 4 KiB DMA transfers from WRAM to VRAM;
- gameplay-balanced: WAI/NMI frame pacing, bounded game logic/WRAM updates,
  scrolling, one visible OBJ, OAM DMA, modest VRAM DMA, and a small CGRAM DMA
  once per frame.

These are diagnostic workloads, not substitutes for commercial-game milestone
validation. Their value is that differences between profiles are attributable to
known guest work and can be reproduced in CI without ROM assets.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

ROM_SIZE = 0x8000  # 32 KiB LoROM
HEADER = 0x7FC0
LOAD_ADDRESS = 0x8000
GAMEPLAY_NMI_ADDRESS = 0x8100
GAMEPLAY_NMI_OFFSET = GAMEPLAY_NMI_ADDRESS - LOAD_ADDRESS
GAMEPLAY_WINDOW_TABLE_ADDRESS = 0x9400


class Assembler:
    """Very small helper for the handful of relative branches used here."""

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
            # Relative branches are measured from the instruction following the
            # signed 8-bit displacement byte.
            delta = self.labels[label] - (operand_index + 1)
            if not -128 <= delta <= 127:
                raise ValueError(f"branch to {label} is out of rel8 range: {delta}")
            self.code[operand_index] = delta & 0xFF
        return bytes(self.code)


def native_prefix(asm: Assembler, *, accumulator_8bit: bool = False) -> None:
    # SEI; CLC; XCE; CLD. Reset begins in emulation mode; XCE enters native mode.
    asm.emit(0x78, 0x18, 0xFB, 0xD8)
    if accumulator_8bit:
        # X/Y 16-bit, accumulator 8-bit.
        asm.emit(0xC2, 0x10)  # REP #$10
        asm.emit(0xE2, 0x20)  # SEP #$20
    else:
        # Accumulator and X/Y 16-bit.
        asm.emit(0xC2, 0x30)  # REP #$30


def workload_idle() -> bytes:
    asm = Assembler()
    native_prefix(asm)
    asm.label("loop")
    asm.branch(0x80, "loop")  # BRA loop
    return asm.finish()


def workload_cpu_alu() -> bytes:
    asm = Assembler()
    native_prefix(asm)
    asm.emit(0xA9, 0x34, 0x12)  # LDA #$1234
    asm.label("outer")
    asm.emit(0xA2, 0xFF, 0xFF)  # LDX #$FFFF
    asm.label("loop")
    asm.emit(0x18)              # CLC
    asm.emit(0x69, 0x01, 0x01)  # ADC #$0101
    asm.emit(0x49, 0x5A, 0xA5)  # EOR #$A55A
    asm.emit(0x2A)              # ROL A
    asm.emit(0xCA)              # DEX
    asm.branch(0xD0, "loop")    # BNE loop
    asm.branch(0x80, "outer")   # BRA outer
    return asm.finish()


def workload_wram() -> bytes:
    asm = Assembler()
    native_prefix(asm)
    asm.emit(0xA2, 0x00, 0x00)        # LDX #$0000
    asm.emit(0xA9, 0x5A, 0x5A)        # LDA #$5A5A
    asm.label("loop")
    asm.emit(0x9F, 0x00, 0x00, 0x7E)  # STA $7E0000,X
    asm.emit(0xBF, 0x00, 0x00, 0x7E)  # LDA $7E0000,X
    asm.emit(0x49, 0xFF, 0xFF)        # EOR #$FFFF
    asm.emit(0x9F, 0x00, 0x00, 0x7E)  # STA $7E0000,X
    asm.emit(0xE8, 0xE8)              # INX; INX (word-aligned stride)
    asm.branch(0x80, "loop")          # BRA loop
    return asm.finish()


def workload_ppu_registers() -> bytes:
    asm = Assembler()
    native_prefix(asm, accumulator_8bit=True)
    asm.emit(0xA9, 0x0F, 0x8D, 0x00, 0x21)  # LDA #$0F; STA $2100 (brightness)
    asm.emit(0xA9, 0x00, 0x8D, 0x21, 0x21)  # LDA #$00; STA $2121 (CGADD)
    asm.emit(0xA2, 0x00, 0x00)              # LDX #$0000
    asm.label("loop")
    asm.emit(0x8A)                          # TXA
    asm.emit(0x8D, 0x22, 0x21)              # STA $2122 (CGRAM low/high stream)
    asm.emit(0x49, 0x1F)                    # EOR #$1F
    asm.emit(0x8D, 0x22, 0x21)              # STA $2122
    asm.emit(0x8A)                          # TXA
    asm.emit(0x8D, 0x0D, 0x21)              # STA $210D (BG1HOFS first write)
    asm.emit(0x8D, 0x0D, 0x21)              # STA $210D (BG1HOFS second write)
    asm.emit(0xE8)                          # INX
    asm.branch(0x80, "loop")                # BRA loop
    return asm.finish()


def workload_dma_vram() -> bytes:
    asm = Assembler()
    native_prefix(asm, accumulator_8bit=True)

    # VRAM address increment after high-byte writes, starting at word 0.
    asm.emit(0xA9, 0x80, 0x8D, 0x15, 0x21)  # LDA #$80; STA $2115 (VMAIN)
    asm.emit(0xA9, 0x00, 0x8D, 0x16, 0x21)  # VMADDL
    asm.emit(0x8D, 0x17, 0x21)              # VMADDH

    asm.label("loop")
    # DMA channel 0: mode 1 alternates $2118/$2119, source $7E:0000,
    # transfer length $1000 bytes. DMA updates source/count, so reload the
    # channel registers before each transfer.
    asm.emit(0xA9, 0x01, 0x8D, 0x00, 0x43)  # DMAP0 = mode 1
    asm.emit(0xA9, 0x18, 0x8D, 0x01, 0x43)  # BBAD0 = $2118
    asm.emit(0xA9, 0x00, 0x8D, 0x02, 0x43)  # A1T0L = $00
    asm.emit(0x8D, 0x03, 0x43)              # A1T0H = $00
    asm.emit(0xA9, 0x7E, 0x8D, 0x04, 0x43)  # A1B0 = $7E
    asm.emit(0xA9, 0x00, 0x8D, 0x05, 0x43)  # DAS0L = $00
    asm.emit(0xA9, 0x10, 0x8D, 0x06, 0x43)  # DAS0H = $10 (4096 bytes)
    asm.emit(0xA9, 0x01, 0x8D, 0x0B, 0x42)  # MDMAEN = channel 0
    asm.branch(0x80, "loop")                # BRA loop
    return asm.finish()



def build_gameplay_window_hdma_table() -> bytes:
    values = bytes(range(224))
    table = bytearray()
    first = 127
    second = 224 - first
    table.append(0x80 | first)
    table.extend(values[:first])
    table.append(0x80 | second)
    table.extend(values[first:])
    table.append(0)
    return bytes(table)


def workload_gameplay_balanced() -> bytes:
    """A deterministic frame-paced workload shaped like ordinary game logic."""
    asm = Assembler()
    native_prefix(asm, accumulator_8bit=True)

    # Begin under forced blank, configure a simple Mode-1/BG1 layout, normal
    # VRAM increment behavior and the OAM base. BG1 + OBJ are the only visible
    # layers so the RSP receives a small but genuine frame-rendering workload.
    asm.emit(0xA9, 0x80, 0x8D, 0x00, 0x21)  # INIDISP = forced blank
    asm.emit(0xA9, 0x01, 0x8D, 0x05, 0x21)  # BGMODE = mode 1
    asm.emit(0xA9, 0x04, 0x8D, 0x07, 0x21)  # BG1SC = tilemap at $0800
    asm.emit(0xA9, 0x01, 0x8D, 0x0B, 0x21)  # BG12NBA = BG1 tiles at $1000
    asm.emit(0xA9, 0x11, 0x8D, 0x2C, 0x21)  # TM = BG1 + OBJ on main screen
    asm.emit(0xA9, 0x80, 0x8D, 0x15, 0x21)  # VMAIN = increment after high byte
    asm.emit(0xA9, 0x00, 0x8D, 0x16, 0x21)  # VMADDL = 0
    asm.emit(0x8D, 0x17, 0x21)              # VMADDH = 0
    asm.emit(0x8D, 0x02, 0x21)              # OAMADDL = 0
    asm.emit(0x8D, 0x03, 0x21)              # OAMADDH = 0

    # Seed a small deterministic staging region used by the per-frame VRAM and
    # CGRAM DMAs. Keep it entirely separate from the 544-byte OAM shadow at
    # $7E2000-$7E221F so sprite metadata and tile/palette staging cannot alias.
    # This is startup-only work and is excluded by profiler warm-up.
    asm.emit(0xA2, 0x00, 0x00)              # LDX #0
    asm.label("seed_loop")
    asm.emit(0x8A)                          # TXA
    asm.emit(0x9F, 0x00, 0x24, 0x7E)        # STA $7E2400,X
    asm.emit(0xE8)                          # INX
    asm.emit(0xE0, 0x00, 0x01)              # CPX #$0100
    asm.branch(0xD0, "seed_loop")           # BNE seed_loop

    # Initialize the full 544-byte OAM shadow explicitly instead of depending on
    # WRAM power-on contents. Then put every sprite below the visible 224-line
    # field; sprite 0 is overridden below as the one deliberately visible OBJ.
    asm.emit(0xA9, 0x00)                    # LDA #0
    asm.emit(0xA2, 0x00, 0x00)              # LDX #0
    asm.label("clear_oam")
    asm.emit(0x9F, 0x00, 0x20, 0x7E)        # STA $7E2000,X
    asm.emit(0xE8)                          # INX
    asm.emit(0xE0, 0x20, 0x02)              # CPX #$0220
    asm.branch(0xD0, "clear_oam")           # BNE clear_oam

    asm.emit(0xA9, 0xF0)                    # Y=$F0: outside visible 224-line field
    asm.emit(0xA2, 0x01, 0x00)              # first Y byte in low OAM table
    asm.label("hide_oam")
    asm.emit(0x9F, 0x00, 0x20, 0x7E)        # STA $7E2000,X
    asm.emit(0xE8, 0xE8, 0xE8, 0xE8)        # next sprite's Y byte
    asm.emit(0xE0, 0x00, 0x02)              # CPX #$0200
    asm.branch(0x90, "hide_oam")             # BCC while still in low OAM table

    # Camera/animation state and sprite 0 start from deterministic values.
    asm.emit(0xA9, 0x00)
    asm.emit(0x8F, 0x00, 0x00, 0x7E)        # camera low
    asm.emit(0x8F, 0x01, 0x00, 0x7E)        # camera high
    asm.emit(0x8F, 0x00, 0x20, 0x7E)        # sprite 0 X
    asm.emit(0xA9, 0x70, 0x8F, 0x01, 0x20, 0x7E)  # sprite 0 Y
    asm.emit(0xA9, 0x00, 0x8F, 0x02, 0x20, 0x7E)  # sprite 0 tile
    asm.emit(0x8F, 0x03, 0x20, 0x7E)              # sprite 0 attributes

    # Enable display and NMI. IRQs remain masked; frame cadence comes from NMI.
    asm.emit(0xA9, 0x0F, 0x8D, 0x00, 0x21)  # brightness 15
    asm.emit(0xA9, 0x80, 0x8D, 0x00, 0x42)  # NMITIMEN: NMI enable

    asm.label("game_loop")
    asm.emit(0xCB)                           # WAI - wait for next NMI/frame

    # Bounded game-simulation work: update 64 bytes of entity state once per
    # frame, rather than burning the S-CPU continuously as cpu-alu/wram do.
    asm.emit(0xA2, 0x00, 0x00)              # LDX #0
    asm.label("entity_loop")
    asm.emit(0xBF, 0x00, 0x10, 0x7E)        # LDA $7E1000,X
    asm.emit(0x18)                           # CLC
    asm.emit(0x69, 0x03)                     # ADC #$03
    asm.emit(0x49, 0x5A)                     # EOR #$5A
    asm.emit(0x9F, 0x00, 0x10, 0x7E)        # STA $7E1000,X
    asm.emit(0xE8)                           # INX
    asm.emit(0xE0, 0x40, 0x00)              # CPX #$0040
    asm.branch(0xD0, "entity_loop")         # BNE entity_loop

    # Advance a 16-bit camera value and mirror its low byte into sprite 0 so the
    # per-frame OAM DMA carries changing game state.
    asm.emit(0xAF, 0x00, 0x00, 0x7E)        # LDA camera low
    asm.emit(0x18)                           # CLC
    asm.emit(0x69, 0x01)                     # ADC #1
    asm.emit(0x8F, 0x00, 0x00, 0x7E)        # store camera low
    asm.emit(0x8F, 0x00, 0x20, 0x7E)        # sprite 0 X = camera low
    asm.emit(0xAF, 0x01, 0x00, 0x7E)        # LDA camera high
    asm.emit(0x69, 0x00)                     # ADC #0 + carry
    asm.emit(0x8F, 0x01, 0x00, 0x7E)        # store camera high
    asm.branch(0x80, "game_loop")           # BRA game_loop

    # Place the NMI handler at a fixed address so the LoROM vectors are stable
    # and trivially testable. NOP padding is never executed in normal flow.
    asm.pad_to(GAMEPLAY_NMI_OFFSET)
    asm.label("nmi")

    # Preserve the registers touched by the frame handler and acknowledge NMI.
    asm.emit(0x48, 0xDA, 0x5A)              # PHA; PHX; PHY
    asm.emit(0xAD, 0x10, 0x42)              # LDA $4210 (RDNMI)

    # Camera-driven horizontal scroll: $210D expects two sequential byte writes.
    asm.emit(0xAF, 0x00, 0x00, 0x7E)        # camera low
    asm.emit(0x8D, 0x0D, 0x21)              # BG1HOFS low
    asm.emit(0xAF, 0x01, 0x00, 0x7E)        # camera high
    asm.emit(0x8D, 0x0D, 0x21)              # BG1HOFS high

    # Typical OAM shadow upload: 544 bytes from WRAM to $2104 via DMA channel 0.
    asm.emit(0xA9, 0x00, 0x8D, 0x02, 0x21)  # OAMADDL = 0
    asm.emit(0x8D, 0x03, 0x21)              # OAMADDH = 0
    asm.emit(0x8D, 0x00, 0x43)              # DMAP0 = mode 0
    asm.emit(0xA9, 0x04, 0x8D, 0x01, 0x43)  # BBAD0 = $2104
    asm.emit(0xA9, 0x00, 0x8D, 0x02, 0x43)  # A1T0L = $00
    asm.emit(0xA9, 0x20, 0x8D, 0x03, 0x43)  # A1T0H = $20
    asm.emit(0xA9, 0x7E, 0x8D, 0x04, 0x43)  # A1B0 = $7E
    asm.emit(0xA9, 0x20, 0x8D, 0x05, 0x43)  # DAS0L = $20
    asm.emit(0xA9, 0x02, 0x8D, 0x06, 0x43)  # DAS0H = $02 (544 bytes)
    asm.emit(0xA9, 0x01, 0x8D, 0x0B, 0x42)  # MDMAEN = channel 0

    # Modest dynamic VRAM update: 128 bytes from $7E2400 through channel 1.
    asm.emit(0xAF, 0x00, 0x00, 0x7E)        # animate VRAM destination with camera
    asm.emit(0x8D, 0x16, 0x21)              # VMADDL
    asm.emit(0xA9, 0x00, 0x8D, 0x17, 0x21)  # VMADDH
    asm.emit(0xA9, 0x01, 0x8D, 0x10, 0x43)  # DMAP1 = mode 1
    asm.emit(0xA9, 0x18, 0x8D, 0x11, 0x43)  # BBAD1 = $2118
    asm.emit(0xA9, 0x00, 0x8D, 0x12, 0x43)  # A1T1L = $00
    asm.emit(0xA9, 0x24, 0x8D, 0x13, 0x43)  # A1T1H = $24
    asm.emit(0xA9, 0x7E, 0x8D, 0x14, 0x43)  # A1B1 = $7E
    asm.emit(0xA9, 0x80, 0x8D, 0x15, 0x43)  # DAS1L = $80
    asm.emit(0xA9, 0x00, 0x8D, 0x16, 0x43)  # DAS1H = 0
    asm.emit(0xA9, 0x02, 0x8D, 0x0B, 0x42)  # MDMAEN = channel 1

    # Small palette refresh: 32 bytes from $7E2480 to CGRAM via channel 2.
    asm.emit(0xA9, 0x00, 0x8D, 0x21, 0x21)  # CGADD = 0
    asm.emit(0x8D, 0x20, 0x43)              # DMAP2 = mode 0
    asm.emit(0xA9, 0x22, 0x8D, 0x21, 0x43)  # BBAD2 = $2122
    asm.emit(0xA9, 0x80, 0x8D, 0x22, 0x43)  # A1T2L = $80
    asm.emit(0xA9, 0x24, 0x8D, 0x23, 0x43)  # A1T2H = $24
    asm.emit(0xA9, 0x7E, 0x8D, 0x24, 0x43)  # A1B2 = $7E
    asm.emit(0xA9, 0x20, 0x8D, 0x25, 0x43)  # DAS2L = 32
    asm.emit(0xA9, 0x00, 0x8D, 0x26, 0x43)  # DAS2H = 0
    asm.emit(0xA9, 0x04, 0x8D, 0x0B, 0x42)  # MDMAEN = channel 2

    asm.emit(0x7A, 0xFA, 0x68, 0x40)        # PLY; PLX; PLA; RTI

    program = asm.finish()
    if asm.labels["nmi"] != GAMEPLAY_NMI_OFFSET:
        raise ValueError("gameplay NMI handler moved away from its fixed vector")
    return program
def workload_gameplay_window_hdma() -> bytes:
    """A deterministic frame-paced workload shaped like ordinary game logic."""
    asm = Assembler()
    native_prefix(asm, accumulator_8bit=True)

    # Begin under forced blank, configure a simple Mode-1/BG1 layout, normal
    # VRAM increment behavior and the OAM base. BG1 + OBJ are the only visible
    # layers so the RSP receives a small but genuine frame-rendering workload.
    asm.emit(0xA9, 0x80, 0x8D, 0x00, 0x21)  # INIDISP = forced blank
    asm.emit(0xA9, 0x01, 0x8D, 0x05, 0x21)  # BGMODE = mode 1
    asm.emit(0xA9, 0x04, 0x8D, 0x07, 0x21)  # BG1SC = tilemap at $0800
    asm.emit(0xA9, 0x01, 0x8D, 0x0B, 0x21)  # BG12NBA = BG1 tiles at $1000
    asm.emit(0xA9, 0x11, 0x8D, 0x2C, 0x21)  # TM = BG1 + OBJ on main screen
    asm.emit(0xA9, 0x80, 0x8D, 0x15, 0x21)  # VMAIN = increment after high byte
    asm.emit(0xA9, 0x00, 0x8D, 0x16, 0x21)  # VMADDL = 0
    asm.emit(0x8D, 0x17, 0x21)              # VMADDH = 0
    asm.emit(0x8D, 0x02, 0x21)              # OAMADDL = 0
    asm.emit(0x8D, 0x03, 0x21)              # OAMADDH = 0

    # Gate-C mixed control: enable BG1 windowing and drive WH0 once per visible
    # line through dedicated HDMA channel 3. Existing gameplay DMA remains on 0-2.
    asm.emit(0xA9, 0x03, 0x8D, 0x23, 0x21)  # W12SEL: BG1 window 1 enabled
    asm.emit(0xA9, 0x00, 0x8D, 0x26, 0x21)  # WH0 initial left edge
    asm.emit(0xA9, 0xFF, 0x8D, 0x27, 0x21)  # WH1 fixed right edge
    asm.emit(0xA9, 0x01, 0x8D, 0x2E, 0x21)  # TMW: BG1 window mask on main
    asm.emit(0xA9, 0x00, 0x8D, 0x30, 0x43)  # DMAP3: direct mode
    asm.emit(0xA9, 0x26, 0x8D, 0x31, 0x43)  # BBAD3: WH0 ($2126)
    asm.emit(0xA9, GAMEPLAY_WINDOW_TABLE_ADDRESS & 0xFF, 0x8D, 0x32, 0x43)
    asm.emit(0xA9, (GAMEPLAY_WINDOW_TABLE_ADDRESS >> 8) & 0xFF, 0x8D, 0x33, 0x43)
    asm.emit(0xA9, 0x00, 0x8D, 0x34, 0x43)  # A1B3 bank 0
    asm.emit(0xA9, 0x08, 0x8D, 0x0C, 0x42)  # HDMAEN channel 3

    # Seed a small deterministic staging region used by the per-frame VRAM and
    # CGRAM DMAs. Keep it entirely separate from the 544-byte OAM shadow at
    # $7E2000-$7E221F so sprite metadata and tile/palette staging cannot alias.
    # This is startup-only work and is excluded by profiler warm-up.
    asm.emit(0xA2, 0x00, 0x00)              # LDX #0
    asm.label("seed_loop")
    asm.emit(0x8A)                          # TXA
    asm.emit(0x9F, 0x00, 0x24, 0x7E)        # STA $7E2400,X
    asm.emit(0xE8)                          # INX
    asm.emit(0xE0, 0x00, 0x01)              # CPX #$0100
    asm.branch(0xD0, "seed_loop")           # BNE seed_loop

    # Initialize the full 544-byte OAM shadow explicitly instead of depending on
    # WRAM power-on contents. Then put every sprite below the visible 224-line
    # field; sprite 0 is overridden below as the one deliberately visible OBJ.
    asm.emit(0xA9, 0x00)                    # LDA #0
    asm.emit(0xA2, 0x00, 0x00)              # LDX #0
    asm.label("clear_oam")
    asm.emit(0x9F, 0x00, 0x20, 0x7E)        # STA $7E2000,X
    asm.emit(0xE8)                          # INX
    asm.emit(0xE0, 0x20, 0x02)              # CPX #$0220
    asm.branch(0xD0, "clear_oam")           # BNE clear_oam

    asm.emit(0xA9, 0xF0)                    # Y=$F0: outside visible 224-line field
    asm.emit(0xA2, 0x01, 0x00)              # first Y byte in low OAM table
    asm.label("hide_oam")
    asm.emit(0x9F, 0x00, 0x20, 0x7E)        # STA $7E2000,X
    asm.emit(0xE8, 0xE8, 0xE8, 0xE8)        # next sprite's Y byte
    asm.emit(0xE0, 0x00, 0x02)              # CPX #$0200
    asm.branch(0x90, "hide_oam")             # BCC while still in low OAM table

    # Camera/animation state and sprite 0 start from deterministic values.
    asm.emit(0xA9, 0x00)
    asm.emit(0x8F, 0x00, 0x00, 0x7E)        # camera low
    asm.emit(0x8F, 0x01, 0x00, 0x7E)        # camera high
    asm.emit(0x8F, 0x00, 0x20, 0x7E)        # sprite 0 X
    asm.emit(0xA9, 0x70, 0x8F, 0x01, 0x20, 0x7E)  # sprite 0 Y
    asm.emit(0xA9, 0x00, 0x8F, 0x02, 0x20, 0x7E)  # sprite 0 tile
    asm.emit(0x8F, 0x03, 0x20, 0x7E)              # sprite 0 attributes

    # Enable display and NMI. IRQs remain masked; frame cadence comes from NMI.
    asm.emit(0xA9, 0x0F, 0x8D, 0x00, 0x21)  # brightness 15
    asm.emit(0xA9, 0x80, 0x8D, 0x00, 0x42)  # NMITIMEN: NMI enable

    asm.label("game_loop")
    asm.emit(0xCB)                           # WAI - wait for next NMI/frame

    # Bounded game-simulation work: update 64 bytes of entity state once per
    # frame, rather than burning the S-CPU continuously as cpu-alu/wram do.
    asm.emit(0xA2, 0x00, 0x00)              # LDX #0
    asm.label("entity_loop")
    asm.emit(0xBF, 0x00, 0x10, 0x7E)        # LDA $7E1000,X
    asm.emit(0x18)                           # CLC
    asm.emit(0x69, 0x03)                     # ADC #$03
    asm.emit(0x49, 0x5A)                     # EOR #$5A
    asm.emit(0x9F, 0x00, 0x10, 0x7E)        # STA $7E1000,X
    asm.emit(0xE8)                           # INX
    asm.emit(0xE0, 0x40, 0x00)              # CPX #$0040
    asm.branch(0xD0, "entity_loop")         # BNE entity_loop

    # Advance a 16-bit camera value and mirror its low byte into sprite 0 so the
    # per-frame OAM DMA carries changing game state.
    asm.emit(0xAF, 0x00, 0x00, 0x7E)        # LDA camera low
    asm.emit(0x18)                           # CLC
    asm.emit(0x69, 0x01)                     # ADC #1
    asm.emit(0x8F, 0x00, 0x00, 0x7E)        # store camera low
    asm.emit(0x8F, 0x00, 0x20, 0x7E)        # sprite 0 X = camera low
    asm.emit(0xAF, 0x01, 0x00, 0x7E)        # LDA camera high
    asm.emit(0x69, 0x00)                     # ADC #0 + carry
    asm.emit(0x8F, 0x01, 0x00, 0x7E)        # store camera high
    asm.branch(0x80, "game_loop")           # BRA game_loop

    # Place the NMI handler at a fixed address so the LoROM vectors are stable
    # and trivially testable. NOP padding is never executed in normal flow.
    asm.pad_to(GAMEPLAY_NMI_OFFSET)
    asm.label("nmi")

    # Preserve the registers touched by the frame handler and acknowledge NMI.
    asm.emit(0x48, 0xDA, 0x5A)              # PHA; PHX; PHY
    asm.emit(0xAD, 0x10, 0x42)              # LDA $4210 (RDNMI)

    # Camera-driven horizontal scroll: $210D expects two sequential byte writes.
    asm.emit(0xAF, 0x00, 0x00, 0x7E)        # camera low
    asm.emit(0x8D, 0x0D, 0x21)              # BG1HOFS low
    asm.emit(0xAF, 0x01, 0x00, 0x7E)        # camera high
    asm.emit(0x8D, 0x0D, 0x21)              # BG1HOFS high

    # Typical OAM shadow upload: 544 bytes from WRAM to $2104 via DMA channel 0.
    asm.emit(0xA9, 0x00, 0x8D, 0x02, 0x21)  # OAMADDL = 0
    asm.emit(0x8D, 0x03, 0x21)              # OAMADDH = 0
    asm.emit(0x8D, 0x00, 0x43)              # DMAP0 = mode 0
    asm.emit(0xA9, 0x04, 0x8D, 0x01, 0x43)  # BBAD0 = $2104
    asm.emit(0xA9, 0x00, 0x8D, 0x02, 0x43)  # A1T0L = $00
    asm.emit(0xA9, 0x20, 0x8D, 0x03, 0x43)  # A1T0H = $20
    asm.emit(0xA9, 0x7E, 0x8D, 0x04, 0x43)  # A1B0 = $7E
    asm.emit(0xA9, 0x20, 0x8D, 0x05, 0x43)  # DAS0L = $20
    asm.emit(0xA9, 0x02, 0x8D, 0x06, 0x43)  # DAS0H = $02 (544 bytes)
    asm.emit(0xA9, 0x01, 0x8D, 0x0B, 0x42)  # MDMAEN = channel 0

    # Modest dynamic VRAM update: 128 bytes from $7E2400 through channel 1.
    asm.emit(0xAF, 0x00, 0x00, 0x7E)        # animate VRAM destination with camera
    asm.emit(0x8D, 0x16, 0x21)              # VMADDL
    asm.emit(0xA9, 0x00, 0x8D, 0x17, 0x21)  # VMADDH
    asm.emit(0xA9, 0x01, 0x8D, 0x10, 0x43)  # DMAP1 = mode 1
    asm.emit(0xA9, 0x18, 0x8D, 0x11, 0x43)  # BBAD1 = $2118
    asm.emit(0xA9, 0x00, 0x8D, 0x12, 0x43)  # A1T1L = $00
    asm.emit(0xA9, 0x24, 0x8D, 0x13, 0x43)  # A1T1H = $24
    asm.emit(0xA9, 0x7E, 0x8D, 0x14, 0x43)  # A1B1 = $7E
    asm.emit(0xA9, 0x80, 0x8D, 0x15, 0x43)  # DAS1L = $80
    asm.emit(0xA9, 0x00, 0x8D, 0x16, 0x43)  # DAS1H = 0
    asm.emit(0xA9, 0x02, 0x8D, 0x0B, 0x42)  # MDMAEN = channel 1

    # Small palette refresh: 32 bytes from $7E2480 to CGRAM via channel 2.
    asm.emit(0xA9, 0x00, 0x8D, 0x21, 0x21)  # CGADD = 0
    asm.emit(0x8D, 0x20, 0x43)              # DMAP2 = mode 0
    asm.emit(0xA9, 0x22, 0x8D, 0x21, 0x43)  # BBAD2 = $2122
    asm.emit(0xA9, 0x80, 0x8D, 0x22, 0x43)  # A1T2L = $80
    asm.emit(0xA9, 0x24, 0x8D, 0x23, 0x43)  # A1T2H = $24
    asm.emit(0xA9, 0x7E, 0x8D, 0x24, 0x43)  # A1B2 = $7E
    asm.emit(0xA9, 0x20, 0x8D, 0x25, 0x43)  # DAS2L = 32
    asm.emit(0xA9, 0x00, 0x8D, 0x26, 0x43)  # DAS2H = 0
    asm.emit(0xA9, 0x04, 0x8D, 0x0B, 0x42)  # MDMAEN = channel 2

    asm.emit(0x7A, 0xFA, 0x68, 0x40)        # PLY; PLX; PLA; RTI

    program = asm.finish()
    if asm.labels["nmi"] != GAMEPLAY_NMI_OFFSET:
        raise ValueError("gameplay NMI handler moved away from its fixed vector")
    return program


WORKLOADS: dict[str, Callable[[], bytes]] = {
    "idle": workload_idle,
    "cpu-alu": workload_cpu_alu,
    "wram": workload_wram,
    "ppu-registers": workload_ppu_registers,
    "dma-vram": workload_dma_vram,
    "gameplay-balanced": workload_gameplay_balanced,
    "gameplay-window-hdma": workload_gameplay_window_hdma,
}


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def build_rom(name: str) -> bytes:
    try:
        program = WORKLOADS[name]()
    except KeyError as exc:
        raise ValueError(f"unknown workload: {name}") from exc

    if len(program) >= HEADER:
        raise ValueError(f"workload {name} is too large for the 32 KiB LoROM")

    rom = bytearray([0xEA]) * ROM_SIZE
    rom[: len(program)] = program

    if name == "gameplay-window-hdma":
        table = build_gameplay_window_hdma_table()
        table_offset = GAMEPLAY_WINDOW_TABLE_ADDRESS - LOAD_ADDRESS
        if len(program) > table_offset:
            raise ValueError("gameplay-window-hdma program overlaps HDMA table")
        if table_offset + len(table) >= HEADER:
            raise ValueError("gameplay-window-hdma HDMA table overlaps LoROM header")
        rom[table_offset : table_offset + len(table)] = table

    title = f"S64P {name.upper()}".encode("ascii")[:21]
    rom[HEADER : HEADER + 21] = title.ljust(21, b" ")
    rom[0x7FD5] = 0x20  # LoROM, slow ROM
    rom[0x7FD6] = 0x00  # ROM only
    rom[0x7FD7] = 0x05  # 32 KiB
    rom[0x7FD8] = 0x00  # no cartridge SRAM
    rom[0x7FD9] = 0x01  # NTSC region
    rom[0x7FDA] = 0x33  # extended maker code marker
    rom[0x7FDB] = 0x00  # version

    # Sodium64's header detector expects the native vector area not to look
    # identical to the reset-vector word. Native COP gets a distinct harmless
    # value; all emulation-mode vectors return to the workload entry point.
    write_vector(rom, 0x7FE4, 0x9000)
    for offset in (0x7FF4, 0x7FF6, 0x7FF8, 0x7FFA, 0x7FFC, 0x7FFE):
        write_vector(rom, offset, LOAD_ADDRESS)

    if name in ("gameplay-balanced", "gameplay-window-hdma"):
        # The workload enables NMI only after entering native mode and finishing
        # startup. Set both vectors defensively; the native vector is the one
        # used during the measured frame loop.
        write_vector(rom, 0x7FEA, GAMEPLAY_NMI_ADDRESS)
        write_vector(rom, 0x7FFA, GAMEPLAY_NMI_ADDRESS)

    # For a checksum/complement pair where the words XOR to $FFFF, the four
    # checksum bytes always contribute $1FE to the byte sum.
    rom[0x7FDC:0x7FE0] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    complement = checksum ^ 0xFFFF
    rom[0x7FDC:0x7FDE] = complement.to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")

    return bytes(rom)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="directory for generated .smc ROMs")
    parser.add_argument(
        "--only",
        choices=sorted(WORKLOADS),
        action="append",
        help="generate only this workload (repeatable); default: all",
    )
    args = parser.parse_args()

    names = args.only or list(WORKLOADS)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        output = args.output_dir / f"profile-{name}.smc"
        rom = build_rom(name)
        output.write_bytes(rom)
        print(f"wrote {name:17s} {len(rom)} bytes -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
