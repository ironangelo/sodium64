#!/usr/bin/env python3
"""Generate a Gate-C worst-case whole-frame renderer-overlay cadence stress.

Original/homebrew-only ROM derived from the validated Mode1<->Mode7 diagnostic.
It keeps the same deterministic assets and state layout, but changes the phase
length from 60 frames to 1 frame so BGMODE alternates every NMI:

    Mode1 -> Mode7 -> Mode1 -> Mode7 -> ...

That forces one fixed-slot renderer overlay transfer per emulated frame. It is
a synthetic stress for real-N64 DMA/bus/cadence measurement, not a claim about
typical game switching frequency or Mode7 pixel fidelity.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import make_gate_c_mode7_switch as base


def build_rom() -> bytes:
    original = base.PHASE_FRAMES
    try:
        base.PHASE_FRAMES = 1
        return base.build_rom()
    finally:
        base.PHASE_FRAMES = original


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    rom = build_rom()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rom)
    print(f"wrote {len(rom)} bytes to {args.output}")
    print(f"sha256={hashlib.sha256(rom).hexdigest()}")
    print("phase_frames=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
