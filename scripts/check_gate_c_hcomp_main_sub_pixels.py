#!/usr/bin/env python3
"""Classify first-hand clean Main/Sub dual rendered color ownership."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import collections
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_gate_c_hcomp_main_sub_lifetime import classify_queue, norm  # noqa: E402

WIDTH = 280
ROWS = 8
STRIP_BYTES = WIDTH * ROWS * 2
ACTIVE_X0 = 12
ACTIVE_X1 = 268

SUB_COLOR = 0xA00E4000
FRAMEBUFFERS = (
    0xA00F2300,
    0xA0113000,
    0xA0133D00,
)

# Guest writes SNES RGB555 red=001F / green=03E0. The runtime renderer consumes
# the converted N64 RGBA5551 palette representation.
MAIN_RED = 0xF801
SUB_GREEN = 0x07C1
CLEARED = 0x0000


def words(data: bytes, mode: str) -> list[int]:
    data = norm(data, mode)
    if len(data) != STRIP_BYTES:
        raise ValueError(f"strip length {len(data)} != 0x{STRIP_BYTES:X}")
    return [int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2)]


def expected_strip(active_word: int) -> list[int]:
    out: list[int] = []
    for _y in range(ROWS):
        for x in range(WIDTH):
            out.append(active_word if ACTIVE_X0 <= x < ACTIVE_X1 else CLEARED)
    return out


EXPECTED_SUB = expected_strip(SUB_GREEN)
EXPECTED_MAIN = expected_strip(MAIN_RED)
ACTIVE_WORDS = (ACTIVE_X1 - ACTIVE_X0) * ROWS
BORDER_WORDS = (WIDTH - (ACTIVE_X1 - ACTIVE_X0)) * ROWS



def strip_diag(data: bytes, mode: str) -> dict[str, object]:
    vals = words(data, mode)
    hist = collections.Counter(vals)
    nonzero = [(i, v) for i, v in enumerate(vals) if v]
    bbox = None
    if nonzero:
        xs = [i % WIDTH for i, _ in nonzero]
        ys = [i // WIDTH for i, _ in nonzero]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    active = [
        vals[y * WIDTH + x]
        for y in range(ROWS)
        for x in range(ACTIVE_X0, ACTIVE_X1)
    ]
    ah = collections.Counter(active)
    return {
        "top_words": [[f"0x{k:04X}", v] for k, v in hist.most_common(6)],
        "active_top_words": [[f"0x{k:04X}", v] for k, v in ah.most_common(6)],
        "nonzero_words": len(nonzero),
        "nonzero_bbox": bbox,
    }


def rdp_frame_diag(data: bytes, mode: str) -> dict[str, object]:
    d = norm(data, mode)
    if len(d) != 24:
        raise ValueError(f"RDP frame dump length {len(d)} != 24")
    words32 = [int.from_bytes(d[i:i + 4], "big") for i in range(0, len(d), 4)]
    return {
        "words32": [f"0x{x:08X}" for x in words32],
        "color_image_word": f"0x{words32[1]:08X}",
    }


def check_strip(data: bytes, mode: str, expected: list[int], label: str) -> dict[str, object]:
    got = words(data, mode)
    wrong: list[dict[str, int]] = []
    for i, (actual, want) in enumerate(zip(got, expected)):
        if actual != want and len(wrong) < 32:
            y, x = divmod(i, WIDTH)
            wrong.append({"x": x, "y": y, "actual": actual, "expected": want})
    if wrong:
        raise ValueError(f"{label} pixel mismatch: {wrong[:4]!r}")

    active_word = expected[ACTIVE_X0]
    active_count = sum(1 for y in range(ROWS) for x in range(ACTIVE_X0, ACTIVE_X1)
                       if got[y * WIDTH + x] == active_word)
    border_count = sum(1 for y in range(ROWS) for x in range(WIDTH)
                       if not (ACTIVE_X0 <= x < ACTIVE_X1)
                       and got[y * WIDTH + x] == CLEARED)
    if active_count != ACTIVE_WORDS or border_count != BORDER_WORDS:
        raise ValueError(
            f"{label} counts active={active_count}/{ACTIVE_WORDS} "
            f"border={border_count}/{BORDER_WORDS}"
        )
    return {
        "active_word": f"0x{active_word:04X}",
        "active_words": active_count,
        "cleared_border_words": border_count,
        "total_words": len(got),
    }


def classify_snapshot(root: Path, prefix: str, mode: str) -> dict[str, object]:
    qdata = {
        q: (root / f"{prefix}-{q}.bin").read_bytes()
        for q in ("q1", "q2")
    }
    sub_data = (root / f"{prefix}-sub.bin").read_bytes()
    main_data = [
        (root / f"{prefix}-main{i}.bin").read_bytes()
        for i in range(1, 4)
    ]
    rdp_data = (root / f"{prefix}-rdp-frame.bin").read_bytes()

    diagnostic = {
        "sub": strip_diag(sub_data, mode),
        "main": [strip_diag(d, mode) for d in main_data],
        "rdp_frame": rdp_frame_diag(rdp_data, mode),
    }

    queue_reports: dict[str, object] = {}
    authority: str | None = None
    for q in ("q1", "q2"):
        try:
            report = classify_queue(qdata[q], mode)
        except ValueError as exc:
            queue_reports[q] = {"passed": False, "reason": str(exc)}
            continue
        queue_reports[q] = {"passed": True, **report}
        authority = q
        break
    if authority is None:
        raise ValueError(
            "no authoritative lifetime queue; diagnostics="
            + json.dumps({"queues": queue_reports, **diagnostic}, sort_keys=True)
        )

    try:
        sub = check_strip(sub_data, mode, EXPECTED_SUB, "compact Sub")
        main_reports = [
            check_strip(data, mode, EXPECTED_MAIN, f"Main framebuffer{i}")
            for i, data in enumerate(main_data, start=1)
        ]

        sub_words = words(sub_data, mode)
        if any(
            sub_words[y * WIDTH + x] == MAIN_RED
            for y in range(ROWS)
            for x in range(ACTIVE_X0, ACTIVE_X1)
        ):
            raise ValueError("Main red leaked into compact Sub active band")

        for i, data in enumerate(main_data, start=1):
            main_words = words(data, mode)
            if any(
                main_words[y * WIDTH + x] == SUB_GREEN
                for y in range(ROWS)
                for x in range(ACTIVE_X0, ACTIVE_X1)
            ):
                raise ValueError(f"Sub green leaked into Main framebuffer{i} active band")
    except ValueError as exc:
        raise ValueError(
            f"{exc}; diagnostics="
            + json.dumps({"queues": queue_reports, **diagnostic}, sort_keys=True)
        ) from exc

    return {
        "classification": "HCOMP_MAIN_SUB_PIXELS_DYNAMIC_VALIDATED",
        "passed": True,
        "prefix": prefix,
        "normalization": mode,
        "lifetime_authority_queue": authority,
        "queues": queue_reports,
        "compact_sub": {
            "address": f"0x{SUB_COLOR:08X}",
            **sub,
        },
        "main_framebuffers": [
            {"address": f"0x{addr:08X}", **rep}
            for addr, rep in zip(FRAMEBUFFERS, main_reports)
        ],
        "rdp_frame": diagnostic["rdp_frame"],
        "active_x": [ACTIVE_X0, ACTIVE_X1],
        "physical_rows": [0, ROWS],
        "sub_expected_rgba5551": f"0x{SUB_GREEN:04X}",
        "main_expected_rgba5551": f"0x{MAIN_RED:04X}",
        "independent_rendered_operands": True,
        "color_math_gating": "NOT_PROVEN",
        "final_pixel_math": "NOT_PROVEN",
    }


def prefixes(root: Path) -> list[str]:
    suffix = "-sub.bin"
    return sorted(p.name[:-len(suffix)] for p in root.glob(f"snap*{suffix}"))


def classify(root: Path) -> dict[str, object]:
    attempts: list[dict[str, object]] = []
    ps = prefixes(root)
    for prefix in ps:
        for mode in ("identity", "word_swap32"):
            try:
                result = classify_snapshot(root, prefix, mode)
            except (OSError, ValueError) as exc:
                attempts.append({
                    "prefix": prefix,
                    "normalization": mode,
                    "passed": False,
                    "reason": str(exc),
                })
                continue
            return {
                **result,
                "snapshots_seen": len(ps),
                "attempts_before_pass": len(attempts),
            }
    return {
        "classification": "HCOMP_MAIN_SUB_PIXELS_DYNAMIC_FAILED",
        "passed": False,
        "snapshots_seen": len(ps),
        "attempts": attempts,
    }


def pack_words(vals: list[int]) -> bytes:
    return b"".join(v.to_bytes(2, "big") for v in vals)


def write_fixture(root: Path, mode: str) -> None:
    # Reuse the lifetime classifier's exact two-record layout.
    from check_gate_c_hcomp_main_sub_lifetime import (
        EXPECTED_FIRST,
        EXPECTED_SECOND,
        SECTION_SIZE,
        make_record,
        swap32,
    )

    q = bytearray(SECTION_SIZE * 4)
    q[:SECTION_SIZE] = make_record(EXPECTED_FIRST, first=True)
    q[SECTION_SIZE:2 * SECTION_SIZE] = make_record(EXPECTED_SECOND, first=False)

    blobs = {
        "q1": bytes(q),
        "q2": bytes(q),
        "sub": pack_words(EXPECTED_SUB),
        "main1": pack_words(EXPECTED_MAIN),
        "main2": pack_words(EXPECTED_MAIN),
        "main3": pack_words(EXPECTED_MAIN),
        "rdp-frame": bytes.fromhex(
            "3F100117000F0000"
            "3D10000000000000"
            "3300000000400000"
        ),
    }
    if mode == "word_swap32":
        blobs = {k: swap32(v) for k, v in blobs.items()}
    for name, data in blobs.items():
        (root / f"snap0-{name}.bin").write_bytes(data)


def self_test() -> None:
    for mode in ("identity", "word_swap32"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, mode)
            result = classify(root)
            assert result["passed"], result

    # Sub/Main swap must fail.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        (root / "snap0-sub.bin").write_bytes(pack_words(EXPECTED_MAIN))
        assert not classify(root)["passed"]

    # One bad Main framebuffer must fail this stable-static discriminator.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_fixture(root, "identity")
        bad = EXPECTED_MAIN.copy()
        bad[ACTIVE_X0] = SUB_GREEN
        (root / "snap0-main2.bin").write_bytes(pack_words(bad))
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
        print("H-COMP Main/Sub pixel classifier self-test: PASS")
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
