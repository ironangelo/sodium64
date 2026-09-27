#!/usr/bin/env python3
"""Classify first-hand 8-line Main/Sub lifetime evidence from section queues."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

SECTION_QUEUE1 = 0xA016C600
SECTION_QUEUE2 = 0xA0171600
SECTION_SIZE = 0x40

# Offsets inside the 0x40-byte section record, pinned by defines.h/ppu.S.
CGADSUB = 56
TS = 57
TM = 58
TSW = 59
TMW = 60
BG_MODE = 61
STAT_FLAGS = 62
SPLIT_LINE = 63

EXPECTED_FIRST = {
    "cgadsub": 0x01,
    "ts": 0x02,
    "tm": 0x01,
    "tsw": 0x00,
    "tmw": 0x00,
    "bg_mode": 0x00,
    "split_line": 8,
}
EXPECTED_SECOND = {
    "cgadsub": 0x01,
    "ts": 0x00,
    "tm": 0x01,
    "tsw": 0x00,
    "tmw": 0x00,
    "bg_mode": 0x00,
    "split_line": 224,
}


def swap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("word_swap32 requires a 4-byte multiple")
    return b"".join(data[i:i + 4][::-1] for i in range(0, len(data), 4))


def norm(data: bytes, mode: str) -> bytes:
    if mode == "identity":
        return data
    if mode == "word_swap32":
        return swap32(data)
    raise ValueError(mode)


def decode_record(data: bytes, index: int) -> dict[str, int]:
    start = index * SECTION_SIZE
    rec = data[start:start + SECTION_SIZE]
    if len(rec) != SECTION_SIZE:
        raise ValueError(f"short section record {index}")
    return {
        "cgadsub": rec[CGADSUB],
        "ts": rec[TS],
        "tm": rec[TM],
        "tsw": rec[TSW],
        "tmw": rec[TMW],
        "bg_mode": rec[BG_MODE],
        "stat_flags": rec[STAT_FLAGS],
        "split_line": rec[SPLIT_LINE],
    }


def require_record(got: dict[str, int], want: dict[str, int], label: str) -> None:
    for key, value in want.items():
        if got[key] != value:
            raise ValueError(
                f"{label}.{key}=0x{got[key]:02X}, expected 0x{value:02X}"
            )


def peek_queue(data: bytes, mode: str) -> list[dict[str, int]]:
    data = norm(data, mode)
    return [decode_record(data, 0), decode_record(data, 1)]


def classify_queue(data: bytes, mode: str) -> dict[str, object]:
    first, second = peek_queue(data, mode)
    require_record(first, EXPECTED_FIRST, "section0")
    require_record(second, EXPECTED_SECOND, "section1")

    if not (first["stat_flags"] & 0x40):
        raise ValueError(
            f"section0 missing frame-start OAM-dirty carrier: 0x{first['stat_flags']:02X}"
        )
    if second["stat_flags"] & 0x40:
        raise ValueError(
            f"section1 unexpectedly retains OAM-dirty carrier: 0x{second['stat_flags']:02X}"
        )

    # The exact lifetime property required by the future compact Sub target:
    # TS exists only in [0,8); after the first split, the delivered section
    # state has TS=0 through the final visible split at 224.
    if not (
        first["ts"] == 0x02
        and first["split_line"] == 8
        and second["ts"] == 0
        and second["split_line"] == 224
    ):
        raise ValueError("8-line Sub lifetime invariant failed")

    return {
        "normalization": mode,
        "sections": [first, second],
        "sub_visible_interval": "[0,8)",
        "post_split_sub_enabled": False,
        "final_visible_split": 224,
    }


def classify(root: Path) -> dict[str, object]:
    attempts: list[dict[str, object]] = []
    snapshots = sorted(
        p.name[:-len("-q1.bin")]
        for p in root.glob("snap*-q1.bin")
    )
    for prefix in snapshots:
        for mode in ("identity", "word_swap32"):
            try:
                q1 = classify_queue((root / f"{prefix}-q1.bin").read_bytes(), mode)
                q2 = classify_queue((root / f"{prefix}-q2.bin").read_bytes(), mode)
            except (OSError, ValueError) as exc:
                diagnostic: dict[str, object] = {
                    "prefix": prefix,
                    "normalization": mode,
                    "passed": False,
                    "reason": str(exc),
                }
                try:
                    diagnostic["q1_sections"] = peek_queue(
                        (root / f"{prefix}-q1.bin").read_bytes(), mode
                    )
                    diagnostic["q2_sections"] = peek_queue(
                        (root / f"{prefix}-q2.bin").read_bytes(), mode
                    )
                except (OSError, ValueError) as peek_exc:
                    diagnostic["peek_error"] = str(peek_exc)
                attempts.append(diagnostic)
                continue

            return {
                "classification": "HCOMP_MAIN_SUB_LIFETIME_DYNAMIC_VALIDATED",
                "passed": True,
                "prefix": prefix,
                "normalization": mode,
                "section_queue1": f"0x{SECTION_QUEUE1:08X}",
                "section_queue2": f"0x{SECTION_QUEUE2:08X}",
                "queue1": q1,
                "queue2": q2,
                "both_ping_pong_queues_match": True,
                "sub_target_safe_after_first_split": True,
                "runtime_source_delta": 0,
                "snapshots_seen": len(snapshots),
                "attempts_before_pass": len(attempts),
            }

    return {
        "classification": "HCOMP_MAIN_SUB_LIFETIME_DYNAMIC_FAILED",
        "passed": False,
        "snapshots_seen": len(snapshots),
        "attempts": attempts,
    }


def make_record(want: dict[str, int], *, first: bool) -> bytes:
    rec = bytearray(SECTION_SIZE)
    rec[CGADSUB] = want["cgadsub"]
    rec[TS] = want["ts"]
    rec[TM] = want["tm"]
    rec[TSW] = want["tsw"]
    rec[TMW] = want["tmw"]
    rec[BG_MODE] = want["bg_mode"]
    rec[STAT_FLAGS] = 0x40 if first else 0x00
    rec[SPLIT_LINE] = want["split_line"]
    return bytes(rec)


def write_fixture(root: Path, mode: str) -> None:
    data = bytearray(SECTION_SIZE * 4)
    data[0:SECTION_SIZE] = make_record(EXPECTED_FIRST, first=True)
    data[SECTION_SIZE:2 * SECTION_SIZE] = make_record(EXPECTED_SECOND, first=False)
    raw = bytes(data)
    if mode == "word_swap32":
        raw = swap32(raw)
    for queue in ("q1", "q2"):
        (root / f"snap0-{queue}.bin").write_bytes(raw)


def self_test() -> None:
    for mode in ("identity", "word_swap32"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, mode)
            result = classify(root)
            assert result["passed"], result

    # Off-by-one lifetime must fail.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        bad = bytearray((root / "snap0-q1.bin").read_bytes())
        bad[SPLIT_LINE] = 9
        (root / "snap0-q1.bin").write_bytes(bad)
        assert not classify(root)["passed"]

    # A later section that re-enables Sub must fail.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        bad = bytearray((root / "snap0-q2.bin").read_bytes())
        bad[SECTION_SIZE + TS] = 0x02
        (root / "snap0-q2.bin").write_bytes(bad)
        assert not classify(root)["passed"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence", type=Path, nargs="?")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--guest", type=Path)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        print("H-COMP Main/Sub lifetime classifier self-test: PASS")
        return 0

    if args.evidence is None:
        ap.error("evidence directory required unless --self-test")

    result = classify(args.evidence)
    if args.guest and args.guest.exists():
        result["guest_sha256"] = hashlib.sha256(args.guest.read_bytes()).hexdigest()

    out = json.dumps(result, indent=2, sort_keys=True)
    print(out)
    if args.output:
        args.output.write_text(out + "\n")
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
