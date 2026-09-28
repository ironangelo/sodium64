#!/usr/bin/env python3
"""Generate clean four-state CGADSUB add/subtract/half discriminator guests."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from make_gate_c_hcomp_cgwsel_source import build_variant, finalize_checksum

CHECKSUM = slice(0x7FDC, 0x7FE0)
CGADSUB_SETUP = bytes((0xA9, 0x01, 0x8D, 0x31, 0x21))
MODES = {
    "add-full": 0x01,
    "add-half": 0x41,
    "sub-full": 0x81,
    "sub-half": 0xC1,
}


def hits(data: bytes | bytearray, pattern: bytes) -> list[int]:
    return [i for i in range(len(data)) if data.startswith(pattern, i)]


def build_mode(mode: str) -> bytes:
    raw = MODES[mode]
    base = build_variant(0x02)
    rom = bytearray(base)

    setup_hits = hits(base, CGADSUB_SETUP)
    if len(setup_hits) != 1:
        raise ValueError(f"expected one CGADSUB setup, found {setup_hits!r}")
    setup = setup_hits[0]
    rom[setup + 1] = raw
    finalize_checksum(rom)

    allowed = {setup + 1}
    diffs = {
        i for i, (a, b) in enumerate(zip(base, rom))
        if a != b and not (CHECKSUM.start <= i < CHECKSUM.stop)
    }
    if not diffs <= allowed:
        raise ValueError(f"unexpected semantic guest diffs: {sorted(diffs - allowed)!r}")
    return bytes(rom)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", type=Path)
    ap.add_argument("--mode", choices=tuple(MODES), required=True)
    args = ap.parse_args()

    data = build_mode(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"mode={args.mode}")
    print(f"cgadsub=0x{MODES[args.mode]:02X}")
    print("cgwsel=0x02")
    print(f"size={len(data)}")
    print("sha256=" + hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
