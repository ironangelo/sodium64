#!/usr/bin/env python3
"""L0 contract proof for lossless mid-frame CGRAM/fixed-color epochs.

No runtime code is changed here. The proof establishes that the proposed
base-snapshot + append-only event-log + per-section sideband representation:
  * fits the measured current base-N64 memory gap,
  * cannot overflow under the pinned ares bulk-transfer timing bound,
  * reconstructs exact palette state at every section prefix,
  * preserves repeated writes and CGRAM entry 0,
  * carries raw fixed color alongside the palette epoch.

Pinned reference:
  ares 17813a3ccda21ab9bd45f09bfc2f91196dbf50ff
  ppu/counter/inline.hpp: active hperiod <= 1364 clocks
  ppu-performance/io.cpp: overscan vdisp=240; CGDATA commits on second byte
  cpu/dma.cpp: each DMA byte transfer consumes at least 8 master clocks
"""

from __future__ import annotations

import ast
from itertools import product
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ARES_PIN = "17813a3ccda21ab9bd45f09bfc2f91196dbf50ff"

# Exact clean current-master artifact 10910596166 / 32339fed.
MEASURED_ELF_END = 0x800BC140

# Proposed KSEG1 layout. Intervals are [start,end).
BASE_Q1 = (0xA00BE200, 0xA00BE400)
BASE_Q2 = (0xA00BE400, 0xA00BE600)
SIDEBAND_Q1 = (0xA00BE600, 0xA00BEB00)
SIDEBAND_Q2 = (0xA00BEB00, 0xA00BF000)
EVENT_Q1 = (0xA00BF000, 0xA00D7000)
EVENT_Q2 = (0xA00D7000, 0xA00EF000)

EVENT_RECORD_SIZE = 4
SECTION_SIDEBAND_SIZE = 4
CGRAM_BYTES = 0x200

# Pinned-ares conservative active-display throughput bound.
MAX_ACTIVE_LINES = 240
MAX_ACTIVE_HPERIOD = 1364
DMA_CLOCKS_PER_BYTE = 8
CGDATA_BYTES_PER_COMMIT = 2


class MacroEval(ast.NodeVisitor):
    def __init__(self, macros: dict[str, str]):
        self.macros = macros
        self.cache: dict[str, int] = {}

    def name(self, name: str) -> int:
        if name in self.cache:
            return self.cache[name]
        if name not in self.macros:
            raise AssertionError(f"unknown macro in layout expression: {name}")
        node = ast.parse(self.macros[name], mode="eval")
        value = self.visit(node.body)
        self.cache[name] = value
        return value

    def visit_Constant(self, node: ast.Constant) -> int:
        if not isinstance(node.value, int):
            raise AssertionError(f"non-integer macro constant: {node.value!r}")
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
        raise AssertionError(f"unsupported macro operator: {ast.dump(node.op)}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> int:
        value = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.Invert):
            return ~value
        raise AssertionError(f"unsupported macro unary op: {ast.dump(node.op)}")

    def generic_visit(self, node):
        raise AssertionError(f"unsupported macro expression: {ast.dump(node)}")


def parse_macros() -> MacroEval:
    text = (ROOT / "src/defines.h").read_text()
    macros: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^#define\s+([A-Z][A-Z0-9_]*)\s+(.+?)\s*$", line)
        if m:
            macros[m.group(1)] = m.group(2).split("//", 1)[0].strip()
    return MacroEval(macros)


def size(interval: tuple[int, int]) -> int:
    return interval[1] - interval[0]


def cached(address: int) -> int:
    if not 0xA0000000 <= address < 0xC0000000:
        raise AssertionError(f"expected KSEG1 address, got 0x{address:08X}")
    return address - 0x20000000


