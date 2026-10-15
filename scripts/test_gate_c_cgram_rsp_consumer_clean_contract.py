#!/usr/bin/env python3
"""Clean-lineage L0 contract for reusing the validated DMA8 CGRAM consumer.

This is deliberately host-only.  It bridges:
  * current integrated master RSP layout/capacity,
  * the exact dynamically-validated clean CPU producer,
  * the historically validated 29-instruction DMA8 RSP consumer format.

It does not change Sodium64 runtime code and does not activate H-COMP arithmetic.
"""

from __future__ import annotations

import argparse
import ast
from itertools import combinations_with_replacement, product
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

MASTER_AUTHORITY = "70d8d8b594c926a7179c43a25c0dfb829745b7cd"
PRODUCER_AUTHORITY = "8dce5f45e6278356172b24576053a66ccf5f6daf"
ARES_PIN = "17813a3ccda21ab9bd45f09bfc2f91196dbf50ff"

DMA_GRANULE = 8
LOGICAL_RECORD_BYTES = 4
CGRAM_ENTRIES = 256
RAW_ENTRY_BYTES = 8
RAW_SHADOW_BYTES = CGRAM_ENTRIES * RAW_ENTRY_BYTES

MAX_COLOR_RECORDS = 20460
MAX_SECTION_MARKERS = 320

CURRENT_RSP_TEXT_BYTES = 0xFC8
RSP_IMEM_BYTES = 0x1000
TAIL_FREE_INSNS = (RSP_IMEM_BYTES - CURRENT_RSP_TEXT_BYTES) // 4
DEAD_PREFIX_INSNS = 8
SAFE_SUFFIX_PEEPHOLES = 8
HISTORICAL_CONSUMER_INSNS = 29
PEEPHOLES_REQUIRED = HISTORICAL_CONSUMER_INSNS - DEAD_PREFIX_INSNS - TAIL_FREE_INSNS

CONSUMER_EVENT_CURSOR = 0xEA0
CONSUMER_PAIR_SCRATCH = 0xEA8
CONSUMER_WRITE_SCRATCH = 0xEB0
CONSUMER_STATE_END = 0xEB8
VEC_DATA = 0xF70

MARKER_META = 0x8000
DEST_OFFSET_MASK = 0x07F8

EXPECTED_LAYOUT = {
    "HCOMP_CGRAM_BASE_QUEUE1": 0xA00C2000,
    "HCOMP_CGRAM_BASE_QUEUE2": 0xA00C2200,
    "HCOMP_CGRAM_SIDEBAND_QUEUE1": 0xA00C2400,
    "HCOMP_CGRAM_SIDEBAND_QUEUE2": 0xA00C2900,
    "HCOMP_CGRAM_EVENT_QUEUE1": 0xA00C2E00,
    "HCOMP_CGRAM_EVENT_QUEUE2": 0xA03E8000,
    "HCOMP_CGRAM_EVENT_CAPACITY": 0x6000,
}
RAW_Q1 = 0xA00EF000
RAW_Q2 = RAW_Q1 + RAW_SHADOW_BYTES
RAW_END = RAW_Q2 + RAW_SHADOW_BYTES
EXPECTED_FRAMEBUFFER1 = 0xA00F2300


class MacroEval(ast.NodeVisitor):
    def __init__(self, macros: dict[str, str]):
        self.macros = macros
        self.cache: dict[str, int] = {}

    def name(self, name: str) -> int:
        if name in self.cache:
            return self.cache[name]
        if name not in self.macros:
            raise AssertionError(f"unknown macro {name}")
        value = self.visit(ast.parse(self.macros[name], mode="eval").body)
        self.cache[name] = value
        return value

    def visit_Constant(self, node: ast.Constant) -> int:
        if not isinstance(node.value, int):
            raise AssertionError(f"non-integer macro value {node.value!r}")
        return node.value

    def visit_Name(self, node: ast.Name) -> int:
        return self.name(node.id)

    def visit_BinOp(self, node: ast.BinOp) -> int:
        left, right = self.visit(node.left), self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.LShift):
            return left << right
        if isinstance(node.op, ast.RShift):
            return left >> right
        raise AssertionError(f"unsupported macro operator {ast.dump(node.op)}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> int:
        value = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.Invert):
            return ~value
        raise AssertionError(f"unsupported unary macro operator {ast.dump(node.op)}")

    def generic_visit(self, node):
        raise AssertionError(f"unsupported macro expression {ast.dump(node)}")


