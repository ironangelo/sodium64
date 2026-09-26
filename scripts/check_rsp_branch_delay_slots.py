#!/usr/bin/env python3
"""Reject RSP binaries containing a control transfer in another control transfer's delay slot."""

from __future__ import annotations

import argparse
import struct
import tempfile
from pathlib import Path


def read_text(path: Path) -> tuple[int, bytes]:
    data = path.read_bytes()
    if len(data) < 52 or data[:4] != b"\\x7fELF" or data[4] != 1:
        raise ValueError(f"{path}: expected ELF32")
    endian = ">" if data[5] == 2 else "<" if data[5] == 1 else None
    if endian is None:
        raise ValueError(f"{path}: unsupported ELF byte order")
    hdr = struct.unpack(endian + "16sHHIIIIIHHHHHH", data[:52])
    shoff, shentsize, shnum, shstrndx = hdr[6], hdr[11], hdr[12], hdr[13]
    if shentsize < 40 or shnum == 0 or shstrndx >= shnum:
        raise ValueError(f"{path}: invalid section table")

    sections = []
    for i in range(shnum):
        off = shoff + i * shentsize
        sections.append(struct.unpack(endian + "IIIIIIIIII", data[off:off + 40]))
    shstr = sections[shstrndx]
    names = data[shstr[4]:shstr[4] + shstr[5]]

    for sec in sections:
        name_off = sec[0]
        end = names.find(b"\\0", name_off)
        if end < 0:
            continue
        name = names[name_off:end].decode("ascii", errors="replace")
        if name == ".text":
            addr, off, size = sec[3], sec[4], sec[5]
            text = data[off:off + size]
            if len(text) != size or size % 4:
                raise ValueError(f"{path}: malformed .text")
            return addr, text
    raise ValueError(f"{path}: .text not found")


def is_control(word: int) -> bool:
    op = (word >> 26) & 0x3F
    if op in (1, 2, 3, 4, 5, 6, 7):
        return True
    if op == 0 and (word & 0x3F) in (8, 9):  # JR / JALR
        return True
    return False


def hazards(path: Path) -> list[tuple[int, int, int]]:
    base, text = read_text(path)
    out = []
    for off in range(0, len(text) - 4, 4):
        first = int.from_bytes(text[off:off + 4], "big")
        delay = int.from_bytes(text[off + 4:off + 8], "big")
        if is_control(first) and is_control(delay):
            out.append((base + off, first, delay))
    return out


def self_test() -> None:
    assert is_control(0x10000000)  # beq
    assert is_control(0x08000000)  # j
    assert is_control(0x00000008)  # jr
    assert not is_control(0x00000000)
    assert not is_control(0x22310008)  # addi s1,s1,8


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("elf", type=Path, nargs="*")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        print("RSP branch-delay classifier self-test: PASS")
        if not args.elf:
            return 0
    if not args.elf:
        ap.error("at least one RSP ELF is required")

    failed = False
    for path in args.elf:
        found = hazards(path)
        if found:
            failed = True
            for addr, first, delay in found:
                print(f"{path}: CONTROL_IN_DELAY_SLOT at {addr:#010x}: {first:08x} -> {delay:08x}")
        else:
            base, text = read_text(path)
            print(f"{path}: PASS base={base:#010x} text={len(text):#x} control-in-delay=0")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
