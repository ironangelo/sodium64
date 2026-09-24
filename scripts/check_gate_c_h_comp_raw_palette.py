#!/usr/bin/env python3
"""Classify the Gate-C H-COMP raw-palette shadow queue dumps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RAW_WORDS = (0xF801, 0x07C1, 0x003F, 0xFFFF)
VISIBLE_WORDS = (0x7801, 0x03C1, 0x001F, 0x7BDF)
ENTRY_SIZE = 8


def swap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("dump length must be divisible by 4")
    return b"".join(data[i:i+4][::-1] for i in range(0, len(data), 4))


def expected_entry(word: int) -> bytes:
    return word.to_bytes(2, "big") * 4


def inspect_queue(data: bytes, expected_words: tuple[int, ...]) -> dict[str, object]:
    entries = []
    passed = True
    for index, word in enumerate(expected_words, start=1):
        start = index * ENTRY_SIZE
        got = data[start:start+ENTRY_SIZE]
        exp = expected_entry(word)
        ok = got == exp
        passed &= ok
        entries.append({
            "index": index,
            "expected": f"0x{word:04X}",
            "actual_hex": got.hex(),
            "passed": ok,
        })
    return {"passed": passed, "entries": entries}


def classify(paths: list[Path]) -> dict[str, object]:
    raw = [p.read_bytes() for p in paths]
    if any(len(x) < 0x28 for x in raw):
        raise ValueError("all dumps must contain at least 0x28 bytes")

    chosen = None
    result = None
    for mode in ("identity", "word_swap32"):
        data = raw if mode == "identity" else [swap32(x) for x in raw]
        checks = {
            "raw_queue1": inspect_queue(data[0], RAW_WORDS),
            "raw_queue2": inspect_queue(data[1], RAW_WORDS),
            "visible_queue1": inspect_queue(data[2], VISIBLE_WORDS),
            "visible_queue2": inspect_queue(data[3], VISIBLE_WORDS),
        }
        both_raw_equal = data[0][8:40] == data[1][8:40]
        both_visible_equal = data[2][8:40] == data[3][8:40]
        passed = all(v["passed"] for v in checks.values()) and both_raw_equal and both_visible_equal
        candidate = {
            "classification": "RAW_PALETTE_SHADOW_VALIDATED" if passed else "RAW_PALETTE_SHADOW_FAILED",
            "passed": passed,
            "dump_normalization": mode,
            "queue_pairs_equal": {
                "raw": both_raw_equal,
                "visible": both_visible_equal,
            },
            "checks": checks,
        }
        if passed:
            chosen, result = mode, candidate
            break
        if result is None:
            result = candidate

    assert result is not None
    return result


def self_test() -> None:
    def queue(words: tuple[int, ...]) -> bytes:
        data = bytearray(0x30)
        for index, word in enumerate(words, start=1):
            data[index*8:index*8+8] = expected_entry(word)
        return bytes(data)

    canon = [queue(RAW_WORDS), queue(RAW_WORDS), queue(VISIBLE_WORDS), queue(VISIBLE_WORDS)]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        files = []
        for i, data in enumerate(canon):
            p = td / f"c{i}.bin"
            p.write_bytes(data)
            files.append(p)
        assert classify(files)["passed"]
        for i, data in enumerate(canon):
            files[i].write_bytes(swap32(data))
        r = classify(files)
        assert r["passed"] and r["dump_normalization"] == "word_swap32"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_queue1", type=Path, nargs="?")
    parser.add_argument("raw_queue2", type=Path, nargs="?")
    parser.add_argument("visible_queue1", type=Path, nargs="?")
    parser.add_argument("visible_queue2", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("raw-palette classifier self-test: PASS")
        return 0

    paths = [args.raw_queue1, args.raw_queue2, args.visible_queue1, args.visible_queue2]
    if any(p is None for p in paths):
        parser.error("four dump paths are required unless --self-test is used")

    result = classify(paths)  # type: ignore[arg-type]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
