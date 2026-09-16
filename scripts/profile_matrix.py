#!/usr/bin/env python3
"""Combine Sodium64 JSON profile summaries into a compact comparison table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BUCKETS = [
    "S-CPU interpreter",
    "SNES memory/I/O",
    "APU JIT generated",
    "APU/SPC700 static",
    "DSP/audio",
    "PPU/events/frame prep",
    "DMA/HDMA",
    "RSP/VRAM semaphore wait",
    "RSP wait",
    "frame/VI wait",
    "profiler overhead",
]

SHORT_NAMES = {
    "S-CPU interpreter": "S-CPU",
    "SNES memory/I/O": "Memory/I-O",
    "APU JIT generated": "APU JIT",
    "APU/SPC700 static": "APU static",
    "DSP/audio": "DSP",
    "PPU/events/frame prep": "PPU",
    "DMA/HDMA": "DMA",
    "RSP/VRAM semaphore wait": "VRAM/RSP wait",
    "RSP wait": "RSP wait",
    "frame/VI wait": "VI wait",
    "profiler overhead": "Profiler",
}


def load_summary(path: Path) -> tuple[int, dict[str, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    subsystems = data.get("subsystems", {})
    samples = int(meta.get("valid_samples", 0))
    return samples, {str(key): int(value) for key, value in subsystems.items()}


def format_percentage(count: int, total: int) -> str:
    if total <= 0:
        return "-"
    return f"{count * 100.0 / total:.1f}%"


def render_matrix(paths: list[Path]) -> str:
    rows: list[tuple[str, int, dict[str, int]]] = []
    for path in paths:
        samples, subsystems = load_summary(path)
        rows.append((path.stem, samples, subsystems))

    header = ["profile", "samples"] + [SHORT_NAMES[name] for name in BUCKETS] + ["other"]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] + ["---:"] * (len(header) - 1)) + " |",
    ]

    for label, samples, subsystems in rows:
        known = sum(subsystems.get(bucket, 0) for bucket in BUCKETS)
        other = max(0, samples - known)
        cells = [label, str(samples)]
        cells.extend(format_percentage(subsystems.get(bucket, 0), samples) for bucket in BUCKETS)
        cells.append(format_percentage(other, samples))
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summaries", nargs="+", type=Path, help="profile JSON summaries")
    parser.add_argument("--output", type=Path, help="optional Markdown output path")
    args = parser.parse_args()

    text = render_matrix(args.summaries)
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
