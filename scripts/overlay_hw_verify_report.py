#!/usr/bin/env python3
"""Decode a Sodium64 PR#13 real-N64 renderer-overlay SRAM capture."""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

MAGIC = 0x5336344F  # S64O
VERSION = 1
TEST_ID = 0x4F564D31  # OVM1
RECORD_SIZE = 0x80
END_MARKER = 0x454E4421
REGULAR_SLOT_WORD = 0x91670E64

OF_PASS = 0x00000001
OF_GUEST_DONE = 0x00000002
OF_SAME_FRAME = 0x00000004
OF_BG_REGULAR = 0x00000008
OF_SP_HALT = 0x00000010
OF_DMA_IDLE = 0x00000020
OF_SLOT_REGULAR = 0x00000040
OF_LOADS_EXACT = 0x00000080
OF_FB_VALID = 0x00000100
OF_REQUIRED = 0x000001FE

VALID_FRAMEBUFFERS = {0xA00F0000, 0xA0113000, 0xA0136000}


@dataclass(frozen=True)
class OverlayCapture:
    capture_format: str
    version: int
    test_id: int
    complete: int
    flags: int
    guest_counter: int
    phase: int
    irq_count: int
    guest_mode: int
    test_done: int
    irq1_frame: int
    irq2_frame: int
    bg_mode: int
    frame_count: int
    sp_status: int
    dma_full: int
    dma_busy: int
    sp_pc: int
    slot_word: int
    mode7_done: int
    main_done: int
    framebuffer: int
    dp_status: int
    expected_slot: int
    checksum: int
    record_size: int
    end_marker: int

    @property
    def passed(self) -> bool:
        return bool(self.flags & OF_PASS)


def normalize_save(blob: bytes) -> tuple[bytes, str]:
    if len(blob) < RECORD_SIZE:
        raise ValueError(f"save is only {len(blob)} bytes; need at least {RECORD_SIZE}")

    if struct.unpack_from(">I", blob, 0)[0] == MAGIC:
        return blob, "canonical big-endian"

    if len(blob) % 4:
        raise ValueError("bad S64O magic and size is not divisible by four")

    if struct.unpack_from("<I", blob, 0)[0] == MAGIC:
        return (
            b"".join(blob[i:i + 4][::-1] for i in range(0, len(blob), 4)),
            "32-bit word-swapped",
        )

    got = struct.unpack_from(">I", blob, 0)[0]
    raise ValueError(f"bad S64O magic 0x{got:08X}; expected 0x{MAGIC:08X}")


def parse_capture(blob: bytes) -> OverlayCapture:
    blob, capture_format = normalize_save(blob)
    words = struct.unpack_from(">32I", blob, 0)

    c = OverlayCapture(
        capture_format=capture_format,
        version=words[1],
        test_id=words[2],
        complete=words[3],
        flags=words[4],
        guest_counter=words[5],
        phase=words[6],
        irq_count=words[7],
        guest_mode=words[8],
        test_done=words[9],
        irq1_frame=words[10],
        irq2_frame=words[11],
        bg_mode=words[12],
        frame_count=words[13],
        sp_status=words[14],
        dma_full=words[15],
        dma_busy=words[16],
        sp_pc=words[17],
        slot_word=words[18],
        mode7_done=words[19],
        main_done=words[20],
        framebuffer=words[21],
        dp_status=words[22],
        expected_slot=words[23],
        checksum=words[24],
        record_size=words[25],
        end_marker=words[26],
    )

    if c.version != VERSION:
        raise ValueError(f"unsupported S64O version {c.version}; expected {VERSION}")
    if c.test_id != TEST_ID:
        raise ValueError(f"wrong S64O test id 0x{c.test_id:08X}; expected OVM1")
    if c.complete != 1:
        raise ValueError("S64O capture is not marked complete")
    if c.record_size != RECORD_SIZE:
        raise ValueError(f"wrong S64O record size 0x{c.record_size:X}")
    if c.end_marker != END_MARKER:
        raise ValueError(f"bad S64O end marker 0x{c.end_marker:08X}")
    if c.expected_slot != REGULAR_SLOT_WORD:
        raise ValueError(
            f"wrong expected regular slot 0x{c.expected_slot:08X}; "
            f"expected 0x{REGULAR_SLOT_WORD:08X}"
        )

    checksum = 0
    for index, word in enumerate(words):
        if index != 24:
            checksum ^= word
    if checksum != c.checksum:
        raise ValueError(
            f"S64O checksum mismatch: stored=0x{c.checksum:08X} "
            f"computed=0x{checksum:08X}"
        )

    expected_flags = 0
    if (
        c.phase == 0x33
        and c.irq_count == 2
        and c.guest_mode == 1
        and c.test_done == 1
    ):
        expected_flags |= OF_GUEST_DONE
    if c.irq1_frame == 30 and c.irq2_frame == 30:
        expected_flags |= OF_SAME_FRAME
    if c.bg_mode == 1:
        expected_flags |= OF_BG_REGULAR
    if c.sp_status & 1:
        expected_flags |= OF_SP_HALT
    if c.dma_full == 0 and c.dma_busy == 0:
        expected_flags |= OF_DMA_IDLE
    if c.slot_word == REGULAR_SLOT_WORD:
        expected_flags |= OF_SLOT_REGULAR
    if c.mode7_done == 1 and c.main_done == 1:
        expected_flags |= OF_LOADS_EXACT
    if c.framebuffer in VALID_FRAMEBUFFERS:
        expected_flags |= OF_FB_VALID

    recorded_required = c.flags & OF_REQUIRED
    if recorded_required != expected_flags:
        raise ValueError(
            "S64O flags disagree with recorded observations: "
            f"recorded=0x{recorded_required:03X} recomputed=0x{expected_flags:03X}"
        )

    if c.passed != (expected_flags == OF_REQUIRED):
        raise ValueError("PASS flag is inconsistent with the recorded overlay evidence")

    return c


def render_text(c: OverlayCapture) -> str:
    return (
        "Sodium64 real-N64 PR#13 overlay capture\n"
        f"  save format:       {c.capture_format}\n"
        f"  test/version:      OVM1 / {c.version}\n"
        f"  result:            {'PASS' if c.passed else 'FAIL'}\n"
        f"  guest:             counter={c.guest_counter} phase=0x{c.phase:02X} "
        f"irq_count={c.irq_count} mode={c.guest_mode} done={c.test_done}\n"
        f"  IRQ frame IDs:     {c.irq1_frame} / {c.irq2_frame}\n"
        f"  Sodium64 BGMODE:   {c.bg_mode}\n"
        f"  SP:                status=0x{c.sp_status:08X} "
        f"dma_full={c.dma_full} dma_busy={c.dma_busy} pc=0x{c.sp_pc:08X}\n"
        f"  overlay slot:      0x{c.slot_word:08X} "
        f"(expected regular 0x{REGULAR_SLOT_WORD:08X})\n"
        f"  completed loads:   Mode7={c.mode7_done} regular={c.main_done}\n"
        f"  framebuffer:       0x{c.framebuffer:08X}\n"
        f"  DP status:         0x{c.dp_status:08X}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    capture = parse_capture(args.save.read_bytes())
    if args.json:
        print(json.dumps(asdict(capture) | {"passed": capture.passed}, indent=2))
    else:
        print(render_text(capture), end="")
    return 0 if capture.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
