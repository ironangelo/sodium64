#!/usr/bin/env python3
"""Capture SRS state and Sodium64 profile on exact 60-VI guest boundaries.

This is a Gate-B measurement harness, not emulator logic. Road-valid settings
are established at the first cpu_execute entry before any guest CPU/APU work.
The benchmark is then observed at complete update_fps boundaries so route
progression is compared in guest time rather than CI wall time.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from gdb_rsp_dump import (
    ARES_N64_GUEST_SIGNALS,
    RSPClient,
    connect_with_retry,
    validate_stop,
)

BREAKPOINT_KIND = 4


def parse_int(text: str) -> int:
    return int(text, 0)


def be(value: int, size: int) -> bytes:
    return int(value).to_bytes(size, "big", signed=False)


def read_uint(client: RSPClient, address: int, size: int) -> int:
    return int.from_bytes(client.read_memory(address, size, size), "big")


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


def write_verified(client: RSPClient, address: int, data: bytes, label: str) -> None:
    client.write_memory(address, data)
    actual = client.read_memory(address, len(data), len(data))
    if actual != data:
        raise RuntimeError(
            f"{label} verification failed at 0x{address:08X}: "
            f"wrote {data.hex()}, read {actual.hex()}"
        )


def read_snes_u16(client: RSPClient, lo_addr: int, hi_addr: int) -> int:
    lo = read_uint(client, lo_addr, 1)
    hi = read_uint(client, hi_addr, 1)
    return lo | (hi << 8)


def read_snes_u32(
    client: RSPClient, b0_addr: int, b1_addr: int, b2_addr: int, b3_addr: int
) -> int:
    b0 = read_uint(client, b0_addr, 1)
    b1 = read_uint(client, b1_addr, 1)
    b2 = read_uint(client, b2_addr, 1)
    b3 = read_uint(client, b3_addr, 1)
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)


def guest_state(client: RSPClient, args: argparse.Namespace) -> dict[str, int]:
    return {
        "frame_counter": read_snes_u32(
            client,
            args.srs_frame_counter,
            args.srs_frame_counter_1,
            args.srs_frame_counter_2,
            args.srs_frame_counter_3,
        ),
        "room_id": read_uint(client, args.srs_room_id, 1),
        "player_x": read_snes_u16(client, args.srs_player_x, args.srs_player_x_hi),
        "player_y": read_snes_u16(client, args.srs_player_y, args.srs_player_y_hi),
        "camera_x": read_snes_u16(client, args.srs_camera_x, args.srs_camera_x_hi),
        "camera_y": read_snes_u16(client, args.srs_camera_y, args.srs_camera_y_hi),
    }


def boundary_state(
    client: RSPClient, args: argparse.Namespace, phase: str, index: int
) -> dict[str, object]:
    state: dict[str, object] = {
        "phase": phase,
        "window": index,
        "fps_native": read_uint(client, args.fps_native, 1),
        "completed_frames": read_uint(client, args.fps_emulate, 1),
        "fps_display_previous": read_uint(client, args.fps_display, 1),
        "frame_queue": read_uint(client, args.frame_count, 1),
        "sample_count": read_uint(client, args.profile_sample_count, 4),
        "apu_clock": read_uint(client, args.apu_clock, 1),
        "skipped_set": read_uint(client, args.skipped_set, 1),
        "audio_set": read_uint(client, args.audio_set, 1),
        "precision_set": read_uint(client, args.precision_set, 1),
        "guest": guest_state(client, args),
    }
    if state["fps_native"] != 59:
        raise RuntimeError(
            f"{phase} window {index}: update_fps boundary expected fps_native=59, "
            f"got {state['fps_native']}"
        )
    for key, expected in (
        ("apu_clock", 21),
        ("skipped_set", 0),
        ("audio_set", 4),
        ("precision_set", 8),
    ):
        if state[key] != expected:
            raise RuntimeError(
                f"{phase} window {index}: {key} drifted to {state[key]}, expected {expected}"
            )
    return state


def advance_from_update_fps(client: RSPClient, args: argparse.Namespace, label: str) -> None:
    continue_to_breakpoint(client, args.check_frame, label)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9140)
    parser.add_argument("--connect-timeout", type=float, default=45.0)
    parser.add_argument("--response-timeout", type=float, default=120.0)

    for name in ("cpu_execute", "update_fps", "check_frame"):
        parser.add_argument("--" + name.replace("_", "-"), type=parse_int, required=True)

    for name in (
        "profile_address", "profile_size", "profile_buffer", "profile_write_ptr",
        "profile_sample_count", "profile_last_epc", "apu_clock", "jit_lookup",
        "jit_lookup_size", "jit_pointer", "jit_buffer", "skipped_set", "audio_set",
        "precision_set", "fps_native", "fps_emulate", "fps_display", "frame_count",
        "srs_frame_counter", "srs_frame_counter_1", "srs_frame_counter_2",
        "srs_frame_counter_3", "srs_room_id", "srs_player_x", "srs_player_x_hi",
        "srs_player_y", "srs_player_y_hi", "srs_camera_x", "srs_camera_x_hi",
        "srs_camera_y", "srs_camera_y_hi",
    ):
        parser.add_argument("--" + name.replace("_", "-"), type=parse_int, required=True)

    parser.add_argument("--warmup-windows", type=int, default=2)
    parser.add_argument("--measure-windows", type=int, default=5)
    parser.add_argument("--chunk-size", type=parse_int, default=0x400)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--state-output", type=Path, required=True)
    args = parser.parse_args()

    if args.profile_size <= 0 or args.jit_lookup_size <= 0 or args.chunk_size <= 0:
        parser.error("profile/JIT/chunk sizes must be positive")
    if args.warmup_windows < 1 or args.measure_windows < 1:
        parser.error("warmup/measure windows must be positive")

    client = connect_with_retry(
        args.host, args.port, args.connect_timeout, args.response_timeout
    )
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        print(f"GDB server capabilities: {supported.decode('ascii', errors='replace')}")
        if b"swbreak+" not in supported or b"QPassSignals+" not in supported:
            raise RuntimeError("required ares GDB capabilities unavailable")

        initial = client.request("?")
        print(f"Initial target state: {initial.decode('ascii', errors='replace')}")
        pass_reply = client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}")
        if pass_reply != b"OK":
            raise RuntimeError(f"target rejected QPassSignals: {pass_reply!r}")

        # Safe M1-proven configuration boundary: Sodium64 initialization and
        # profile_init are complete, but guest CPU/APU execution has not begun.
        continue_to_breakpoint(client, args.cpu_execute, "first guest cpu_execute")

        client.zero_memory(args.jit_lookup, args.jit_lookup_size, args.chunk_size)
        write_verified(client, args.apu_clock, b"\x15", "APU clock")
        write_verified(client, args.jit_pointer, be(args.jit_buffer, 4), "JIT pointer")
        write_verified(client, args.skipped_set, b"\x00", "frameskip")
        write_verified(client, args.audio_set, b"\x04", "audio")
        write_verified(client, args.precision_set, b"\x08", "precision")

        configured = {
            "apu_clock": read_uint(client, args.apu_clock, 1),
            "skipped_set": read_uint(client, args.skipped_set, 1),
            "audio_set": read_uint(client, args.audio_set, 1),
            "precision_set": read_uint(client, args.precision_set, 1),
            "jit_pointer": read_uint(client, args.jit_pointer, 4),
        }
        print("Configured before first guest execution: " + json.dumps(configured, sort_keys=True))

        warmup: list[dict[str, object]] = []
        for index in range(1, args.warmup_windows + 1):
            continue_to_breakpoint(client, args.update_fps, f"warmup update_fps #{index}")
            state = boundary_state(client, args, "warmup", index)
            warmup.append(state)
            print("Warmup boundary: " + json.dumps(state, sort_keys=True))
            if index != args.warmup_windows:
                advance_from_update_fps(client, args, f"warmup check_frame #{index}")

        # Reset only statistical ring state at an exact guest-time boundary.
        write_verified(client, args.profile_sample_count, b"\x00\x00\x00\x00", "sample count")
        write_verified(client, args.profile_write_ptr, be(args.profile_buffer, 4), "write pointer")
        write_verified(client, args.profile_last_epc, b"\x00\x00\x00\x00", "last EPC")

        advance_from_update_fps(client, args, "measurement start check_frame")
        measurement_start = time.monotonic()

        measured: list[dict[str, object]] = []
        previous_samples = 0
        for index in range(1, args.measure_windows + 1):
            continue_to_breakpoint(client, args.update_fps, f"measured update_fps #{index}")
            state = boundary_state(client, args, "measured", index)
            sample_count = int(state["sample_count"])
            if sample_count <= previous_samples:
                raise RuntimeError(
                    f"window {index}: profile sample count did not advance "
                    f"({previous_samples} -> {sample_count})"
                )
            previous_samples = sample_count
            measured.append(state)
            print("Measured boundary: " + json.dumps(state, sort_keys=True))
            if index != args.measure_windows:
                advance_from_update_fps(client, args, f"measured check_frame #{index}")

        data = client.read_memory(args.profile_address, args.profile_size, args.chunk_size)
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_bytes(data)

        frame_counts = [int(row["completed_frames"]) for row in measured]
        result = {
            "measurement_contract": {
                "configuration_boundary": "first_cpu_execute_before_guest_execution",
                "window_boundary": "update_fps_entry",
                "vi_per_window": 60,
                "warmup_windows": args.warmup_windows,
                "measured_windows": args.measure_windows,
                "guest_state_sampling": "byte-wise at every complete 60-VI boundary",
            },
            "configured": configured,
            "warmup": warmup,
            "measured": measured,
            "summary": {
                "frame_counts": frame_counts,
                "mean_frames_per_60_vi": statistics.fmean(frame_counts),
                "min_frames_per_60_vi": min(frame_counts),
                "max_frames_per_60_vi": max(frame_counts),
                "final_sample_count": int(measured[-1]["sample_count"]),
                "measured_wall_seconds": time.monotonic() - measurement_start,
            },
        }
        args.state_output.parent.mkdir(parents=True, exist_ok=True)
        args.state_output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("Matched SRS result: " + json.dumps(result["summary"], sort_keys=True))

        try:
            reply = client.request("D")
            print(f"Detach reply: {reply.decode('ascii', errors='replace')}")
        except (ConnectionError, OSError, RuntimeError):
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
