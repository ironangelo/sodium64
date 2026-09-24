#!/usr/bin/env python3
"""Host oracle for exact color-window segmentation consumed by the legacy fill loop."""

from __future__ import annotations

from itertools import product
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_h_comp_window_contract as ref
import test_gate_c_window_span_runtime as layer

EXPECTED_CASES = 8 ** 4 * 16 * 4 * 4


def color_segments(width: int, cfg: ref.WindowConfig, bounds: tuple[int, int, int, int], mode: int):
    """Mirror calc_color_window_segments at the truth/segment level."""
    if mode == 0:
        return True, (width - 1,)
    if mode == 3:
        return False, (width - 1,)

    spans = layer.rsp_style_spans(width, cfg, bounds, want_selected=(mode == 1))
    if not spans:
        return False, (width - 1,)

    initial = spans[0][0] == 0
    ends: list[int] = []
    for lo, hi in spans:
        if lo > 0:
            end = lo - 1
            if not ends or ends[-1] != end:
                ends.append(end)
        if not ends or ends[-1] != hi:
            ends.append(hi)

    if ends[-1] != width - 1:
        ends.append(width - 1)
    if len(ends) > 7:
        raise AssertionError(f"too many alternating segments: {spans=} {ends=}")
    return initial, tuple(ends)


def decode_segments(width: int, initial: bool, ends: tuple[int, ...]) -> list[bool]:
    if not ends or ends[-1] != width - 1:
        raise AssertionError(f"segment list does not terminate at screen edge: {ends}")
    bits = [False] * width
    start = 0
    truth = initial
    for end in ends:
        if not (start <= end < width):
            raise AssertionError(f"bad segment {start=} {end=} {ends=}")
        for x in range(start, end + 1):
            bits[x] = truth
        start = end + 1
        truth = not truth
    if start != width:
        raise AssertionError(f"segment list did not cover screen: {start=} {width=}")
    return bits


def prove_semantics() -> int:
    width = 8
    cases = 0
    for bounds in product(range(width), repeat=4):
        common = dict(
            one_left=bounds[0],
            one_right=bounds[1],
            two_left=bounds[2],
            two_right=bounds[3],
        )
        for nibble in range(16):
            for logic in range(4):
                cfg = ref.decode_select(nibble, logic)
                for mode in range(4):
                    reference = ref.ares_color_enabled(
                        width,
                        cfg=cfg,
                        color_mask=mode,
                        **common,
                    )
                    initial, ends = color_segments(width, cfg, bounds, mode)
                    got = decode_segments(width, initial, ends)
                    if got != reference:
                        raise AssertionError(
                            f"color-window mismatch: {cfg=} {bounds=} {mode=} "
                            f"{initial=} {ends=} {got=} {reference=}"
                        )
                    cases += 1
    if cases != EXPECTED_CASES:
        raise AssertionError(f"unexpected case count {cases} != {EXPECTED_CASES}")
    return cases


def prove_full_range_edges() -> None:
    width = 256

    # A one-pixel enabled segment at x=0 is the discriminator the old fill
    # loop missed: the following segment must begin at x=1, not x=0 again.
    cfg = ref.decode_select(0x2, 0)
    bounds = (0, 0, 0, 0)
    initial, ends = color_segments(width, cfg, bounds, 1)
    got = decode_segments(width, initial, ends)
    expected = ref.ares_color_enabled(
        width, cfg=cfg, color_mask=1,
        one_left=0, one_right=0, two_left=0, two_right=0,
    )
    if got != expected or not initial or ends[:2] != (0, 255):
        raise AssertionError(
            f"x0 singleton transition mismatch: {initial=} {ends=}"
        )

    # Inverted W1 makes the selected region outside the singleton; INSIDE mode
    # therefore enables everything except x255.
    cfg = ref.decode_select(0x3, 0)
    bounds = (255, 255, 0, 0)
    initial, ends = color_segments(width, cfg, bounds, 1)
    got = decode_segments(width, initial, ends)
    expected = ref.ares_color_enabled(
        width, cfg=cfg, color_mask=1,
        one_left=255, one_right=255, two_left=0, two_right=0,
    )
    if got != expected or got[255]:
        raise AssertionError("W1 x255 color edge lost")

    # OUTSIDE mode is the exact complement and must retain the x255 singleton.
    initial, ends = color_segments(width, cfg, bounds, 2)
    got = decode_segments(width, initial, ends)
    if sum(got) != 1 or not got[255]:
        raise AssertionError("W1 x255 outside singleton lost")

    # Reversed W1 contains no pixels.
    cfg = ref.decode_select(0x2, 0)
    bounds = (200, 100, 0, 0)
    initial, ends = color_segments(width, cfg, bounds, 1)
    if any(decode_segments(width, initial, ends)):
        raise AssertionError("reversed W1 INSIDE should be empty")

    # Reachable three-span XOR topology exercises the seven-segment maximum.
    cfg = ref.decode_select(0xA, 2)
    bounds = (1, 2, 5, 6)
    initial, ends = color_segments(width, cfg, bounds, 2)
    got = decode_segments(width, initial, ends)
    expected = ref.ares_color_enabled(
        width, cfg=cfg, color_mask=2,
        one_left=1, one_right=2, two_left=5, two_right=6,
    )
    if got != expected:
        raise AssertionError(f"three-span color XOR mismatch: {initial=} {ends=}")