def prove_layout() -> tuple[int, int, int]:
    ev = parse_macros()
    framebuffer1 = ev.name("FRAMEBUFFER1")
    section_q1 = ev.name("SECTION_QUEUE1")
    section_q2 = ev.name("SECTION_QUEUE2")
    section_size = ev.name("SECTION_SIZE")

    # The clean master has no H-COMP raw-palette reservation. Keep the proven
    # epoch geometry below 0xA00EF000 and independently require a guard gap
    # before the actual first framebuffer rather than depending on old macros.
    if framebuffer1 != 0xA00F2300:
        raise AssertionError(f"FRAMEBUFFER1 drift: 0x{framebuffer1:X}")
    if section_q2 - section_q1 != 0x5000:
        raise AssertionError("section queue size drift")
    if section_size != 0x40:
        raise AssertionError("SECTION_SIZE drift")

    section_capacity = (section_q2 - section_q1) // section_size
    if section_capacity != 320:
        raise AssertionError(f"unexpected section capacity {section_capacity}")

    intervals = [BASE_Q1, BASE_Q2, SIDEBAND_Q1, SIDEBAND_Q2, EVENT_Q1, EVENT_Q2]
    if intervals != sorted(intervals):
        raise AssertionError("proposed CGRAM intervals are not ordered")
    for left, right in zip(intervals, intervals[1:]):
        if left[1] > right[0]:
            raise AssertionError(f"layout overlap: {left} {right}")

    if size(BASE_Q1) != CGRAM_BYTES or size(BASE_Q2) != CGRAM_BYTES:
        raise AssertionError("base snapshot is not exactly 256 RGB555 words")
    if size(SIDEBAND_Q1) != section_capacity * SECTION_SIDEBAND_SIZE:
        raise AssertionError("Q1 sideband does not match section capacity")
    if size(SIDEBAND_Q2) != section_capacity * SECTION_SIDEBAND_SIZE:
        raise AssertionError("Q2 sideband does not match section capacity")
    if EVENT_Q2[1] != 0xA00EF000:
        raise AssertionError("event high-water drift")
    if EVENT_Q1[0] != BASE_Q1[0] + 2*CGRAM_BYTES + 2*section_capacity*SECTION_SIDEBAND_SIZE:
        raise AssertionError("unexpected hole/overlap before event queues")
    if EVENT_Q2[1] > framebuffer1:
        raise AssertionError("epoch event area overlaps FRAMEBUFFER1")

    lowest_cached = cached(BASE_Q1[0])
    high_cached = cached(EVENT_Q2[1])
    total_gap = high_cached - MEASURED_ELF_END
    headroom = lowest_cached - MEASURED_ELF_END
    framebuffer_guard = framebuffer1 - EVENT_Q2[1]
    if total_gap != 0x32EC0:
        raise AssertionError(f"measured free-gap arithmetic changed: 0x{total_gap:X}")
    if headroom != 0x20C0:
        raise AssertionError(f"proposed low-water headroom changed: 0x{headroom:X}")
    if framebuffer_guard != 0x3300:
        raise AssertionError(f"unexpected framebuffer guard: 0x{framebuffer_guard:X}")
    if headroom <= 0:
        raise AssertionError("proposed layout collides with current ELF")

    event_capacity = size(EVENT_Q1) // EVENT_RECORD_SIZE
    if size(EVENT_Q1) != size(EVENT_Q2) or event_capacity != 24576:
        raise AssertionError("event queue geometry drift")
    if event_capacity > 0xFFFF:
        raise AssertionError("16-bit cumulative section event count is insufficient")

    return section_capacity, event_capacity, headroom, framebuffer_guard


def prove_timing_capacity(event_capacity: int) -> tuple[int, int]:
    active_clocks = MAX_ACTIVE_LINES * MAX_ACTIVE_HPERIOD
    clocks_per_commit = DMA_CLOCKS_PER_BYTE * CGDATA_BYTES_PER_COMMIT
    max_complete_commits = active_clocks // clocks_per_commit

    # This intentionally overestimates real availability: it allocates every
    # active-display master clock to the pinned model's bulk DMA byte path and
    # ignores DMA setup/edge overhead and all other CPU/PPU work.
    if max_complete_commits != 20460:
        raise AssertionError(f"timing arithmetic changed: {max_complete_commits}")
    if max_complete_commits >= event_capacity:
        raise AssertionError(
            f"event queue can overflow: bound={max_complete_commits} capacity={event_capacity}"
        )
    return max_complete_commits, event_capacity - max_complete_commits


def canonical_rgb555(value: int) -> int:
    return value & 0x7FFF


def replay(base: tuple[int, ...], events: tuple[tuple[int, int], ...], count: int) -> tuple[int, ...]:
    if not 0 <= count <= len(events):
        raise AssertionError("invalid cumulative event count")
    state = list(base)
    for index, value in events[:count]:
        state[index] = canonical_rgb555(value)
    return tuple(state)


def prove_replay_equivalence() -> int:
    # Exhaust every length<=4 event stream on a four-entry reduced palette.
    # This covers arbitrary overwrite order, repeated indices and entry0 while
    # keeping the state space finite enough for CI.
    base = (0x0000, 0x0001, 0x1234, 0x7FFF)
    atoms = tuple(product(range(4), range(4)))
    streams = 0

    for length in range(5):
        for flat in product(atoms, repeat=length):
            events = tuple((index, value) for index, value in flat)
            live = list(base)
            if replay(base, events, 0) != tuple(live):
                raise AssertionError("base epoch replay mismatch")

            last_count = 0
            for count, (index, value) in enumerate(events, start=1):
                live[index] = canonical_rgb555(value)
                got = replay(base, events, count)
                if got != tuple(live):
                    raise AssertionError(
                        f"epoch replay mismatch: {events=} {count=} {got=} {tuple(live)=}"
                    )
                if count < last_count:
                    raise AssertionError("section event counts are not monotonic")
                last_count = count
            streams += 1

    if streams != 69905:
        raise AssertionError(f"unexpected exhaustive replay stream count {streams}")

    # Explicitly prove CGDATA high bit cannot contaminate raw RGB555 state.
    for value in range(0x10000):
        if canonical_rgb555(value) != canonical_rgb555(value ^ 0x8000):
            raise AssertionError("RGB555 bit15 canonicalization failed")

    return streams


