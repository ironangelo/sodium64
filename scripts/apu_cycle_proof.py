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
S3_GPR_INDEX = 19
A0_GPR_INDEX = 4


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


def read_gpr(client: RSPClient, index: int) -> int:
    reply = client.request(f"p{index:x}")
    if len(reply) == 3 and reply.startswith(b"E"):
        raise RuntimeError(f"target rejected GPR read p{index:x}: {reply!r}")
    text = reply.decode("ascii")
    if len(text) != 16:
        raise RuntimeError(f"unexpected 64-bit GPR reply for p{index:x}: {reply!r}")
    try:
        return int(text, 16)
    except ValueError as exc:
        raise RuntimeError(f"invalid GPR reply for p{index:x}: {reply!r}") from exc


def signed_delta_u64(after: int, before: int) -> int:
    delta = (after - before) & 0xFFFFFFFFFFFFFFFF
    if delta & (1 << 63):
        delta -= 1 << 64
    return delta


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
    if matches:
        # finish_block emits the block-wide static debit last. Earlier s3
        # ADDIs are explicit conditional runtime timing charges.
        return matches[-1]["debit"], matches
    return None, matches


def arm_case(
    client: RSPClient,
    *,
    code: bytes,
    apu_ram: int,
    apu_map: int,
    apu_count: int,
    apu_clock: int,
    apu_reg_x: int,
    apu_reg_y: int,
    apu_accum: int,
    apu_stack: int,
    apu_flags: int,
    apu_halt: int,
    jit_lookup: int,
    jit_pointer: int,
    x_value: int = 0x04,
    y_value: int = 0x06,
    a_value: int = 0x11,
    stack_value: int = 0x7F,
    flags_value: int = 0x00,
    memory_writes: tuple[tuple[int, bytes], ...] = (),
) -> None:
    lookup_entry = jit_lookup + TEST_PC * 4
    client.write_memory(apu_ram + TEST_PC, code)
    # Force the top 64-byte page to RAM so TCALL/BRK vector reads are
    # deterministic and do not depend on the guest's inherited IPL-ROM mapping.
    client.write_memory(apu_map + 0x3FF, b"\x00")
    client.write_memory(apu_count, be(TEST_PC, 2))
    client.write_memory(apu_clock, bytes([APU_CLOCK]))
    client.write_memory(apu_reg_x, bytes([x_value & 0xFF]))
    client.write_memory(apu_reg_y, bytes([y_value & 0xFF]))
    client.write_memory(apu_accum, bytes([a_value & 0xFF]))
    client.write_memory(apu_stack, bytes([stack_value & 0xFF]))
    client.write_memory(apu_flags, bytes([flags_value & 0xFF]))
    client.write_memory(apu_halt, b"\x00")
    for offset, data in memory_writes:
        client.write_memory(apu_ram + offset, data)
    client.write_memory(lookup_entry, bytes(4))
    client.write_memory(jit_pointer, be(JIT_BUFFER, 4))

    # Verify every piece of state that makes the experiment deterministic.
    if client.read_memory(apu_ram + TEST_PC, len(code), min(len(code), 0x100)) != code:
        raise RuntimeError("APU test program verification failed")
    if read_u8(client, apu_map + 0x3FF) != 0:
        raise RuntimeError("apu_map top-page verification failed")
    if read_u16(client, apu_count) != TEST_PC:
        raise RuntimeError("apu_count verification failed")
    if read_u8(client, apu_clock) != APU_CLOCK:
        raise RuntimeError("apu_clock verification failed")
    if read_u8(client, apu_reg_x) != (x_value & 0xFF):
        raise RuntimeError("apu_reg_x verification failed")
    if read_u8(client, apu_reg_y) != (y_value & 0xFF):
        raise RuntimeError("apu_reg_y verification failed")
    if read_u8(client, apu_accum) != (a_value & 0xFF):
        raise RuntimeError("apu_accum verification failed")
    if read_u8(client, apu_stack) != (stack_value & 0xFF):
        raise RuntimeError("apu_stack verification failed")
    if read_u8(client, apu_flags) != (flags_value & 0xFF):
        raise RuntimeError("apu_flags verification failed")
    if read_u8(client, apu_halt) != 0:
        raise RuntimeError("apu_halt verification failed")
    for offset, data in memory_writes:
        if client.read_memory(apu_ram + offset, len(data), len(data)) != data:
            raise RuntimeError(f"APU data patch verification failed at 0x{offset:04X}")
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
    x_value: int = 0x04,
    a_value: int = 0x11,
    stack_value: int = 0x7F,
    flags_value: int = 0x00,
    memory_writes: tuple[tuple[int, bytes], ...] = (),
    expected_accum: int | None = None,
    expected_x: int | None = None,
    expected_memory: tuple[int, int] | None = None,
    expected_memories: tuple[tuple[int, int], ...] = (),
    expected_y: int | None = None,
    expected_stack: int | None = None,
    expected_flags: int | None = None,
    expected_pc_after: int | None = None,
    expected_halt: int | None = None,
    expected_runtime_debits: tuple[int, ...] = (),
) -> dict[str, object]:
    # Arrive before apu_execute touches s0/lookup. This avoids changing apu_count
    # while an old generated block is still in flight.
    continue_to_breakpoint(client, addresses.apu_execute, f"{name}: apu_execute boundary")

    arm_case(
        client,
        code=code,
        apu_ram=addresses.apu_ram,
        apu_map=addresses.apu_map,
        apu_count=addresses.apu_count,
        apu_clock=addresses.apu_clock,
        apu_reg_x=addresses.apu_reg_x,
        apu_reg_y=addresses.apu_reg_y,
        apu_accum=addresses.apu_accum,
        apu_stack=addresses.apu_stack,
        apu_flags=addresses.apu_flags,
        apu_halt=addresses.apu_halt,
        jit_lookup=addresses.jit_lookup,
        jit_pointer=addresses.jit_pointer,
        x_value=x_value,
        y_value=y_value,
        a_value=a_value,
        stack_value=stack_value,
        flags_value=flags_value,
        memory_writes=memory_writes,
    )

    # apu_execute can service DSP first depending on s3/a3. Waiting specifically
    # for compile_block makes the test independent of that scheduler phase.
    continue_to_breakpoint(client, addresses.compile_block, f"{name}: compile_block")
    s3_before = read_gpr(client, S3_GPR_INDEX)
    # Starting at compile_block now guarantees the next return to cpu_execute is
    # the block we just compiled/executed.
    continue_to_breakpoint(client, addresses.cpu_execute, f"{name}: cpu_execute return")
    s3_after = read_gpr(client, S3_GPR_INDEX)
    total_cycle_debit = signed_delta_u64(s3_after, s3_before)
    expected_total_debit = (
        -reference_cycles * APU_CLOCK if reference_cycles is not None else None
    )

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
        "runtime_cycle_debits": [item["debit"] for item in debit_matches[:-1]],
        "expected_runtime_cycle_debits": list(expected_runtime_debits),
        "runtime_cycle_debits_match_expected": (
            [item["debit"] for item in debit_matches[:-1]] == list(expected_runtime_debits)
        ),
        "source_clock_units": (-debit // APU_CLOCK) if debit is not None and debit <= 0 else None,
        "reference_spc_cycles": reference_cycles,
        "s3_before": s3_before,
        "s3_after": s3_after,
        "total_cycle_debit": total_cycle_debit,
        "total_clock_units": (
            -total_cycle_debit // APU_CLOCK if total_cycle_debit <= 0 else None
        ),
        "expected_total_cycle_debit": expected_total_debit,
        "total_cycle_debit_matches_reference": (
            expected_total_debit is None or total_cycle_debit == expected_total_debit
        ),
        "expected_end_region": expected_end_region,
        "span_matches_expected": start_region == TEST_PC // 64 and end_region == expected_end_region,
        "apu_count_after_block": read_u16(client, addresses.apu_count),
        "apu_reg_x_after_block": read_u8(client, addresses.apu_reg_x),
        "apu_reg_y_after_block": read_u8(client, addresses.apu_reg_y),
        "apu_accum_after_block": read_u8(client, addresses.apu_accum),
        "apu_stack_after_block": read_u8(client, addresses.apu_stack),
        "apu_flags_after_block": read_u8(client, addresses.apu_flags),
        "apu_halt_after_block": read_u8(client, addresses.apu_halt),
        "jit_pointer_uncached": end_uncached,
    }

    if expected_pc_after is None:
        expected_pc_after = TEST_PC + 11 if name == "long_nop_dbnzy" else TEST_PC
    result["expected_apu_count_after_block"] = expected_pc_after
    semantic_checks: list[bool] = [
        result["apu_count_after_block"] == expected_pc_after
    ]
    if expected_accum is not None:
        semantic_checks.append(result["apu_accum_after_block"] == expected_accum)
    if expected_x is not None:
        semantic_checks.append(result["apu_reg_x_after_block"] == expected_x)
    if expected_y is not None:
        semantic_checks.append(result["apu_reg_y_after_block"] == expected_y)
    if expected_stack is not None:
        semantic_checks.append(result["apu_stack_after_block"] == expected_stack)
    if expected_flags is not None:
        semantic_checks.append(result["apu_flags_after_block"] == expected_flags)
    if expected_halt is not None:
        semantic_checks.append(result["apu_halt_after_block"] == expected_halt)
    if expected_memory is not None:
        offset, value = expected_memory
        observed = read_u8(client, addresses.apu_ram + offset)
        result["expected_memory_offset"] = offset
        result["expected_memory_value"] = value
        result["observed_memory_value"] = observed
        semantic_checks.append(observed == value)
    if expected_memories:
        checks = []
        for offset, value in expected_memories:
            observed = read_u8(client, addresses.apu_ram + offset)
            checks.append({"offset": offset, "expected": value, "observed": observed})
            semantic_checks.append(observed == value)
        result["memory_checks"] = checks
    result["semantics_match_expected"] = all(semantic_checks)

    print(json.dumps(result, sort_keys=True))
    if not result["cycle_debit_matches_expected"]:
        raise RuntimeError(f"{name}: static cycle debit mismatch")
    if not result["runtime_cycle_debits_match_expected"]:
        raise RuntimeError(f"{name}: generated runtime cycle debit shape mismatch")
    if not result["total_cycle_debit_matches_reference"]:
        raise RuntimeError(f"{name}: total s3 cycle debit mismatch")
    if not result["span_matches_expected"]:
        raise RuntimeError(f"{name}: JIT header span mismatch")
    if not result["semantics_match_expected"]:
        raise RuntimeError(f"{name}: semantic postcondition mismatch")
    return result



