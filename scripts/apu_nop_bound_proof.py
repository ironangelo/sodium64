#!/usr/bin/env python3
"""Validate the bounded NOP JIT-block correctness candidate.

The test stops Sodium64 at safe scheduler boundaries, injects a long NOP stream
starting eight bytes before a 64-byte JIT-tag boundary, and observes the exact
generated block. The candidate is valid only if the nominal 16-byte bound is
enforced and a mutation in the covered end-tag region prevents re-entry into
the stale generated block.
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
TEST_PC = 0x0238
APU_CLOCK = 21
BLOCK_SIZE = 16
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


def compile_long_nop_case(client: RSPClient, a: argparse.Namespace) -> dict[str, object]:
    # 126 NOPs plus a terminator that should never be reached by this candidate
    # in a single JIT block. The source payload is deliberately much longer
    # than BLOCK_SIZE.
    source = b"\x00" * 126 + bytes.fromhex("fe80")
    lookup_entry = a.jit_lookup + TEST_PC * 4

    continue_to_breakpoint(client, a.apu_execute, "arm: apu_execute boundary")

    client.write_memory(a.apu_ram + TEST_PC, source)
    client.write_memory(a.apu_count, be(TEST_PC, 2))
    client.write_memory(a.apu_clock, bytes([APU_CLOCK]))
    client.write_memory(lookup_entry, bytes(4))
    client.write_memory(a.jit_pointer, be(JIT_BUFFER, 4))

    if client.read_memory(a.apu_ram + TEST_PC, len(source), 0x100) != source:
        raise RuntimeError("APU NOP stream verification failed")
    if read_u16(client, a.apu_count) != TEST_PC:
        raise RuntimeError("apu_count verification failed")
    if read_u8(client, a.apu_clock) != APU_CLOCK:
        raise RuntimeError("apu_clock verification failed")
    if read_u32(client, lookup_entry) != 0:
        raise RuntimeError("JIT lookup entry did not clear")
    if read_u32(client, a.jit_pointer) != JIT_BUFFER:
        raise RuntimeError("JIT pointer reset verification failed")

    continue_to_breakpoint(client, a.compile_block, "compile: compile_block")
    continue_to_breakpoint(client, a.cpu_execute, "execute: cpu_execute return")

    block = read_u32(client, lookup_entry)
    if block == 0:
        raise RuntimeError("JIT lookup entry remained zero")

    header = client.read_memory(block, 12, 12)
    start_tag_offset = int.from_bytes(header[0:2], "big")
    end_tag_offset = int.from_bytes(header[2:4], "big")
    start_region = start_tag_offset // 4
    end_region = end_tag_offset // 4

    end_uncached = read_u32(client, a.jit_pointer)
    end_cached = cached(end_uncached)
    code_start = block + 12
    if end_cached <= code_start or end_cached - code_start > 0x4000:
        raise RuntimeError(
            f"implausible generated-code range 0x{code_start:08X}..0x{end_cached:08X}"
        )
    generated = client.read_memory(code_start, end_cached - code_start, 0x400)
    debit, debit_matches = find_cycle_debit(generated)
    units = (-debit // APU_CLOCK) if debit is not None and debit <= 0 else None

    result = {
        "test_pc": TEST_PC,
        "source_payload_bytes": len(source),
        "lookup_block": block,
        "generated_code_start": code_start,
        "generated_code_end": end_cached,
        "generated_bytes": len(generated),
        "header_start_region": start_region,
        "header_end_region": end_region,
        "header_start_tag_offset": start_tag_offset,
        "header_end_tag_offset": end_tag_offset,
        "cycle_debit": debit,
        "cycle_debit_matches": debit_matches,
        "source_clock_units": units,
        "apu_count_after_block": read_u16(client, a.apu_count),
        "jit_pointer_uncached": end_uncached,
    }
    print(json.dumps(result, sort_keys=True))
    return result


def probe_covered_end_region_invalidation(
    client: RSPClient,
    *,
    block_result: dict[str, object],
    a: argparse.Namespace,
) -> dict[str, object]:
    lookup_entry = a.jit_lookup + TEST_PC * 4

    start_region = int(block_result["header_start_region"])
    end_region = int(block_result["header_end_region"])
    if end_region != start_region + 1:
        raise RuntimeError(
            f"expected a two-region bounded block, got {start_region}->{end_region}"
        )

    # Stop at the scheduler boundary before changing apu_count/tag state.
    continue_to_breakpoint(client, a.apu_execute, "invalidate: apu_execute boundary")

    old_lookup = read_u32(client, lookup_entry)
    pointer_before = read_u32(client, a.jit_pointer)

    # 0x0240 is inside the 16-byte compiled range 0x0238..0x0247 and belongs
    # to the header's tracked end region. Change NOP->CLRC and advance the tag
    # exactly as apu_write8 would.
    mutation_apu_address = (start_region + 1) * 64
    mutation_addr = a.apu_ram + mutation_apu_address
    tag_addr = a.jit_tags + end_region * 4
    byte_before = read_u8(client, mutation_addr)
    tag_before = read_u32(client, tag_addr)

    client.write_memory(mutation_addr, b"\x60")
    client.write_memory(tag_addr, be((tag_before + 1) & 0xFFFFFFFF, 4))
    client.write_memory(a.apu_count, be(TEST_PC, 2))

    # Continue to the first main-CPU scheduler return. Exactly one APU block
    # has completed at this point. If endpoint validation rejected the cached
    # block, compile_block must have advanced jit_pointer and replaced lookup.
    # This avoids the old ambiguous timed Ctrl-C/SIGTRAP breakpoint criterion.
    continue_to_breakpoint(
        client, a.cpu_execute, "invalidate: first cpu_execute return"
    )

    lookup_after = read_u32(client, lookup_entry)
    pointer_after = read_u32(client, a.jit_pointer)
    lookup_changed = lookup_after != old_lookup
    pointer_advanced = pointer_after != pointer_before
    recompiled_before_return = lookup_changed and pointer_advanced

    result = {
        "mutation_apu_address": mutation_apu_address,
        "mutation_byte_before": byte_before,
        "mutation_byte_after": read_u8(client, mutation_addr),
        "end_region": end_region,
        "tag_before": tag_before,
        "tag_after": read_u32(client, tag_addr),
        "lookup_before": old_lookup,
        "lookup_after": lookup_after,
        "lookup_changed": lookup_changed,
        "jit_pointer_before": pointer_before,
        "jit_pointer_after": pointer_after,
        "jit_pointer_advanced": pointer_advanced,
        "recompiled_before_first_cpu_return": recompiled_before_return,
        "stale_block_reused_without_recompile": not recompiled_before_return,
    }
    print(json.dumps(result, sort_keys=True))
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=9123)
    p.add_argument("--connect-timeout", type=float, default=45.0)
    p.add_argument("--response-timeout", type=float, default=60.0)
    p.add_argument("--apu-ram", type=parse_int, required=True)
    p.add_argument("--apu-count", type=parse_int, required=True)
    p.add_argument("--apu-clock", type=parse_int, required=True)
    p.add_argument("--jit-tags", type=parse_int, required=True)
    p.add_argument("--jit-lookup", type=parse_int, required=True)
    p.add_argument("--jit-pointer", type=parse_int, required=True)
    p.add_argument("--apu-execute", type=parse_int, required=True)
    p.add_argument("--compile-block", type=parse_int, required=True)
    p.add_argument("--cpu-execute", type=parse_int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    client = connect_with_retry(a.host, a.port, a.connect_timeout, a.response_timeout)
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

        validate_stop(client.continue_then_interrupt(1.0), "warmup stop")

        block = compile_long_nop_case(client, a)
        invalidation = probe_covered_end_region_invalidation(
            client, block_result=block, a=a
        )

        expected_end = TEST_PC + BLOCK_SIZE
        summary = {
            "nop_bound_enforced": (
                block["source_clock_units"] == BLOCK_SIZE
                and block["apu_count_after_block"] == expected_end
            ),
            "bounded_block_tracks_only_two_regions": (
                block["header_start_region"] == TEST_PC // 64
                and block["header_end_region"] == expected_end // 64
                and block["header_end_region"] - block["header_start_region"] == 1
            ),
            "covered_end_tag_prevents_stale_reentry": (
                invalidation["recompiled_before_first_cpu_return"]
                and not invalidation["stale_block_reused_without_recompile"]
            ),
        }
        report = {
            "apu_clock": APU_CLOCK,
            "block_size": BLOCK_SIZE,
            "test_pc": TEST_PC,
            "block": block,
            "covered_end_region_invalidation": invalidation,
            "summary": summary,
        }

        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))

        if not all(summary.values()):
            raise RuntimeError(f"NOP-bound candidate did not validate: {summary}")

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
