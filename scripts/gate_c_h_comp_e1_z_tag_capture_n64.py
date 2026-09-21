#!/usr/bin/env python3
"""Capture/classify Gate-C E1d raw RGB555 saturating-add proof."""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gdb_rsp_dump import (  # noqa: E402
    ARES_N64_GUEST_SIGNALS,
    RSPClient,
    connect_with_retry,
    validate_stop,
)

FB_WIDTH = 280
FB_HEIGHT = 240
FB_BYTES = FB_WIDTH * FB_HEIGHT * 2

Z_COMMAND_ADDR = 0xA00BEE80
Z_BASE = 0xA00C0000
Z_SIZE = FB_BYTES
Z_PREFIX_SIZE = Z_BASE - Z_COMMAND_ADDR
Z_SUFFIX_SIZE = 64
STATUS_ADDR = 0xA00E1000
STATUS_MARKER = 0xE1F00D01
STATUS_SIZE = 8
SP_STATUS_ADDR = 0xA4040010
DP_STATUS_ADDR = 0xA410000C

SECTION_QUEUE1_ADDR = 0xA016C600
SECTION_QUEUE2_ADDR = 0xA0171600
SECTION_RECORD_SIZE = 0x40
SECTION_RECORD_COUNT = 16
SECTION_CAPTURE_SIZE = SECTION_RECORD_SIZE * SECTION_RECORD_COUNT
SECTION_BGNBA_OFFSET = 0x10
SECTION_BG1SC_OFFSET = 0x2A
SECTION_TM_OFFSET = 0x3A
SECTION_BG_MODE_OFFSET = 0x3D
SECTION_STAT_FLAGS_OFFSET = 0x3E
SECTION_SPLIT_LINE_OFFSET = 0x3F

PREFIX_BYTE = 0xC3
SENTINEL_WORD = 0x55AA
SUFFIX_BYTE = 0x3C
BACKDROP_TAG_WORD = 0x0400
BG1_TAG_WORD = 0x0C00
BG2_TAG_WORD = 0x1400
BG1_BLACK_RGBA5551 = 0x0001
BG2_GREEN_RGBA5551 = 0x07C1

E1D_BASE_ADDR = 0xA00C6000
E1D_PREFIX_GUARD_ADDR = E1D_BASE_ADDR
E1D_A_ADDR = E1D_BASE_ADDR + 0x20
E1D_B_ADDR = E1D_BASE_ADDR + 0x40
E1D_OUTPUT_ADDR = E1D_BASE_ADDR + 0x60
E1D_SUFFIX_GUARD_ADDR = E1D_BASE_ADDR + 0x80
E1D_RESERVE_ADDR = E1D_BASE_ADDR + 0xA0
E1D_WORD_BYTES = 32
E1D_GUARD_BYTES = 32
E1D_RESERVE_BYTES = 0x60
E1D_PREFIX_BYTE = 0xA5
E1D_SUFFIX_BYTE = 0x5A
E1D_RESERVE_BYTE = 0xD7
E1D_OUTPUT_BYTE = 0xCC
E1D_A_WORDS = [
    0x0000, 0x001F, 0x03E0, 0x7C00, 0x7FFF, 0x0010, 0x0200, 0x4000,
    0x001F, 0x03E0, 0x4210, 0x1084, 0x7C1F, 0x03FF, 0x5555, 0x1234,
]
E1D_B_WORDS = [
    0x0000, 0x0001, 0x0020, 0x0400, 0x7FFF, 0x000F, 0x01E0, 0x3C00,
    0x0020, 0x0400, 0x2108, 0x0842, 0x03E0, 0x7C00, 0x2AAA, 0x4321,
]
E1D_EXPECTED_WORDS = [
    0x0000, 0x001F, 0x03E0, 0x7C00, 0x7FFF, 0x001F, 0x03E0, 0x7C00,
    0x003F, 0x07E0, 0x6318, 0x18C6, 0x7FFF, 0x7FFF, 0x7FFF, 0x53F5,
]


def parse_int(text: str) -> int:
    return int(text, 0)


def read_u(client: RSPClient, address: int, size: int) -> int:
    return int.from_bytes(client.read_memory(address, size, size), "big")


def write_pattern(client: RSPClient, address: int, data: bytes, chunk: int = 0x400) -> None:
    for offset in range(0, len(data), chunk):
        client.write_memory(address + offset, data[offset:offset + chunk])