def verify_cycle_budget_reuse(
    client: RSPClient,
    *,
    base_result: dict[str, object],
    addresses: argparse.Namespace,
) -> dict[str, object]:
    """Verify cached execution is stable and a covered-region tag change recompiles."""

    lookup_entry = addresses.jit_lookup + TEST_PC * 4

    def restore_guest_state() -> None:
        # Restore only guest-visible state. Keep JIT lookup/pointer/tags intact so
        # the next entry genuinely exercises the cached block.
        client.write_memory(addresses.apu_count, be(TEST_PC, 2))
        client.write_memory(addresses.apu_reg_x, b"\x04")
        client.write_memory(addresses.apu_reg_y, b"\x01")
        client.write_memory(addresses.apu_accum, b"\x08")
        client.write_memory(addresses.apu_stack, b"\x7f")
        client.write_memory(addresses.apu_flags, b"\x49")
        client.write_memory(addresses.apu_halt, b"\x00")

    # First, prove an unchanged cached entry executes without compilation.
    continue_to_breakpoint(client, addresses.apu_execute, "budget-reuse: cached boundary")
    lookup_before = read_u32(client, lookup_entry)
    pointer_before = read_u32(client, addresses.jit_pointer)
    restore_guest_state()
    s3_before = read_gpr(client, S3_GPR_INDEX)
    continue_to_breakpoint(client, addresses.cpu_execute, "budget-reuse: cached return")
    s3_after = read_gpr(client, S3_GPR_INDEX)
    lookup_after = read_u32(client, lookup_entry)
    pointer_after = read_u32(client, addresses.jit_pointer)

    cached_debit = signed_delta_u64(s3_after, s3_before)
    cached_pc = read_u16(client, addresses.apu_count)
    cached_a = read_u8(client, addresses.apu_accum)
    cached_y = read_u8(client, addresses.apu_reg_y)
    cached_flags = read_u8(client, addresses.apu_flags)
    cached_reused = (
        lookup_after == lookup_before
        and pointer_after == pointer_before
        and cached_debit == -32 * APU_CLOCK
        and cached_pc == TEST_PC + 11
        and cached_a == 0x42
        and cached_y == 0x00
        and cached_flags == 0x01
    )

    # Then change a byte in the covered tag region and advance that region's tag
    # exactly as an APU write would. Entry validation must reject the stale block.
    continue_to_breakpoint(client, addresses.apu_execute, "budget-reuse: tag boundary")
    region = TEST_PC // 64
    tag_addr = addresses.jit_tags + region * 4
    tag_before = read_u32(client, tag_addr)
    mutation_addr = addresses.apu_ram + TEST_PC
    mutation_before = read_u8(client, mutation_addr)
    client.write_memory(mutation_addr, b"\x60")  # CLRC, same 1-byte/2-cycle shape as NOP.
    client.write_memory(tag_addr, be((tag_before + 1) & 0xFFFFFFFF, 4))
    restore_guest_state()

    stale_lookup = read_u32(client, lookup_entry)
    stale_pointer = read_u32(client, addresses.jit_pointer)
    continue_to_breakpoint(client, addresses.cpu_execute, "budget-reuse: recompiled return")
    recompiled_lookup = read_u32(client, lookup_entry)
    recompiled_pointer = read_u32(client, addresses.jit_pointer)
    tag_after = read_u32(client, tag_addr)

    recompiled = (
        recompiled_lookup != stale_lookup
        and recompiled_pointer != stale_pointer
        and tag_after == ((tag_before + 1) & 0xFFFFFFFF)
    )

    result = {
        "base_case": base_result["name"],
        "cached_lookup_before": lookup_before,
        "cached_lookup_after": lookup_after,
        "cached_pointer_before": pointer_before,
        "cached_pointer_after": pointer_after,
        "cached_cycle_debit": cached_debit,
        "cached_pc_after": cached_pc,
        "cached_accum_after": cached_a,
        "cached_y_after": cached_y,
        "cached_flags_after": cached_flags,
        "cached_reused_without_recompile": cached_reused,
        "tag_region": region,
        "mutation_address": TEST_PC,
        "mutation_before": mutation_before,
        "mutation_after": read_u8(client, mutation_addr),
        "tag_before": tag_before,
        "tag_after": tag_after,
        "stale_lookup_before_reentry": stale_lookup,
        "recompiled_lookup_after_reentry": recompiled_lookup,
        "stale_pointer_before_reentry": stale_pointer,
        "recompiled_pointer_after_reentry": recompiled_pointer,
        "tag_mutation_forced_recompile": recompiled,
    }
    print(json.dumps(result, sort_keys=True))
    if not cached_reused:
        raise RuntimeError("cycle-budget cached block did not reproduce initial execution")
    if not recompiled:
        raise RuntimeError("cycle-budget tag mutation reused a stale block")
    return result


