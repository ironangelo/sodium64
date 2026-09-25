#!/usr/bin/env python3
"""L0 contract for a production-capable third H-COMP renderer-slot overlay.

Host-only: proves a zero-resident-growth dispatch architecture before any
runtime source is changed.
"""

from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

SLOT_START = 0x13A8
HCOMP_ENTRY = 0x13B0
MODE7_ENTRY = 0x1788
SLOT_END = 0x1790
SLOT_BYTES = SLOT_END - SLOT_START

# Proposed DMEM ABI. E8C..E8F is explicitly free in current defines/comments.
MODE7_SRC_NEW = 0xE8C
MAIN_SRC = 0xE90
HCOMP_SRC = 0xE94
RAW_PTRS = 0xE98

# Hardware-validated E4d resident body measured earlier; this is a capacity
# anchor only, not a claim that a complete production compositor is 368 B.
E4D_KERNEL_BYTES = 368
HCOMP_START_FAULT_BYTES = 8
HCOMP_HALT_BYTES = 16
HCOMP_MODE7_FAULT_BYTES = 8


def instructions(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"):
            continue
        out.append(line)
    return out


def extract(src: str, start: str, end: str) -> str:
    i = src.index(start)
    j = src.index(end, i)
    return src[i:j]


def define_literal(src: str, name: str) -> int:
    m = re.search(rf"^#define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\s*$", src, re.M)
    if not m:
        raise AssertionError(f"missing literal {name}")
    return int(m.group(1), 16)


def prove_current_abi() -> None:
    defs = (ROOT / "src/defines.h").read_text()
    if define_literal(defs, "OVERLAY_MAIN_SRC") != MAIN_SRC:
        raise AssertionError("main overlay ABI drift")
    if define_literal(defs, "OVERLAY_MODE7_SRC") != HCOMP_SRC:
        raise AssertionError("current Mode7 pointer not at expected E94 baseline")
    if define_literal(defs, "HCOMP_RAW_PALETTE_PTRS") != RAW_PTRS:
        raise AssertionError("raw palette ABI drift")
    for anchor in (
        "E8B..E8F stay free before overlay ABI",
        "#define WIN_COUNT (WIN_BOUNDS + 0x6)",
    ):
        if anchor not in defs:
            raise AssertionError(f"free-gap contract drift: {anchor}")

    if not (MODE7_SRC_NEW + 4 == MAIN_SRC == HCOMP_SRC - 4 == RAW_PTRS - 8):
        raise AssertionError("proposed pointer packing is not contiguous/aligned")


def prove_zero_growth_dispatch() -> None:
    for name in ("rsp_main.S", "rsp_mode7.S"):
        src = (ROOT / "src" / name).read_text()

        next_frame = extract(src, "next_frame:", "\n\nclear_cache:")
        old_nf = instructions(next_frame)
        if len(old_nf) != 4:
            raise AssertionError(f"{name}: next_frame baseline not 4 instructions: {old_nf}")

        loader = extract(src, "overlay_load_mode7:", "\noverlay_load_main:")
        old_loader = instructions(loader)
        if len(old_loader) != 6:
            raise AssertionError(f"{name}: Mode7 loader baseline not 6 instructions: {old_loader}")
        if old_loader != [
            "lw a1, OVERLAY_MODE7_SRC",
            "li a0, 0x13A8",
            "jal dma_read",
            "li a2, 0x3E7",
            "b draw_mode7_entry",
            "nop",
        ]:
            raise AssertionError(f"{name}: Mode7 loader shape drift")

    main = (ROOT / "src/rsp_main.S").read_text()
    fault = extract(main, "draw_mode7_entry:", "\n\ndraw_obj:")
    if instructions(fault) != ["b overlay_load_mode7", "nop"]:
        raise AssertionError("regular Mode7 fault stub no longer exactly two instructions")

    # Proposed sequences have exactly the same resident instruction footprints.
    proposed_next_frame = [
        "lw a1, OVERLAY_HCOMP_SRC(sp)",
        f"li t9, 0x{HCOMP_ENTRY:X}",
        "b overlay_load_slot",
        "xori sp, sp, 4",
    ]
    proposed_loader = [
        "lw a1, OVERLAY_MODE7_SRC(sp)",
        # overlay_load_slot: label only
        "li a0, 0x13A8",
        "jal dma_read",
        "li a2, 0x3E7",
        "jr t9",
        "nop",
    ]
    proposed_fault = ["b overlay_load_mode7", f"li t9, 0x{MODE7_ENTRY:X}"]
    if len(proposed_next_frame) != 4 or len(proposed_loader) != 6 or len(proposed_fault) != 2:
        raise AssertionError("zero-growth dispatch arithmetic broken")


def prove_build_path() -> None:
    make = (ROOT / "Makefile").read_text()
    anchors = (
        "SFILES := $(foreach dir,$(SRC_DIRS),$(wildcard $(dir)/*.S))",
        'if case "$$FILENAME" in "rsp"*) true;; *) false;; esac; then',
        "$(N64_OBJCOPY) -O binary -j .text",
    )
    for anchor in anchors:
        if anchor not in make:
            raise AssertionError(f"RSP third-payload build path drift: {anchor!r}")


def prove_slot_capacity() -> None:
    fixed = (
        HCOMP_START_FAULT_BYTES
        + E4D_KERNEL_BYTES
        + HCOMP_HALT_BYTES
        + HCOMP_MODE7_FAULT_BYTES
    )
    if SLOT_BYTES != 1000:
        raise AssertionError(f"fixed renderer slot drift: {SLOT_BYTES}")
    if HCOMP_ENTRY != SLOT_START + HCOMP_START_FAULT_BYTES:
        raise AssertionError("H-COMP entry not immediately after regular fault stub")
    if fixed != 400:
        raise AssertionError(f"fixed H-COMP infrastructure drift: {fixed}")
    if SLOT_BYTES - fixed != 600:
        raise AssertionError("expected 600 B routing/headroom not preserved")


def transition(current: str, wanted: str) -> tuple[str, str]:
    if wanted == "regular":
        return ("regular", "none" if current == "regular" else "load_main")
    if wanted == "mode7":
        return ("mode7", "none" if current == "mode7" else "load_mode7")
    raise ValueError(wanted)


def prove_state_machine() -> None:
    # Start a frame with any slot left resident, including H-COMP from the prior
    # frame, then exhaust renderer-switch sequences and require frame-end H-COMP.
    sequences = (
        ("regular",),
        ("mode7",),
        ("regular", "mode7", "regular"),
        ("mode7", "regular", "mode7"),
        ("regular", "regular", "mode7"),
    )
    for start in ("regular", "mode7", "hcomp"):
        for seq in sequences:
            cur = start
            for wanted in seq:
                cur, action = transition(cur, wanted)
                if cur != wanted:
                    raise AssertionError((start, seq, wanted, action))
            # next_frame always loads H-COMP through the generic slot loader.
            cur = "hcomp"
            # H-COMP halts while remaining resident. The following frame must
            # fault cleanly to either renderer.
            for first in ("regular", "mode7"):
                nxt, action = transition(cur, first)
                if nxt != first or action not in ("load_main", "load_mode7"):
                    raise AssertionError((seq, first, nxt, action))


def prove_cpu_publication_shape() -> None:
    main = (ROOT / "src/main.S").read_text()
    for anchor in (
        "rsp_main_text_start",
        "rsp_mode7_text_start",
        "sw t0, DMEM(OVERLAY_MAIN_SRC)",
        "sw t0, DMEM(OVERLAY_MODE7_SRC)",
    ):
        if anchor not in main:
            raise AssertionError(f"CPU overlay publication drift: {anchor}")


def main() -> int:
    prove_current_abi()
    prove_zero_growth_dispatch()
    prove_build_path()
    prove_slot_capacity()
    prove_state_machine()
    prove_cpu_publication_shape()
    print("HCOMP_THIRD_OVERLAY_L0_VALIDATED")
    print("resident_imem_growth=0")
    print("mode7_ptr_proposed=E8C")
    print("main_ptr=E90")
    print("hcomp_ptr_proposed=E94")
    print("raw_ptrs=E98/E9C")
    print("slot_bytes=1000")
    print("validated_kernel_anchor_bytes=368")
    print("fixed_hcomp_infrastructure_bytes=400")
    print("uncommitted_routing_headroom_bytes=600")
    print("mode7_loader_instructions=6_to_6")
    print("next_frame_instructions=4_to_4")
    print("regular_mode7_fault_instructions=2_to_2")
    print("production_completeness=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
