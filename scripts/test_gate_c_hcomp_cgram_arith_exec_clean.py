#!/usr/bin/env python3
"""Source/binary contract for the clean executable PR18->H-COMP E1f bridge."""
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]


def insns(text: str) -> list[str]:
    out = []
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
        raise AssertionError(f"missing {name}")
    return int(m.group(1), 16)


def syms(path: Path) -> dict[str, int]:
    out = {}
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


def rgb555_to_rgba5551(v: int) -> int:
    v &= 0x7FFF
    return ((v & 0x1F) << 11) | ((v & 0x3E0) << 1) | ((v & 0x7C00) >> 9) | 1


def rgba5551_to_rgb555(v: int) -> int:
    return ((v >> 11) & 0x1F) | ((v & 0x07C0) >> 1) | ((v & 0x003E) << 9)


def e1f(a: int, b: int) -> int:
    a &= 0x7FFF
    b &= 0x7FFF
    return (a + b - ((a ^ b) & 0x0421)) >> 1


def source_contract() -> None:
    d = (ROOT / "src/defines.h").read_text()
    expect = {
        "OVERLAY_MODE7_SRC": 0xE8C,
        "OVERLAY_MAIN_SRC": 0xE90,
        "OVERLAY_HCOMP_SRC": 0xE94,
        "HCOMP_RAW_PALETTE_PTRS": 0xE98,
        "HCOMP_CGRAM_EVENT_CURSOR": 0xEA0,
        "HCOMP_CGRAM_PAIR_SCRATCH": 0xEA8,
        "HCOMP_CGRAM_WRITE_SCRATCH": 0xEB0,
        "VEC_DATA": 0xF70,
    }
    for k, v in expect.items():
        if lit(d, k) != v:
            raise AssertionError(f"{k} drift")
    if not (0xE8C + 4 == 0xE90 and 0xE90 + 4 == 0xE94 and 0xE94 + 4 == 0xE98 and 0xE98 + 8 == 0xEA0):
        raise AssertionError("DMEM pointer packing broken")

    main = (ROOT / "src/main.S").read_text()
    for anchor in (
        "rsp_mode7_text_start",
        "DMEM(OVERLAY_MODE7_SRC)",
        "rsp_main_text_start",
        "DMEM(OVERLAY_MAIN_SRC)",
        "rsp_hcomp_text_start",
        "DMEM(OVERLAY_HCOMP_SRC)",
        "DMEM(HCOMP_RAW_PALETTE_PTRS)",
        "DMEM(HCOMP_RAW_PALETTE_PTRS + 4)",
    ):
        if anchor not in main:
            raise AssertionError(f"CPU publication missing {anchor}")

    for name in ("rsp_main.S", "rsp_mode7.S"):
        src = (ROOT / "src" / name).read_text()
        order = [
            "overlay_mode7_src: .word 0",
            "overlay_main_src: .word 0",
            "overlay_hcomp_src: .word 0",
            "hcomp_raw_palette_ptrs: .word 0, 0",
        ]
        pos = [src.index(x) for x in order]
        if pos != sorted(pos):
            raise AssertionError(f"{name}: DMEM pointer order drift")

        nf = insns(section(src, "next_frame:", "\n\nclear_cache:"))
        want_nf = [
            "lw a1, OVERLAY_HCOMP_SRC",
            "li t9, 0x13B0",
            "b overlay_load_slot",
            "nop",
        ]
        if nf != want_nf:
            raise AssertionError(f"{name}: current-slot frame-end dispatch drift {nf}")

        ld = insns(section(src, "overlay_load_mode7:", "\noverlay_load_main:"))
        want_ld = [
            "lw a1, OVERLAY_MODE7_SRC",
            "li a0, 0x13A8",
            "jal dma_read",
            "li a2, 0x3E7",
            "jr t9",
            "nop",
        ]
        if ld != want_ld:
            raise AssertionError(f"{name}: generic loader drift {ld}")

        # PR #18 replay remains resident and still targets the slot selected by sp.
        for anchor in (
            "hcomp_cgram_pair_ready:",
            "HCOMP_CGRAM_EVENT_CURSOR",
            "HCOMP_CGRAM_WRITE_SCRATCH",
            "HCOMP_RAW_PALETTE_PTRS(sp)",
        ):
            if anchor not in src:
                raise AssertionError(f"{name}: PR18 replay anchor lost {anchor}")

    reg = (ROOT / "src/rsp_main.S").read_text()
    reg_entry = insns(section(reg, "draw_mode7_entry:", "\n\ndraw_obj:"))
    if reg_entry != ["b overlay_load_mode7", "li t9, 0x1788"]:
        raise AssertionError(f"regular Mode7 fault drift {reg_entry}")

    m7 = (ROOT / "src/rsp_mode7.S").read_text()
    m7_entry = insns(section(m7, "draw_mode7_entry:", "\n\ndraw_obj:"))
    if m7_entry != ["b draw_mode7_impl", "nop"]:
        raise AssertionError(f"true Mode7 entry drift {m7_entry}")

    h = (ROOT / "src/rsp_hcomp.S").read_text()
    if ".byte 0:0x3A8" not in h or ".byte 0:0x328" not in h:
        raise AssertionError("HCOMP fixed-slot padding drift")
    if insns(section(h, "draw_bg:", "\nhcomp_entry:")) != [
        "j 0xA4001F90",
        "move v0, t0",
    ]:
        raise AssertionError("HCOMP regular fault surface drift")
    if insns(h[h.index("draw_mode7_entry:"):])[:2] != [
        "j 0xA4001F78",
        "li t9, 0x1788",
    ]:
        raise AssertionError("HCOMP Mode7 fault surface drift")

    body = insns(section(h, "hcomp_entry:", "\n// Keep the externally visible Mode7 entry"))
    if len(body) != 44:
        raise AssertionError(f"HCOMP bridge body {len(body)} insns != 44")

    required = [
        "li a0, SCRN_DATA",
        "lw a1, HCOMP_RAW_PALETTE_PTRS(sp)",
        "jal 0xA4001F40",
        "li a2, 0x1F",
        "srl t2, t0, 11",
        "andi t3, t0, 0x07C0",
        "andi t3, t0, 0x003E",
        "srl t4, t1, 11",
        "andi t5, t1, 0x07C0",
        "andi t5, t1, 0x003E",
        "xor t2, t0, t1",
        "andi t2, t2, 0x0421",
        "add t3, t0, t1",
        "sub t3, t3, t2",
        "srl t3, t3, 1",
        "li a1, 0xA00F0000",
        "jal 0xA4001F08",
        "li a2, 0x7",
        "xori sp, sp, 4",
        "li t0, 0x2",
        "mtc0 t0, COP0_SP_STATUS",
        "j 0xA400103C",
        "nop",
    ]
    cursor = -1
    for anchor in required:
        try:
            cursor = body.index(anchor, cursor + 1)
        except ValueError as exc:
            raise AssertionError(f"HCOMP bridge sequence missing/reordered {anchor!r}") from exc

    # Ownership invariant: current slot is read before sp changes.
    if body.index("lw a1, HCOMP_RAW_PALETTE_PTRS(sp)") > body.index("xori sp, sp, 4"):
        raise AssertionError("HCOMP toggles queue slot before consuming it")
    if body.index("jal 0xA4001F08") > body.index("xori sp, sp, 4"):
        raise AssertionError("HCOMP toggles queue slot before proof publication")

    # Representation and arithmetic discriminator remain exact in the executable.
    for rgb in range(0x8000):
        if rgba5551_to_rgb555(rgb555_to_rgba5551(rgb)) != rgb:
            raise AssertionError(f"RGBA5551 roundtrip failed at {rgb:#x}")
    if e1f(0x7FFF, 0x7FFF) != 0x7FFF:
        raise AssertionError("E1f high-sum discriminator drift")
    if e1f(0x001F, 0x0020) != 0x000F:
        raise AssertionError("E1f cross-channel discriminator drift")


