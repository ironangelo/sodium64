#!/usr/bin/env python3
"""Source/binary contract for the clean executable 8-line Main/Sub ownership rung."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUB_COLOR = 0xA00E4000
ACTIVE_Y0 = 16
ROW_BYTES = 280 * 2
SUB_COLOR_RDP_BASE = (SUB_COLOR & 0x00FFFFFF) - ACTIVE_Y0 * ROW_BYTES
STRIP_BYTES = 280 * 8 * 2


def insns(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"):
            continue
        out.append(line)
    return out


def section(src: str, start: str, end: str) -> str:
    i = src.index(start)
    j = src.index(end, i)
    return src[i:j]


def lit(src: str, name: str) -> int:
    m = re.search(rf"^#define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\s*$", src, re.M)
    if not m:
        raise AssertionError(f"missing literal define {name}")
    return int(m.group(1), 16)


def syms(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in path.read_text().splitlines():
        p = line.split()
        if len(p) >= 8 and p[0].rstrip(":").isdigit():
            try:
                out[p[-1]] = int(p[1], 16)
            except ValueError:
                pass
    return out


def text_size(path: Path) -> int:
    s = path.read_text()
    m = re.search(r"^\s*\.text\s+0xa4001000\s+0x([0-9A-Fa-f]+)\b", s, re.M)
    if not m:
        raise AssertionError(f"{path}: .text missing")
    return int(m.group(1), 16)


def prove_source() -> None:
    defs = (ROOT / "src/defines.h").read_text()
    expected_defs = {
        "OVERLAY_MODE7_SRC": 0xE8C,
        "OVERLAY_MAIN_SRC": 0xE90,
        "OVERLAY_HCOMP_SRC": 0xE94,
        "HCOMP_RAW_PALETTE_PTRS": 0xE98,
        "HCOMP_CGRAM_EVENT_CURSOR": 0xEA0,
        "HCOMP_CGRAM_PAIR_SCRATCH": 0xEA8,
        "HCOMP_CGRAM_WRITE_SCRATCH": 0xEB0,
        "VEC_DATA": 0xF70,
    }
    for name, want in expected_defs.items():
        if lit(defs, name) != want:
            raise AssertionError(f"{name} drift")

    if SUB_COLOR_RDP_BASE != 0x000E1D00 or STRIP_BYTES != 0x1180:
        raise AssertionError("compact Sub geometry drift")

    ppu = (ROOT / "src/ppu.S").read_text()
    for anchor in (
        "andi t0, a1, 0x4",
        "sll t0, t0, 1",
        "xori t0, t0, 0x8",
        "sb t0, fb_border",
        "addi t1, t1, 8",
        "sw t1, DMEM(FB_OFFSET)(t5)",
    ):
        if anchor not in ppu:
            raise AssertionError(f"y16 source anchor drift: {anchor!r}")

    for name in ("rsp_main.S", "rsp_mode7.S"):
        src = (ROOT / "src" / name).read_text()

        frame = insns(section(
            src,
            "// Gate-C Main/Sub ownership proof: begin the frame on the compact",
            "// Run the RDP to start the frame",
        ))
        if frame != [
            "lui t0, 0x000E",
            "ori t0, t0, 0x1D00",
            "lw t1, PALETTE_PTR(sp)",
            "sw t0, RDP_FRAME + 4",
            "sw t1, RDP_FRAME + 12",
        ]:
            raise AssertionError(f"{name}: compact Sub frame target drift {frame}")

        mask = insns(section(
            src,
            "// Gate-C Main/Sub ownership proof: screen order is semantic",
            "next_layer:",
        ))
        if mask != [
            "lbu s7, TS",
            "lbu t0, TM",
            "sll t0, t0, 8",
            "or s7, s7, t0",
        ]:
            raise AssertionError(f"{name}: semantic screen pack drift {mask}")

        transition = insns(section(
            src,
            "// Move from semantic TS to semantic TM.",
            "// Fixed renderer overlay begins",
        ))
        if transition != [
            "srl s7, s7, 8",
            "beqz s7, next_section",
            "andi s3, s3, 0xF0",
            "lw a1, OVERLAY_HCOMP_SRC",
            "li t9, 0x1760",
            "b overlay_load_slot",
            "nop",
        ]:
            raise AssertionError(f"{name}: TS->TM transition drift {transition}")

        nf = insns(section(src, "next_frame:", "clear_cache:"))
        if nf != [
            "lw a1, OVERLAY_HCOMP_SRC",
            "li t9, 0x13B0",
            "b overlay_load_slot",
            "nop",
        ]:
            raise AssertionError(f"{name}: frame-end HCOMP dispatch drift {nf}")

        loader = insns(section(src, "overlay_load_mode7:", "overlay_load_main:"))
        if loader != [
            "lw a1, OVERLAY_MODE7_SRC",
            "li a0, 0x13A8",
            "jal dma_read",
            "li a2, 0x3E7",
            "jr t9",
            "nop",
        ]:
            raise AssertionError(f"{name}: generic slot loader drift {loader}")

        for anchor in (
            "hcomp_cgram_pair_ready:",
            "HCOMP_CGRAM_EVENT_CURSOR",
            "HCOMP_CGRAM_WRITE_SCRATCH",
            "HCOMP_RAW_PALETTE_PTRS(sp)",
        ):
            if anchor not in src:
                raise AssertionError(f"{name}: PR18 replay anchor lost {anchor}")

    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0x3A8" not in h or ".byte 0:0x300" not in h:
        raise AssertionError("HCOMP padding/placement drift")

    if insns(section(h, "draw_bg:", "hcomp_entry:")) != [
        "j 0xA4001F90",
        "move v0, t0",
    ]:
        raise AssertionError("HCOMP regular fault surface drift")

    body = insns(section(h, "hcomp_entry:", "// Mid-frame Main/Sub ownership helper."))
    if len(body) != 44:
        raise AssertionError(f"frame-end HCOMP body drift: {len(body)} != 44")
    for anchor in (
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "jal 0xA4001F40",
        "xor t2, t0, t1",
        "andi t2, t2, 0x0421",
        "jal 0xA4001F08",
        "xori sp, sp, 4",
        "mtc0 t0, COP0_SP_STATUS",
        "j 0xA400103C",
    ):
        if anchor not in body:
            raise AssertionError(f"frame-end HCOMP arithmetic/ownership drift: {anchor}")

    switch = insns(section(h, "hcomp_screen_switch:", "// Keep the externally visible Mode7 entry"))
    if switch != [
        "lw t0, FRAMEBUFFER(sp)",
        "addi t0, t0, 280 * -16",
        "sw t0, RDP_FRAME + 4",
        "li a0, RDP_FRAME",
        "jal 0xA4001F5C",
        "li a1, RDP_FRAME + 8",
        "lw a1, OVERLAY_MAIN_SRC",
        "li t9, 0x1364",
        "j 0xA4001F7C",
        "nop",
    ]:
        raise AssertionError(f"HCOMP screen switch drift {switch}")

    if insns(h[h.index("draw_mode7_entry:"):])[:2] != [
        "j 0xA4001F78",
        "li t9, 0x1788",
    ]:
        raise AssertionError("HCOMP Mode7 fault surface drift")

    active = (2 + 44 + 10 + 2) * 4
    if active != 232 or active > 1000:
        raise AssertionError(f"HCOMP active fixed-slot budget drift: {active}")


def prove_binary(maps: list[Path], symbols: list[Path]) -> None:
    if len(maps) != 3 or len(symbols) != 3:
        raise AssertionError("need regular+Mode7+HCOMP maps/symbols")
    rm, m7m, hm = maps
    rs, m7s, hs = [syms(p) for p in symbols]

    rsize = text_size(rm)
    m7size = text_size(m7m)
    if rsize != 0x1000 or m7size != 0x1000:
        raise AssertionError(
            f"resident renderer text geometry drift regular={rsize:#x} mode7={m7size:#x}"
        )
    if text_size(hm) != 0x790:
        raise AssertionError(f"HCOMP text size {text_size(hm):#x} != 0x790")

    fixed = {
        "draw_frame": 0xA400103C,
        "next_layer": 0xA4001364,
        "draw_bg": 0xA40013A8,
        "draw_mode7_entry": 0xA4001788,
        "draw_obj": 0xA4001790,
        "dma_write": 0xA4001F08,
        "dma_read": 0xA4001F40,
        "rdp_send": 0xA4001F5C,
        "overlay_load_mode7": 0xA4001F78,
        "overlay_load_slot": 0xA4001F7C,
        "overlay_load_main": 0xA4001F90,
    }
    for label, table in (("regular", rs), ("mode7", m7s)):
        for name, want in fixed.items():
            got = table.get(name)
            if got != want:
                raise AssertionError(f"{label}: {name}={got} expected {want:#x}")

    hfixed = {
        "draw_bg": 0xA40013A8,
        "hcomp_entry": 0xA40013B0,
        "hcomp_pair_loop": 0xA40013D0,
        "hcomp_screen_switch": 0xA4001760,
        "draw_mode7_entry": 0xA4001788,
    }
    for name, want in hfixed.items():
        got = hs.get(name)
        if got != want:
            raise AssertionError(f"HCOMP: {name}={got} expected {want:#x}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs=3, type=Path)
    ap.add_argument("--symbols", nargs=3, type=Path)
    args = ap.parse_args()
    prove_source()
    if args.maps or args.symbols:
        if not args.maps or not args.symbols:
            ap.error("--maps and --symbols must be supplied together")
        prove_binary(args.maps, args.symbols)

    print("HCOMP_MAIN_SUB_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("scope=8_line_dual_color_ownership_only")
    print("sub_color=0xA00E4000")
    print("sub_color_rdp_base=0x000E1D00")
    print("semantic_screen_order=TS_then_TM")
    print("next_layer=0xA4001364")
    print("hcomp_screen_switch=0xA4001760")
    print("hcomp_active_slot_bytes=232")
    print("resident_text_bytes=4096")
    print("resident_imem_growth=0")
    print("frame_end_E1f_preserved=true")
    print("metadata_wiring=NOT_PROVEN")
    print("color_math_gating=NOT_PROVEN")
    print("final_pixels=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