def parse_macros(root: Path) -> MacroEval:
    text = (root / "src" / "defines.h").read_text()
    macros: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^#define\s+([A-Z][A-Z0-9_]*)\s+(.+?)\s*$", line)
        if m:
            macros[m.group(1)] = m.group(2).split("//", 1)[0].strip()
    return MacroEval(macros)


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i + len(start))
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


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


def producer_record(index: int, rgb555: int) -> int:
    return ((index & 0xFF) << 24) | (rgb555 & 0x7FFF)


def decode_producer_record(record: int) -> tuple[int, int]:
    if record & 0x00FF8000:
        raise AssertionError(f"producer reserved/high RGB bits set: 0x{record:08X}")
    return (record >> 24) & 0xFF, record & 0x7FFF


def color_record(index: int, rgb555: int) -> int:
    return (rgb555_to_rgba5551(rgb555) << 16) | ((index & 0xFF) << 3)


def marker_record(fixed_rgb555: int) -> int:
    return (rgb555_to_rgba5551(fixed_rgb555) << 16) | MARKER_META


def decode_typed_record(record: int) -> tuple[str, int, int]:
    payload = (record >> 16) & 0xFFFF
    meta = record & 0xFFFF
    if meta & MARKER_META:
        if meta != MARKER_META:
            raise AssertionError(f"marker metadata drift: 0x{meta:04X}")
        return "marker", -1, payload
    if meta & ~DEST_OFFSET_MASK:
        raise AssertionError(f"unexpected color metadata bits: 0x{meta:04X}")
    return "color", (meta & DEST_OFFSET_MASK) >> 3, payload


def producer_replay(
    base: tuple[int, ...],
    events: tuple[tuple[int, int], ...],
    count: int,
) -> tuple[int, ...]:
    if not 0 <= count <= len(events):
        raise AssertionError("invalid cumulative event count")
    state = [v & 0x7FFF for v in base]
    for index, value in events[:count]:
        state[index] = value & 0x7FFF
    return tuple(state)


