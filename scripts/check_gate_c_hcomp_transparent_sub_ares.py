#!/usr/bin/env python3
"""Strict three-state oracle for Z-tagged transparent-Sub fallback and HALF suppression."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from check_gate_c_hcomp_main_sub_lifetime import (
    SECTION_SIZE, STAT_FLAGS, make_record, norm, peek_queue,
)
from check_gate_c_hcomp_main_provenance_ares import (
    BG_TAG, PROVENANCE_PREFIX, PROVENANCE_SUFFIX, UNTOUCHED_MAIN,
    canonical_main, expected_main, expected_provenance, expected_sub, require_fence,
)
from check_gate_c_hcomp_main_sub_pixels_ares import (
    ACTIVE_X0, ACTIVE_X1, SENTINEL, SUB_ROWS, WIDTH, classify_surface, pack,
)

CGWSEL = 55
SUB_COLOR = 38

RED_RGBA5551 = 0xF801
GREEN_RGBA5551 = 0x07C1
RED_RGB555 = 0x001F
GREEN_RGB555 = 0x03E0
BLUE_RGB555 = 0x7C00
BLUE_RGBA5551 = 0x003F
BLUE_SECTION_N64 = 0x003E
TS_BACKDROP_TAG = 0x0400
TS_BG2_TAG = BG_TAG[2]

CGADSUB_HALF_BG1 = 0x41
WINNER_TAG = BG_TAG[1]
WINNER_MASK = 0x01

MODES = {
    "fixed-half": {
        "cgwsel": 0x00, "ts": 0x02, "source_flags": 0x0100,
        "selected": BLUE_RGB555, "result": 0x3C0F, "coverage": "present",
        "ts_tag": TS_BG2_TAG, "presence": 1,
    },
    "sub-present-half": {
        "cgwsel": 0x02, "ts": 0x02, "source_flags": 0x0101,
        "selected": GREEN_RGB555, "result": 0x01EF, "coverage": "present",
        "ts_tag": TS_BG2_TAG, "presence": 1,
    },
    "sub-absent-half": {
        "cgwsel": 0x02, "ts": 0x00, "source_flags": 0x0002,
        "selected": BLUE_RGB555, "result": 0x7C1F, "coverage": "absent",
        "ts_tag": TS_BACKDROP_TAG, "presence": 0,
    },
}


def rgba5551_to_rgb555(value: int) -> int:
    return ((value >> 11) | ((value & 0x07C0) >> 1) | ((value & 0x003E) << 9)) & 0x7FFF


def words(blob: bytes) -> list[int]:
    if len(blob) != WIDTH * SUB_ROWS * 2:
        raise ValueError(f"Sub capture length {len(blob)}")
    return [int.from_bytes(blob[i:i + 2], "big") for i in range(0, len(blob), 2)]


def section_ext(blob: bytes, mode: str, index: int) -> tuple[int, int]:
    data = norm(blob, mode)
    start = index * SECTION_SIZE
    rec = data[start:start + SECTION_SIZE]
    return rec[CGWSEL], int.from_bytes(rec[SUB_COLOR:SUB_COLOR + 2], "big")


def require_queue(root: Path, *, cgwsel: int, ts: int) -> dict[str, object]:
    reports: dict[str, object] = {}
    authority = None
    for name in ("q1", "q2"):
        blob = (root / f"section-{name}.bin").read_bytes()
        for normalization in ("identity", "word_swap32"):
            try:
                first, second = peek_queue(blob, normalization)
                for index, (label, rec, want_ts, split, dirty) in enumerate((
                    ("section0", first, ts, 8, True),
                    ("section1", second, 0, 224, False),
                )):
                    expected = {
                        "cgadsub": CGADSUB_HALF_BG1, "ts": want_ts, "tm": 0x01,
                        "tsw": 0, "tmw": 0, "bg_mode": 0, "split_line": split,
                    }
                    for key, value in expected.items():
                        if rec[key] != value:
                            raise ValueError(f"{label}.{key}={rec[key]:#x} expected {value:#x}")
                    if bool(rec["stat_flags"] & 0x40) != dirty:
                        raise ValueError(f"{label}.stat_flags OAM carrier drift")
                    got_cgwsel, got_fixed = section_ext(blob, normalization, index)
                    if got_cgwsel != cgwsel:
                        raise ValueError(f"{label}.cgwsel={got_cgwsel:#x} expected {cgwsel:#x}")
                    if got_fixed != BLUE_SECTION_N64:
                        raise ValueError(f"{label}.SUB_COLOR={got_fixed:#x} expected {BLUE_SECTION_N64:#x}")
            except ValueError as exc:
                reports[f"{name}:{normalization}"] = {"passed": False, "reason": str(exc)}
                continue
            report = {"passed": True, "queue": name, "normalization": normalization,
                      "sections": [first, second]}
            reports[f"{name}:{normalization}"] = report
            if authority is None:
                authority = report
            break
    if authority is None:
        raise ValueError(f"no coherent queue: {reports!r}")
    return {"authority": authority, "reports": reports}


def mailbox_words(root: Path) -> tuple[int, ...]:
    data = (root / "gating-mailbox.bin").read_bytes()
    if len(data) != 28:
        raise ValueError(f"mailbox length {len(data)} != 28")
    return tuple(int.from_bytes(data[i:i + 2], "big") for i in range(0, 28, 2))


def classify_state(root: Path, mode: str) -> dict[str, object]:
    cfg = MODES[mode]
    sub_blob = (root / "sub.bin").read_bytes()
    if cfg["coverage"] == "present":
        sub_word = GREEN_RGBA5551
        sub_rgb = GREEN_RGB555
    else:
        # Color is deliberately not the presence authority. Opaque backdrop
        # remains blue while compact Z carries the independent absence tag.
        sub_word = BLUE_RGBA5551
        sub_rgb = BLUE_RGB555
    sub_report = classify_surface(
        sub_blob, expected_sub(sub_word), SUB_ROWS, f"{mode}_sub_surface"
    )
    if not sub_report["passed"]:
        raise ValueError(f"{mode} Sub color surface drift: {sub_report!r}")

    mains = [(root / f"main{i}.bin").read_bytes() for i in range(1, 4)]
    want_main = expected_main(RED_RGBA5551)
    rendered = [
        classify_surface(blob, want_main, 16, f"main{i}_bg1_red")
        for i, blob in enumerate(mains, start=1)
    ]
    untouched = [
        classify_surface(blob, UNTOUCHED_MAIN, 16, f"main{i}_untouched")
        for i, blob in enumerate(mains, start=1)
    ]
    rendered_indices = [i + 1 for i, r in enumerate(rendered) if r["passed"]]
    untouched_indices = [i + 1 for i, r in enumerate(untouched) if r["passed"]]
    if not (len(rendered_indices) == 1 and len(untouched_indices) == 2
            and set(rendered_indices + untouched_indices) == {1, 2, 3}):
        raise ValueError(f"{mode} Main ownership drift: rendered={rendered_indices} untouched={untouched_indices}")

    prefix = (root / "provenance-prefix.bin").read_bytes()
    suffix = (root / "provenance-suffix.bin").read_bytes()
    if prefix != PROVENANCE_PREFIX or suffix != PROVENANCE_SUFFIX:
        raise ValueError(f"{mode} provenance guard corruption")
    provenance_report = classify_surface(
        (root / "provenance.bin").read_bytes(),
        expected_provenance(WINNER_TAG), 8, f"{mode}_provenance_bg1",
    )
    if not provenance_report["passed"]:
        raise ValueError(f"{mode} provenance drift: {provenance_report!r}")

    want = (
        RED_RGB555, sub_rgb, cfg["result"], 1,
        WINNER_TAG, WINNER_MASK, CGADSUB_HALF_BG1, 0,
        BLUE_RGB555, cfg["selected"], cfg["cgwsel"], cfg["source_flags"],
        cfg["ts_tag"], cfg["presence"],
    )
    got = mailbox_words(root)
    if got != want:
        raise ValueError(
            f"{mode} mailbox " + ",".join(f"{x:04X}" for x in got)
            + " != " + ",".join(f"{x:04X}" for x in want)
        )

    return {
        "passed": True,
        "mode": mode,
        "main_rendered_index": rendered_indices[0],
        "sub_report": sub_report,
        "main_report": rendered[rendered_indices[0] - 1],
        "provenance_report": provenance_report,
        "provenance_guards_intact": True,
        "queue": require_queue(root, cgwsel=cfg["cgwsel"], ts=cfg["ts"]),
        "mailbox": [f"0x{x:04X}" for x in got],
        "source_code": cfg["source_flags"] & 0x3,
        "half_effective": bool(cfg["source_flags"] & 0x100),
        "ts_presence_tag": f"0x{cfg['ts_tag']:04X}",
        "ts_present": bool(cfg["presence"]),
        "selected_rgb555": f"0x{cfg['selected']:04X}",
        "result_rgb555": f"0x{cfg['result']:04X}",
        "capture_state": require_fence(root),
    }


def classify(roots: dict[str, Path]) -> dict[str, object]:
    states = {mode: classify_state(roots[mode], mode) for mode in MODES}
    base = roots["fixed-half"]
    live = roots["sub-present-half"]
    absent = roots["sub-absent-half"]

    if (base / "sub.bin").read_bytes() != (live / "sub.bin").read_bytes():
        raise ValueError("direct-fixed control changed the live Sub surface")
    for other in (live, absent):
        for name in ("provenance-prefix.bin", "provenance.bin", "provenance-suffix.bin"):
            if (other / name).read_bytes() != (base / name).read_bytes():
                raise ValueError(f"{name} changed across transparency states")
        if canonical_main(other, states[other.name]) != canonical_main(base, states["fixed-half"]):
            raise ValueError("canonical Main changed across transparency states")

    return {
        "classification": "HCOMP_TRANSPARENT_SUB_HALF_SUPPRESSION_VALIDATED",
        "passed": True,
        "states": states,
        "main_provenance_identical_across_states": True,
        "direct_fixed_half_result": "0x3C0F",
        "live_sub_half_result": "0x01EF",
        "transparent_sub_fallback_full_result": "0x7C1F",
        "coverage_carrier": "reused_compact_Z16_TS_winner_tag",
        "new_per_pixel_surface": False,
        "windows_clip_prevent": "NOT_PROVEN",
        "real_n64_rdp_rsp_fence": "NOT_PROVEN",
    }


def fixture_sub(present: bool) -> list[int]:
    return expected_sub(GREEN_RGBA5551 if present else BLUE_RGBA5551)


def write_fixture(root: Path, mode: str, rendered_main: int) -> None:
    cfg = MODES[mode]
    first = {"cgadsub": CGADSUB_HALF_BG1, "ts": cfg["ts"], "tm": 1,
             "tsw": 0, "tmw": 0, "bg_mode": 0, "split_line": 8}
    second = {**first, "ts": 0, "split_line": 224}
    q = bytearray(SECTION_SIZE * 4)
    for index, (record, is_first) in enumerate(((first, True), (second, False))):
        rec = bytearray(make_record(record, first=is_first))
        rec[CGWSEL] = cfg["cgwsel"]
        rec[SUB_COLOR:SUB_COLOR + 2] = BLUE_SECTION_N64.to_bytes(2, "big")
        q[index * SECTION_SIZE:(index + 1) * SECTION_SIZE] = rec
    (root / "section-q1.bin").write_bytes(q)
    (root / "section-q2.bin").write_bytes(q)

    present = cfg["coverage"] == "present"
    sub_vals = fixture_sub(present)
    (root / "sub.bin").write_bytes(pack(sub_vals))
    for i in range(1, 4):
        vals = expected_main(RED_RGBA5551) if i == rendered_main else UNTOUCHED_MAIN
        (root / f"main{i}.bin").write_bytes(pack(vals))
    (root / "provenance-prefix.bin").write_bytes(PROVENANCE_PREFIX)
    (root / "provenance.bin").write_bytes(pack(expected_provenance(WINNER_TAG)))
    (root / "provenance-suffix.bin").write_bytes(PROVENANCE_SUFFIX)

    sub_rgb = GREEN_RGB555 if present else BLUE_RGB555
    got = (
        RED_RGB555, sub_rgb, cfg["result"], 1,
        WINNER_TAG, WINNER_MASK, CGADSUB_HALF_BG1, 0,
        BLUE_RGB555, cfg["selected"], cfg["cgwsel"], cfg["source_flags"],
        cfg["ts_tag"], cfg["presence"],
    )
    (root / "gating-mailbox.bin").write_bytes(pack(list(got)))
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
        for i, mode in enumerate(MODES):
            root = base / mode
            root.mkdir()
            write_fixture(root, mode, 1 + i)
            roots[mode] = root
        assert classify(roots)["passed"]

        bad = bytearray((roots["sub-absent-half"] / "gating-mailbox.bin").read_bytes())
        bad[22:24] = (0x0102).to_bytes(2, "big")
        (roots["sub-absent-half"] / "gating-mailbox.bin").write_bytes(bad)
        try:
            classify(roots)
        except ValueError:
            pass
        else:
            raise AssertionError("HALF-active transparent fallback unexpectedly accepted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for mode in MODES:
        ap.add_argument("--" + mode, dest=mode.replace("-", "_"), type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        print("H-COMP transparent-Sub classifier self-test: PASS")
        return 0
    roots = {mode: getattr(args, mode.replace("-", "_")) for mode in MODES}
    if any(v is None for v in roots.values()):
        ap.error("all three evidence directories are required unless --self-test")
    result = classify(roots)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
