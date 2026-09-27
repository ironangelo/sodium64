#!/usr/bin/env python3
"""Clean-lineage L0 contract for Main/Sub provenance feeding H-COMP.

Host-only.  This branch intentionally changes no Sodium64 runtime source.

The contract reconciles three already-validated pieces without importing the
historical cumulative E2/E3/E4 runtime:
  * PR #18 historical CGRAM replay + current-slot ownership;
  * the clean third fixed-slot H-COMP overlay;
  * E2g-B's semantic result that the minimum controlled BG provenance facts are
    sub_present and main_math_eligible.

The first executable successor is intentionally narrower than full production
metadata: semantic TS renders first, semantic TM renders second, independently
of MASK_SEL; the TS->TM transition temporarily loads the already-existing
H-COMP overlay as a screen-switch micro-routine, then reloads the regular
renderer.  This avoids resident-IMEM growth.  A deterministic all-opaque BG
rung can then prove real rendered Main/Sub operands with one Main BG's
CGADSUB bit disabled vs enabled before OBJ/backdrop/window/brightness semantics.

This L0 also reserves non-overlapping clean-lineage 280x8 RGB16/Z16 surfaces
for later E2g-B metadata wiring.  The old E2g-B Z addresses are explicitly
rejected because PR #18 now owns them.
"""

from __future__ import annotations

from pathlib import Path
import ast
import operator
import re

ROOT = Path(__file__).resolve().parents[1]

# Current fixed-slot ABI.
SLOT_START = 0x13A8
HCOMP_ENTRY = 0x13B0
HCOMP_SCREEN_SWITCH_ENTRY = 0x1760
MODE7_ENTRY = 0x1788
SLOT_END = 0x1790
SLOT_BYTES = SLOT_END - SLOT_START

# Current clean overlay pointer ABI.
MODE7_SRC = 0xE8C
MAIN_SRC = 0xE90
HCOMP_SRC = 0xE94
RAW_PTRS = 0xE98
EVENT_CURSOR = 0xEA0
PAIR_SCRATCH = 0xEA8
WRITE_SCRATCH = 0xEB0
VEC_DATA = 0xF70

# Audited free late-DMEM word for the first-screen RGB target command value.
# F10..F6F is the clean-lineage padding after live PR#18 scratch.
SUB_TARGET_WORD_DMEM = 0xF10
LATE_DMEM_FREE_END = VEC_DATA

# Clean-lineage RDRAM proposal.  One 280x8 RGB16/Z16 strip is 0x1180 bytes.
# Q2 ends at A00DD000; raw-palette Q1 begins at A00EF000.
STRIP_BYTES = 280 * 8 * 2
SUB_META = 0xA00DE000
MAIN_META = 0xA00E0000
SUB_COLOR = 0xA00E4000

# Sodium64's normal RGB16 framebuffer underflow maps global y=8 to physical row0.
ACTIVE_Y0 = 8
ROW_BYTES = 280 * 2
SUB_COLOR_RDP_BASE = (SUB_COLOR & 0x00FFFFFF) - ACTIVE_Y0 * ROW_BYTES

# Current clean H-COMP proof body is 44 instructions plus two 2-insn faults.
CURRENT_HCOMP_BODY_INSNS = 44
FAULT_INSNS = 4

# Proposed mid-frame switch payload lives at a fixed late slot address.  It
# patches only Color Image, sends that 8-byte command through the resident
# sender, then reloads the regular renderer through the existing generic loader.
SCREEN_SWITCH_INSNS = (
    "lw t0, FRAMEBUFFER(sp)",
    "addi t0, t0, 280 * -16",
    "sw t0, RDP_FRAME + 4",
    "li a0, RDP_FRAME",
    "jal RESIDENT_RDP_SEND",
    "li a1, RDP_FRAME + 8",
    "lw a1, OVERLAY_MAIN_SRC",
    "li t9, NEXT_LAYER",
    "j RESIDENT_OVERLAY_LOAD_SLOT",
    "nop",
)

