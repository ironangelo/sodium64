#!/usr/bin/env python3
"""Analyze raw Sodium64 16-bit N64 framebuffers for the Gate-C OBJ-window test."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

WIDTH = 280
HEIGHT = 240
EXPECTED_BYTES = WIDTH * HEIGHT * 2

# Sodium64's regular tile path adds the 12-pixel framebuffer border. The two
# outer diagnostic OBJ probes therefore render around these framebuffer centers.
OUTER_PROBE_CENTERS = ((31.5, 99.5), (239.5, 99.5))


def decode_rgba5551(data: bytes) -> list[tuple[int, int, int]]:
    if len(data) != EXPECTED_BYTES:
        raise ValueError(f"expected {EXPECTED_BYTES} bytes, got {len(data)}")
    pixels: list[tuple[int, int, int]] = []
    for i in range(0, len(data), 2):
        value = (data[i] << 8) | data[i + 1]
        pixels.append(((value >> 11) & 31, (value >> 6) & 31, (value >> 1) & 31))
    return pixels


def component_boxes(mask: list[bool], *, min_area: int) -> list[dict[str, float]]:
    seen = bytearray(len(mask))
    boxes: list[dict[str, float]] = []
    for start, enabled in enumerate(mask):
        if not enabled or seen[start]:
            continue
        queue = deque([start])
        seen[start] = 1
        area = 0
        min_x = WIDTH
        max_x = -1
        min_y = HEIGHT
        max_y = -1
        while queue:
            index = queue.popleft()
            y, x = divmod(index, WIDTH)
            area += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nx < 0 or nx >= WIDTH or ny < 0 or ny >= HEIGHT:
                    continue
                ni = ny * WIDTH + nx
                if mask[ni] and not seen[ni]:
                    seen[ni] = 1
                    queue.append(ni)
        if area >= min_area:
            boxes.append(
                {
                    "area": area,
                    "x0": min_x,
                    "x1": max_x,
                    "y0": min_y,
                    "y1": max_y,
                    "width": max_x - min_x + 1,
                    "height": max_y - min_y + 1,
                    "cx": (min_x + max_x) / 2,
                    "cy": (min_y + max_y) / 2,
                }
            )
    return boxes


def _near(component: dict[str, float], center: tuple[float, float]) -> bool:
    return abs(component["cx"] - center[0]) <= 3 and abs(component["cy"] - center[1]) <= 3


def analyze(path: Path) -> dict[str, object]:
    pixels = decode_rgba5551(path.read_bytes())
    red = [r >= 24 and g <= 7 and b <= 7 for r, g, b in pixels]
    green = [g >= 24 and r <= 7 and b <= 7 for r, g, b in pixels]
    red_components = component_boxes(red, min_area=16)
    green_components = component_boxes(green, min_area=64)
    outer_present = [
        any(_near(component, center) for component in red_components)
        for center in OUTER_PROBE_CENTERS
    ]
    return {
        "path": str(path),
        "red_pixels": sum(red),
        "green_pixels": sum(green),
        "red_components": red_components,
        "green_components": green_components,
        "red_component_count": len(red_components),
        "outer_present": outer_present,
    }


def classify(control: dict[str, object], treatment: dict[str, object]) -> str:
    c_outer = list(control["outer_present"])
    t_outer = list(treatment["outer_present"])
    if c_outer != [True, True]:
        return f"INDETERMINATE_CONTROL_OUTER_{c_outer}"
    if t_outer == [False, False]:
        return "H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ"
    if t_outer == [True, True]:
        return "H_OBJ_SUPPORTED_SODIUM64_IGNORES_OBJ_WINDOW"
    return f"INDETERMINATE_TREATMENT_OUTER_{t_outer}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path)
    parser.add_argument("treatment", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = {
        "control": analyze(args.control),
        "treatment": analyze(args.treatment),
    }
    result["classification"] = classify(result["control"], result["treatment"])
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
