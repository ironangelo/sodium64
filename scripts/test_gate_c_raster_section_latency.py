#!/usr/bin/env python3
"""L0/source proof for raster-sensitive section-boundary latency."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

RASTER_WRITERS = (
    "write_bgmode",
    "write_w12sel",
    "write_w34sel",
    "write_wobjsel",
    "write_wbglog",
    "write_wobjlog",
    "write_tm",
    "write_ts",
    "write_tmw",
    "write_tsw",
    "write_cgwsel",
    "write_cgadsub",
)

ADAPTIVE_CONTROLS = (
    "write_bg1hofs",
    "write_bg1vofs",
    "write_bg2hofs",
    "write_bg2vofs",
    "write_m7a",
    "write_m7b",
)


def adaptive_dirty(status: int) -> int:
    # Big-endian sb 1,sect_status writes the high/dirty byte only.
    return (status & 0x00FF) | 0x0100


def immediate_dirty(_: int) -> int:
    # sh 0x0100,sect_status also clears the low-byte countdown.
    return 0x0100


def run_line(status: int) -> tuple[int, bool]:
    low = status & 0xFF
    if low:
        status -= 1
    emit = status == 0x0100
    return status, emit


def lines_until_emit(status: int) -> int:
    for line in range(1, 300):
        status, emit = run_line(status)
        if emit:
            return line
    raise AssertionError("section did not emit")


def prove_latency_model() -> None:
    # Road-valid precision8 can have a nonzero cooldown; four is the first
    # documented value and is enough to prove the semantic distinction.
    base = 0x0004
    adaptive = lines_until_emit(adaptive_dirty(base))
    immediate = lines_until_emit(immediate_dirty(base))
    if adaptive != 4:
        raise AssertionError(f"adaptive model changed unexpectedly: {adaptive}")
    if immediate != 1:
        raise AssertionError(f"immediate raster state did not emit next line: {immediate}")

    # Immediate writes must dominate any larger residual adaptive cooldown.
    for cooldown in range(1, 256):
        if lines_until_emit(immediate_dirty(cooldown)) != 1:
            raise AssertionError(f"immediate latency failed at cooldown={cooldown}")


def block(src: str, label: str) -> str:
    start = src.find(label + ":")
    if start < 0:
        raise AssertionError(f"missing {label}")
    end = src.find("\n.align 5", start + 1)
    if end < 0:
        end = len(src)
    return src[start:end]


def prove_source_scope() -> None:
    src = (ROOT / "src/ppu.S").read_text()
    defs = (ROOT / "src/defines.h").read_text()

    for label in RASTER_WRITERS:
        body = block(src, label)
        if "update_window_frame" not in body:
            raise AssertionError(f"{label} is not immediate")
        if re.search(r"\bupdate_frame\b", body):
            raise AssertionError(f"{label} still reaches adaptive update_frame")

    # Keep unrelated precision-sensitive work adaptive; this is not a global
    # precision=max rewrite.
    for label in ADAPTIVE_CONTROLS:
        body = block(src, label)
        if "update_frame" not in body:
            raise AssertionError(f"{label} unexpectedly stopped using adaptive update_frame")

    update_window = block(src, "update_window_frame")
    if "li t0, 0x100" not in update_window or "sh t0, sect_status" not in update_window:
        raise AssertionError("immediate helper no longer clears countdown")

    update_fill = block(src, "update_fill")
    if "li t1, 0x100" not in update_fill or "sh t1, sect_status" not in update_fill:
        raise AssertionError("fill-color changes do not clear countdown")

    inidisp = block(src, "write_inidisp")
    for anchor in ("li t1, 0x100", "sh t1, sect_status", "li t2, 0x100", "sh t2, sect_status"):
        if anchor not in inidisp:
            raise AssertionError(f"INIDISP raster anchor missing: {anchor}")

    bright = block(src, "set_bright")
    for anchor in ("lbu t2, brightness", "beq t2, t0, bright_store_done", "li t2, 0x100", "sh t2, sect_status"):
        if anchor not in bright:
            raise AssertionError(f"clean brightness raster anchor missing: {anchor}")
    for forbidden in ("andi t1, t1, 0xE0", "or t1, t1, t0", "sb t1, stat_flags"):
        if forbidden in bright:
            raise AssertionError(
                f"brightness repair unexpectedly packs H-COMP metadata: {forbidden}"
            )

    section_size = re.search(r"#define SECTION_SIZE\s+(0x[0-9A-Fa-f]+|\d+)", defs)
    queue = re.search(r"#define SECTION_QUEUE2 \(OBJECT_CACHE - (0x[0-9A-Fa-f]+|\d+)\)", defs)
    if not section_size or not queue:
        raise AssertionError("section capacity constants not found")
    size = int(section_size.group(1), 0)
    capacity_bytes = int(queue.group(1), 0)
    capacity = capacity_bytes // size
    # Conservative PAL bound: 313 scanlines plus initial/final records.
    # 320 entries therefore still permit one targeted boundary per line.
    required = 315
    if capacity < required:
        raise AssertionError(
            f"section queue cannot hold conservative PAL per-line boundaries: {capacity} < {required}"
        )


def main() -> int:
    prove_latency_model()
    prove_source_scope()
    print("RASTER_SECTION_LATENCY_VALIDATED")
    print("adaptive_example_lines=4")
    print("raster_sensitive_lines=1")
    print("section_capacity=320")
    print("conservative_pal_required=315")
    print("scope=targeted_not_global")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
