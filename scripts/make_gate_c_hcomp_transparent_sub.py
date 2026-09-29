#!/usr/bin/env python3
"""Generate transparent-Sub fallback/HALF discriminator guests."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from make_gate_c_hcomp_cgwsel_source import (
    HOOK_OFFSET, NMI_OFFSET, build_variant, finalize_checksum, hits,
)
from make_gate_c_hcomp_main_sub_lifetime import (
    HDMA_TS_TABLE_ADDRESS, LOAD_ADDRESS, build_hdma_ts_table,
)

CGADSUB_SETUP = bytes((0xA9, 0x01, 0x8D, 0x31, 0x21))
TS_BG2_SETUP = bytes((0xA9, 0x02, 0x8D, 0x2D, 0x21))
HDMA_TS_TARGET_SETUP = bytes((0xA9, 0x2D, 0x8D, 0x01, 0x43))

MODES = {
    "fixed-half": (0x00, False),
    "sub-present-half": (0x02, False),
    "sub-absent-half": (0x02, True),
}


def absent_split_hdma_table() -> bytes:
    """Keep the 8-line section split without ever enabling a Sub layer."""
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
            # HDMA is retargeted to WH0 below. TSW/TMW stay disabled, so WH0
            # is semantically inert here; the 0->1 edge at line8 exists only
            # to preserve the compact proof surface's audited 8-row lifetime.
            table[offset + i] = 0 if line + i < 8 else 1
        line += count
        offset += count
    if line != 224:
        raise ValueError(f"unexpected inherited HDMA visible length {line}")
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

        # The compact clean proof owns only eight Sub rows. Do not remove that
        # section boundary: a 224-line first section would overrun the bounded
        # proof surface. Retarget inherited HDMA from TS to WH0 and make WH0
        # change 0->1 at line8. Windows are disabled (TSW=TMW=0), so this
        # creates only the raster split while TS remains zero for the frame.
        target_hits = hits(rom, HDMA_TS_TARGET_SETUP)
        if len(target_hits) != 1:
            raise ValueError(f"expected one HDMA TS target setup, found {target_hits!r}")
        rom[target_hits[0] + 1] = 0x26  # WH0 ($2126), inert with windows disabled.

        # Explicitly initialize WH0=0 in the existing proof-hook padding and
        # move RTS to the final byte without moving the frozen NMI at $8200.
        hook = bytes((
            0xA9, cgwsel, 0x8D, 0x30, 0x21,
            0xA9, 0x9F, 0x8D, 0x32, 0x21,
            0x60,
        )) + bytes((0xEA,)) * (NMI_OFFSET - HOOK_OFFSET - 11)
        if bytes(rom[HOOK_OFFSET:NMI_OFFSET]) != hook:
            raise ValueError("CGWSEL proof hook drifted before absent split setup")
        absent_hook = bytes((
            0xA9, cgwsel, 0x8D, 0x30, 0x21,
            0xA9, 0x9F, 0x8D, 0x32, 0x21,
            0xA9, 0x00, 0x8D, 0x26, 0x21,
            0x60,
        ))
        if len(absent_hook) != NMI_OFFSET - HOOK_OFFSET:
            raise ValueError("absent proof hook no longer fills the frozen padding")
        rom[HOOK_OFFSET:NMI_OFFSET] = absent_hook

        table_offset = HDMA_TS_TABLE_ADDRESS - LOAD_ADDRESS
        original = build_hdma_ts_table()
        if bytes(rom[table_offset:table_offset + len(original)]) != original:
            raise ValueError("inherited TS HDMA table drifted")
        rom[table_offset:table_offset + len(original)] = absent_split_hdma_table()

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
