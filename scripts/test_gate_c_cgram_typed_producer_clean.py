#!/usr/bin/env python3
"""Source/model oracle for the clean typed CPU CGRAM producer."""

from __future__ import annotations

from itertools import product
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_cgram_rsp_consumer_clean_contract as l0


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i + len(start))
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def prove_layout() -> None:
    ev = l0.parse_macros(ROOT)
    expected = {
        "HCOMP_RAW_PALETTE_QUEUE1": 0xA00EF000,
        "HCOMP_RAW_PALETTE_QUEUE2": 0xA00EF800,
        "HCOMP_CGRAM_BASE_QUEUE1": 0xA00BE200,
        "HCOMP_CGRAM_BASE_QUEUE2": 0xA00BE400,
        "HCOMP_CGRAM_EVENT_QUEUE1": 0xA00BF000,
        "HCOMP_CGRAM_EVENT_QUEUE2": 0xA00D7000,
        "HCOMP_CGRAM_EVENT_CAPACITY": 0x6000,
        "HCOMP_CGRAM_EVENT_CURSOR": 0xEA0,
        "VEC_DATA": 0xF70,
    }
    for name, want in expected.items():
        got = ev.name(name)
        if got != want:
            raise AssertionError(f"{name} drift: 0x{got:X} != 0x{want:X}")

    fb = ev.name("FRAMEBUFFER1")
    raw_end = ev.name("HCOMP_RAW_PALETTE_QUEUE2") + l0.RAW_SHADOW_BYTES
    if fb - raw_end != 0x2300:
        raise AssertionError("raw-shadow/framebuffer guard drift")

    total = l0.MAX_COLOR_RECORDS + l0.MAX_SECTION_MARKERS
    if total != 20780 or total >= ev.name("HCOMP_CGRAM_EVENT_CAPACITY"):
        raise AssertionError("typed stream capacity drift")