def strip_instruction_lines(block: str) -> list[str]:
    out: list[str] = []
    for raw in block.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.endswith(":") or line.startswith(".") or line.startswith("#"):
            continue
        out.append(line)
    return out


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i)
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def prove_source_abi() -> None:
    main_src = (ROOT / "src/rsp_main.S").read_text()
    mode7_src = (ROOT / "src/rsp_mode7.S").read_text()

    if "calc_windows:" in main_src or "calc_windows:" in mode7_src:
        raise AssertionError("obsolete W1-only calc_windows remains")

    helper_main = extract(main_src, "calc_color_window_segments:", "calc_bg_window_spans:")
    helper_mode7 = extract(mode7_src, "calc_color_window_segments:", "calc_bg_window_spans:")
    if strip_instruction_lines(helper_main) != strip_instruction_lines(helper_mode7):
        raise AssertionError("color-window helper diverged across RSP variants")

    common_main = extract(main_src, "calc_window_spans:", "multiply:")
    common_mode7 = extract(mode7_src, "calc_window_spans:", "multiply:")
    if strip_instruction_lines(common_main) != strip_instruction_lines(common_mode7):
        raise AssertionError("shared span helper diverged across RSP variants")

    prefix_main = extract(main_src, "not_blank:", "draw_bg:")
    prefix_mode7 = extract(mode7_src, "not_blank:", "draw_bg:")
    if strip_instruction_lines(prefix_main) != strip_instruction_lines(prefix_mode7):
        raise AssertionError("pre-overlay color-window prefix diverged across variants")

    forbidden = re.compile(r"\b(?:s[2-8]|v0|v1|gp|k0|k1)\b|\$v\d+")
    for line in strip_instruction_lines(helper_main):
        if forbidden.search(line):
            raise AssertionError(f"color helper clobbers protected renderer state: {line}")

    for required in (
        "move a3, t6",
        "move t6, a3",
        "move t9, ra",
        "move ra, t9",
        "jal calc_window_spans",
        "lbu t0, CGWSEL",
        "lbu t0, WOBJSEL",
        "lbu t0, WOBJLOG",
        "li a0, WIN_BOUNDS",
        "lbu t8, WIN_BOUNDS + 0",
        "li t9, 0",
    ):
        if required not in helper_main:
            raise AssertionError(f"missing color-helper ABI/semantic anchor: {required}")

    # The actual backdrop fill loop must distinguish first-vs-later segments by
    # ordinal, not by previous coordinate value. Otherwise a boundary at x=0
    # makes the second segment start at x=0 and overwrite the singleton.
    fill_loop = extract(main_src, "fill_backdrop:", "// Skip layers for force blank")
    if "sltu t0, zero, t9" not in fill_loop:
        raise AssertionError("fill loop does not use segment ordinal for +1")
    if "sltu t0, zero, t7" in fill_loop:
        raise AssertionError("legacy coordinate-based x0 overlap rule remains")

    prefix = extract(main_src, "oam_skip:", "not_blank:")
    if "li t9, 0 // Segment ordinal; zero means first segment" not in prefix:
        raise AssertionError("backdrop segment ordinal does not initialize at zero")


def main() -> int:
    cases = prove_semantics()
    prove_full_range_edges()
    prove_source_abi()
    print("COLOR_WINDOW_RUNTIME_MODEL_VALIDATED")
    print(f"ares_pin={ref.ARES_PIN}")
    print(f"color_segment_cases={cases}")
    print("max_segment_ends=7")
    print("x0_x255_edges=preserved")
    print("reversed_bounds=preserved")
    print("common_helpers=source_identical")
    print("protected_register_contract=preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
