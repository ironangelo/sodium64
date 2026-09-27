#!/usr/bin/env python3
"""Strict seeded ares oracle for clean Main/Sub rendered color ownership."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_gate_c_hcomp_main_sub_lifetime import classify_queue  # noqa: E402

WIDTH = 280
ROWS = 8
STRIP_BYTES = WIDTH * ROWS * 2
ACTIVE_X0 = 12
ACTIVE_X1 = 268
ACTIVE_WORDS = (ACTIVE_X1 - ACTIVE_X0) * ROWS
BORDER_WORDS = (WIDTH - (ACTIVE_X1 - ACTIVE_X0)) * ROWS

SUB_COLOR_ADDR = 0xA00E4000
FRAMEBUFFER_ADDRS = (
    0xA00F2300,
    0xA0113000,
    0xA0133D00,
)
SECTION_QUEUE_ADDRS = (
    0xA016C600,
    0xA0171600,
)

SENTINEL = 0x55AA
SUB_GREEN = 0x07C1
MAIN_RED = 0xF801


def u16_words(data: bytes) -> list[int]:
    if len(data) != STRIP_BYTES:
        raise ValueError(f"strip length {len(data)} != {STRIP_BYTES}")
    return [int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2)]


def expected_rendered(active: int) -> list[int]:
    vals: list[int] = []
    for _y in range(ROWS):
        for x in range(WIDTH):
            vals.append(active if ACTIVE_X0 <= x < ACTIVE_X1 else SENTINEL)
    return vals


EXPECTED_SUB = expected_rendered(SUB_GREEN)
EXPECTED_MAIN = expected_rendered(MAIN_RED)
EXPECTED_UNTOUCHED = [SENTINEL] * (WIDTH * ROWS)


def mismatch_sample(got: list[int], want: list[int], limit: int = 24) -> list[dict[str, int]]:
    out: list[dict[str, int]] = []
    for i, (a, b) in enumerate(zip(got, want)):
        if a == b:
            continue
        y, x = divmod(i, WIDTH)
        out.append({"x": x, "y": y, "actual": a, "expected": b})
        if len(out) >= limit:
            break
    return out


def histogram(vals: list[int]) -> list[dict[str, object]]:
    return [
        {"word": f"0x{word:04X}", "count": count}
        for word, count in Counter(vals).most_common(8)
    ]


def classify_surface(data: bytes, want: list[int], label: str) -> dict[str, object]:
    got = u16_words(data)
    wrong = mismatch_sample(got, want)
    return {
        "label": label,
        "passed": not wrong,
        "histogram": histogram(got),
        "mismatches": wrong,
    }


def find_lifetime_authority(q1: bytes, q2: bytes) -> tuple[str, dict[str, object], dict[str, object]]:
    reports: dict[str, object] = {}
    authority: tuple[str, dict[str, object]] | None = None
    for name, blob in (("q1", q1), ("q2", q2)):
        try:
            report = classify_queue(blob, "identity")
        except ValueError as exc:
            reports[name] = {"passed": False, "reason": str(exc)}
            continue
        reports[name] = {"passed": True, **report}
        if authority is None:
            authority = (name, report)
    if authority is None:
        raise ValueError(f"no coherent lifetime queue: {reports!r}")
    return authority[0], authority[1], reports


def classify_capture(root: Path) -> dict[str, object]:
    q1 = (root / "section-q1.bin").read_bytes()
    q2 = (root / "section-q2.bin").read_bytes()
    authority_name, authority, queue_reports = find_lifetime_authority(q1, q2)

    sub = (root / "sub.bin").read_bytes()
    mains = [(root / f"main{i}.bin").read_bytes() for i in range(1, 4)]

    sub_report = classify_surface(sub, EXPECTED_SUB, "compact_sub")
    main_rendered_reports = [
        classify_surface(blob, EXPECTED_MAIN, f"main{i}_rendered")
        for i, blob in enumerate(mains, start=1)
    ]
    main_untouched_reports = [
        classify_surface(blob, EXPECTED_UNTOUCHED, f"main{i}_untouched")
        for i, blob in enumerate(mains, start=1)
    ]

    rendered_main_indices = [
        i + 1 for i, report in enumerate(main_rendered_reports)
        if report["passed"]
    ]
    untouched_main_indices = [
        i + 1 for i, report in enumerate(main_untouched_reports)
        if report["passed"]
    ]

    exact_main_ownership = (
        len(rendered_main_indices) == 1
        and len(untouched_main_indices) == 2
        and set(rendered_main_indices).isdisjoint(untouched_main_indices)
        and set(rendered_main_indices + untouched_main_indices) == {1, 2, 3}
    )

    state = json.loads((root / "capture-state.json").read_text())
    if state.get("guest_frame_delta") != 1:
        raise ValueError(f"capture is not exactly one fresh guest frame: {state!r}")
    if not state.get("rsp_halted"):
        raise ValueError(f"capture boundary missing RSP HALT: {state!r}")
    if not state.get("rdp_idle"):
        raise ValueError(f"capture boundary has RDP busy: {state!r}")

    passed = bool(
        sub_report["passed"]
        and exact_main_ownership
        and authority_name
    )

    result = {
        "classification": (
            "HCOMP_MAIN_SUB_ARES_PIXELS_VALIDATED"
            if passed
            else "HCOMP_MAIN_SUB_ARES_PIXELS_FAILED"
        ),
        "passed": passed,
        "capture_state": state,
        "lifetime_authority_queue": authority_name,
        "lifetime_authority": authority,
        "queue_reports": queue_reports,
        "sub": {
            "address": f"0x{SUB_COLOR_ADDR:08X}",
            "expected_active": f"0x{SUB_GREEN:04X}",
            "expected_active_words": ACTIVE_WORDS,
            "expected_sentinel_border_words": BORDER_WORDS,
            **sub_report,
        },
        "main": {
            "addresses": [f"0x{x:08X}" for x in FRAMEBUFFER_ADDRS],
            "expected_active": f"0x{MAIN_RED:04X}",
            "rendered_main_indices": rendered_main_indices,
            "untouched_main_indices": untouched_main_indices,
            "exactly_one_main_rendered": exact_main_ownership,
            "rendered_hypotheses": main_rendered_reports,
            "untouched_hypotheses": main_untouched_reports,
        },
        "sentinel": f"0x{SENTINEL:04X}",
        "active_x": [ACTIVE_X0, ACTIVE_X1],
        "rows": [0, ROWS],
        "same_fresh_frame_dual_target": passed,
        "color_math_gating": "NOT_PROVEN",
        "final_pixel_math": "NOT_PROVEN",
    }
    return result


def pack(vals: list[int]) -> bytes:
    return b"".join(v.to_bytes(2, "big") for v in vals)


def write_fixture(root: Path, rendered_main: int = 2) -> None:
    from check_gate_c_hcomp_main_sub_lifetime import (
        EXPECTED_FIRST,
        EXPECTED_SECOND,
        SECTION_SIZE,
        make_record,
    )

    q = bytearray(SECTION_SIZE * 4)
    q[:SECTION_SIZE] = make_record(EXPECTED_FIRST, first=True)
    q[SECTION_SIZE:2 * SECTION_SIZE] = make_record(EXPECTED_SECOND, first=False)
    (root / "section-q1.bin").write_bytes(bytes(q))
    (root / "section-q2.bin").write_bytes(bytes(SECTION_SIZE * 4))

    (root / "sub.bin").write_bytes(pack(EXPECTED_SUB))
    for i in range(1, 4):
        vals = EXPECTED_MAIN if i == rendered_main else EXPECTED_UNTOUCHED
        (root / f"main{i}.bin").write_bytes(pack(vals))
    (root / "capture-state.json").write_text(json.dumps({
        "guest_frame_delta": 1,
        "rsp_halted": True,
        "rdp_idle": True,
    }))


def self_test() -> None:
    for rendered in (1, 2, 3):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, rendered)
            result = classify_capture(root)
            assert result["passed"], result

    # No Sub write must fail.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, 1)
        (root / "sub.bin").write_bytes(pack(EXPECTED_UNTOUCHED))
        assert not classify_capture(root)["passed"]

    # Two Main targets changing in one frame must fail.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, 1)
        (root / "main2.bin").write_bytes(pack(EXPECTED_MAIN))
        assert not classify_capture(root)["passed"]

    # A stale/multi-frame capture cannot be promoted.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, 1)
        state = json.loads((root / "capture-state.json").read_text())
        state["guest_frame_delta"] = 2
        (root / "capture-state.json").write_text(json.dumps(state))
        try:
            classify_capture(root)
        except ValueError:
            pass
        else:
            raise AssertionError("multi-frame fixture unexpectedly accepted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        print("H-COMP Main/Sub ares seeded pixel classifier self-test: PASS")
        return 0
    if args.capture is None:
        ap.error("capture directory is required unless --self-test")

    result = classify_capture(args.capture)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
