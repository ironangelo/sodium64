#!/usr/bin/env python3
"""Analyze a sequence of ares SNES reference screenshots for the OBJ-window test."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

from PIL import Image


def components(mask: list[bool], width: int, height: int, min_area: int) -> list[dict[str, float]]:
    seen = bytearray(len(mask))
    out: list[dict[str, float]] = []
    for start, enabled in enumerate(mask):
        if not enabled or seen[start]:
            continue
        q = deque([start])
        seen[start] = 1
        area = 0
        x0, y0 = width, height
        x1 = y1 = -1
        while q:
            i = q.popleft()
            y, x = divmod(i, width)
            area += 1
            x0, x1 = min(x0, x), max(x1, x)
            y0, y1 = min(y0, y), max(y1, y)
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    ni = ny * width + nx
                    if mask[ni] and not seen[ni]:
                        seen[ni] = 1
                        q.append(ni)
        if area >= min_area:
            out.append({
                "area": area,
                "x0": x0,
                "x1": x1,
                "y0": y0,
                "y1": y1,
                "width": x1 - x0 + 1,
                "height": y1 - y0 + 1,
                "cx": (x0 + x1) / 2,
                "cy": (y0 + y1) / 2,
            })
    return out


def analyze_frame(path: Path) -> dict[str, object]:
    image = Image.open(path).convert("RGB")
    width, height = image.size
    pix = list(image.getdata())

    green_mask = [
        g >= 140 and r <= 120 and b <= 120 and g > r * 1.5 and g > b * 1.5
        for r, g, b in pix
    ]
    red_mask = [
        r >= 140 and g <= 120 and b <= 120 and r > g * 1.5 and r > b * 1.5
        for r, g, b in pix
    ]

    green = components(green_mask, width, height, min_area=500)
    if not green:
        return {"path": str(path), "status": "NO_GREEN_VIEWPORT", "red_component_count": None}
    main_green = max(green, key=lambda c: c["area"])

    # The visible BG window is 128 SNES pixels wide. The center diagnostic OBJ
    # lies behind opaque BG1 at the chosen priority, so the useful oracle is the
    # two *outer* OBJ probes: control shows both; treatment masks both.
    scale = float(main_green["width"]) / 128.0
    if not 0.5 <= scale <= 8.0:
        return {
            "path": str(path),
            "status": "BAD_SCALE",
            "scale": scale,
            "green": main_green,
            "red_component_count": None,
        }

    viewport_x0 = float(main_green["x0"]) - 64.0 * scale
    viewport_x1 = viewport_x0 + 256.0 * scale
    viewport_y0 = float(main_green["y0"])
    viewport_y1 = viewport_y0 + 224.0 * scale

    red = components(red_mask, width, height, min_area=max(4, int(scale * scale * 6)))
    probe_red = [
        c for c in red
        if viewport_x0 - 2 <= c["cx"] <= viewport_x1 + 2
        and viewport_y0 - 2 <= c["cy"] <= viewport_y1 + 2
    ]

    return {
        "path": str(path),
        "status": "OK",
        "scale": scale,
        "green": main_green,
        "viewport": {
            "x0": viewport_x0,
            "x1": viewport_x1,
            "y0": viewport_y0,
            "y1": viewport_y1,
        },
        "red_components": probe_red,
        "red_component_count": len(probe_red),
    }


def classify(frames: list[dict[str, object]]) -> str:
    counts = [
        int(f["red_component_count"])
        for f in frames
        if f.get("status") == "OK" and f.get("red_component_count") is not None
    ]
    # The ROM's only alternating PPU variable is TMW bit 4. Seeing both stable
    # states in the same pinned reference sequence therefore establishes the
    # object-window semantic oracle without assuming which wall-clock sample was
    # captured first.
    if 2 in counts and 0 in counts:
        return "REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0"
    return "REFERENCE_INDETERMINATE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    frames = [analyze_frame(path) for path in sorted(args.frames)]
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
