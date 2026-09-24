#!/usr/bin/env python3
"""Validate live H-COMP raw-palette pointer publication in RSP DMEM."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

def swap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("dump length must be divisible by 4")
    return b"".join(data[i:i+4][::-1] for i in range(0, len(data), 4))

def symbols(elf: Path) -> dict[str, int]:
    out = subprocess.check_output(["nm", "-n", str(elf)], text=True)
    wanted = {"rsp_main_text_start", "rsp_mode7_text_start"}
    result: dict[str, int] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] in wanted:
            result[parts[2]] = int(parts[0], 16)
    missing = wanted - result.keys()
    if missing:
        raise RuntimeError(f"missing ELF symbols: {sorted(missing)}")
    return result

def classify(elf: Path, dump: Path) -> dict[str, object]:
    raw = dump.read_bytes()
    if len(raw) < 16:
        raise ValueError("DMEM dump must contain at least 16 bytes")
    syms = symbols(elf)
    expected = (
        syms["rsp_main_text_start"] + 0x3A8,
        syms["rsp_mode7_text_start"] + 0x3A8,
        0xA00EF000,
        0xA00EF800,
    )
    first = None
    for mode in ("identity", "word_swap32"):
        data = raw[:16] if mode == "identity" else swap32(raw[:16])
        observed = tuple(int.from_bytes(data[i:i+4], "big") for i in range(0, 16, 4))
        passed = observed == expected
        result = {
            "classification": "RAW_PALETTE_PTRS_LIVE_VALIDATED" if passed else "RAW_PALETTE_PTRS_LIVE_FAILED",
            "passed": passed,
            "dump_normalization": mode,
            "observed": [f"0x{x:08X}" for x in observed],
            "expected": [f"0x{x:08X}" for x in expected],
            "labels": ["overlay_main", "overlay_mode7", "raw_queue1", "raw_queue2"],
        }
        if passed:
            return result
        if first is None:
            first = result
    assert first is not None
    return first

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)
        # Use a tiny fake nm executable so self-test exercises both dump formats.
        elf = td / "fake.elf"
        elf.write_bytes(b"x")
        nm = td / "nm"
        nm.write_text(
            "#!/bin/sh\n"
            "echo '80001000 D rsp_main_text_start'\n"
            "echo '80003000 D rsp_mode7_text_start'\n",
            encoding="utf-8",
        )
        nm.chmod(0o755)
        import os
        old = os.environ.get("PATH", "")
        os.environ["PATH"] = str(td) + os.pathsep + old
        try:
            expected = [0x800013A8, 0x800033A8, 0xA00EF000, 0xA00EF800]
            canonical = b"".join(x.to_bytes(4, "big") for x in expected)
            p = td / "dump.bin"
            p.write_bytes(canonical)
            assert classify(elf, p)["passed"]
            p.write_bytes(swap32(canonical))
            r = classify(elf, p)
            assert r["passed"] and r["dump_normalization"] == "word_swap32"
            bad = bytearray(canonical)
            bad[-1] ^= 1
            p.write_bytes(bytes(bad))
            assert not classify(elf, p)["passed"]
        finally:
            os.environ["PATH"] = old

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("elf", type=Path, nargs="?")
    ap.add_argument("dump", type=Path, nargs="?")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        print("raw-palette live-pointer classifier self-test: PASS")
        return 0
    if args.elf is None or args.dump is None:
        ap.error("ELF and DMEM dump are required unless --self-test is used")
    result = classify(args.elf, args.dump)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