def apply_coldata(current: int, write: int) -> int:
    intensity = write & 0x1F
    out = current & 0x7FFF
    for channel, enable_bit in ((0, 5), (1, 6), (2, 7)):
        if write & (1 << enable_bit):
            mask = 0x1F << (channel * 5)
            out = (out & ~mask) | (intensity << (channel * 5))
    return out


def prove_fixed_color_sideband() -> int:
    # Full COLDATA write-byte domain over representative edge/interior channel
    # states; channel independence then covers the entire 15-bit state space.
    values = (0, 1, 15, 30, 31)
    cases = 0
    for r, g, b in product(values, repeat=3):
        current = r | (g << 5) | (b << 10)
        for write in range(256):
            got = apply_coldata(current, write)
            intensity = write & 0x1F
            expected = [r, g, b]
            for ch, bit in enumerate((5, 6, 7)):
                if write & (1 << bit):
                    expected[ch] = intensity
            want = expected[0] | expected[1] << 5 | expected[2] << 10
            if got != want:
                raise AssertionError(f"COLDATA mismatch: {current=:04x} {write=:02x}")
            cases += 1

    if cases != 32000:
        raise AssertionError(f"unexpected fixed-color case count {cases}")
    return cases


def prove_source_boundary_contract() -> None:
    ppu = (ROOT / "src/ppu.S").read_text()

    # The L0 design deliberately starts from the known current gap: nonzero
    # CGRAM writes mutate only live cgram[] and create no historical epoch.
    cg = ppu[ppu.index("write_cgdata:"):ppu.index(".align 5\nwrite_w12sel:")]
    for anchor in (
        "sh t1, cgram(t0)",
        "beqz t0, update_fill",
        "jr ra",
    ):
        if anchor not in cg:
            raise AssertionError(f"current CGRAM source contract drift: missing {anchor!r}")

    vb = ppu[ppu.index("vblank_end:"):ppu.index(".align 5\nvcount_irq:")]
    order = [
        vb.index("sh zero, sect_status"),
        vb.index("sh zero, cur_line"),
        vb.index("j section_init"),
    ]
    if order != sorted(order):
        raise AssertionError("vblank_end/first-section ordering drift")

    rsp = ppu[ppu.index("rsp_frame:"):ppu.index(".align 5\n", ppu.index("rsp_frame:")+16)]
    if "jal make_section" not in rsp:
        raise AssertionError("final-frame section contract drift")

    col = ppu[ppu.index("write_coldata:"):ppu.index(".align 5\nwrite_setini:")]
    if "sh t0, coldata" not in col or "j update_fill" not in col:
        raise AssertionError("raw fixed-color source contract drift")

    # Current clean boot clear starts at FRAMEBUFFER1, above the proposed epoch
    # arena. A future producer MUST extend this low-water mark to BASE_Q1 before
    # the first snapshot can be considered initialized.
    main = (ROOT / "src/main.S").read_text()
    clear = main[main.index("li t0, FRAMEBUFFER1"):main.index("clear_vram:") + 64]
    if "li t0, FRAMEBUFFER1" not in clear or "li t1, JIT_BUFFER - 8" not in clear:
        raise AssertionError("clean boot-clear baseline drift")


def main() -> int:
    section_capacity, event_capacity, headroom, framebuffer_guard = prove_layout()
    max_commits, event_margin = prove_timing_capacity(event_capacity)
    replay_streams = prove_replay_equivalence()
    fixed_cases = prove_fixed_color_sideband()
    prove_source_boundary_contract()

    print("CGRAM_EPOCH_CONTRACT_VALIDATED")
    print(f"ares_pin={ARES_PIN}")
    print(f"measured_elf_end=0x{MEASURED_ELF_END:08X}")
    print(f"section_capacity={section_capacity}")
    print(f"event_capacity_per_slot={event_capacity}")
    print(f"max_active_display_commits_bound={max_commits}")
    print(f"event_margin={event_margin}")
    print(f"layout_headroom_bytes={headroom}")
    print(f"framebuffer_guard_bytes={framebuffer_guard}")
    print(f"replay_streams={replay_streams}")
    print(f"fixed_color_cases={fixed_cases}")
    print("entry0=replay_preserved")
    print("repeated_writes=replay_preserved")
    print("rgb555_bit15=canonicalized")
    print("vblank_writes=fold_into_next_base_snapshot")
    print("boot_clear_extension_required=BASE_Q1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
