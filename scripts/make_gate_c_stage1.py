#!/usr/bin/env python3
"""Original Stage 1 guests. No assets from commercial ROMs."""
from pathlib import Path
import argparse
import hashlib
from make_gate_c_hcomp_color_window import build_case, WINDOW_HOOK_OFFSET
from make_gate_c_hcomp_transparent_sub import build_mode
from make_gate_c_hcomp_cgwsel_source import finalize_checksum

MODES = ('fixed', 'absent', 'control', 'clip', 'prevent', 'both')


def build(mode):
    if mode in ('fixed', 'absent'):
        return build_mode({'fixed': 'fixed-half', 'absent': 'sub-absent-half'}[mode])
    rom = bytearray(build_case(mode + '-inside'))
    # WH0/WH1 are the fourth/fifth immediate stores in the verified hook.
    rom[WINDOW_HOOK_OFFSET + 3 * 5 + 1] = 64
    rom[WINDOW_HOOK_OFFSET + 4 * 5 + 1] = 191
    finalize_checksum(rom)
    return bytes(rom)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', choices=MODES, required=True)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    data = build(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(args.mode, hashlib.sha256(data).hexdigest())


if __name__ == '__main__':
    main()
