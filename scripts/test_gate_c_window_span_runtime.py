#!/usr/bin/env python3
"""Host oracle for the exact event-scan window-span helper used by the RSP.

The reference is the already-pinned ares window model carried by
scripts/test_gate_c_h_comp_window_contract.py. This test mirrors the RSP
algorithm (scan only W1/W2 transition coordinates, merge adjacent true spans)
and checks source/layout invariants that are easy to break while editing the
fixed renderer slot.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_h_comp_window_contract as ref

EXPECTED_FIXED_SLOT_INSNS = 242
EXPECTED_CASES = 8 ** 4 * 16 * 4 * 2


def selected_pixel(x: int, cfg: ref.WindowConfig, bounds: tuple[int, int, int, int]) -> bool:
    one_left, one_right, two_left, two_right = bounds

    one = False
    if cfg.one_enable:
        one = ref.inside(x, one_left, one_right) != cfg.one_invert

    two = False
    if cfg.two_enable:
        two = ref.inside(x, two_left, two_right) != cfg.two_invert

    if cfg.one_enable and not cfg.two_enable:
        return one
    if cfg.two_enable and not cfg.one_enable:
        return two
    if not cfg.one_enable and not cfg.two_enable:
        return False
    return ref.combine(one, two, cfg.combine)


def rsp_style_spans(
    width: int,
    cfg: ref.WindowConfig,
    bounds: tuple[int, int, int, int],
    want_selected: bool,
) -> tuple[tuple[int, int], ...]:
    """Mirror calc_window_spans: visit only edge coordinates and merge truth."""

    one_left, one_right, two_left, two_right = bounds
    current = 0
    spans: list[list[int]] = []

    while True:
        selected = selected_pixel(current, cfg, bounds)
        truth = selected if want_selected else not selected

        next_edge = width
        for candidate in (one_left, one_right + 1, two_left, two_right + 1):
            if current < candidate < next_edge:
                next_edge = candidate

        if truth:
            upper = next_edge - 1
            if spans and spans[-1][1] + 1 == current:
                spans[-1][1] = upper
            else:
                spans.append([current, upper])

        if next_edge == width:
            break
        current = next_edge

    out = tuple((lo, hi) for lo, hi in spans)
    if len(out) > 3:
        raise AssertionError(f"RSP-style helper exceeded 3 spans: {cfg=} {bounds=} {out=}")
    return out


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

                layer_bits = ref.ares_layer_visible(
                    width,
                    cfg=cfg,
                    screen_window_enable=True,
                    **common,
                )
                layer_ref = ref.encode_true_spans(layer_bits)
                layer_rsp = rsp_style_spans(width, cfg, bounds, want_selected=False)
                if layer_rsp != layer_ref:
                    raise AssertionError(
                        f"layer mismatch: {cfg=} {bounds=} {layer_rsp=} {layer_ref=}"
                    )
                cases += 1

                selected_bits = ref.ares_color_enabled(
                    width,
                    cfg=cfg,
                    color_mask=1,  # INSIDE == selected W1/W2 result
                    **common,
                )
                selected_ref = ref.encode_true_spans(selected_bits)
                selected_rsp = rsp_style_spans(width, cfg, bounds, want_selected=True)
                if selected_rsp != selected_ref:
                    raise AssertionError(
                        f"selected mismatch: {cfg=} {bounds=} "
                        f"{selected_rsp=} {selected_ref=}"
                    )
                cases += 1

    if cases != EXPECTED_CASES:
        raise AssertionError(f"unexpected exhaustive case count {cases}")
    return cases


def prove_full_range_edges() -> None:
    # W1 inverted singleton at x=255 => selected interior, visible complement.
    cfg = ref.decode_select(0x3, 0)
    bounds = (255, 255, 0, 0)
    if rsp_style_spans(256, cfg, bounds, True) != ((255, 255),):
        raise AssertionError("W1 selected x255 singleton lost")

    # W2 inverted singleton at x=255.
    cfg = ref.decode_select(0xC, 0)
    bounds = (0, 0, 255, 255)
    if rsp_style_spans(256, cfg, bounds, True) != ((255, 255),):
        raise AssertionError("W2 selected x255 singleton lost")

    # Reversed W1 contains nothing, so visible complement is full-screen.
    cfg = ref.decode_select(0x2, 0)
    bounds = (200, 100, 0, 0)
    if rsp_style_spans(256, cfg, bounds, False) != ((0, 255),):
        raise AssertionError("reversed W1 visibility mismatch")

    # Reachable 3-span XOR discriminator from the L0 contract.
    cfg = ref.decode_select(0xA, 2)
    bounds = (1, 2, 5, 6)
    expected = ((0, 0), (3, 4), (7, 255))
    got = rsp_style_spans(256, cfg, bounds, False)
    if got != expected:
        raise AssertionError(f"three-span XOR mismatch: {got}")


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
    defines = (ROOT / "src/defines.h").read_text()

    if "#define WIN_COUNT (WIN_BOUNDS + 0x6)" not in defines:
        raise AssertionError("WIN_COUNT is not at E8A-relative layout")
    if "OBJ_WIN_COUNT" in main_src or "OBJ_WIN_COUNT" in mode7_src:
        raise AssertionError("legacy OBJ-only window count remains")

    helper_main = extract(main_src, "calc_window_spans:", "calc_windows:")
    helper_mode7 = extract(mode7_src, "calc_window_spans:", "calc_windows:")
    insn_main = strip_instruction_lines(helper_main)
    insn_mode7 = strip_instruction_lines(helper_mode7)
    if insn_main != insn_mode7:
        raise AssertionError("common window helper diverged across RSP variants")

    forbidden = re.compile(
        r"\b(?:a3|t5|t9|v0|v1|gp|k0|k1|s[0-8])\b|\$v\d+|\bjal\b"
    )
    for line in insn_main:
        if forbidden.search(line):
            raise AssertionError(f"helper clobbers live renderer state: {line}")

    # The regular renderer slot must keep the exact parent instruction footprint.
    fixed = extract(main_src, "draw_bg:", "draw_mode7_entry:")
    count = len(strip_instruction_lines(fixed))
    if count != EXPECTED_FIXED_SLOT_INSNS:
        raise AssertionError(
            f"fixed renderer slot instruction drift: {count} != {EXPECTED_FIXED_SLOT_INSNS}"
        )

    # Everything from OBJ onward is resident/common and must stay instruction-identical.
    suffix_main = strip_instruction_lines(main_src[main_src.index("draw_obj:"):])
    suffix_mode7 = strip_instruction_lines(mode7_src[mode7_src.index("draw_obj:"):])
    if suffix_main != suffix_mode7:
        raise AssertionError("resident common suffix diverged across overlays")


def main() -> int:
    cases = prove_semantics()
    prove_full_range_edges()
    prove_source_abi()

    print("WINDOW_LAYER_RUNTIME_MODEL_VALIDATED")
    print(f"ares_pin={ref.ARES_PIN}")
    print(f"event_scan_cases={cases}")
    print("max_true_spans=3")
    print("x255_singleton=preserved")
    print("reversed_bounds=preserved")
    print(f"fixed_slot_instructions={EXPECTED_FIXED_SLOT_INSNS}")
    print("common_suffix=source_identical")
    print("live_register_contract=preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
