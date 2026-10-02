#!/usr/bin/env python3
"""Semantic/source contract for HCOMP FAST1.

FAST1 is intentionally narrow: CGADSUB=$20, CGWSEL=$12, black Main backdrop,
and one full-screen selected color-window span [0,255]. Under those SNES
conditions color math is add/full and only Main backdrop is eligible. Therefore
rendering fixed-color + Sub first, then transparent Main layers, is exactly the
same pixel equation as the general compositor.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def eligible(cgadsub, cgwsel, main_color, win_count, lower, upper):
    return (
        cgadsub == 0x20
        and cgwsel == 0x12
        and main_color == 0
        and win_count == 1
        and lower == 0
        and upper == 255
    )


def general_pixel(main_present, main_pixel, sub_present, sub_pixel, fixed_color):
    # Only backdrop participates. Main backdrop is black and full-screen math
    # is ADD/full, so black + selected second operand == second operand.
    if main_present:
        return main_pixel
    return sub_pixel if sub_present else fixed_color


def fast1_pixel(main_present, main_pixel, sub_present, sub_pixel, fixed_color):
    # Base target is fixed color, Sub opaque pixels overwrite it, then Main
    # opaque pixels overwrite the result.
    base = sub_pixel if sub_present else fixed_color
    return main_pixel if main_present else base


assert eligible(0x20, 0x12, 0, 1, 0, 255)
for args in [
    (0x21, 0x12, 0, 1, 0, 255),
    (0x20, 0x02, 0, 1, 0, 255),
    (0x20, 0x12, 1, 1, 0, 255),
    (0x20, 0x12, 0, 0, 0, 255),
    (0x20, 0x12, 0, 2, 0, 255),
    (0x20, 0x12, 0, 1, 1, 255),
    (0x20, 0x12, 0, 1, 0, 254),
]:
    assert not eligible(*args), args

# Exhaust every 15-bit source value independently. The equation does not
# depend on a relationship between sub and fixed colors.
for color in range(0x8000):
    assert general_pixel(False, 0x1234, True, color, 0x4567) == fast1_pixel(
        False, 0x1234, True, color, 0x4567
    )
    assert general_pixel(False, 0x1234, False, 0x2345, color) == fast1_pixel(
        False, 0x1234, False, 0x2345, color
    )
    assert general_pixel(True, color, True, 0x3456, 0x4567) == fast1_pixel(
        True, color, True, 0x3456, 0x4567
    )

src = (ROOT / "src/rsp_hcomp.S").read_text()
required = [
    "beq t0, t1, hcomp_fast1_probe",
    "xori t0, t0, 0x12",
    "lbu t1, WIN_COUNT",
    "lhu t0, MAIN_COLOR",
    "lhu t0, WIN_BOUNDS",
    "li t0, 2",
    "sw t0, HCOMP_BAND_RAW",
    "lhu s0, SUB_COLOR(t0)",
    "beq t1, t0, hcomp_fast1_main",
    "b hcomp_render_screen",
]
for token in required:
    assert token in src, token

print("HCOMP FAST1 backdrop-only semantic contract: PASS")
