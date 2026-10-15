#!/usr/bin/env python3
"""One-frame ares capture at the clean pre-RSP-launch command fence."""

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
SUB_ROWS = 8
MAIN_ROWS = 16
SUB_STRIP_BYTES = WIDTH * SUB_ROWS * 2
MAIN_CAPTURE_BYTES = WIDTH * MAIN_ROWS * 2
SENTINEL = 0x55AA

SUB_COLOR_ADDR = 0xA00E4000
GATING_MAILBOX_ADDR = 0xA00F0008
GATING_MAILBOX_BYTES = 28
PROVENANCE_ACTIVE_ADDR = 0xA00E2000
PROVENANCE_ROWS = 8
PROVENANCE_CAPTURE_BYTES = WIDTH * PROVENANCE_ROWS * 2
PROVENANCE_PREFIX_ADDR = PROVENANCE_ACTIVE_ADDR - 0x40
PROVENANCE_SUFFIX_ADDR = PROVENANCE_ACTIVE_ADDR + PROVENANCE_CAPTURE_BYTES
PROVENANCE_GUARD_BYTES = 0x40
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
DP_END_ADDR = 0xA4100004
DP_CURRENT_ADDR = 0xA4100008
DP_STATUS_ADDR = 0xA410000C
DP_ADDR_MASK = 0x00FFFFFF


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


def read_engine_state(client: RSPClient) -> dict[str, object]:
    sp = read_u(client, SP_STATUS_ADDR, 4)
    dp_end = read_u(client, DP_END_ADDR, 4) & DP_ADDR_MASK
    dp_current = read_u(client, DP_CURRENT_ADDR, 4) & DP_ADDR_MASK
    dp = read_u(client, DP_STATUS_ADDR, 4)

    # Pinned ares 17813a3 renders each submitted DP command list synchronously
    # inside flushCommands(). It clears bufferBusy when render() returns, but
    # leaves pipeBusy asserted until a Sync Full command. Sodium64 emits no
    # Sync Full in this proof runtime, so pipeBusy is diagnostic only here.
    commands_complete = not bool(dp & 0x40) and dp_current == dp_end

    return {
        "sp_status": f"0x{sp:08X}",
        "dp_status": f"0x{dp:08X}",
        "dp_current": f"0x{dp_current:06X}",
        "dp_end": f"0x{dp_end:06X}",
        "rsp_halted": bool(sp & 1),
        "rdp_tmem_busy": bool(dp & 0x10),
        "rdp_pipe_busy": bool(dp & 0x20),
        "rdp_buffer_busy": bool(dp & 0x40),
        "rdp_ready": bool(dp & 0x80),
        "rdp_commands_complete": commands_complete,
    }