def measure_halt_ticks(
    client: RSPClient,
    *,
    name: str,
    expected_halt: int,
    addresses: argparse.Namespace,
    ticks: int = 2,
) -> dict[str, object]:
    expected_pc = TEST_PC + 1
    observations: list[dict[str, object]] = []

    if read_u16(client, addresses.apu_count) != expected_pc:
        raise RuntimeError(f"{name}: entry PC did not advance to instruction-after-opcode")
    if read_u8(client, addresses.apu_halt) != expected_halt:
        raise RuntimeError(f"{name}: halt latch mismatch after entry")

    for index in range(ticks):
        continue_to_breakpoint(
            client, addresses.apu_execute, f"{name}: halted apu_execute tick {index + 1}"
        )
        s3_before = read_gpr(client, S3_GPR_INDEX)
        pc_before = read_u16(client, addresses.apu_count)
        halt_before = read_u8(client, addresses.apu_halt)
        pointer_before = read_u32(client, addresses.jit_pointer)

        continue_to_breakpoint(
            client, addresses.apu_read8, f"{name}: halted read tick {index + 1}"
        )
        read_address = read_gpr(client, A0_GPR_INDEX) & 0xFFFF

        continue_to_breakpoint(
            client, addresses.cpu_execute, f"{name}: halted cpu return tick {index + 1}"
        )
        s3_after = read_gpr(client, S3_GPR_INDEX)
        pc_after = read_u16(client, addresses.apu_count)
        halt_after = read_u8(client, addresses.apu_halt)
        pointer_after = read_u32(client, addresses.jit_pointer)
        debit = signed_delta_u64(s3_after, s3_before)

        tick = {
            "tick": index + 1,
            "s3_before": s3_before,
            "s3_after": s3_after,
            "cycle_debit": debit,
            "expected_cycle_debit": -2 * APU_CLOCK,
            "pc_before": pc_before,
            "pc_after": pc_after,
            "read_address": read_address,
            "halt_before": halt_before,
            "halt_after": halt_after,
            "jit_pointer_before": pointer_before,
            "jit_pointer_after": pointer_after,
        }
        tick["matches_expected"] = (
            debit == -2 * APU_CLOCK
            and pc_before == expected_pc
            and pc_after == expected_pc
            and read_address == expected_pc
            and halt_before == expected_halt
            and halt_after == expected_halt
            and pointer_before == pointer_after
        )
        observations.append(tick)
        print(json.dumps({"name": name, **tick}, sort_keys=True))

    result = {
        "name": name,
        "expected_halt": expected_halt,
        "expected_pc": expected_pc,
        "ticks": observations,
        "all_ticks_match_expected": all(bool(item["matches_expected"]) for item in observations),
    }
    if not result["all_ticks_match_expected"]:
        raise RuntimeError(f"{name}: persistent halt scheduler semantics mismatch")
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
    parser.add_argument("--apu-map", type=parse_int, required=True)
    parser.add_argument("--apu-count", type=parse_int, required=True)
    parser.add_argument("--apu-clock", type=parse_int, required=True)
    parser.add_argument("--apu-reg-x", type=parse_int, required=True)
    parser.add_argument("--apu-reg-y", type=parse_int, required=True)
    parser.add_argument("--apu-accum", type=parse_int, required=True)
    parser.add_argument("--apu-stack", type=parse_int, required=True)
    parser.add_argument("--apu-flags", type=parse_int, required=True)
    parser.add_argument("--apu-halt", type=parse_int, required=True)
    parser.add_argument("--jit-tags", type=parse_int, required=True)
    parser.add_argument("--jit-lookup", type=parse_int, required=True)
    parser.add_argument("--jit-pointer", type=parse_int, required=True)
    parser.add_argument("--apu-execute", type=parse_int, required=True)
    parser.add_argument("--apu-read8", type=parse_int, required=True)
    parser.add_argument("--compile-block", type=parse_int, required=True)
    parser.add_argument("--cpu-execute", type=parse_int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cases = [
        ("bra", bytes.fromhex("2ffe"), -84, 4, 8, 0x5A),
        ("nop_bra", bytes.fromhex("002ffd"), -126, 6, 8, 0x5A),
        ("mul_bra", bytes.fromhex("cf2ffd"), -273, 13, 8, 0x5A),
        ("div_bra", bytes.fromhex("9e2ffd"), -336, 16, 8, 0x5A),
        # Regression probe: source contains 126 NOPs + DBNZ Y,-128. With the
        # cycle-bounded compiler, 11 two-cycle NOPs produce a 22-cycle block;
        # the temporal limit intentionally stops before the old 16-byte bound.
        ("long_nop_dbnzy", b"\x00" * 126 + bytes.fromhex("fe80"), -462, 22, 8, 0xFF),
    ]


    budget_edge_cases = [
        # Exact temporal edge: 10 NOPs = 20 cycles, then the 12-cycle DIV.
        # A trailing sentinel NOP must NOT enter this block. Total = 32 cycles.
        dict(
            name="budget_20_nop_div_32",
            code=(b"\x00" * 10) + bytes.fromhex("9e00"),
            expected_debit=-672,
            reference_cycles=32,
            expected_end_region=8,
            x_value=0x04,
            y_value=0x01,
            a_value=0x08,
            flags_value=0x49,
            expected_pc_after=TEST_PC + 11,
            expected_accum=0x42,
            expected_y=0x00,
            expected_flags=0x01,
        ),
        # Same 20-cycle prefix, but 12 cycles come from four real guest reads
        # (OR A,dp = 2 static source cycles + 1 apu_read8 runtime cycle each)
        # and 8 cycles from four NOPs. DIV takes the block to exactly 32.
        dict(
            name="budget_20_access_div_32",
            code=(bytes.fromhex("0420") * 4) + (b"\x00" * 4) + bytes.fromhex("9e00"),
            expected_debit=-588,
            reference_cycles=32,
            expected_end_region=8,
            x_value=0x04,
            y_value=0x01,
            a_value=0x08,
            flags_value=0x49,
            memory_writes=((0x0020, b"\x00"),),
            expected_pc_after=TEST_PC + 13,
            expected_accum=0x42,
            expected_y=0x00,
            expected_flags=0x01,
        ),
        # Near-cut conditional path: 9 NOPs = 18 cycles; BPL has a 2-cycle
        # base and +2 when taken. Compiler budgeting must conservatively account
        # for the 22-cycle taken path while runtime totals remain path-correct.
        dict(
            name="budget_branch_taken_22",
            code=(b"\x00" * 9) + bytes.fromhex("10fe00"),
            expected_debit=-420,
            reference_cycles=22,
            expected_end_region=8,
            y_value=0x06,
            flags_value=0x00,
            expected_pc_after=TEST_PC + 9,
            expected_runtime_debits=(-42,),
        ),
        dict(
            name="budget_branch_not_taken_20",
            code=(b"\x00" * 9) + bytes.fromhex("10fe00"),
            expected_debit=-420,
            reference_cycles=20,
            expected_end_region=8,
            y_value=0x06,
            flags_value=0x80,
            expected_pc_after=TEST_PC + 11,
            expected_runtime_debits=(-42,),
        ),
    ]


    address_cases = [
        dict(name="direct_read", code=bytes.fromhex("04202ffc"), expected_debit=-126,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x22"),), expected_accum=0x33),
        dict(name="direct_write", code=bytes.fromhex("c4202ffc"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x33"),), expected_memory=(0x0020, 0x11)),
        dict(name="direct_x_read", code=bytes.fromhex("14202ffc"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0024, b"\x22"),), expected_accum=0x33),
        dict(name="direct_x_write", code=bytes.fromhex("d4202ffc"), expected_debit=-168,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0024, b"\x33"),), expected_memory=(0x0024, 0x11)),
        dict(name="indirect_x_read", code=bytes.fromhex("062ffd"), expected_debit=-126,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0004, b"\x22"),), expected_accum=0x33),
        dict(name="indirect_x_write", code=bytes.fromhex("c62ffd"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0004, b"\x33"),), expected_memory=(0x0004, 0x11)),
        dict(name="indirect_x_inc_read", code=bytes.fromhex("bf2ffd"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0004, b"\x22"),), expected_accum=0x22, expected_x=0x05),
        dict(name="indirect_x_inc_write", code=bytes.fromhex("af2ffd"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0004, b"\x33"),), expected_x=0x05,
             expected_memory=(0x0004, 0x11)),
        dict(name="absolute_read", code=bytes.fromhex("0500042ffb"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0400, b"\x22"),), expected_accum=0x33),
        dict(name="absolute_write", code=bytes.fromhex("c500042ffb"), expected_debit=-168,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0400, b"\x33"),), expected_memory=(0x0400, 0x11)),
        dict(name="absolute_x_read", code=bytes.fromhex("1500042ffb"), expected_debit=-168,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0404, b"\x22"),), expected_accum=0x33),
        dict(name="absolute_x_write", code=bytes.fromhex("d500042ffb"), expected_debit=-189,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0404, b"\x33"),), expected_memory=(0x0404, 0x11)),
        dict(name="indexed_indirect_read", code=bytes.fromhex("07402ffc"), expected_debit=-147,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0044, b"\x00\x04"), (0x0400, b"\x22")),
             expected_accum=0x33),
        dict(name="indexed_indirect_write", code=bytes.fromhex("c7402ffc"), expected_debit=-168,
             reference_cycles=11, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0044, b"\x00\x04"), (0x0400, b"\x33")),
             expected_memory=(0x0400, 0x11)),
        dict(name="indirect_indexed_read", code=bytes.fromhex("17502ffc"), expected_debit=-147,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0050, b"\x00\x04"), (0x0406, b"\x22")),
             expected_accum=0x33),
        dict(name="indirect_indexed_write", code=bytes.fromhex("d7502ffc"), expected_debit=-168,
             reference_cycles=11, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0050, b"\x00\x04"), (0x0406, b"\x33")),
             expected_memory=(0x0406, 0x11)),
    ]

    branch_cases = [
        # Ordinary condition branches: base 2, taken +2.
        dict(name="bpl_taken", code=bytes.fromhex("10fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="bpl_not_taken", code=bytes.fromhex("10fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x80,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
        dict(name="bmi_taken", code=bytes.fromhex("30fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x80,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="bmi_not_taken", code=bytes.fromhex("30fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
        dict(name="bvc_taken", code=bytes.fromhex("50fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="bvc_not_taken", code=bytes.fromhex("50fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x40,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
        dict(name="bvs_taken", code=bytes.fromhex("70fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x40,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="bvs_not_taken", code=bytes.fromhex("70fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
        dict(name="bcc_taken", code=bytes.fromhex("90fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="bcc_not_taken", code=bytes.fromhex("90fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x01,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
        dict(name="bcs_taken", code=bytes.fromhex("b0fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x01,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="bcs_not_taken", code=bytes.fromhex("b0fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
        dict(name="bne_taken", code=bytes.fromhex("d0fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="bne_not_taken", code=bytes.fromhex("d0fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x02,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
        dict(name="beq_taken", code=bytes.fromhex("f0fe"), expected_debit=-42,
             reference_cycles=4, expected_end_region=8, y_value=0x06, flags_value=0x02,
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="beq_not_taken", code=bytes.fromhex("f0fe"), expected_debit=-42,
             reference_cycles=2, expected_end_region=8, y_value=0x06, flags_value=0x00,
             expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),

        # BranchBit: base 5, taken 7.
        dict(name="bbs_taken", code=bytes.fromhex("0320fd"), expected_debit=-84,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x01"),), expected_pc_after=TEST_PC,
             expected_runtime_debits=(-42,)),
        dict(name="bbs_not_taken", code=bytes.fromhex("0320fd"), expected_debit=-84,
             reference_cycles=5, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x00"),), expected_pc_after=TEST_PC + 3,
             expected_runtime_debits=(-42,)),
        dict(name="bbc_taken", code=bytes.fromhex("1320fd"), expected_debit=-84,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x00"),), expected_pc_after=TEST_PC,
             expected_runtime_debits=(-42,)),
        dict(name="bbc_not_taken", code=bytes.fromhex("1320fd"), expected_debit=-84,
             reference_cycles=5, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x01"),), expected_pc_after=TEST_PC + 3,
             expected_runtime_debits=(-42,)),

        # CBNE: direct base 5 / indexed base 6, taken +2.
        dict(name="cbne_direct_taken", code=bytes.fromhex("2e20fd"), expected_debit=-84,
             reference_cycles=7, expected_end_region=8, y_value=0x06, a_value=0x11,
             memory_writes=((0x0020, b"\x22"),), expected_pc_after=TEST_PC,
             expected_runtime_debits=(-42,)),
        dict(name="cbne_direct_not_taken", code=bytes.fromhex("2e20fd"), expected_debit=-84,
             reference_cycles=5, expected_end_region=8, y_value=0x06, a_value=0x11,
             memory_writes=((0x0020, b"\x11"),), expected_pc_after=TEST_PC + 3,
             expected_runtime_debits=(-42,)),
        dict(name="cbne_direct_x_taken", code=bytes.fromhex("de20fd"), expected_debit=-105,
             reference_cycles=8, expected_end_region=8, y_value=0x06, a_value=0x11,
             memory_writes=((0x0024, b"\x22"),), expected_pc_after=TEST_PC,
             expected_runtime_debits=(-42,)),
        dict(name="cbne_direct_x_not_taken", code=bytes.fromhex("de20fd"), expected_debit=-105,
             reference_cycles=6, expected_end_region=8, y_value=0x06, a_value=0x11,
             memory_writes=((0x0024, b"\x11"),), expected_pc_after=TEST_PC + 3,
             expected_runtime_debits=(-42,)),

        # DBNZ memory: base 5, taken 7.
        dict(name="dbnzm_taken", code=bytes.fromhex("6e20fd"), expected_debit=-63,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x02"),), expected_memory=(0x0020, 0x01),
             expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="dbnzm_not_taken", code=bytes.fromhex("6e20fd"), expected_debit=-63,
             reference_cycles=5, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x01"),), expected_memory=(0x0020, 0x00),
             expected_pc_after=TEST_PC + 3, expected_runtime_debits=(-42,)),

        # DBNZ Y: base 4, taken 6.
        dict(name="dbnzy_taken", code=bytes.fromhex("fefe"), expected_debit=-84,
             reference_cycles=6, expected_end_region=8, y_value=0x02,
             expected_y=0x01, expected_pc_after=TEST_PC, expected_runtime_debits=(-42,)),
        dict(name="dbnzy_not_taken", code=bytes.fromhex("fefe"), expected_debit=-84,
             reference_cycles=4, expected_end_region=8, y_value=0x01,
             expected_y=0x00, expected_pc_after=TEST_PC + 2, expected_runtime_debits=(-42,)),
    ]

    stack_semantic_cases = [
        # POP A increments S=0x7F to 0x80 and must read stack page 0x0180.
        # Direct page 0x0080 carries a distinct sentinel to detect aliasing.
        dict(
            name="pop_a_stack_page",
            code=bytes.fromhex("ae2ffd"),
            expected_debit=-147,
            reference_cycles=8,
            expected_end_region=8,
            y_value=0x06,
            stack_value=0x7F,
            memory_writes=((0x0080, b"\xAA"), (0x0180, b"\xBB")),
            expected_accum=0xBB,
            expected_stack=0x80,
            expected_pc_after=TEST_PC,
        ),
    ]

    fixed_family_cases = [
        # Implied ALU: opcode fetch + dummy PC read = 2; trailing BRA = 4.
        dict(name="inca_fixed", code=bytes.fromhex("bc2ffd"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             a_value=0x10, expected_accum=0x11),
        # Register transfers: one dummy PC read beyond opcode fetch.
        dict(name="mov_x_a_fixed", code=bytes.fromhex("5d2ffd"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             a_value=0x44, expected_x=0x44),
        dict(name="mov_sp_x_fixed", code=bytes.fromhex("bd2ffd"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             x_value=0x55, expected_stack=0x55),
        # Ordinary flags: one dummy PC read.
        dict(name="clrc_fixed", code=bytes.fromhex("602ffd"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             flags_value=0x01, expected_flags=0x00),
        # I flag operations and NOTC each have two missing cycles.
        dict(name="di_fixed", code=bytes.fromhex("c02ffd"), expected_debit=-147,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             flags_value=0x04, expected_flags=0x00),
        dict(name="ei_fixed", code=bytes.fromhex("a02ffd"), expected_debit=-147,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             flags_value=0x00, expected_flags=0x04),
        dict(name="notc_fixed", code=bytes.fromhex("ed2ffd"), expected_debit=-147,
             reference_cycles=7, expected_end_region=8, y_value=0x06,
             flags_value=0x00, expected_flags=0x01),
        # XCN is 5 cycles by itself: opcode fetch + dummy read + 3 idles.
        dict(name="xcn_fixed", code=bytes.fromhex("9f2ffd"), expected_debit=-189,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             a_value=0x12, expected_accum=0x21),
        # PUSH A: 7 static units plus one runtime stack write = 8 total.
        dict(name="push_a_fixed", code=bytes.fromhex("2d2ffd"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             a_value=0x11, stack_value=0x80, expected_stack=0x7F,
             expected_memory=(0x0180, 0x11)),
    ]


    call_return_cases = [
        # CALL absolute: 3 fetch units + 3 fixed idles + 2 runtime stack writes = 8.
        dict(name="call_absolute", code=bytes.fromhex("3f3412"), expected_debit=-126,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             stack_value=0x80, expected_stack=0x7E, expected_pc_after=0x1234,
             expected_memories=((0x0180, 0x02), (0x017F, 0x03))),
        # PCALL: opcode+operand +2 fixed +2 stack writes = 6.
        dict(name="pcall", code=bytes.fromhex("4f34"), expected_debit=-84,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             stack_value=0x80, expected_stack=0x7E, expected_pc_after=0xFF34,
             expected_memories=((0x0180, 0x02), (0x017F, 0x02))),
        # TCALL 0: opcode +3 fixed +2 stack writes +2 vector reads = 8.
        dict(name="tcall0", code=bytes.fromhex("01"), expected_debit=-84,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             stack_value=0x80, expected_stack=0x7E, expected_pc_after=0x1234,
             memory_writes=((0xFFDE, b"\x34\x12"),),
             expected_memories=((0x0180, 0x02), (0x017F, 0x01))),
        # RET: opcode +2 fixed +2 stack reads = 5.
        dict(name="ret", code=bytes.fromhex("6f"), expected_debit=-63,
             reference_cycles=5, expected_end_region=8, y_value=0x06,
             stack_value=0x7E, expected_stack=0x80, expected_pc_after=0x1234,
             memory_writes=((0x017F, b"\x34"), (0x0180, b"\x12"))),
        # RET1: opcode +2 fixed +3 stack reads = 6.
        dict(name="ret1", code=bytes.fromhex("7f"), expected_debit=-63,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             stack_value=0x7D, flags_value=0x00, expected_stack=0x80,
             expected_pc_after=0x1234, expected_flags=0x04,
             memory_writes=((0x017E, b"\x04"), (0x017F, b"\x34"), (0x0180, b"\x12"))),
        # BRK: opcode +2 fixed +3 stack writes +2 vector reads = 8.
        dict(name="brk", code=bytes.fromhex("0f"), expected_debit=-63,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             stack_value=0x80, flags_value=0x04, expected_stack=0x7D,
             expected_pc_after=0x1234, expected_flags=0x10,
             memory_writes=((0xFFDE, b"\x34\x12"),),
             expected_memories=((0x0180, 0x02), (0x017F, 0x01), (0x017E, 0x04))),
    ]


    word_cases = [
        # Direct-page word timing. Each case ends in BRA back to TEST_PC (4 cycles).
        # ADDW/SUBW/MOVW YA,dp have one internal idle between low/high reads.
        dict(name="addw_word", code=bytes.fromhex("7a202ffc"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x01, a_value=0x02,
             memory_writes=((0x0020, b"\x03\x02"),),
             expected_accum=0x05, expected_y=0x03),
        dict(name="subw_word", code=bytes.fromhex("9a202ffc"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x03, a_value=0x05,
             memory_writes=((0x0020, b"\x03\x02"),),
             expected_accum=0x02, expected_y=0x01),
        dict(name="movw_ya_dp_word", code=bytes.fromhex("ba202ffc"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x00, a_value=0x00,
             memory_writes=((0x0020, b"\x34\x12"),),
             expected_accum=0x34, expected_y=0x12),

        # Controls expected to be cycle-complete already.
        dict(name="cmpw_word_control", code=bytes.fromhex("5a202ffc"), expected_debit=-126,
             reference_cycles=8, expected_end_region=8, y_value=0x03, a_value=0x05,
             memory_writes=((0x0020, b"\x03\x02"),),
             expected_accum=0x05, expected_y=0x03),
        dict(name="decw_word_control", code=bytes.fromhex("1a202ffc"), expected_debit=-126,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x00\x01"),),
             expected_memories=((0x0020, 0xFF), (0x0021, 0x00))),
        dict(name="incw_word_control", code=bytes.fromhex("3a202ffc"), expected_debit=-126,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\xFF\x00"),),
             expected_memories=((0x0020, 0x00), (0x0021, 0x01))),
        dict(name="movw_dp_ya_word_control", code=bytes.fromhex("da202ffc"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x12, a_value=0x34,
             memory_writes=((0x0020, b"\x00\x00"),),
             expected_memories=((0x0020, 0x34), (0x0021, 0x12))),
    ]


    bit_cases = [
        # Absolute bit-address instructions use bit 0 of RAM[0x0400].
        # Each case ends in the already validated 4-cycle BRA loop.
        dict(name="or1_bit", code=bytes.fromhex("0a00042ffb"), expected_debit=-168,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             flags_value=0x00, memory_writes=((0x0400, b"\x01"),),
             expected_flags=0x01),
        dict(name="or1_not_bit", code=bytes.fromhex("2a00042ffb"), expected_debit=-168,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             flags_value=0x00, memory_writes=((0x0400, b"\x00"),),
             expected_flags=0x01),
        dict(name="eor1_bit", code=bytes.fromhex("8a00042ffb"), expected_debit=-168,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             flags_value=0x00, memory_writes=((0x0400, b"\x01"),),
             expected_flags=0x01),
        dict(name="mov1_mem_c_bit", code=bytes.fromhex("ca00042ffb"), expected_debit=-168,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             flags_value=0x01, memory_writes=((0x0400, b"\x00"),),
             expected_flags=0x01, expected_memory=(0x0400, 0x01)),

        # Controls expected to be cycle-complete already.
        dict(name="and1_bit_control", code=bytes.fromhex("4a00042ffb"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             flags_value=0x01, memory_writes=((0x0400, b"\x01"),),
             expected_flags=0x01),
        dict(name="and1_not_bit_control", code=bytes.fromhex("6a00042ffb"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             flags_value=0x01, memory_writes=((0x0400, b"\x00"),),
             expected_flags=0x01),
        dict(name="mov1_c_mem_bit_control", code=bytes.fromhex("aa00042ffb"), expected_debit=-147,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             flags_value=0x00, memory_writes=((0x0400, b"\x01"),),
             expected_flags=0x01),
        dict(name="not1_bit_control", code=bytes.fromhex("ea00042ffb"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0400, b"\x00"),), expected_memory=(0x0400, 0x01)),
        dict(name="set1_dp_control", code=bytes.fromhex("02202ffc"), expected_debit=-126,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x00"),), expected_memory=(0x0020, 0x01)),
        dict(name="clr1_dp_control", code=bytes.fromhex("12202ffc"), expected_debit=-126,
             reference_cycles=8, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x01"),), expected_memory=(0x0020, 0x00)),

        # TSET/TCLR now perform the second real read required by the pinned
        # reference. Static debit drops by one unit while total stays 10.
        dict(name="tset1_ram_total", code=bytes.fromhex("0e00042ffb"), expected_debit=-147,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             a_value=0xF0, flags_value=0x00, memory_writes=((0x0400, b"\x0F"),),
             expected_flags=0x80, expected_memory=(0x0400, 0xFF)),
        dict(name="tclr1_ram_total", code=bytes.fromhex("4e00042ffb"), expected_debit=-147,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             a_value=0x0F, flags_value=0x00, memory_writes=((0x0400, b"\xFF"),),
             expected_flags=0x00, expected_memory=(0x0400, 0xF0)),
    ]


    operand_form_cases = [
        # Remaining shared operand-form timing cluster. Every case ends in the
        # already validated 4-cycle BRA loop.
        dict(name="cmp_dp_dp", code=bytes.fromhex("6920212ffb"), expected_debit=-168,
             reference_cycles=10, expected_end_region=8, y_value=0x06,
             flags_value=0x00, memory_writes=((0x0020, b"\x03"), (0x0021, b"\x05")),
             expected_flags=0x01),
        dict(name="cmp_dp_imm", code=bytes.fromhex("7803212ffb"), expected_debit=-168,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             flags_value=0x00, memory_writes=((0x0021, b"\x05"),),
             expected_flags=0x01),
        dict(name="cmp_x_y", code=bytes.fromhex("792ffd"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x20, x_value=0x21,
             flags_value=0x00, memory_writes=((0x0020, b"\x03"), (0x0021, b"\x05")),
             expected_flags=0x01),
        dict(name="or_x_y", code=bytes.fromhex("192ffd"), expected_debit=-126,
             reference_cycles=9, expected_end_region=8, y_value=0x20, x_value=0x21,
             flags_value=0x00, memory_writes=((0x0020, b"\x02"), (0x0021, b"\x01")),
             expected_flags=0x00, expected_memory=(0x0021, 0x03)),
        dict(name="mov_dp_imm", code=bytes.fromhex("8f7a212ffb"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0021, b"\x55"),), expected_memory=(0x0021, 0x7A)),
        dict(name="mov_dp_dp_control", code=bytes.fromhex("fa20212ffb"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             memory_writes=((0x0020, b"\x66"), (0x0021, b"\x00")),
             expected_memory=(0x0021, 0x66)),
    ]


    half_carry_cases = [
        # ADC/SBC 8-bit Half-Carry semantics. Timing must remain unchanged.
        dict(name="adc_imm_h_set", code=bytes.fromhex("88012ffc"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             a_value=0x0F, flags_value=0x00, expected_accum=0x10, expected_flags=0x08),
        dict(name="adc_imm_h_clear", code=bytes.fromhex("88012ffc"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             a_value=0x01, flags_value=0x08, expected_accum=0x02, expected_flags=0x00),
        dict(name="sbc_imm_h_set", code=bytes.fromhex("a8012ffc"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             a_value=0x11, flags_value=0x01, expected_accum=0x10, expected_flags=0x09),
        dict(name="sbc_imm_h_clear", code=bytes.fromhex("a8012ffc"), expected_debit=-126,
             reference_cycles=6, expected_end_region=8, y_value=0x06,
             a_value=0x10, flags_value=0x09, expected_accum=0x0F, expected_flags=0x01),
        dict(name="adc_dp_imm_h_set", code=bytes.fromhex("9801202ffb"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             flags_value=0x00, memory_writes=((0x0020, b"\x0F"),),
             expected_memory=(0x0020, 0x10), expected_flags=0x08),
        dict(name="sbc_dp_imm_h_set", code=bytes.fromhex("b801202ffb"), expected_debit=-147,
             reference_cycles=9, expected_end_region=8, y_value=0x06,
             flags_value=0x01, memory_writes=((0x0020, b"\x11"),),
             expected_memory=(0x0020, 0x10), expected_flags=0x09),
    ]


    word_half_carry_cases = [
        # Word H is the high-byte nibble half-carry/borrow produced by the
        # second 8-bit ADC/SBC step in the pinned reference.
        dict(name="addw_h_set_via_low_carry", code=bytes.fromhex("7a202ffc"),
             expected_debit=-147, reference_cycles=9, expected_end_region=8,
             y_value=0x0F, a_value=0xFF, flags_value=0x00,
             memory_writes=((0x0020, b"\x01\x00"),),
             expected_accum=0x00, expected_y=0x10, expected_flags=0x08),
        dict(name="addw_h_clear", code=bytes.fromhex("7a202ffc"),
             expected_debit=-147, reference_cycles=9, expected_end_region=8,
             y_value=0x01, a_value=0x00, flags_value=0x08,
             memory_writes=((0x0020, b"\x00\x01"),),
             expected_accum=0x00, expected_y=0x02, expected_flags=0x00),
        dict(name="subw_h_set_via_low_borrow", code=bytes.fromhex("9a202ffc"),
             expected_debit=-147, reference_cycles=9, expected_end_region=8,
             y_value=0x11, a_value=0x00, flags_value=0x00,
             memory_writes=((0x0020, b"\x01\x00"),),
             expected_accum=0xFF, expected_y=0x10, expected_flags=0x09),
        dict(name="subw_h_clear_via_low_borrow", code=bytes.fromhex("9a202ffc"),
             expected_debit=-147, reference_cycles=9, expected_end_region=8,
             y_value=0x10, a_value=0x00, flags_value=0x08,
             memory_writes=((0x0020, b"\x01\x00"),),
             expected_accum=0xFF, expected_y=0x0F, expected_flags=0x01),
    ]


    div_semantic_cases = [
        # DIV total is 12 cycles; each case ends in the validated 4-cycle BRA.
        dict(name="div_normal_hv_clear", code=bytes.fromhex("9e2ffd"),
             expected_debit=-336, reference_cycles=16, expected_end_region=8,
             x_value=0x04, y_value=0x01, a_value=0x08, flags_value=0x49,
             expected_accum=0x42, expected_y=0x00, expected_flags=0x01),
        dict(name="div_normal_9bit_quotient", code=bytes.fromhex("9e2ffd"),
             expected_debit=-336, reference_cycles=16, expected_end_region=8,
             x_value=0x04, y_value=0x05, a_value=0x00, flags_value=0x00,
             expected_accum=0x40, expected_y=0x00, expected_flags=0x48),
        dict(name="div_special_known_failure", code=bytes.fromhex("9e2ffd"),
             expected_debit=-336, reference_cycles=16, expected_end_region=8,
             x_value=0x04, y_value=0x5A, a_value=0x11, flags_value=0x00,
             expected_accum=0xAC, expected_y=0x61, expected_flags=0xC8),
        dict(name="div_special_h_clear", code=bytes.fromhex("9e2ffd"),
             expected_debit=-336, reference_cycles=16, expected_end_region=8,
             x_value=0x09, y_value=0x12, a_value=0x00, flags_value=0x08,
             expected_accum=0xFF, expected_y=0x09, expected_flags=0xC0),
        dict(name="div_x_zero", code=bytes.fromhex("9e2ffd"),
             expected_debit=-336, reference_cycles=16, expected_end_region=8,
             x_value=0x00, y_value=0x02, a_value=0x34, flags_value=0x00,
             expected_accum=0xFD, expected_y=0x34, expected_flags=0xC8),
        dict(name="div_zero_result", code=bytes.fromhex("9e2ffd"),
             expected_debit=-336, reference_cycles=16, expected_end_region=8,
             x_value=0x04, y_value=0x00, a_value=0x00, flags_value=0x49,
             expected_accum=0x00, expected_y=0x00, expected_flags=0x03),
    ]


    halt_entry_cases = [
        dict(name="sleep_entry", code=bytes.fromhex("ef"),
             expected_debit=-42, reference_cycles=3, expected_end_region=8,
             y_value=0x06, expected_pc_after=TEST_PC + 1, expected_halt=1),
        dict(name="stop_entry", code=bytes.fromhex("ff"),
             expected_debit=-42, reference_cycles=3, expected_end_region=8,
             y_value=0x06, expected_pc_after=TEST_PC + 1, expected_halt=2),
    ]

    decimal_adjust_cases = [
        # DAA/DAS are 3-cycle instructions; each test ends with the validated
        # 4-cycle BRA loop, so total reference time is 7 cycles.
        dict(name="daa_low_only", code=bytes.fromhex("df2ffd"),
             expected_debit=-147, reference_cycles=7, expected_end_region=8,
             y_value=0x06, a_value=0x0A, flags_value=0x40,
             expected_accum=0x10, expected_flags=0x40),
        dict(name="daa_high_only", code=bytes.fromhex("df2ffd"),
             expected_debit=-147, reference_cycles=7, expected_end_region=8,
             y_value=0x06, a_value=0x15, flags_value=0x41,
             expected_accum=0x75, expected_flags=0x41),
        dict(name="daa_both_wrap_zero", code=bytes.fromhex("df2ffd"),
             expected_debit=-147, reference_cycles=7, expected_end_region=8,
             y_value=0x06, a_value=0x9A, flags_value=0x48,
             expected_accum=0x00, expected_flags=0x4B),
        dict(name="das_low_only", code=bytes.fromhex("be2ffd"),
             expected_debit=-147, reference_cycles=7, expected_end_region=8,
             y_value=0x06, a_value=0x15, flags_value=0x41,
             expected_accum=0x0F, expected_flags=0x41),
        dict(name="das_high_only", code=bytes.fromhex("be2ffd"),
             expected_debit=-147, reference_cycles=7, expected_end_region=8,
             y_value=0x06, a_value=0x75, flags_value=0x48,
             expected_accum=0x15, expected_flags=0x48),
        dict(name="das_both_negative", code=bytes.fromhex("be2ffd"),
             expected_debit=-147, reference_cycles=7, expected_end_region=8,
             y_value=0x06, a_value=0x00, flags_value=0x40,
             expected_accum=0x9A, expected_flags=0xC0),
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

        for case in budget_edge_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in address_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in branch_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in stack_semantic_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in fixed_family_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in call_return_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in word_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in bit_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in operand_form_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in half_carry_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in word_half_carry_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in div_semantic_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        for case in decimal_adjust_cases:
            results.append(compile_one_case(client, addresses=args, **case))

        budget_edge_result = next(
            item for item in results if item["name"] == "budget_20_nop_div_32"
        )
        cycle_budget_reuse = verify_cycle_budget_reuse(
            client, base_result=budget_edge_result, addresses=args
        )

        long_result = next(item for item in results if item["name"] == "long_nop_dbnzy")
        reentry = middle_region_reentry(client, long_result=long_result, addresses=args)

        halt_scheduler: list[dict[str, object]] = []
        for case in halt_entry_cases:
            entry = compile_one_case(client, addresses=args, **case)
            results.append(entry)
            halt_scheduler.append(
                measure_halt_ticks(
                    client,
                    name=case["name"],
                    expected_halt=int(case["expected_halt"]),
                    addresses=args,
                )
            )

        report = {
            "apu_clock": APU_CLOCK,
            "test_pc": TEST_PC,
            "jit_buffer": JIT_BUFFER,
            "cases": results,
            "middle_region_reentry": reentry,
            "cycle_budget_reuse": cycle_budget_reuse,
            "halt_scheduler": halt_scheduler,
            "summary": {
                "all_static_debits_match_source_prediction": all(
                    bool(item["cycle_debit_matches_expected"]) for item in results
                ),
                "all_header_spans_match_source_prediction": all(
                    bool(item["span_matches_expected"]) for item in results
                ),
                "all_total_debits_match_reference": all(
                    bool(item["total_cycle_debit_matches_reference"]) for item in results
                ),
                "all_runtime_cycle_debits_match_expected": all(
                    bool(item["runtime_cycle_debits_match_expected"]) for item in results
                ),
                "all_semantics_match_expected": all(
                    bool(item["semantics_match_expected"]) for item in results
                ),
                "all_halt_scheduler_ticks_match_expected": all(
                    bool(item["all_ticks_match_expected"]) for item in halt_scheduler
                ),
                "long_source_program_exceeds_block_size": int(long_result["source_bytes"]) > 16,
                "compiled_long_probe_is_bounded_to_one_tag_region": (
                    int(long_result["header_end_region"])
                    == int(long_result["header_start_region"])
                    and int(long_result["source_clock_units"]) == 22
                ),
                "all_cycle_budget_edge_cases_at_or_below_32": all(
                    int(item["total_clock_units"]) <= 32
                    for item in results
                    if str(item["name"]).startswith("budget_")
                ),
                "exact_20_plus_div_reaches_32": (
                    int(budget_edge_result["total_clock_units"]) == 32
                    and int(budget_edge_result["apu_count_after_block"]) == TEST_PC + 11
                ),
                "cached_cycle_budget_block_reused_without_recompile": bool(
                    cycle_budget_reuse["cached_reused_without_recompile"]
                ),
                "covered_tag_mutation_forces_recompile": bool(
                    cycle_budget_reuse["tag_mutation_forced_recompile"]
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

        required = (
            report["summary"]["all_static_debits_match_source_prediction"]
            and report["summary"]["all_header_spans_match_source_prediction"]
            and report["summary"]["all_total_debits_match_reference"]
            and report["summary"]["all_runtime_cycle_debits_match_expected"]
            and report["summary"]["all_semantics_match_expected"]
            and report["summary"]["all_halt_scheduler_ticks_match_expected"]
            and report["summary"]["compiled_long_probe_is_bounded_to_one_tag_region"]
            and report["summary"]["all_cycle_budget_edge_cases_at_or_below_32"]
            and report["summary"]["exact_20_plus_div_reaches_32"]
            and report["summary"]["cached_cycle_budget_block_reused_without_recompile"]
            and report["summary"]["covered_tag_mutation_forces_recompile"]
        )
        if not required:
            raise RuntimeError("SPC700 cycle/addressing proof failed required invariants")

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