def binary_contract(maps: list[Path], symbols: list[Path]) -> None:
    if len(maps) != 3 or len(symbols) != 3:
        raise AssertionError("need regular+Mode7+HCOMP maps/symbol tables")
    rm, r7m, hm = maps
    rs, r7s, hs = [syms(p) for p in symbols]

    if text_size(rm) != 0x1000 or text_size(r7m) != 0x1000:
        raise AssertionError("resident renderer IMEM grew")
    if text_size(hm) != 0x790:
        raise AssertionError(f"HCOMP payload size {text_size(hm):#x} != 0x790")

    fixed = {
        "draw_frame": 0xA400103C,
        "dma_write": 0xA4001F08,
        "dma_read": 0xA4001F40,
        "overlay_load_mode7": 0xA4001F78,
        "overlay_load_slot": 0xA4001F7C,
        "overlay_load_main": 0xA4001F90,
        "draw_bg": 0xA40013A8,
        "draw_mode7_entry": 0xA4001788,
        "draw_obj": 0xA4001790,
    }
    for label, s in (("regular", rs), ("mode7", r7s)):
        for k, v in fixed.items():
            if s.get(k) != v:
                raise AssertionError(f"{label}: {k}={s.get(k)} expected {v:#x}")

    if hs.get("draw_bg") != 0xA40013A8:
        raise AssertionError("HCOMP draw_bg moved")
    if hs.get("hcomp_entry") != 0xA40013B0:
        raise AssertionError("HCOMP entry moved")
    if hs.get("hcomp_pair_loop") != 0xA40013D0:
        raise AssertionError(f"HCOMP pair loop moved: {hs.get('hcomp_pair_loop')}")
    if hs.get("draw_mode7_entry") != 0xA4001788:
        raise AssertionError("HCOMP Mode7 entry moved")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs=3, type=Path)
    ap.add_argument("--symbols", nargs=3, type=Path)
    a = ap.parse_args()
    source_contract()
    if a.maps or a.symbols:
        if not a.maps or not a.symbols:
            ap.error("--maps and --symbols must be supplied together")
        binary_contract(a.maps, a.symbols)
    print("HCOMP_CGRAM_ARITH_EXEC_CLEAN_CONTRACT_VALIDATED")
    print("runtime_scope=proof_only_PR18_replay_to_E1f")
    print("active_slot_bytes=192")
    print("resident_imem_growth=0")
    print("queue_toggle=after_arithmetic_before_HALT")
    print("main_sub_provenance=NOT_PROVEN")
    print("color_math_gating=NOT_PROVEN")
    print("final_pixels=NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
