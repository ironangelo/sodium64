#!/usr/bin/env python3
"""Validate live RSP DMEM publication of overlay and raw-palette pointers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RAW1 = 0xA00EF000
RAW2 = 0xA00EF800


def parse_int(text: str) -> int:
    return int(text, 0)


def swapped32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("word_swap32 requires a multiple of four bytes")
    return b"".join(data[i:i + 4][::-1] for i in range(0, len(data), 4))


def words(data: bytes) -> list[int]:
    if len(data) != 16:
        raise ValueError(f"expected exactly 16 dump bytes, got {len(data)}")
    return [int.from_bytes(data[i:i + 4], "big") for i in range(0, 16, 4)]


def classify(data: bytes, overlay_main: int, overlay_mode7: int) -> dict[str, object]:
    expected = [overlay_main, overlay_mode7, RAW1, RAW2]
    candidates = {
        "canonical": data,
        "word_swap32": swapped32(data),
    }
    for mode, normalized in candidates.items():
        observed = words(normalized)
        if observed == expected:
            return {
                "passed": True,
                "classification": "RAW_PALETTE_DMEM_PUBLICATION_VALIDATED",
                "dump_normalization": mode,
                "observed": [f"0x{x:08X}" for x in observed],
                "expected": [f"0x{x:08X}" for x in expected],
            }
    return {
        "passed": False,
        "classification": "RAW_PALETTE_DMEM_PUBLICATION_MISMATCH",
        "observed_candidates": {
            mode: [f"0x{x:08X}" for x in words(normalized)]
            for mode, normalized in candidates.items()
        },
        "expected": [f"0x{x:08X}" for x in expected],
    }


def self_test() -> None:
    expected = [0x800B7A90, 0x800B9998, RAW1, RAW2]
    canonical = b"".join(x.to_bytes(4, "big") for x in expected)
    assert classify(canonical, expected[0], expected[1])["passed"]
    swapped = swapped32(canonical)
    got = classify(swapped, expected[0], expected[1])
    assert got["passed"] and got["dump_normalization"] == "word_swap32"
    bad = bytearray(canonical)
    bad[-1] ^= 1
    assert not classify(bytes(bad), expected[0], expected[1])["passed"]
    print("raw-palette DMEM publication classifier self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", nargs="?", type=Path)
    parser.add_argument("--expected-overlay-main", type=parse_int)
    parser.add_argument("--expected-overlay-mode7", type=parse_int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.dump is None or args.expected_overlay_main is None or args.expected_overlay_mode7 is None:
        parser.error("dump and both expected overlay addresses are required")
    result = classify(
        args.dump.read_bytes(),
        args.expected_overlay_main,
        args.expected_overlay_mode7,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
