#!/usr/bin/env python3
"""Classify first-hand PR #18 active-CGRAM -> clean H-COMP E1f evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

EVENT_Q1 = 0xA00BF000
RAW_Q1 = 0xA00EF000
MAILBOX = 0xA00F0000
MAX_RECORDS = 64

EXPECTED_COLORS = (
    (0, 0x7FFF),
    (1, 0x7FFF),
    (2, 0x001F),
    (3, 0x0020),
)
EXPECTED_RAW_RGB = dict(EXPECTED_COLORS)
EXPECTED_RESULTS = (0x7FFF, 0x000F)
EXPECTED_FIXED = 0x0000


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


def rgb555_to_rgba5551(value: int) -> int:
    value &= 0x7FFF
    return (
        ((value & 0x001F) << 11)
        | ((value & 0x03E0) << 1)
        | ((value & 0x7C00) >> 9)
        | 1
    )


def rgba5551_to_rgb555(value: int) -> int:
    return (
        ((value >> 11) & 0x1F)
        | ((value & 0x07C0) >> 1)
        | ((value & 0x003E) << 9)
    )


def e1f(a: int, b: int) -> int:
    a &= 0x7FFF
    b &= 0x7FFF
    return (a + b - ((a ^ b) & 0x0421)) >> 1


def prove_oracle() -> None:
    if tuple(e1f(a, b) for a, b in ((0x7FFF, 0x7FFF), (0x001F, 0x0020))) != EXPECTED_RESULTS:
        raise AssertionError("E1f discriminator drift")
    for rgb in range(0x8000):
        if rgba5551_to_rgb555(rgb555_to_rgba5551(rgb)) != rgb:
            raise AssertionError(f"representation roundtrip failed at 0x{rgb:04X}")


def decode_record(rec: bytes) -> tuple[str, int, int]:
    if len(rec) != 4:
        raise ValueError("short event record")
    word = int.from_bytes(rec, "big")
    payload = (word >> 16) & 0xFFFF
    meta = word & 0xFFFF
    if not (payload & 1):
        raise ValueError(f"payload alpha clear: 0x{word:08X}")
    rgb = rgba5551_to_rgb555(payload)
    if meta == 0x8000:
        return ("marker", -1, rgb)
    if meta & 0x8000 or meta > 0x7F8 or (meta & 7):
        raise ValueError(f"invalid event metadata 0x{meta:04X}")
    return ("color", meta >> 3, rgb)


def parse_stream(data: bytes) -> tuple[list[tuple[str, int, int]], int]:
    records: list[tuple[str, int, int]] = []
    for i in range(MAX_RECORDS):
        rec = data[i * 4:(i + 1) * 4]
        if len(rec) < 4 or rec == b"\x00\x00\x00\x00":
            break
        records.append(decode_record(rec))

    # Producer emits bootstrap marker, four active CGRAM records, section marker,
    # then rsp_frame appends the terminal sentinel that must remain unconsumed.
    rendered = [
        ("marker", -1, EXPECTED_FIXED),
        *[("color", index, rgb) for index, rgb in EXPECTED_COLORS],
        ("marker", -1, EXPECTED_FIXED),
    ]
    expected = rendered + [("marker", -1, EXPECTED_FIXED)]
    if records != expected:
        raise ValueError(f"typed stream mismatch: {records!r}")
    return records, len(rendered)


def raw_word(data: bytes, index: int) -> int:
    rec = data[index * 8:(index + 1) * 8]
    if len(rec) != 8:
        raise ValueError(f"short raw entry {index}")
    words = [int.from_bytes(rec[i:i + 2], "big") for i in range(0, 8, 2)]
    if len(set(words)) != 1:
        raise ValueError(f"raw entry {index} not duplicated: {words!r}")
    return words[0]


def mailbox_words(data: bytes) -> tuple[int, int, int, int]:
    if len(data) != 8:
        raise ValueError(f"mailbox length {len(data)} != 8")
    return tuple(int.from_bytes(data[i:i + 2], "big") for i in range(0, 8, 2))  # type: ignore[return-value]


def classify_snapshot(root: Path, prefix: str, mode: str) -> dict[str, object]:
    event = norm((root / f"{prefix}-event-q1.bin").read_bytes(), mode)
    raw = norm((root / f"{prefix}-raw-q1.bin").read_bytes(), mode)
    mailbox = norm((root / f"{prefix}-mailbox.bin").read_bytes(), mode)

    records, consumed = parse_stream(event)

    ea0 = int((root / f"{prefix}-ea0.txt").read_text().strip(), 16)
    expected_ea0 = EVENT_Q1 + consumed * 4
    if ea0 != expected_ea0:
        raise ValueError(f"EA0 0x{ea0:08X} != expected 0x{expected_ea0:08X}")

    raw_report: dict[str, str] = {}
    for index, rgb in EXPECTED_RAW_RGB.items():
        got = raw_word(raw, index)
        want = rgb555_to_rgba5551(rgb)
        if got != want:
            raise ValueError(
                f"replayed raw{index}=0x{got:04X}, expected RGBA5551 0x{want:04X}"
            )
        raw_report[str(index)] = f"0x{got:04X}"

    got_mailbox = mailbox_words(mailbox)
    want_mailbox = (*EXPECTED_RESULTS, 0x0000, 0x0000)
    if got_mailbox != want_mailbox:
        raise ValueError(
            "H-COMP mailbox "
            + ",".join(f"{x:04X}" for x in got_mailbox)
            + " != "
            + ",".join(f"{x:04X}" for x in want_mailbox)
        )

    return {
        "classification": "HCOMP_CGRAM_ARITH_DYNAMIC_VALIDATED",
        "passed": True,
        "prefix": prefix,
        "normalization": mode,
        "event_queue": f"0x{EVENT_Q1:08X}",
        "raw_queue": f"0x{RAW_Q1:08X}",
        "mailbox": f"0x{MAILBOX:08X}",
        "records": len(records),
        "rendered_records_consumed": consumed,
        "terminal_sentinel_unconsumed": True,
        "ea0": f"0x{ea0:08X}",
        "expected_ea0": f"0x{expected_ea0:08X}",
        "raw_operands": raw_report,
        "hcomp_results_rgb555": [f"0x{x:04X}" for x in got_mailbox[:2]],
        "mailbox_guard": [f"0x{x:04X}" for x in got_mailbox[2:]],
        "main_sub_provenance": "NOT_PROVEN",
        "color_math_gating": "NOT_PROVEN",
        "final_pixels": "NOT_PROVEN",
    }


def prefixes(root: Path) -> list[str]:
    suffix = "-event-q1.bin"
    return sorted(p.name[:-len(suffix)] for p in root.glob(f"snap*{suffix}"))


def classify(root: Path) -> dict[str, object]:
    attempts: list[dict[str, object]] = []
    ps = prefixes(root)
    for prefix in ps:
        for mode in ("identity", "word_swap32"):
            try:
                result = classify_snapshot(root, prefix, mode)
            except (ValueError, OSError) as exc:
                attempts.append(
                    {
                        "passed": False,
                        "prefix": prefix,
                        "normalization": mode,
                        "reason": str(exc),
                    }
                )
                continue
            return {
                **result,
                "snapshots_seen": len(ps),
                "attempts_before_pass": len(attempts),
            }
    return {
        "classification": "HCOMP_CGRAM_ARITH_DYNAMIC_FAILED",
        "passed": False,
        "snapshots_seen": len(ps),
        "attempts": attempts,
    }


def encode_record(kind: str, index: int, rgb: int) -> bytes:
    payload = rgb555_to_rgba5551(rgb)
    meta = 0x8000 if kind == "marker" else index * 8
    return ((payload << 16) | meta).to_bytes(4, "big")


def write_fixture(root: Path, mode: str) -> None:
    records = [encode_record("marker", -1, EXPECTED_FIXED)]
    records += [encode_record("color", i, v) for i, v in EXPECTED_COLORS]
    records += [
        encode_record("marker", -1, EXPECTED_FIXED),
        encode_record("marker", -1, EXPECTED_FIXED),
    ]

    event = bytearray(256)
    for i, rec in enumerate(records):
        event[i * 4:(i + 1) * 4] = rec

    raw = bytearray(64)
    for index, rgb in EXPECTED_RAW_RGB.items():
        payload = rgb555_to_rgba5551(rgb).to_bytes(2, "big")
        raw[index * 8:(index + 1) * 8] = payload * 4

    mailbox = bytearray()
    for word in (*EXPECTED_RESULTS, 0, 0):
        mailbox += word.to_bytes(2, "big")

    if mode == "word_swap32":
        event = bytearray(swap32(bytes(event)))
        raw = bytearray(swap32(bytes(raw)))
        mailbox = bytearray(swap32(bytes(mailbox)))

    (root / "snap0-event-q1.bin").write_bytes(event)
    (root / "snap0-raw-q1.bin").write_bytes(raw)
    (root / "snap0-mailbox.bin").write_bytes(mailbox)
    rendered_count = 1 + len(EXPECTED_COLORS) + 1
    (root / "snap0-ea0.txt").write_text(f"{EVENT_Q1 + rendered_count * 4:08x}\n")


def self_test() -> None:
    prove_oracle()
    for mode in ("identity", "word_swap32"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, mode)
            result = classify(root)
            assert result["passed"], result

    # A stale/incorrect arithmetic mailbox must fail even if replay state is valid.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        bad = bytearray((root / "snap0-mailbox.bin").read_bytes())
        bad[0:2] = (0x3DEF).to_bytes(2, "big")
        (root / "snap0-mailbox.bin").write_bytes(bad)
        assert not classify(root)["passed"]

    # Consuming the terminal sentinel is also a failure.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        rendered_count = 1 + len(EXPECTED_COLORS) + 1
        (root / "snap0-ea0.txt").write_text(
            f"{EVENT_Q1 + (rendered_count + 1) * 4:08x}\n"
        )
        assert not classify(root)["passed"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence", type=Path, nargs="?")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--guest", type=Path)
    args = ap.parse_args()

    prove_oracle()

    if args.self_test:
        self_test()
        print("H-COMP CGRAM arithmetic dynamic classifier self-test: PASS")
        return 0

    if args.evidence is None:
        ap.error("evidence directory required unless --self-test")

    result = classify(args.evidence)
    if args.guest and args.guest.exists():
        result["guest_sha256"] = hashlib.sha256(args.guest.read_bytes()).hexdigest()

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
