#!/usr/bin/env python3
"""Classify alternating-frame raw/visible palette queue ownership."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import tempfile

ENTRY_SIZE = 8
PHASES = {
    "red":   (0xF801, 0x7801),
    "green": (0x07C1, 0x03C1),
}
FIXED = {
    2: (0x003F, 0x001F),  # blue
    3: (0xFFFF, 0x7BDF),  # white
}

def swap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("dump length must be divisible by 4")
    return b"".join(data[i:i+4][::-1] for i in range(0, len(data), 4))

def expected_entry(word: int) -> bytes:
    return word.to_bytes(2, "big") * 4

def entry(data: bytes, index: int) -> bytes:
    start = index * ENTRY_SIZE
    return data[start:start+ENTRY_SIZE]

def phase_for(raw: bytes, visible: bytes) -> str | None:
    for name, (rw, vw) in PHASES.items():
        if entry(raw, 1) == expected_entry(rw) and entry(visible, 1) == expected_entry(vw):
            return name
    return None

def fixed_ok(raw: bytes, visible: bytes) -> bool:
    return all(
        entry(raw, idx) == expected_entry(rw)
        and entry(visible, idx) == expected_entry(vw)
        for idx, (rw, vw) in FIXED.items()
    )

def classify(paths: list[Path]) -> dict[str, object]:
    dumps = [p.read_bytes() for p in paths]
    if any(len(x) < 0x20 for x in dumps):
        raise ValueError("all dumps must contain at least 0x20 bytes")

    first_failure = None
    for mode in ("identity", "word_swap32"):
        data = dumps if mode == "identity" else [swap32(x) for x in dumps]
        raw1, raw2, vis1, vis2 = data
        q1_phase = phase_for(raw1, vis1)
        q2_phase = phase_for(raw2, vis2)
        q1_fixed = fixed_ok(raw1, vis1)
        q2_fixed = fixed_ok(raw2, vis2)
        opposite = {q1_phase, q2_phase} == {"red", "green"}
        passed = bool(q1_fixed and q2_fixed and opposite)
        result = {
            "classification": "RAW_PALETTE_OWNERSHIP_VALIDATED" if passed else "RAW_PALETTE_OWNERSHIP_FAILED",
            "passed": passed,
            "dump_normalization": mode,
            "queue1_phase": q1_phase,
            "queue2_phase": q2_phase,
            "opposite_phases": opposite,
            "fixed_markers": {"queue1": q1_fixed, "queue2": q2_fixed},
        }
        if passed:
            return result
        if first_failure is None:
            first_failure = result
    assert first_failure is not None
    return first_failure

def self_test() -> None:
    def make(phase: str, raw: bool) -> bytes:
        data = bytearray(0x28)
        rw, vw = PHASES[phase]
        data[8:16] = expected_entry(rw if raw else vw)
        for idx, (fr, fv) in FIXED.items():
            data[idx*8:idx*8+8] = expected_entry(fr if raw else fv)
        return bytes(data)

    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)
        good = [make("red", True), make("green", True), make("red", False), make("green", False)]
        paths = []
        for i, blob in enumerate(good):
            p = td / f"good{i}.bin"
            p.write_bytes(blob)
            paths.append(p)
        assert classify(paths)["passed"]

        for p, blob in zip(paths, good):
            p.write_bytes(swap32(blob))
        r = classify(paths)
        assert r["passed"] and r["dump_normalization"] == "word_swap32"

        # Wrong-side pairing must fail even though every queue contains a legal phase.
        bad = [make("red", True), make("green", True), make("green", False), make("red", False)]
        for p, blob in zip(paths, bad):
            p.write_bytes(blob)
        assert not classify(paths)["passed"]

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw_queue1", type=Path, nargs="?")
    ap.add_argument("raw_queue2", type=Path, nargs="?")
    ap.add_argument("visible_queue1", type=Path, nargs="?")
    ap.add_argument("visible_queue2", type=Path, nargs="?")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        print("raw-palette ownership classifier self-test: PASS")
        return 0

    paths = [args.raw_queue1, args.raw_queue2, args.visible_queue1, args.visible_queue2]
    if any(p is None for p in paths):
        ap.error("four dump paths are required unless --self-test is used")
    result = classify(paths)  # type: ignore[arg-type]
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
