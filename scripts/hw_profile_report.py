#!/usr/bin/env python3
"""Decode a Sodium64 real-N64 M0 profiler SRAM capture.

HW_PROFILE=1 writes a compact S64H header at SRAM offset 0 and the existing
canonical S64P statistical snapshot at offset 0x100. This tool validates the
Road-to-1.0 measurement settings and extracts that S64P payload for the normal
profile_report.py symbolication/classification path.
"""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

HW_MAGIC = 0x53363448  # S64H
PROFILE_MAGIC = 0x53363450  # S64P
HW_VERSION = 1
HEADER_WORDS = 32
HEADER_SIZE = HEADER_WORDS * 4
MIN_DECISION_SAMPLES = 800


@dataclass(frozen=True)
class HardwareCapture:
    capture_format: str
    version: int
    warmup_seconds: int
    measure_seconds: int
    sample_count: int
    sample_interval: int
    profile_size: int
    snapshot_offset: int
    frame_budgets: tuple[int, int, int, int, int]
    skipped_set: int
    apu_clock: int
    audio_set: int
    precision_set: int
    frame_count: int
    sp_status: int
    sp_dma_full: int
    sp_dma_busy: int
    sp_pc_raw: int
    complete: int

    @property
    def sp_pc_meaningful(self) -> bool:
        return bool(self.sp_status & 1)

    @property
    def sp_pc(self) -> int | None:
        return self.sp_pc_raw if self.sp_pc_meaningful else None


def normalize_save(blob: bytes) -> tuple[bytes, str]:
    """Normalize a raw cart save to canonical N64 big-endian word order."""
    if len(blob) < HEADER_SIZE:
        raise ValueError(f"save is only {len(blob)} bytes; need at least {HEADER_SIZE}")

    magic_be = struct.unpack_from(">I", blob, 0)[0]
    if magic_be == HW_MAGIC:
        return blob, "canonical big-endian"

    if len(blob) % 4:
        raise ValueError(
            "bad S64H magic and save size is not divisible by four; cannot test word-swapped format"
        )

    magic_le = struct.unpack_from("<I", blob, 0)[0]
    if magic_le == HW_MAGIC:
        normalized = b"".join(
            blob[offset : offset + 4][::-1]
            for offset in range(0, len(blob), 4)
        )
        return normalized, "32-bit word-swapped"

    raise ValueError(
        f"bad hardware capture magic 0x{magic_be:08X}; expected 0x{HW_MAGIC:08X}"
    )


def parse_capture(blob: bytes, *, strict: bool = True) -> tuple[HardwareCapture, bytes]:
    blob, capture_format = normalize_save(blob)
    words = struct.unpack_from(">32I", blob, 0)

    capture = HardwareCapture(
        capture_format=capture_format,
        version=words[1],
        warmup_seconds=words[2],
        measure_seconds=words[3],
        sample_count=words[4],
        sample_interval=words[5],
        profile_size=words[6],
        snapshot_offset=words[7],
        frame_budgets=tuple(words[8:13]),
        skipped_set=words[13],
        apu_clock=words[14],
        audio_set=words[15],
        precision_set=words[16],
        frame_count=words[17],
        sp_status=words[18],
        sp_dma_full=words[19],
        sp_dma_busy=words[20],
        sp_pc_raw=words[21],
        complete=words[22],
    )

    if capture.version != HW_VERSION:
        raise ValueError(f"unsupported S64H version {capture.version}; expected {HW_VERSION}")
    if capture.complete != 1:
        raise ValueError("hardware capture is not marked complete; do not interpret a partial save")
    if capture.snapshot_offset < HEADER_SIZE or capture.snapshot_offset % 4:
        raise ValueError(f"invalid snapshot offset 0x{capture.snapshot_offset:X}")
    if capture.profile_size < 32 or capture.snapshot_offset + capture.profile_size > len(blob):
        raise ValueError(
            f"snapshot range 0x{capture.snapshot_offset:X}+0x{capture.profile_size:X} "
            f"does not fit save size 0x{len(blob):X}"
        )

    snapshot = blob[
        capture.snapshot_offset : capture.snapshot_offset + capture.profile_size
    ]
    if len(snapshot) < 4 or struct.unpack_from(">I", snapshot, 0)[0] != PROFILE_MAGIC:
        raise ValueError("embedded statistical snapshot does not begin with canonical S64P magic")

    if strict:
        if capture.warmup_seconds != 2 or capture.measure_seconds != 5:
            raise ValueError(
                "unexpected M0 timing window: "
                f"warmup={capture.warmup_seconds}s measure={capture.measure_seconds}s"
            )
        if capture.sample_count < MIN_DECISION_SAMPLES:
            raise ValueError(
                f"only {capture.sample_count} statistical samples; need at least {MIN_DECISION_SAMPLES}"
            )
        if capture.skipped_set != 0:
            raise ValueError(f"frameskip must be 0, got {capture.skipped_set}")
        if capture.apu_clock != 21:
            raise ValueError(f"full-rate APU requires apu_clock=21, got {capture.apu_clock}")
        if capture.audio_set == 0:
            raise ValueError("audio was disabled during the hardware capture")
        if capture.precision_set != 8:
            raise ValueError(f"M0 package requires precision_set=8, got {capture.precision_set}")

    return capture, snapshot


def render_text(capture: HardwareCapture) -> str:
    budgets = ", ".join(f"{value}/60" for value in capture.frame_budgets)
    if capture.sp_pc_meaningful:
        sp_pc = f"0x{capture.sp_pc_raw:08X} (RSP halted; meaningful)"
    else:
        sp_pc = f"0x{capture.sp_pc_raw:08X} (RSP running; do not interpret PC)"

    return "\n".join(
        [
            "Sodium64 real-N64 M0 capture",
            f"  save format:      {capture.capture_format}",
            f"  window:           {capture.warmup_seconds}s warmup + {capture.measure_seconds}s measured",
            f"  samples:          {capture.sample_count} @ {capture.sample_interval} Count ticks",
            f"  frame budgets:    {budgets}",
            f"  frameskip:        {capture.skipped_set}",
            f"  APU clock:        {capture.apu_clock}",
            f"  audio setting:    {capture.audio_set}",
            f"  precision:        {capture.precision_set}",
            f"  queue at capture: {capture.frame_count}",
            f"  SP status:        0x{capture.sp_status:08X}",
            f"  SP DMA full/busy: {capture.sp_dma_full}/{capture.sp_dma_busy}",
            f"  SP PC:            {sp_pc}",
            f"  S64P payload:     0x{capture.profile_size:X} bytes @ save+0x{capture.snapshot_offset:X}",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path, help="raw SummerCart/N64 SRAM save file")
    parser.add_argument(
        "--snapshot-output",
        type=Path,
        help="write the embedded canonical S64P snapshot to this path",
    )
    parser.add_argument("--json-output", type=Path, help="optional parsed capture JSON")
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="parse provenance/debug captures without enforcing M0 Road settings",
    )
    args = parser.parse_args()

    capture, snapshot = parse_capture(args.save.read_bytes(), strict=not args.no_strict)
    print(render_text(capture), end="")

    if args.snapshot_output:
        args.snapshot_output.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot_output.write_bytes(snapshot)

    if args.json_output:
        payload = asdict(capture)
        payload["frame_budgets"] = list(capture.frame_budgets)
        payload["sp_pc_meaningful"] = capture.sp_pc_meaningful
        payload["sp_pc"] = capture.sp_pc
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, struct.error) as exc:
        raise SystemExit(f"error: {exc}")
