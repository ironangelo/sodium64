#!/usr/bin/env python3
"""Classify read-only Mupen snapshots of the DMA8 CGRAM producer."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

EVENT_BASE = {0: 0xA00BF000, 4: 0xA00D7000}
RAW_FILE = {0: "raw-q1", 4: "raw-q2"}
BASE_FILE = {0: "base-q1", 4: "base-q2"}
EVENT_FILE = {0: "event-q1", 4: "event-q2"}

PHASES = {
    "A": {"base": (0x001F, 0x03E0, 0x7C00), "fixed": 0x0C63},
    "B": {"base": (0x03E0, 0x001F, 0x7FFF), "fixed": 0x14A5},
}
ACTIVE_FIXED = 0x1CE7
EXPECTED_COLORS = (
    (1, 0x1234),
    (1, 0x4567),
    (0, 0x2AAA),
    (2, 0x7FFF),
)
EXPECTED_FINAL = (0x2AAA, 0x4567, 0x7FFF)
MAX_RECORDS = 64


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
    return ((value & 0x1F) << 11) | ((value & 0x3E0) << 1) | ((value & 0x7C00) >> 9) | 1


def rgba5551_to_rgb555(value: int) -> int:
    return ((value >> 11) & 0x1F) | (((value >> 6) & 0x1F) << 5) | (((value >> 1) & 0x1F) << 10)


def words16(data: bytes, count: int) -> tuple[int, ...]:
    return tuple(int.from_bytes(data[i:i + 2], "big") for i in range(0, count * 2, 2))


def raw_entries(data: bytes, count: int) -> tuple[int, ...]:
    out = []
    for i in range(count):
        rec = data[i * 8:(i + 1) * 8]
        if len(rec) != 8:
            raise ValueError("short raw palette dump")
        words = words16(rec, 4)
        if len(set(words)) != 1:
            raise ValueError(f"raw entry {i} is not duplicated across 8 bytes: {words}")
        out.append(rgba5551_to_rgb555(words[0]))
    return tuple(out)


def decode_record(rec: bytes) -> tuple[str, int, int]:
    if len(rec) != 4:
        raise ValueError("short typed record")
    word = int.from_bytes(rec, "big")
    payload = (word >> 16) & 0xFFFF
    meta = word & 0xFFFF
    if not (payload & 1):
        raise ValueError(f"typed payload alpha bit is clear: {rec.hex()}")
    rgb = rgba5551_to_rgb555(payload)
    if meta == 0x8000:
        return ("marker", -1, rgb)
    if meta & 0x8000 or meta > 0x7F8 or meta & 7:
        raise ValueError(f"invalid typed metadata 0x{meta:04X}")
    return ("color", meta >> 3, rgb)


def parse_handed_stream(data: bytes, phase: str) -> dict[str, object]:
    expected_fixed = int(PHASES[phase]["fixed"])
    color_pos = 0
    first_color_index = None
    active_marker_index = None
    replay = list(PHASES[phase]["base"])
    markers_before = 0
    interleaved_markers = 0

    # Decode lazily so stale/padding bytes after the terminal active marker are
    # outside the stream contract and cannot create a false classifier failure.
    for i in range(MAX_RECORDS):
        kind, index, value = decode_record(data[i * 4:(i + 1) * 4])
        if kind == "marker":
            if color_pos < len(EXPECTED_COLORS):
                if value != expected_fixed:
                    raise ValueError(
                        f"marker before active fixed change is 0x{value:04X}, expected 0x{expected_fixed:04X}"
                    )
                if color_pos == 0:
                    markers_before += 1
                else:
                    interleaved_markers += 1
                continue
            if value == ACTIVE_FIXED:
                active_marker_index = i
                break
            if value == expected_fixed:
                interleaved_markers += 1
                continue
            raise ValueError(f"unexpected marker after colors: 0x{value:04X}")

        want_index, want_value = EXPECTED_COLORS[color_pos] if color_pos < len(EXPECTED_COLORS) else (-1, -1)
        if (index, value) != (want_index, want_value):
            raise ValueError(
                f"unexpected color record at {i}: {(index, hex(value))}, "
                f"expected {(want_index, hex(want_value))}"
            )
        if first_color_index is None:
            first_color_index = i
        if index < len(replay):
            replay[index] = value
        color_pos += 1

    if color_pos != len(EXPECTED_COLORS):
        raise ValueError(f"only found {color_pos}/{len(EXPECTED_COLORS)} active colors")
    if active_marker_index is None:
        raise ValueError("no active fixed-color marker found after active colors")
    if tuple(replay) != EXPECTED_FINAL:
        raise ValueError(f"typed replay final mismatch: {tuple(replay)}")

    return {
        "first_color_record": first_color_index,
        "active_marker_record": active_marker_index,
        "markers_before_colors": markers_before,
        "interleaved_base_markers": interleaved_markers,
        "replay_first3": [f"0x{x:04X}" for x in replay],
    }


def classify_snapshot(root: Path, prefix: str, mode: str) -> dict[str, object]:
    ea0_bytes = norm((root / f"{prefix}-ea0.bin").read_bytes(), mode)
    if len(ea0_bytes) != 4:
        raise ValueError("EA0 dump must be 4 bytes")
    ea0 = int.from_bytes(ea0_bytes, "big")
    slot = next((s for s, base in EVENT_BASE.items() if ea0 == base), None)
    if slot is None:
        return {
            "passed": False, "prefix": prefix, "normalization": mode,
            "reason": "EA0 is not an exact handed event-queue base",
            "ea0": f"0x{ea0:08X}",
        }

    base = norm((root / f"{prefix}-{BASE_FILE[slot]}.bin").read_bytes(), mode)
    raw = norm((root / f"{prefix}-{RAW_FILE[slot]}.bin").read_bytes(), mode)
    event = norm((root / f"{prefix}-{EVENT_FILE[slot]}.bin").read_bytes(), mode)
    first3 = words16(base, 3)
    phase = next((name for name, info in PHASES.items() if first3 == info["base"]), None)
    if phase is None:
        return {
            "passed": False, "prefix": prefix, "normalization": mode, "slot": slot,
            "reason": "handed base snapshot is not phase A/B",
            "base_first3": [f"0x{x:04X}" for x in first3],
        }

    raw3 = raw_entries(raw, 3)
    if raw3 != first3:
        return {
            "passed": False, "prefix": prefix, "normalization": mode, "slot": slot,
            "phase": phase, "reason": "raw shadow is not historical base",
            "base_first3": [f"0x{x:04X}" for x in first3],
            "raw_first3": [f"0x{x:04X}" for x in raw3],
        }
    if raw3 == EXPECTED_FINAL:
        return {
            "passed": False, "prefix": prefix, "normalization": mode, "slot": slot,
            "phase": phase, "reason": "raw shadow looks frame-final instead of historical-base",
        }

    stream = parse_handed_stream(event, phase)

    state = norm((root / f"{prefix}-state.bin").read_bytes(), mode)
    if len(state) != 12:
        raise ValueError("state dump must be 12 bytes")
    producer_ptr = int.from_bytes(state[0:4], "big")
    producer_count = int.from_bytes(state[8:10], "big")
    producer_overflow = state[10]
    producer_slot = None
    for s, base_addr in EVENT_BASE.items():
        if base_addr <= producer_ptr <= base_addr + 0x18000 and (producer_ptr - base_addr) % 4 == 0:
            producer_slot = s
            break

    # Stable pipeline evidence requires CPU producer ownership to have moved to
    # the opposite slot while EA0 keeps the handed slot. Pause races are simply
    # rejected so another snapshot can qualify.
    if producer_slot is None or producer_slot == slot:
        return {
            "passed": False, "prefix": prefix, "normalization": mode, "slot": slot,
            "phase": phase, "reason": "snapshot does not show opposite producer/handed ownership",
            "producer_ptr": f"0x{producer_ptr:08X}",
            "producer_count": producer_count,
        }
    if producer_overflow != 0:
        return {
            "passed": False, "prefix": prefix, "normalization": mode,
            "reason": "current producer overflow byte is nonzero",
            "producer_overflow": producer_overflow,
        }

    return {
        "classification": "CGRAM_DMA8_DYNAMIC_PRODUCER_VALIDATED",
        "passed": True,
        "prefix": prefix,
        "normalization": mode,
        "handed_slot": slot,
        "producer_slot": producer_slot,
        "phase": phase,
        "ea0": f"0x{ea0:08X}",
        "producer_ptr": f"0x{producer_ptr:08X}",
        "producer_count": producer_count,
        "producer_overflow": producer_overflow,
        "base_first3": [f"0x{x:04X}" for x in first3],
        "raw_first3": [f"0x{x:04X}" for x in raw3],
        **stream,
    }


def prefixes(root: Path) -> list[str]:
    return sorted(p.name[:-10] for p in root.glob("snap*-state.bin"))


def classify(root: Path) -> dict[str, object]:
    attempts = []
    ps = prefixes(root)
    for prefix in ps:
        for mode in ("identity", "word_swap32"):
            try:
                result = classify_snapshot(root, prefix, mode)
            except (ValueError, OSError) as exc:
                result = {"passed": False, "prefix": prefix, "normalization": mode, "reason": str(exc)}
            attempts.append(result)
            if result.get("passed"):
                return {**result, "snapshots_seen": len(ps), "attempts_before_pass": len(attempts) - 1}
    return {
        "classification": "CGRAM_DMA8_DYNAMIC_PRODUCER_FAILED",
        "passed": False,
        "snapshots_seen": len(ps),
        "attempts": attempts,
    }


def encode_record(kind: str, index: int, rgb: int) -> bytes:
    payload = rgb555_to_rgba5551(rgb)
    meta = 0x8000 if kind == "marker" else index * 8
    return ((payload << 16) | meta).to_bytes(4, "big")


def write_snapshot(root: Path, prefix: str, mode: str, handed: int, phase: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    producer = handed ^ 4
    state = (
        (EVENT_BASE[producer] + 12).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + (3).to_bytes(2, "big")
        + b"\x00\x00"
    )
    ea0 = EVENT_BASE[handed].to_bytes(4, "big")

    base = bytearray(16)
    for i, value in enumerate(PHASES[phase]["base"]):
        base[i * 2:i * 2 + 2] = int(value).to_bytes(2, "big")

    raw = bytearray(32)
    for i, value in enumerate(PHASES[phase]["base"]):
        rgba = rgb555_to_rgba5551(int(value)).to_bytes(2, "big")
        raw[i * 8:(i + 1) * 8] = rgba * 4

    event = bytearray(256)
    records = [encode_record("marker", -1, int(PHASES[phase]["fixed"]))]
    records += [encode_record("color", i, v) for i, v in EXPECTED_COLORS]
    records.append(encode_record("marker", -1, ACTIVE_FIXED))
    for i, rec in enumerate(records):
        event[i * 4:(i + 1) * 4] = rec

    def save(name: str, data: bytes) -> None:
        (root / f"{prefix}-{name}.bin").write_bytes(norm(data, mode))

    save("state", state)
    save("ea0", ea0)
    for s in (0, 4):
        if s == handed:
            save(BASE_FILE[s], bytes(base))
            save(RAW_FILE[s], bytes(raw))
            save(EVENT_FILE[s], bytes(event))
        else:
            save(BASE_FILE[s], bytes(16))
            save(RAW_FILE[s], bytes(32))
            save(EVENT_FILE[s], bytes(256))


def self_test() -> None:
    for mode, handed, phase in (("identity", 0, "A"), ("word_swap32", 4, "B")):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_snapshot(root, "snap0", mode, handed, phase)
            result = classify(root)
            assert result["passed"], result
            assert result["handed_slot"] == handed
            assert result["phase"] == phase

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_snapshot(root, "snap0", "identity", 0, "A")
        raw = bytearray((root / "snap0-raw-q1.bin").read_bytes())
        raw[0:8] = rgb555_to_rgba5551(0x2AAA).to_bytes(2, "big") * 4
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
        print("CGRAM DMA8 dynamic classifier self-test: PASS")
        return 0
    if args.evidence is None:
        ap.error("evidence directory is required unless --self-test is used")

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
