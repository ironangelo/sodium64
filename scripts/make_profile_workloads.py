#!/usr/bin/env python3
"""Generate original deterministic SNES ROMs for Sodium64 profiling.

The workloads contain no copyrighted game data. Each ROM stresses a different
part of the SNES execution path while remaining tiny and deterministic:

- idle: minimal native-mode branch loop;
- cpu-alu: arithmetic/branch-heavy 65C816 execution;
- wram: long-indexed WRAM reads and writes;
- ppu-registers: repeated CGRAM/scroll register updates;
- dma-vram: repeated 4 KiB DMA transfers from WRAM to VRAM.

These are diagnostic workloads, not substitutes for commercial-game milestone
validation. Their value is that differences between profiles are attributable to
known changes in guest work and can be reproduced in CI without ROM assets.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

ROM_SIZE = 0x8000  # 32 KiB LoROM
HEADER = 0x7FC0
LOAD_ADDRESS = 0x8000


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


WORKLOADS: dict[str, Callable[[], bytes]] = {
    "idle": workload_idle,
    "cpu-alu": workload_cpu_alu,
    "wram": workload_wram,
    "ppu-registers": workload_ppu_registers,
    "dma-vram": workload_dma_vram,
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
        print(f"wrote {name:13s} {len(rom)} bytes -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
