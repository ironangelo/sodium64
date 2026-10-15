#!/usr/bin/env python3
"""Strict four-state oracle for clean BG1/BG2 Main winner provenance + CGADSUB gating."""

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
    peek_queue,
)
from check_gate_c_hcomp_main_sub_pixels_ares import (
    ACTIVE_X0,
    ACTIVE_X1,
    MAIN_ACTIVE_Y0,
    MAIN_ACTIVE_Y1,
    MAIN_ROWS,
    SENTINEL,
    SUB_ROWS,
    WIDTH,
    classify_surface,
    pack,
)

RED_RGBA5551 = 0xF801
GREEN_RGBA5551 = 0x07C1
RED_RGB555 = 0x001F
GREEN_RGB555 = 0x03E0
HALF_ADD_RED_GREEN = 0x01EF

BG_TAG = {1: 0x0C00, 2: 0x1400}
BG_MASK = {1: 0x01, 2: 0x02}
BG_RGBA = {1: RED_RGBA5551, 2: GREEN_RGBA5551}
BG_RGB = {1: RED_RGB555, 2: GREEN_RGB555}
PROVENANCE_PREFIX = bytes((0xC3,)) * 0x40
PROVENANCE_SUFFIX = bytes((0x3C,)) * 0x40


def expected_sub(word: int) -> list[int]:
    return [
        word if ACTIVE_X0 <= x < ACTIVE_X1 else SENTINEL
        for _y in range(SUB_ROWS)
        for x in range(WIDTH)
    ]


def expected_main(word: int) -> list[int]:
    vals: list[int] = []
    for y in range(MAIN_ROWS):
        for x in range(WIDTH):
            active = (
                MAIN_ACTIVE_Y0 <= y < MAIN_ACTIVE_Y1
                and ACTIVE_X0 <= x < ACTIVE_X1
            )
            vals.append(word if active else SENTINEL)
    return vals


def expected_provenance(tag: int) -> list[int]:
    return [
        tag if ACTIVE_X0 <= x < ACTIVE_X1 else SENTINEL
        for _y in range(8)
        for x in range(WIDTH)
    ]


UNTOUCHED_MAIN = [SENTINEL] * (WIDTH * MAIN_ROWS)


def require_fence(root: Path) -> dict[str, object]:
    state = json.loads((root / "capture-state.json").read_text())
    if state.get("renderer_frame_reentries") != 1:
        raise ValueError(f"not exactly one renderer frame: {state!r}")
    if int(state.get("guest_frame_delta", 0)) < 1:
        raise ValueError(f"no fresh guest time: {state!r}")
    if not state.get("rsp_halted"):
        raise ValueError(f"RSP not halted: {state!r}")
    if not state.get("rdp_commands_complete"):
        raise ValueError(f"RDP commands incomplete: {state!r}")
    if state.get("rdp_buffer_busy"):
        raise ValueError(f"RDP buffer busy: {state!r}")
    if state.get("dp_current") != state.get("dp_end"):
        raise ValueError(f"DPC_CURRENT != DPC_END: {state!r}")
    return state


def require_queue(root: Path, *, winner: int, cgadsub: int) -> dict[str, object]:
    main_mask = BG_MASK[winner]
    sub_mask = BG_MASK[2 if winner == 1 else 1]
    reports: dict[str, object] = {}
    authority: dict[str, object] | None = None

    for name in ("q1", "q2"):
        blob = (root / f"section-{name}.bin").read_bytes()
        for mode in ("identity", "word_swap32"):
            try:
                first, second = peek_queue(blob, mode)
                for label, rec, want_ts, split, first_rec in (
                    ("section0", first, sub_mask, 8, True),
                    ("section1", second, 0, 224, False),
                ):
                    want = {
                        CGADSUB: cgadsub,
                        TS: want_ts,
                        TM: main_mask,
                        TSW: 0,
                        TMW: 0,
                        BG_MODE: 0,
                        SPLIT_LINE: split,
                    }
                    keys = {
                        CGADSUB: "cgadsub",
                        TS: "ts",
                        TM: "tm",
                        TSW: "tsw",
                        TMW: "tmw",
                        BG_MODE: "bg_mode",
                        SPLIT_LINE: "split_line",
                    }
                    for off, value in want.items():
                        key = keys[off]
                        if rec[key] != value:
                            raise ValueError(
                                f"{label}.{key}={rec[key]} expected {value}"
                            )
                    dirty = bool(rec["stat_flags"] & 0x40)
                    if dirty != first_rec:
                        raise ValueError(
                            f"{label}.stat_flags={rec['stat_flags']:#x} OAM carrier drift"
                        )
            except ValueError as exc:
                reports[f"{name}:{mode}"] = {"passed": False, "reason": str(exc)}
                continue

            report = {
                "passed": True,
                "queue": name,
                "normalization": mode,
                "sections": [first, second],
            }
            reports[f"{name}:{mode}"] = report
            if authority is None:
                authority = report
            break

    if authority is None:
        raise ValueError(
            f"no coherent queue winner=BG{winner} cgadsub={cgadsub}: {reports!r}"
        )
    return {"authority": authority, "reports": reports}


