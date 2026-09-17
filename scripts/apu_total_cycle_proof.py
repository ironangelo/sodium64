#!/usr/bin/env python3
"""Directed Layer-1 SPC700 total-cycle proof for Sodium64's JIT.

This diagnostic does not measure throughput and does not claim cycle-accurate
bus/I/O ordering. It injects four already-audited SPC700 snippets at a safe
apu_execute boundary, forces compilation, inspects the generated block's single
ADDI s3,s3,imm debit, and checks total guest-cycle units against the pinned
hardware/reference totals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, RSPClient, connect_with_retry, validate_stop

JIT_BUFFER = 0xA01C0000
TEST_PC = 0x0200
APU_CLOCK = 21
BREAKPOINT_KIND = 4


def parse_int(text: str) -> int:
    return int(text, 0)


def be(value: int, size: int) -> bytes:
    return int(value).to_bytes(size, "big", signed=False)


def read_u8(client: RSPClient, address: int) -> int:
    return client.read_memory(address, 1, 1)[0]


def read_u16(client: RSPClient, address: int) -> int:
    return int.from_bytes(client.read_memory(address, 2, 2), "big")


def read_u32(client: RSPClient, address: int) -> int:
    return int.from_bytes(client.read_memory(address, 4, 4), "big")


def cached(address: int) -> int:
    if 0xA0000000 <= address < 0xC0000000:
        return address - 0x20000000
    return address


def signal_number(reply: bytes) -> int | None:
    if len(reply) >= 3 and reply[:1] in (b"S", b"T"):
        try:
            return int(reply[1:3], 16)
        except ValueError:
            return None
    return None


def set_breakpoint(client: RSPClient, address: int, enabled: bool) -> None:
    op = "Z" if enabled else "z"
    reply = client.request(f"{op}0,{address:x},{BREAKPOINT_KIND}")
    if reply != b"OK":
        raise RuntimeError(
            f"target rejected {'insert' if enabled else 'remove'} breakpoint "
            f"at 0x{address:08X}: {reply!r}"
        )


def continue_to_breakpoint(client: RSPClient, address: int, label: str) -> None:
    set_breakpoint(client, address, True)
    try:
        reply = client.request("c")
        validate_stop(reply, label)
        if signal_number(reply) != 5:
            raise RuntimeError(
                f"{label} did not stop with SIGTRAP at 0x{address:08X}: {reply!r}"
            )
    finally:
        set_breakpoint(client, address, False)


def find_cycle_debit(code: bytes) -> tuple[int | None, list[dict[str, int]]]:
    matches: list[dict[str, int]] = []
    for offset in range(0, len(code) - 3, 4):
        word = int.from_bytes(code[offset : offset + 4], "big")
        if (word & 0xFFFF0000) != 0x22730000:  # ADDI s3,s3,imm
            continue
        imm = word & 0xFFFF
        if imm & 0x8000:
            imm -= 0x10000
        matches.append({"offset": offset, "word": word, "debit": imm})
    if len(matches) == 1:
        return matches[0]["debit"], matches
    return None, matches


def arm_case(client: RSPClient, code: bytes, a: argparse.Namespace) -> None:
    lookup_entry = a.jit_lookup + TEST_PC * 4
    client.write_memory(a.apu_ram + TEST_PC, code)
    client.write_memory(a.apu_count, be(TEST_PC, 2))
    client.write_memory(a.apu_clock, bytes([APU_CLOCK]))
    client.write_memory(lookup_entry, bytes(4))
    client.write_memory(a.jit_pointer, be(JIT_BUFFER, 4))

    if client.read_memory(a.apu_ram + TEST_PC, len(code), len(code)) != code:
        raise RuntimeError("APU test program verification failed")
    if read_u16(client, a.apu_count) != TEST_PC:
        raise RuntimeError("apu_count verification failed")
    if read_u8(client, a.apu_clock) != APU_CLOCK:
        raise RuntimeError("apu_clock verification failed")
    if read_u32(client, lookup_entry) != 0:
        raise RuntimeError("JIT lookup entry did not clear")
    if read_u32(client, a.jit_pointer) != JIT_BUFFER:
        raise RuntimeError("JIT pointer reset verification failed")


def run_case(
    client: RSPClient,
    *,
    name: str,
    source: bytes,
    expected_units: int,
    a: argparse.Namespace,
) -> dict[str, object]:
    continue_to_breakpoint(client, a.apu_execute, f"{name}: apu_execute boundary")
    arm_case(client, source, a)

    # apu_execute may service DSP first; compile_block is the unambiguous
    # boundary proving that this exact injected block is being compiled.
    continue_to_breakpoint(client, a.compile_block, f"{name}: compile_block")
    continue_to_breakpoint(client, a.cpu_execute, f"{name}: first cpu_execute return")

    lookup_entry = a.jit_lookup + TEST_PC * 4
    block = read_u32(client, lookup_entry)
    if block == 0:
        raise RuntimeError(f"{name}: lookup remained zero")

    end_uncached = read_u32(client, a.jit_pointer)
    end_cached = cached(end_uncached)
    code_start = block + 12
    if end_cached <= code_start or end_cached - code_start > 0x4000:
        raise RuntimeError(
            f"{name}: implausible generated range "
            f"0x{code_start:08X}..0x{end_cached:08X}"
        )
    generated = client.read_memory(code_start, end_cached - code_start, 0x400)
    debit, matches = find_cycle_debit(generated)
    units = (-debit // APU_CLOCK) if debit is not None and debit <= 0 else None
    expected_debit = -(expected_units * APU_CLOCK)

    result: dict[str, object] = {
        "name": name,
        "source_hex": source.hex(),
        "source_bytes": len(source),
        "cycle_debit": debit,
        "cycle_debit_matches": matches,
        "guest_cycle_units": units,
        "expected_guest_cycle_units": expected_units,
        "expected_cycle_debit": expected_debit,
        "matches_expected": debit == expected_debit and units == expected_units,
        "apu_count_after_block": read_u16(client, a.apu_count),
        "lookup_block": block,
        "generated_bytes": len(generated),
    }
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=9170)
    p.add_argument("--connect-timeout", type=float, default=45.0)
    p.add_argument("--response-timeout", type=float, default=60.0)
    p.add_argument("--apu-ram", type=parse_int, required=True)
    p.add_argument("--apu-count", type=parse_int, required=True)
    p.add_argument("--apu-clock", type=parse_int, required=True)
    p.add_argument("--jit-lookup", type=parse_int, required=True)
    p.add_argument("--jit-pointer", type=parse_int, required=True)
    p.add_argument("--apu-execute", type=parse_int, required=True)
    p.add_argument("--compile-block", type=parse_int, required=True)
    p.add_argument("--cpu-execute", type=parse_int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    cases = [
        ("bra", bytes.fromhex("2ffe"), 4),
        ("nop_bra", bytes.fromhex("002ffd"), 6),
        ("mul_bra", bytes.fromhex("cf2ffd"), 13),
        ("div_bra", bytes.fromhex("9e2ffd"), 16),
    ]

    client = connect_with_retry(a.host, a.port, a.connect_timeout, a.response_timeout)
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        print(f"GDB server capabilities: {supported.decode('ascii', errors='replace')}")
        if b"swbreak+" not in supported or b"QPassSignals+" not in supported:
            raise RuntimeError("required ares GDB capabilities unavailable")
        print(f"Initial target state: {client.request('?').decode('ascii', errors='replace')}")
        if client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}") != b"OK":
            raise RuntimeError("target rejected QPassSignals")

        # Boot the embedded workload far enough that Sodium64 owns the scheduler.
        validate_stop(client.continue_then_interrupt(1.0), "warmup stop")

        results = [
            run_case(client, name=name, source=source, expected_units=units, a=a)
            for name, source, units in cases
        ]
        summary = {
            "all_total_cycle_cases_match": all(bool(x["matches_expected"]) for x in results),
            "case_count": len(results),
        }
        report = {
            "apu_clock": APU_CLOCK,
            "test_pc": TEST_PC,
            "scope": "Layer-1 total guest cycles only; not bus/I/O cycle ordering",
            "cases": results,
            "summary": summary,
        }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))
        if not summary["all_total_cycle_cases_match"]:
            raise RuntimeError(f"total-cycle architecture proof failed: {summary}")

        try:
            print(f"Detach reply: {client.request('D').decode('ascii', errors='replace')}")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
