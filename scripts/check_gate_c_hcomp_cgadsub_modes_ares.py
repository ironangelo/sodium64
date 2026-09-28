#!/usr/bin/env python3
"""Strict four-state oracle for clean CGADSUB add/subtract/half semantics."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from check_gate_c_hcomp_main_sub_lifetime import (
    SECTION_SIZE, make_record, norm, peek_queue,
)
from check_gate_c_hcomp_main_provenance_ares import (
    BG_TAG, PROVENANCE_PREFIX, PROVENANCE_SUFFIX, UNTOUCHED_MAIN,
    canonical_main, expected_main, expected_provenance, expected_sub, require_fence,
)
from check_gate_c_hcomp_main_sub_pixels_ares import MAIN_ROWS, SUB_ROWS, classify_surface, pack
from check_gate_c_hcomp_cgwsel_source_ares import (
    CGWSEL, SUB_COLOR, RED_RGBA5551, GREEN_RGBA5551, RED_RGB555,
    GREEN_RGB555, BLUE_RGB555, BLUE_SECTION_N64, WINNER_MASK,
)

WINNER_TAG = BG_TAG[1]
CGWSEL_SUB = 0x02
MODES = {
    "add-full": (0x01, 0x03FF),
    "add-half": (0x41, 0x01EF),
    "sub-full": (0x81, 0x001F),
    "sub-half": (0xC1, 0x000F),
}


def section_ext(blob: bytes, normalization: str, index: int) -> tuple[int, int]:
    data = norm(blob, normalization)
    start = index * SECTION_SIZE
    rec = data[start:start + SECTION_SIZE]
    if len(rec) != SECTION_SIZE:
        raise ValueError(f"short section record {index}")
    return rec[CGWSEL], int.from_bytes(rec[SUB_COLOR:SUB_COLOR + 2], "big")


def require_queue(root: Path, cgadsub: int) -> dict[str, object]:
    reports: dict[str, object] = {}
    authority: dict[str, object] | None = None
    for name in ("q1", "q2"):
        blob = (root / f"section-{name}.bin").read_bytes()
        for normalization in ("identity", "word_swap32"):
            try:
                first, second = peek_queue(blob, normalization)
                for index, (label, rec, want_ts, split, dirty) in enumerate((
                    ("section0", first, 0x02, 8, True),
                    ("section1", second, 0x00, 224, False),
                )):
                    expected = {
                        "cgadsub": cgadsub, "ts": want_ts, "tm": 0x01,
                        "tsw": 0, "tmw": 0, "bg_mode": 0, "split_line": split,
                    }
                    for key, value in expected.items():
                        if rec[key] != value:
                            raise ValueError(
                                f"{label}.{key}={rec[key]:#x} expected {value:#x}"
                            )
                    if bool(rec["stat_flags"] & 0x40) != dirty:
                        raise ValueError(f"{label}.stat_flags={rec['stat_flags']:#x} drift")
                    cgwsel, fixed_n64 = section_ext(blob, normalization, index)
                    if cgwsel != CGWSEL_SUB:
                        raise ValueError(f"{label}.cgwsel={cgwsel:#x} expected 0x02")
                    if fixed_n64 != BLUE_SECTION_N64:
                        raise ValueError(
                            f"{label}.SUB_COLOR={fixed_n64:#06x} expected {BLUE_SECTION_N64:#06x}"
                        )
            except ValueError as exc:
                reports[f"{name}:{normalization}"] = {"passed": False, "reason": str(exc)}
                continue
            report = {
                "passed": True, "queue": name, "normalization": normalization,
                "sections": [first, second], "cgwsel": "0x02",
                "cgadsub": f"0x{cgadsub:02X}",
                "section_fixed_n64": f"0x{BLUE_SECTION_N64:04X}",
            }
            reports[f"{name}:{normalization}"] = report
            if authority is None:
                authority = report
            break
    if authority is None:
        raise ValueError(f"no coherent queue for CGADSUB={cgadsub:#x}: {reports!r}")
    return {"authority": authority, "reports": reports}


def mailbox_words(root: Path) -> tuple[int, ...]:
    data = (root / "gating-mailbox.bin").read_bytes()
    if len(data) != 24:
        raise ValueError(f"mailbox length {len(data)} != 24")
    return tuple(int.from_bytes(data[i:i + 2], "big") for i in range(0, 24, 2))


def classify_state(root: Path, mode: str) -> dict[str, object]:
    cgadsub, result = MODES[mode]
    sub_report = classify_surface(
        (root / "sub.bin").read_bytes(), expected_sub(GREEN_RGBA5551),
        SUB_ROWS, "sub_bg2_green",
    )
    mains = [(root / f"main{i}.bin").read_bytes() for i in range(1, 4)]
    rendered = [
        classify_surface(blob, expected_main(RED_RGBA5551), MAIN_ROWS, f"main{i}_bg1_red")
        for i, blob in enumerate(mains, start=1)
    ]
    untouched = [
        classify_surface(blob, UNTOUCHED_MAIN, MAIN_ROWS, f"main{i}_untouched")
        for i, blob in enumerate(mains, start=1)
    ]
    rendered_indices = [i + 1 for i, r in enumerate(rendered) if r["passed"]]
    untouched_indices = [i + 1 for i, r in enumerate(untouched) if r["passed"]]
    if not (
        sub_report["passed"] and len(rendered_indices) == 1 and len(untouched_indices) == 2
        and set(rendered_indices + untouched_indices) == {1, 2, 3}
    ):
        raise ValueError(
            f"color ownership drift {mode}: sub={sub_report!r} "
            f"rendered={rendered_indices} untouched={untouched_indices}"
        )

    prefix = (root / "provenance-prefix.bin").read_bytes()
    suffix = (root / "provenance-suffix.bin").read_bytes()
    if prefix != PROVENANCE_PREFIX or suffix != PROVENANCE_SUFFIX:
        raise ValueError(f"provenance guard corruption {mode}")
    provenance_report = classify_surface(
        (root / "provenance.bin").read_bytes(), expected_provenance(WINNER_TAG),
        8, "provenance_bg1",
    )
    if not provenance_report["passed"]:
        raise ValueError(f"provenance drift {mode}: {provenance_report!r}")

    want = (
        RED_RGB555, GREEN_RGB555, result, 1,
        WINNER_TAG, WINNER_MASK, cgadsub, 0,
        BLUE_RGB555, GREEN_RGB555, CGWSEL_SUB, 1,
    )
    got = mailbox_words(root)
    if got != want:
        raise ValueError(
            f"{mode} mailbox " + ",".join(f"{x:04X}" for x in got)
            + " != " + ",".join(f"{x:04X}" for x in want)
        )

    return {
        "passed": True, "mode": mode, "cgadsub": f"0x{cgadsub:02X}",
        "result_rgb555": f"0x{result:04X}",
        "main_rendered_index": rendered_indices[0],
        "mailbox": [f"0x{x:04X}" for x in got],
        "sub_report": sub_report,
        "main_report": rendered[rendered_indices[0] - 1],
        "provenance_report": provenance_report,
        "provenance_guards_intact": True,
        "queue": require_queue(root, cgadsub),
        "capture_state": require_fence(root),
    }


def classify(roots: dict[str, Path]) -> dict[str, object]:
    states = {mode: classify_state(roots[mode], mode) for mode in MODES}
    baseline = next(iter(MODES))
    base_root = roots[baseline]
    base_main = canonical_main(base_root, states[baseline])
    for mode in list(MODES)[1:]:
        root = roots[mode]
        for name in ("sub.bin", "provenance-prefix.bin", "provenance.bin", "provenance-suffix.bin"):
            if (root / name).read_bytes() != (base_root / name).read_bytes():
                raise ValueError(f"{name} changed between {baseline} and {mode}")
        if canonical_main(root, states[mode]) != base_main:
            raise ValueError(f"canonical Main changed between {baseline} and {mode}")

    return {
        "classification": "HCOMP_CGADSUB_MODES_VALIDATED",
        "passed": True,
        "states": states,
        "main_sub_provenance_identical_across_modes": True,
        "operands_rgb555": {"main": "0x001F", "sub": "0x03E0"},
        "expected_results": {k: f"0x{v[1]:04X}" for k, v in MODES.items()},
        "transparent_sub_half_suppression": "NOT_PROVEN",
        "fixed_color_half_special_case": "NOT_PROVEN",
        "windows_clip_prevent": "NOT_PROVEN",
        "real_n64_rdp_rsp_fence": "NOT_PROVEN",
    }


def write_fixture(root: Path, mode: str, rendered_main: int) -> None:
    cgadsub, result = MODES[mode]
    first = {
        "cgadsub": cgadsub, "ts": 0x02, "tm": 0x01, "tsw": 0, "tmw": 0,
        "bg_mode": 0, "split_line": 8,
    }
    second = {**first, "ts": 0, "split_line": 224}
    q = bytearray(SECTION_SIZE * 4)
    for index, (record, is_first) in enumerate(((first, True), (second, False))):
        rec = bytearray(make_record(record, first=is_first))
        rec[CGWSEL] = CGWSEL_SUB
        rec[SUB_COLOR:SUB_COLOR + 2] = BLUE_SECTION_N64.to_bytes(2, "big")
        start = index * SECTION_SIZE
        q[start:start + SECTION_SIZE] = rec
    (root / "section-q1.bin").write_bytes(q)
    (root / "section-q2.bin").write_bytes(q)
    (root / "sub.bin").write_bytes(pack(expected_sub(GREEN_RGBA5551)))
    for i in range(1, 4):
        vals = expected_main(RED_RGBA5551) if i == rendered_main else UNTOUCHED_MAIN
        (root / f"main{i}.bin").write_bytes(pack(vals))
    (root / "provenance-prefix.bin").write_bytes(PROVENANCE_PREFIX)
    (root / "provenance.bin").write_bytes(pack(expected_provenance(WINNER_TAG)))
    (root / "provenance-suffix.bin").write_bytes(PROVENANCE_SUFFIX)
    words = (
        RED_RGB555, GREEN_RGB555, result, 1, WINNER_TAG, WINNER_MASK, cgadsub, 0,
        BLUE_RGB555, GREEN_RGB555, CGWSEL_SUB, 1,
    )
    (root / "gating-mailbox.bin").write_bytes(pack(list(words)))
    (root / "capture-state.json").write_text(json.dumps({
        "guest_frame_delta": 1, "renderer_frame_reentries": 1,
        "rsp_halted": True, "rdp_commands_complete": True,
        "rdp_buffer_busy": False, "rdp_pipe_busy": True,
        "dp_current": "0x000C58", "dp_end": "0x000C58",
    }))


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        roots = {}
        for index, mode in enumerate(MODES):
            root = base / mode
            root.mkdir()
            write_fixture(root, mode, 1 + (index % 3))
            roots[mode] = root
        assert classify(roots)["passed"]
        bad = bytearray((roots["sub-half"] / "gating-mailbox.bin").read_bytes())
        bad[4:6] = (0x001F).to_bytes(2, "big")
        (roots["sub-half"] / "gating-mailbox.bin").write_bytes(bad)
        try:
            classify(roots)
        except ValueError:
            pass
        else:
            raise AssertionError("wrong sub-half result unexpectedly accepted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for mode in MODES:
        ap.add_argument("--" + mode, dest=mode.replace("-", "_"), type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        print("H-COMP CGADSUB modes classifier self-test: PASS")
        return 0
    roots = {
        mode: getattr(args, mode.replace("-", "_"))
        for mode in MODES
    }
    if any(v is None for v in roots.values()):
        ap.error("all four mode evidence directories are required unless --self-test")
    result = classify(roots)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
