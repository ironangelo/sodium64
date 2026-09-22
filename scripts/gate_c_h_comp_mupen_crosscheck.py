#!/usr/bin/env python3
"""Generate and classify the Gate-C E4b Mupen64Plus + Angrylion crosscheck.

The runtime under test is intentionally unchanged from the original-Main
color-landing diagnostic. This helper only drives the Mupen debugger:
  1. break at rsp_wait+0x14 after a quiescent frame,
  2. seed the exact clean-epoch proof memory,
  3. run exactly to the next capture-ready hit,
  4. dump raw RDRAM for host-side classification.

Mupen's dumpmem writes its internal RDRAM byte layout directly. The classifier
detects whether 32-bit word unswapping is required from the pre-seeded oracle
instead of assuming host endianness.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

FB_WIDTH = 280
FB_HEIGHT = 240
FB_BYTES = FB_WIDTH * FB_HEIGHT * 2
ROWS_0_23_BYTES = 24 * FB_WIDTH * 2
ROWS_0_7_BYTES = 8 * FB_WIDTH * 2
ROWS_8_23_BYTES = 16 * FB_WIDTH * 2

Z_COMMAND_ADDR = 0xA00BEE80
Z_BASE = 0xA00C0000
Z_SIZE = FB_BYTES
Z_PREFIX_SIZE = Z_BASE - Z_COMMAND_ADDR
Z_SUFFIX_SIZE = 64
STATUS_ADDR = 0xA00E1000
STATUS_MARKER = 0xE1F00D01
STATUS_SIZE = 8

PREFIX_BYTE = 0xC3
SENTINEL_WORD = 0x55AA
SUFFIX_BYTE = 0x3C

E2G_SECOND_Z_ADDR = 0xA00C2000
E2G_SECOND_Z_PREFIX_ADDR = 0xA00C1FC0
E2G_SECOND_Z_SUFFIX_ADDR = 0xA00C3180
E2G_SECOND_Z_PREFIX_BYTE = 0xD6
E2G_SECOND_Z_SUFFIX_BYTE = 0x6D
COMPACT_SIZE = 0x1180
GUARD_SIZE = 64

E2A_COLOR_SCRATCH_ADDR = 0xA00E4000
E2A_COLOR_ARCHIVE_A_ADDR = 0xA00E6000
E2A_COLOR_PREFIX_GUARD_ADDR = 0xA00E3FC0
E2A_COLOR_SUFFIX_GUARD_ADDR = 0xA00E5180
E2A_MAIN_BEFORE_ADDR = 0xA00E8000
E2A_MAIN_AFTER_ADDR = 0xA00EA000
E2A_ARCHIVE_INIT = 0xCC
E2A_MAIN_BEFORE_INIT = 0xA6
E2A_MAIN_AFTER_INIT = 0x5B

MAIN_SENTINEL_WORD = 0x294B
FRAMEBUFFER_ADDRS = (
    0xA00F2300,
    0xA0113000,
    0xA0133D00,
)

RAW_RED = 0xF801
RAW_BLUE = 0x003F
BOOL_FALSE = 0x0400
BOOL_TRUE = 0x0C00
ACTIVE_X0 = 12
ACTIVE_X1 = 268


def parse_int(text: str) -> int:
    return int(text, 0)


def repeated_byte_dword(value: int) -> int:
    return int.from_bytes(bytes([value & 0xFF]) * 8, "big")


def repeated_half_dword(value: int) -> int:
    return int.from_bytes((value & 0xFFFF).to_bytes(2, "big") * 4, "big")


def emit_fill(lines: list[str], address: int, size: int, dword: int) -> None:
    if address & 7:
        raise ValueError(f"unaligned fill address: 0x{address:08X}")
    if size & 7:
        raise ValueError(f"unaligned fill size: 0x{size:X}")
    for offset in range(0, size, 8):
        lines.append(f"write 0x{address + offset:08X} d 0x{dword:016X}")


def emit_dump(lines: list[str], address: int, size: int, name: str) -> None:
    lines.append(f"dumpmem 0x{address:08X} 0x{size:X} {name}")


def build_commands(capture_ready: int, guest_counter: int) -> list[str]:
    lines: list[str] = []
    lines.append(f"bp add 0x{capture_ready:08X} 1 8")
    lines.append("run")

    # First capture-ready hit: stop before update_menu/menu_return, record the
    # guest counter, then establish the same clean epoch used by the ares lab.
    counter_base = guest_counter & ~3
    emit_dump(lines, counter_base, 4, "pre-counter.raw")

    emit_fill(lines, Z_COMMAND_ADDR, Z_PREFIX_SIZE, repeated_byte_dword(PREFIX_BYTE))
    emit_fill(lines, Z_BASE, Z_SIZE, repeated_half_dword(SENTINEL_WORD))
    emit_fill(lines, Z_BASE + Z_SIZE, Z_SUFFIX_SIZE, repeated_byte_dword(SUFFIX_BYTE))
    emit_fill(lines, STATUS_ADDR, STATUS_SIZE, 0)

    emit_fill(
        lines,
        E2G_SECOND_Z_PREFIX_ADDR,
        GUARD_SIZE,
        repeated_byte_dword(E2G_SECOND_Z_PREFIX_BYTE),
    )
    emit_fill(lines, E2G_SECOND_Z_ADDR, COMPACT_SIZE, repeated_half_dword(SENTINEL_WORD))
    emit_fill(
        lines,
        E2G_SECOND_Z_SUFFIX_ADDR,
        GUARD_SIZE,
        repeated_byte_dword(E2G_SECOND_Z_SUFFIX_BYTE),
    )

    emit_fill(lines, E2A_COLOR_PREFIX_GUARD_ADDR, GUARD_SIZE, repeated_byte_dword(PREFIX_BYTE))
    emit_fill(lines, E2A_COLOR_SCRATCH_ADDR, COMPACT_SIZE, repeated_half_dword(SENTINEL_WORD))
    emit_fill(lines, E2A_COLOR_SUFFIX_GUARD_ADDR, GUARD_SIZE, repeated_byte_dword(SUFFIX_BYTE))
    emit_fill(lines, E2A_COLOR_ARCHIVE_A_ADDR, COMPACT_SIZE, repeated_byte_dword(E2A_ARCHIVE_INIT))
    emit_fill(lines, E2A_MAIN_BEFORE_ADDR, COMPACT_SIZE, repeated_byte_dword(E2A_MAIN_BEFORE_INIT))
    emit_fill(lines, E2A_MAIN_AFTER_ADDR, COMPACT_SIZE, repeated_byte_dword(E2A_MAIN_AFTER_INIT))

    for fb in FRAMEBUFFER_ADDRS:
        emit_fill(lines, fb, ROWS_0_7_BYTES, repeated_half_dword(MAIN_SENTINEL_WORD))
        emit_fill(
            lines,
            fb + ROWS_0_7_BYTES,
            ROWS_8_23_BYTES,
            repeated_half_dword(MAIN_SENTINEL_WORD),
        )

    # Pre-run dumps prove the debugger writes established the requested epoch.
    emit_dump(lines, STATUS_ADDR, STATUS_SIZE, "pre-status.raw")
    emit_dump(lines, Z_BASE, Z_SIZE, "pre-z.raw")
    emit_dump(lines, E2G_SECOND_Z_ADDR, COMPACT_SIZE, "pre-main-z.raw")
    emit_dump(lines, E2A_COLOR_SCRATCH_ADDR, COMPACT_SIZE, "pre-compact.raw")
    emit_dump(lines, E2A_COLOR_ARCHIVE_A_ADDR, COMPACT_SIZE, "pre-archive.raw")
    emit_dump(lines, E2A_MAIN_BEFORE_ADDR, COMPACT_SIZE, "pre-main-before.raw")
    emit_dump(lines, E2A_MAIN_AFTER_ADDR, COMPACT_SIZE, "pre-main-after.raw")
    for index, fb in enumerate(FRAMEBUFFER_ADDRS, 1):
        emit_dump(lines, fb, ROWS_0_23_BYTES, f"pre-fb{index}.raw")

    # Leave the current capture-ready instruction before re-arming the same
    # breakpoint. This prevents an immediate self-hit on resume.
    lines.append(f"bp rm 0x{capture_ready:08X}")
    lines.append("step")
    lines.append(f"bp add 0x{capture_ready:08X} 1 8")
    lines.append("run")

    # Second capture-ready hit: exactly one renderer frame later.
    emit_dump(lines, counter_base, 4, "post-counter.raw")
    emit_dump(lines, STATUS_ADDR, STATUS_SIZE, "post-status.raw")
    emit_dump(lines, Z_BASE, Z_SIZE, "post-z.raw")
    emit_dump(lines, E2G_SECOND_Z_ADDR, COMPACT_SIZE, "post-main-z.raw")
    emit_dump(lines, E2A_COLOR_SCRATCH_ADDR, COMPACT_SIZE, "post-compact.raw")
    emit_dump(lines, E2A_COLOR_ARCHIVE_A_ADDR, COMPACT_SIZE, "post-archive.raw")
    emit_dump(lines, E2A_MAIN_BEFORE_ADDR, COMPACT_SIZE, "post-main-before.raw")
    emit_dump(lines, E2A_MAIN_AFTER_ADDR, COMPACT_SIZE, "post-main-after.raw")
    for index, fb in enumerate(FRAMEBUFFER_ADDRS, 1):
        emit_dump(lines, fb, ROWS_0_23_BYTES, f"post-fb{index}.raw")
    lines.append("quit")
    return lines


def unswap32(data: bytes) -> bytes:
    if len(data) % 4:
        raise ValueError("raw dump length must be a multiple of 4 for word unswapping")
    out = bytearray(len(data))
    for i in range(0, len(data), 4):
        out[i:i + 4] = data[i:i + 4][::-1]
    return bytes(out)


def load_raw(root: Path, name: str) -> bytes:
    path = root / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_bytes()


def words16(data: bytes) -> list[int]:
    if len(data) % 2:
        raise ValueError("16-bit buffer has odd length")
    return [
        int.from_bytes(data[i:i + 2], "big")
        for i in range(0, len(data), 2)
    ]


def band_stats(framebuffer: bytes, row0: int, row1: int) -> dict[str, object]:
    active: list[int] = []
    border: list[int] = []
    for y in range(row0, row1):
        row = framebuffer[y * FB_WIDTH * 2:(y + 1) * FB_WIDTH * 2]
        row_words = words16(row)
        border.extend(row_words[:ACTIVE_X0])
        active.extend(row_words[ACTIVE_X0:ACTIVE_X1])
        border.extend(row_words[ACTIVE_X1:])

    ah = collections.Counter(active)
    bh = collections.Counter(border)
    return {
        "active_words": len(active),
        "border_words": len(border),
        "active_red": ah[RAW_RED],
        "active_blue": ah[RAW_BLUE],
        "active_main_sentinel": ah[MAIN_SENTINEL_WORD],
        "border_main_sentinel": bh[MAIN_SENTINEL_WORD],
        "active_top": [
            {"word": hex(word), "count": count}
            for word, count in ah.most_common(8)
        ],
        "border_top": [
            {"word": hex(word), "count": count}
            for word, count in bh.most_common(8)
        ],
    }


def all_pattern(data: bytes, pattern: bytes) -> bool:
    if not pattern or len(data) % len(pattern):
        return False
    return data == pattern * (len(data) // len(pattern))


def classify(root: Path, guest_counter: int) -> dict[str, object]:
    pre_fb1_raw = load_raw(root, "pre-fb1.raw")
    expected_fb = MAIN_SENTINEL_WORD.to_bytes(2, "big") * (ROWS_0_23_BYTES // 2)

    raw_matches = pre_fb1_raw == expected_fb
    swapped_matches = unswap32(pre_fb1_raw) == expected_fb
    if raw_matches == swapped_matches:
        raise RuntimeError(
            "cannot uniquely determine Mupen RDRAM dump byte layout from pre-fb1 seed"
        )
    transform = (lambda b: b) if raw_matches else unswap32
    layout = "guest-byte-order" if raw_matches else "mupen-word-swapped-32"

    def read(name: str) -> bytes:
        return transform(load_raw(root, name))

    pre_checks = {
        "status_zero": read("pre-status.raw") == bytes(STATUS_SIZE),
        "z_sentinel": all_pattern(
            read("pre-z.raw"), SENTINEL_WORD.to_bytes(2, "big")
        ),
        "main_z_sentinel": all_pattern(
            read("pre-main-z.raw"), SENTINEL_WORD.to_bytes(2, "big")
        ),
        "compact_sentinel": all_pattern(
            read("pre-compact.raw"), SENTINEL_WORD.to_bytes(2, "big")
        ),
        "archive_init": read("pre-archive.raw") == bytes([E2A_ARCHIVE_INIT]) * COMPACT_SIZE,
        "main_before_init": read("pre-main-before.raw") == bytes([E2A_MAIN_BEFORE_INIT]) * COMPACT_SIZE,
        "main_after_init": read("pre-main-after.raw") == bytes([E2A_MAIN_AFTER_INIT]) * COMPACT_SIZE,
    }
    for index in range(1, 4):
        pre_checks[f"fb{index}_seed"] = read(f"pre-fb{index}.raw") == expected_fb
    pre_ok = all(pre_checks.values())

    counter_base = guest_counter & ~3
    counter_offset = guest_counter - counter_base
    pre_counter = transform(load_raw(root, "pre-counter.raw"))[counter_offset]
    post_counter = transform(load_raw(root, "post-counter.raw"))[counter_offset]
    counter_delta = (post_counter - pre_counter) & 0xFF

    status = read("post-status.raw")
    marker = int.from_bytes(status[:4], "big")
    framebuffer_pointer = int.from_bytes(status[4:8], "big")
    pointer_map = {
        addr: read(f"post-fb{index}.raw")
        for index, addr in enumerate(FRAMEBUFFER_ADDRS, 1)
    }
    selected_fb = pointer_map.get(framebuffer_pointer)

    main_z = read("post-main-z.raw")
    main_z_hist = collections.Counter(words16(main_z))
    main_z_written = (
        main_z_hist[BOOL_FALSE] + main_z_hist[BOOL_TRUE] > 0
        and main_z_hist[SENTINEL_WORD] < len(main_z) // 2
    )

    compact = read("post-compact.raw")
    archive = read("post-archive.raw")
    compact_written = compact != SENTINEL_WORD.to_bytes(2, "big") * (COMPACT_SIZE // 2)
    archive_written = archive != bytes([E2A_ARCHIVE_INIT]) * COMPACT_SIZE

    if selected_fb is None:
        band0 = None
        band1 = None
        band0_healthy = False
        band0_missing = False
        band1_healthy = False
    else:
        band0 = band_stats(selected_fb, 0, 8)
        band1 = band_stats(selected_fb, 8, 16)
        band0_healthy = (
            band0["active_red"] == 1024
            and band0["active_blue"] == 1024
            and band0["active_main_sentinel"] == 0
            and band0["border_main_sentinel"] == 192
        )
        band0_missing = (
            band0["active_main_sentinel"] == 2048
            and band0["border_main_sentinel"] == 192
        )
        band1_healthy = (
            band1["active_red"] == 1024
            and band1["active_blue"] == 1024
            and band1["active_main_sentinel"] == 0
            and band1["border_main_sentinel"] == 192
        )

    controls_ok = bool(
        pre_ok
        and marker == STATUS_MARKER
        and framebuffer_pointer in FRAMEBUFFER_ADDRS
        and counter_delta == 1
        and band1_healthy
        and main_z_written
        and compact_written
        and archive_written
    )

    if controls_ok and band0_healthy:
        classification = "MUPEN_ANGLYLION_BAND0_MAIN_COLOR_VALID"
        decisive = True
    elif controls_ok and band0_missing:
        classification = "MUPEN_ANGLYLION_REPRODUCES_BAND0_MAIN_COLOR_MISSING"
        decisive = True
    else:
        classification = "MUPEN_ANGLYLION_CROSSCHECK_AMBIGUOUS"
        decisive = False

    return {
        "classification": classification,
        "passed": decisive,
        "dump_layout": layout,
        "pre_epoch": {
            "passed": pre_ok,
            "checks": pre_checks,
        },
        "capture": {
            "pre_guest_counter": pre_counter,
            "post_guest_counter": post_counter,
            "counter_delta": counter_delta,
            "status_marker": hex(marker),
            "status_marker_ok": marker == STATUS_MARKER,
            "framebuffer_pointer": hex(framebuffer_pointer),
            "framebuffer_pointer_known": framebuffer_pointer in FRAMEBUFFER_ADDRS,
        },
        "controls": {
            "passed": controls_ok,
            "band1_healthy": band1_healthy,
            "main_z_written": main_z_written,
            "compact_written": compact_written,
            "archive_written": archive_written,
            "main_z_counts": {
                "false_0x0400": main_z_hist[BOOL_FALSE],
                "true_0x0c00": main_z_hist[BOOL_TRUE],
                "sentinel_0x55aa": main_z_hist[SENTINEL_WORD],
            },
        },
        "band0": band0,
        "band1": band1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("commands")
    gen.add_argument("--capture-ready-address", required=True, type=parse_int)
    gen.add_argument("--guest-counter-address", required=True, type=parse_int)
    gen.add_argument("--output", required=True, type=Path)

    cls = sub.add_parser("classify")
    cls.add_argument("--guest-counter-address", required=True, type=parse_int)
    cls.add_argument("--input-dir", required=True, type=Path)
    cls.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()

    if args.command == "commands":
        lines = build_commands(args.capture_ready_address, args.guest_counter_address)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "commands": len(lines),
                    "bytes": args.output.stat().st_size,
                    "capture_ready_address": hex(args.capture_ready_address),
                    "guest_counter_address": hex(args.guest_counter_address),
                },
                indent=2,
            )
        )
        return 0

    result = classify(args.input_dir, args.guest_counter_address)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
