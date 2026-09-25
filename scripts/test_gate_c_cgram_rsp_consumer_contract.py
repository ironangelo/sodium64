#!/usr/bin/env python3
"""L0 contract for a capacity-safe RSP CGRAM epoch consumer.

The consumer does not activate H-COMP arithmetic. It proves a typed 4-byte
stream can delimit sections without a sideband DMA and that an RSP replay loop
fits the exact current IMEM layout by replacing existing dead/padding work
rather than adding another overlay.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_cgram_epoch_contract as base_contract

TEXT_BYTES = 0xFC8
IMEM_BYTES = 0x1000
TAIL_FREE_INSNS = (IMEM_BYTES - TEXT_BYTES) // 4
CONSUMER_INSNS = 20

MAX_COLOR_RECORDS = 20460
MAX_SECTION_MARKERS = 320
EVENT_CAPACITY = 24576

# Reclaimable DMEM left behind by the retired executable H-COMP scaffold.
CONSUMER_EVENT_CURSOR = 0xEA0
CONSUMER_BASE_PTR = 0xEA4
CONSUMER_RECORD_SCRATCH = 0xEA8  # 4 bytes are sufficient
CONSUMER_STATE_END = 0xEAC
VEC_DATA = 0xF70

COLOR = 0
SECTION = 1


def color(index: int, value: int) -> tuple[int, int, int]:
    return index & 0xFF, COLOR, value & 0x7FFF


def marker(raw_coldata: int) -> tuple[int, int, int]:
    return 0, SECTION, raw_coldata & 0x7FFF


def consume_one_section(
    palette: list[int],
    stream: tuple[tuple[int, int, int], ...],
    cursor: int,
) -> tuple[int, int, int]:
    """Mirror the proposed RSP loop: replay colors until one section marker."""
    while cursor < len(stream):
        index, kind, payload = stream[cursor]
        cursor += 1
        if kind == SECTION:
            return cursor, payload, 1
        if kind != COLOR:
            raise AssertionError(f"unknown record type {kind}")
        palette[index] = payload & 0x7FFF
    raise AssertionError("stream ended before section marker")


def prove_stream_semantics() -> int:
    base = [0x0000, 0x0001, 0x1234, 0x7FFF]
    atoms = tuple((i, v) for i, v in product(range(4), range(4)))
    fixed_values = (0x0000, 0x001F, 0x4210, 0x7FFF)
    cases = 0

    # Exhaust color streams through length 3 and every possible division into
    # up to three sections. Repeated indices and entry0 are naturally covered.
    for n in range(4):
        for events in product(atoms, repeat=n):
            # A cut mask says which event positions end a section. Always append
            # a final marker so every color record belongs to exactly one section.
            for cutmask in range(1 << n):
                stream: list[tuple[int, int, int]] = []
                expected_states: list[tuple[int, ...]] = []
                expected_fixed: list[int] = []
                live = list(base)
                fi = 0
                for i, (index, value) in enumerate(events):
                    stream.append(color(index, value))
                    live[index] = value & 0x7FFF
                    if cutmask & (1 << i):
                        fixed = fixed_values[fi % len(fixed_values)]
                        fi += 1
                        stream.append(marker(fixed))
                        expected_states.append(tuple(live))
                        expected_fixed.append(fixed)
                if not stream or stream[-1][1] != SECTION:
                    fixed = fixed_values[fi % len(fixed_values)]
                    stream.append(marker(fixed))
                    expected_states.append(tuple(live))
                    expected_fixed.append(fixed)

                got = list(base)
                cursor = 0
                for want_state, want_fixed in zip(expected_states, expected_fixed):
                    cursor, raw_fixed, markers = consume_one_section(
                        got, tuple(stream), cursor
                    )
                    if markers != 1:
                        raise AssertionError("consumer crossed multiple markers")
                    if tuple(got) != want_state:
                        raise AssertionError(
                            f"typed replay mismatch: {events=} {cutmask=} "
                            f"{tuple(got)=} {want_state=}"
                        )
                    if raw_fixed != want_fixed:
                        raise AssertionError("marker fixed color mismatch")
                if cursor != len(stream):
                    raise AssertionError("consumer left records after final section")
                cases += 1

    # Explicitly retain the audit-critical cases.
    palette = [0, 1, 2]
    stream = (
        color(1, 0x1234),
        color(1, 0x4567),  # repeated index
        color(0, 0x2AAA),  # entry0
        marker(0x1CE7),
        color(2, 0x7FFF),
        marker(0x0C63),
    )
    cursor, fixed, _ = consume_one_section(palette, stream, 0)
    if palette != [0x2AAA, 0x4567, 2] or fixed != 0x1CE7:
        raise AssertionError("explicit first epoch mismatch")
    cursor, fixed, _ = consume_one_section(palette, stream, cursor)
    if palette != [0x2AAA, 0x4567, 0x7FFF] or fixed != 0x0C63:
        raise AssertionError("explicit second epoch mismatch")
    if cursor != len(stream):
        raise AssertionError("explicit stream cursor mismatch")

    return cases


def prove_capacity() -> int:
    if TAIL_FREE_INSNS != 14:
        raise AssertionError(f"current IMEM free instruction count drift: {TAIL_FREE_INSNS}")
    total_records = MAX_COLOR_RECORDS + MAX_SECTION_MARKERS
    if total_records != 20780:
        raise AssertionError("record-bound arithmetic drift")
    if total_records >= EVENT_CAPACITY:
        raise AssertionError("typed record stream can overflow")
    margin = EVENT_CAPACITY - total_records
    if margin != 3796:
        raise AssertionError(f"typed record margin drift: {margin}")
    return margin


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i)
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def prove_dead_dmem_reclaim() -> None:
    for name in ("rsp_main.S", "rsp_mode7.S"):
        src = (ROOT / "src" / name).read_text()
        for symbol in (
            "hcomp_vec_carrylo",
            "hcomp_vec_carryhi",
            "hcomp_vec_half",
            "hcomp_vec_one",
            "hcomp_vec_three",
            "hcomp_vec_shr10",
            "hcomp_vec_shr11",
        ):
            occurrences = len(re.findall(rf"\b{symbol}\b", src))
            if occurrences != 1:
                raise AssertionError(
                    f"{name}: retired DMEM symbol {symbol} has {occurrences} refs"
                )
        if ".byte 0:0x60" not in src:
            raise AssertionError(f"{name}: retired EA0..F6F padding layout drift")
        if "vec_data:" not in src:
            raise AssertionError(f"{name}: VEC_DATA anchor missing")

    if not (0xEA0 <= CONSUMER_EVENT_CURSOR < CONSUMER_STATE_END <= VEC_DATA):
        raise AssertionError("consumer state escapes retired DMEM interval")


def prove_current_consumer_inputs() -> None:
    ppu = (ROOT / "src/ppu.S").read_text()
    rsp = (ROOT / "src/rsp_main.S").read_text()

    # Queue ownership and immutable handoff already exist: non-skipped frame
    # changes queue_id before the next producer begins.
    rf = extract(ppu, "rsp_frame:", "ignore_frame:")
    for anchor in (
        "lbu t5, queue_id",
        "xori t6, t5, 4",
        "sb t6, queue_id",
        "sw t3, DMEM(SECTION_PTR)(t5)",
        "sw t7, DMEM(OAM_PTR)(t5)",
    ):
        if anchor not in rf:
            raise AssertionError(f"frame handoff contract drift: {anchor}")

    # The consumer insertion point is common resident code before renderer
    # dispatch and therefore applies equally to regular and Mode7 overlays.
    ns = extract(rsp, "next_section:", "// Check if this section has an OAM update")
    for anchor in (
        "jal dma_read",
        "li a2, SECTION_SIZE - 1",
        "move k0, k1",
        "lbu k1, SPLIT_LINE",
    ):
        if anchor not in ns:
            raise AssertionError(f"next_section anchor drift: {anchor}")


def safe_peephole_count(src: str) -> int:
    """Count precommitted delay-slot compactions valid in both RSP variants."""
    anchors = (
        # Taken path overwrites/ignores a0.
        "beqz t0, obj_no_windows\n    nop\n\n    lbu a0, WOBJSEL",
        # Taken path exits OBJ traversal and does not use t2.
        "bltz t8, obj_finish_objects\n    nop\n\n    // Advance by explicit span count",
        # Taken path overwrites t0 in color_window_none.
        "beq t1, t2, color_window_none\n    nop\n\n    // Modes 1/2",
        # Taken path overwrites t0 in color_window_none.
        "beqz t8, color_window_none\n    nop\n\n    // Snapshot all possible span endpoints",
        # Taken path does not consume a1 before it is overwritten.
        "bnez t0, color_window_initial_ready\n    nop\n    move a1, s0",
        # color_window_tail overwrites a1 immediately.
        "beq t8, a1, color_window_tail\n    nop\n\n    addi a1, t2, -1",
        # Second count test has the same a1 property.
        "beq t8, a1, color_window_tail\n    nop\n\n    addi a1, t4, -1",
        # New-span path does not consume t2 loaded from prior span.
        "beqz t7, window_new_span\n    nop\n    lbu t2, -1(t6)",
    )
    found = 0
    for anchor in anchors:
        if anchor not in src:
            raise AssertionError(f"missing safe peephole anchor: {anchor!r}")
        found += 1
    return found


def prove_instruction_budget() -> tuple[int, int]:
    main = (ROOT / "src/rsp_main.S").read_text()
    mode7 = (ROOT / "src/rsp_mode7.S").read_text()
    p_main = safe_peephole_count(main)
    p_mode7 = safe_peephole_count(mode7)
    if p_main != p_mode7 or p_main != 8:
        raise AssertionError("common peephole budget diverged")

    # next_section uses a direct branch whose delay slot reuses the existing
    # move k0,k1; the consumer returns with lbu k1,SPLIT_LINE in its branch
    # delay slot. Therefore the call-site footprint itself does not grow.
    available = TAIL_FREE_INSNS + p_main
    spare = available - CONSUMER_INSNS
    if available != 22 or spare != 2:
        raise AssertionError(
            f"consumer IMEM budget changed: {available=} {CONSUMER_INSNS=} {spare=}"
        )
    return available, spare


def main() -> int:
    # Reuse the already-validated physical color-commit bound.
    _, event_capacity, _ = base_contract.prove_layout()
    max_commits, _ = base_contract.prove_timing_capacity(event_capacity)
    if max_commits != MAX_COLOR_RECORDS or event_capacity != EVENT_CAPACITY:
        raise AssertionError("upstream CGRAM capacity authority drift")

    cases = prove_stream_semantics()
    margin = prove_capacity()
    prove_dead_dmem_reclaim()
    prove_current_consumer_inputs()
    available, spare = prove_instruction_budget()

    print("CGRAM_RSP_CONSUMER_CONTRACT_VALIDATED")
    print(f"max_color_records={MAX_COLOR_RECORDS}")
    print(f"max_section_markers={MAX_SECTION_MARKERS}")
    print(f"total_record_bound={MAX_COLOR_RECORDS + MAX_SECTION_MARKERS}")
    print(f"record_capacity={EVENT_CAPACITY}")
    print(f"record_margin={margin}")
    print(f"typed_replay_cases={cases}")
    print("record_type0=color_write")
    print("record_type1=section_marker_with_raw_coldata")
    print("entry0=preserved")
    print("repeated_writes=preserved")
    print("consumer_mutates=owned_base_snapshot")
    print("sideband_dma=not_required_for_palette_replay")
    print(f"consumer_instruction_budget={available}")
    print(f"consumer_instructions_required={CONSUMER_INSNS}")
    print(f"consumer_spare_instructions={spare}")
    print("third_overlay=not_required")
    print("fixed_renderer_slot=must_not_move")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
