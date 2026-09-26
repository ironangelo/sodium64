#!/usr/bin/env python3
"""Classify read-only Mupen snapshots of Sodium64's CGRAM epoch producer."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

EVENT_BASE = {0: 0xA00BF000, 4: 0xA00D7000}
SIDE_BASE = {0: 0xA00BE600, 4: 0xA00BEB00}
BASE_FILE = {0: "base-q1", 4: "base-q2"}
SIDE_FILE = {0: "side-q1", 4: "side-q2"}
EVENT_FILE = {0: "event-q1", 4: "event-q2"}

PHASES = {
    "A": {
        "base": (0x001F, 0x03E0, 0x7C00),
        "fixed": 0x0C63,
    },
    "B": {
        "base": (0x03E0, 0x001F, 0x7FFF),
        "fixed": 0x14A5,
    },
}
ACTIVE_FIXED = 0x1CE7
EXPECTED_EVENTS = (
    (1, 0x1234),
    (1, 0x4567),
    (0, 0x2AAA),
    (2, 0x7FFF),
)
EXPECTED_FINAL = (0x2AAA, 0x4567, 0x7FFF)


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


def words16(data: bytes, count: int) -> tuple[int, ...]:
    return tuple(int.from_bytes(data[i:i + 2], "big") for i in range(0, count * 2, 2))


def parse_events(data: bytes, count: int) -> tuple[tuple[int, int], ...]:
    out = []
    for i in range(count):
        rec = data[i * 4:(i + 1) * 4]
        if len(rec) != 4:
            raise ValueError("short event dump")
        if rec[1] != 0:
            raise ValueError(f"reserved event byte is nonzero at {i}: {rec.hex()}")
        out.append((rec[0], int.from_bytes(rec[2:4], "big")))
    return tuple(out)


def replay(first3: tuple[int, int, int], events: tuple[tuple[int, int], ...]) -> tuple[int, int, int]:
    state = list(first3)
    for index, value in events:
        if index < len(state):
            state[index] = value & 0x7FFF
    return tuple(state)


def classify_snapshot(root: Path, prefix: str, mode: str) -> dict[str, object]:
    state = norm((root / f"{prefix}-state.bin").read_bytes(), mode)
    if len(state) != 12:
        raise ValueError(f"{prefix}: state dump is {len(state)} bytes")
    event_ptr = int.from_bytes(state[0:4], "big")
    side_ptr = int.from_bytes(state[4:8], "big")
    event_count = int.from_bytes(state[8:10], "big")
    overflow = state[10]

    slot = None
    for candidate, base in EVENT_BASE.items():
        if event_ptr == base + event_count * 4:
            slot = candidate
            break
    if slot is None:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "event pointer/count is not coherent with Q1/Q2",
            "event_ptr": f"0x{event_ptr:08X}",
            "event_count": event_count,
            "overflow": overflow,
        }

    side_base = SIDE_BASE[slot]
    if not side_base <= side_ptr <= side_base + 0x500 or (side_ptr - side_base) % 4:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "sideband pointer is outside/coherency-invalid for selected slot",
            "slot": slot,
            "side_ptr": f"0x{side_ptr:08X}",
        }
    section_count = (side_ptr - side_base) // 4

    if event_count != 4:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "snapshot not in complete active/post-active epoch",
            "slot": slot,
            "event_count": event_count,
            "section_count": section_count,
            "overflow": overflow,
        }
    if overflow != 0:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "producer overflow byte is nonzero",
            "slot": slot,
            "overflow": overflow,
        }
    if not 1 <= section_count <= 320:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "section count outside validated capacity",
            "slot": slot,
            "section_count": section_count,
        }

    base = norm((root / f"{prefix}-{BASE_FILE[slot]}.bin").read_bytes(), mode)
    side = norm((root / f"{prefix}-{SIDE_FILE[slot]}.bin").read_bytes(), mode)
    event = norm((root / f"{prefix}-{EVENT_FILE[slot]}.bin").read_bytes(), mode)
    if len(base) < 6 or len(side) < section_count * 4 or len(event) < event_count * 4:
        raise ValueError(f"{prefix}: selected dump is too short")

    first3 = words16(base, 3)
    phase = None
    for name, info in PHASES.items():
        if first3 == info["base"]:
            phase = name
            break
    if phase is None:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "base snapshot does not match phase A or B",
            "slot": slot,
            "base_first3": [f"0x{x:04X}" for x in first3],
        }

    events = parse_events(event, event_count)
    if events != EXPECTED_EVENTS:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "event records differ from guest sequence",
            "slot": slot,
            "phase": phase,
            "events": [[i, f"0x{v:04X}"] for i, v in events],
        }

    side_records = []
    last_count = -1
    for i in range(section_count):
        rec = side[i * 4:(i + 1) * 4]
        count = int.from_bytes(rec[0:2], "big")
        fixed = int.from_bytes(rec[2:4], "big")
        if count < last_count or count > event_count:
            return {
                "passed": False,
                "prefix": prefix,
                "normalization": mode,
                "reason": "sideband cumulative event counts are invalid",
                "slot": slot,
                "section_index": i,
                "count": count,
                "previous": last_count,
            }
        last_count = count
        side_records.append((count, fixed))

    expected_base_fixed = int(PHASES[phase]["fixed"])
    if not side_records or side_records[0] != (0, expected_base_fixed):
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "first section does not carry base epoch/fixed color",
            "slot": slot,
            "phase": phase,
            "first_sideband": side_records[0] if side_records else None,
            "expected_fixed": f"0x{expected_base_fixed:04X}",
        }

    active_indices = [i for i, rec in enumerate(side_records) if rec == (4, ACTIVE_FIXED)]
    if not active_indices:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "no section carries completed active epoch + active fixed color",
            "slot": slot,
            "phase": phase,
            "side_records": [[c, f"0x{v:04X}"] for c, v in side_records],
        }

    final = replay(first3, events)
    if final != EXPECTED_FINAL:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "base+events replay final colors mismatch",
            "slot": slot,
            "phase": phase,
            "final": [f"0x{x:04X}" for x in final],
        }

    return {
        "classification": "CGRAM_EPOCH_DYNAMIC_PRODUCER_VALIDATED",
        "passed": True,
        "prefix": prefix,
        "normalization": mode,
        "slot": slot,
        "phase": phase,
        "event_count": event_count,
        "section_count": section_count,
        "event_ptr": f"0x{event_ptr:08X}",
        "side_ptr": f"0x{side_ptr:08X}",
        "overflow": overflow,
        "base_first3": [f"0x{x:04X}" for x in first3],
        "events": [[i, f"0x{v:04X}"] for i, v in events],
        "active_sideband_indices": active_indices,
        "replay_first3": [f"0x{x:04X}" for x in final],
    }


def prefixes(root: Path) -> list[str]:
    return sorted(p.name[:-10] for p in root.glob("snap*-state.bin"))


def classify(root: Path) -> dict[str, object]:
    attempts = []
    for prefix in prefixes(root):
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
                    "snapshots_seen": len(prefixes(root)),
                    "attempts_before_pass": len(attempts) - 1,
                }
    return {
        "classification": "CGRAM_EPOCH_DYNAMIC_PRODUCER_FAILED",
        "passed": False,
        "snapshots_seen": len(prefixes(root)),
        "attempts": attempts,
    }


def write_snapshot(root: Path, prefix: str, mode: str, slot: int, phase: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    count = 4
    section_records = [
        (0, int(PHASES[phase]["fixed"])),
        (4, ACTIVE_FIXED),
        (4, ACTIVE_FIXED),
    ]
    state = (
        (EVENT_BASE[slot] + count * 4).to_bytes(4, "big")
        + (SIDE_BASE[slot] + len(section_records) * 4).to_bytes(4, "big")
        + count.to_bytes(2, "big")
        + b"\x00\x00"
    )
    base = bytearray(16)
    for i, value in enumerate(PHASES[phase]["base"]):
        base[i * 2:i * 2 + 2] = int(value).to_bytes(2, "big")
    side = bytearray(0x500)
    for i, (ec, fixed) in enumerate(section_records):
        side[i * 4:i * 4 + 2] = ec.to_bytes(2, "big")
        side[i * 4 + 2:i * 4 + 4] = fixed.to_bytes(2, "big")
    events = bytearray(64)
    for i, (index, value) in enumerate(EXPECTED_EVENTS):
        events[i * 4:i * 4 + 4] = bytes([index, 0]) + value.to_bytes(2, "big")

    def save(name: str, data: bytes) -> None:
        (root / f"{prefix}-{name}.bin").write_bytes(norm(data, mode))

    save("state", state)
    for s in (0, 4):
        if s == slot:
            save(BASE_FILE[s], bytes(base))
            save(SIDE_FILE[s], bytes(side))
            save(EVENT_FILE[s], bytes(events))
        else:
            save(BASE_FILE[s], bytes(16))
            save(SIDE_FILE[s], bytes(0x500))
            save(EVENT_FILE[s], bytes(64))


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_snapshot(root, "snap0", "identity", 0, "A")
        result = classify(root)
        assert result["passed"] and result["slot"] == 0 and result["phase"] == "A"

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_snapshot(root, "snap0", "word_swap32", 4, "B")
        result = classify(root)
        assert result["passed"] and result["slot"] == 4 and result["phase"] == "B"
        assert result["normalization"] == "word_swap32"

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_snapshot(root, "snap0", "identity", 0, "A")
        state = bytearray((root / "snap0-state.bin").read_bytes())
        state[10] = 1
        (root / "snap0-state.bin").write_bytes(state)
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
        print("CGRAM epoch dynamic classifier self-test: PASS")
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
