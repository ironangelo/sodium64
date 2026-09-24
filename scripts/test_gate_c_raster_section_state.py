#!/usr/bin/env python3
"""L0 proof for Gate-C raster-sensitive section publication.

This protects the controlled repair that bypasses Sodium64's adaptive section
cooldown for state whose observable effect must begin at the next scanline
boundary in the current scanline-granular renderer. It deliberately does not
claim dot-level timing or mid-frame CGRAM1..255 palette epoch preservation.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PPU = (ROOT / "src/ppu.S").read_text()
DEFINES = (ROOT / "src/defines.h").read_text()
MENU = (ROOT / "src/menu.S").read_text()

PAL_CONSERVATIVE_SCANLINES = 313
FRAME_BOOKENDS = 2

FORCED_HANDLERS = (
    "set_mode",
    "write_w12sel",
    "write_w34sel",
    "write_wobjsel",
    "write_wh0",
    "write_wh1",
    "write_wh2",
    "write_wh3",
    "write_wbglog",
    "write_wobjlog",
    "write_tm",
    "write_ts",
    "write_tmw",
    "write_tsw",
    "write_cgwsel",
    "write_cgadsub",
)


def macro_hex(name: str) -> int:
    m = re.search(rf"^#define\s+{re.escape(name)}\s+0x([0-9A-Fa-f]+)\s*$", DEFINES, re.M)
    if not m:
        raise AssertionError(f"missing literal macro {name}")
    return int(m.group(1), 16)


def extract(start: str, end: str) -> str:
    i = PPU.find(start)
    if i < 0:
        raise AssertionError(f"missing source anchor {start!r}")
    j = PPU.find(end, i + len(start))
    if j < 0:
        raise AssertionError(f"missing source end {end!r}")
    return PPU[i:j]


def next_aligned_block(label: str) -> str:
    token = label + ":"
    i = PPU.find(token)
    if i < 0:
        raise AssertionError(f"missing handler {label}")
    j = PPU.find(".align 5", i + len(token))
    if j < 0:
        j = len(PPU)
    return PPU[i:j]


def prove_capacity() -> int:
    section_size = macro_hex("SECTION_SIZE")
    m = re.search(r"^#define\s+SECTION_QUEUE2\s+\(OBJECT_CACHE\s+-\s+0x([0-9A-Fa-f]+)\)", DEFINES, re.M)
    if not m:
        raise AssertionError("SECTION_QUEUE2 reservation is not a literal OBJECT_CACHE delta")
    queue_bytes = int(m.group(1), 16)
    if "#define SECTION_QUEUE1 (SECTION_QUEUE2 - 0x5000)" not in DEFINES:
        raise AssertionError("SECTION_QUEUE1 reservation no longer matches queue2")

    slots = queue_bytes // section_size
    if queue_bytes % section_size:
        raise AssertionError("section queue is not an integral number of sections")
    if slots != 320:
        raise AssertionError(f"unexpected section capacity: {slots}")
    if PAL_CONSERVATIVE_SCANLINES + FRAME_BOOKENDS > slots:
        raise AssertionError(
            f"one-section-per-line capacity fails: "
            f"{PAL_CONSERVATIVE_SCANLINES + FRAME_BOOKENDS}>{slots}"
        )
    return slots


def precision8_values() -> tuple[int, int, int]:
    if "precision_set: .byte 2 << 2" not in MENU:
        raise AssertionError("default/Road precision index changed")

    m = re.search(
        r"section_vals:\s*\.word\s+"
        r"0x[0-9A-Fa-f]+,\s*0x[0-9A-Fa-f]+,\s*0x([0-9A-Fa-f]+)",
        PPU,
    )
    if not m:
        raise AssertionError("precision8 section tuple not found")
    word = int(m.group(1), 16)
    raw = word.to_bytes(4, "big")
    shift, minimum, increment = raw[1], raw[2], raw[3]
    if (shift, minimum, increment) != (2, 16, 1):
        raise AssertionError(
            f"precision8 tuple drifted: shift={shift} minimum={minimum} increment={increment}"
        )
    return shift, minimum, increment


def prove_delay_model() -> int:
    shift, minimum, increment = precision8_values()

    # Mirrors run_line after the first section: cooldown increments, then its
    # shifted value becomes sect_status low byte. update_frame only sets the
    # high dirty byte, preserving that countdown.
    cooldown = minimum + increment
    adaptive_countdown = cooldown >> shift
    if adaptive_countdown != 4:
        raise AssertionError(f"expected first precision8 adaptive delay=4, got {adaptive_countdown}")

    status = 0x100 | adaptive_countdown
    ticks = 0
    while status != 0x100:
        low = status & 0xFF
        status -= 1 if low else 0
        ticks += 1
        if ticks > 255:
            raise AssertionError("adaptive countdown did not converge")
    if ticks != 4:
        raise AssertionError(f"adaptive dirty state became ready after {ticks}, expected 4")

    forced_status = 0x100
    if forced_status != 0x100:
        raise AssertionError("forced state is not immediately section-ready")
    return adaptive_countdown


def prove_forced_handlers() -> None:
    for label in FORCED_HANDLERS:
        block = next_aligned_block(label)
        if "update_window_frame" not in block:
            raise AssertionError(f"{label} does not route changed state to forced raster boundary")
        if re.search(r"\bupdate_frame\b", block):
            raise AssertionError(f"{label} still contains adaptive update_frame path")

    raster = next_aligned_block("update_window_frame")
    if "li t0, 0x100" not in raster or "sh t0, sect_status" not in raster:
        raise AssertionError("forced raster helper no longer writes exact 0x0100 status")

    inidisp = extract("write_inidisp:", "write_obsel:")
    if "li t1, 0x100" not in inidisp or "sh t1, sect_status" not in inidisp:
        raise AssertionError("force-blank transition is not forced")
    if "li t2, 0x100" not in inidisp or "sh t2, sect_status" not in inidisp:
        raise AssertionError("brightness transition is not forced")

    fill = extract("update_fill:", "rsp_frame:")
    if "li t1, 0x100" not in fill or "sh t1, sect_status" not in fill:
        raise AssertionError("changed backdrop/fixed-color fill is not forced")


def prove_cgram_nonclaim() -> None:
    block = extract("cg_high:", "write_w12sel:")
    if "beqz t0, update_fill" not in block:
        raise AssertionError("CGRAM0 update path changed unexpectedly")
    tail = block.split("beqz t0, update_fill", 1)[1]
    if "jr ra" not in tail:
        raise AssertionError("nonzero CGRAM return path disappeared")
    if "update_window_frame" in tail:
        raise AssertionError(
            "nonzero CGRAM was marked raster-fixed without adding palette epoch storage"
        )


def main() -> int:
    slots = prove_capacity()
    delay = prove_delay_model()
    prove_forced_handlers()
    prove_cgram_nonclaim()

    print("RASTER_SECTION_STATE_VALIDATED")
    print(f"section_slots={slots}")
    print(f"conservative_pal_sections={PAL_CONSERVATIVE_SCANLINES + FRAME_BOOKENDS}")
    print(f"precision8_first_adaptive_delay_lines={delay}")
    print("forced_state_visibility=next_scanline_section")
    print("cgram1_255_epochs=EXPLICITLY_UNRESOLVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
