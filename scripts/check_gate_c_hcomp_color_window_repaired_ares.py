#!/usr/bin/env python3
"""Strict repaired-sample acceptance; the original gap oracle stays unchanged."""
from __future__ import annotations
import argparse
import json
import tempfile
from pathlib import Path
import check_gate_c_hcomp_transparent_sub_ares as parent
from check_gate_c_hcomp_color_window_ares import (
    CASES, WHX, WOBJSEL, WOBJLOG, require_section_layout,
    require_window_queue, reference,
)


def repaired_cfg(case: str) -> dict:
    ref = reference(case)
    return {**parent.MODES["sub-present-half"], "cgwsel": CASES[case]["cgwsel"],
            "main": ref["effective_main"], "gate": int(ref["math_permitted"]),
            "result": int(ref["result_rgb555"], 16),
            "source_flags": 1 | (int(ref["half_effective"]) << 8),
            "extra": (parent.RED_RGB555,
                      int(ref["main_visible"]) | (int(ref["math_permitted"]) << 1))}


def classify(base: Path) -> dict:
    require_section_layout()
    states, canonical, invariant = {}, None, None
    for case in CASES:
        root = base / case
        parent.MODES[case] = repaired_cfg(case)
        observed = parent.classify_state(root, case)
        require_window_queue(root, case, observed["queue"])
        main = parent.canonical_main(root, observed)
        raw = tuple((root / n).read_bytes() for n in
                    ("sub.bin", "provenance-prefix.bin", "provenance.bin", "provenance-suffix.bin"))
        if canonical is not None and (canonical != main or invariant != raw):
            raise ValueError("window controls changed raw operands or provenance")
        canonical, invariant = main, raw
        states[case] = {"reference": reference(case), "observed": observed,
                        "matches_reference": True}
    return {"classification": "HCOMP_COLOR_WINDOW_SAMPLE_REPAIR_VALIDATED", "passed": True,
            "runtime_color_window_sample_validated": True,
            "states": states, "reference_mismatches": [],
            "rendered_operands_and_provenance_invariant": True,
            "coverage": "eight_W1_singleton_cases_at_semantic_x0",
            "all_16_mode_pairs": "NOT_PROVEN", "W2_invert_combine": "NOT_PROVEN",
            "full_frame_output": "NOT_PROVEN", "smw_iris_correctness": "NOT_PROVEN",
            "real_n64": "NOT_PROVEN"}


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        for i, case in enumerate(CASES):
            root = base / case
            root.mkdir()
            parent.MODES[case] = repaired_cfg(case)
            parent.write_fixture(root, case, i % 3 + 1)
            for queue in ("q1", "q2"):
                path = root / f"section-{queue}.bin"
                data = bytearray(path.read_bytes())
                for j in range(2):
                    start = j * 64
                    data[start + WHX:start + WHX + 4] = bytes((CASES[case]["left"], CASES[case]["right"], 0, 0))
                    data[start + WOBJSEL] = 0x20
                    data[start + WOBJLOG] = 0
                path.write_bytes(data)
        assert classify(base)["passed"]
        # Exact results alone must not accept wrong effective Main/gate/HALF,
        # raw carrier, window predicate, queue geometry, or guest-frame fence.
        for case, name, offset, replacement in (
            ("clip-inside", "gating-mailbox.bin", 0, b"\x00\x1f"),
            ("clip-inside", "gating-mailbox.bin", 22, b"\x01\x01"),
            ("clip-inside", "gating-mailbox.bin", 28, b"\x00\x00"),
            ("clip-inside", "gating-mailbox.bin", 30, b"\x00\x03"),
            ("prevent-inside", "gating-mailbox.bin", 6, b"\x00\x01"),
            ("both-inside", "gating-mailbox.bin", 4, b"\x01\xef"),
            ("control-outside", "section-q2.bin", WOBJSEL, b"\x00"),
            ("clip-inside", "section-q1.bin", 63, b"\xe0"),
        ):
            path = base / case / name
            original = path.read_bytes()
            bad = bytearray(original); bad[offset:offset + len(replacement)] = replacement
            path.write_bytes(bad)
            try: classify(base)
            except ValueError: pass
            else: raise AssertionError(f"corruption accepted: {case}/{name}/{offset}")
            path.write_bytes(original)
        path = base / "clip-inside" / "capture-state.json"
        state = json.loads(path.read_text()); state["guest_frame_delta"] = 0
        path.write_text(json.dumps(state))
        try: classify(base)
        except ValueError: pass
        else: raise AssertionError("stale frame accepted")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--captures", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test(); print("H-COMP repaired color-window oracle self-test: PASS"); return 0
    if args.captures is None: ap.error("--captures is required")
    output = json.dumps(classify(args.captures), indent=2, sort_keys=True) + "\n"
    print(output, end="")
    if args.output: args.output.write_text(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