def words_to_bytes(words: list[int]) -> bytes:
    return b"".join(word.to_bytes(2, "big") for word in words)


def initialize_proof_memory(client: RSPClient) -> None:
    prefix = bytes([E1D_PREFIX_BYTE]) * E1D_GUARD_BYTES
    a = words_to_bytes(E1D_A_WORDS)
    b = words_to_bytes(E1D_B_WORDS)
    output = bytes([E1D_OUTPUT_BYTE]) * E1D_WORD_BYTES
    suffix = bytes([E1D_SUFFIX_BYTE]) * E1D_GUARD_BYTES
    reserve = bytes([E1D_RESERVE_BYTE]) * E1D_RESERVE_BYTES
    write_pattern(client, E1D_PREFIX_GUARD_ADDR, prefix + a + b + output + suffix + reserve)
    client.write_memory(STATUS_ADDR, bytes(STATUS_SIZE))

    assert client.read_memory(E1D_PREFIX_GUARD_ADDR, E1D_GUARD_BYTES, 0x100) == prefix
    assert client.read_memory(E1D_A_ADDR, E1D_WORD_BYTES, 0x100) == a
    assert client.read_memory(E1D_B_ADDR, E1D_WORD_BYTES, 0x100) == b
    assert client.read_memory(E1D_OUTPUT_ADDR, E1D_WORD_BYTES, 0x100) == output
    assert client.read_memory(E1D_SUFFIX_GUARD_ADDR, E1D_GUARD_BYTES, 0x100) == suffix
    assert client.read_memory(E1D_RESERVE_ADDR, E1D_RESERVE_BYTES, 0x100) == reserve
    assert client.read_memory(STATUS_ADDR, STATUS_SIZE, STATUS_SIZE) == bytes(STATUS_SIZE)

def wait_for_proof(
    client: RSPClient,
    *,
    guest_counter_address: int,
    poll_seconds: float,
    attempts: int,
    minimum_counter: int | None = None,
    baseline_counter: int | None = None,
) -> dict[str, int]:
    for attempt in range(1, attempts + 1):
        validate_stop(
            client.continue_then_interrupt(poll_seconds),
            f"E1d proof poll #{attempt}",
        )
        counter = read_u(client, guest_counter_address, 1)
        marker = read_u(client, STATUS_ADDR, 4)
        delta = None if baseline_counter is None else ((counter - baseline_counter) & 0xFF)
        print(
            f"poll {attempt}: guest_counter=0x{counter:02X} "
            f"delta={delta} status=0x{marker:08X}"
        )
        counter_ok = True
        if minimum_counter is not None:
            counter_ok = counter >= minimum_counter
        if baseline_counter is not None:
            counter_ok = delta is not None and delta >= 1
        if counter_ok and marker == STATUS_MARKER:
            return {
                "attempt": attempt,
                "guest_counter": counter,
                "status": marker,
                "counter_delta": 0 if delta is None else delta,
            }
    raise RuntimeError("E1d proof marker/fresh guest frame was not observed")


def set_breakpoint(client: RSPClient, address: int, enabled: bool) -> None:
    command = "Z0" if enabled else "z0"
    reply = client.request(f"{command},{address:x},4")
    if reply != b"OK":
        action = "insert" if enabled else "remove"
        raise RuntimeError(
            f"target rejected software breakpoint {action} at 0x{address:08X}: "
            f"{reply.decode('ascii', errors='replace')}"
        )


def read_quiescent_state(client: RSPClient) -> dict[str, int]:
    marker = read_u(client, STATUS_ADDR, 4)
    framebuffer_pointer = read_u(client, STATUS_ADDR + 4, 4)
    sp_status = read_u(client, SP_STATUS_ADDR, 4)
    dp_status = read_u(client, DP_STATUS_ADDR, 4)
    return {
        "status": marker,
        "proof_framebuffer_pointer": framebuffer_pointer,
        "sp_status": sp_status,
        "dp_status": dp_status,
    }


