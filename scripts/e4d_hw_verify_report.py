#!/usr/bin/env python3
"""Decode a Sodium64 E4d real-N64 correctness SRAM capture."""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

MAGIC = 0x53363445  # S64E
VERSION = 1
TEST_ID = 0x45344431  # E4D1
RECORD_SIZE = 0x80
END_MARKER = 0x454E4421  # END!

ROW_MAGIC = 0x53363452  # S64R
ROW_VERSION = 1
ROW_END = 0x524F5721  # ROW!

FLAG_PASS = 0x01
FLAG_FRESH = 0x02
FLAG_SP_HALT = 0x04
FLAG_DP_IDLE = 0x08
FLAG_FB_VALID = 0x10
REQUIRED_FLAGS = FLAG_FRESH | FLAG_SP_HALT | FLAG_DP_IDLE | FLAG_FB_VALID


@dataclass(frozen=True)
class E4dCapture:
    capture_format: str
    version: int
    test_id: int
    complete: int
    flags: int
    baseline_counter: int
    final_counter: int
    counter_delta: int
    sp_status: int
    dp_status: int
    framebuffer: int
    active_mismatches: int
    border_mismatches: int
    blue_count: int
    red_count: int
    yellow_count: int
    other_count: int
    first_active_xy: int
    first_active_actual_expected: int
    first_border_xy: int
    first_border_actual_expected: int
    seed_sp_status: int
    seed_dp_status: int
    seed_counter: int
    expected_active: int
    expected_border: int
    seed_stage: int
    checksum: int
    record_size: int
    sentinel: int
    end_marker: int

    @property
    def passed(self) -> bool:
        return bool(self.flags & FLAG_PASS)


def normalize_save(blob: bytes) -> tuple[bytes, str]:
    if len(blob) < RECORD_SIZE:
        raise ValueError(f"save is only {len(blob)} bytes; need at least {RECORD_SIZE}")

    if struct.unpack_from(">I", blob, 0)[0] == MAGIC:
        return blob, "canonical big-endian"

    if len(blob) % 4:
        raise ValueError("bad S64E magic and size is not divisible by four")

    if struct.unpack_from("<I", blob, 0)[0] == MAGIC:
        return (
            b"".join(blob[i:i + 4][::-1] for i in range(0, len(blob), 4)),
            "32-bit word-swapped",
        )

    got = struct.unpack_from(">I", blob, 0)[0]
    raise ValueError(f"bad S64E magic 0x{got:08X}; expected 0x{MAGIC:08X}")


def _xy(word: int) -> tuple[int, int] | None:
    if word == 0xFFFFFFFF:
        return None
    return word & 0xFFFF, (word >> 16) & 0xFFFF


def _actual_expected(word: int) -> tuple[int, int]:
    return (word >> 16) & 0xFFFF, word & 0xFFFF


def parse_capture(blob: bytes) -> E4dCapture:
    blob, capture_format = normalize_save(blob)
    words = struct.unpack_from(">32I", blob, 0)

    capture = E4dCapture(
        capture_format=capture_format,
        version=words[1],
        test_id=words[2],
        complete=words[3],
        flags=words[4],
        baseline_counter=words[5],
        final_counter=words[6],
        counter_delta=words[7],
        sp_status=words[8],
        dp_status=words[9],
        framebuffer=words[10],
        active_mismatches=words[11],
        border_mismatches=words[12],
        blue_count=words[13],
        red_count=words[14],
        yellow_count=words[15],
        other_count=words[16],
        first_active_xy=words[17],
        first_active_actual_expected=words[18],
        first_border_xy=words[19],
        first_border_actual_expected=words[20],
        seed_sp_status=words[21],
        seed_dp_status=words[22],
        seed_counter=words[23],
        expected_active=words[24],
        expected_border=words[25],
        seed_stage=words[26],
        checksum=words[28],
        record_size=words[29],
        sentinel=words[30],
        end_marker=words[31],
    )

    if capture.version != VERSION:
        raise ValueError(f"unsupported S64E version {capture.version}; expected {VERSION}")
    if capture.test_id != TEST_ID:
        raise ValueError(f"wrong S64E test id 0x{capture.test_id:08X}; expected E4D1")
    if capture.complete != 1:
        raise ValueError("S64E capture is not marked complete; do not interpret a partial save")
    if capture.record_size != RECORD_SIZE:
        raise ValueError(f"wrong S64E record size 0x{capture.record_size:X}")
    if capture.end_marker != END_MARKER:
        raise ValueError(f"bad S64E end marker 0x{capture.end_marker:08X}")
    if capture.expected_active != 4096 or capture.expected_border != 2624:
        raise ValueError(
            "capture oracle geometry does not match E4d contract: "
            f"active={capture.expected_active} border={capture.expected_border}"
        )
    if capture.sentinel != 0x294B or capture.seed_stage != 1:
        raise ValueError(
            f"bad clean-epoch metadata: sentinel=0x{capture.sentinel:04X} "
            f"seed_stage={capture.seed_stage}"
        )

    checksum = 0
    for index, word in enumerate(words):
        if index != 28:
            checksum ^= word
    if checksum != capture.checksum:
        raise ValueError(
            f"S64E checksum mismatch: stored=0x{capture.checksum:08X} "
            f"computed=0x{checksum:08X}"
        )

    required_ok = (capture.flags & REQUIRED_FLAGS) == REQUIRED_FLAGS
    pixel_ok = capture.active_mismatches == 0 and capture.border_mismatches == 0
    if capture.passed != (required_ok and pixel_ok):
        raise ValueError(
            "PASS flag is inconsistent with recorded freshness/quiescence/pixel evidence"
        )

    if capture.passed:
        expected_hist = (2048, 1024, 1024, 0)
        got_hist = (
            capture.blue_count,
            capture.red_count,
            capture.yellow_count,
            capture.other_count,
        )
        if got_hist != expected_hist:
            raise ValueError(
                f"PASS capture has impossible active histogram {got_hist}; "
                f"expected {expected_hist}"
            )

    return capture