def transform_validated_producer(
    base: tuple[int, ...],
    events: tuple[tuple[int, int], ...],
    sidebands: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Convert base+events+cumulative sideband to old consumer's typed stream."""
    if not sidebands:
        raise AssertionError("a handed frame must have at least one section marker")

    raw = tuple(rgb555_to_rgba5551(v) for v in base)
    stream: list[int] = []
    previous = 0
    for count, fixed in sidebands:
        if not previous <= count <= len(events):
            raise AssertionError(
                f"non-monotonic/out-of-range sideband count: {previous=} {count=}"
            )
        for index, value in events[previous:count]:
            stream.append(color_record(index, value))
        stream.append(marker_record(fixed))
        previous = count

    if previous != len(events):
        raise AssertionError(
            f"terminal section does not cover final producer events: {previous=} {len(events)=}"
        )
    return raw, tuple(stream)


def consume_typed_stream(
    raw_base: tuple[int, ...],
    stream: tuple[int, ...],
) -> tuple[list[tuple[tuple[int, ...], int]], int]:
    """Mirror aligned 8-byte pair DMA with cached second-half semantics."""
    raw = list(raw_base)
    cursor = 0
    pair: tuple[int, int] | None = None
    pair_reads = 0
    sections: list[tuple[tuple[int, ...], int]] = []

    while cursor < len(stream) * LOGICAL_RECORD_BYTES:
        half = cursor & 0x4
        if half == 0:
            record_index = cursor // LOGICAL_RECORD_BYTES
            first = stream[record_index]
            second = stream[record_index + 1] if record_index + 1 < len(stream) else 0
            pair = (first, second)
            if cursor & (DMA_GRANULE - 1):
                raise AssertionError("event DMA address lost 8-byte alignment")
            pair_reads += 1
        if pair is None:
            raise AssertionError("cached pair missing")

        record = pair[1 if half else 0]
        cursor += LOGICAL_RECORD_BYTES
        kind, index, payload = decode_typed_record(record)

        if kind == "marker":
            sections.append(
                (
                    tuple(rgba5551_to_rgb555(v) for v in raw),
                    rgba5551_to_rgb555(payload),
                )
            )
            continue

        destination = index * RAW_ENTRY_BYTES
        if destination & (DMA_GRANULE - 1):
            raise AssertionError("raw-shadow destination lost DMA alignment")
        raw[index] = payload

    expected_reads = (len(stream) + 1) // 2
    if pair_reads != expected_reads:
        raise AssertionError(f"pair-cache read drift: {pair_reads=} {expected_reads=}")
    return sections, pair_reads


def prove_rgb_mapping() -> None:
    for rgb in range(0x8000):
        rgba = rgb555_to_rgba5551(rgb)
        if not rgba & 1:
            raise AssertionError("RGBA5551 alpha bit was not set")
        if rgba5551_to_rgb555(rgba) != rgb:
            raise AssertionError(f"RGB555/RGBA5551 mapping failed at 0x{rgb:04X}")


def prove_record_encoding() -> None:
    for index in range(256):
        for rgb in (0x0000, 0x0001, 0x001F, 0x03E0, 0x4210, 0x7C00, 0x7FFF):
            pr = producer_record(index, rgb)
            if decode_producer_record(pr) != (index, rgb):
                raise AssertionError("clean producer record roundtrip failed")
            kind, got_index, payload = decode_typed_record(color_record(index, rgb))
            if kind != "color" or got_index != index:
                raise AssertionError("typed color metadata roundtrip failed")
            if rgba5551_to_rgb555(payload) != rgb:
                raise AssertionError("typed color payload roundtrip failed")

    for fixed in range(0x8000):
        kind, index, payload = decode_typed_record(marker_record(fixed))
        if kind != "marker" or index != -1:
            raise AssertionError("marker classification failed")
        if rgba5551_to_rgb555(payload) != fixed:
            raise AssertionError("marker fixed-color payload failed")


def prove_transform_equivalence() -> int:
    base = (0x0000, 0x0001, 0x1234, 0x7FFF)
    atoms = tuple(product(range(4), range(4)))
    fixed_values = (0x001F, 0x4210, 0x7FFF)
    cases = 0

    # Three section markers deliberately permit repeated cumulative counts.
    # This covers sections with no CGRAM writes as well as markers landing in
    # either half of an aligned DMA pair.
    for n in range(4):
        for events_raw in product(atoms, repeat=n):
            events = tuple((index, value) for index, value in events_raw)
            for c1, c2 in combinations_with_replacement(range(n + 1), 2):
                sidebands = (
                    (c1, fixed_values[0]),
                    (c2, fixed_values[1]),
                    (n, fixed_values[2]),
                )
                if c2 > n:
                    raise AssertionError("test generator escaped event range")
                expected = [
                    (producer_replay(base, events, count), fixed)
                    for count, fixed in sidebands
                ]
                raw, typed = transform_validated_producer(base, events, sidebands)
                got, _ = consume_typed_stream(raw, typed)
                if got != expected:
                    raise AssertionError(
                        f"typed transform mismatch: {events=} {sidebands=} {got=} {expected=}"
                    )
                cases += 1

    # Explicit historical hazard: marker in word0, next section's first color
    # in word1 must remain cached when control returns at the marker.
    stream = (
        marker_record(0x001F),
        color_record(1, 0x1234),
        marker_record(0x4210),
    )
    got, reads = consume_typed_stream(
        tuple(rgb555_to_rgba5551(v) for v in (0, 1, 2)),
        stream,
    )
    if got != [
        ((0, 1, 2), 0x001F),
        ((0, 0x1234, 2), 0x4210),
    ]:
        raise AssertionError("first-half marker cached-pair replay failed")
    if reads != 2:
        raise AssertionError("cached second half caused redundant DMA")

    return cases


def prove_capacity_and_layout(producer_root: Path) -> tuple[int, int, int]:
    ev = parse_macros(producer_root)
    for name, expected in EXPECTED_LAYOUT.items():
        got = ev.name(name)
        if got != expected:
            raise AssertionError(f"producer {name} drift: 0x{got:X} != 0x{expected:X}")

    event_q1 = ev.name("HCOMP_CGRAM_EVENT_QUEUE1")
    event_q2 = ev.name("HCOMP_CGRAM_EVENT_QUEUE2")
    capacity = ev.name("HCOMP_CGRAM_EVENT_CAPACITY")
    event_bytes = capacity * LOGICAL_RECORD_BYTES
    if capacity != 0x6000 or event_bytes != 0x18000:
        raise AssertionError("validated event-slot geometry drift")

    typed_records = MAX_COLOR_RECORDS + MAX_SECTION_MARKERS
    typed_bytes = typed_records * LOGICAL_RECORD_BYTES
    if typed_records != 20780:
        raise AssertionError("worst typed-record count drift")
    if typed_records >= capacity:
        raise AssertionError("typed stream no longer fits producer event slot")
    rounded = (typed_bytes + DMA_GRANULE - 1) & ~(DMA_GRANULE - 1)
    if rounded > event_bytes:
        raise AssertionError("last aligned event-pair DMA crosses slot")

    record_margin = capacity - typed_records
    byte_margin = event_bytes - typed_bytes
    if (record_margin, byte_margin) != (3796, 15184):
        raise AssertionError(f"typed stream margin drift: {record_margin=} {byte_margin=}")

    master_ev = parse_macros(ROOT)
    framebuffer1 = master_ev.name("FRAMEBUFFER1")
    if framebuffer1 != EXPECTED_FRAMEBUFFER1:
        raise AssertionError(f"current FRAMEBUFFER1 drift: 0x{framebuffer1:X}")
    from check_event_arena import layout, prove_disjoint
    prove_disjoint(layout(producer_root / "src/defines.h"))
    if RAW_Q1 & 7 or RAW_Q2 & 7 or RAW_END & 7:
        raise AssertionError("raw-shadow queues lost 8-byte alignment")
    if RAW_END > framebuffer1:
        raise AssertionError("raw shadows overlap FRAMEBUFFER1")
    framebuffer_guard = framebuffer1 - RAW_END
    if framebuffer_guard != 0x2300:
        raise AssertionError(f"raw-shadow framebuffer guard drift: 0x{framebuffer_guard:X}")

    for base in (RAW_Q1, RAW_Q2):
        for index in range(CGRAM_ENTRIES):
            if (base + index * RAW_ENTRY_BYTES) & 7:
                raise AssertionError("raw palette entry lost 8-byte DMA alignment")

    return record_margin, byte_margin, framebuffer_guard


def prove_validated_producer_source(producer_root: Path) -> None:
    ppu = (producer_root / "src" / "ppu.S").read_text()
    main = (producer_root / "src" / "main.S").read_text()
    rsp_main = (producer_root / "src" / "rsp_main.S").read_text()
    rsp_mode7 = (producer_root / "src" / "rsp_mode7.S").read_text()

    if "li t0, HCOMP_CGRAM_BASE_QUEUE1" not in main:
        raise AssertionError("validated producer no longer clears epoch arena")

    begin = extract(ppu, "hcomp_cgram_begin_frame:", ".align 5\nupdate_frame:")
    for anchor in (
        "lbu t0, queue_id",
        "lw t1, hcomp_cgram_base_queues(t0)",
        "lw t2, hcomp_cgram_event_queues(t0)",
        "lw t3, hcomp_cgram_sideband_queues(t0)",
        "sh zero, hcomp_cgram_event_count",
        "sb zero, hcomp_cgram_event_overflow",
        "andi t3, t3, 0x7FFF",
        "sh t3, 0(t1)",
    ):
        if anchor not in begin:
            raise AssertionError(f"validated producer base snapshot drift: {anchor!r}")

    section = extract(ppu, "section_init:", ".align 5\nhcomp_cgram_begin_frame:")
    for anchor in (
        "lhu t0, hcomp_cgram_event_count",
        "lhu t2, coldata",
        "sh t0, 0(t1)",
        "sh t2, 2(t1)",
        "addi t1, t1, 4",
    ):
        if anchor not in section:
            raise AssertionError(f"validated producer sideband drift: {anchor!r}")

    cg = extract(ppu, "write_cgdata:", ".align 5\nwrite_w12sel:")
    for anchor in (
        "andi t4, t1, 0x7FFF",
        "sll t3, t3, 24",
        "or t3, t3, t4",
        "sw t3, 0(t4)",
        "addi t4, t4, 4",
        "sh t2, hcomp_cgram_event_count",
        "li t3, 0x100",
        "sh t3, sect_status",
    ):
        if anchor not in cg:
            raise AssertionError(f"validated producer event drift: {anchor!r}")

    for name, src in (("rsp_main", rsp_main), ("rsp_mode7", rsp_mode7)):
        if "HCOMP_CGRAM_" in src:
            raise AssertionError(f"{name}: producer authority unexpectedly consumes epochs")


def prove_current_master_rsp_budget() -> tuple[int, int]:
    expected_peepholes = (
        "beqz t0, obj_no_windows\n    nop\n\n    lbu a0, WOBJSEL",
        "bltz t8, obj_finish_objects\n    nop\n\n    // Advance by explicit span count",
        "beq t1, t2, color_window_none\n    nop\n\n    // Modes 1/2",
        "beqz t8, color_window_none\n    nop\n\n    // Snapshot all possible span endpoints",
        "bnez t0, color_window_initial_ready\n    nop\n    move a1, s0",
        "beq t8, a1, color_window_tail\n    nop\n\n    addi a1, t2, -1",
        "beq t8, a1, color_window_tail\n    nop\n\n    addi a1, t4, -1",
        "beqz t7, window_new_span\n    nop\n    lbu t2, -1(t6)",
    )

    for name in ("rsp_main.S", "rsp_mode7.S"):
        src = (ROOT / "src" / name).read_text()
        if "HCOMP_CGRAM_" in src:
            raise AssertionError(f"{name}: consumer already exists on supposed clean master")

        block = extract(src, "fill_win:", "fill_backdrop:")
        nops = sum(1 for line in block.splitlines() if line.strip() == "nop")
        if nops != DEAD_PREFIX_INSNS:
            raise AssertionError(f"{name}: dead prefix drift: {nops}")
        if "FILL_JUMPS" in src:
            raise AssertionError(f"{name}: retired FILL_JUMPS became executable")

        for anchor in expected_peepholes:
            if anchor not in src:
                raise AssertionError(f"{name}: historical safe peephole anchor drift")

    if TAIL_FREE_INSNS != 14:
        raise AssertionError(f"tail-free instruction authority drift: {TAIL_FREE_INSNS}")
    if PEEPHOLES_REQUIRED != 7:
        raise AssertionError(f"required peephole count drift: {PEEPHOLES_REQUIRED}")
    if PEEPHOLES_REQUIRED > SAFE_SUFFIX_PEEPHOLES:
        raise AssertionError("historical DMA8 consumer no longer fits current RSP")

    maximum = TAIL_FREE_INSNS + DEAD_PREFIX_INSNS + SAFE_SUFFIX_PEEPHOLES
    spare = maximum - HISTORICAL_CONSUMER_INSNS
    if (maximum, spare) != (30, 1):
        raise AssertionError(f"consumer IMEM budget drift: {maximum=} {spare=}")

    if not (
        0xEA0 <= CONSUMER_EVENT_CURSOR
        < CONSUMER_PAIR_SCRATCH
        < CONSUMER_WRITE_SCRATCH
        < CONSUMER_STATE_END
        <= VEC_DATA
    ):
        raise AssertionError("consumer scratch escapes retired DMEM interval")
    if CONSUMER_PAIR_SCRATCH & 7 or CONSUMER_WRITE_SCRATCH & 7:
        raise AssertionError("consumer scratch lost 8-byte alignment")

    return maximum, spare


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--producer-root", type=Path, required=True)
    ap.add_argument("--producer-sha", required=True)
    args = ap.parse_args()

    if args.producer_sha != PRODUCER_AUTHORITY:
        raise AssertionError(
            f"producer authority drift: {args.producer_sha} != {PRODUCER_AUTHORITY}"
        )

    prove_validated_producer_source(args.producer_root)
    prove_rgb_mapping()
    prove_record_encoding()
    replay_cases = prove_transform_equivalence()
    record_margin, byte_margin, framebuffer_guard = prove_capacity_and_layout(
        args.producer_root
    )
    maximum, spare = prove_current_master_rsp_budget()

    print("CGRAM_RSP_CONSUMER_CLEAN_CONTRACT_VALIDATED")
    print(f"master_authority={MASTER_AUTHORITY}")
    print(f"producer_authority={PRODUCER_AUTHORITY}")
    print(f"ares_pin={ARES_PIN}")
    print("decision=typed_4byte_stream_plus_double_buffered_raw_rgba5551_shadow")
    print("producer_semantics=base_snapshot_plus_raw_events_plus_cumulative_section_sideband")
    print("transform=lossless_to_historical_dma8_consumer_format")
    print(f"transform_replay_cases={replay_cases}")
    print("rgb555_rgba5551_bijection=all_32768")
    print("logical_record_bytes=4")
    print("dma_pair_bytes=8")
    print("pair_second_half=cache_preserved_across_section_marker")
    print(f"max_color_records={MAX_COLOR_RECORDS}")
    print(f"max_section_markers={MAX_SECTION_MARKERS}")
    print("typed_record_capacity=24576")
    print(f"typed_record_margin={record_margin}")
    print(f"typed_byte_margin={byte_margin}")
    print(f"raw_shadow_q1=0x{RAW_Q1:08X}")
    print(f"raw_shadow_q2=0x{RAW_Q2:08X}")
    print(f"raw_shadow_framebuffer_guard={framebuffer_guard}")
    print(f"consumer_instruction_budget={maximum}")
    print(f"historical_consumer_instructions={HISTORICAL_CONSUMER_INSNS}")
    print(f"consumer_spare_instructions={spare}")
    print("suffix_peepholes_available=8")
    print("suffix_peepholes_required=7")
    print("sideband_direct_rsp_consumer=not_selected_not_proven_impossible")
    print("next_runtime_step=transform_clean_cpu_producer_to_typed_stream_and_raw_shadow")
    print("hcomp_arithmetic=frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
