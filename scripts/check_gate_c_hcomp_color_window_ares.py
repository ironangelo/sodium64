#!/usr/bin/env python3
"""Strict baseline reproduction of missing H-COMP clip/prevent semantics.

A green diagnostic means the gap was reproduced, NEVER that color windows
are correct. The exact reference matrix is precommitted independently of the
measured baseline. Unexpected results fail instead of being explained away.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
import check_gate_c_hcomp_transparent_sub_ares as parent
from make_gate_c_hcomp_color_window import CASES, build_case
from test_gate_c_h_comp_window_contract import decode_select, ares_color_enable_pixel

# Offsets from the CPU's audited 64-byte section layout.
WHX, WOBJSEL, WOBJLOG = 46, 52, 54
GOLDEN_RESULTS = {
    "control-inside": 0x01EF, "control-outside": 0x01EF,
    "clip-inside": 0x03E0, "clip-outside": 0x01EF,
    "prevent-inside": 0x001F, "prevent-outside": 0x01EF,
    "both-inside": 0x0000, "both-outside": 0x01EF,
}


def require_section_layout() -> None:
    # Derive offsets from the runtime header, independently of fixture bytes.
    # Catch stale classifier constants even if self-test writer shares them.
    defines = (Path(__file__).resolve().parents[1] / "src/defines.h").read_text()
    relative = {"BGHOFS": 0}
    for name, previous, delta in re.findall(
        r"^#define\s+(\w+)\s+\((\w+)\s*\+\s*(0x[0-9A-Fa-f]+)\)", defines, re.M
    ):
        if previous in relative:
            relative[name] = relative[previous] + int(delta, 16)
    expected = {"WHX": WHX, "WOBJSEL": WOBJSEL, "WOBJLOG": WOBJLOG,
                "CGWSEL": parent.CGWSEL, "SUB_COLOR": parent.SUB_COLOR}
    if any(relative.get(k) != v for k, v in expected.items()):
        raise ValueError(f"classifier/header section layout conflict: {relative}")


def reference(case: str) -> dict[str, object]:
    cfg = CASES[case]
    args = dict(cfg=decode_select(2, 0), one_left=cfg["left"],
                one_right=cfg["right"], two_left=0, two_right=0)
    visible = ares_color_enable_pixel(0, color_mask=(cfg["cgwsel"] >> 6) & 3, **args)
    permitted = ares_color_enable_pixel(0, color_mask=(cfg["cgwsel"] >> 4) & 3, **args)
    main = 31 if visible else 0
    # Independent per-channel arithmetic; clip precedes math, disables HALF,
    # and leaves the rendered BG1 winner eligible.
    rgb = (main, 0, 0)
    if permitted:
        rgb = tuple((a + b) // 2 if visible else min(31, a + b)
                    for a, b in zip(rgb, (0, 31, 0)))
    result = rgb[0] | rgb[1] << 5 | rgb[2] << 10
    if result != GOLDEN_RESULTS[case]:
        raise ValueError(f"reference/precommitted oracle conflict for {case}")
    return {"main_visible": visible, "math_permitted": permitted,
            "half_effective": visible and permitted,
            "effective_main": main, "result_rgb555": f"0x{result:04X}"}


def baseline_cfg(case: str) -> dict[str, object]:
    return {**parent.MODES["sub-present-half"], "cgwsel": CASES[case]["cgwsel"]}


def require_window_queue(root: Path, case: str, report: dict) -> None:
    for queue in ("q1", "q2"):
        candidates = [v for k, v in report["reports"].items()
                      if k.startswith(queue + ":") and v["passed"]]
        if len(candidates) != 1:
            raise ValueError(f"{case}: both queue copies must be coherent ({queue})")
        mode = candidates[0]["normalization"]
        data = parent.norm((root / f"section-{queue}.bin").read_bytes(), mode)
        for i in range(2):
            rec = data[i * 64:(i + 1) * 64]
            want = bytes((CASES[case]["left"], CASES[case]["right"], 0, 0))
            if rec[WHX:WHX + 4] != want or rec[WOBJSEL] != 0x20 or rec[WOBJLOG] != 0:
                raise ValueError(f"{case}/{queue}/section{i}: window capture drift")


def classify(base: Path) -> dict[str, object]:
    require_section_layout()
    states = {}
    canonical = None
    invariant = None
    for case in CASES:
        root = base / case
        # Reuse the already strict parent surface/provenance/fence oracle.
        # This CLI is a separate process; all aliases share identical operands.
        parent.MODES[case] = baseline_cfg(case)
        observed = parent.classify_state(root, case)
        require_window_queue(root, case, observed["queue"])
        main = parent.canonical_main(root, observed)
        raw = tuple((root / n).read_bytes() for n in
                    ("sub.bin", "provenance-prefix.bin", "provenance.bin", "provenance-suffix.bin"))
        if canonical is not None and (canonical != main or invariant != raw):
            raise ValueError("window controls changed rendered operands or provenance")
        canonical, invariant = main, raw
        states[case] = {"reference": reference(case), "observed": observed,
                        "matches_reference": GOLDEN_RESULTS[case] == 0x01EF}
    mismatches = [c for c, s in states.items() if not s["matches_reference"]]
    if mismatches != ["clip-inside", "prevent-inside", "both-inside"]:
        raise ValueError(f"unexpected baseline gap family {mismatches}")
    return {"classification": "HCOMP_COLOR_WINDOW_GAP_REPRODUCED", "passed": True,
            "runtime_color_windows_validated": False, "runtime_changed": False,
            "states": states, "reference_mismatches": mismatches,
            "rendered_operands_and_provenance_invariant": True,
            "smw_iris_correctness": "NOT_PROVEN", "real_n64": "NOT_PROVEN"}


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        for index, case in enumerate(CASES):
            root = base / case
            root.mkdir()
            parent.MODES[case] = baseline_cfg(case)
            parent.write_fixture(root, case, index % 3 + 1)
            for queue in ("q1", "q2"):
                p = root / f"section-{queue}.bin"
                q = bytearray(p.read_bytes())
                for i in range(2):
                    start = i * 64
                    q[start + WHX:start + WHX + 4] = bytes((CASES[case]["left"], CASES[case]["right"], 0, 0))
                    q[start + WOBJSEL] = 0x20
                    q[start + WOBJLOG] = 0
                p.write_bytes(q)
            if build_case(case) != build_case(case):
                raise AssertionError("non-deterministic guest")
        if not classify(base)["passed"]:
            raise AssertionError("positive diagnostic fixture failed")
        # Reject missing window controls, accidental HALF change, unbounded
        # geometry, and stale-frame captures independently.
        root = base / "clip-inside"
        for name, offset, replacement in (
            ("section-q1.bin", WOBJSEL, b"\x00"),
            ("gating-mailbox.bin", 22, b"\x00\x01"),
            ("section-q2.bin", 63, b"\xE0"),
        ):
            p = root / name
            original = p.read_bytes()
            bad = bytearray(original)
            bad[offset:offset + len(replacement)] = replacement
            p.write_bytes(bad)
            try:
                classify(base)
            except ValueError:
                pass
            else:
                raise AssertionError(f"corrupt fixture accepted: {name}")
            p.write_bytes(original)
        p = root / "capture-state.json"
        original = p.read_text()
        state = json.loads(original)
        state["guest_frame_delta"] = 0
        p.write_text(json.dumps(state))
        try:
            classify(base)
        except ValueError:
            pass
        else:
            raise AssertionError("stale frame accepted")
        p.write_text(original)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--captures", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        print("H-COMP color-window gap oracle self-test: PASS")
        return 0
    if args.captures is None:
        ap.error("--captures is required")
    result = classify(args.captures)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(output, end="")
    if args.output:
        args.output.write_text(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
