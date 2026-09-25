#!/usr/bin/env python3
"""Classify first-handoff Q1 evidence for the DMA8 RSP CGRAM consumer."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

EVENT_Q1 = 0xA00BF000
RAW_Q1 = 0xA00EF000
ACTIVE_FIXED = 0x1CE7
EXPECTED_COLORS = (
    (3, 0x1357),  # audit-critical cached word1 after startup marker word0
    (1, 0x1234),
    (1, 0x4567),
    (0, 0x2AAA),
    (2, 0x7FFF),
)
EXPECTED_RAW = {
    0: 0x2AAA,
    1: 0x4567,
    2: 0x7FFF,
    3: 0x1357,
}
CONTROL_INDEX = 4
MAX_RECORDS = 64


def swap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("word_swap32 requires 4-byte multiple")
    return b"".join(data[i:i + 4][::-1] for i in range(0, len(data), 4))


def norm(data: bytes, mode: str) -> bytes:
    return data if mode == "identity" else swap32(data)


def rgb555_to_rgba5551(value: int) -> int:
    value &= 0x7FFF
    return ((value & 0x1F) << 11) | ((value & 0x3E0) << 1) | ((value & 0x7C00) >> 9) | 1


def rgba5551_to_rgb555(value: int) -> int:
    return ((value >> 11) & 0x1F) | (((value >> 6) & 0x1F) << 5) | (((value >> 1) & 0x1F) << 10)


def decode_record(rec: bytes) -> tuple[str, int, int]:
    if len(rec) != 4:
        raise ValueError("short record")
    word = int.from_bytes(rec, "big")
    payload = (word >> 16) & 0xFFFF
    meta = word & 0xFFFF
    if not (payload & 1):
        raise ValueError(f"payload alpha bit clear: 0x{word:08X}")
    rgb = rgba5551_to_rgb555(payload)
    if meta == 0x8000:
        return ("marker", -1, rgb)
    if meta & 0x8000 or meta > 0x7F8 or meta & 7:
        raise ValueError(f"invalid color metadata: 0x{meta:04X}")
    return ("color", meta >> 3, rgb)


def parse_stream(data: bytes) -> tuple[list[tuple[str, int, int]], dict[str, object]]:
    records: list[tuple[str, int, int]] = []
    for i in range(MAX_RECORDS):
        rec = data[i * 4:(i + 1) * 4]
        if len(rec) < 4:
            break
        if rec == b"\x00\x00\x00\x00":
            break
        records.append(decode_record(rec))

    if len(records) < 3:
        raise ValueError(f"Q1 stream too short: {len(records)}")
    if records[0] != ("marker", -1, 0x0000):
        raise ValueError(f"record0 is not startup fixed0 marker: {records[0]}")
    if records[1] != ("color", 3, 0x1357):
        raise ValueError(f"record1 is not cached-half discriminator: {records[1]}")
    if records[-1] != ("marker", -1, ACTIVE_FIXED):
        raise ValueError(f"last record is not final fixed E7 marker: {records[-1]}")

    color_pos = 0
    seen_active_fixed = False
    markers = 0
    active_markers = 0
    for i, (kind, index, value) in enumerate(records):
        if kind == "marker":
            markers += 1
            if value == ACTIVE_FIXED:
                seen_active_fixed = True
                active_markers += 1
            elif value == 0:
                if seen_active_fixed:
                    raise ValueError("fixed0 marker appears after fixed E7 marker")
            else:
                raise ValueError(f"unexpected marker value at {i}: 0x{value:04X}")
            continue

        if seen_active_fixed:
            raise ValueError("color appears after fixed E7 marker")
        if color_pos >= len(EXPECTED_COLORS):
            raise ValueError(f"unexpected extra color record at {i}: {(index, value)}")
        if (index, value) != EXPECTED_COLORS[color_pos]:
            raise ValueError(
                f"color sequence mismatch at {i}: {(index, hex(value))} != "
                f"{(EXPECTED_COLORS[color_pos][0], hex(EXPECTED_COLORS[color_pos][1]))}"
            )
        color_pos += 1

    if color_pos != len(EXPECTED_COLORS):
        raise ValueError(f"found {color_pos}/{len(EXPECTED_COLORS)} expected colors")
    if active_markers < 1:
        raise ValueError("no fixed E7 marker in Q1 stream")

    return records, {
        "record_count": len(records),
        "marker_count": markers,
        "active_marker_count": active_markers,
        "cached_half_record1": "index3=0x1357",
    }


def raw_word(data: bytes, index: int) -> int:
    rec = data[index * 8:(index + 1) * 8]
    if len(rec) != 8:
        raise ValueError(f"short raw entry {index}")
    words = [int.from_bytes(rec[i:i + 2], "big") for i in range(0, 8, 2)]
    if len(set(words)) != 1:
        raise ValueError(f"raw entry {index} not duplicated: {words}")
    return words[0]


def classify_snapshot(root: Path, prefix: str, mode: str) -> dict[str, object]:
    event = norm((root / f"{prefix}-event-q1.bin").read_bytes(), mode)
    raw = norm((root / f"{prefix}-raw-q1.bin").read_bytes(), mode)
    records, stream_info = parse_stream(event)

    ea0_text = (root / f"{prefix}-ea0.txt").read_text(encoding="utf-8").strip()
    ea0 = int(ea0_text, 16)
    expected_ea0 = EVENT_Q1 + len(records) * 4
    if ea0 != expected_ea0:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "EA0 did not advance through complete first-hand Q1 stream",
            "ea0": f"0x{ea0:08X}",
            "expected_ea0": f"0x{expected_ea0:08X}",
            **stream_info,
        }

    raw_report: dict[str, str] = {}
    for index, rgb in EXPECTED_RAW.items():
        got = raw_word(raw, index)
        want = rgb555_to_rgba5551(rgb)
        raw_report[str(index)] = f"0x{got:04X}"
        if got != want:
            return {
                "passed": False,
                "prefix": prefix,
                "normalization": mode,
                "reason": f"raw entry {index} mismatch",
                "got": f"0x{got:04X}",
                "want": f"0x{want:04X}",
                **stream_info,
            }

    control = raw_word(raw, CONTROL_INDEX)
    if control != 0:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "untouched bootstrap raw control entry changed",
            "control_index": CONTROL_INDEX,
            "control_value": f"0x{control:04X}",
            **stream_info,
        }

    return {
        "classification": "CGRAM_RSP_DMA8_DYNAMIC_CONSUMER_VALIDATED",
        "passed": True,
        "prefix": prefix,
        "normalization": mode,
        "event_base": f"0x{EVENT_Q1:08X}",
        "raw_base": f"0x{RAW_Q1:08X}",
        "ea0": f"0x{ea0:08X}",
        "expected_ea0": f"0x{expected_ea0:08X}",
        "raw_entries": raw_report,
        "untouched_control_index": CONTROL_INDEX,
        "untouched_control_value": "0x0000",
        **stream_info,
    }


def prefixes(root: Path) -> list[str]:
    suffix = "-event-q1.bin"
    return sorted(p.name[:-len(suffix)] for p in root.glob(f"snap*{suffix}"))


def classify(root: Path) -> dict[str, object]:
    attempts = []
    ps = prefixes(root)
    for prefix in ps:
        for mode in ("identity", "word_swap32"):
            try:
                result = classify_snapshot(root, prefix, mode)
            except (ValueError, OSError) as exc:
                result = {
                    "passed": False,
                    "prefix": prefix,
                    "normalization": mode,
                    "reason": str(exc),
                }
            attempts.append(result)
            if result.get("passed"):
                return {
                    **result,
                    "snapshots_seen": len(ps),
                    "attempts_before_pass": len(attempts) - 1,
                }
    return {
        "classification": "CGRAM_RSP_DMA8_DYNAMIC_CONSUMER_FAILED",
        "passed": False,
        "snapshots_seen": len(ps),
        "attempts": attempts,
    }


def encode_record(kind: str, index: int, rgb: int) -> bytes:
    payload = rgb555_to_rgba5551(rgb)
    meta = 0x8000 if kind == "marker" else index * 8
    return ((payload << 16) | meta).to_bytes(4, "big")


def write_fixture(root: Path, mode: str) -> None:
    records = [encode_record("marker", -1, 0)]
    records += [encode_record("color", i, v) for i, v in EXPECTED_COLORS]
    records.append(encode_record("marker", -1, ACTIVE_FIXED))

    event = bytearray(256)
    for i, rec in enumerate(records):
        event[i * 4:(i + 1) * 4] = rec

    raw = bytearray(64)
    for index, rgb in EXPECTED_RAW.items():
        payload = rgb555_to_rgba5551(rgb).to_bytes(2, "big")
        raw[index * 8:(index + 1) * 8] = payload * 4

    if mode == "word_swap32":
        event = bytearray(swap32(bytes(event)))
        raw = bytearray(swap32(bytes(raw)))

    (root / "snap0-event-q1.bin").write_bytes(event)
    (root / "snap0-raw-q1.bin").write_bytes(raw)
    (root / "snap0-ea0.txt").write_text(
        f"{EVENT_Q1 + len(records) * 4:08x}\n", encoding="utf-8"
    )


def self_test() -> None:
    for mode in ("identity", "word_swap32"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, mode)
            result = classify(root)
            assert result["passed"], result

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        raw = bytearray((root / "snap0-raw-q1.bin").read_bytes())
        raw[3 * 8:4 * 8] = b"\x00" * 8
        (root / "snap0-raw-q1.bin").write_bytes(raw)
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
        print("CGRAM DMA8 RSP consumer dynamic classifier self-test: PASS")
        return 0
    if args.evidence is None:
        ap.error("evidence directory required unless --self-test")

    result = classify(args.evidence)
    if args.guest and args.guest.exists():
        result["guest_sha256"] = hashlib.sha256(args.guest.read_bytes()).hexdigest()
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