def produce_stream(
    base: tuple[int, ...],
    sections: tuple[tuple[tuple[int, int], ...], ...],
    fixed: tuple[int, ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if len(sections) != len(fixed):
        raise AssertionError("section/fixed mismatch")
    raw = tuple(l0.rgb555_to_rgba5551(v) for v in base)
    stream: list[int] = []
    for writes, raw_fixed in zip(sections, fixed):
        for index, value in writes:
            stream.append(l0.color_record(index, value))
        stream.append(l0.marker_record(raw_fixed))
    return raw, tuple(stream)


def prove_roundtrip() -> int:
    base = (0x0000, 0x0001, 0x1234, 0x7FFF)
    atoms = tuple((i, v) for i, v in product(
        range(4), (0x0000, 0x001F, 0x4210, 0x7FFF)
    ))
    choices = ((),) + tuple((x,) for x in atoms)
    fixed_values = (0x0000, 0x03E0, 0x7C00, 0x7FFF)
    cases = 0

    for first in choices:
        for second in choices:
            for f0 in fixed_values:
                for f1 in fixed_values:
                    raw, stream = produce_stream(base, (first, second), (f0, f1))
                    got, _ = l0.consume_typed_stream(raw, stream)
                    live = list(base)
                    want = []
                    for writes, fixed in ((first, f0), (second, f1)):
                        for index, value in writes:
                            live[index] = value & 0x7FFF
                        want.append((tuple(live), fixed))
                    if got != want:
                        raise AssertionError(
                            f"producer/consumer mismatch: {first=} {second=} "
                            f"{f0=:04X} {f1=:04X}"
                        )
                    cases += 1

    # Exact audit-critical sequence from the historical dynamic proof family.
    raw, stream = produce_stream(
        base,
        (
            (),
            ((1, 0x1234), (1, 0x4567), (0, 0x2AAA)),
            ((2, 0x7FFF),),
        ),
        (0x001F, 0x03E0, 0x7C00),
    )
    got, reads = l0.consume_typed_stream(raw, stream)
    want = [
        (base, 0x001F),
        ((0x2AAA, 0x4567, 0x1234, 0x7FFF), 0x03E0),
        ((0x2AAA, 0x4567, 0x7FFF, 0x7FFF), 0x7C00),
    ]
    if got != want:
        raise AssertionError("audit-critical typed stream mismatch")
    if reads != (len(stream) + 1) // 2:
        raise AssertionError("cached half-pair DMA count drift")
    return cases


def prove_source() -> None:
    defs = (ROOT / "src" / "defines.h").read_text()
    main = (ROOT / "src" / "main.S").read_text()
    ppu = (ROOT / "src" / "ppu.S").read_text()
    rsp_main = (ROOT / "src" / "rsp_main.S").read_text()
    rsp_mode7 = (ROOT / "src" / "rsp_mode7.S").read_text()

    for name, src in (("rsp_main", rsp_main), ("rsp_mode7", rsp_mode7)):
        if "HCOMP_CGRAM_" in src:
            raise AssertionError(f"{name}: RSP consumer activated too early")
        if "HCOMP_RAW_PALETTE_PTRS" in src:
            raise AssertionError(f"{name}: raw-shadow consumer pointer activated too early")

    clear = extract(main, "// Clear the complete fixed RDRAM arena", "// Initialize the VI")
    if "li t0, HCOMP_CGRAM_BASE_QUEUE1" not in clear:
        raise AssertionError("boot clear does not cover typed producer arena")
    if "li t1, JIT_BUFFER - 8" not in clear:
        raise AssertionError("boot clear upper bound drift")

    data = extract(ppu, "pal_queues:", ".align 4\n// Values that control")
    for anchor in (
        "hcomp_raw_pal_queues: .word HCOMP_RAW_PALETTE_QUEUE1, HCOMP_RAW_PALETTE_QUEUE2",
        "hcomp_cgram_base_queues: .word HCOMP_CGRAM_BASE_QUEUE1, HCOMP_CGRAM_BASE_QUEUE2",
        "hcomp_cgram_event_queues: .word HCOMP_CGRAM_EVENT_QUEUE1, HCOMP_CGRAM_EVENT_QUEUE2",
        "hcomp_cgram_event_ptr: .word HCOMP_CGRAM_EVENT_QUEUE1",
        "hcomp_cgram_event_count: .hword 0",
        "hcomp_cgram_event_overflow: .byte 0",
    ):
        if anchor not in data:
            raise AssertionError(f"producer data anchor missing: {anchor!r}")

    vb = extract(ppu, "vblank_end:", ".align 5\nvcount_irq:")
    if "jal hcomp_cgram_begin_frame" not in vb:
        raise AssertionError("vblank_end does not start typed producer")
    if vb.index("jal hcomp_cgram_begin_frame") > vb.index("j section_init"):
        raise AssertionError("typed base snapshot occurs after first section")

    begin = extract(ppu, "hcomp_cgram_begin_frame:", ".align 5\nupdate_frame:")
    for anchor in (
        "lw t5, hcomp_raw_pal_queues(t0)",
        "sw t2, hcomp_cgram_event_ptr",
        "sh zero, hcomp_cgram_event_count",
        "sb zero, hcomp_cgram_event_overflow",
        "li t4, 0x200",
        "andi t3, t3, 0x7FFF",
        "sh t3, 0(t1)",
        "ori t6, t6, 0x1",
        "sw t6, 0(t5)",
        "sw t6, 4(t5)",
        "addi t5, t5, 8",
    ):
        if anchor not in begin:
            raise AssertionError(f"typed base/raw init drift: {anchor!r}")

    section = extract(ppu, "section_init:", ".align 5\nhcomp_cgram_begin_frame:")
    marker_anchors = (
        "lhu t0, hcomp_cgram_event_count",
        "li t1, HCOMP_CGRAM_EVENT_CAPACITY",
        "bge t0, t1, hcomp_cgram_marker_overflow",
        "lhu t2, coldata",
        "ori t3, t3, 0x1",
        "sll t3, t3, 16",
        "ori t3, t3, 0x8000",
        "lw t1, hcomp_cgram_event_ptr",
        "sw t3, 0(t1)",
        "addi t1, t1, 4",
        "sw t1, hcomp_cgram_event_ptr",
        "addi t0, t0, 1",
        "sh t0, hcomp_cgram_event_count",
    )
    positions = []
    for anchor in marker_anchors:
        if anchor not in section:
            raise AssertionError(f"typed marker drift: {anchor!r}")
        positions.append(section.index(anchor))
    if positions != sorted(positions):
        raise AssertionError("typed marker encode/store order drift")
    if "hcomp_cgram_sideband_ptr" in section:
        raise AssertionError("legacy sideband write remains active")

    cg = extract(ppu, "write_cgdata:", ".align 5\nwrite_w12sel:")
    for anchor in (
        "lbu t2, hvbjoy",
        "lbu t2, frame_done",
        "li t3, HCOMP_CGRAM_EVENT_CAPACITY",
        "bge t2, t3, cg_epoch_overflow",
        "ori t3, t3, 0x1",
        "sll t3, t3, 16",
        "sll t4, t0, 2",
        "or t3, t3, t4",
        "sw t3, 0(t4)",
        "addi t2, t2, 1",
        "sh t2, hcomp_cgram_event_count",
        "li t3, 0x100",
        "sh t3, sect_status",
    ):
        if anchor not in cg:
            raise AssertionError(f"typed color event drift: {anchor!r}")
    if cg.index("bge t2, t3, cg_epoch_overflow") > cg.index("sw t3, 0(t4)"):
        raise AssertionError("color overflow guard occurs after store")
    if cg.index("lbu t2, frame_done") > cg.index("sw t3, 0(t4)"):
        raise AssertionError("early-frame-close guard occurs after store")

    rf = extract(ppu, "rsp_frame:", "ignore_frame:")
    handoff = rf.index("sw t0, DMEM(HCOMP_CGRAM_EVENT_CURSOR)")
    select = rf.rfind("lw t0, hcomp_cgram_event_queues(t5)", 0, handoff)
    semaphore = rf.index("lw t0, 0xA404001C")
    unhalt = rf.index("sw t0, 0x0010(t1)")
    if select < 0 or not (select < handoff < semaphore < unhalt):
        raise AssertionError("typed event cursor publication ordering drift")
    if ppu.count("DMEM(HCOMP_CGRAM_EVENT_CURSOR)") != 1:
        raise AssertionError("typed event cursor publication count drift")

    if "HCOMP_RAW_PALETTE_PTRS" in defs or "hcomp_vector_band_probe" in ppu:
        raise AssertionError("consumer/H-COMP arithmetic leaked into producer-only stage")


def main() -> int:
    prove_layout()
    l0.prove_rgb_mapping()
    l0.prove_record_encoding()
    cases = prove_roundtrip()
    prove_source()

    print("CGRAM_TYPED_PRODUCER_CLEAN_VALIDATED")
    print("runtime_scope=cpu_producer_only")
    print("raw_shadow_initialization=256_entries_including_entry0")
    print("raw_shadow_geometry=8bytes_per_entry_double_buffered")
    print("typed_color=rgba5551_plus_index_times_8")
    print("typed_marker=rgba5551_fixed_plus_0x8000")
    print("event_count=colors_plus_markers")
    print("event_capacity=24576")
    print("event_worst_case=20780")
    print("event_margin=3796")
    print(f"producer_consumer_roundtrip_cases={cases}")
    print("event_cursor_dmem=0xEA0")
    print("event_cursor_publish=while_rsp_halted")
    print("rsp_consumer=frozen")
    print("hcomp_arithmetic=frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
