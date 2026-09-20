#!/usr/bin/env python3
"""Capture control/treatment Sodium64 framebuffers for the Gate-C OBJ-window test.

The target is a pinned N64 ares instance running the wrapped original diagnostic.
This client synchronizes on the diagnostic's WRAM phase mirror and captures a
non-blank displayed Sodium64 framebuffer plus selected emulator state through
ares' N64 GDB server. A blank framebuffer is treated as startup/stale lab state,
never as semantic evidence.
"""

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


CONTROL = 0x01
TREATMENT = 0x11
FB_WIDTH = 280
FB_HEIGHT = 240
FB_BYTES = FB_WIDTH * FB_HEIGHT * 2


def parse_int(text: str) -> int:
    return int(text, 0)


def parse_observation(text: str) -> tuple[str, int, int]:
    try:
        label, address_text, size_text = text.split(":", 2)
        address = int(address_text, 0)
        size = int(size_text, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("observations use LABEL:ADDRESS:SIZE") from exc
    if size not in (1, 2, 4):
        raise argparse.ArgumentTypeError("observation size must be 1, 2, or 4")
    return label, address, size


def read_u(client: RSPClient, address: int, size: int) -> int:
    return int.from_bytes(client.read_memory(address, size, size), "big")


def wait_for_phase(
    client: RSPClient,
    *,
    phase_address: int,
    target: int,
    poll_seconds: float,
    attempts: int,
) -> None:
    for attempt in range(1, attempts + 1):
        validate_stop(
            client.continue_then_interrupt(poll_seconds),
            f"Phase {target:02x} poll #{attempt}",
        )
        phase = read_u(client, phase_address, 1)
        if phase == target:
            return
        print(f"phase mirror=0x{phase:02X}, waiting for 0x{target:02X}")
    raise RuntimeError(f"did not observe phase 0x{target:02X}")


def capture_nonblank_phase(
    client: RSPClient,
    *,
    name: str,
    target: int,
    phase_address: int,
    framebuffer_address: int,
    observations: list[tuple[str, int, int]],
    output_dir: Path,
    poll_seconds: float,
    attempts: int,
) -> dict[str, object]:
    wait_for_phase(
        client,
        phase_address=phase_address,
        target=target,
        poll_seconds=poll_seconds,
        attempts=attempts,
    )

    # The control phase is already active during emulator startup, so a first
    # displayed-buffer pointer can legitimately refer to a not-yet-rendered
    # cleared buffer. Require actual rendered pixels while the guest remains in
    # the requested phase. This removes wall-clock startup races from evidence.
    for render_attempt in range(1, attempts + 1):
        phase = read_u(client, phase_address, 1)
        if phase != target:
            print(
                f"{name}: phase changed to 0x{phase:02X} before a rendered "
                "frame was captured; waiting for next occurrence"
            )
            wait_for_phase(
                client,
                phase_address=phase_address,
                target=target,
                poll_seconds=poll_seconds,
                attempts=attempts,
            )

        fb_pointer = read_u(client, framebuffer_address, 4)
        if not (0x80000000 <= fb_pointer <= 0xBFFFFFFF):
            raise RuntimeError(f"unexpected framebuffer pointer 0x{fb_pointer:08X}")
        raw = client.read_memory(fb_pointer, FB_BYTES, 0x400)

        if any(raw) and read_u(client, phase_address, 1) == target:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / f"{name}.rgba5551").write_bytes(raw)

            state: dict[str, int] = {
                "phase": target,
                "framebuffer_pointer": fb_pointer,
                "render_attempt": render_attempt,
            }
            for label, address, size in observations:
                state[label] = read_u(client, address, size)
            print(
                f"{name}: phase=0x{target:02X} framebuffer=0x{fb_pointer:08X} "
                f"bytes={len(raw)} render_attempt={render_attempt} state={state}"
            )
            return state

        print(
            f"{name}: blank/stale framebuffer 0x{fb_pointer:08X} on "
            f"render attempt {render_attempt}; continuing"
        )
        validate_stop(
            client.continue_then_interrupt(poll_seconds),
            f"{name} render poll #{render_attempt}",
        )

    raise RuntimeError(f"no non-blank framebuffer captured for phase 0x{target:02X}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9140)
    parser.add_argument("--connect-timeout", type=float, default=30.0)
    parser.add_argument("--response-timeout", type=float, default=30.0)
    parser.add_argument("--phase-address", required=True, type=parse_int)
    parser.add_argument("--framebuffer-address", required=True, type=parse_int)
    parser.add_argument(
        "--observe",
        action="append",
        type=parse_observation,
        default=[],
        metavar="LABEL:ADDRESS:SIZE",
    )
    parser.add_argument("--poll-seconds", type=float, default=0.20)
    parser.add_argument("--attempts", type=int, default=50)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    client = connect_with_retry(
        args.host,
        args.port,
        args.connect_timeout,
        args.response_timeout,
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

        states = {}
        for name, target in (("control", CONTROL), ("treatment", TREATMENT)):
            states[name] = capture_nonblank_phase(
                client,
                name=name,
                target=target,
                phase_address=args.phase_address,
                framebuffer_address=args.framebuffer_address,
                observations=args.observe,
                output_dir=args.output_dir,
                poll_seconds=args.poll_seconds,
                attempts=args.attempts,
            )

        (args.output_dir / "state.json").write_text(
            json.dumps(states, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            client.request("D")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
