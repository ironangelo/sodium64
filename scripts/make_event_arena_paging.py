#!/usr/bin/env python3
"""Original 4 MiB LoROM: read 640 pages through the real cart paging path."""
import argparse
from pathlib import Path
from make_gate_c_hcomp_cgwsel_source import finalize_checksum


def build():
    rom = bytearray([0xea]) * 0x400000
    for page in range(512):
        pos = page*8192 + 0x1f00
        rom[pos:pos+2] = (0x1234+page).to_bytes(2, 'little')
    code = bytearray([0x78, 0x18, 0xfb, 0xc2, 0x30])  # native M16/X16
    code += bytes([0xa9, 0x55, 0xaa, 0x8f, 0, 0x10, 0x7e])
    patches = []
    for page in list(range(512)) + list(range(128)):
        address = ((0x80+page//4)<<16) | (0x8000+(page%4)*8192+0x1f00)
        code += bytes([0xaf])+address.to_bytes(3, 'little')
        code += bytes([0xc9])+(0x1234+page).to_bytes(2, 'little')
        code += bytes([0xf0, 3, 0x4c, 0, 0])
        patches.append(len(code)-2)
    code += bytes([0xa9, 0xde, 0xc0, 0x8f, 0, 0x10, 0x7e, 0x80, 0xfe])
    fail = 0x8000+len(code)
    code += bytes([0x8f, 2, 0x10, 0x7e, 0xa9, 0xd0, 0xba,
                   0x8f, 0, 0x10, 0x7e, 0x80, 0xfe])
    for patch in patches:
        code[patch:patch+2] = fail.to_bytes(2, 'little')
    assert len(code) < 0x1f00, len(code)
    rom[:len(code)] = code
    rom[0x7fc0:0x7fd5] = b'S64 ARENA ROM PAGING'.ljust(21, b' ')
    rom[0x7fd5:0x7fdc] = bytes([0x20, 0, 12, 0, 1, 0x33, 0])
    rom[0x7fe4:0x7fe6] = (0x9000).to_bytes(2, 'little')
    for pos in (0x7ff4, 0x7ff6, 0x7ff8, 0x7ffa, 0x7ffc, 0x7ffe):
        rom[pos:pos+2] = (0x8000).to_bytes(2, 'little')
    finalize_checksum(rom)
    return bytes(rom)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build())
