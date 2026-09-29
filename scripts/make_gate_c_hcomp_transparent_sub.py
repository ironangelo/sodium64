#!/usr/bin/env python3
"""Generate transparent-Sub fallback/HALF discriminator guests."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from make_gate_c_hcomp_cgwsel_source import build_variant, finalize_checksum, hits
from make_gate_c_hcomp_main_sub_lifetime import (
    HDMA_TS_TABLE_ADDRESS, LOAD_ADDRESS, build_hdma_ts_table,
)

CGADSUB_SETUP = bytes((0xA9, 0x01, 0x8D, 0x31, 0x21))
TS_BG2_SETUP = bytes((0xA9, 0x02, 0x8D, 0x2D, 0x21))

MODES = {
    "fixed-half": (0x00, False),
    "sub-present-half": (0x02, False),
    "sub-absent-half": (0x02, True),
}


def absent_hdma_table() -> bytes:
    """Preserve the lifetime table shape while forcing TS=0 in every block."""
    table = bytearray(build_hdma_ts_table())
    offset = 0
    while True:
        header = table[offset]
        if header == 0:
            break
        count = header & 0x7F
        offset += 1
        table[offset:offset + count] = bytes(count)
        offset += count
    return bytes(table)


def build_mode(mode: str) -> bytes:
    if mode not in MODES:
        raise ValueError(mode)
    cgwsel, absent = MODES[mode]
    rom = bytearray(build_variant(cgwsel))

    cg_hits = hits(rom, CGADSUB_SETUP)
    if len(cg_hits) != 1:
        raise ValueError(f"expected one CGADSUB setup, found {cg_hits!r}")
    rom[cg_hits[0] + 1] = 0x41  # BG1 eligible + HALF, ADD operation.

    ts_hits = hits(rom, TS_BG2_SETUP)
    if len(ts_hits) != 2:
        raise ValueError(f"expected startup+NMI TS=BG2 writes, found {ts_hits!r}")
    if absent:
        for off in ts_hits:
            rom[off + 1] = 0x00

        # This guest inherits the lifetime discriminator's direct HDMA table,
        # which otherwise re-enables BG2 on TS for the first eight visible
        # lines even after the startup/NMI writes above are cleared.  Preserve
        # the exact table headers/length but force every transferred TS value
        # to zero so the absent state has no hidden real-Sub interval.
        table_offset = HDMA_TS_TABLE_ADDRESS - LOAD_ADDRESS
        original = build_hdma_ts_table()
        if bytes(rom[table_offset:table_offset + len(original)]) != original:
            raise ValueError("inherited TS HDMA table drifted")
        rom[table_offset:table_offset + len(original)] = absent_hdma_table()

    finalize_checksum(rom)
    return bytes(rom)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=tuple(MODES), required=True)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    data = build_mode(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    cgwsel, absent = MODES[args.mode]
    print(f"mode={args.mode}")
    print(f"cgwsel=0x{cgwsel:02X}")
    print("cgadsub=0x41")
    print(f"sub_present={0 if absent else 1}")
    print("fixed_rgb555=0x7C00")
    print(f"size={len(data)}")
    print("sha256=" + hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
