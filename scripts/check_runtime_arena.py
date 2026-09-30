#!/usr/bin/env python3
"""Reject linked runtime sections overlapping the uncached renderer arena."""
import argparse
import re
import struct
from pathlib import Path


def allocated_sections(path):
    data = Path(path).read_bytes()
    if data[:4] != b'\x7fELF' or data[4] not in (1, 2):
        raise ValueError('expected ELF32/ELF64')
    endian = '>' if data[5] == 2 else '<'
    hfmt, sfmt = ('16sHHIIIIIHHHHHH', 'IIIIIIIIII') if data[4] == 1 else ('16sHHIQQQIHHHHHH', 'IIQQQQIIQQ')
    h = struct.unpack_from(endian + hfmt, data)
    secs = [struct.unpack_from(endian + sfmt, data, h[6] + i*h[11]) for i in range(h[12])]
    strings = secs[h[13]]
    names = data[strings[4]:strings[4]+strings[5]]
    for sec in secs:
        if sec[2] & 2 and sec[5]:  # SHF_ALLOC, including NOBITS
            name = names[sec[0]:].split(b'\0', 1)[0].decode()
            start = sec[3] & 0x1fffffff
            yield name, start, start + sec[5]


def check(elf, start, end=0x1c0000):
    overlaps = [(name, a, b) for name, a, b in allocated_sections(elf)
                if a < end and b > start]
    if overlaps:
        raise ValueError(f'{elf}: runtime overlaps boot-clear/renderer arena [{start:#x},{end:#x}): {overlaps}')
    return max(b for _, _, b in allocated_sections(elf))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('elf', type=Path)
    ap.add_argument('--defines', type=Path, default=Path('src/defines.h'))
    ap.add_argument('--arena-start', type=lambda s: int(s, 0))
    args = ap.parse_args()
    start = args.arena_start
    if start is None:
        m = re.search(r'^#define HCOMP_CGRAM_BASE_QUEUE1 (0x[0-9A-Fa-f]+)$', args.defines.read_text(), re.M)
        if not m:
            raise ValueError('missing literal arena start')
        start = int(m[1], 0) & 0x1fffffff
    end = check(args.elf, start)
    print(f'RUNTIME_ARENA_DISJOINT PASS: allocated_end={end:#x}, arena_start={start:#x}, gap={start-end:#x}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, struct.error) as e:
        raise SystemExit(str(e))
