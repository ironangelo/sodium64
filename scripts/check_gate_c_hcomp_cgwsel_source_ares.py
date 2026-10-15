#!/usr/bin/env python3
"""Strict two-state oracle for clean CGWSEL Sub-vs-fixed source selection."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from check_gate_c_hcomp_main_sub_lifetime import (
    BG_MODE,
    CGADSUB,
    SECTION_SIZE,
    SPLIT_LINE,
    STAT_FLAGS,
    TM,
    TMW,
    TS,
    TSW,
    make_record,
    norm,
    peek_queue,
)
from check_gate_c_hcomp_main_provenance_ares import (
    BG_TAG,
    PROVENANCE_PREFIX,
    PROVENANCE_SUFFIX,
    UNTOUCHED_MAIN,
    canonical_main,
    expected_main,
    expected_provenance,
    expected_sub,
    require_fence,
)
from check_gate_c_hcomp_main_sub_pixels_ares import (
    MAIN_ROWS,
    SUB_ROWS,
    classify_surface,
    pack,
)

CGWSEL = 55
SUB_COLOR = 38

RED_RGBA5551 = 0xF801
GREEN_RGBA5551 = 0x07C1
RED_RGB555 = 0x001F
GREEN_RGB555 = 0x03E0
BLUE_RGB555 = 0x7C00
BLUE_SECTION_N64 = 0x003E

CGADSUB_BG1 = 0x01
WINNER_TAG = BG_TAG[1]
WINNER_MASK = 0x01

FIXED_CGWSEL = 0x00
SUB_CGWSEL = 0x02
FIXED_RESULT = 0x3C0F
SUB_RESULT = 0x01EF


def section_ext(blob: bytes, mode: str, index: int) -> tuple[int, int]:
    data = norm(blob, mode)
    start = index * SECTION_SIZE
    rec = data[start:start + SECTION_SIZE]
    if len(rec) != SECTION_SIZE:
        raise ValueError(f"short section record {index}")
    cgwsel = rec[CGWSEL]
    fixed_n64 = int.from_bytes(rec[SUB_COLOR:SUB_COLOR + 2], "big")
    return cgwsel, fixed_n64


def require_queue(root: Path, expected_cgwsel: int) -> dict[str, object]:
    reports: dict[str, object] = {}
    authority: dict[str, object] | None = None

    for name in ("q1", "q2"):
        blob = (root / f"section-{name}.bin").read_bytes()
        for mode in ("identity", "word_swap32"):
            try:
                first, second = peek_queue(blob, mode)
                for index, (label, rec, want_ts, split, dirty_want) in enumerate((
                    ("section0", first, 0x02, 8, True),
                    ("section1", second, 0x00, 224, False),
                )):
                    expected = {
                        "cgadsub": CGADSUB_BG1,
                        "ts": want_ts,
                        "tm": 0x01,
                        "tsw": 0,
                        "tmw": 0,
                        "bg_mode": 0,
                        "split_line": split,
                    }
                    for key, value in expected.items():
                        if rec[key] != value:
                            raise ValueError(
                                f"{label}.{key}={rec[key]:#x} expected {value:#x}"
                            )
                    if bool(rec["stat_flags"] & 0x40) != dirty_want:
                        raise ValueError(
                            f"{label}.stat_flags={rec['stat_flags']:#x} OAM carrier drift"
                        )
                    cgwsel, fixed_n64 = section_ext(blob, mode, index)
                    if cgwsel != expected_cgwsel:
                        raise ValueError(
                            f"{label}.cgwsel={cgwsel:#x} expected {expected_cgwsel:#x}"
                        )
                    if fixed_n64 != BLUE_SECTION_N64:
                        raise ValueError(
                            f"{label}.SUB_COLOR={fixed_n64:#06x} "
                            f"expected blue full-brightness {BLUE_SECTION_N64:#06x}"
                        )
            except ValueError as exc:
                reports[f"{name}:{mode}"] = {"passed": False, "reason": str(exc)}
                continue

            report = {
                "passed": True,
                "queue": name,
                "normalization": mode,
                "sections": [first, second],
                "cgwsel": f"0x{expected_cgwsel:02X}",
                "section_fixed_n64": f"0x{BLUE_SECTION_N64:04X}",
            }
            reports[f"{name}:{mode}"] = report
            if authority is None:
                authority = report
            break

    if authority is None:
        raise ValueError(
            f"no coherent section queue for CGWSEL={expected_cgwsel:#x}: {reports!r}"
        )
    return {"authority": authority, "reports": reports}


def mailbox_words(root: Path) -> tuple[int, ...]:
    data = (root / "gating-mailbox.bin").read_bytes()
    if len(data) != 24:
        raise ValueError(f"mailbox length {len(data)} != 24")
    return tuple(
        int.from_bytes(data[i:i + 2], "big")
        for i in range(0, 24, 2)
    )


def classify_state(root: Path, cgwsel: int) -> dict[str, object]:
    if cgwsel not in (FIXED_CGWSEL, SUB_CGWSEL):
        raise ValueError(cgwsel)

    sub_report = classify_surface(
        (root / "sub.bin").read_bytes(),
        expected_sub(GREEN_RGBA5551),
        SUB_ROWS,
        "sub_bg2_green",
    )
    mains = [(root / f"main{i}.bin").read_bytes() for i in range(1, 4)]
    want_main = expected_main(RED_RGBA5551)
    rendered = [
        classify_surface(blob, want_main, MAIN_ROWS, f"main{i}_bg1_red")
        for i, blob in enumerate(mains, start=1)
    ]
    untouched = [
        classify_surface(blob, UNTOUCHED_MAIN, MAIN_ROWS, f"main{i}_untouched")
        for i, blob in enumerate(mains, start=1)
    ]
    rendered_indices = [i + 1 for i, r in enumerate(rendered) if r["passed"]]
    untouched_indices = [i + 1 for i, r in enumerate(untouched) if r["passed"]]
    exact_main = (
        len(rendered_indices) == 1
        and len(untouched_indices) == 2
        and set(rendered_indices + untouched_indices) == {1, 2, 3}
    )
    if not sub_report["passed"] or not exact_main:
        raise ValueError(
            f"color ownership drift CGWSEL={cgwsel:#x}: "
            f"sub={sub_report!r} rendered={rendered_indices} "
            f"untouched={untouched_indices}"
        )

    prefix = (root / "provenance-prefix.bin").read_bytes()
    suffix = (root / "provenance-suffix.bin").read_bytes()
    if prefix != PROVENANCE_PREFIX or suffix != PROVENANCE_SUFFIX:
        raise ValueError(
            f"provenance guard corruption CGWSEL={cgwsel:#x}: "
            f"prefix_ok={prefix == PROVENANCE_PREFIX} "
            f"suffix_ok={suffix == PROVENANCE_SUFFIX}"
        )

    provenance_report = classify_surface(
        (root / "provenance.bin").read_bytes(),
        expected_provenance(WINNER_TAG),
        8,
        "provenance_bg1",
    )
    if not provenance_report["passed"]:
        raise ValueError(f"BG1 provenance drift: {provenance_report!r}")

    use_sub = 1 if cgwsel & 0x02 else 0
    selected = GREEN_RGB555 if use_sub else BLUE_RGB555
    result = SUB_RESULT if use_sub else FIXED_RESULT
    want_mailbox = (
        RED_RGB555,
        GREEN_RGB555,
        result,
        1,
        WINNER_TAG,
        WINNER_MASK,
        CGADSUB_BG1,
        0,
        BLUE_RGB555,
        selected,
        cgwsel,
        use_sub,
    )
    got_mailbox = mailbox_words(root)
    if got_mailbox != want_mailbox:
        raise ValueError(
            "mailbox "
            + ",".join(f"{x:04X}" for x in got_mailbox)
            + " != "
            + ",".join(f"{x:04X}" for x in want_mailbox)
        )

    queue = require_queue(root, cgwsel)
    fence = require_fence(root)
    return {
        "passed": True,
        "cgwsel": f"0x{cgwsel:02X}",
        "source": "subscreen" if use_sub else "fixed_color",
        "main_rendered_index": rendered_indices[0],
        "mailbox": [f"0x{x:04X}" for x in got_mailbox],
        "sub_report": sub_report,
        "main_report": rendered[rendered_indices[0] - 1],
        "provenance_report": provenance_report,
        "provenance_guards_intact": True,
        "queue": queue,
        "capture_state": fence,
    }


def classify(fixed: Path, sub: Path) -> dict[str, object]:
    off = classify_state(fixed, FIXED_CGWSEL)
    on = classify_state(sub, SUB_CGWSEL)

    for name in (
        "sub.bin",
        "provenance-prefix.bin",
        "provenance.bin",
        "provenance-suffix.bin",
    ):
        if (fixed / name).read_bytes() != (sub / name).read_bytes():
            raise ValueError(f"{name} changed across CGWSEL source states")
    if canonical_main(fixed, off) != canonical_main(sub, on):
        raise ValueError("canonical Main changed across CGWSEL source states")

    return {
        "classification": "HCOMP_CGWSEL_SOURCE_SELECTION_VALIDATED",
        "passed": True,
        "fixed": off,
        "subscreen": on,
        "main_sub_provenance_identical_across_source_states": True,
        "fixed_rgb555": "0x7C00",
        "sub_rgb555": "0x03E0",
        "fixed_result_rgb555": "0x3C0F",
        "sub_result_rgb555": "0x01EF",
        "midframe_fixed_color_history": "NOT_PROVEN",
        "brightness_ordering": "NOT_PROVEN",
        "absent_sub_fallback": "NOT_PROVEN",
        "add_sub_half_modes": "NOT_PROVEN",
        "real_n64_rdp_rsp_fence": "NOT_PROVEN",
    }


def write_fixture(root: Path, *, cgwsel: int, rendered_main: int) -> None:
    first = {
        "cgadsub": CGADSUB_BG1,
        "ts": 0x02,
        "tm": 0x01,
        "tsw": 0,
        "tmw": 0,
        "bg_mode": 0,
        "split_line": 8,
    }
    second = {**first, "ts": 0, "split_line": 224}
    q = bytearray(SECTION_SIZE * 4)
    for index, (record, is_first) in enumerate(((first, True), (second, False))):
        rec = bytearray(make_record(record, first=is_first))
        rec[CGWSEL] = cgwsel
        rec[SUB_COLOR:SUB_COLOR + 2] = BLUE_SECTION_N64.to_bytes(2, "big")
        start = index * SECTION_SIZE
        q[start:start + SECTION_SIZE] = rec
    (root / "section-q1.bin").write_bytes(bytes(q))
    (root / "section-q2.bin").write_bytes(bytes(q))

    (root / "sub.bin").write_bytes(pack(expected_sub(GREEN_RGBA5551)))
    for i in range(1, 4):
        vals = expected_main(RED_RGBA5551) if i == rendered_main else UNTOUCHED_MAIN
        (root / f"main{i}.bin").write_bytes(pack(vals))
    (root / "provenance-prefix.bin").write_bytes(PROVENANCE_PREFIX)
    (root / "provenance.bin").write_bytes(pack(expected_provenance(WINNER_TAG)))
    (root / "provenance-suffix.bin").write_bytes(PROVENANCE_SUFFIX)

    use_sub = 1 if cgwsel & 0x02 else 0
    selected = GREEN_RGB555 if use_sub else BLUE_RGB555
    result = SUB_RESULT if use_sub else FIXED_RESULT
    words = (
        RED_RGB555, GREEN_RGB555, result, 1,
        WINNER_TAG, WINNER_MASK, CGADSUB_BG1, 0,
        BLUE_RGB555, selected, cgwsel, use_sub,
    )
    (root / "gating-mailbox.bin").write_bytes(pack(list(words)))
    (root / "capture-state.json").write_text(json.dumps({
        "guest_frame_delta": 1,
        "renderer_frame_reentries": 1,
        "rsp_halted": True,
        "rdp_commands_complete": True,
        "rdp_buffer_busy": False,
        "rdp_pipe_busy": True,
        "dp_current": "0x000C58",
        "dp_end": "0x000C58",
    }))


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        fixed = base / "fixed"
        sub = base / "sub"
        fixed.mkdir()
        sub.mkdir()
        write_fixture(fixed, cgwsel=FIXED_CGWSEL, rendered_main=1)
        write_fixture(sub, cgwsel=SUB_CGWSEL, rendered_main=3)
        result = classify(fixed, sub)
        assert result["passed"], result

        bad = bytearray((sub / "gating-mailbox.bin").read_bytes())
        bad[18:20] = BLUE_RGB555.to_bytes(2, "big")
        (sub / "gating-mailbox.bin").write_bytes(bad)
        try:
            classify(fixed, sub)
        except ValueError:
            pass
        else:
            raise AssertionError("wrong selected Sub addend unexpectedly accepted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixed", type=Path)
    ap.add_argument("--subscreen", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        print("H-COMP CGWSEL source-selection classifier self-test: PASS")
        return 0
    if args.fixed is None or args.subscreen is None:
        ap.error("--fixed and --subscreen are required unless --self-test")

    result = classify(args.fixed, args.subscreen)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