def mailbox_words(root: Path) -> tuple[int, ...]:
    data = (root / "gating-mailbox.bin").read_bytes()
    if len(data) != 16:
        raise ValueError(f"mailbox length {len(data)} != 16")
    return tuple(
        int.from_bytes(data[i:i + 2], "big")
        for i in range(0, 16, 2)
    )


def classify_state(root: Path, *, winner: int, cgadsub: int) -> dict[str, object]:
    if winner not in (1, 2) or cgadsub not in (1, 2):
        raise ValueError("winner/cgadsub must be 1 or 2")
    sub_bg = 2 if winner == 1 else 1

    sub_report = classify_surface(
        (root / "sub.bin").read_bytes(),
        expected_sub(BG_RGBA[sub_bg]),
        SUB_ROWS,
        f"sub_bg{sub_bg}",
    )
    mains = [(root / f"main{i}.bin").read_bytes() for i in range(1, 4)]
    want_main = expected_main(BG_RGBA[winner])
    rendered = [
        classify_surface(blob, want_main, MAIN_ROWS, f"main{i}_bg{winner}")
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
            f"color ownership drift BG{winner}: sub={sub_report!r} "
            f"rendered={rendered_indices} untouched={untouched_indices}"
        )

    prefix = (root / "provenance-prefix.bin").read_bytes()
    suffix = (root / "provenance-suffix.bin").read_bytes()
    if prefix != PROVENANCE_PREFIX or suffix != PROVENANCE_SUFFIX:
        raise ValueError(
            f"provenance guard corruption BG{winner}: "
            f"prefix_ok={prefix == PROVENANCE_PREFIX} "
            f"suffix_ok={suffix == PROVENANCE_SUFFIX}"
        )

    provenance_report = classify_surface(
        (root / "provenance.bin").read_bytes(),
        expected_provenance(BG_TAG[winner]),
        8,
        f"provenance_bg{winner}",
    )
    if not provenance_report["passed"]:
        raise ValueError(f"winner provenance drift BG{winner}: {provenance_report!r}")

    gate = 1 if cgadsub == BG_MASK[winner] else 0
    result = HALF_ADD_RED_GREEN if gate else BG_RGB[winner]
    want_mailbox = (
        BG_RGB[winner],
        BG_RGB[sub_bg],
        result,
        gate,
        BG_TAG[winner],
        BG_MASK[winner],
        cgadsub,
        0,
    )
    got_mailbox = mailbox_words(root)
    if got_mailbox != want_mailbox:
        raise ValueError(
            "mailbox "
            + ",".join(f"{x:04X}" for x in got_mailbox)
            + " != "
            + ",".join(f"{x:04X}" for x in want_mailbox)
        )

    queue = require_queue(root, winner=winner, cgadsub=cgadsub)
    state = require_fence(root)
    return {
        "passed": True,
        "winner": f"BG{winner}",
        "cgadsub": f"0x{cgadsub:02X}",
        "gate_applied": bool(gate),
        "main_rendered_index": rendered_indices[0],
        "mailbox": [f"0x{x:04X}" for x in got_mailbox],
        "sub_report": sub_report,
        "main_report": rendered[rendered_indices[0] - 1],
        "provenance_report": provenance_report,
        "provenance_guards_intact": True,
        "queue": queue,
        "capture_state": state,
    }


def canonical_main(root: Path, report: dict[str, object]) -> bytes:
    return (root / f"main{report['main_rendered_index']}.bin").read_bytes()


