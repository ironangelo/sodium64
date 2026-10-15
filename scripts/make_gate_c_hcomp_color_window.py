#!/usr/bin/env python3
"""Original eight-case color-window guest; frozen Main/Sub and HDMA geometry."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from make_gate_c_hcomp_transparent_sub import build_mode
from make_gate_c_hcomp_cgwsel_source import HOOK_OFFSET, NMI_OFFSET, finalize_checksum

WINDOW_HOOK_OFFSET = 0x1A0
CASES = {
    f"{name}-{side}": {"cgwsel": value, "left": edge, "right": edge}
    for name, value in (("control", 0x02), ("clip", 0x82),
                        ("prevent", 0x22), ("both", 0xA2))
    for side, edge in (("inside", 0), ("outside", 1))
}


def build_case(case: str) -> bytes:
    cfg = CASES[case]
    base = build_mode("sub-present-half")
    rom = bytearray(base)
    old_hook = bytes((0xA9, 2, 0x8D, 0x30, 0x21,
                      0xA9, 0x9F, 0x8D, 0x32, 0x21, 0x60)) + b"\xEA" * 5
    if rom[HOOK_OFFSET:NMI_OFFSET] != old_hook:
        raise ValueError("validated source hook drift")
    # Layer windows stay disabled. Color window has its own WOBJSEL high
    # nibble and is independently active despite TMW=TSW=0.
    setup = ((cfg["cgwsel"], 0x2130), (0x9F, 0x2132),
             (0x20, 0x2125), (cfg["left"], 0x2126),
             (cfg["right"], 0x2127), (0, 0x2128), (0, 0x2129), (0, 0x212B))
    hook = bytes(v for value, address in setup
                 for v in (0xA9, value, 0x8D, address & 255, address >> 8)) + b"\x60"
    end = WINDOW_HOOK_OFFSET + len(hook)
    if end > HOOK_OFFSET or rom[WINDOW_HOOK_OFFSET:end] != b"\xEA" * len(hook):
        raise ValueError("window setup exceeds verified unused startup padding")
    rom[WINDOW_HOOK_OFFSET:end] = hook
    address = 0x8000 + WINDOW_HOOK_OFFSET
    rom[HOOK_OFFSET:NMI_OFFSET] = bytes((0x20, address & 255, address >> 8, 0x60)) + b"\xEA" * 12
    finalize_checksum(rom)
    allowed = set(range(WINDOW_HOOK_OFFSET, end)) | set(range(HOOK_OFFSET, NMI_OFFSET)) | set(range(0x7FDC, 0x7FE0))
    if any(i not in allowed for i, (x, y) in enumerate(zip(base, rom)) if x != y):
        raise ValueError("guest changed outside controlled hook/checksum slots")
    if len(rom) != 32768:
        raise ValueError("guest size drift")
    return bytes(rom)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True, choices=tuple(CASES))
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    data = build_case(args.case)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"case={args.case} config={CASES[args.case]} sha256={hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