def validate_quiescent_state(state: dict[str, int], *, require_marker: bool) -> None:
    if (state["sp_status"] & 0x1) == 0:
        raise RuntimeError(
            f"capture breakpoint reached without RSP HALT: SP_STATUS=0x{state['sp_status']:08X}"
        )
    if state["dp_status"] & 0x70:
        raise RuntimeError(
            f"capture breakpoint reached with DP busy: DP_STATUS=0x{state['dp_status']:08X}"
        )
    if require_marker and state["status"] != STATUS_MARKER:
        raise RuntimeError(
            f"capture breakpoint reached without fresh proof marker: 0x{state['status']:08X}"
        )
    if require_marker and not (
        0x80000000 <= state["proof_framebuffer_pointer"] <= 0xBFFFFFFF
    ):
        raise RuntimeError(
            "proof marker contains invalid framebuffer pointer "
            f"0x{state['proof_framebuffer_pointer']:08X}"
        )


def decode_section_queue(data: bytes) -> list[dict[str, int]]:
    if len(data) != SECTION_CAPTURE_SIZE:
        raise ValueError(f"unexpected section capture size: {len(data)}")
    records: list[dict[str, int]] = []
    for index in range(SECTION_RECORD_COUNT):
        base = index * SECTION_RECORD_SIZE
        record = data[base:base + SECTION_RECORD_SIZE]
        records.append({
            "index": index,
            "bgnba": int.from_bytes(
                record[SECTION_BGNBA_OFFSET:SECTION_BGNBA_OFFSET + 2], "big"
            ),
            "bg1sc": record[SECTION_BG1SC_OFFSET],
            "tm": record[SECTION_TM_OFFSET],
            "bg_mode": record[SECTION_BG_MODE_OFFSET],
            "stat_flags": record[SECTION_STAT_FLAGS_OFFSET],
            "split_line": record[SECTION_SPLIT_LINE_OFFSET],
        })
    return records


