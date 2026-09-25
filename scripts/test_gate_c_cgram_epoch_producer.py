#!/usr/bin/env python3
"""Source/model oracle for the DMA8-ready CPU CGRAM producer."""

from __future__ import annotations

from itertools import product
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_cgram_epoch_contract as epoch_contract
import test_gate_c_cgram_rsp_consumer_contract as dma8


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i)
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def prove_layout() -> None:
    sections, events, _ = epoch_contract.prove_layout()
    if (sections, events) != (320, 24576):
        raise AssertionError("upstream CGRAM layout drift")
    dma8.prove_rgba_mapping()
    if dma8.prove_dma_capacity() != 3796:
        raise AssertionError("DMA8 packed-stream margin drift")
    dma8.prove_raw_shadow_alignment()

    ev = epoch_contract.parse_macros()
    for name, want in {
        "HCOMP_RAW_PALETTE_QUEUE1": 0xA00EF000,
        "HCOMP_RAW_PALETTE_QUEUE2": 0xA00EF800,
        "HCOMP_CGRAM_EVENT_QUEUE1": 0xA00BF000,
        "HCOMP_CGRAM_EVENT_QUEUE2": 0xA00D7000,
        "HCOMP_CGRAM_EVENT_CAPACITY": 0x6000,
        "HCOMP_CGRAM_EVENT_CURSOR": 0xEA0,
    }.items():
        got = ev.name(name)
        if got != want:
            raise AssertionError(f"{name} drift: 0x{got:X} != 0x{want:X}")


def prove_historical_raw_base() -> int:
    palette = [((i * 17) ^ (i << 5) ^ (i << 10)) & 0x7FFF for i in range(256)]
    palette[0:4] = [0x2AAA, 0x001F, 0x03E0, 0x7C00]
    palette[255] = 0x7FFF
    raw = [dma8.rgb555_to_rgba5551(v) for v in palette]
    for i, (rgb, rgba) in enumerate(zip(palette, raw)):
        if dma8.rgba5551_to_rgb555(rgba) != rgb:
            raise AssertionError(f"historical raw mismatch at entry {i}")
        if (i * 8) & 7:
            raise AssertionError("raw entry alignment lost")
    if dma8.rgba5551_to_rgb555(raw[0]) != 0x2AAA:
        raise AssertionError("entry0 not preserved")
    return len(raw)


def produce_stream(
    base: tuple[int, ...],
    sections: tuple[tuple[tuple[int, int], ...], ...],
    fixed: tuple[int, ...],
) -> tuple[int, ...]:
    if len(sections) != len(fixed):
        raise AssertionError("section/fixed mismatch")
    stream: list[int] = []
    for writes, raw_fixed in zip(sections, fixed):
        for index, value in writes:
            stream.append(dma8.color_record(index, value))
        stream.append(dma8.marker_record(raw_fixed))
    return tuple(stream)


def prove_roundtrip() -> int:
    base = (0x0000, 0x0001, 0x1234, 0x7FFF)
    atoms = tuple((i, v) for i, v in product(range(4), (0x0000, 0x001F, 0x4210, 0x7FFF)))
    choices = ((),) + tuple((x,) for x in atoms)
    fixed_values = (0x0000, 0x03E0, 0x7C00, 0x7FFF)
    cases = 0

    for first in choices:
        for second in choices:
            for f0 in fixed_values:
                for f1 in fixed_values:
                    stream = produce_stream(base, (first, second), (f0, f1))
                    got, _ = dma8.consume_stream(list(base), stream)
                    live = list(base)
                    want = []
                    for writes, fixed in ((first, f0), (second, f1)):
                        for index, value in writes:
                            live[index] = value & 0x7FFF
                        want.append((tuple(live), fixed))
                    if got != want:
                        raise AssertionError(
                            f"producer->consumer mismatch: {first=} {second=} "
                            f"{f0=:04X} {f1=:04X}"
                        )
                    cases += 1

    # Marker is word0; next section's first color is cached word1.
    stream = produce_stream(
        base,
        (
            (),
            ((1, 0x1234), (1, 0x4567), (0, 0x2AAA)),
            ((2, 0x7FFF),),
        ),
        (0x001F, 0x03E0, 0x7C00),
    )
    got, reads = dma8.consume_stream(list(base), stream)
    want = [
        (base, 0x001F),
        ((0x2AAA, 0x4567, 0x1234, 0x7FFF), 0x03E0),
        ((0x2AAA, 0x4567, 0x7FFF, 0x7FFF), 0x7C00),
    ]
    if got != want or reads != (len(stream) + 1) // 2:
        raise AssertionError("audit-critical cached-half typed stream mismatch")
    return cases


