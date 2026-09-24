#!/usr/bin/env python3
"""L0 proof for exact SNES W1/W2 layer and color-window span contracts.

Reference semantics are transcribed from pinned ares
17813a3ccda21ab9bd45f09bfc2f91196dbf50ff:
  ares/sfc/ppu-performance/window.cpp
  ares/sfc/ppu-performance/io.cpp

The proof exhausts every endpoint topology on an 8-pixel ordered domain. Window
truth depends only on interval membership and relative endpoint order, so this
covers all order/equality/reversed-bound shapes. Separate 256-pixel edge cases
cover the byte-domain endpoints, especially the legal x=255 singleton.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

ARES_PIN = "17813a3ccda21ab9bd45f09bfc2f91196dbf50ff"

# Exact current publication layout (58880d5f lineage), independently audited.
PRIO_CHECKS = 0xE7C
WIN_BOUNDS = 0xE84
CURRENT_OBJ_WIN_COUNT = 0xE89
PROPOSED_WIN_COUNT = 0xE8A
OVERLAY_MAIN_SRC = 0xE90
OVERLAY_MODE7_SRC = 0xE94
HCOMP_RAW_PALETTE_PTRS = 0xE98

COMBINE_NAMES = ("OR", "AND", "XOR", "XNOR")
COLOR_MASK_NAMES = ("ALWAYS", "INSIDE", "OUTSIDE", "NEVER")


@dataclass(frozen=True)
class WindowConfig:
    one_invert: bool
    one_enable: bool
    two_invert: bool
    two_enable: bool
    combine: int


def decode_select(nibble: int, combine: int) -> WindowConfig:
    return WindowConfig(
        one_invert=bool(nibble & 0x1),
        one_enable=bool(nibble & 0x2),
        two_invert=bool(nibble & 0x4),
        two_enable=bool(nibble & 0x8),
        combine=combine,
    )


def inside(x: int, left: int, right: int) -> bool:
    # Matches ares: reversed bounds simply contain no x.
    return x >= left and x <= right


def combine(one: bool, two: bool, mode: int) -> bool:
    if mode == 0:
        return one or two
    if mode == 1:
        return one and two
    if mode == 2:
        return one != two
    if mode == 3:
        return one == two
    raise AssertionError(mode)


def ares_layer_mask_pixel(
    x: int,
    *,
    cfg: WindowConfig,
    screen_window_enable: bool,
    one_left: int,
    one_right: int,
    two_left: int,
    two_right: int,
) -> bool:
    """Return ares Layer::render output: True means the layer is masked."""
    if not screen_window_enable or (not cfg.one_enable and not cfg.two_enable):
        return False

    one = inside(x, one_left, one_right)
    two = inside(x, two_left, two_right)

    if cfg.one_enable and not cfg.two_enable:
        return one != cfg.one_invert
    if cfg.two_enable and not cfg.one_enable:
        return two != cfg.two_invert

    one_mask = one != cfg.one_invert
    two_mask = two != cfg.two_invert
    return combine(one_mask, two_mask, cfg.combine)


def ares_layer_visible(width: int, **kwargs: object) -> list[bool]:
    return [
        not ares_layer_mask_pixel(x, **kwargs)
        for x in range(width)
    ]


def ares_color_enable_pixel(
    x: int,
    *,
    cfg: WindowConfig,
    color_mask: int,
    one_left: int,
    one_right: int,
    two_left: int,
    two_right: int,
) -> bool:
    """Return ares Color::render output: True means color is enabled."""
    if color_mask == 0:  # always
        return True
    if color_mask == 3:  # never
        return False

    set_value = color_mask == 1
    clear_value = not set_value

    if not cfg.one_enable and not cfg.two_enable:
        return clear_value

    one = inside(x, one_left, one_right)
    two = inside(x, two_left, two_right)

    if cfg.one_enable and not cfg.two_enable:
        if cfg.one_invert:
            set_value = not set_value
            clear_value = not clear_value
        return set_value if one else clear_value

    if cfg.two_enable and not cfg.one_enable:
        if cfg.two_invert:
            set_value = not set_value
            clear_value = not clear_value
        return set_value if two else clear_value

    one_mask = one != cfg.one_invert
    two_mask = two != cfg.two_invert
    selected = combine(one_mask, two_mask, cfg.combine)
    return set_value if selected else clear_value


def ares_color_enabled(width: int, **kwargs: object) -> list[bool]:
    return [
        ares_color_enable_pixel(x, **kwargs)
        for x in range(width)
    ]


def encode_true_spans(bits: list[bool]) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    start: int | None = None
    for x, value in enumerate(bits):
        if value and start is None:
            start = x
        if start is not None and (not value or x == len(bits) - 1):
            end = x if value and x == len(bits) - 1 else x - 1
            spans.append((start, end))
            start = None
    return tuple(spans)


def decode_spans(width: int, spans: tuple[tuple[int, int], ...]) -> list[bool]:
    bits = [False] * width
    for lower, upper in spans:
        if not (0 <= lower <= upper < width):
            raise AssertionError(f"invalid inclusive span {(lower, upper)}")
        for x in range(lower, upper + 1):
            if bits[x]:
                raise AssertionError(f"overlapping span at x={x}: {spans}")
            bits[x] = True
    return bits


def prove_layout_capacity() -> None:
    if WIN_BOUNDS != PRIO_CHECKS + 8:
        raise AssertionError("unexpected WIN_BOUNDS layout")
    if CURRENT_OBJ_WIN_COUNT != WIN_BOUNDS + 5:
        raise AssertionError("unexpected current OBJ count layout")

    six_span_bytes_end = WIN_BOUNDS + 6  # exclusive: E84..E89
    if six_span_bytes_end != PROPOSED_WIN_COUNT:
        raise AssertionError("proposed count must follow six span bytes")
    if not (PROPOSED_WIN_COUNT < OVERLAY_MAIN_SRC):
        raise AssertionError("proposed count overlaps overlay source pointer")
    if OVERLAY_MODE7_SRC != OVERLAY_MAIN_SRC + 4:
        raise AssertionError("overlay pointer ABI moved")
    if HCOMP_RAW_PALETTE_PTRS != OVERLAY_MODE7_SRC + 4:
        raise AssertionError("raw-palette pointer ABI moved")


def prove_exhaustive_topologies() -> tuple[int, int, int, tuple | None, tuple | None]:
    width = 8
    layer_cases = 0
    color_cases = 0
    max_layer = 0
    max_color = 0
    layer_max_example = None
    color_max_example = None

    endpoints = range(width)
    for one_left, one_right, two_left, two_right in product(endpoints, repeat=4):
        common = dict(
            one_left=one_left,
            one_right=one_right,
            two_left=two_left,
            two_right=two_right,
        )
        for nibble in range(16):
            for mode in range(4):
                cfg = decode_select(nibble, mode)

                for screen_enable in (False, True):
                    visible = ares_layer_visible(
                        width,
                        cfg=cfg,
                        screen_window_enable=screen_enable,
                        **common,
                    )
                    spans = encode_true_spans(visible)
                    if decode_spans(width, spans) != visible:
                        raise AssertionError(
                            f"layer span roundtrip mismatch: {cfg=} {common=} "
                            f"{screen_enable=} {spans=}"
                        )
                    if len(spans) > 3:
                        raise AssertionError(
                            f"layer needs >3 spans: {cfg=} {common=} "
                            f"{screen_enable=} {spans=}"
                        )
                    if len(spans) > max_layer:
                        max_layer = len(spans)
                        layer_max_example = (cfg, common.copy(), screen_enable, spans)
                    layer_cases += 1

                for color_mask in range(4):
                    enabled = ares_color_enabled(
                        width,
                        cfg=cfg,
                        color_mask=color_mask,
                        **common,
                    )
                    spans = encode_true_spans(enabled)
                    if decode_spans(width, spans) != enabled:
                        raise AssertionError(
                            f"color span roundtrip mismatch: {cfg=} {common=} "
                            f"{color_mask=} {spans=}"
                        )
                    if len(spans) > 3:
                        raise AssertionError(
                            f"color needs >3 spans: {cfg=} {common=} "
                            f"{color_mask=} {spans=}"
                        )
                    if len(spans) > max_color:
                        max_color = len(spans)
                        color_max_example = (cfg, common.copy(), color_mask, spans)
                    color_cases += 1

    if max_layer != 3:
        raise AssertionError(f"expected a reachable 3-span layer topology, got {max_layer}")
    if max_color != 3:
        raise AssertionError(f"expected a reachable 3-span color topology, got {max_color}")

    return layer_cases, color_cases, max_layer, layer_max_example, color_max_example


def prove_full_range_edges() -> None:
    width = 256

    # Legal singleton at the final pixel: W1 enabled + inverted => only the
    # inclusive interior remains visible for a layer.
    cfg = decode_select(0x3, 0)
    visible = ares_layer_visible(
        width,
        cfg=cfg,
        screen_window_enable=True,
        one_left=255,
        one_right=255,
        two_left=0,
        two_right=0,
    )
    spans = encode_true_spans(visible)
    if spans != ((255, 255),):
        raise AssertionError(f"x255 singleton lost: {spans}")

    # Same requirement for W2 proves the second window has identical endpoint
    # semantics and cannot reuse an in-band 255 terminator.
    cfg = decode_select(0xC, 0)
    visible = ares_layer_visible(
        width,
        cfg=cfg,
        screen_window_enable=True,
        one_left=0,
        one_right=0,
        two_left=255,
        two_right=255,
    )
    spans = encode_true_spans(visible)
    if spans != ((255, 255),):
        raise AssertionError(f"W2 x255 singleton lost: {spans}")

    # Reversed normal W1 contains no pixels, so it masks nothing.
    cfg = decode_select(0x2, 0)
    visible = ares_layer_visible(
        width,
        cfg=cfg,
        screen_window_enable=True,
        one_left=200,
        one_right=100,
        two_left=0,
        two_right=0,
    )
    if encode_true_spans(visible) != ((0, 255),):
        raise AssertionError("reversed W1 did not leave full layer visible")

    # CGWSEL color-window modes 0/3 are unconditional regardless W1/W2 state.
    cfg = decode_select(0xF, 3)
    common = dict(
        cfg=cfg,
        one_left=255,
        one_right=255,
        two_left=0,
        two_right=255,
    )
    if encode_true_spans(ares_color_enabled(width, color_mask=0, **common)) != ((0, 255),):
        raise AssertionError("color ALWAYS mode is not full screen")
    if encode_true_spans(ares_color_enabled(width, color_mask=3, **common)) != ():
        raise AssertionError("color NEVER mode is not empty")


def prove_current_w1_only_helper_is_insufficient() -> None:
    # Concrete legal W1+W2 XOR case. Current Sodium64 calc_windows only
    # recognizes single-W1 nibble 2/3, so a both-enabled nibble cannot express
    # these two holes and falls through its no-window behavior.
    width = 8
    cfg = decode_select(0xA, 2)  # W1+W2 enabled, no invert, XOR
    reference = ares_layer_visible(
        width,
        cfg=cfg,
        screen_window_enable=True,
        one_left=1,
        one_right=2,
        two_left=5,
        two_right=6,
    )
    current_fallthrough = [True] * width
    if reference == current_fallthrough:
        raise AssertionError("chosen W2/combine discriminator did not distinguish current helper")
    if encode_true_spans(reference) != ((0, 0), (3, 4), (7, 7)):
        raise AssertionError(f"unexpected XOR reference spans: {encode_true_spans(reference)}")


def main() -> int:
    prove_layout_capacity()
    prove_current_w1_only_helper_is_insufficient()
    layer_cases, color_cases, max_layer, layer_example, color_example = prove_exhaustive_topologies()
    prove_full_range_edges()

    print("HCOMP_WINDOW_CONTRACT_VALIDATED")
    print(f"ares_pin={ARES_PIN}")
    print(f"layer_topology_cases={layer_cases}")
    print(f"color_topology_cases={color_cases}")
    print(f"max_layer_visible_spans={max_layer}")
    print("max_color_enable_spans=3")
    print(
        f"layout=WIN_BOUNDS:0x{WIN_BOUNDS:X}-0x{WIN_BOUNDS + 5:X},"
        f"WIN_COUNT:0x{PROPOSED_WIN_COUNT:X},"
        f"OVERLAY_MAIN_SRC:0x{OVERLAY_MAIN_SRC:X}"
    )
    print(f"layer_three_span_example={layer_example!r}")
    print(f"color_three_span_example={color_example!r}")
    print("x255_singleton=preserved")
    print("current_w1_only_helper=W2_COMBINE_INSUFFICIENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
