#!/usr/bin/env python3
"""Classify the post-init DMEM publication block E90..E9F."""

from __future__ import annotations
import argparse, json
from pathlib import Path

EXPECTED_RAW = (0xA00EF000, 0xA00EF800)

def swap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("length must be divisible by 4")
    return b"".join(data[i:i+4][::-1] for i in range(0, len(data), 4))

def classify(data: bytes) -> dict[str, object]:
    if len(data) != 16:
        raise ValueError(f"expected 16 bytes, got {len(data)}")
    first = None
    for mode in ("identity", "word_swap32"):
        d = data if mode == "identity" else swap32(data)
        words = tuple(int.from_bytes(d[i:i+4], "big") for i in range(0, 16, 4))
        overlay_ok = (
            words[0] != 0 and words[1] != 0 and
            words[0] != words[1] and
            words[0] % 4 == 0 and words[1] % 4 == 0 and
            0x80000000 <= words[0] < 0x80800000 and
            0x80000000 <= words[1] < 0x80800000
        )
        raw_ok = words[2:] == EXPECTED_RAW
        passed = overlay_ok and raw_ok
        result = {
            "classification": "RAW_PALETTE_PTRS_PUBLISHED" if passed else "RAW_PALETTE_PTRS_FAILED",
            "passed": passed,
            "dump_normalization": mode,
            "overlay_main_src": f"0x{words[0]:08X}",
            "overlay_mode7_src": f"0x{words[1]:08X}",
            "raw_queue1": f"0x{words[2]:08X}",
            "raw_queue2": f"0x{words[3]:08X}",
            "overlay_pair_sane": overlay_ok,
            "raw_pair_exact": raw_ok,
        }
        if passed:
            return result
        if first is None:
            first = result
    assert first is not None
    return first

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump", type=Path)
    ap.add_argument("--output", type=Path)
    args=ap.parse_args()
    result=classify(args.dump.read_bytes())
    text=json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text+"\n", encoding="utf-8")
    return 0 if result["passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())
