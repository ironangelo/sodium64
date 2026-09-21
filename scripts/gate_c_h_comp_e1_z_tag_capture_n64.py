#!/usr/bin/env python3
"""Capture/classify Gate-C E1c within-frame compact Z-scratch reuse proof."""

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

E1C_Z_SCRATCH_ADDR = 0xA00C0000
E1C_Z_SCRATCH_SIZE = 0x1180
E1C_ARCHIVE_A_ADDR = 0xA00C2000
E1C_PREFIX_GUARD_ADDR = 0xA00BFFC0
E1C_SUFFIX_GUARD_ADDR = 0xA00C1180
E1C_GUARD_SIZE = 64
E1C_ROWS = 8
E1C_ACTIVE_X0 = 12
E1C_ACTIVE_X1 = 268


def parse_int(text: str) -> int:
    return int(text, 0)


def read_u(client: RSPClient, address: int, size: int) -> int:
    return int.from_bytes(client.read_memory(address, size, size), "big")


def write_pattern(client: RSPClient, address: int, data: bytes, chunk: int = 0x400) -> None:
    for offset in range(0, len(data), chunk):
        client.write_memory(address + offset, data[offset:offset + chunk])


def initialize_proof_memory(client: RSPClient) -> None:
    write_pattern(client, Z_COMMAND_ADDR, bytes([PREFIX_BYTE]) * Z_PREFIX_SIZE)
    write_pattern(client, Z_BASE, SENTINEL_WORD.to_bytes(2, "big") * (Z_SIZE // 2))
    write_pattern(client, Z_BASE + Z_SIZE, bytes([SUFFIX_BYTE]) * Z_SUFFIX_SIZE)
    client.write_memory(STATUS_ADDR, bytes(STATUS_SIZE))

    assert client.read_memory(Z_COMMAND_ADDR, Z_PREFIX_SIZE, 0x400) == bytes([PREFIX_BYTE]) * Z_PREFIX_SIZE
    assert client.read_memory(Z_BASE, Z_SIZE, 0x400) == SENTINEL_WORD.to_bytes(2, "big") * (Z_SIZE // 2)
    assert client.read_memory(Z_BASE + Z_SIZE, Z_SUFFIX_SIZE, 0x100) == bytes([SUFFIX_BYTE]) * Z_SUFFIX_SIZE
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
            f"E1c proof poll #{attempt}",
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
    raise RuntimeError("E1c proof marker/fresh guest frame was not observed")


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
    archive_a: bytes,
    final_b: bytes,
    prefix_guard: bytes,
    suffix_guard: bytes,
) -> dict[str, object]:
    assert len(archive_a) == E1C_Z_SCRATCH_SIZE
    assert len(final_b) == E1C_Z_SCRATCH_SIZE
    assert len(prefix_guard) == E1C_GUARD_SIZE
    assert len(suffix_guard) == E1C_GUARD_SIZE

    def words(data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)
        ]

    a_words = words(archive_a)
    b_words = words(final_b)
    a_hist = collections.Counter(a_words)
    b_hist = collections.Counter(b_words)

    a_wrong: list[dict[str, int]] = []
    b_wrong: list[dict[str, int]] = []
    for index, (za, zb) in enumerate(zip(a_words, b_words)):
        y, x = divmod(index, FB_WIDTH)
        active = E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1
        expected_a = BG1_TAG_WORD if active else SENTINEL_WORD
        expected_b = BG2_TAG_WORD if active else SENTINEL_WORD
        if za != expected_a and len(a_wrong) < 64:
            a_wrong.append({"x": x, "y": y, "actual": za, "expected": expected_a})
        if zb != expected_b and len(b_wrong) < 64:
            b_wrong.append({"x": x, "y": y, "actual": zb, "expected": expected_b})

    prefix_ok = prefix_guard == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
    suffix_ok = suffix_guard == bytes([SUFFIX_BYTE]) * E1C_GUARD_SIZE
    expected_active = (E1C_ACTIVE_X1 - E1C_ACTIVE_X0) * E1C_ROWS
    expected_border = (FB_WIDTH - (E1C_ACTIVE_X1 - E1C_ACTIVE_X0)) * E1C_ROWS

    passed = (
        prefix_ok
        and suffix_ok
        and not a_wrong
        and not b_wrong
        and a_hist[BG1_TAG_WORD] == expected_active
        and a_hist[SENTINEL_WORD] == expected_border
        and b_hist[BG2_TAG_WORD] == expected_active
        and b_hist[SENTINEL_WORD] == expected_border
        and b_hist[BG1_TAG_WORD] == 0
        and len(a_words) == FB_WIDTH * E1C_ROWS
        and len(b_words) == FB_WIDTH * E1C_ROWS
    )

    return {
        "classification": (
            "E1C_STRIP_REUSE_CONTRACT_VALIDATED"
            if passed
            else "E1C_STRIP_REUSE_CONTRACT_FAILED"
        ),
        "passed": passed,
        "constants": {
            "width": FB_WIDTH,
            "rows": E1C_ROWS,
            "scratch_address": hex(E1C_Z_SCRATCH_ADDR),
            "scratch_size": E1C_Z_SCRATCH_SIZE,
            "archive_a_address": hex(E1C_ARCHIVE_A_ADDR),
            "prefix_guard_address": hex(E1C_PREFIX_GUARD_ADDR),
            "suffix_guard_address": hex(E1C_SUFFIX_GUARD_ADDR),
            "guard_size": E1C_GUARD_SIZE,
            "active_x0": E1C_ACTIVE_X0,
            "active_x1_exclusive": E1C_ACTIVE_X1,
            "sentinel_word": hex(SENTINEL_WORD),
            "band_a_tag_word": hex(BG1_TAG_WORD),
            "band_b_tag_word": hex(BG2_TAG_WORD),
            "expected_active_words": expected_active,
            "expected_border_words": expected_border,
        },
        "counts": {
            "archive_a_tag_words": a_hist[BG1_TAG_WORD],
            "archive_a_sentinel_words": a_hist[SENTINEL_WORD],
            "final_b_tag_words": b_hist[BG2_TAG_WORD],
            "final_b_sentinel_words": b_hist[SENTINEL_WORD],
            "final_b_stale_a_words": b_hist[BG1_TAG_WORD],
            "words_per_compact_strip": len(a_words),
        },
        "guards": {
            "prefix_ok": prefix_ok,
            "suffix_ok": suffix_ok,
        },
        "archive_a_histogram_top": [
            {"word": hex(word), "count": count}
            for word, count in a_hist.most_common(8)
        ],
        "final_b_histogram_top": [
            {"word": hex(word), "count": count}
            for word, count in b_hist.most_common(8)
        ],
        "mismatches": {
            "archive_a_wrong": a_wrong,
            "final_b_wrong": b_wrong,
        },
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
        validate_stop(client.request("c"), "E1c clean-epoch breakpoint")
        anchor = read_quiescent_state(client)
        validate_quiescent_state(anchor, require_marker=True)

        # Create the clean epoch only now, between frames with the RSP halted.
        initialize_proof_memory(client)
        baseline_counter = read_u(client, args.guest_counter_address, 1)

        # Step over the breakpoint once, reinstall it behind the PC, and let one
        # complete subsequent RSP frame reach the same quiescent boundary.
        set_breakpoint(client, args.capture_ready_address, False)
        validate_stop(client.request("s"), "E1c breakpoint step-over")
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "E1c fenced capture breakpoint")

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
        archive_a = client.read_memory(
            E1C_ARCHIVE_A_ADDR, E1C_Z_SCRATCH_SIZE, 0x400
        )
        final_b = client.read_memory(
            E1C_Z_SCRATCH_ADDR, E1C_Z_SCRATCH_SIZE, 0x400
        )
        prefix_guard = client.read_memory(
            E1C_PREFIX_GUARD_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )
        suffix_guard = client.read_memory(
            E1C_SUFFIX_GUARD_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )

        (out / "framebuffer.rgba5551").write_bytes(framebuffer)
        (out / "archive_a.bin").write_bytes(archive_a)
        (out / "final_b.bin").write_bytes(final_b)
        (out / "prefix_guard.bin").write_bytes(prefix_guard)
        (out / "suffix_guard.bin").write_bytes(suffix_guard)

        result = classify(archive_a, final_b, prefix_guard, suffix_guard)
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
            raise RuntimeError("E1c semantic classifier failed; see result.json")

        try:
            client.request("D")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
