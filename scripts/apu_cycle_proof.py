#!/usr/bin/env python3
"""Dynamically prove Sodium64 SPC700 JIT cycle debit and block-span behavior.

This diagnostic deliberately observes the inherited JIT without changing it. It
uses ares' GDB RSP server to stop at safe scheduler boundaries, inject tiny
SPC700 snippets into APU RAM, force compilation from a clean lookup entry, and
inspect the generated JIT header/code. A final long-NOP case mutates a middle
64-byte tag region and asks whether the already-cached block is re-entered.

The script records observations instead of assuming the timing/span hypotheses
are true. Setup/integrity failures are fatal; hypothesis falsification is data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gdb_rsp_dump import (
    ARES_N64_GUEST_SIGNALS,
    RSPClient,
    connect_with_retry,
    validate_stop,
)


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
        action = "insert" if enabled else "remove"
        raise RuntimeError(
            f"target rejected {action} breakpoint at 0x{address:08X}: {reply!r}"
        )


def continue_to_breakpoint(client: RSPClient, address: int, label: str) -> bytes:
    set_breakpoint(client, address, True)
    try:
        reply = client.request("c")
        validate_stop(reply, label)
        if signal_number(reply) != 5:
            raise RuntimeError(
                f"{label} did not stop with SIGTRAP at 0x{address:08X}: {reply!r}"
            )
        return reply
    finally:
        # The target is stopped when this succeeds, so removing the breakpoint
        # cannot race guest execution.
        set_breakpoint(client, address, False)


def find_cycle_debit(code: bytes) -> tuple[int | None, list[dict[str, int]]]:
    """Find emitted ADDI s3,s3,imm instructions and return their signed immediates."""
    matches: list[dict[str, int]] = []
    for offset in range(0, len(code) - 3, 4):
        word = int.from_bytes(code[offset : offset + 4], "big")
        if (word & 0xFFFF0000) != 0x22730000:
            continue
        imm = word & 0xFFFF
        if imm & 0x8000:
            imm -= 0x10000
        matches.append({"offset": offset, "word": word, "debit": imm})
    if len(matches) == 1:
        return matches[0]["debit"], matches
    return None, matches


def arm_case(
    client: RSPClient,
    *,
    code: bytes,
    apu_ram: int,
    apu_count: int,
    apu_clock: int,
    apu_reg_y: int,
    jit_lookup: int,
    jit_pointer: int,
    y_value: int = 0x5A,
) -> None:
    lookup_entry = jit_lookup + TEST_PC * 4
    client.write_memory(apu_ram + TEST_PC, code)
    client.write_memory(apu_count, be(TEST_PC, 2))
    client.write_memory(apu_clock, bytes([APU_CLOCK]))
    client.write_memory(apu_reg_y, bytes([y_value & 0xFF]))
    client.write_memory(lookup_entry, bytes(4))
    client.write_memory(jit_pointer, be(JIT_BUFFER, 4))

    # Verify every piece of state that makes the experiment deterministic.
    if client.read_memory(apu_ram + TEST_PC, len(code), min(len(code), 0x100)) != code:
        raise RuntimeError("APU test program verification failed")
    if read_u16(client, apu_count) != TEST_PC:
        raise RuntimeError("apu_count verification failed")
    if read_u8(client, apu_clock) != APU_CLOCK:
        raise RuntimeError("apu_clock verification failed")
    if read_u32(client, lookup_entry) != 0:
        raise RuntimeError("JIT lookup entry did not clear")
    if read_u32(client, jit_pointer) != JIT_BUFFER:
        raise RuntimeError("JIT pointer reset verification failed")


def compile_one_case(
    client: RSPClient,
    *,
    name: str,
    code: bytes,
    expected_debit: int,
    reference_cycles: int | None,
    expected_end_region: int,
    y_value: int,
    addresses: argparse.Namespace,
) -> dict[str, object]:
    # Arrive before apu_execute touches s0/lookup. This avoids changing apu_count
    # while an old generated block is still in flight.
    continue_to_breakpoint(client, addresses.apu_execute, f"{name}: apu_execute boundary")

    arm_case(
        client,
        code=code,
        apu_ram=addresses.apu_ram,
        apu_count=addresses.apu_count,
        apu_clock=addresses.apu_clock,
        apu_reg_y=addresses.apu_reg_y,
        jit_lookup=addresses.jit_lookup,
        jit_pointer=addresses.jit_pointer,
        y_value=y_value,
    )

    # apu_execute can service DSP first depending on s3/a3. Waiting specifically
    # for compile_block makes the test independent of that scheduler phase.
    continue_to_breakpoint(client, addresses.compile_block, f"{name}: compile_block")
    # Starting at compile_block now guarantees the next return to cpu_execute is
    # the block we just compiled/executed.
    continue_to_breakpoint(client, addresses.cpu_execute, f"{name}: cpu_execute return")

    lookup_entry = addresses.jit_lookup + TEST_PC * 4
    block = read_u32(client, lookup_entry)
    if block == 0:
        raise RuntimeError(f"{name}: JIT lookup entry remained zero")

    header = client.read_memory(block, 12, 12)
    start_tag_offset = int.from_bytes(header[0:2], "big")
    end_tag_offset = int.from_bytes(header[2:4], "big")
    start_region = start_tag_offset // 4
    end_region = end_tag_offset // 4

    end_uncached = read_u32(client, addresses.jit_pointer)
    end_cached = cached(end_uncached)
    code_start = block + 12
    if end_cached <= code_start or end_cached - code_start > 0x4000:
        raise RuntimeError(
            f"{name}: implausible generated-code range "
            f"0x{code_start:08X}..0x{end_cached:08X}"
        )
    generated = client.read_memory(code_start, end_cached - code_start, 0x400)
    debit, debit_matches = find_cycle_debit(generated)

    result: dict[str, object] = {
        "name": name,
        "test_pc": TEST_PC,
        "source_bytes": len(code),
        "lookup_block": block,
        "generated_code_start": code_start,
        "generated_code_end": end_cached,
        "generated_bytes": len(generated),
        "header_start_tag_offset": start_tag_offset,
        "header_end_tag_offset": end_tag_offset,
        "header_start_region": start_region,
        "header_end_region": end_region,
        "cycle_debit": debit,
        "cycle_debit_matches": debit_matches,
        "expected_cycle_debit": expected_debit,
        "cycle_debit_matches_expected": debit == expected_debit,
        "source_clock_units": (-debit // APU_CLOCK) if debit is not None and debit <= 0 else None,
        "reference_spc_cycles": reference_cycles,
        "expected_end_region": expected_end_region,
        "span_matches_expected": start_region == TEST_PC // 64 and end_region == expected_end_region,
        "apu_count_after_block": read_u16(client, addresses.apu_count),
        "apu_reg_y_after_block": read_u8(client, addresses.apu_reg_y),
        "jit_pointer_uncached": end_uncached,
    }
    print(json.dumps(result, sort_keys=True))
    return result


def middle_region_reentry(
    client: RSPClient,
    *,
    long_result: dict[str, object],
    addresses: argparse.Namespace,
) -> dict[str, object]:
    start_region = TEST_PC // 64
    middle_region = start_region + 1
    if int(long_result["header_end_region"]) <= middle_region:
        result = {
            "applicable": False,
            "middle_region": middle_region,
            "reason": "bounded block has no untracked intermediate tag region",
            "lookup_changed": None,
            "jit_pointer_changed": None,
            "recompiled_before_first_cpu_return": None,
            "stale_block_reused_without_recompile": None,
        }
        print(json.dumps(result, sort_keys=True))
        return result

    lookup_entry = addresses.jit_lookup + TEST_PC * 4

    # Arrive at a safe APU scheduler boundary before changing PC/tag state.
    continue_to_breakpoint(
        client, addresses.apu_execute, "middle-region: apu_execute boundary"
    )

    old_lookup = read_u32(client, lookup_entry)
    pointer_before = read_u32(client, addresses.jit_pointer)
    tag_addr = addresses.jit_tags + middle_region * 4
    tag_before = read_u32(client, tag_addr)

    # Mutate an actually covered byte in region 9 from NOP to CLRC and advance
    # the tag exactly as apu_write8 would. Header endpoint tags (regions 8/10)
    # are deliberately left untouched.
    mutation_addr = addresses.apu_ram + middle_region * 64
    byte_before = read_u8(client, mutation_addr)
    client.write_memory(mutation_addr, b"\x60")
    client.write_memory(tag_addr, be((tag_before + 1) & 0xFFFFFFFF, 4))
    client.write_memory(addresses.apu_count, be(TEST_PC, 2))

    # Stop at the first scheduler return from this APU execution. If endpoint-
    # only validation accepted the stale block, no compilation occurs and both
    # lookup and jit_pointer remain unchanged. If validation rejected it,
    # compile_block necessarily changes both before this return.
    continue_to_breakpoint(
        client, addresses.cpu_execute, "middle-region: first cpu_execute return"
    )

    pointer_after = read_u32(client, addresses.jit_pointer)
    lookup_after = read_u32(client, lookup_entry)
    lookup_changed = lookup_after != old_lookup
    pointer_changed = pointer_after != pointer_before
    recompiled_before_return = lookup_changed and pointer_changed
    stale_reused = not recompiled_before_return

    result = {
        "middle_region": middle_region,
        "mutation_apu_address": middle_region * 64,
        "mutation_byte_before": byte_before,
        "mutation_byte_after": read_u8(client, mutation_addr),
        "tag_before": tag_before,
        "tag_after": read_u32(client, tag_addr),
        "lookup_before": old_lookup,
        "lookup_after": lookup_after,
        "lookup_changed": lookup_changed,
        "jit_pointer_before": pointer_before,
        "jit_pointer_after": pointer_after,
        "jit_pointer_changed": pointer_changed,
        "recompiled_before_first_cpu_return": recompiled_before_return,
        "stale_block_reused_without_recompile": stale_reused,
    }
    print(json.dumps(result, sort_keys=True))
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9123)
    parser.add_argument("--connect-timeout", type=float, default=45.0)
    parser.add_argument("--response-timeout", type=float, default=60.0)
    parser.add_argument("--apu-ram", type=parse_int, required=True)
    parser.add_argument("--apu-count", type=parse_int, required=True)
    parser.add_argument("--apu-clock", type=parse_int, required=True)
    parser.add_argument("--apu-reg-y", type=parse_int, required=True)
    parser.add_argument("--jit-tags", type=parse_int, required=True)
    parser.add_argument("--jit-lookup", type=parse_int, required=True)
    parser.add_argument("--jit-pointer", type=parse_int, required=True)
    parser.add_argument("--apu-execute", type=parse_int, required=True)
    parser.add_argument("--compile-block", type=parse_int, required=True)
    parser.add_argument("--cpu-execute", type=parse_int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cases = [
        ("bra", bytes.fromhex("2ffe"), -84, 4, 8, 0x5A),
        ("nop_bra", bytes.fromhex("002ffd"), -126, 6, 8, 0x5A),
        ("mul_bra", bytes.fromhex("cf2ffd"), -273, 13, 8, 0x5A),
        ("div_bra", bytes.fromhex("9e2ffd"), -336, 16, 8, 0x5A),
        # Regression probe: source contains 126 NOPs + DBNZ Y,-128, but with
        # NOP routed through finish_opcode the compiler must stop after the
        # first 16 bytes at the existing BLOCK_SIZE boundary.
        ("long_nop_dbnzy", b"\x00" * 126 + bytes.fromhex("fe80"), -672, None, 8, 0xFF),
    ]

    client = connect_with_retry(args.host, args.port, args.connect_timeout, args.response_timeout)
    results: list[dict[str, object]] = []
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        print(f"GDB server capabilities: {supported.decode('ascii', errors='replace')}")
        if b"swbreak+" not in supported:
            raise RuntimeError("GDB server does not advertise software breakpoints")
        if b"QPassSignals+" not in supported:
            raise RuntimeError("GDB server does not advertise QPassSignals support")

        initial = client.request("?")
        print(f"Initial target state: {initial.decode('ascii', errors='replace')}")
        pass_reply = client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}")
        if pass_reply != b"OK":
            raise RuntimeError(f"target rejected QPassSignals: {pass_reply!r}")

        # Let Sodium64 boot the embedded workload before taking over the APU.
        validate_stop(client.continue_then_interrupt(1.0), "warmup stop")

        for name, code, expected_debit, reference_cycles, expected_end_region, y_value in cases:
            result = compile_one_case(
                client,
                name=name,
                code=code,
                expected_debit=expected_debit,
                reference_cycles=reference_cycles,
                expected_end_region=expected_end_region,
                y_value=y_value,
                addresses=args,
            )
            results.append(result)

        long_result = next(item for item in results if item["name"] == "long_nop_dbnzy")
        reentry = middle_region_reentry(client, long_result=long_result, addresses=args)

        report = {
            "apu_clock": APU_CLOCK,
            "test_pc": TEST_PC,
            "jit_buffer": JIT_BUFFER,
            "cases": results,
            "middle_region_reentry": reentry,
            "summary": {
                "all_static_debits_match_source_prediction": all(
                    bool(item["cycle_debit_matches_expected"]) for item in results
                ),
                "all_header_spans_match_source_prediction": all(
                    bool(item["span_matches_expected"]) for item in results
                ),
                "long_source_program_exceeds_block_size": int(long_result["source_bytes"]) > 16,
                "compiled_long_probe_is_bounded_to_one_tag_region": (
                    int(long_result["header_end_region"])
                    == int(long_result["header_start_region"])
                    and int(long_result["source_clock_units"]) == 32
                ),
                "middle_region_probe_applicable": bool(reentry.get("applicable", True)),
                "stale_block_reentered_after_middle_tag_mutation": (
                    reentry["stale_block_reused_without_recompile"]
                    if reentry.get("applicable", True) else None
                ),
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report["summary"], indent=2, sort_keys=True))

        try:
            reply = client.request("D")
            print(f"Detach reply: {reply.decode('ascii', errors='replace')}")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
