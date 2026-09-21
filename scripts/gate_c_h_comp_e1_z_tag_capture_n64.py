#!/usr/bin/env python3
"""Capture/classify Gate-C E1a primitive-Z metadata proof in pinned N64 ares."""

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

PREFIX_BYTE = 0xC3
SENTINEL_WORD = 0x55AA
SUFFIX_BYTE = 0x3C
TAG_WORD = 0x0C00
OPAQUE_BLACK_RGBA5551 = 0x0001


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
            f"E1a proof poll #{attempt}",
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
    raise RuntimeError("E1a proof marker/fresh guest frame was not observed")


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


def classify(framebuffer: bytes, depth: bytes, prefix: bytes, suffix: bytes) -> dict[str, object]:
    assert len(framebuffer) == FB_BYTES
    assert len(depth) == Z_SIZE

    fb_words = [
        int.from_bytes(framebuffer[i:i + 2], "big")
        for i in range(0, len(framebuffer), 2)
    ]
    z_words = [
        int.from_bytes(depth[i:i + 2], "big")
        for i in range(0, len(depth), 2)
    ]

    fb_hist = collections.Counter(fb_words)
    z_hist = collections.Counter(z_words)

    opaque_pixels = 0
    visible_backdrop_pixels = 0
    opaque_wrong: list[dict[str, int]] = []
    backdrop_wrong: list[dict[str, int]] = []
    unexpected_depth: list[dict[str, int]] = []
    tag_on_nonblack: list[dict[str, int]] = []

    for index, (fb, z) in enumerate(zip(fb_words, z_words)):
        y, x = divmod(index, FB_WIDTH)
        if fb == OPAQUE_BLACK_RGBA5551:
            opaque_pixels += 1
            if z != TAG_WORD and len(opaque_wrong) < 64:
                opaque_wrong.append({"x": x, "y": y, "fb": fb, "z": z})
        elif fb != 0:
            visible_backdrop_pixels += 1
            if z != SENTINEL_WORD and len(backdrop_wrong) < 64:
                backdrop_wrong.append({"x": x, "y": y, "fb": fb, "z": z})

        if z not in (SENTINEL_WORD, TAG_WORD) and len(unexpected_depth) < 64:
            unexpected_depth.append({"x": x, "y": y, "fb": fb, "z": z})
        if z == TAG_WORD and fb != OPAQUE_BLACK_RGBA5551 and len(tag_on_nonblack) < 64:
            tag_on_nonblack.append({"x": x, "y": y, "fb": fb, "z": z})

    prefix_ok = prefix == bytes([PREFIX_BYTE]) * Z_PREFIX_SIZE
    suffix_ok = suffix == bytes([SUFFIX_BYTE]) * Z_SUFFIX_SIZE
    enough_opaque = opaque_pixels >= 10000
    enough_backdrop = visible_backdrop_pixels >= 10000

    passed = (
        prefix_ok
        and suffix_ok
        and enough_opaque
        and enough_backdrop
        and not opaque_wrong
        and not backdrop_wrong
        and not unexpected_depth
        and not tag_on_nonblack
        and z_hist[TAG_WORD] == opaque_pixels
    )

    return {
        "classification": "E1A_Z_TAG_ALPHA_CONTRACT_VALIDATED" if passed else "E1A_Z_TAG_ALPHA_CONTRACT_FAILED",
        "passed": passed,
        "constants": {
            "width": FB_WIDTH,
            "height": FB_HEIGHT,
            "z_command_address": hex(Z_COMMAND_ADDR),
            "z_base": hex(Z_BASE),
            "z_size": Z_SIZE,
            "status_address": hex(STATUS_ADDR),
            "status_marker": hex(STATUS_MARKER),
            "sentinel_word": hex(SENTINEL_WORD),
            "expected_tag_word": hex(TAG_WORD),
            "opaque_black_rgba5551": hex(OPAQUE_BLACK_RGBA5551),
        },
        "counts": {
            "opaque_black_pixels": opaque_pixels,
            "visible_backdrop_pixels": visible_backdrop_pixels,
            "tag_words": z_hist[TAG_WORD],
            "sentinel_words": z_hist[SENTINEL_WORD],
            "total_pixels": len(z_words),
        },
        "guards": {
            "prefix_ok": prefix_ok,
            "suffix_ok": suffix_ok,
        },
        "framebuffer_histogram_top": [
            {"word": hex(word), "count": count}
            for word, count in fb_hist.most_common(12)
        ],
        "depth_histogram_top": [
            {"word": hex(word), "count": count}
            for word, count in z_hist.most_common(12)
        ],
        "mismatches": {
            "opaque_wrong": opaque_wrong,
            "backdrop_wrong": backdrop_wrong,
            "unexpected_depth": unexpected_depth,
            "tag_on_nonblack": tag_on_nonblack,
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
        validate_stop(client.request("c"), "E1a clean-epoch breakpoint")
        anchor = read_quiescent_state(client)
        validate_quiescent_state(anchor, require_marker=True)

        # Create the clean epoch only now, between frames with the RSP halted.
        initialize_proof_memory(client)
        baseline_counter = read_u(client, args.guest_counter_address, 1)

        # Step over the breakpoint once, reinstall it behind the PC, and let one
        # complete subsequent RSP frame reach the same quiescent boundary.
        set_breakpoint(client, args.capture_ready_address, False)
        validate_stop(client.request("s"), "E1a breakpoint step-over")
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "E1a fenced capture breakpoint")

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
        prefix = client.read_memory(Z_COMMAND_ADDR, Z_PREFIX_SIZE, 0x400)
        depth = client.read_memory(Z_BASE, Z_SIZE, 0x400)
        suffix = client.read_memory(Z_BASE + Z_SIZE, Z_SUFFIX_SIZE, 0x100)

        (out / "framebuffer.rgba5551").write_bytes(framebuffer)
        (out / "depth.bin").write_bytes(depth)
        (out / "prefix_guard.bin").write_bytes(prefix)
        (out / "suffix_guard.bin").write_bytes(suffix)

        result = classify(framebuffer, depth, prefix, suffix)
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
            raise RuntimeError("E1a semantic classifier failed; see result.json")

        try:
            client.request("D")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
