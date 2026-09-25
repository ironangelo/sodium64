#!/usr/bin/env python3
"""Source/model oracle for the CPU-side CGRAM epoch producer."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_c_cgram_epoch_contract as contract


def extract(src: str, start: str, end: str) -> str:
    i = src.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = src.find(end, i)
    if j < 0:
        raise AssertionError(f"missing source anchor {end!r}")
    return src[i:j]


def prove_layout_source() -> None:
    ev = contract.parse_macros()
    expected = {
        "HCOMP_CGRAM_BASE_QUEUE1": 0xA00BE200,
        "HCOMP_CGRAM_BASE_QUEUE2": 0xA00BE400,
        "HCOMP_CGRAM_SIDEBAND_QUEUE1": 0xA00BE600,
        "HCOMP_CGRAM_SIDEBAND_QUEUE2": 0xA00BEB00,
        "HCOMP_CGRAM_EVENT_QUEUE1": 0xA00BF000,
        "HCOMP_CGRAM_EVENT_QUEUE2": 0xA00D7000,
        "HCOMP_CGRAM_EVENT_CAPACITY": 0x6000,
    }
    for name, value in expected.items():
        got = ev.name(name)
        if got != value:
            raise AssertionError(f"{name} drift: 0x{got:X} != 0x{value:X}")

    section_capacity, event_capacity, headroom = contract.prove_layout()
    if (section_capacity, event_capacity, headroom) != (320, 24576, 8368):
        raise AssertionError("validated L0 layout no longer matches producer")


def prove_source_contract() -> None:
    ppu = (ROOT / "src/ppu.S").read_text()
    main_src = (ROOT / "src/main.S").read_text()
    main_rsp = (ROOT / "src/rsp_main.S").read_text()
    mode7_rsp = (ROOT / "src/rsp_mode7.S").read_text()

    # The manual epoch arena is below FRAMEBUFFER1, so boot must clear from
    # its true low-water mark or the first produced Q1 base would be undefined.
    clear_block = extract(main_src, "// Clear the complete fixed RDRAM arena", "// Initialize the VI")
    if "li t0, HCOMP_CGRAM_BASE_QUEUE1" not in clear_block:
        raise AssertionError("startup clear does not initialize CGRAM epoch arena")
    if "li t1, JIT_BUFFER - 8" not in clear_block:
        raise AssertionError("startup clear upper bound drift")

    # Producer only: RSP consumption remains frozen.
    for src, name in ((main_rsp, "rsp_main"), (mode7_rsp, "rsp_mode7")):
        if "HCOMP_CGRAM_" in src:
            raise AssertionError(f"{name} consumes CGRAM epoch state too early")

    data = extract(ppu, "pal_queues:", ".align 4\n// Values that control")
    for anchor in (
        "hcomp_cgram_base_queues: .word HCOMP_CGRAM_BASE_QUEUE1, HCOMP_CGRAM_BASE_QUEUE2",
        "hcomp_cgram_sideband_queues: .word HCOMP_CGRAM_SIDEBAND_QUEUE1, HCOMP_CGRAM_SIDEBAND_QUEUE2",
        "hcomp_cgram_event_queues: .word HCOMP_CGRAM_EVENT_QUEUE1, HCOMP_CGRAM_EVENT_QUEUE2",
        "hcomp_cgram_event_ptr: .word HCOMP_CGRAM_EVENT_QUEUE1",
        "hcomp_cgram_sideband_ptr: .word HCOMP_CGRAM_SIDEBAND_QUEUE1",
        "hcomp_cgram_event_count: .hword 0",
        "hcomp_cgram_event_overflow: .byte 0",
    ):
        if anchor not in data:
            raise AssertionError(f"missing producer data anchor: {anchor}")

    vb = extract(ppu, "vblank_end:", ".align 5\nvcount_irq:")
    if "jal hcomp_cgram_begin_frame" not in vb:
        raise AssertionError("vblank_end does not start CGRAM epoch producer")
    if vb.index("jal hcomp_cgram_begin_frame") > vb.index("j section_init"):
        raise AssertionError("base snapshot happens after first section")

    begin = extract(ppu, "hcomp_cgram_begin_frame:", ".align 5\nupdate_frame:")
    for anchor in (
        "lbu t0, queue_id",
        "lw t1, hcomp_cgram_base_queues(t0)",
        "lw t2, hcomp_cgram_event_queues(t0)",
        "lw t3, hcomp_cgram_sideband_queues(t0)",
        "sw t2, hcomp_cgram_event_ptr",
        "sw t3, hcomp_cgram_sideband_ptr",
        "sh zero, hcomp_cgram_event_count",
        "sb zero, hcomp_cgram_event_overflow",
        "andi t3, t3, 0x7FFF",
    ):
        if anchor not in begin:
            raise AssertionError(f"begin-frame contract missing {anchor!r}")

    section = extract(ppu, "section_init:", ".align 5\nhcomp_cgram_begin_frame:")
    sideband_anchors = (
        "lw t1, hcomp_cgram_sideband_ptr",
        "lhu t0, hcomp_cgram_event_count",
        "lhu t2, coldata",
        "sh t0, 0(t1)",
        "sh t2, 2(t1)",
        "addi t1, t1, 4",
        "sw t1, hcomp_cgram_sideband_ptr",
    )
    pos = [section.index(x) for x in sideband_anchors]
    if pos != sorted(pos):
        raise AssertionError("sideband stores are out of order")

    cg = extract(ppu, "write_cgdata:", ".align 5\nwrite_w12sel:")
    required = (
        "sh t1, cgram(t0)",
        "lbu t2, hvbjoy",
        "andi t2, t2, 0x80",
        "bnez t2, cg_epoch_done",
        "lhu t2, hcomp_cgram_event_count",
        "li t3, HCOMP_CGRAM_EVENT_CAPACITY",
        "bge t2, t3, cg_epoch_overflow",
        "srl t3, t0, 1",
        "sll t3, t3, 24",
        "andi t4, t1, 0x7FFF",
        "lw t4, hcomp_cgram_event_ptr",
        "sw t3, 0(t4)",
        "addi t4, t4, 4",
        "sh t2, hcomp_cgram_event_count",
        "li t3, 0x100",
        "sh t3, sect_status",
        "sb t2, hcomp_cgram_event_overflow",
        "beqz t0, update_fill",
    )
    for anchor in required:
        if anchor not in cg:
            raise AssertionError(f"CGDATA producer missing {anchor!r}")

    if cg.index("bge t2, t3, cg_epoch_overflow") > cg.index("sw t3, 0(t4)"):
        raise AssertionError("overflow guard occurs after event write")
    if cg.index("bnez t2, cg_epoch_done") > cg.index("sw t3, 0(t4)"):
        raise AssertionError("VBlank guard occurs after event write")


def simulate_frame_slots(skip_pattern: tuple[bool, ...]) -> tuple[int, ...]:
    """Mirror rsp_frame ownership: non-skipped frames toggle; skipped reuse."""
    queue_id = 0
    producer_slots = []
    for skipped in skip_pattern:
        current = queue_id
        next_slot = current ^ 4
        if not skipped:
            queue_id = next_slot
        # vblank_end begins producing into the post-rsp_frame queue_id.
        producer_slots.append(queue_id)
    return tuple(producer_slots)


def prove_queue_ownership() -> None:
    cases = {
        (False, False, False, False): (4, 0, 4, 0),
        (True, True, True, True): (0, 0, 0, 0),
        (False, True, False, True): (4, 4, 0, 0),
        (True, False, True, False): (0, 4, 4, 0),
    }
    for pattern, expected in cases.items():
        got = simulate_frame_slots(pattern)
        if got != expected:
            raise AssertionError(f"queue ownership mismatch: {pattern=} {got=} {expected=}")


def prove_epoch_model() -> None:
    # VBlank writes become base state; active writes become events. Each section
    # sideband captures the cumulative count and current raw fixed color.
    live = [0, 1, 2, 3]
    live[2] = 0x1234  # VBlank write
    base = tuple(live)
    events: list[tuple[int, int]] = []
    sidebands: list[tuple[int, int]] = []

    fixed = 0x001F
    sidebands.append((len(events), fixed))  # first section

    events.append((1, 0x7FFF))
    live[1] = 0x7FFF
    sidebands.append((len(events), fixed))

    events.append((0, 0x8001))  # entry0 + high-bit canonicalization
    live[0] = 0x0001
    fixed = contract.apply_coldata(fixed, 0x5A)
    sidebands.append((len(events), fixed))

    events.append((1, 0x0002))  # repeated index
    live[1] = 0x0002
    sidebands.append((len(events), fixed))

    last = -1
    for count, raw_fixed in sidebands:
        if count < last:
            raise AssertionError("sideband event counts regressed")
        last = count
        got = contract.replay(base, tuple(events), count)
        # Build the expected state by replaying exactly the same prefix.
        expected = list(base)
        for index, value in events[:count]:
            expected[index] = contract.canonical_rgb555(value)
        if got != tuple(expected):
            raise AssertionError(f"producer epoch replay mismatch at count={count}")
        if not 0 <= raw_fixed <= 0x7FFF:
            raise AssertionError("fixed color sideband escaped RGB555 domain")

    if contract.replay(base, tuple(events), len(events)) != tuple(live):
        raise AssertionError("final producer state is not losslessly reconstructible")


def main() -> int:
    prove_layout_source()
    prove_source_contract()
    prove_queue_ownership()
    prove_epoch_model()
    print("CGRAM_EPOCH_PRODUCER_MODEL_VALIDATED")
    print("queue_ownership=existing_queue_id")
    print("vblank_policy=base_snapshot")
    print("active_cgdata=append_event_plus_next_line_section")
    print("section_sideband=event_count_plus_raw_coldata")
    print("overflow_guard=before_store")
    print("rsp_consumption=frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