def prove_source() -> None:
    ppu = (ROOT / "src/ppu.S").read_text()
    rsp_main = (ROOT / "src/rsp_main.S").read_text()
    rsp_mode7 = (ROOT / "src/rsp_mode7.S").read_text()

    for src, name in ((rsp_main, "rsp_main"), (rsp_mode7, "rsp_mode7")):
        if "HCOMP_CGRAM_EVENT_CURSOR" in src or "HCOMP_CGRAM_EVENT_" in src:
            raise AssertionError(f"{name} consumes the stream too early")

    begin = extract(ppu, "hcomp_cgram_begin_frame:", ".align 5\nupdate_frame:")
    for anchor in (
        "lbu t0, queue_id",
        "lw t1, hcomp_cgram_base_queues(t0)",
        "lw t2, hcomp_cgram_event_queues(t0)",
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
        "addi t0, t0, 2",
        "addi t1, t1, 2",
        "addi t5, t5, 8",
        "bnez t4, hcomp_cgram_base_loop",
    ):
        if anchor not in begin:
            raise AssertionError(f"historical-base source missing {anchor!r}")

    section = extract(ppu, "section_init:", ".align 5\nhcomp_cgram_begin_frame:")
    marker = (
        "lhu t0, hcomp_cgram_event_count",
        "li t1, HCOMP_CGRAM_EVENT_CAPACITY",
        "bge t0, t1, hcomp_cgram_marker_overflow",
        "lhu t2, coldata",
        "andi t1, t2, 0x3E0",
        "sll t1, t1, 1",
        "or t3, t3, t1",
        "andi t1, t2, 0x7C00",
        "srl t1, t1, 9",
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
    for anchor in marker:
        if anchor not in section:
            raise AssertionError(f"typed marker source missing {anchor!r}")
        positions.append(section.index(anchor))
    if positions != sorted(positions):
        raise AssertionError("marker encode/store ordering drift")
    if section.index("sw t1, section_ptr") > section.index("sw t3, 0(t1)"):
        raise AssertionError("marker emitted before section snapshot")
    if section.index("bge t0, t1, hcomp_cgram_marker_overflow") > section.index("sw t3, 0(t1)"):
        raise AssertionError("marker guard occurs after marker store")
    if "hcomp_cgram_sideband_ptr" in section:
        raise AssertionError("legacy sideband write still active")
    marker_block = extract(section, "// Append one typed section marker", "hcomp_cgram_marker_overflow:")
    if "t4" in marker_block:
        raise AssertionError("section marker clobbers rsp_frame saved return register t4")

    cg = extract(ppu, "write_cgdata:", ".align 5\nwrite_w12sel:")
    for anchor in (
        "sh t1, cgram(t0)",
        "lbu t2, hvbjoy",
        "bnez t2, cg_epoch_done",
        "lbu t2, frame_done",
        "lhu t2, hcomp_cgram_event_count",
        "li t3, HCOMP_CGRAM_EVENT_CAPACITY",
        "bge t2, t3, cg_epoch_overflow",
        "ori t3, t3, 0x1",
        "sll t3, t3, 16",
        "sll t4, t0, 2",
        "or t3, t3, t4",
        "lw t4, hcomp_cgram_event_ptr",
        "sw t3, 0(t4)",
        "addi t4, t4, 4",
        "sw t4, hcomp_cgram_event_ptr",
        "addi t2, t2, 1",
        "sh t2, hcomp_cgram_event_count",
        "li t3, 0x100",
        "sh t3, sect_status",
    ):
        if anchor not in cg:
            raise AssertionError(f"typed color source missing {anchor!r}")
    if cg.index("bge t2, t3, cg_epoch_overflow") > cg.index("sw t3, 0(t4)"):
        raise AssertionError("color guard occurs after store")
    if cg.index("lbu t2, frame_done") > cg.index("sw t3, 0(t4)"):
        raise AssertionError("early-close guard occurs after store")

    rf = extract(ppu, "rsp_frame:", "ignore_frame:")
    if "hcomp_raw_pal_queues" in rf:
        raise AssertionError("rsp_frame still overwrites historical raw shadow")
    handoff = rf.index("sw t0, DMEM(HCOMP_CGRAM_EVENT_CURSOR)")
    select = rf.rfind("lw t0, hcomp_cgram_event_queues(t5)", 0, handoff)
    semaphore = rf.index("lw t0, 0xA404001C")
    unhalt = rf.index("sw t0, 0x0010(t1)")
    if select < 0 or not (select < handoff < semaphore < unhalt):
        raise AssertionError("EA0 publication ordering drift")
    if ppu.count("DMEM(HCOMP_CGRAM_EVENT_CURSOR)") != 1:
        raise AssertionError("EA0 publication count drift")


def main() -> int:
    prove_layout()
    raw_entries = prove_historical_raw_base()
    cases = prove_roundtrip()
    prove_source()

    print("CGRAM_DMA8_PRODUCER_MODEL_VALIDATED")
    print(f"historical_raw_entries={raw_entries}")
    print("historical_raw_includes_entry0=yes")
    print("frame_final_raw_overwrite=absent")
    print("typed_color_record=raw_rgba5551_plus_index_times_8")
    print("typed_section_marker=raw_fixed_rgba5551_plus_0x8000")
    print("event_count=colors_plus_markers")
    print("event_capacity=24576")
    print("event_worst_case=20780")
    print("event_margin=3796")
    print(f"producer_consumer_roundtrip_cases={cases}")
    print("event_cursor_dmem=0xEA0")
    print("event_cursor_publish=before_rsp_unhalt")
    print("rsp_consumer=still_frozen")
    print("hcomp_arithmetic=still_frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
