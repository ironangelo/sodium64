#!/usr/bin/env python3
"""Strict two-state CGADSUB BG1 gating oracle over live rendered Main/Sub samples."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from check_gate_c_hcomp_main_sub_lifetime import (
    CGADSUB,
    SECTION_SIZE,
    peek_queue,
)
from check_gate_c_hcomp_main_sub_pixels_ares import (
    EXPECTED_MAIN,
    EXPECTED_MAIN_UNTOUCHED,
    EXPECTED_SUB,
    MAIN_ROWS,
    SUB_ROWS,
    classify_surface,
    write_fixture as write_pixel_fixture,
)

EXPECTED_MAIN_RGB555 = 0x001F
EXPECTED_SUB_RGB555 = 0x03E0
EXPECTED_ENABLED_RESULT = 0x01EF
EXPECTED_DISABLED_RESULT = EXPECTED_MAIN_RGB555


def require_queue(root: Path, expected_cgadsub: int) -> dict[str, object]:
    reports: dict[str, object] = {}
    authority: dict[str, object] | None = None

    for name in ("q1", "q2"):
        blob = (root / f"section-{name}.bin").read_bytes()
        passed = False
        for mode in ("identity", "word_swap32"):
            try:
                first, second = peek_queue(blob, mode)
                for label, rec, cg, ts, tm, split in (
                    ("section0", first, expected_cgadsub, 2, 1, 8),
                    ("section1", second, expected_cgadsub, 0, 1, 224),
                ):
                    if rec["cgadsub"] != cg:
                        raise ValueError(
                            f"{label}.cgadsub={rec['cgadsub']} expected {cg}"
                        )
                    if rec["ts"] != ts or rec["tm"] != tm or rec["split_line"] != split:
                        raise ValueError(
                            f"{label} routing/split drift: {rec!r}"
                        )
                    if rec["tsw"] != 0 or rec["tmw"] != 0 or rec["bg_mode"] != 0:
                        raise ValueError(f"{label} unrelated state drift: {rec!r}")
                if not (first["stat_flags"] & 0x40):
                    raise ValueError("section0 missing OAM-dirty frame-start bit")
                if second["stat_flags"] & 0x40:
                    raise ValueError("section1 unexpectedly retains OAM-dirty bit")
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
            passed = True
            break

        if not passed:
            continue

    if authority is None:
        raise ValueError(f"no coherent queue for CGADSUB={expected_cgadsub}: {reports!r}")
    return {"authority": authority, "reports": reports}


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


def mailbox_words(root: Path) -> tuple[int, int, int, int]:
    data = (root / "gating-mailbox.bin").read_bytes()
    if len(data) != 8:
        raise ValueError(f"gating mailbox length {len(data)} != 8")
    return tuple(
        int.from_bytes(data[i:i + 2], "big")
        for i in range(0, 8, 2)
    )  # type: ignore[return-value]


def classify_state(root: Path, expected_cgadsub: int) -> dict[str, object]:
    sub = (root / "sub.bin").read_bytes()
    mains = [(root / f"main{i}.bin").read_bytes() for i in range(1, 4)]

    sub_report = classify_surface(sub, EXPECTED_SUB, SUB_ROWS, "compact_sub")
    rendered = [
        classify_surface(blob, EXPECTED_MAIN, MAIN_ROWS, f"main{i}_rendered")
        for i, blob in enumerate(mains, start=1)
    ]
    untouched = [
        classify_surface(blob, EXPECTED_MAIN_UNTOUCHED, MAIN_ROWS, f"main{i}_untouched")
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
            f"pixel ownership drift cgadsub={expected_cgadsub}: "
            f"sub={sub_report!r} rendered={rendered_indices} untouched={untouched_indices}"
        )

    queue = require_queue(root, expected_cgadsub)
    state = require_fence(root)
    words = mailbox_words(root)
    want_result = (
        EXPECTED_ENABLED_RESULT if expected_cgadsub else EXPECTED_DISABLED_RESULT
    )
    want = (
        EXPECTED_MAIN_RGB555,
        EXPECTED_SUB_RGB555,
        want_result,
        expected_cgadsub,
    )
    if words != want:
        raise ValueError(
            "gating mailbox "
            + ",".join(f"{x:04X}" for x in words)
            + " != "
            + ",".join(f"{x:04X}" for x in want)
        )

    return {
        "passed": True,
        "cgadsub": expected_cgadsub,
        "main_rendered_index": rendered_indices[0],
        "mailbox_rgb555": [f"0x{x:04X}" for x in words],
        "queue": queue,
        "capture_state": state,
        "sub_report": sub_report,
        "main_rendered_report": rendered[rendered_indices[0] - 1],
    }


def classify(disabled: Path, enabled: Path) -> dict[str, object]:
    off = classify_state(disabled, 0)
    on = classify_state(enabled, 1)

    for name in ("sub.bin", "main1.bin", "main2.bin", "main3.bin"):
        if (disabled / name).read_bytes() != (enabled / name).read_bytes():
            raise ValueError(f"rendered operand changed across gating states: {name}")

    if off["main_rendered_index"] != on["main_rendered_index"]:
        raise ValueError("Main ownership rotated across gating states")

    return {
        "classification": "HCOMP_CGADSUB_BG1_LIVE_GATING_VALIDATED",
        "passed": True,
        "disabled": off,
        "enabled": on,
        "rendered_operands_identical_across_gate_states": True,
        "controlled_main_winner": "BG1",
        "general_winner_metadata": "NOT_PROVEN",
        "add_sub_half_modes": "NOT_PROVEN",
        "real_n64_rdp_rsp_fence": "NOT_PROVEN",
    }


def patch_fixture_cgadsub(root: Path, value: int) -> None:
    for name in ("q1", "q2"):
        path = root / f"section-{name}.bin"
        data = bytearray(path.read_bytes())
        data[CGADSUB] = value
        data[SECTION_SIZE + CGADSUB] = value
        path.write_bytes(data)


def write_fixture(root: Path, value: int) -> None:
    write_pixel_fixture(root, rendered_main=1)
    patch_fixture_cgadsub(root, value)
    result = EXPECTED_ENABLED_RESULT if value else EXPECTED_DISABLED_RESULT
    words = (EXPECTED_MAIN_RGB555, EXPECTED_SUB_RGB555, result, value)
    (root / "gating-mailbox.bin").write_bytes(
        b"".join(x.to_bytes(2, "big") for x in words)
    )


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        off = base / "off"
        on = base / "on"
        off.mkdir()
        on.mkdir()
        write_fixture(off, 0)
        write_fixture(on, 1)
        result = classify(off, on)
        assert result["passed"], result

        bad = bytearray((on / "gating-mailbox.bin").read_bytes())
        bad[4:6] = EXPECTED_DISABLED_RESULT.to_bytes(2, "big")
        (on / "gating-mailbox.bin").write_bytes(bad)
        try:
            classify(off, on)
        except ValueError:
            pass
        else:
            raise AssertionError("wrong enabled arithmetic result unexpectedly accepted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--disabled", type=Path)
    ap.add_argument("--enabled", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        print("H-COMP CGADSUB live-gating classifier self-test: PASS")
        return 0
    if args.disabled is None or args.enabled is None:
        ap.error("--disabled and --enabled are required unless --self-test")

    result = classify(args.disabled, args.enabled)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