# The resident screen-mask + first->second transition is the key zero-growth
# proof.  Current source consumes 8 + 4 = 12 instructions.  Semantic TS/TM
# packing removes MASK_SEL/shared suppression (4 instructions), while dispatch
# into the existing H-COMP overlay needs 7 at the transition.
PROPOSED_MASK_INSNS = (
    "lbu s7, TS",
    "lbu t0, TM",
    "sll t0, t0, 8",
    "or s7, s7, t0",
)
PROPOSED_TRANSITION_INSNS = (
    "srl s7, s7, 8",
    "beqz s7, next_section",
    "andi s3, s3, 0xF0",
    "lw a1, OVERLAY_HCOMP_SRC",
    f"li t9, 0x{HCOMP_SCREEN_SWITCH_ENTRY:X}",
    "b overlay_load_slot",
    "nop",
)


def instructions(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"):
            continue
        out.append(line)
    return out


def section(src: str, start: str, end: str) -> str:
    i = src.index(start)
    j = src.index(end, i)
    return src[i:j]


def parse_object_macros(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        m = re.match(r"^#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$", raw)
        if not m:
            continue
        name, expr = m.groups()
        # Ignore function-like definitions; regex above already excludes NAME(...).
        if "(" in name:
            continue
        expr = expr.split("//", 1)[0].strip()
        out[name] = expr
    return out


BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitAnd: operator.and_,
}


def resolve_macro(macros: dict[str, str], name: str, stack: tuple[str, ...] = ()) -> int:
    if name in stack:
        raise AssertionError(f"recursive macro: {' -> '.join((*stack, name))}")
    if name not in macros:
        raise AssertionError(f"missing macro {name}")

    expr = macros[name]
    tree = ast.parse(expr, mode="eval")

    def ev(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return int(node.value)
        if isinstance(node, ast.Name):
            return resolve_macro(macros, node.id, (*stack, name))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in BINOPS:
            return BINOPS[type(node.op)](ev(node.left), ev(node.right))
        raise AssertionError(f"unsupported macro expression {name}: {expr!r}")

    return ev(tree)


def ranges_overlap(a0: int, a1: int, b0: int, b1: int) -> bool:
    return max(a0, b0) < min(a1, b1)


def prove_current_runtime_anchors() -> None:
    defs = (ROOT / "src/defines.h").read_text()
    main = (ROOT / "src/rsp_main.S").read_text()
    mode7 = (ROOT / "src/rsp_mode7.S").read_text()
    hcomp = (ROOT / "src/rsp_hcomp.S").read_text()

    expected_literals = {
        "OVERLAY_MODE7_SRC": MODE7_SRC,
        "OVERLAY_MAIN_SRC": MAIN_SRC,
        "OVERLAY_HCOMP_SRC": HCOMP_SRC,
        "HCOMP_RAW_PALETTE_PTRS": RAW_PTRS,
        "HCOMP_CGRAM_EVENT_CURSOR": EVENT_CURSOR,
        "HCOMP_CGRAM_PAIR_SCRATCH": PAIR_SCRATCH,
        "HCOMP_CGRAM_WRITE_SCRATCH": WRITE_SCRATCH,
        "VEC_DATA": VEC_DATA,
    }
    macros = parse_object_macros(defs)
    for name, want in expected_literals.items():
        got = resolve_macro(macros, name)
        if got != want:
            raise AssertionError(f"{name}=0x{got:X}, expected 0x{want:X}")

    for name, src in (("main", main), ("mode7", mode7)):
        for anchor in (
            "overlay_mode7_src: .word 0",
            "overlay_main_src: .word 0",
            "overlay_hcomp_src: .word 0",
            "hcomp_raw_palette_ptrs: .word 0, 0",
            "hcomp_cgram_pair_ready:",
            "HCOMP_RAW_PALETTE_PTRS(sp)",
            "overlay_load_slot:",
        ):
            if anchor not in src:
                raise AssertionError(f"{name}: clean-lineage anchor drift {anchor!r}")

    for anchor in (
        "draw_bg:",
        "hcomp_entry:",
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "xori sp, sp, 4",
        "draw_mode7_entry:",
    ):
        if anchor not in hcomp:
            raise AssertionError(f"H-COMP anchor drift {anchor!r}")


def prove_rdram_capacity() -> None:
    defs = (ROOT / "src/defines.h").read_text()
    macros = parse_object_macros(defs)

    q1 = resolve_macro(macros, "HCOMP_CGRAM_EVENT_QUEUE1")
    q2 = resolve_macro(macros, "HCOMP_CGRAM_EVENT_QUEUE2")
    cap = resolve_macro(macros, "HCOMP_CGRAM_EVENT_CAPACITY")
    raw1 = resolve_macro(macros, "HCOMP_RAW_PALETTE_QUEUE1")
    raw2 = resolve_macro(macros, "HCOMP_RAW_PALETTE_QUEUE2")
    fb1 = resolve_macro(macros, "FRAMEBUFFER1")

    if (q1, q2, cap) != (0xA00BF000, 0xA00D7000, 0x6000):
        raise AssertionError("PR18 event arena drift")
    if raw1 != 0xA00EF000 or raw2 != 0xA00EF800 or fb1 != 0xA00F2300:
        raise AssertionError("lower framebuffer/raw-shadow map drift")

    q1r = (q1, q1 + cap)
    q2r = (q2, q2 + cap)
    rawr = (raw1, raw2 + 0x800)
    proposed = {
        "sub_meta": (SUB_META, SUB_META + STRIP_BYTES),
        "main_meta": (MAIN_META, MAIN_META + STRIP_BYTES),
        "sub_color": (SUB_COLOR, SUB_COLOR + STRIP_BYTES),
    }

    # Historical E2g-B Z surfaces are now invalid on the clean lineage.
    for old in (0xA00C0000, 0xA00C2000):
        if not ranges_overlap(old, old + STRIP_BYTES, *q1r):
            raise AssertionError("expected historical E2g-B/Q1 collision disappeared")

    # Every proposed range must fit strictly between Q2 event storage and raw Q1.
    gap_lo = q2r[1]
    gap_hi = raw1
    if gap_lo != 0xA00DD000 or gap_hi != 0xA00EF000:
        raise AssertionError("clean free-gap boundaries drift")
    for name, (lo, hi) in proposed.items():
        if not (gap_lo <= lo < hi <= gap_hi):
            raise AssertionError(f"{name} escapes clean free gap: 0x{lo:X}..0x{hi-1:X}")
        for occupied_name, occupied in (("q1", q1r), ("q2", q2r), ("raw", rawr)):
            if ranges_overlap(lo, hi, *occupied):
                raise AssertionError(f"{name} overlaps {occupied_name}")

    vals = list(proposed.items())
    for i, (an, ar) in enumerate(vals):
        for bn, br in vals[i + 1:]:
            if ranges_overlap(*ar, *br):
                raise AssertionError(f"proposed {an}/{bn} overlap")

    # Deliberate guards between authoritative/proposed ranges.
    if SUB_META - gap_lo < 0x1000:
        raise AssertionError("missing Q2->Sub metadata guard")
    if MAIN_META - proposed["sub_meta"][1] < 0x800:
        raise AssertionError("missing Sub/Main metadata guard")
    if SUB_COLOR - proposed["main_meta"][1] < 0x2000:
        raise AssertionError("missing metadata->color guard")
    if gap_hi - proposed["sub_color"][1] < 0x9000:
        raise AssertionError("missing compact-color->raw-shadow guard")

    if STRIP_BYTES != 0x1180:
        raise AssertionError(f"280x8 RGB16/Z16 strip size drift: 0x{STRIP_BYTES:X}")
    if SUB_COLOR_RDP_BASE != 0x000E2E80:
        raise AssertionError(f"compact Sub underflow drift: 0x{SUB_COLOR_RDP_BASE:X}")


def prove_semantic_screen_routing() -> None:
    src = (ROOT / "src/rsp_main.S").read_text()

    current_mask = instructions(
        section(
            src,
            "// Create a layer mask based on main and sub masks, with shared layers on top",
            "next_layer:",
        )
    )
    want_mask = [
        "lw t0, MASK_SEL(sp)",
        "lbu s7, TS(t0)",
        "xori t0, t0, 0x1",
        "lbu t0, TS(t0)",
        "and t1, t0, s7",
        "sub s7, s7, t1",
        "sll t0, t0, 8",
        "or s7, s7, t0",
    ]
    if current_mask != want_mask:
        raise AssertionError(f"current screen-mask footprint drift: {current_mask}")

    current_transition = instructions(
        section(
            src,
            "// Move to the next screen's layers until the section is finished",
            "// Fixed renderer overlay begins",
        )
    )
    want_transition = [
        "srl s7, s7, 8",
        "beqz s7, next_section",
        "andi s3, s3, 0xF0",
        "b next_layer",
    ]
    if current_transition != want_transition:
        raise AssertionError(f"current screen transition drift: {current_transition}")

    old_total = len(current_mask) + len(current_transition)
    new_total = len(PROPOSED_MASK_INSNS) + len(PROPOSED_TRANSITION_INSNS)
    if (old_total, new_total) != (12, 11):
        raise AssertionError(f"resident footprint arithmetic drift: {old_total}->{new_total}")

    # Exhaust screen-enable packing.  Proposed routing is semantic TS low byte,
    # TM high byte and therefore independent of the UI/manual MASK_SEL setting.
    for ts in range(0x20):
        for tm in range(0x20):
            packed = ts | (tm << 8)
            for mask_sel in (0, 1):
                proposed = ts | (tm << 8)
                if proposed != packed:
                    raise AssertionError((ts, tm, mask_sel))
            # Shared membership must survive in both bytes.
            shared = ts & tm
            if (packed & shared) != shared or ((packed >> 8) & shared) != shared:
                raise AssertionError(f"shared layer lost ts={ts:#x} tm={tm:#x}")

    # Pin why the historical workaround cannot remain production authority.
    ts = tm = 0x01
    historical_low = ts - (ts & tm)  # MASK_SEL=0 first traversal
    historical_high = tm
    if historical_low != 0 or historical_high != 1:
        raise AssertionError("historical shared-suppression discriminator drift")


def prove_overlay_capacity_and_lifetime() -> None:
    h = (ROOT / "src/rsp_hcomp.S").read_text()

    body = instructions(section(h, "hcomp_entry:", "// Keep the externally visible Mode7 entry"))
    if len(body) != CURRENT_HCOMP_BODY_INSNS:
        raise AssertionError(f"current H-COMP body drift: {len(body)} != {CURRENT_HCOMP_BODY_INSNS}")

    current_active = (CURRENT_HCOMP_BODY_INSNS + FAULT_INSNS) * 4
    switch_bytes = len(SCREEN_SWITCH_INSNS) * 4
    proposed_active = current_active + switch_bytes

    if (current_active, switch_bytes, proposed_active) != (192, 40, 232):
        raise AssertionError(
            f"H-COMP capacity arithmetic drift: {current_active}/{switch_bytes}/{proposed_active}"
        )
    if proposed_active > SLOT_BYTES:
        raise AssertionError("screen-switch helper no longer fits H-COMP fixed slot")

    body_end = HCOMP_ENTRY + CURRENT_HCOMP_BODY_INSNS * 4
    if not (body_end <= HCOMP_SCREEN_SWITCH_ENTRY < HCOMP_SCREEN_SWITCH_ENTRY + switch_bytes <= MODE7_ENTRY):
        raise AssertionError(
            f"fixed switch placement collision body_end=0x{body_end:X}"
        )

    # The screen switch uses the already-published H-COMP source and generic
    # loader; no fourth overlay source pointer or resident loader is required.
    if HCOMP_SRC + 4 != RAW_PTRS:
        raise AssertionError("clean pointer packing drift")
    if "overlay_load_slot:" not in (ROOT / "src/rsp_main.S").read_text():
        raise AssertionError("generic fixed-slot loader disappeared")

    # Late DMEM can hold a compact first-screen target word without touching
    # PR #18 scratch or VEC_DATA. Reserve only 4 B in this first contract.
    if not (WRITE_SCRATCH + 8 <= SUB_TARGET_WORD_DMEM < SUB_TARGET_WORD_DMEM + 4 <= LATE_DMEM_FREE_END):
        raise AssertionError("late-DMEM target word overlaps live state")
    if LATE_DMEM_FREE_END - SUB_TARGET_WORD_DMEM != 0x60:
        raise AssertionError("F10..F6F padding size drift")


def prove_first_discriminator_semantics() -> None:
    # First executable rung deliberately avoids OBJ/backdrop/window/brightness:
    # one opaque Main BG and one opaque Sub BG.  Therefore sub_present is true,
    # while Main eligibility is exactly that BG's CGADSUB bit.
    main_bg_index = 0  # BG1
    sub_present = True
    seen = set()
    for cgadsub in range(256):
        eligible = bool(cgadsub & (1 << main_bg_index))
        seen.add((eligible, sub_present))
    if seen != {(False, True), (True, True)}:
        raise AssertionError(f"first discriminator cannot exercise both Main eligibility states: {seen}")

    # Explicitly pin two frame-level states for the future dynamic guest.
    if bool(0x00 & 0x01):
        raise AssertionError("disabled control drift")
    if not bool(0x01 & 0x01):
        raise AssertionError("enabled control drift")


def main() -> int:
    prove_current_runtime_anchors()
    prove_rdram_capacity()
    prove_semantic_screen_routing()
    prove_overlay_capacity_and_lifetime()
    prove_first_discriminator_semantics()

    print("HCOMP_MAIN_SUB_CLEAN_L0_VALIDATED")
    print("runtime_delta=0")
    print("parent=validated_clean_CGRAM_to_HCOMP_dynamic_authority")
    print("semantic_screen_order=TS_then_TM")
    print("manual_MASK_SEL_dependency=REMOVED_IN_PROPOSAL")
    print("shared_layers=preserved_in_both_screen_masks")
    print("resident_screen_routing_instructions=current12 proposed11")
    print(f"hcomp_screen_switch_entry=0x{HCOMP_SCREEN_SWITCH_ENTRY:04X}")
    print("hcomp_current_active_bytes=192")
    print("hcomp_switch_helper_bytes=40")
    print("hcomp_proposed_active_bytes=232")
    print("fixed_slot_bytes=1000")
    print(f"sub_meta=0x{SUB_META:08X} size=0x{STRIP_BYTES:X}")
    print(f"main_meta=0x{MAIN_META:08X} size=0x{STRIP_BYTES:X}")
    print(f"sub_color=0x{SUB_COLOR:08X} size=0x{STRIP_BYTES:X}")
    print(f"sub_color_rdp_base=0x{SUB_COLOR_RDP_BASE:08X}")
    print("historical_e2g_z_addresses=REJECTED_COLLISION_WITH_PR18_Q1")
    print("first_dynamic_rung=opaque_BG_Main_math_disabled_vs_enabled")
    print("metadata_runtime_wiring=DEFERRED_AFTER_FIRST_DUAL_COLOR_PROOF")
    print("obj_backdrop_windows_brightness=NOT_PROVEN")
    print("throughput_cadence_hardware=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
