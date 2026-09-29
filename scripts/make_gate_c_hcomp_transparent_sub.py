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
HDMA_TS_DEST_SETUP = bytes((0xA9, 0x2D, 0x8D, 0x01, 0x43))

MODES = {
    "fixed-half": (0x00, False),
    "sub-present-half": (0x02, False),
    "sub-absent-half": (0x02, True),
}


def absent_hdma_table() -> bytes:
    """Keep the line-8 section split without ever writing TS in absent mode."""
    table = bytearray(build_hdma_ts_table())
    offset = 0
    line = 0
    while True:
        header = table[offset]
        if header == 0:
            break
        count = header & 0x7F
        offset += 1
        for i in range(count):
            # Retargeted to WH0: keep its reset value through lines 0..7,
            # then change once at line 8. Window enables are zero, so this is
            # a section-boundary carrier only and cannot mask any pixels.
            table[offset + i] = 0x00 if line < 8 else 0x01
            line += 1
        offset += count
    if line != 224:
        raise ValueError(f"unexpected inherited HDMA line count: {line}")
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
        startup_ts, nmi_ts = ts_hits
        rom[startup_ts + 1] = 0x00  # TS starts and remains disabled.

        # TS no longer changes in the NMI path, so reuse the same-size write to
        # restore harmless WH0=0 before each frame. The retargeted HDMA below
        # changes WH0 only at line 8, preserving the compact proof geometry.
        rom[nmi_ts:nmi_ts + len(TS_BG2_SETUP)] = bytes((
            0xA9, 0x00, 0x8D, 0x26, 0x21,
        ))

        dest_hits = hits(rom, HDMA_TS_DEST_SETUP)
        if len(dest_hits) != 1:
            raise ValueError(f"expected one TS HDMA destination setup, found {dest_hits!r}")
        rom[dest_hits[0] + 1] = 0x26  # $2126 WH0; window enables stay disabled.

        table_offset = HDMA_TS_TABLE_ADDRESS - LOAD_ADDRESS
        original = build_hdma_ts_table()
        if bytes(rom[table_offset:table_offset + len(original)]) != original:
            raise ValueError("inherited TS HDMA table drifted")
        replacement = absent_hdma_table()
        rom[table_offset:table_offset + len(original)] = replacement

        # Deterministic construction guards: no instruction/HDMA destination
        # may re-enable BG2 on TS, and the harmless WH0 carrier must split at 8.
        if hits(rom, TS_BG2_SETUP):
            raise ValueError("absent guest still contains a TS=BG2 write")
        if hits(rom, HDMA_TS_DEST_SETUP):
            raise ValueError("absent guest still targets TS with HDMA")
        payload = []
        offset = 0
        while replacement[offset] != 0:
            count = replacement[offset] & 0x7F
            offset += 1
            payload.extend(replacement[offset:offset + count])
            offset += count
        if payload[:8] != [0] * 8 or payload[8:] != [1] * (len(payload) - 8):
            raise ValueError("WH0 section-boundary carrier drifted")

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
