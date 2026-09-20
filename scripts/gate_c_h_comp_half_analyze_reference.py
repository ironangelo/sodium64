#!/usr/bin/env python3
"""Analyze ares Super Famicom screenshots for the H-COMP half-add reference."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from PIL import Image


def analyze_frame(path: Path) -> dict[str, object]:
    image = Image.open(path).convert("RGB")
    pixels = list(image.getdata())

    # The ROM's visible field is a large yellow rectangle. Require both red and
    # green, little blue, and near-equal R/G to reject most UI/background pixels.
    yellow = [
        (r, g, b)
        for r, g, b in pixels
        if min(r, g) >= 24
        and b <= 40
        and abs(r - g) <= 28
        and max(r, g) >= b * 2
    ]
    if len(yellow) < 5000:
        return {
            "path": str(path),
            "status": "NO_LARGE_YELLOW_FIELD",
            "yellow_pixels": len(yellow),
        }

    levels = [(r + g) / 2.0 for r, g, _ in yellow]
    return {
        "path": str(path),
        "status": "OK",
        "yellow_pixels": len(yellow),
        "median_level": statistics.median(levels),
        "mean_level": statistics.fmean(levels),
    }


def classify(frames: list[dict[str, object]]) -> str:
    levels = [
        float(frame["median_level"])
        for frame in frames
        if frame.get("status") == "OK"
    ]
    if len(levels) < 4:
        return "REFERENCE_INDETERMINATE"
    low = min(levels)
    high = max(levels)
    # Same guest, same sources, only CGADSUB half changes. A substantial
    # two-level brightness split is sufficient to establish the direct-SNES
    # phase oracle without relying on screenshot scale or host timing.
    if low > 0 and high / low >= 1.45 and (high - low) >= 30:
        return "REFERENCE_CONFIRMS_HALF_ADD_TWO_LEVELS"
    return "REFERENCE_INDETERMINATE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    frames = [analyze_frame(p) for p in sorted(args.frames)]
    result = {
        "classification": classify(frames),
        "frames": frames,
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
