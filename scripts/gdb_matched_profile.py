#!/usr/bin/env python3
"""Capture repeated Sodium64 profiles on exact 60-VI guest boundaries.

This is a measurement harness, not emulator logic. It configures the Road-to-1.0
APU/audio settings before the first guest cpu_execute, warms for an exact number
of 60-VI windows, resets only profiler-ring state at an update_fps boundary, and
captures a fixed number of complete subsequent windows.
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


def boundary_state(client: RSPClient, args: argparse.Namespace, index: int) -> dict[str, int]:
    state = {
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
        "dsp_due_count": read_uint(client, args.dsp_due_count, 4),
        "dsp_late_sum": read_uint(client, args.dsp_late_sum, 4),
        "dsp_late_max": read_uint(client, args.dsp_late_max, 4),
        "dsp_multi_due_count": read_uint(client, args.dsp_multi_due_count, 4),
    }
    if state["fps_native"] != 59:
        raise RuntimeError(
            f"window {index}: update_fps boundary expected fps_native=59, "
            f"got {state['fps_native']}"
        )
    if state["apu_clock"] != 21:
        raise RuntimeError(f"window {index}: apu_clock drifted to {state['apu_clock']}")
    if state["skipped_set"] != 0:
        raise RuntimeError(f"window {index}: frameskip drifted to {state['skipped_set']}")
    if state["audio_set"] != 4:
        raise RuntimeError(f"window {index}: audio setting drifted to {state['audio_set']}")
    if state["precision_set"] != 8:
        raise RuntimeError(
            f"window {index}: precision setting drifted to {state['precision_set']}"
        )
    return state


def advance_from_update_fps(client: RSPClient, args: argparse.Namespace, label: str) -> None:
    # The target is stopped at update_fps entry. Move past that exact boundary
    # before arming update_fps again, otherwise the same breakpoint would re-hit.
    continue_to_breakpoint(client, args.check_frame, label)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9140)
    parser.add_argument("--connect-timeout", type=float, default=45.0)
    parser.add_argument("--response-timeout", type=float, default=120.0)

    parser.add_argument("--cpu-execute", type=parse_int, required=True)
    parser.add_argument("--update-fps", type=parse_int, required=True)
    parser.add_argument("--check-frame", type=parse_int, required=True)

    parser.add_argument("--profile-address", type=parse_int, required=True)
    parser.add_argument("--profile-size", type=parse_int, required=True)
    parser.add_argument("--profile-buffer", type=parse_int, required=True)
    parser.add_argument("--profile-write-ptr", type=parse_int, required=True)
    parser.add_argument("--profile-sample-count", type=parse_int, required=True)
    parser.add_argument("--profile-last-epc", type=parse_int, required=True)

    parser.add_argument("--dsp-due-count", type=parse_int, required=True)
    parser.add_argument("--dsp-late-sum", type=parse_int, required=True)
    parser.add_argument("--dsp-late-max", type=parse_int, required=True)
    parser.add_argument("--dsp-multi-due-count", type=parse_int, required=True)

    parser.add_argument("--apu-clock", type=parse_int, required=True)
    parser.add_argument("--jit-lookup", type=parse_int, required=True)
    parser.add_argument("--jit-lookup-size", type=parse_int, required=True)
    parser.add_argument("--jit-pointer", type=parse_int, required=True)
    parser.add_argument("--jit-buffer", type=parse_int, required=True)
    parser.add_argument("--skipped-set", type=parse_int, required=True)
    parser.add_argument("--audio-set", type=parse_int, required=True)
    parser.add_argument("--precision-set", type=parse_int, required=True)

    parser.add_argument("--fps-native", type=parse_int, required=True)
    parser.add_argument("--fps-emulate", type=parse_int, required=True)
    parser.add_argument("--fps-display", type=parse_int, required=True)
    parser.add_argument("--frame-count", type=parse_int, required=True)

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
        if b"swbreak+" not in supported:
            raise RuntimeError("GDB server does not advertise software breakpoints")
        if b"QPassSignals+" not in supported:
            raise RuntimeError("GDB server does not advertise QPassSignals support")

        initial = client.request("?")
        print(f"Initial target state: {initial.decode('ascii', errors='replace')}")
        pass_reply = client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}")
        if pass_reply != b"OK":
            raise RuntimeError(f"target rejected QPassSignals: {pass_reply!r}")

        # Sodium64 has completed all emulator initialization and profile_init by
        # the first cpu_execute entry, but no guest CPU/APU execution has run yet.
        # This is a deterministic configuration boundary and avoids patching an
        # in-flight old APU JIT block.
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

        warmup: list[dict[str, int]] = []
        for index in range(1, args.warmup_windows + 1):
            continue_to_breakpoint(
                client, args.update_fps, f"warmup update_fps #{index}"
            )
            state = boundary_state(client, args, index)
            warmup.append(state)
            print("Warmup boundary: " + json.dumps(state, sort_keys=True))
            if index != args.warmup_windows:
                advance_from_update_fps(
                    client, args, f"warmup check_frame #{index}"
                )

        # We are stopped exactly at update_fps entry after the final warmup
        # 60-VI interval. Reset ONLY profiler ring metadata here. The next
        # update_fps entry will therefore delimit one exact measured 60-VI window.
        write_verified(
            client, args.profile_sample_count, b"\x00\x00\x00\x00",
            "profile sample count",
        )
        write_verified(
            client, args.profile_write_ptr, be(args.profile_buffer, 4),
            "profile write pointer",
        )
        write_verified(
            client, args.profile_last_epc, b"\x00\x00\x00\x00",
            "profile last EPC",
        )

        for address, label in (
            (args.dsp_due_count, "DSP due count"),
            (args.dsp_late_sum, "DSP late sum"),
            (args.dsp_late_max, "DSP late max"),
            (args.dsp_multi_due_count, "DSP multi-due count"),
        ):
            write_verified(client, address, b"\x00\x00\x00\x00", label)

        advance_from_update_fps(
            client, args, "measurement start check_frame"
        )
        measurement_start = time.monotonic()

        measured: list[dict[str, int]] = []
        previous_samples = 0
        for index in range(1, args.measure_windows + 1):
            continue_to_breakpoint(
                client, args.update_fps, f"measured update_fps #{index}"
            )
            state = boundary_state(client, args, index)
            if state["sample_count"] <= previous_samples:
                raise RuntimeError(
                    f"window {index}: profile sample count did not advance "
                    f"({previous_samples} -> {state['sample_count']})"
                )
            previous_samples = state["sample_count"]
            measured.append(state)
            print("Measured boundary: " + json.dumps(state, sort_keys=True))
            if index != args.measure_windows:
                advance_from_update_fps(
                    client, args, f"measured check_frame #{index}"
                )

        measured_wall_seconds = time.monotonic() - measurement_start
        frame_counts = [row["completed_frames"] for row in measured]
        final_samples = measured[-1]["sample_count"]

        data = client.read_memory(args.profile_address, args.profile_size, args.chunk_size)
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_bytes(data)

        result = {
            "measurement_contract": {
                "configuration_boundary": "first_cpu_execute_before_guest_execution",
                "window_boundary": "update_fps_entry",
                "vi_per_window": 60,
                "warmup_windows": args.warmup_windows,
                "measured_windows": args.measure_windows,
            },
            "configured": configured,
            "warmup": warmup,
            "measured": measured,
            "summary": {
                "frame_counts": frame_counts,
                "mean_frames_per_60_vi": statistics.fmean(frame_counts),
                "min_frames_per_60_vi": min(frame_counts),
                "max_frames_per_60_vi": max(frame_counts),
                "final_sample_count": final_samples,
                "measured_wall_seconds": measured_wall_seconds,
                "dsp_due_count": measured[-1]["dsp_due_count"],
                "dsp_late_sum": measured[-1]["dsp_late_sum"],
                "dsp_late_max": measured[-1]["dsp_late_max"],
                "dsp_multi_due_count": measured[-1]["dsp_multi_due_count"],
                "dsp_late_avg": (
                    measured[-1]["dsp_late_sum"] / measured[-1]["dsp_due_count"]
                    if measured[-1]["dsp_due_count"] else 0.0
                ),
            },
        }
        args.state_output.parent.mkdir(parents=True, exist_ok=True)
        args.state_output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Matched-window result: " + json.dumps(result["summary"], sort_keys=True))
        print(
            f"Captured {len(data)} bytes from 0x{args.profile_address:08X} "
            f"after {args.measure_windows} exact 60-VI windows"
        )

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
