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
ROOT = Path(__file__).resolve().parents[1]


def prove_terminal_sentinel_source_contract() -> None:
    """Prove why the final make_section marker is not part of rendered replay."""
    ppu = (ROOT / "src/ppu.S").read_text()
    rsp = (ROOT / "src/rsp_main.S").read_text()

    make = ppu[ppu.index("make_section: // a0: line"):ppu.index(".align 5\nhcomp_cgram_begin_frame:")]
    if "section_init:" not in make:
        raise AssertionError("make_section no longer falls through section_init")
    if "sw t3, 0(t1)" not in make or "hcomp_cgram_event_count" not in make:
        raise AssertionError("section_init no longer appends the typed section marker")

    frame = ppu[ppu.index("rsp_frame:"):ppu.index("ignore_frame:")]
    anchors = (
        "lhu a0, cur_line",
        "jal make_section",
        "addi t2, t2, -1",
        "sw t2, DMEM(FRAME_END)(t5)",
        "sw t0, DMEM(HCOMP_CGRAM_EVENT_CURSOR)",
    )
    for anchor in anchors:
        if anchor not in frame:
            raise AssertionError(f"terminal sentinel CPU contract missing {anchor!r}")
    if not (
        frame.index("lhu a0, cur_line")
        < frame.index("jal make_section")
        < frame.index("addi t2, t2, -1")
        < frame.index("sw t2, DMEM(FRAME_END)(t5)")
        < frame.index("sw t0, DMEM(HCOMP_CGRAM_EVENT_CURSOR)")
    ):
        raise AssertionError("terminal sentinel CPU ordering drift")

    next_section = rsp[rsp.index("next_section:"):rsp.index("hcomp_cgram_return:")]
    anchors = (
        "lw t0, FRAME_END(sp)",
        "beq k1, t0, next_frame",
        "lw a1, SECTION_PTR(sp)",
        "b hcomp_cgram_consume",
    )
    for anchor in anchors:
        if anchor not in next_section:
            raise AssertionError(f"terminal sentinel RSP contract missing {anchor!r}")
    if not (
        next_section.index("lw t0, FRAME_END(sp)")
        < next_section.index("beq k1, t0, next_frame")
        < next_section.index("lw a1, SECTION_PTR(sp)")
        < next_section.index("b hcomp_cgram_consume")
    ):
        raise AssertionError("RSP no longer stops before loading trailing section")


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

    # This deterministic guest closes one rendered section and rsp_frame then
    # falls through section_init once more, producing one trailing marker for
    # the next (unrendered) section. The RSP must stop at FRAME_END before it.
    rendered = [
        ("marker", -1, 0x0000),
        *[("color", i, v) for i, v in EXPECTED_COLORS],
        ("marker", -1, ACTIVE_FIXED),
    ]
    expected = rendered + [("marker", -1, ACTIVE_FIXED)]
    if records != expected:
        raise ValueError(f"Q1 deterministic stream mismatch: {records} != {expected}")

    return records, {
        "record_count": len(records),
        "rendered_record_count": len(rendered),
        "marker_count": 3,
        "active_marker_count": 2,
        "terminal_sentinel_count": 1,
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
    # EA0 is a logical next-record cursor. The final nonzero record is the
    # source-proven marker for the next unrendered section, so consuming it
    # would be wrong. Require the cursor immediately after the marker that
    # terminates the last rendered section and immediately before the sentinel.
    consumed_count = int(stream_info["rendered_record_count"])
    expected_ea0 = EVENT_Q1 + consumed_count * 4
    if ea0 != expected_ea0:
        return {
            "passed": False,
            "prefix": prefix,
            "normalization": mode,
            "reason": "EA0 is not between rendered terminator and terminal sentinel",
            "ea0": f"0x{ea0:08X}",
            "expected_ea0": f"0x{expected_ea0:08X}",
            "consumed_record_count": consumed_count,
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
        "consumed_record_count": consumed_count,
        "terminal_sentinel_unconsumed": True,
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
    records.append(encode_record("marker", -1, ACTIVE_FIXED))  # terminal sentinel

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
        f"{EVENT_Q1 + (len(records) - 1) * 4:08x}\n", encoding="utf-8"
    )


def self_test() -> None:
    prove_terminal_sentinel_source_contract()
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

    # Consuming the terminal next-section marker must fail too; the proof is
    # specifically about stopping at FRAME_END with that sentinel untouched.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        (root / "snap0-ea0.txt").write_text(
            f"{EVENT_Q1 + (len(EXPECTED_COLORS) + 3) * 4:08x}\n", encoding="utf-8"
        )
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

    prove_terminal_sentinel_source_contract()
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