def require_fenced_boundary(client: RSPClient, *, stage: str) -> dict[str, object]:
    """Require the pinned-ares command fence without manufacturing progress."""
    state = read_engine_state(client)
    if not state["rsp_halted"]:
        raise RuntimeError(f"{stage}: boundary reached without RSP HALT: {state}")
    if not state["rdp_commands_complete"]:
        raise RuntimeError(
            f"{stage}: submitted RDP command list is not complete in pinned ares: {state}"
        )
    return state


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
    ap.add_argument("--prelaunch-address", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--mailbox-bytes", type=int, choices=(28, 32), default=28)
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

        # Stop immediately before the existing RSP-unhalt sequence after
        # frame_wait. In pinned ares, DP command-list execution is synchronous
        # with DP_END publication; PIPE_BUSY itself is sticky until Sync Full.
        # Accept only a naturally fenced list (bufferBusy clear and
        # DPC_CURRENT==DPC_END) with the RSP still HALT. Never manufacture
        # completion by repeated CPU stepping.
        set_breakpoint(client, args.prelaunch_address, True)
        validate_stop(client.request("c"), "seed prelaunch")
        seed_state = require_fenced_boundary(client, stage="seed prelaunch")

        sub_sentinel = SENTINEL.to_bytes(2, "big") * (SUB_STRIP_BYTES // 2)
        main_sentinel = SENTINEL.to_bytes(2, "big") * (MAIN_CAPTURE_BYTES // 2)
        write_pattern(client, SUB_COLOR_ADDR, sub_sentinel)
        verify_pattern(client, SUB_COLOR_ADDR, sub_sentinel)
        for address in FRAMEBUFFER_ADDRS:
            write_pattern(client, address, main_sentinel)
            verify_pattern(client, address, main_sentinel)

        # Clean provenance reuses the historical E1c compact 280x8 scratch.
        # Guard both sides so a green result proves section-lifetime bounding,
        # not merely that the sampled 8 rows happened to contain correct tags.
        provenance_sentinel = SENTINEL.to_bytes(2, "big") * (
            PROVENANCE_CAPTURE_BYTES // 2
        )
        provenance_prefix = bytes((0xC3,)) * PROVENANCE_GUARD_BYTES
        provenance_suffix = bytes((0x3C,)) * PROVENANCE_GUARD_BYTES
        write_pattern(client, PROVENANCE_PREFIX_ADDR, provenance_prefix)
        write_pattern(client, PROVENANCE_ACTIVE_ADDR, provenance_sentinel)
        write_pattern(client, PROVENANCE_SUFFIX_ADDR, provenance_suffix)
        verify_pattern(client, PROVENANCE_PREFIX_ADDR, provenance_prefix)
        verify_pattern(client, PROVENANCE_ACTIVE_ADDR, provenance_sentinel)
        verify_pattern(client, PROVENANCE_SUFFIX_ADDR, provenance_suffix)

        baseline_counter = read_u(client, args.guest_counter_address, 1)

        # Advance exactly across the inert +0x14 lui without GDB single-step.
        # Pinned ares can let an R4300 single-step cross the following jr delay
        # slot, whose +0x1C store clears SP HALT. Instead, arm a temporary
        # software breakpoint at +0x18 (the jr itself), remove +0x14, and
        # continue normally. Stopping before the jr guarantees the unhalt store
        # has not executed; then re-arm +0x14 behind the PC before releasing
        # the renderer for one complete frame.
        stepover_address = args.prelaunch_address + 4
        set_breakpoint(client, stepover_address, True)
        set_breakpoint(client, args.prelaunch_address, False)
        validate_stop(client.request("c"), "prelaunch one-instruction continue")
        step_state = require_fenced_boundary(client, stage="pre-jr prelaunch")
        set_breakpoint(client, args.prelaunch_address, True)
        set_breakpoint(client, stepover_address, False)

        validate_stop(client.request("c"), "fresh-frame prelaunch")
        final_state = require_fenced_boundary(client, stage="capture prelaunch")
        set_breakpoint(client, args.prelaunch_address, False)

        current_counter = read_u(client, args.guest_counter_address, 1)
        delta = (current_counter - baseline_counter) & 0xFF
        if delta < 1:
            raise RuntimeError(
                "renderer reentry did not include fresh guest time: "
                f"baseline=0x{baseline_counter:02X} current=0x{current_counter:02X}"
            )

        (out / "sub.bin").write_bytes(
            client.read_memory(SUB_COLOR_ADDR, SUB_STRIP_BYTES, 0x400)
        )
        for i, address in enumerate(FRAMEBUFFER_ADDRS, start=1):
            (out / f"main{i}.bin").write_bytes(
                client.read_memory(address, MAIN_CAPTURE_BYTES, 0x400)
            )
        for i, address in enumerate(SECTION_QUEUE_ADDRS, start=1):
            (out / f"section-q{i}.bin").write_bytes(
                client.read_memory(address, SECTION_CAPTURE_BYTES, 0x100)
            )
        (out / "gating-mailbox.bin").write_bytes(
            client.read_memory(GATING_MAILBOX_ADDR, args.mailbox_bytes, args.mailbox_bytes)
        )
        (out / "provenance-prefix.bin").write_bytes(
            client.read_memory(
                PROVENANCE_PREFIX_ADDR,
                PROVENANCE_GUARD_BYTES,
                PROVENANCE_GUARD_BYTES,
            )
        )
        (out / "provenance.bin").write_bytes(
            client.read_memory(
                PROVENANCE_ACTIVE_ADDR,
                PROVENANCE_CAPTURE_BYTES,
                0x400,
            )
        )
        (out / "provenance-suffix.bin").write_bytes(
            client.read_memory(
                PROVENANCE_SUFFIX_ADDR,
                PROVENANCE_GUARD_BYTES,
                PROVENANCE_GUARD_BYTES,
            )
        )

        state = {
            "warm_counter": warm_counter,
            "baseline_counter": baseline_counter,
            "current_counter": current_counter,
            "guest_frame_delta": delta,
            "renderer_frame_reentries": 1,
            "prelaunch_address": f"0x{args.prelaunch_address:08X}",
            "stepover_address": f"0x{stepover_address:08X}",
            "step_over_boundary": step_state,
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

