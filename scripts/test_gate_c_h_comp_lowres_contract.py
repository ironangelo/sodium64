#!/usr/bin/env python3
"""Exhaustive L0 proof for the low-res H-COMP post-winner metadata contract.

Scope:
- standard low-res output only (no hires/pseudo-hires);
- raw Main/Sub winner colors are assumed to have already been selected;
- direct-color generation and winner selection are outside this proof;
- section state keeps CGADSUB/C GWSEL-derived arithmetic mode and fixed color.

Reference semantics are transcribed from pinned ares
17813a3ccda21ab9bd45f09bfc2f91196dbf50ff:
  ares/sfc/ppu-performance/dac.cpp::PPU::DAC::pixel()
  ares/sfc/ppu-performance/io.cpp::CGADDSUB
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

ARES_PIN = "17813a3ccda21ab9bd45f09bfc2f91196dbf50ff"


class Source(IntEnum):
    BG1 = 0
    BG2 = 1
    BG3 = 2
    BG4 = 3
    OBJ1 = 4  # OBJ palette < 192: never color-math eligible
    OBJ2 = 5  # OBJ palette >= 192: controlled by CGADSUB bit 4
    COL = 6   # backdrop/COL: controlled by CGADSUB bit 5


class Operand(IntEnum):
    NONE = 0
    FIXED = 1
    SUB = 2


class Action(IntEnum):
    CLIP_NO_MATH = 0
    PASS_NO_MATH = 1
    CLIP_FIXED = 2
    PASS_FIXED_HALFABLE = 3
    PASS_FIXED_NOHALF = 4
    CLIP_SUB = 5
    PASS_SUB_HALFABLE = 6


@dataclass(frozen=True)
class Decision:
    main_visible: bool
    operand: Operand
    halve: bool


def ares_color_enabled(source: Source, cgadsub: int) -> bool:
    """Exact CGADSUB source eligibility used by pinned ares performance PPU."""
    if source == Source.BG1:
        return bool(cgadsub & 0x01)
    if source == Source.BG2:
        return bool(cgadsub & 0x02)
    if source == Source.BG3:
        return bool(cgadsub & 0x04)
    if source == Source.BG4:
        return bool(cgadsub & 0x08)
    if source == Source.OBJ1:
        return False
    if source == Source.OBJ2:
        return bool(cgadsub & 0x10)
    if source == Source.COL:
        return bool(cgadsub & 0x20)
    raise AssertionError(source)


def ares_reference_decision(
    *,
    source: Source,
    cgadsub: int,
    window_above: bool,
    window_below: bool,
    blend_mode: bool,
    below_is_col: bool,
) -> Decision:
    """Symbolic form of pinned ares DAC::pixel() for standard low-res.

    In non-hires prepare(), a COL below pixel carries fixedColor(). Therefore
    blend-mode + below COL and fixed-color mode select the same color operand,
    but differ in whether halving is allowed.
    """
    main_visible = window_above

    if not window_below:
        return Decision(main_visible, Operand.NONE, False)

    if not ares_color_enabled(source, cgadsub):
        return Decision(main_visible, Operand.NONE, False)

    halve_requested = bool(cgadsub & 0x40)

    if not blend_mode:
        return Decision(
            main_visible,
            Operand.FIXED,
            halve_requested and window_above,
        )

    if below_is_col:
        # Pinned ares suppresses half when subscreen mode resolves to COL.
        return Decision(main_visible, Operand.FIXED, False)

    return Decision(
        main_visible,
        Operand.SUB,
        halve_requested and window_above,
    )


def encode_action(
    *,
    source: Source,
    cgadsub: int,
    window_above: bool,
    window_below: bool,
    blend_mode: bool,
    below_is_col: bool,
) -> Action:
    """Production-oriented compact classifier.

    The 3-bit value captures only per-pixel information. ADD/SUB, the requested
    HALF bit, and fixedColor remain section state; raw Main/Sub remain separate
    color surfaces.
    """
    math_enabled = window_below and ares_color_enabled(source, cgadsub)

    if not math_enabled:
        return Action.PASS_NO_MATH if window_above else Action.CLIP_NO_MATH

    if blend_mode and not below_is_col:
        return Action.PASS_SUB_HALFABLE if window_above else Action.CLIP_SUB

    if not window_above:
        return Action.CLIP_FIXED

    if blend_mode and below_is_col:
        return Action.PASS_FIXED_NOHALF

    return Action.PASS_FIXED_HALFABLE


def encode_action_from_factors(
    *,
    main_math_eligible: bool,
    sub_present: bool,
    window_above: bool,
    window_below: bool,
    blend_mode: bool,
) -> Action:
    """Same compact action using only the two renderer-produced pixel facts."""
    math_enabled = window_below and main_math_eligible

    if not math_enabled:
        return Action.PASS_NO_MATH if window_above else Action.CLIP_NO_MATH

    if blend_mode and sub_present:
        return Action.PASS_SUB_HALFABLE if window_above else Action.CLIP_SUB

    if not window_above:
        return Action.CLIP_FIXED

    if blend_mode and not sub_present:
        return Action.PASS_FIXED_NOHALF

    return Action.PASS_FIXED_HALFABLE


def decode_action(action: Action, *, halve_requested: bool) -> Decision:
    if action == Action.CLIP_NO_MATH:
        return Decision(False, Operand.NONE, False)
    if action == Action.PASS_NO_MATH:
        return Decision(True, Operand.NONE, False)
    if action == Action.CLIP_FIXED:
        return Decision(False, Operand.FIXED, False)
    if action == Action.PASS_FIXED_HALFABLE:
        return Decision(True, Operand.FIXED, halve_requested)
    if action == Action.PASS_FIXED_NOHALF:
        return Decision(True, Operand.FIXED, False)
    if action == Action.CLIP_SUB:
        return Decision(False, Operand.SUB, False)
    if action == Action.PASS_SUB_HALFABLE:
        return Decision(True, Operand.SUB, halve_requested)
    raise AssertionError(action)


def prove_exhaustive_equivalence() -> tuple[int, dict[Action, int]]:
    checked = 0
    uses = {action: 0 for action in Action}

    for source in Source:
        for cgadsub in range(256):
            for window_above in (False, True):
                for window_below in (False, True):
                    for blend_mode in (False, True):
                        for below_is_col in (False, True):
                            ref = ares_reference_decision(
                                source=source,
                                cgadsub=cgadsub,
                                window_above=window_above,
                                window_below=window_below,
                                blend_mode=blend_mode,
                                below_is_col=below_is_col,
                            )
                            action = encode_action(
                                source=source,
                                cgadsub=cgadsub,
                                window_above=window_above,
                                window_below=window_below,
                                blend_mode=blend_mode,
                                below_is_col=below_is_col,
                            )
                            factor_action = encode_action_from_factors(
                                main_math_eligible=ares_color_enabled(source, cgadsub),
                                sub_present=not below_is_col,
                                window_above=window_above,
                                window_below=window_below,
                                blend_mode=blend_mode,
                            )
                            if factor_action != action:
                                raise AssertionError(
                                    "factorized producer contract mismatch: "
                                    f"source={source.name} cgadsub=0x{cgadsub:02X} "
                                    f"window_above={window_above} "
                                    f"window_below={window_below} "
                                    f"blend_mode={blend_mode} "
                                    f"below_is_col={below_is_col} "
                                    f"source_action={action.name} "
                                    f"factor_action={factor_action.name}"
                                )
                            got = decode_action(
                                factor_action,
                                halve_requested=bool(cgadsub & 0x40),
                            )
                            if got != ref:
                                raise AssertionError(
                                    "contract mismatch: "
                                    f"source={source.name} cgadsub=0x{cgadsub:02X} "
                                    f"window_above={window_above} "
                                    f"window_below={window_below} "
                                    f"blend_mode={blend_mode} "
                                    f"below_is_col={below_is_col} "
                                    f"action={action.name} ref={ref} got={got}"
                                )
                            uses[action] += 1
                            checked += 1

    return checked, uses


def prove_three_bits_are_necessary_and_sufficient() -> None:
    # Each Action must represent a unique observable behavior over both values
    # of the section-level HALF request. If seven unique signatures are live,
    # fewer than 3 bits cannot encode the contract.
    signatures: dict[Action, tuple[Decision, Decision]] = {
        action: (
            decode_action(action, halve_requested=False),
            decode_action(action, halve_requested=True),
        )
        for action in Action
    }

    unique = set(signatures.values())
    if len(unique) != len(Action):
        raise AssertionError(f"action aliases detected: {signatures}")

    required_bits = (len(unique) - 1).bit_length()
    if required_bits != 3:
        raise AssertionError(
            f"expected seven distinct behaviors to require 3 bits, got {required_bits}"
        )

    if max(int(action) for action in Action) >= (1 << required_bits):
        raise AssertionError("3-bit encoding does not contain all actions")


def prove_adversarial_edges() -> None:
    # OBJ1 is never color-math eligible even when OBJ's CGADSUB bit is set.
    for cgadsub in range(256):
        if ares_color_enabled(Source.OBJ1, cgadsub):
            raise AssertionError(f"OBJ1 unexpectedly eligible: 0x{cgadsub:02X}")

    # OBJ2 follows bit 4 exactly; COL follows bit 5 exactly.
    for cgadsub in range(256):
        if ares_color_enabled(Source.OBJ2, cgadsub) != bool(cgadsub & 0x10):
            raise AssertionError(f"OBJ2 mapping mismatch: 0x{cgadsub:02X}")
        if ares_color_enabled(Source.COL, cgadsub) != bool(cgadsub & 0x20):
            raise AssertionError(f"COL mapping mismatch: 0x{cgadsub:02X}")

    # With visible eligible Main and HALF requested, fixed-color mode may halve.
    fixed = ares_reference_decision(
        source=Source.BG1,
        cgadsub=0x41,
        window_above=True,
        window_below=True,
        blend_mode=False,
        below_is_col=True,
    )
    if fixed != Decision(True, Operand.FIXED, True):
        raise AssertionError(f"fixed-color HALF edge mismatch: {fixed}")

    # In subscreen mode, a COL/fixed fallback suppresses HALF.
    empty_sub = ares_reference_decision(
        source=Source.BG1,
        cgadsub=0x41,
        window_above=True,
        window_below=True,
        blend_mode=True,
        below_is_col=True,
    )
    if empty_sub != Decision(True, Operand.FIXED, False):
        raise AssertionError(f"COL fallback HALF suppression mismatch: {empty_sub}")

    # A real subscreen winner restores HALF eligibility.
    real_sub = ares_reference_decision(
        source=Source.BG1,
        cgadsub=0x41,
        window_above=True,
        window_below=True,
        blend_mode=True,
        below_is_col=False,
    )
    if real_sub != Decision(True, Operand.SUB, True):
        raise AssertionError(f"real-sub HALF edge mismatch: {real_sub}")


def main() -> int:
    prove_adversarial_edges()
    checked, uses = prove_exhaustive_equivalence()
    prove_three_bits_are_necessary_and_sufficient()

    print("HCOMP_LOWRES_CONTRACT_VALIDATED")
    print(f"ares_pin={ARES_PIN}")
    print(f"cases={checked}")
    print(f"actions={len(Action)} required_bits=3")
    print("producer_pixel_facts=main_math_eligible,sub_present")
    print("section_facts=window_above,window_below,blend_mode,halve_requested")
    for action in Action:
        print(f"{action.value}:{action.name} uses={uses[action]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
