#!/usr/bin/env python3
"""Source/binary oracle for the implemented DMA8 RSP CGRAM consumer."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_cgram_epoch_contract as epoch
import test_gate_c_cgram_rsp_consumer_contract as l0

CALLSITE_INSNS = 3
PREFIX_INSNS = 8
PREFIX_USED = 7
TAIL_INSNS = 19
TOTAL_CONSUMER_INSNS = CALLSITE_INSNS + PREFIX_USED + TAIL_INSNS
PEEPHOLES_APPLIED = 7
PEEPHOLES_SPARE = 1
EXPECTED_TEXT_BYTES = 0x1000
EXPECTED_FIXED_SLOT = 0xA40013A8

TRANSFORMED_PEEPHOLES = (
    "beqz t0, obj_no_windows\n    lbu a0, WOBJSEL",
    "bltz t8, obj_finish_objects\n    lbu t2, WIN_COUNT",
    "beq t1, t2, color_window_none\n    lbu t0, WOBJSEL",
    "beqz t8, color_window_none\n    lbu t0, WIN_BOUNDS + 0",
    "bnez t0, color_window_initial_ready\n    move a1, s0",
    "beq t8, a1, color_window_tail\n    addi a1, t2, -1",
    "beq t8, a1, color_window_tail\n    addi a1, t4, -1",
)
SPARE_PEEPHOLE = "beqz t7, window_new_span\n    nop\n    lbu t2, -1(t6)"


def extract(src: str, start: str, end: str | None = None) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    if end is None:
        return src[i:]
    j = src.find(end, i)
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def insns(block: str) -> list[str]:
    out = []
    for raw in block.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.endswith(":") or line.startswith("."):
            continue
        out.append(line)
    return out


def macro(name: str) -> int:
    text = (ROOT / "src/defines.h").read_text()
    m = re.search(rf"^#define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\s*$", text, re.M)
    if not m:
        raise AssertionError(f"missing numeric macro {name}")
    return int(m.group(1), 16)


def prove_upstream_semantics() -> None:
    _, cap, _ = epoch.prove_layout()
    max_commits, _ = epoch.prove_timing_capacity(cap)
    if (cap, max_commits) != (24576, 20460):
        raise AssertionError("epoch authority drift")
    l0.prove_rgba_mapping()
    cases = l0.prove_stream_semantics()
    margin = l0.prove_dma_capacity()
    l0.prove_raw_shadow_alignment()
    l0.prove_dead_dmem_reclaim()
    if cases != 33825 or margin != 3796:
        raise AssertionError("DMA8 L0 semantic authority drift")


def prove_dmem_abi() -> None:
    got = (
        macro("HCOMP_CGRAM_EVENT_CURSOR"),
        macro("HCOMP_CGRAM_PAIR_SCRATCH"),
        macro("HCOMP_CGRAM_WRITE_SCRATCH"),
        macro("VEC_DATA"),
    )
    if got != (0xEA0, 0xEA8, 0xEB0, 0xF70):
        raise AssertionError(f"consumer DMEM ABI drift: {got}")
    if got[1] & 7 or got[2] & 7 or not (got[0] < got[1] < got[2] < 0xEB8 <= got[3]):
        raise AssertionError("consumer scratch alignment/range drift")


def prove_source(path: Path) -> None:
    src = path.read_text()

    call = extract(src, "next_section:", "// Check if this section has an OAM update")
    call_expected = (
        "lw t0, FRAME_END(sp)",
        "beq k1, t0, next_frame",
        "lw a1, HCOMP_CGRAM_EVENT_CURSOR",
        "b hcomp_cgram_consume",
        "andi t0, a1, 0x4",
        "lw a1, SECTION_PTR(sp)",
        "jal dma_read",
        "li a2, SECTION_SIZE - 1",
    )
    positions = [call.find(x) for x in call_expected]
    if any(x < 0 for x in positions) or positions != sorted(positions):
        raise AssertionError(f"{path.name}: section consumer callsite/order drift")

    prefix = extract(src, "fill_win:", "fill_backdrop:")
    prefix_insns = insns(prefix)
    expected_prefix = [
        "bnez t0, hcomp_cgram_pair_ready",
        "li a0, HCOMP_CGRAM_PAIR_SCRATCH",
        "jal dma_read",
        "li a2, 0x7",
        "andi t0, a1, 0x4",
        "b hcomp_cgram_consume_tail",
        "lw t2, HCOMP_CGRAM_PAIR_SCRATCH(t0)",
        "nop",
    ]
    if prefix_insns != expected_prefix:
        raise AssertionError(f"{path.name}: 8-slot consumer prefix drift: {prefix_insns}")

    tail = extract(src, "hcomp_cgram_consume_tail:")
    tail_insns = insns(tail)
    expected_tail = [
        "addi a1, a1, 0x4",
        "sw a1, HCOMP_CGRAM_EVENT_CURSOR",
        "andi t3, t2, 0x8000",
        "bnez t3, hcomp_cgram_section_ready",
        "li a0, BGHOFS",
        "andi t3, t2, 0x07F8",
        "srl t2, t2, 16",
        "sll t0, t2, 16",
        "or t2, t2, t0",
        "sw t2, HCOMP_CGRAM_WRITE_SCRATCH",
        "sw t2, HCOMP_CGRAM_WRITE_SCRATCH + 4",
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "add a1, a1, t3",
        "li a0, HCOMP_CGRAM_WRITE_SCRATCH",
        "jal dma_write",
        "li a2, 0x7",
        "lw a1, HCOMP_CGRAM_EVENT_CURSOR",
        "b hcomp_cgram_consume",
        "andi t0, a1, 0x4",
    ]
    if tail_insns != expected_tail:
        raise AssertionError(f"{path.name}: 19-insn consumer tail drift: {tail_insns}")

    for p in TRANSFORMED_PEEPHOLES:
        if p not in src:
            raise AssertionError(f"{path.name}: missing applied safe peephole {p!r}")
    if SPARE_PEEPHOLE not in src:
        raise AssertionError(f"{path.name}: reserved eighth peephole was consumed")

    if TOTAL_CONSUMER_INSNS != 29 or PEEPHOLES_APPLIED != 7 or PEEPHOLES_SPARE != 1:
        raise AssertionError("consumer instruction-budget constants drift")
    if "HCOMP_CGRAM_EVENT_CURSOR" not in call or "HCOMP_RAW_PALETTE_PTRS(sp)" not in tail:
        raise AssertionError(f"{path.name}: event/raw ownership linkage missing")


def map_text_size(path: Path) -> int:
    text = path.read_text()
    m = re.search(r"^\.text\s+0xa4001000\s+(0x[0-9a-fA-F]+)", text, re.M)
    if not m:
        raise AssertionError(f"{path}: cannot find linked .text size")
    return int(m.group(1), 16)


def symbol_value(obj: Path, symbol: str) -> int:
    out = subprocess.check_output(["readelf", "-sW", str(obj)], text=True)
    for line in out.splitlines():
        fields = line.split()
        if fields and fields[-1] == symbol:
            return int(fields[1], 16)
    raise AssertionError(f"{obj}: missing symbol {symbol}")


def prove_binary(build: Path) -> None:
    pairs = (
        ("rsp_main", "draw_bg"),
        ("rsp_mode7", "draw_mode7_entry"),
    )
    for stem, fixed_symbol in pairs:
        mp = build / f"{stem}.map"
        obj = build / "src" / f"{stem}.o"
        size = map_text_size(mp)
        if size != EXPECTED_TEXT_BYTES:
            raise AssertionError(f"{stem}: .text size 0x{size:X} != 0x1000")
        addr = symbol_value(obj, fixed_symbol)
        if addr != EXPECTED_FIXED_SLOT:
            raise AssertionError(
                f"{stem}: fixed renderer slot moved: {fixed_symbol}=0x{addr:X}"
            )


def main() -> int:
    prove_upstream_semantics()
    prove_dmem_abi()
    main_src = ROOT / "src/rsp_main.S"
    mode7_src = ROOT / "src/rsp_mode7.S"
    prove_source(main_src)
    prove_source(mode7_src)

    build = ROOT / "build"
    prove_binary(build)

    print("CGRAM_RSP_DMA8_CONSUMER_IMPLEMENTATION_VALIDATED")
    print("consumer_instructions=29")
    print("callsite_instructions=3")
    print("dead_prefix_slots=8")
    print("dead_prefix_used=7")
    print("tail_instructions=19")
    print("safe_suffix_peepholes_applied=7")
    print("safe_suffix_peepholes_spare=1")
    print("rsp_text_bytes=4096")
    print("fixed_renderer_slot=0xA40013A8")
    print("event_pair_dma=8_bytes")
    print("logical_record=4_bytes")
    print("cached_second_half=yes")
    print("raw_palette_write_dma=8_bytes")
    print("marker_returns_to_section=yes")
    print("hcomp_arithmetic=still_frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
