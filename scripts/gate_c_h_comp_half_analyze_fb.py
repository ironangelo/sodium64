#!/usr/bin/env python3
"""Analyze raw Sodium64 framebuffers for the Gate-C H-COMP half-add diagnostic."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

WIDTH = 280
HEIGHT = 240
EXPECTED_BYTES = WIDTH * HEIGHT * 2
CONTROL_EXPECTED = (16, 16, 0)
TREATMENT_EXPECTED = (8, 8, 0)

# The diagnostic fills the whole SNES field. Stay far from Sodium64 borders.
X0, X1 = 96, 184
Y0, Y1 = 72, 168


def decode_rgb5(data: bytes) -> list[tuple[int, int, int]]:
    if len(data) != EXPECTED_BYTES:
        raise ValueError(f"expected {EXPECTED_BYTES} bytes, got {len(data)}")
    out = []
    for i in range(0, len(data), 2):
        value = (data[i] << 8) | data[i + 1]
        out.append(((value >> 11) & 31, (value >> 6) & 31, (value >> 1) & 31))
    return out


def central_mode(path: Path) -> dict[str, object]:
    pixels = decode_rgb5(path.read_bytes())
    crop = []
    for y in range(Y0, Y1):
        row = y * WIDTH
        crop.extend(pixels[row + X0 : row + X1])
    counts = Counter(crop)
    color, count = counts.most_common(1)[0]
    return {
        "path": str(path),
        "mode_rgb5": list(color),
        "mode_pixels": count,
        "crop_pixels": len(crop),
        "mode_fraction": count / len(crop),
        "top_colors": [
            {"rgb5": list(rgb), "count": n}
            for rgb, n in counts.most_common(8)
        ],
    }


def classify(control: dict[str, object], treatment: dict[str, object]) -> str:
    c = tuple(int(x) for x in control["mode_rgb5"])
    t = tuple(int(x) for x in treatment["mode_rgb5"])
    if c == CONTROL_EXPECTED and t == TREATMENT_EXPECTED:
        return "H_COMP_HALF_FALSIFIED_EXACT_SODIUM64_MATH"
    if c == t:
        return "H_COMP_HALF_SUPPORTED_NO_HALF_EFFECT"
    return "H_COMP_HALF_SUPPORTED_WRONG_ARITHMETIC"


def analyze(control_path: Path, treatment_path: Path) -> dict[str, object]:
    control = central_mode(control_path)
    treatment = central_mode(treatment_path)
    return {
        "classification": classify(control, treatment),
        "expected": {
            "control_rgb5": list(CONTROL_EXPECTED),
            "treatment_rgb5": list(TREATMENT_EXPECTED),
        },
        "control": control,
        "treatment": treatment,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path)
    parser.add_argument("treatment", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.control, args.treatment)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
