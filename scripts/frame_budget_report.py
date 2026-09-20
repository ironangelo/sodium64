#!/usr/bin/env python3
"""Summarize Sodium64 frame-budget observations captured through GDB.

The values come from Sodium64's own runtime counters inside the emulated N64.
They are useful for Phase 1 because they compare completed SNES frames against
N64 VI cadence without using the host PC's wall-clock throughput. They remain an
emulator-lab result; real N64 hardware is the authority for final performance.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


FPS_SENTINEL = 0xFF
REQUIRED_OBSERVATIONS = {
    "fps_display",
    "fps_native",
    "fps_emulate",
    "frame_count",
    "skipped_set",
    "apu_clock",
    "audio_set",
    "precision_set",
}


@dataclass(frozen=True)
class BudgetRow:
    label: str
    measured_wall_seconds: float
    fps_display: int
    fps_native: int
    fps_emulate: int
    frame_count: int
    skipped_set: int
    apu_clock: int
    audio_set: int
    precision_set: int
    target_fps: int

    @property
    def full_interval_percent(self) -> float:
        return self.fps_display * 100.0 / self.target_fps

    @property
    def cadence_status(self) -> str:
        if self.fps_display >= self.target_fps:
            return "at/above virtual target"
        return "below virtual target"


def label_from_path(path: Path) -> str:
    name = path.stem
    if name.endswith("-state"):
        name = name[: -len("-state")]
    return name


def load_budget_row(path: Path, target_fps: int) -> BudgetRow:
    payload = json.loads(path.read_text(encoding="utf-8"))
    observations = payload.get("observations")
    if not isinstance(observations, dict):
        raise ValueError(f"{path}: missing observations object")

    missing = sorted(REQUIRED_OBSERVATIONS - observations.keys())
    if missing:
        raise ValueError(f"{path}: missing observations: {', '.join(missing)}")

    values = {name: int(observations[name]) for name in REQUIRED_OBSERVATIONS}
    if values["fps_display"] == FPS_SENTINEL:
        raise ValueError(
            f"{path}: fps_display is still sentinel 0xFF; no complete 60-VI budget "
            "window was observed after measurement reset"
        )
    if values["skipped_set"] != 0:
        raise ValueError(
            f"{path}: frameskip must be disabled for Road-to-1.0 profiling "
            f"(skipped_set={values['skipped_set']})"
        )
    if values["apu_clock"] != 21:
        raise ValueError(
            f"{path}: APU must run at full rate (apu_clock=21, got {values['apu_clock']})"
        )
    if values["audio_set"] == 0:
        raise ValueError(f"{path}: audio is disabled during a frame-budget measurement")
    if target_fps <= 0:
        raise ValueError("target_fps must be positive")

    return BudgetRow(
        label=label_from_path(path),
        measured_wall_seconds=float(payload.get("measured_wall_seconds", 0.0)),
        fps_display=values["fps_display"],
        fps_native=values["fps_native"],
        fps_emulate=values["fps_emulate"],
        frame_count=values["frame_count"],
        skipped_set=values["skipped_set"],
        apu_clock=values["apu_clock"],
        audio_set=values["audio_set"],
        precision_set=values["precision_set"],
        target_fps=target_fps,
    )


def render_markdown(rows: list[BudgetRow]) -> str:
    lines = [
        "| workload | last complete VI window | virtual budget | partial VI window | partial guest frames | queue | precision | lab wall s |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.label} | {row.fps_display}/{row.target_fps} | "
            f"{row.full_interval_percent:.1f}% ({row.cadence_status}) | "
            f"{row.fps_native}/60 | {row.fps_emulate} | {row.frame_count} | "
            f"{row.precision_set} | {row.measured_wall_seconds:g} |"
        )
    lines.extend(
        [
            "",
            "> `lab wall s` is only the duration on the CI host. It is not real-N64 performance. "
            "The frame-budget signal comes from Sodium64's own `fps_display` counter inside the "
            "emulated N64: completed emulated frames per 60 VI interrupts.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("states", nargs="+", type=Path, help="GDB state JSON files")
    parser.add_argument("--target-fps", type=int, default=60)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = [load_budget_row(path, args.target_fps) for path in args.states]
    markdown = render_markdown(rows)
    print(markdown, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"error: {exc}")
