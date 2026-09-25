#!/usr/bin/env python3
"""Localize the live RSP stage using Mupen debugger MMIO reads.

This proof is tooling-only. It reuses the already validated first-RDP-return
workload and inspects SP/DPC registers at the same paused observation point.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

import check_gate_c_hcomp_mode7_rdp_return as prior

ROOT = Path(__file__).resolve().parents[1]
IMEM_BASE = 0xA4001000


def read_state(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if not raw or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        out[key] = int(value, 16)
    required = {
        "sp_pc", "sp_status", "sp_dma_full", "sp_dma_busy",
        "dp_start", "dp_end", "dp_current", "dp_status",
    }
    missing = sorted(required - out.keys())
    if missing:
        raise AssertionError(f"missing SP/DP observations: {missing}")
    return out


def read_symbols(path: Path) -> list[tuple[int, str]]:
    syms: list[tuple[int, str]] = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) < 8 or not parts[0].endswith(":"):
            continue
        try:
            value = int(parts[1], 16)
        except ValueError:
            continue
        name = parts[-1]
        if IMEM_BASE <= value < IMEM_BASE + 0x1000 and name:
            syms.append((value, name))
    if not syms:
        raise AssertionError("no RSP IMEM symbols parsed")
    syms.sort()
    return syms


def nearest_symbol(symbols: list[tuple[int, str]], addr: int) -> tuple[str, int, int]:
    candidates = [(value, name) for value, name in symbols if value <= addr]
    if not candidates:
        raise AssertionError(f"no symbol at/before IMEM address 0x{addr:08X}")
    value, name = max(candidates, key=lambda x: x[0])
    return name, value, addr - value


def source_contract() -> None:
    prior.source_contract()
    wf = (ROOT / ".github/workflows/gate-c-hcomp-mode7-sp-state.yml").read_text()
    for anchor in (
        'mem /1w 0xA4080000',
        'mem /3w 0xA4040010',
        'mem /4w 0xA4100000',
        'M64P_MEM_RSPREG',
        'M64P_MEM_RSP',
        'M64P_MEM_DP',
    ):
        if anchor not in wf:
            raise AssertionError(f"MMIO proof workflow drift: {anchor!r}")


def classify(root: Path, symbols_path: Path) -> dict:
    source_contract()

    prior_result = prior.classify(root)
    if not prior_result.get("passed"):
        return {
            "passed": False,
            "reason": "first-RDP-return prerequisite no longer valid",
            "prior": prior_result,
        }
    if prior_result.get("classification") != "MODE7_FIRST_RDP_SEND_RETURNED_HCOMP_NOT_REACHED":
        return {
            "passed": False,
            "reason": "workload no longer isolates post-second-texture pre-HCOMP state",
            "prior": prior_result,
        }

    state = read_state(root / "sp-state.txt")
    pc = state["sp_pc"] & 0xFFF
    imem_addr = IMEM_BASE + pc
    symbols = read_symbols(symbols_path)
    name, sym_addr, offset = nearest_symbol(symbols, imem_addr)

    halted = bool(state["sp_status"] & 0x1)
    broke = bool(state["sp_status"] & 0x2)
    dma_busy = bool(state["sp_dma_busy"] & 0x1)
    dma_full = bool(state["sp_dma_full"] & 0x1)
    dp_cmd_busy = bool(state["dp_status"] & 0x40)

    if halted:
        classification = "MODE7_RSP_HALTED_BEFORE_HCOMP"
        meaning = (
            "RSP is halted while the H-COMP mailbox is still untouched; "
            "localize the unexpected halt at the sampled IMEM symbol."
        )
    else:
        classification = "MODE7_RSP_RUNNING_BEFORE_HCOMP"
        meaning = (
            "RSP is still running after the second texture DMA while H-COMP is "
            "untouched; sampled IMEM symbol localizes the live post-RDP path."
        )

    return {
        "passed": True,
        "classification": classification,
        "meaning": meaning,
        "sp_pc_raw": f"0x{state['sp_pc']:08X}",
        "imem_address": f"0x{imem_addr:08X}",
        "nearest_symbol": name,
        "nearest_symbol_address": f"0x{sym_addr:08X}",
        "symbol_offset": offset,
        "sp_status": f"0x{state['sp_status']:08X}",
        "sp_halt": halted,
        "sp_broke": broke,
        "sp_dma_full": dma_full,
        "sp_dma_busy": dma_busy,
        "dp_start": f"0x{state['dp_start']:08X}",
        "dp_end": f"0x{state['dp_end']:08X}",
        "dp_current": f"0x{state['dp_current']:08X}",
        "dp_status": f"0x{state['dp_status']:08X}",
        "dp_command_busy": dp_cmd_busy,
        "prior_classification": prior_result["classification"],
        "semantic_scope": (
            "single pinned-Mupen MMIO stage sample only; not real-N64 timing/"
            "performance authority and not proof of long-run renderer progress"
        ),
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "mode7-texture-slot0.bin").write_bytes(bytes(8))
        (root / "mode7-texture-slot1.bin").write_bytes(bytes(8))
        (root / "mailbox.bin").write_bytes(prior.MAILBOX_SENTINEL)
        (root / "guest-state.bin").write_bytes(prior.EXPECTED_GUEST)
        (root / "sp-state.txt").write_text(
            "\n".join(
                (
                    "sp_pc=00000ABC",
                    "sp_status=00000000",
                    "sp_dma_full=00000000",
                    "sp_dma_busy=00000000",
                    "dp_start=00001300",
                    "dp_end=00001400",
                    "dp_current=00001380",
                    "dp_status=00000040",
                )
            )
            + "\n"
        )
        syms = root / "rsp-mode7.syms"
        syms.write_text(
            "  1: A4001A00 0 NOTYPE LOCAL DEFAULT 1 next_tile7\n"
            "  2: A4001ABC 0 NOTYPE LOCAL DEFAULT 1 rdp_send\n"
        )
        r = classify(root, syms)
        assert r["passed"]
        assert r["classification"] == "MODE7_RSP_RUNNING_BEFORE_HCOMP"
        assert r["nearest_symbol"] == "rdp_send"
        assert r["symbol_offset"] == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence", type=Path, nargs="?")
    ap.add_argument("--symbols", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        print("Mode7 SP-state classifier self-test: PASS")
        return 0
    if args.evidence is None or args.symbols is None:
        ap.error("evidence directory and --symbols are required")

    result = classify(args.evidence, args.symbols)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
