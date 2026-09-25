#!/usr/bin/env python3
"""Classify first-hand CGRAM-history -> H-COMP bridge execution evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENT_Q1 = 0xA00BF000
RAW_Q1 = 0xA00EF000
ACTIVE_FIXED = 0x1CE7
EXPECTED_COLORS = (
    (3, 0x1357),
    (1, 0x1234),
    (1, 0x4567),
    (0, 0x2AAA),
    (2, 0x7FFF),
)
EXPECTED_RAW_RGB = {0: 0x2AAA, 1: 0x4567, 2: 0x7FFF, 3: 0x1357}
EXPECTED_BRIDGE = {4: 0x7BDF, 5: 0x7BD5}
CONTROL_INDEX = 6
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


def half_add_rgb555(a: int, b: int) -> int:
    out = 0
    for shift in (0, 5, 10):
        ca = (a >> shift) & 0x1F
        cb = (b >> shift) & 0x1F
        out |= (min(ca + cb, 31) >> 1) << shift
    return out


def prove_semantic_discriminator() -> None:
    got4 = rgb555_to_rgba5551(half_add_rgb555(0x2AAA, 0x7FFF))
    got5 = rgb555_to_rgba5551(half_add_rgb555(0x4567, 0x1357))
    if (got4, got5) != (0x7BDF, 0x7BD5):
        raise AssertionError(f"bridge discriminator drift: {(got4, got5)!r}")


def instruction_count(text: str) -> int:
    count = 0
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"):
            continue
        count += 1
    return count


def prove_source_contract() -> None:
    main = (ROOT / "src/rsp_main.S").read_text()
    mode7 = (ROOT / "src/rsp_mode7.S").read_text()

    for name, src in (("main", main), ("mode7", mode7)):
        for anchor in (
            "hcomp_bridge_carrylo:",
            "hcomp_bridge_carryhi:",
            ".byte 0:0x40",
            "hcomp_cgram_marker:",
            "b overlay_load_mode7\n    lbu k1, SPLIT_LINE",
            "overlay_load_main:",
            "b hcomp_cgram_return\n    move t0, v0",
            "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
            "jal dma_write\n    li a2, 0x7",
        ):
            if anchor not in src:
                raise AssertionError(f"{name}: missing bridge/consumer anchor {anchor!r}")

        # Consumer still advances the same logical cursor and writes the same
        # aligned 8-byte historical-palette entries before the proof hook.
        tail = src[src.index("hcomp_cgram_pair_ready:"):]
        for anchor in (
            "addi t6, t6, 4",
            "sw t6, HCOMP_CGRAM_EVENT_CURSOR",
            "andi t0, t8, 0x7F8",
            "li a0, HCOMP_CGRAM_WRITE_SCRATCH",
            "jal dma_write\n    li a2, 0x7",
            "b hcomp_cgram_consume\n    nop",
        ):
            if anchor not in tail:
                raise AssertionError(f"{name}: consumer semantic anchor drift {anchor!r}")

    if "hcomp_bridge_probe:" in main:
        raise AssertionError("regular renderer slot was replaced; proof isolation lost")
    if mode7.count("hcomp_bridge_probe:") != 1:
        raise AssertionError("Mode7 proof slot must contain exactly one bridge probe")
    if "draw_mode7_impl:" in mode7:
        raise AssertionError("old Mode7 implementation survived proof-only slot replacement")

    probe = mode7[mode7.index("hcomp_bridge_probe:"):mode7.index("    // Keep the external entry", mode7.index("hcomp_bridge_probe:"))]
    if instruction_count(probe) != 40:
        raise AssertionError(f"bridge body is {instruction_count(probe)} instructions, expected 40")

    required_vector_sequence = (
        "vmudl $v00, $v00, $v24, 8",
        "vmudl $v01, $v01, $v24, 8",
        "vxor $v03, $v00, $v01, 0",
        "vand $v03, $v03, $v17, 0",
        "vaddc $v04, $v00, $v01, 0",
        "vsubc $v05, $v04, $v03, 0",
        "vand $v05, $v05, $v18, 0",
        "vsubc $v04, $v04, $v05, 0",
        "vmudl $v06, $v05, $v24, 12",
        "vsubc $v05, $v05, $v06, 0",
        "vor $v04, $v04, $v05, 0",
        "vand $v04, $v04, $v19, 0",
        "vor $v04, $v04, $v20, 0",
    )
    last = -1
    for anchor in required_vector_sequence:
        pos = probe.find(anchor)
        if pos < 0 or pos <= last:
            raise AssertionError(f"vector core missing/reordered {anchor!r}")
        last = pos

    if ".byte 0:0x340" not in mode7:
        raise AssertionError("proof slot exact padding missing")
    entry = mode7[mode7.index("draw_mode7_entry:"):mode7.index("\n\ndraw_obj:", mode7.index("draw_mode7_entry:"))]
    if instruction_count(entry) != 2 or "b hcomp_bridge_probe" not in entry:
        raise AssertionError("external Mode7 entry trampoline drift")

    # Terminal-sentinel contract remains source-grounded even though rendered
    # markers now route through the proof overlay.
    ppu = (ROOT / "src/ppu.S").read_text()
    make = ppu[ppu.index("make_section: // a0: line"):ppu.index(".align 5\nhcomp_cgram_begin_frame:")]
    if "section_init:" not in make or "sw t3, 0(t1)" not in make:
        raise AssertionError("CPU terminal-sentinel generation drift")
    next_section = main[main.index("next_section:"):main.index("hcomp_cgram_return:")]
    if not (
        next_section.index("lw t0, FRAME_END(sp)")
        < next_section.index("beq k1, t0, next_frame")
        < next_section.index("lw a1, SECTION_PTR(sp)")
        < next_section.index("b hcomp_cgram_consume")
    ):
        raise AssertionError("RSP terminal-sentinel stop ordering drift")


def parse_symbols(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in path.read_text().splitlines():
        # readelf -sW: Num: Value Size Type Bind Vis Ndx Name
        parts = line.split()
        if len(parts) >= 8 and parts[0].rstrip(":").isdigit():
            try:
                value = int(parts[1], 16)
            except ValueError:
                continue
            out[parts[-1]] = value
    return out


def parse_text_size(path: Path) -> int:
    text = path.read_text()
    m = re.search(r"^\.text\s+0xa4001000\s+0x([0-9a-fA-F]+)\b", text, re.M)
    if not m:
        raise AssertionError(f"{path}: .text size missing")
    return int(m.group(1), 16)


def prove_binary(maps: list[Path], symbols: list[Path]) -> None:
    if len(maps) != 2 or len(symbols) != 2:
        raise AssertionError("need regular+Mode7 map/symbol files")
    for mp in maps:
        if parse_text_size(mp) != 0x1000:
            raise AssertionError(f"{mp}: RSP text no longer exactly 0x1000")

    reg = parse_symbols(symbols[0])
    m7 = parse_symbols(symbols[1])
    for name, syms in (("regular", reg), ("mode7", m7)):
        if syms.get("draw_bg") != 0xA40013A8:
            raise AssertionError(f"{name}: draw_bg moved")
        if syms.get("draw_obj") != 0xA4001790:
            raise AssertionError(f"{name}: draw_obj moved")
        if syms.get("hcomp_bridge_carrylo", 0) & 0xFFF != 0xF10:
            raise AssertionError(f"{name}: carrylo not at F10")
        if syms.get("hcomp_bridge_carryhi", 0) & 0xFFF != 0xF20:
            raise AssertionError(f"{name}: carryhi not at F20")
        if syms.get("vec_data", 0) & 0xFFF != 0xF70:
            raise AssertionError(f"{name}: VEC_DATA moved")
    if "hcomp_bridge_probe" in reg:
        raise AssertionError("regular binary contains proof probe")
    if m7.get("hcomp_bridge_probe") != 0xA40013A8:
        raise AssertionError("Mode7 probe not at fixed slot start")
    if m7.get("draw_mode7_entry") != 0xA4001788:
        raise AssertionError("Mode7 external entry moved")


def decode_record(rec: bytes) -> tuple[str, int, int]:
    word = int.from_bytes(rec, "big")
    payload = (word >> 16) & 0xFFFF
    meta = word & 0xFFFF
    if not (payload & 1):
        raise ValueError(f"payload alpha clear 0x{word:08X}")
    rgb = rgba5551_to_rgb555(payload)
    if meta == 0x8000:
        return ("marker", -1, rgb)
    if meta & 0x8000 or meta > 0x7F8 or meta & 7:
        raise ValueError(f"invalid metadata 0x{meta:04X}")
    return ("color", meta >> 3, rgb)


def parse_stream(data: bytes) -> tuple[list[tuple[str, int, int]], int]:
    records = []
    for i in range(MAX_RECORDS):
        rec = data[i * 4:(i + 1) * 4]
        if len(rec) < 4 or rec == b"\0\0\0\0":
            break
        records.append(decode_record(rec))
    rendered = [
        ("marker", -1, 0),
        *[("color", i, v) for i, v in EXPECTED_COLORS],
        ("marker", -1, ACTIVE_FIXED),
    ]
    expected = rendered + [("marker", -1, ACTIVE_FIXED)]
    if records != expected:
        raise ValueError(f"stream mismatch {records!r}")
    return records, len(rendered)


def raw_word(data: bytes, index: int) -> int:
    rec = data[index * 8:(index + 1) * 8]
    if len(rec) != 8:
        raise ValueError(f"short raw entry {index}")
    words = [int.from_bytes(rec[i:i + 2], "big") for i in range(0, 8, 2)]
    if len(set(words)) != 1:
        raise ValueError(f"raw entry {index} not duplicated: {words!r}")
    return words[0]


def classify_snapshot(root: Path, prefix: str, mode: str) -> dict[str, object]:
    event = norm((root / f"{prefix}-event-q1.bin").read_bytes(), mode)
    raw = norm((root / f"{prefix}-raw-q1.bin").read_bytes(), mode)
    records, consumed = parse_stream(event)
    ea0 = int((root / f"{prefix}-ea0.txt").read_text().strip(), 16)
    expected_ea0 = EVENT_Q1 + consumed * 4
    if ea0 != expected_ea0:
        raise ValueError(f"EA0 0x{ea0:08X} != 0x{expected_ea0:08X}")

    raw_report: dict[str, str] = {}
    for index, rgb in EXPECTED_RAW_RGB.items():
        got = raw_word(raw, index)
        want = rgb555_to_rgba5551(rgb)
        if got != want:
            raise ValueError(f"consumer raw{index}=0x{got:04X} != 0x{want:04X}")
        raw_report[str(index)] = f"0x{got:04X}"

    bridge_report: dict[str, str] = {}
    for index, want in EXPECTED_BRIDGE.items():
        got = raw_word(raw, index)
        if got != want:
            raise ValueError(f"bridge raw{index}=0x{got:04X} != 0x{want:04X}")
        bridge_report[str(index)] = f"0x{got:04X}"

    control = raw_word(raw, CONTROL_INDEX)
    if control != 0:
        raise ValueError(f"control raw{CONTROL_INDEX}=0x{control:04X} != 0")

    return {
        "classification": "CGRAM_HCOMP_BRIDGE_DYNAMIC_VALIDATED",
        "passed": True,
        "prefix": prefix,
        "normalization": mode,
        "ea0": f"0x{ea0:08X}",
        "expected_ea0": f"0x{expected_ea0:08X}",
        "records": len(records),
        "rendered_records_consumed": consumed,
        "terminal_sentinel_unconsumed": True,
        "consumer_raw_entries": raw_report,
        "bridge_raw_entries": bridge_report,
        "untouched_control_index": CONTROL_INDEX,
        "untouched_control_value": "0x0000",
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
                attempts.append({"passed": False, "prefix": prefix, "normalization": mode, "reason": str(exc)})
                continue
            return {**result, "snapshots_seen": len(ps), "attempts_before_pass": len(attempts)}
    return {"classification": "CGRAM_HCOMP_BRIDGE_DYNAMIC_FAILED", "passed": False, "snapshots_seen": len(ps), "attempts": attempts}


def encode_record(kind: str, index: int, rgb: int) -> bytes:
    payload = rgb555_to_rgba5551(rgb)
    meta = 0x8000 if kind == "marker" else index * 8
    return ((payload << 16) | meta).to_bytes(4, "big")


def write_fixture(root: Path, mode: str) -> None:
    records = [encode_record("marker", -1, 0)]
    records += [encode_record("color", i, v) for i, v in EXPECTED_COLORS]
    records += [encode_record("marker", -1, ACTIVE_FIXED), encode_record("marker", -1, ACTIVE_FIXED)]
    event = bytearray(256)
    for i, rec in enumerate(records):
        event[i * 4:(i + 1) * 4] = rec
    raw = bytearray(64)
    for index, rgb in EXPECTED_RAW_RGB.items():
        payload = rgb555_to_rgba5551(rgb).to_bytes(2, "big")
        raw[index * 8:(index + 1) * 8] = payload * 4
    for index, word in EXPECTED_BRIDGE.items():
        raw[index * 8:(index + 1) * 8] = word.to_bytes(2, "big") * 4

    if mode == "word_swap32":
        event = bytearray(swap32(bytes(event)))
        raw = bytearray(swap32(bytes(raw)))
    (root / "snap0-event-q1.bin").write_bytes(event)
    (root / "snap0-raw-q1.bin").write_bytes(raw)
    (root / "snap0-ea0.txt").write_text(f"{EVENT_Q1 + (len(records)-1)*4:08x}\n")


def self_test() -> None:
    prove_semantic_discriminator()
    prove_source_contract()
    for mode in ("identity", "word_swap32"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, mode)
            assert classify(root)["passed"]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        raw = bytearray((root / "snap0-raw-q1.bin").read_bytes())
        raw[4 * 8:5 * 8] = b"\0" * 8
        (root / "snap0-raw-q1.bin").write_bytes(raw)
        assert not classify(root)["passed"]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        (root / "snap0-ea0.txt").write_text(f"{EVENT_Q1 + (len(EXPECTED_COLORS)+3)*4:08x}\n")
        assert not classify(root)["passed"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence", type=Path, nargs="?")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--maps", nargs=2, type=Path)
    ap.add_argument("--symbols", nargs=2, type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--guest", type=Path)
    args = ap.parse_args()

    prove_semantic_discriminator()
    prove_source_contract()
    if args.maps or args.symbols:
        if not args.maps or not args.symbols:
            ap.error("--maps and --symbols must be provided together")
        prove_binary(args.maps, args.symbols)

    if args.self_test:
        self_test()
        print("CGRAM H-COMP bridge dynamic classifier self-test: PASS")
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
