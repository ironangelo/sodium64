#!/usr/bin/env python3
"""DMA-aware L0 contract for the RSP CGRAM epoch consumer.

No runtime code is changed here. This revision supersedes the earlier 2-byte
base-snapshot mutation plan after auditing the pinned ares N64 SP-DMA model:
SP/DRAM addresses and transfers are 8-byte granular. Logical records therefore
remain 4 bytes but are consumed two-at-a-time from aligned 8-byte DMA pairs.
Palette mutations target the existing 8-byte-per-entry raw RGBA5551 shadow.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_cgram_epoch_contract as base_contract

ARES_PIN = "17813a3ccda21ab9bd45f09bfc2f91196dbf50ff"
TEXT_BYTES = 0xFC8
IMEM_BYTES = 0x1000
TAIL_FREE_INSNS = (IMEM_BYTES - TEXT_BYTES) // 4

DMA_GRANULE = 8
LOGICAL_RECORD_BYTES = 4
MAX_COLOR_RECORDS = 20460
MAX_SECTION_MARKERS = 320
EVENT_BYTES_PER_SLOT = 0x18000
EVENT_CAPACITY_4B = EVENT_BYTES_PER_SLOT // LOGICAL_RECORD_BYTES
EVENT_CAPACITY_8B = EVENT_BYTES_PER_SLOT // DMA_GRANULE

# Reclaimed definition-only DMEM after the retired H-COMP scaffold.
CONSUMER_EVENT_CURSOR = 0xEA0
CONSUMER_PAIR_SCRATCH = 0xEA8   # one aligned 8-byte event pair
CONSUMER_WRITE_SCRATCH = 0xEB0  # one aligned 8-byte raw-palette entry
CONSUMER_STATE_END = 0xEB8
VEC_DATA = 0xF70

# The corrected consumer is split across the existing 8-instruction dead
# pre-overlay padding block and resident tail space. One bridge branch is
# included in this count. Marker payload remains live for the future H-COMP
# continuation; this stage does not activate arithmetic.
CONSUMER_INSNS = 29
DEAD_PREFIX_INSNS = 8
SAFE_SUFFIX_PEEPHOLES = 8
PEEPHOLES_REQUIRED = CONSUMER_INSNS - DEAD_PREFIX_INSNS - TAIL_FREE_INSNS

MARKER_META = 0x8000
DEST_OFFSET_MASK = 0x07F8


def rgb555_to_rgba5551(value: int) -> int:
    value &= 0x7FFF
    return (
        ((value & 0x001F) << 11)
        | ((value & 0x03E0) << 1)
        | ((value & 0x7C00) >> 9)
        | 0x0001
    )


def rgba5551_to_rgb555(value: int) -> int:
    return (
        ((value >> 11) & 0x1F)
        | (((value >> 6) & 0x1F) << 5)
        | (((value >> 1) & 0x1F) << 10)
    )


def color_record(index: int, rgb555: int) -> int:
    # High half is already RSP/RDP-ready raw RGBA5551. Low half carries the
    # 8-byte destination offset directly, saving an RSP shift.
    return (rgb555_to_rgba5551(rgb555) << 16) | ((index & 0xFF) << 3)


def marker_record(fixed_rgb555: int) -> int:
    # bit15 in metadata is impossible for a palette offset (max 0x7F8).
    return (rgb555_to_rgba5551(fixed_rgb555) << 16) | MARKER_META


def decode_record(record: int) -> tuple[str, int, int]:
    payload = (record >> 16) & 0xFFFF
    meta = record & 0xFFFF
    if meta & MARKER_META:
        return "marker", -1, payload
    offset = meta & DEST_OFFSET_MASK
    if offset != meta:
        raise AssertionError(f"unexpected color metadata bits: 0x{meta:04X}")
    return "color", offset >> 3, payload


def prove_rgba_mapping() -> None:
    for rgb in range(0x8000):
        rgba = rgb555_to_rgba5551(rgb)
        if not (rgba & 1):
            raise AssertionError("RGBA5551 alpha bit was not set")
        if rgba5551_to_rgb555(rgba) != rgb:
            raise AssertionError(f"RGB555 mapping is not lossless at 0x{rgb:04X}")


def consume_stream(
    base: list[int],
    stream: tuple[int, ...],
) -> tuple[list[tuple[tuple[int, ...], int]], int]:
    """Mirror aligned-pair DMA consumption, retaining half-pair across markers."""
    raw = [rgb555_to_rgba5551(v) for v in base]
    cursor_bytes = 0
    pair: tuple[int, int] | None = None
    pair_reads = 0
    sections: list[tuple[tuple[int, ...], int]] = []

    while cursor_bytes < len(stream) * LOGICAL_RECORD_BYTES:
        half = cursor_bytes & 0x4
        if half == 0:
            record_index = cursor_bytes // LOGICAL_RECORD_BYTES
            first = stream[record_index]
            second = stream[record_index + 1] if record_index + 1 < len(stream) else 0
            pair = (first, second)
            dma_address = cursor_bytes & ~(DMA_GRANULE - 1)
            if dma_address & (DMA_GRANULE - 1):
                raise AssertionError("event DMA address is not aligned")
            pair_reads += 1
        if pair is None:
            raise AssertionError("second-half record lost its cached DMA pair")

        record = pair[1 if half else 0]
        cursor_bytes += LOGICAL_RECORD_BYTES
        kind, index, payload = decode_record(record)

        if kind == "marker":
            sections.append(
                (
                    tuple(rgba5551_to_rgb555(v) for v in raw),
                    rgba5551_to_rgb555(payload),
                )
            )
            continue

        destination = index * DMA_GRANULE
        if destination & (DMA_GRANULE - 1):
            raise AssertionError("raw palette destination is not 8-byte aligned")
        raw[index] = payload

    expected_reads = (len(stream) + 1) // 2
    if pair_reads != expected_reads:
        raise AssertionError(f"pair cache lost efficiency: {pair_reads=} {expected_reads=}")
    return sections, pair_reads


def prove_stream_semantics() -> int:
    base = [0x0000, 0x0001, 0x1234, 0x7FFF]
    atoms = tuple((i, v) for i, v in product(range(4), range(4)))
    fixed_values = (0x0000, 0x001F, 0x4210, 0x7FFF)
    cases = 0

    for n in range(4):
        for events in product(atoms, repeat=n):
            for cutmask in range(1 << n):
                stream: list[int] = []
                expected: list[tuple[tuple[int, ...], int]] = []
                live = list(base)
                fi = 0
                for i, (index, value) in enumerate(events):
                    live[index] = value & 0x7FFF
                    stream.append(color_record(index, value))
                    if cutmask & (1 << i):
                        fixed = fixed_values[fi % len(fixed_values)]
                        fi += 1
                        stream.append(marker_record(fixed))
                        expected.append((tuple(live), fixed))
                if not stream or not (stream[-1] & MARKER_META):
                    fixed = fixed_values[fi % len(fixed_values)]
                    stream.append(marker_record(fixed))
                    expected.append((tuple(live), fixed))

                got, _ = consume_stream(base, tuple(stream))
                if got != expected:
                    raise AssertionError(
                        f"DMA-pair replay mismatch: {events=} {cutmask=} {got=} {expected=}"
                    )
                cases += 1

    # Explicitly put the first section marker in word0 of an 8-byte pair.
    # The next section's first color is word1 of that same pair and therefore
    # must survive the section return in DMEM without another DMA read.
    stream = (
        marker_record(0x001F),
        color_record(1, 0x1234),
        marker_record(0x4210),
    )
    got, reads = consume_stream([0, 1, 2], stream)
    if got != [
        ((0, 1, 2), 0x001F),
        ((0, 0x1234, 2), 0x4210),
    ]:
        raise AssertionError("explicit first-half-marker cached replay mismatch")
    if reads != 2:
        raise AssertionError("cached second half triggered a redundant DMA")

    return cases


def prove_dma_capacity() -> int:
    total_records = MAX_COLOR_RECORDS + MAX_SECTION_MARKERS
    if total_records != 20780:
        raise AssertionError("record-bound arithmetic drift")
    if EVENT_CAPACITY_8B >= total_records:
        raise AssertionError("8-byte-record rejection is no longer true")
    if EVENT_CAPACITY_8B != 12288:
        raise AssertionError("8-byte record capacity drift")
    if EVENT_CAPACITY_4B != 24576 or total_records >= EVENT_CAPACITY_4B:
        raise AssertionError("packed 4-byte stream no longer fits")
    margin = EVENT_CAPACITY_4B - total_records
    if margin != 3796:
        raise AssertionError(f"packed record margin drift: {margin}")
    # Worst logical stream still leaves enough allocation slack for the final
    # aligned 8-byte pair read, even when the last logical record is odd.
    used = total_records * LOGICAL_RECORD_BYTES
    rounded = (used + DMA_GRANULE - 1) & ~(DMA_GRANULE - 1)
    if rounded > EVENT_BYTES_PER_SLOT:
        raise AssertionError("final aligned pair DMA crosses event allocation")
    return margin


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i)
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def safe_peephole_count(src: str) -> int:
    anchors = (
        "beqz t0, obj_no_windows\n    nop\n\n    lbu a0, WOBJSEL",
        "bltz t8, obj_finish_objects\n    nop\n\n    // Advance by explicit span count",
        "beq t1, t2, color_window_none\n    nop\n\n    // Modes 1/2",
        "beqz t8, color_window_none\n    nop\n\n    // Snapshot all possible span endpoints",
        "bnez t0, color_window_initial_ready\n    nop\n    move a1, s0",
        "beq t8, a1, color_window_tail\n    nop\n\n    addi a1, t2, -1",
        "beq t8, a1, color_window_tail\n    nop\n\n    addi a1, t4, -1",
        "beqz t7, window_new_span\n    nop\n    lbu t2, -1(t6)",
    )
    for anchor in anchors:
        if anchor not in src:
            raise AssertionError(f"missing pre-audited suffix peephole: {anchor!r}")
    return len(anchors)


def prove_dead_prefix_padding(src: str) -> int:
    block = extract(src, "fill_win:", "fill_backdrop:")
    nops = sum(1 for line in block.splitlines() if line.strip() == "nop")
    if nops != DEAD_PREFIX_INSNS:
        raise AssertionError(f"dead pre-overlay padding drift: {nops}")
    # These labels survive only in the legacy DMEM jump table. Current RSP code
    # contains no FILL_JUMPS load/dispatch, so normal control flow branches over
    # the padding directly to fill_backdrop.
    if "FILL_JUMPS" in src:
        raise AssertionError("legacy fill jump table became executable again")
    for symbol in ("fill_win", "fill_notwin"):
        if len(re.findall(rf"\b{symbol}\b", src)) != 2:
            raise AssertionError(f"{symbol} reference count changed")
    if len(re.findall(r"\buse_window\b", src)) != 1:
        raise AssertionError("use_window reference count changed")
    return nops


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
            if len(re.findall(rf"\b{symbol}\b", src)) != 1:
                raise AssertionError(f"{name}: retired DMEM symbol became live: {symbol}")
    if not (
        0xEA0 <= CONSUMER_EVENT_CURSOR
        < CONSUMER_PAIR_SCRATCH
        < CONSUMER_WRITE_SCRATCH
        < CONSUMER_STATE_END
        <= VEC_DATA
    ):
        raise AssertionError("consumer state escapes retired DMEM interval")
    if CONSUMER_PAIR_SCRATCH & 7 or CONSUMER_WRITE_SCRATCH & 7:
        raise AssertionError("consumer DMA scratch is not 8-byte aligned")


def prove_raw_shadow_alignment() -> None:
    ev = base_contract.parse_macros()
    q1 = ev.name("HCOMP_RAW_PALETTE_QUEUE1")
    q2 = ev.name("HCOMP_RAW_PALETTE_QUEUE2")
    if (q1, q2) != (0xA00EF000, 0xA00EF800):
        raise AssertionError(f"raw shadow ABI drift: 0x{q1:X} 0x{q2:X}")
    for base in (q1, q2):
        for index in range(256):
            if (base + index * DMA_GRANULE) & 7:
                raise AssertionError("raw shadow entry lost DMA alignment")


def prove_instruction_budget() -> tuple[int, int]:
    if TAIL_FREE_INSNS != 14:
        raise AssertionError(f"current tail-free instruction count drift: {TAIL_FREE_INSNS}")
    main = (ROOT / "src/rsp_main.S").read_text()
    mode7 = (ROOT / "src/rsp_mode7.S").read_text()

    p_main = safe_peephole_count(main)
    p_mode7 = safe_peephole_count(mode7)
    d_main = prove_dead_prefix_padding(main)
    d_mode7 = prove_dead_prefix_padding(mode7)
    if p_main != SAFE_SUFFIX_PEEPHOLES or p_mode7 != SAFE_SUFFIX_PEEPHOLES:
        raise AssertionError("common suffix peephole budget diverged")
    if d_main != DEAD_PREFIX_INSNS or d_mode7 != DEAD_PREFIX_INSNS:
        raise AssertionError("common dead-prefix budget diverged")

    if PEEPHOLES_REQUIRED != 7:
        raise AssertionError(f"corrected consumer peephole need drift: {PEEPHOLES_REQUIRED}")
    if PEEPHOLES_REQUIRED > SAFE_SUFFIX_PEEPHOLES:
        raise AssertionError("corrected consumer no longer fits resident IMEM")

    maximum = TAIL_FREE_INSNS + DEAD_PREFIX_INSNS + SAFE_SUFFIX_PEEPHOLES
    spare = maximum - CONSUMER_INSNS
    if maximum != 30 or spare != 1:
        raise AssertionError(f"DMA-aware IMEM budget drift: {maximum=} {spare=}")
    return maximum, spare


def prove_current_handoff() -> None:
    ppu = (ROOT / "src/ppu.S").read_text()
    rsp = (ROOT / "src/rsp_main.S").read_text()
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

    ns = extract(rsp, "next_section:", "// Check if this section has an OAM update")
    for anchor in (
        "jal dma_read",
        "li a2, SECTION_SIZE - 1",
        "move k0, k1",
        "lbu k1, SPLIT_LINE",
    ):
        if anchor not in ns:
            raise AssertionError(f"next_section anchor drift: {anchor}")


def main() -> int:
    _, event_capacity, _ = base_contract.prove_layout()
    max_commits, _ = base_contract.prove_timing_capacity(event_capacity)
    if max_commits != MAX_COLOR_RECORDS or event_capacity != EVENT_CAPACITY_4B:
        raise AssertionError("upstream CGRAM capacity authority drift")

    prove_rgba_mapping()
    cases = prove_stream_semantics()
    margin = prove_dma_capacity()
    prove_dead_dmem_reclaim()
    prove_raw_shadow_alignment()
    prove_current_handoff()
    maximum, spare = prove_instruction_budget()

    print("CGRAM_RSP_DMA8_CONSUMER_CONTRACT_VALIDATED")
    print(f"ares_pin={ARES_PIN}")
    print(f"dma_granule={DMA_GRANULE}")
    print("logical_record_bytes=4")
    print("event_dma=aligned_8byte_pair_with_cached_second_half")
    print(f"max_color_records={MAX_COLOR_RECORDS}")
    print(f"max_section_markers={MAX_SECTION_MARKERS}")
    print(f"packed_record_capacity={EVENT_CAPACITY_4B}")
    print(f"eight_byte_record_capacity_rejected={EVENT_CAPACITY_8B}")
    print(f"packed_record_margin={margin}")
    print(f"typed_replay_cases={cases}")
    print("color_payload=raw_rgba5551")
    print("color_meta=raw_shadow_byte_offset")
    print("marker_meta_bit=0x8000")
    print("rgb555_rgba5551_mapping=bijective_all_32768")
    print("consumer_mutates=owned_raw_rgba_shadow")
    print("base_shadow_init=cpu_from_historical_frame_base_required")
    print(f"dead_prefix_instructions={DEAD_PREFIX_INSNS}")
    print(f"tail_free_instructions={TAIL_FREE_INSNS}")
    print(f"safe_suffix_peepholes={SAFE_SUFFIX_PEEPHOLES}")
    print(f"peepholes_required={PEEPHOLES_REQUIRED}")
    print(f"consumer_instructions_required={CONSUMER_INSNS}")
    print(f"consumer_max_instruction_budget={maximum}")
    print(f"consumer_spare_instructions={spare}")
    print("fixed_renderer_slot=must_not_move")
    print("hcomp_arithmetic=still_frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
