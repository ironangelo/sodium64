#!/usr/bin/env python3
"""Clean-lineage L0 contract for a zero-resident-growth third H-COMP overlay.

Host-only: no Sodium64 runtime source changes. Re-proves the historically
validated placement/dispatch shape against current master after PR #18.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

SLOT_START = 0x13A8
HCOMP_ENTRY = 0x13B0
MODE7_ENTRY = 0x1788
SLOT_END = 0x1790
SLOT_BYTES = SLOT_END - SLOT_START

MODE7_SRC_NEW = 0xE8C
MAIN_SRC = 0xE90
HCOMP_SRC = 0xE94
RAW_PTRS = 0xE98
EVENT_CURSOR = 0xEA0
PAIR_SCRATCH = 0xEA8
WRITE_SCRATCH = 0xEB0
VEC_DATA = 0xF70

# Historical hardware-validated arithmetic body: capacity anchor only.
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


def prove_current_dmem_abi() -> None:
    defs = (ROOT / "src/defines.h").read_text()
    expected = {
        "OVERLAY_MAIN_SRC": MAIN_SRC,
        "OVERLAY_MODE7_SRC": HCOMP_SRC,
        "HCOMP_RAW_PALETTE_PTRS": RAW_PTRS,
        "HCOMP_CGRAM_EVENT_CURSOR": EVENT_CURSOR,
        "HCOMP_CGRAM_PAIR_SCRATCH": PAIR_SCRATCH,
        "HCOMP_CGRAM_WRITE_SCRATCH": WRITE_SCRATCH,
        "VEC_DATA": VEC_DATA,
    }
    for name, value in expected.items():
        got = define_literal(defs, name)
        if got != value:
            raise AssertionError(f"{name} drift: 0x{got:X} != 0x{value:X}")

    if "E8B..E8F stay free before overlay ABI" not in defs:
        raise AssertionError("audited pre-overlay free-gap contract disappeared")

    # Proposed packing consumes only the already-audited E8C word and the
    # current Mode7 word at E94, leaving PR#18 raw/cursor/scratch ABI intact.
    if not (
        MODE7_SRC_NEW + 4 == MAIN_SRC
        and MAIN_SRC + 4 == HCOMP_SRC
        and HCOMP_SRC + 4 == RAW_PTRS
        and RAW_PTRS + 8 == EVENT_CURSOR
        and EVENT_CURSOR < PAIR_SCRATCH < WRITE_SCRATCH < VEC_DATA
    ):
        raise AssertionError("proposed pointer packing overlaps PR#18 consumer state")
    for addr in (MODE7_SRC_NEW, MAIN_SRC, HCOMP_SRC, RAW_PTRS, EVENT_CURSOR, PAIR_SCRATCH, WRITE_SCRATCH):
        if addr & 3:
            raise AssertionError(f"unaligned DMEM state 0x{addr:X}")
    if PAIR_SCRATCH & 7 or WRITE_SCRATCH & 7:
        raise AssertionError("PR#18 DMA scratch lost 8-byte alignment")


def prove_current_dispatch_footprints() -> None:
    for name in ("rsp_main.S", "rsp_mode7.S"):
        src = (ROOT / "src" / name).read_text()
        nf = instructions(extract(src, "next_frame:", "\n\nclear_cache:"))
        if len(nf) != 4:
            raise AssertionError(f"{name}: next_frame is no longer 4 instructions: {nf}")

        loader = instructions(extract(src, "overlay_load_mode7:", "\noverlay_load_main:"))
        want = [
            "lw a1, OVERLAY_MODE7_SRC",
            "li a0, 0x13A8",
            "jal dma_read",
            "li a2, 0x3E7",
            "b draw_mode7_entry",
            "nop",
        ]
        if loader != want:
            raise AssertionError(f"{name}: Mode7 loader shape drift: {loader}")

    main = (ROOT / "src/rsp_main.S").read_text()
    fault = instructions(extract(main, "draw_mode7_entry:", "\n\ndraw_obj:"))
    if fault != ["b overlay_load_mode7", "nop"]:
        raise AssertionError(f"regular Mode7 fault stub drift: {fault}")

    proposed_next_frame = [
        "lw a1, OVERLAY_HCOMP_SRC",
        f"li t9, 0x{HCOMP_ENTRY:X}",
        "b overlay_load_slot",
        "xori sp, sp, 4",
    ]
    proposed_loader = [
        "lw a1, OVERLAY_MODE7_SRC",
        "li a0, 0x13A8",
        "jal dma_read",
        "li a2, 0x3E7",
        "jr t9",
        "nop",
    ]
    proposed_fault = ["b overlay_load_mode7", f"li t9, 0x{MODE7_ENTRY:X}"]
    if (len(proposed_next_frame), len(proposed_loader), len(proposed_fault)) != (4, 6, 2):
        raise AssertionError("zero-growth dispatch instruction arithmetic failed")


def prove_slot_capacity() -> None:
    if SLOT_BYTES != 1000:
        raise AssertionError(f"renderer slot drift: {SLOT_BYTES}")
    if HCOMP_ENTRY != SLOT_START + HCOMP_START_FAULT_BYTES:
        raise AssertionError("H-COMP entry must follow the 2-instruction regular fault stub")
    fixed = HCOMP_START_FAULT_BYTES + E4D_KERNEL_BYTES + HCOMP_HALT_BYTES + HCOMP_MODE7_FAULT_BYTES
    if fixed != 400 or SLOT_BYTES - fixed != 600:
        raise AssertionError(f"historical capacity anchor drift: fixed={fixed} free={SLOT_BYTES-fixed}")


def transition(current: str, wanted: str) -> tuple[str, str]:
    if wanted == "regular":
        return ("regular", "none" if current == "regular" else "load_main")
    if wanted == "mode7":
        return ("mode7", "none" if current == "mode7" else "load_mode7")
    raise ValueError(wanted)


def prove_state_machine() -> None:
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
                cur, _ = transition(cur, wanted)
                if cur != wanted:
                    raise AssertionError((start, seq, wanted))
            cur = "hcomp"  # frame-end loads H-COMP; it halts resident.
            for first in ("regular", "mode7"):
                nxt, action = transition(cur, first)
                if nxt != first or action not in ("load_main", "load_mode7"):
                    raise AssertionError((start, seq, first, nxt, action))


def prove_cpu_and_build_paths() -> None:
    main = (ROOT / "src/main.S").read_text()
    for anchor in (
        "rsp_main_text_start",
        "rsp_mode7_text_start",
        "sw t0, DMEM(OVERLAY_MAIN_SRC)",
        "sw t0, DMEM(OVERLAY_MODE7_SRC)",
        "sw t0, DMEM(HCOMP_RAW_PALETTE_PTRS)",
        "sw t0, DMEM(HCOMP_RAW_PALETTE_PTRS + 4)",
    ):
        if anchor not in main:
            raise AssertionError(f"CPU publication anchor drift: {anchor}")

    make = (ROOT / "Makefile").read_text()
    for anchor in (
        "SFILES := $(foreach dir,$(SRC_DIRS),$(wildcard $(dir)/*.S))",
        'if case "$$FILENAME" in "rsp"*) true;; *) false;; esac; then',
        "$(N64_OBJCOPY) -O binary -j .text",
    ):
        if anchor not in make:
            raise AssertionError(f"third RSP payload build path drift: {anchor!r}")


def main() -> int:
    prove_current_dmem_abi()
    prove_current_dispatch_footprints()
    prove_slot_capacity()
    prove_state_machine()
    prove_cpu_and_build_paths()
    print("HCOMP_THIRD_OVERLAY_CLEAN_L0_VALIDATED")
    print("runtime_delta=0")
    print("resident_imem_growth_proposed=0")
    print("mode7_ptr_proposed=E8C")
    print("main_ptr=E90")
    print("hcomp_ptr_proposed=E94")
    print("raw_ptrs=E98/E9C")
    print("event_cursor=EA0 pair_scratch=EA8 write_scratch=EB0 vec_data=F70")
    print("slot_bytes=1000")
    print("historical_kernel_capacity_anchor_bytes=368")
    print("fixed_hcomp_infrastructure_bytes=400")
    print("uncommitted_routing_headroom_bytes=600")
    print("mode7_loader_instructions=6_to_6")
    print("next_frame_instructions=4_to_4")
    print("regular_mode7_fault_instructions=2_to_2")
    print("production_completeness=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
