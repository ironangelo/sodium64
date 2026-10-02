#!/usr/bin/env python3
"""Regression contract for the native RDP texture-load synchronization repair.

The Gate-C native flight recorder captured a real N64 RDP deadlock with
CURRENT stuck at the start of rdp_tile. Keep every LoadBlock preceded by
LoadSync without growing the fixed DMEM command map. The palette LoadBlock
therefore occupies the retired first slot of rdp_fill, while actual fill/
scissor submissions begin at RDP_FILL+8.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RSP = [ROOT / "src/rsp_main.S", ROOT / "src/rsp_mode7.S"]

SYNC_LOAD = "0x2600000000000000"
LOAD_PALETTE = "0x3300000000400000"
LOAD_TEXTURE = "0x330000000101F800"
SET_SCISSOR = "0x2D030020004303A0"


def table(text: str, name: str, next_name: str) -> list[str]:
    m = re.search(
        rf"^{name}:\n(?P<body>.*?)(?=^{next_name}:)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not m:
        raise AssertionError(f"missing {name}->{next_name} table")
    return re.findall(r"\.dword\s+(0x[0-9A-Fa-f]+)", m.group("body"))


for path in RSP:
    text = path.read_text()

    frame = table(text, "rdp_frame", "rdp_fill")
    fill = table(text, "rdp_fill", "rdp_window")
    tile = table(text, "rdp_tile", "rdp_tile7")
    tile7 = table(text, "rdp_tile7", "tile_params")

    assert len(frame) == 3, (path, "rdp_frame layout changed", frame)
    assert frame[-1].lower() == SYNC_LOAD.lower(), (path, "palette LoadSync missing", frame)

    assert len(fill) == 7, (path, "rdp_fill fixed extent changed", fill)
    assert fill[0].lower() == LOAD_PALETTE.lower(), (path, "palette LoadBlock slot", fill)
    assert fill[1].lower() == SET_SCISSOR.lower(), (path, "fill SetScissor moved", fill)

    for name, seq in (("rdp_tile", tile), ("rdp_tile7", tile7)):
        load_i = next((i for i, v in enumerate(seq) if v.lower() == LOAD_TEXTURE.lower()), None)
        assert load_i is not None and load_i > 0, (path, name, "LoadBlock missing")
        assert seq[load_i - 1].lower() == SYNC_LOAD.lower(), (
            path, name, "LoadBlock is not immediately preceded by LoadSync", seq
        )

    assert "li a1, RDP_FILL + 8" in text, (path, "frame palette endpoint missing")
    assert "    li a0, RDP_FILL\n" not in text, (
        path, "a fill/scissor submission would replay palette LoadBlock"
    )

hcomp = (ROOT / "src/rsp_hcomp.S").read_text()
assert "    li a0, RDP_FILL\n" not in hcomp
assert "    li a0, RDP_FILL + 8\n" in hcomp

defines = (ROOT / "src/defines.h").read_text()
assert "#define RDP_FILL (RDP_FRAME + 0x18)" in defines
assert "#define RDP_WINDOW (RDP_FILL + 0x38)" in defines

print("RDP LoadSync fixed-layout contract: PASS")