def classify(cases: dict[tuple[int, int], Path]) -> dict[str, object]:
    reports = {
        key: classify_state(path, winner=key[0], cgadsub=key[1])
        for key, path in cases.items()
    }

    # Changing only CGADSUB for a fixed winner must not change operands or
    # provenance, regardless of independent-process triple-buffer phase.
    for winner in (1, 2):
        a = cases[(winner, 1)]
        b = cases[(winner, 2)]
        ra = reports[(winner, 1)]
        rb = reports[(winner, 2)]
        for name in (
            "sub.bin",
            "provenance-prefix.bin",
            "provenance.bin",
            "provenance-suffix.bin",
        ):
            if (a / name).read_bytes() != (b / name).read_bytes():
                raise ValueError(f"BG{winner} {name} changed across CGADSUB states")
        if canonical_main(a, ra) != canonical_main(b, rb):
            raise ValueError(f"BG{winner} canonical Main changed across CGADSUB states")

    # Positive and negative gating must both be observed for both winner bits.
    for winner in (1, 2):
        positive = reports[(winner, BG_MASK[winner])]["gate_applied"]
        negative = reports[(winner, BG_MASK[2 if winner == 1 else 1])]["gate_applied"]
        if positive is not True or negative is not False:
            raise ValueError(f"BG{winner} gating matrix incomplete")

    return {
        "classification": "HCOMP_MAIN_BG12_PROVENANCE_GATING_VALIDATED",
        "passed": True,
        "cases": {
            f"bg{w}-cg{c}": reports[(w, c)]
            for w in (1, 2) for c in (1, 2)
        },
        "winner_tags": {"BG1": "0x0C00", "BG2": "0x1400"},
        "winner_masks": {"BG1": "0x01", "BG2": "0x02"},
        "color_operands_stable_within_winner_pairs": True,
        "provenance_stable_within_winner_pairs": True,
        "physical_main_slot_may_rotate_across_processes": True,
        "overlapping_priority_arbitration": "NOT_PROVEN",
        "bg3_bg4_obj_backdrop_provenance": "NOT_PROVEN",
        "real_n64_rdp_rsp_fence": "NOT_PROVEN",
    }


def write_fixture(root: Path, *, winner: int, cgadsub: int, rendered_main: int) -> None:
    sub_bg = 2 if winner == 1 else 1
    first = {
        "cgadsub": cgadsub,
        "ts": BG_MASK[sub_bg],
        "tm": BG_MASK[winner],
        "tsw": 0,
        "tmw": 0,
        "bg_mode": 0,
        "split_line": 8,
    }
    second = {**first, "ts": 0, "split_line": 224}
    q = bytearray(SECTION_SIZE * 4)
    q[:SECTION_SIZE] = make_record(first, first=True)
    q[SECTION_SIZE:2 * SECTION_SIZE] = make_record(second, first=False)
    (root / "section-q1.bin").write_bytes(bytes(q))
    (root / "section-q2.bin").write_bytes(bytes(q))

    (root / "sub.bin").write_bytes(pack(expected_sub(BG_RGBA[sub_bg])))
    for i in range(1, 4):
        vals = expected_main(BG_RGBA[winner]) if i == rendered_main else UNTOUCHED_MAIN
        (root / f"main{i}.bin").write_bytes(pack(vals))
    (root / "provenance-prefix.bin").write_bytes(PROVENANCE_PREFIX)
    (root / "provenance.bin").write_bytes(pack(expected_provenance(BG_TAG[winner])))
    (root / "provenance-suffix.bin").write_bytes(PROVENANCE_SUFFIX)

    gate = 1 if cgadsub == BG_MASK[winner] else 0
    result = HALF_ADD_RED_GREEN if gate else BG_RGB[winner]
    words = (
        BG_RGB[winner], BG_RGB[sub_bg], result, gate,
        BG_TAG[winner], BG_MASK[winner], cgadsub, 0,
    )
    (root / "gating-mailbox.bin").write_bytes(pack(list(words)))
    (root / "capture-state.json").write_text(json.dumps({
        "guest_frame_delta": 1,
        "renderer_frame_reentries": 1,
        "rsp_halted": True,
        "rdp_commands_complete": True,
        "rdp_buffer_busy": False,
        "rdp_pipe_busy": True,
        "dp_current": "0x000C70",
        "dp_end": "0x000C70",
    }))


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        cases: dict[tuple[int, int], Path] = {}
        slots = {(1, 1): 1, (1, 2): 3, (2, 1): 2, (2, 2): 1}
        for key, slot in slots.items():
            root = base / f"bg{key[0]}-cg{key[1]}"
            root.mkdir()
            write_fixture(root, winner=key[0], cgadsub=key[1], rendered_main=slot)
            cases[key] = root
        result = classify(cases)
        assert result["passed"], result

        bad = bytearray((cases[(2, 2)] / "provenance.bin").read_bytes())
        bad[24:26] = BG_TAG[1].to_bytes(2, "big")
        (cases[(2, 2)] / "provenance.bin").write_bytes(bad)
        try:
            classify(cases)
        except ValueError:
            pass
        else:
            raise AssertionError("wrong winner provenance unexpectedly accepted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bg1-cg1", type=Path)
    ap.add_argument("--bg1-cg2", type=Path)
    ap.add_argument("--bg2-cg1", type=Path)
    ap.add_argument("--bg2-cg2", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        print("H-COMP Main BG1/BG2 provenance classifier self-test: PASS")
        return 0

    paths = {
        (1, 1): args.bg1_cg1,
        (1, 2): args.bg1_cg2,
        (2, 1): args.bg2_cg1,
        (2, 2): args.bg2_cg2,
    }
    if any(v is None for v in paths.values()):
        ap.error("all four --bgN-cgN capture directories are required")

    result = classify({k: v for k, v in paths.items() if v is not None})
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
