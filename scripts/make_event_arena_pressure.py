#!/usr/bin/env python3
"""Separate original stress guest: active-display DMA produces 16384 colors/frame."""
import argparse
from pathlib import Path
from make_gate_c_stage1 import build
from make_gate_c_hcomp_main_sub_lifetime import Assembler, lda_sta_abs
from make_gate_c_hcomp_cgwsel_source import finalize_checksum


def build_pressure():
    rom = bytearray(build('visual'))
    loop = bytes([0xcb, 0x80, 0xfd])
    assert rom.count(loop) == 1
    offset = rom.index(loop)
    rom[offset:offset+3] = bytes([0x4c, 0, 0x88])
    a = Assembler()
    a.label('frame')
    a.emit(0xcb)  # NMI occurs during VBlank; palette burst waits for active scan.
    a.label('active')
    a.emit(0xad, 0x12, 0x42, 0x29, 0x80)
    a.branch(0xd0, 'active')
    for port, value in ((0x2121, 0), (0x4310, 0), (0x4311, 0x22),
                        (0x4312, 0), (0x4313, 0x80), (0x4314, 0),
                        (0x4315, 0), (0x4316, 0x80), (0x420b, 2)):
        lda_sta_abs(a, value, port)
    a.emit(0xaf, 0x10, 0x10, 0x7e, 0x1a, 0x8f, 0x10, 0x10, 0x7e)
    a.branch(0x80, 'frame')
    code = a.finish()
    assert len(code) < 0x100
    rom[0x800:0x800+len(code)] = code
    rom[0x7fc0:0x7fd5] = b'S64 ARENA PRESSURE'.ljust(21, b' ')
    finalize_checksum(rom)
    return bytes(rom)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build_pressure())