def parse_row_extension(blob: bytes) -> list[tuple[int, int]] | None:
    blob, _ = normalize_save(blob)
    if len(blob) < 0xD0:
        return None
    if struct.unpack_from(">I", blob, 0x80)[0] != ROW_MAGIC:
        return None
    version = struct.unpack_from(">I", blob, 0x84)[0]
    if version != ROW_VERSION:
        raise ValueError(f"unsupported S64R version {version}")
    end_marker = struct.unpack_from(">I", blob, 0xCC)[0]
    if end_marker != ROW_END:
        raise ValueError(f"bad S64R end marker 0x{end_marker:08X}")

    words = list(struct.unpack_from(">20I", blob, 0x80))
    stored = words[18]
    checksum = 0
    for index, word in enumerate(words):
        if index != 18:
            checksum ^= word
    if checksum != stored:
        raise ValueError(
            f"S64R checksum mismatch: stored=0x{stored:08X} computed=0x{checksum:08X}"
        )

    rows = []
    for word in words[2:18]:
        rows.append(((word >> 16) & 0xFFFF, word & 0xFFFF))
    return rows


def render_text(c: E4dCapture, rows: list[tuple[int, int]] | None = None) -> str:
    lines = [
        "Sodium64 real-N64 E4d resident color-math capture",
        f"  save format:       {c.capture_format}",
        f"  test/version:      E4D1 / {c.version}",
        f"  result:            {'PASS' if c.passed else 'FAIL'}",
        f"  guest counter:     {c.baseline_counter} -> {c.final_counter} (delta {c.counter_delta})",
        f"  framebuffer:       0x{c.framebuffer:08X}",
        f"  SP status:         0x{c.sp_status:08X} ({'HALT' if c.flags & FLAG_SP_HALT else 'NOT HALTED'})",
        f"  DP status:         0x{c.dp_status:08X} ({'idle' if c.flags & FLAG_DP_IDLE else 'busy'})",
        f"  active pixels:     {4096 - c.active_mismatches}/4096 correct",
        f"  border pixels:     {2624 - c.border_mismatches}/2624 correct",
        "  active histogram: "
        f"blue={c.blue_count} red={c.red_count} yellow={c.yellow_count} other={c.other_count}",
    ]

    if c.active_mismatches:
        xy = _xy(c.first_active_xy)
        actual, expected = _actual_expected(c.first_active_actual_expected)
        lines.append(
            f"  first active miss: x={xy[0] if xy else '?'} y={xy[1] if xy else '?'} "
            f"actual=0x{actual:04X} expected=0x{expected:04X}"
        )
    if c.border_mismatches:
        xy = _xy(c.first_border_xy)
        actual, expected = _actual_expected(c.first_border_actual_expected)
        lines.append(
            f"  first border miss: x={xy[0] if xy else '?'} y={xy[1] if xy else '?'} "
            f"actual=0x{actual:04X} expected=0x{expected:04X}"
        )

    if rows is not None:
        lines.append("  row diagnostics:")
        for index, (mismatches, first_pixel) in enumerate(rows):
            lines.append(
                f"    y={index + 8:02d}: mismatches={mismatches:3d} "
                f"x12_actual=0x{first_pixel:04X}"
            )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path, help="raw N64/SummerCart/EverDrive SRAM save")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    blob = args.save.read_bytes()
    capture = parse_capture(blob)
    rows = parse_row_extension(blob)
    if args.json:
        payload = asdict(capture) | {"passed": capture.passed}
        if rows is not None:
            payload["row_diagnostics"] = [
                {
                    "y": index + 8,
                    "mismatches": mismatches,
                    "x12_actual": first_pixel,
                }
                for index, (mismatches, first_pixel) in enumerate(rows)
            ]
        print(json.dumps(payload, indent=2))
    else:
        print(render_text(capture, rows), end="")
    return 0 if capture.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
