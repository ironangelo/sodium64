#!/usr/bin/env python3
"""Generate a tiny original LoROM image for Sodium64 integration smoke tests.

The ROM contains no copyrighted game data. Its 65C816 program enters a tight
BRA loop after reset; Sodium64 still advances its APU/PPU/event machinery around
that guest CPU execution, which is enough to exercise emulator startup and the
statistical R4300 profiler.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROM_SIZE = 0x8000  # 32 KiB LoROM
HEADER = 0x7FC0


def write_vector(rom: bytearray, offset: int, address: int) -> None:
    rom[offset : offset + 2] = address.to_bytes(2, "little")


def build_rom() -> bytes:
    # Fill unused ROM with 65C816 NOPs so accidental execution is benign.
    rom = bytearray([0xEA]) * ROM_SIZE

    # $00:8000: SEI; CLC; XCE; BRA -2
    # XCE leaves reset emulation mode in a deterministic way before the loop.
    rom[0:5] = bytes([0x78, 0x18, 0xFB, 0x80, 0xFE])

    title = b"SODIUM64 PROF SMOKE"
    rom[HEADER : HEADER + 21] = title.ljust(21, b" ")
    rom[0x7FD5] = 0x20  # LoROM, slow ROM
    rom[0x7FD6] = 0x00  # ROM only
    rom[0x7FD7] = 0x05  # 32 KiB
    rom[0x7FD8] = 0x00  # no cartridge SRAM
    rom[0x7FD9] = 0x01  # NTSC region
    rom[0x7FDA] = 0x33  # extended maker code marker
    rom[0x7FDB] = 0x00  # version

    # Sodium64's header detector additionally requires the native vector area
    # not to look identical to the reset-vector word. Give native COP a distinct
    # harmless value while all emulation-mode vectors point at our loop.
    write_vector(rom, 0x7FE4, 0x9000)
    for offset in (0x7FF4, 0x7FF6, 0x7FF8, 0x7FFA, 0x7FFC, 0x7FFE):
        write_vector(rom, offset, 0x8000)

    # Populate a valid complement/checksum pair. With the four checksum bytes
    # temporarily zero, the final checksum+complement pair contributes 0x1FE to
    # the byte sum because the two 16-bit values XOR to 0xFFFF.
    rom[0x7FDC:0x7FE0] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    complement = checksum ^ 0xFFFF
    rom[0x7FDC:0x7FDE] = complement.to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")

    return bytes(rom)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="output .smc path")
    args = parser.parse_args()

    rom = build_rom()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rom)
    print(f"wrote {len(rom)} bytes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
