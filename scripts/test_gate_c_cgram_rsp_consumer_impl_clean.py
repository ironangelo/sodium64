#!/usr/bin/env python3
"""Implementation oracle for the 29-instruction DMA8 CGRAM RSP consumer."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_cgram_rsp_consumer_clean_contract as l0

EXPECTED_TEXT_BYTES = 0x1000
FIXED_SLOT_START = 0xA40013A8
FIXED_SLOT_END_NEXT = 0xA4001790


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i)
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def instruction_count(block: str) -> int:
    count = 0
    for raw in block.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.endswith(":") or line.startswith("."):
            continue
        count += 1
    return count


def prove_model() -> None:
    l0.prove_rgb_mapping()
    l0.prove_record_encoding()
    if l0.prove_transform_equivalence() != 42545:
        raise AssertionError("clean typed replay authority drift")
    typed_records = l0.MAX_COLOR_RECORDS + l0.MAX_SECTION_MARKERS
    if typed_records != 20780:
        raise AssertionError("typed record bound drift")
    if 24576 - typed_records != 3796:
        raise AssertionError("DMA8 capacity margin drift")
    if l0.RAW_Q1 & 7 or l0.RAW_Q2 & 7:
        raise AssertionError("raw shadow lost 8-byte alignment")


def prove_defines() -> None:
    text = (ROOT / "src/defines.h").read_text()
    expected = {
        "HCOMP_CGRAM_EVENT_CURSOR": 0xEA0,
        "HCOMP_CGRAM_PAIR_SCRATCH": 0xEA8,
        "HCOMP_CGRAM_WRITE_SCRATCH": 0xEB0,
        "HCOMP_RAW_PALETTE_PTRS": 0xE98,
        "VEC_DATA": 0xF70,
    }
    for name, value in expected.items():
        m = re.search(rf"^#define\s+{name}\s+(0x[0-9A-Fa-f]+)\s*$", text, re.M)
        if not m or int(m.group(1), 16) != value:
            raise AssertionError(f"{name} definition drift")
    if not (0xE98 < 0xEA0 < 0xEA8 < 0xEB0 < 0xEB8 <= 0xF70):
        raise AssertionError("consumer state escapes retired DMEM interval")


def prove_inherited_typed_producer() -> None:
    ppu = (ROOT / "src/ppu.S").read_text()

    begin = extract(ppu, "hcomp_cgram_begin_frame:", ".align 5\nupdate_frame:")
    for required in (
        "lw t5, hcomp_raw_pal_queues(t0)",
        "sh zero, hcomp_cgram_event_count",
        "sb zero, hcomp_cgram_event_overflow",
        "sw t6, 0(t5)",
        "sw t6, 4(t5)",
    ):
        if required not in begin:
            raise AssertionError(f"inherited typed producer base/raw init drift: {required!r}")

    section = extract(ppu, "section_init:", ".align 5\nhcomp_cgram_begin_frame:")
    marker = extract(section, "// Append one typed section marker", "hcomp_cgram_marker_overflow:")
    if "t4" in marker:
        raise AssertionError("inherited typed producer reintroduced rsp_frame t4 clobber")
    for required in (
        "andi t1, t2, 0x3E0",
        "sll t1, t1, 1",
        "or t3, t3, t1",
        "andi t1, t2, 0x7C00",
        "srl t1, t1, 9",
        "ori t3, t3, 0x8000",
    ):
        if required not in marker:
            raise AssertionError(f"inherited t1-safe marker drift: {required!r}")

    cg = extract(ppu, "write_cgdata:", ".align 5\nwrite_w12sel:")
    for required in (
        "li t3, HCOMP_CGRAM_EVENT_CAPACITY",
        "bge t2, t3, cg_epoch_overflow",
        "sll t4, t0, 2",
        "sw t3, 0(t4)",
        "sh t2, hcomp_cgram_event_count",
    ):
        if required not in cg:
            raise AssertionError(f"inherited typed color-event drift: {required!r}")

    frame = extract(ppu, "rsp_frame:", "ignore_frame:")
    for required in (
        "lw t0, hcomp_cgram_event_queues(t5)",
        "sw t0, DMEM(HCOMP_CGRAM_EVENT_CURSOR)",
    ):
        if required not in frame:
            raise AssertionError(f"inherited EA0 handoff drift: {required!r}")


def prove_main_publication() -> None:
    src = (ROOT / "src/main.S").read_text()
    block = extract(
        src,
        "// Publish the fixed renderer-slot sources",
        "sw zero, 0xA4080000 // SP_PC",
    )
    anchors = (
        "sw t0, DMEM(OVERLAY_MAIN_SRC)",
        "sw t0, DMEM(OVERLAY_MODE7_SRC)",
        "li t0, HCOMP_RAW_PALETTE_QUEUE1",
        "sw t0, DMEM(HCOMP_RAW_PALETTE_PTRS)",
        "li t0, HCOMP_RAW_PALETTE_QUEUE2",
        "sw t0, DMEM(HCOMP_RAW_PALETTE_PTRS + 4)",
    )
    for anchor in anchors:
        if anchor not in block:
            raise AssertionError(f"raw-shadow publication drift: {anchor!r}")
    positions = [block.index(anchor) for anchor in anchors]
    if positions != sorted(positions):
        raise AssertionError("raw-shadow publication ordering drift")


def prove_rsp_source(path: Path) -> None:
    src = path.read_text()
    name = path.name

    hook = extract(src, "next_section:", "// Check if this section has an OAM update")
    for anchor in (
        "jal dma_read\n    li a2, SECTION_SIZE - 1",
        "addi a1, a1, SECTION_SIZE",
        "sw a1, SECTION_PTR(sp)",
        "b hcomp_cgram_consume\n    move k0, k1",
        "hcomp_cgram_return:",
    ):
        if anchor not in hook:
            raise AssertionError(f"{name}: next_section hook drift: {anchor!r}")
    if "lbu k1, SPLIT_LINE" in hook:
        raise AssertionError(f"{name}: split-line load was not moved to consumer return")

    prefix = extract(src, "hcomp_cgram_consume:", "fill_backdrop:")
    if instruction_count(prefix) != 8:
        raise AssertionError(f"{name}: consumer prefix is not exactly 8 instructions")
    for anchor in (
        "lw t6, HCOMP_CGRAM_EVENT_CURSOR",
        "andi t7, t6, 0x4",
        "bnez t7, hcomp_cgram_pair_ready",
        "li a0, HCOMP_CGRAM_PAIR_SCRATCH",
        "move a1, t6",
        "jal dma_read",
        "li a2, 0x7",
        "b hcomp_cgram_pair_ready",
    ):
        if anchor not in prefix:
            raise AssertionError(f"{name}: prefix missing {anchor!r}")

    # Preserve the three legacy labels at their historical 0/2/3 instruction
    # offsets so definition-only FILL_JUMPS data remains layout-stable.
    before_fill_not = extract(prefix, "fill_win:", "fill_notwin:")
    before_use = extract(prefix, "fill_win:", "use_window:")
    if instruction_count(before_fill_not) != 2 or instruction_count(before_use) != 3:
        raise AssertionError(f"{name}: legacy padding-label offsets moved")

    tail = src[src.index("hcomp_cgram_pair_ready:"):]
    if instruction_count(tail) != 21:
        raise AssertionError(f"{name}: consumer tail is not exactly 21 instructions")
    expected_tail = (
        "add t0, a0, t7",
        "lw t8, 0(t0)",
        "addi t6, t6, 4",
        "sw t6, HCOMP_CGRAM_EVENT_CURSOR",
        "andi t0, t8, 0x8000",
        "bnez t0, hcomp_cgram_marker\n    srl t7, t8, 16",
        "sll t0, t7, 16",
        "or t7, t7, t0",
        "sw t7, HCOMP_CGRAM_WRITE_SCRATCH",
        "sw t7, HCOMP_CGRAM_WRITE_SCRATCH + 4",
        "andi t0, t8, 0x7F8",
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "add a1, a1, t0",
        "li a0, HCOMP_CGRAM_WRITE_SCRATCH",
        "jal dma_write\n    li a2, 0x7",
        "b hcomp_cgram_consume\n    nop",
        "hcomp_cgram_marker:",
        "b hcomp_cgram_return\n    lbu k1, SPLIT_LINE",
    )
    for anchor in expected_tail:
        if anchor not in tail:
            raise AssertionError(f"{name}: tail missing {anchor!r}")

    # Exactly seven pre-audited suffix NOPs are consumed. Keep the memory-read
    # peephole deliberately untouched as the one-instruction spare.
    optimized = (
        "beqz t0, obj_no_windows\n    lbu a0, WOBJSEL",
        "bltz t8, obj_finish_objects\n    lbu t2, WIN_COUNT",
        "beq t1, t2, color_window_none\n    lbu t0, WOBJSEL",
        "beqz t8, color_window_none\n    lbu t0, WIN_BOUNDS + 0",
        "bnez t0, color_window_initial_ready\n    move a1, s0",
        "beq t8, a1, color_window_tail\n    addi a1, t2, -1",
        "beq t8, a1, color_window_tail\n    addi a1, t4, -1",
    )
    for anchor in optimized:
        if anchor not in src:
            raise AssertionError(f"{name}: missing approved peephole {anchor!r}")
    if "beqz t7, window_new_span\n    nop\n    lbu t2, -1(t6)" not in src:
        raise AssertionError(f"{name}: reserved eighth peephole was unexpectedly consumed")

    if instruction_count(prefix) + instruction_count(tail) != 29:
        raise AssertionError(f"{name}: consumer instruction total drift")
    if "hcomp_vector_band_probe" in hook or "hcomp_vector_band_probe" in prefix or "hcomp_vector_band_probe" in tail:
        raise AssertionError(f"{name}: dormant H-COMP arithmetic activated")
    if src.count("HCOMP_CGRAM_EVENT_CURSOR") != 2:
        raise AssertionError(f"{name}: event cursor must have exactly one load and one store")


def parse_text_size(path: Path) -> int:
    text = path.read_text()
    m = re.search(r"^\.text\s+0xa4001000\s+0x([0-9a-fA-F]+)\b", text, re.M)
    if not m:
        raise AssertionError(f"{path}: .text size not found")
    return int(m.group(1), 16)


def parse_symbol(path: Path, symbol: str) -> int:
    text = path.read_text()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[-1] == symbol:
            return int(parts[0], 16)
    raise AssertionError(f"{path}: missing symbol {symbol}")


def prove_binary(maps: list[Path], nms: list[Path]) -> None:
    if len(maps) != 2 or len(nms) != 2:
        raise AssertionError("binary proof needs two maps and two nm dumps")
    for mp in maps:
        size = parse_text_size(mp)
        if size != EXPECTED_TEXT_BYTES:
            raise AssertionError(f"{mp}: RSP text 0x{size:X} != 0x1000")
    for nm in nms:
        draw_bg = parse_symbol(nm, "draw_bg")
        draw_obj = parse_symbol(nm, "draw_obj")
        if draw_bg != FIXED_SLOT_START or draw_obj != FIXED_SLOT_END_NEXT:
            raise AssertionError(
                f"{nm}: fixed slot moved: draw_bg=0x{draw_bg:X} draw_obj=0x{draw_obj:X}"
            )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs=2, type=Path)
    ap.add_argument("--nms", nargs=2, type=Path)
    args = ap.parse_args()

    prove_model()
    prove_defines()
    prove_inherited_typed_producer()
    prove_main_publication()
    for name in ("rsp_main.S", "rsp_mode7.S"):
        prove_rsp_source(ROOT / "src" / name)

    if args.maps or args.nms:
        if not args.maps or not args.nms:
            ap.error("--maps and --nms must be provided together")
        prove_binary(args.maps, args.nms)

    print("CGRAM_RSP_DMA8_CONSUMER_IMPLEMENTATION_VALIDATED")
    print("consumer_instructions=29")
    print("consumer_prefix_instructions=8")
    print("consumer_tail_instructions=21")
    print("suffix_peepholes_consumed=7")
    print("suffix_peephole_spare=1")
    print("event_dma=8byte_aligned_pair")
    print("logical_record=4byte_cached_half")
    print("raw_palette_write=8byte_aligned")
    print("marker_payload=t7_live_on_return")
    print("hcomp_arithmetic=frozen")
    if args.maps:
        print("rsp_text_bytes=4096")
        print("fixed_renderer_slot=A40013A8..A400178F")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
