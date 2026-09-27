#!/usr/bin/env python3
"""Fenced one-frame ares capture for clean Main/Sub pixel ownership."""

from __future__ import annotations

import argparse
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

WIDTH = 280
ROWS = 8
STRIP_BYTES = WIDTH * ROWS * 2
SENTINEL = 0x55AA

SUB_COLOR_ADDR = 0xA00E4000
FRAMEBUFFER_ADDRS = (
    0xA00F2300,
    0xA0113000,
    0xA0133D00,
)
SECTION_QUEUE_ADDRS = (
    0xA016C600,
    0xA0171600,
)
SECTION_CAPTURE_BYTES = 0x100

SP_STATUS_ADDR = 0xA4040010
DP_STATUS_ADDR = 0xA410000C


def read_u(client: RSPClient, address: int, size: int) -> int:
    return int.from_bytes(client.read_memory(address, size, size), "big")


def write_pattern(client: RSPClient, address: int, data: bytes, chunk: int = 0x400) -> None:
    for offset in range(0, len(data), chunk):
        part = data[offset:offset + chunk]
        client.write_memory(address + offset, part)


def verify_pattern(client: RSPClient, address: int, data: bytes) -> None:
    got = client.read_memory(address, len(data), 0x400)
    if got != data:
        raise RuntimeError(f"seed verification failed at 0x{address:08X}")


def set_breakpoint(client: RSPClient, address: int, enabled: bool) -> None:
    op = "Z0" if enabled else "z0"
    reply = client.request(f"{op},{address:x},4")
    if reply != b"OK":
        raise RuntimeError(
            f"breakpoint {'insert' if enabled else 'remove'} "
            f"0x{address:08X} rejected: {reply!r}"
        )


def quiescent(client: RSPClient) -> dict[str, object]:
    sp = read_u(client, SP_STATUS_ADDR, 4)
    dp = read_u(client, DP_STATUS_ADDR, 4)
    halted = bool(sp & 1)
    idle = not bool(dp & 0x70)
    if not halted:
        raise RuntimeError(f"RSP not halted at fenced boundary: SP_STATUS=0x{sp:08X}")
    if not idle:
        raise RuntimeError(f"RDP busy at fenced boundary: DP_STATUS=0x{dp:08X}")
    return {
        "sp_status": f"0x{sp:08X}",
        "dp_status": f"0x{dp:08X}",
        "rsp_halted": halted,
        "rdp_idle": idle,
    }


def wait_guest_warm(
    client: RSPClient,
    guest_counter_address: int,
    *,
    minimum: int = 5,
    attempts: int = 80,
    seconds: float = 0.20,
) -> int:
    for i in range(attempts):
        validate_stop(
            client.continue_then_interrupt(seconds),
            f"warmup#{i + 1}",
        )
        counter = read_u(client, guest_counter_address, 1)
        print(f"warmup#{i + 1}: guest_counter=0x{counter:02X}")
        if counter >= minimum:
            return counter
    raise RuntimeError("guest did not reach warmup counter")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9149)
    ap.add_argument("--connect-timeout", type=float, default=30.0)
    ap.add_argument("--response-timeout", type=float, default=30.0)
    ap.add_argument("--guest-counter-address", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--capture-ready-address", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    client = connect_with_retry(
        args.host,
        args.port,
        args.connect_timeout,
        args.response_timeout,
    )
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        print("GDB capabilities:", supported.decode("ascii", errors="replace"))
        initial = client.request("?")
        print("Initial target state:", initial.decode("ascii", errors="replace"))
        if b"QPassSignals+" not in supported:
            raise RuntimeError("ares GDB server lacks QPassSignals")
        if client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}") != b"OK":
            raise RuntimeError("ares rejected QPassSignals")

        warm_counter = wait_guest_warm(client, args.guest_counter_address)

        # Reach the established post-rsp_wait quiescent boundary.
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "seed boundary")
        seed_state = quiescent(client)

        sentinel = SENTINEL.to_bytes(2, "big") * (STRIP_BYTES // 2)
        for address in (SUB_COLOR_ADDR, *FRAMEBUFFER_ADDRS):
            write_pattern(client, address, sentinel)
            verify_pattern(client, address, sentinel)

        baseline_counter = read_u(client, args.guest_counter_address, 1)

        # Step over the breakpoint, reinstall it, and permit exactly one RSP
        # frame to reach the same post-HALT/DP-idle boundary.
        set_breakpoint(client, args.capture_ready_address, False)
        validate_stop(client.request("s"), "breakpoint step-over")
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "fresh-frame boundary")
        final_state = quiescent(client)

        current_counter = read_u(client, args.guest_counter_address, 1)
        delta = (current_counter - baseline_counter) & 0xFF
        if delta != 1:
            raise RuntimeError(
                "strict proof requires exactly one fresh guest frame: "
                f"baseline=0x{baseline_counter:02X} current=0x{current_counter:02X} "
                f"delta={delta}"
            )

        (out / "sub.bin").write_bytes(
            client.read_memory(SUB_COLOR_ADDR, STRIP_BYTES, 0x400)
        )
        for i, address in enumerate(FRAMEBUFFER_ADDRS, start=1):
            (out / f"main{i}.bin").write_bytes(
                client.read_memory(address, STRIP_BYTES, 0x400)
            )
        for i, address in enumerate(SECTION_QUEUE_ADDRS, start=1):
            (out / f"section-q{i}.bin").write_bytes(
                client.read_memory(address, SECTION_CAPTURE_BYTES, 0x100)
            )

        state = {
            "warm_counter": warm_counter,
            "baseline_counter": baseline_counter,
            "current_counter": current_counter,
            "guest_frame_delta": delta,
            "capture_ready_address": f"0x{args.capture_ready_address:08X}",
            "sentinel": f"0x{SENTINEL:04X}",
            "seed_boundary": seed_state,
            **final_state,
        }
        (out / "capture-state.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(state, indent=2, sort_keys=True))

        try:
            client.request("D")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