def classify(
    output: bytes,
    prefix_guard: bytes,
    suffix_guard: bytes,
    reserve: bytes,
) -> dict[str, object]:
    actual = [
        int.from_bytes(output[i:i + 2], "big")
        for i in range(0, len(output), 2)
    ]
    mismatches = [
        {
            "index": i,
            "a": hex(E1D_A_WORDS[i]),
            "b": hex(E1D_B_WORDS[i]),
            "actual": hex(actual[i]),
            "expected": hex(E1D_EXPECTED_WORDS[i]),
        }
        for i in range(len(E1D_EXPECTED_WORDS))
        if actual[i] != E1D_EXPECTED_WORDS[i]
    ]
    prefix_ok = prefix_guard == bytes([E1D_PREFIX_BYTE]) * E1D_GUARD_BYTES
    suffix_ok = suffix_guard == bytes([E1D_SUFFIX_BYTE]) * E1D_GUARD_BYTES
    reserve_ok = reserve == bytes([E1D_RESERVE_BYTE]) * E1D_RESERVE_BYTES
    passed = (
        len(output) == E1D_WORD_BYTES
        and not mismatches
        and prefix_ok
        and suffix_ok
        and reserve_ok
    )
    return {
        "classification": (
            "E1D_RGB555_SAT_ADD_VALIDATED"
            if passed
            else "E1D_RGB555_SAT_ADD_FAILED"
        ),
        "passed": passed,
        "constants": {
            "base_address": hex(E1D_BASE_ADDR),
            "a_address": hex(E1D_A_ADDR),
            "b_address": hex(E1D_B_ADDR),
            "output_address": hex(E1D_OUTPUT_ADDR),
            "word_count": len(E1D_EXPECTED_WORDS),
        },
        "vectors": [
            {
                "index": i,
                "a": hex(E1D_A_WORDS[i]),
                "b": hex(E1D_B_WORDS[i]),
                "expected": hex(E1D_EXPECTED_WORDS[i]),
                "actual": hex(actual[i]),
            }
            for i in range(len(E1D_EXPECTED_WORDS))
        ],
        "guards": {
            "prefix_ok": prefix_ok,
            "suffix_ok": suffix_ok,
            "reserve_ok": reserve_ok,
        },
        "mismatches": mismatches,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9149)
    parser.add_argument("--connect-timeout", type=float, default=30.0)
    parser.add_argument("--response-timeout", type=float, default=30.0)
    parser.add_argument("--guest-counter-address", required=True, type=parse_int)
    parser.add_argument("--framebuffer-address", required=True, type=parse_int)
    parser.add_argument("--capture-ready-address", required=True, type=parse_int)
    parser.add_argument("--poll-seconds", type=float, default=0.20)
    parser.add_argument("--attempts", type=int, default=80)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    client = connect_with_retry(
        args.host, args.port, args.connect_timeout, args.response_timeout
    )
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        print(f"GDB server capabilities: {supported.decode('ascii', errors='replace')}")
        initial = client.request("?")
        print(f"Initial target state: {initial.decode('ascii', errors='replace')}")
        if b"QPassSignals+" not in supported:
            raise RuntimeError("GDB server does not advertise QPassSignals")
        if client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}") != b"OK":
            raise RuntimeError("target rejected QPassSignals")

        # Warm the guest/runtime before touching the evidence scratch. The initial
        # GDB stop can occur while startup ownership is still unstable; E1a only needs
        # guest progress plus the post-DP-fence marker to establish a stable epoch.
        warmup = wait_for_proof(
            client,
            guest_counter_address=args.guest_counter_address,
            poll_seconds=args.poll_seconds,
            attempts=args.attempts,
            minimum_counter=5,
        )

        # Stop at the CPU's post-rsp_wait point. Sodium64 reaches this PC only
        # after observing SP_STATUS.HALT, so both producer and DP can be checked
        # at a deterministic between-frame boundary rather than a timed host poll.
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "E1d clean-epoch breakpoint")
        anchor = read_quiescent_state(client)
        validate_quiescent_state(anchor, require_marker=True)

        # Create the clean epoch only now, between frames with the RSP halted.
        initialize_proof_memory(client)
        baseline_counter = read_u(client, args.guest_counter_address, 1)

        # Step over the breakpoint once, reinstall it behind the PC, and let one
        # complete subsequent RSP frame reach the same quiescent boundary.
        set_breakpoint(client, args.capture_ready_address, False)
        validate_stop(client.request("s"), "E1d breakpoint step-over")
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "E1d fenced capture breakpoint")

        quiescent = read_quiescent_state(client)
        validate_quiescent_state(quiescent, require_marker=True)
        counter = read_u(client, args.guest_counter_address, 1)
        delta = (counter - baseline_counter) & 0xFF
        if delta < 1:
            raise RuntimeError(
                "capture breakpoint did not include a fresh guest frame: "
                f"baseline=0x{baseline_counter:02X} current=0x{counter:02X}"
            )

        state = {
            "attempt": 1,
            "guest_counter": counter,
            "status": quiescent["status"],
            "counter_delta": delta,
            "warmup_counter": warmup["guest_counter"],
            "baseline_counter": baseline_counter,
            "sp_status": quiescent["sp_status"],
            "dp_status": quiescent["dp_status"],
        }

        fb_pointer = quiescent["proof_framebuffer_pointer"]
        display_fb_pointer = read_u(client, args.framebuffer_address, 4)
        framebuffer = client.read_memory(fb_pointer, FB_BYTES, 0x400)
        output = client.read_memory(E1D_OUTPUT_ADDR, E1D_WORD_BYTES, 0x100)
        prefix_guard = client.read_memory(
            E1D_PREFIX_GUARD_ADDR, E1D_GUARD_BYTES, E1D_GUARD_BYTES
        )
        suffix_guard = client.read_memory(
            E1D_SUFFIX_GUARD_ADDR, E1D_GUARD_BYTES, E1D_GUARD_BYTES
        )
        reserve = client.read_memory(
            E1D_RESERVE_ADDR, E1D_RESERVE_BYTES, E1D_RESERVE_BYTES
        )

        (out / "framebuffer.rgba5551").write_bytes(framebuffer)
        (out / "output.rgb555").write_bytes(output)
        (out / "prefix_guard.bin").write_bytes(prefix_guard)
        (out / "suffix_guard.bin").write_bytes(suffix_guard)
        (out / "reserve.bin").write_bytes(reserve)

        result = classify(output, prefix_guard, suffix_guard, reserve)
        result["capture_state"] = {
            **state,
            "framebuffer_pointer": hex(fb_pointer),
            "display_framebuffer_pointer": hex(display_fb_pointer),
            "capture_ready_address": hex(args.capture_ready_address),
        }
        (out / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["passed"]:
            raise RuntimeError("E1d semantic classifier failed; see result.json")

        try:
            client.request("D")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
