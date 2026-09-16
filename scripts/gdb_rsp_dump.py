#!/usr/bin/env python3
"""Run a remote target through GDB RSP and capture a profiling memory region.

This intentionally implements only the small subset needed by Sodium64 CI:
connect to a GDB server, optionally warm the target up, patch/zero known memory,
run one or more measured windows, interrupt, read memory in bounded chunks, and
detach. Keeping the client here avoids depending on a particular host GDB build
or interactive command timing.
"""

from __future__ import annotations

import argparse
import socket
import time
from pathlib import Path


# ares maps normal emulated N64 CPU exceptions onto GDB signals. For profiling
# those exceptions must remain guest-visible instead of stopping the debugger;
# the target's own exception handler should see exactly what hardware would.
# Ctrl-C still halts through ares' explicit debugger halt path, so it is not
# affected by this pass list.
ARES_N64_GUEST_SIGNALS = "04;05;06;08;0a;0b;0c;10;11;1d"


def checksum(payload: bytes) -> bytes:
    return f"{sum(payload) & 0xFF:02x}".encode("ascii")


class RSPClient:
    def __init__(self, host: str, port: int, timeout: float = 30.0) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        # ares' TCPText GDB server uses an initial '+' as a lightweight
        # anti-browser handshake before it will accept the first RSP packet.
        self.sock.sendall(b"+")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def _send_packet_bytes(self, payload: bytes) -> None:
        self.sock.sendall(b"$" + payload + b"#" + checksum(payload))

    def _read_packet(self) -> bytes:
        while True:
            byte = self.sock.recv(1)
            if not byte:
                raise ConnectionError("GDB RSP connection closed")
            if byte in (b"+", b"-"):
                continue
            if byte != b"$":
                continue

            payload = bytearray()
            while True:
                byte = self.sock.recv(1)
                if not byte:
                    raise ConnectionError("GDB RSP connection closed mid-packet")
                if byte == b"#":
                    break
                payload.extend(byte)

            received_sum = self.sock.recv(2)
            if len(received_sum) != 2:
                raise ConnectionError("GDB RSP connection closed during checksum")
            expected = checksum(bytes(payload))
            if received_sum.lower() != expected:
                self.sock.sendall(b"-")
                continue
            self.sock.sendall(b"+")
            return bytes(payload)

    def request(self, payload: str) -> bytes:
        self._send_packet_bytes(payload.encode("ascii"))
        return self._read_packet()

    def continue_then_interrupt(self, seconds: float) -> bytes:
        self._send_packet_bytes(b"c")

        # A target may stop on its own before the requested sampling window
        # expires. Listen for that stop while the window is open. Sending
        # Ctrl-C after an already-pending stop would queue a second stop packet
        # and shift every following request/reply pair out of sync.
        previous_timeout = self.sock.gettimeout()
        try:
            self.sock.settimeout(seconds)
            try:
                return self._read_packet()
            except socket.timeout:
                pass

            # No spontaneous stop arrived in the requested window. Halt the
            # target explicitly. Heavy PPU/RDP workloads can leave ares busy in
            # host shader work for several seconds, so use the normal response
            # timeout here rather than the short sampling-window timeout.
            self.sock.settimeout(previous_timeout)
            self.sock.sendall(b"\x03")
            return self._read_packet()
        finally:
            self.sock.settimeout(previous_timeout)

    def read_memory(self, address: int, size: int, chunk_size: int) -> bytes:
        result = bytearray()
        offset = 0
        while offset < size:
            length = min(chunk_size, size - offset)
            reply = self.request(f"m{address + offset:x},{length:x}")
            if reply.startswith(b"E"):
                raise RuntimeError(
                    f"target rejected memory read at 0x{address + offset:08X}: "
                    f"{reply.decode('ascii', errors='replace')}"
                )
            try:
                data = bytes.fromhex(reply.decode("ascii"))
            except ValueError as exc:
                raise RuntimeError(
                    f"invalid hex memory reply at 0x{address + offset:08X}: {reply!r}"
                ) from exc
            if len(data) != length:
                raise RuntimeError(
                    f"short memory reply at 0x{address + offset:08X}: "
                    f"expected {length}, got {len(data)}"
                )
            result.extend(data)
            offset += length
        return bytes(result)

    def write_memory(self, address: int, data: bytes) -> None:
        if not data:
            raise ValueError("cannot write an empty memory payload")
        reply = self.request(f"M{address:x},{len(data):x}:{data.hex()}")
        if reply != b"OK":
            raise RuntimeError(
                f"target rejected memory write at 0x{address:08X}: "
                f"{reply.decode('ascii', errors='replace')}"
            )

    def zero_memory(self, address: int, size: int, chunk_size: int) -> None:
        if size <= 0:
            raise ValueError("zero-memory size must be positive")
        offset = 0
        while offset < size:
            length = min(chunk_size, size - offset)
            self.write_memory(address + offset, bytes(length))
            offset += length

        # Verify the complete range. This happens while the target is stopped,
        # so correctness matters more than a small amount of host-side traffic.
        verify = self.read_memory(address, size, chunk_size)
        if any(verify):
            raise RuntimeError(
                f"zero-memory verification failed for 0x{address:08X}+0x{size:X}"
            )


def connect_with_retry(
    host: str,
    port: int,
    deadline: float,
    response_timeout: float,
) -> RSPClient:
    end = time.monotonic() + deadline
    last_error: OSError | None = None
    while time.monotonic() < end:
        try:
            return RSPClient(host, port, timeout=response_timeout)
        except OSError as exc:
            last_error = exc
            time.sleep(0.25)
    raise ConnectionError(
        f"could not connect to GDB RSP server at {host}:{port} within {deadline}s"
    ) from last_error


def parse_int(text: str) -> int:
    return int(text, 0)


def parse_write(text: str) -> tuple[int, bytes]:
    """Parse ADDRESS:HEXBYTES, e.g. 0x80001234:15."""
    try:
        address_text, data_text = text.split(":", 1)
        address = int(address_text, 0)
        data = bytes.fromhex(data_text)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            "memory writes must use ADDRESS:HEXBYTES, e.g. 0x80001234:15"
        ) from exc
    if not data:
        raise argparse.ArgumentTypeError("memory write payload cannot be empty")
    return address, data


def parse_range(text: str) -> tuple[int, int]:
    """Parse ADDRESS:SIZE, with both values accepting Python integer syntax."""
    try:
        address_text, size_text = text.split(":", 1)
        address = int(address_text, 0)
        size = int(size_text, 0)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            "ranges must use ADDRESS:SIZE, e.g. 0x80010000:0x40000"
        ) from exc
    if size <= 0:
        raise argparse.ArgumentTypeError("range size must be positive")
    return address, size


def validate_stop(reply: bytes, stage: str) -> None:
    text = reply.decode("ascii", errors="replace")
    print(f"{stage} target state: {text}")
    if not reply.startswith((b"S", b"T")):
        raise RuntimeError(f"unexpected {stage.lower()} stop reply: {reply!r}")


def read_be_u32(client: RSPClient, address: int) -> int:
    return int.from_bytes(client.read_memory(address, 4, 4), "big")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9123)
    parser.add_argument("--connect-timeout", type=float, default=30.0)
    parser.add_argument(
        "--response-timeout",
        type=float,
        default=30.0,
        help="timeout for GDB replies after the target is explicitly stopped",
    )
    parser.add_argument(
        "--warmup-seconds",
        type=float,
        default=0.0,
        help="run once before applying memory patches and starting measurement",
    )
    parser.add_argument(
        "--run-seconds",
        type=float,
        default=3.0,
        help="wall-clock duration of each measured run window",
    )
    parser.add_argument(
        "--max-run-seconds",
        type=float,
        help="maximum summed measured run-window time when --min-samples is used",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=0,
        help="continue additional measured windows until this many samples exist",
    )
    parser.add_argument(
        "--sample-count-address",
        type=parse_int,
        help="big-endian u32 profile sample-count address used by --min-samples",
    )
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--size", required=True, type=parse_int)
    parser.add_argument("--chunk-size", type=parse_int, default=0x400)
    parser.add_argument(
        "--write",
        action="append",
        type=parse_write,
        default=[],
        metavar="ADDRESS:HEXBYTES",
        help="patch target memory after warmup and before measurement (repeatable)",
    )
    parser.add_argument(
        "--zero",
        action="append",
        type=parse_range,
        default=[],
        metavar="ADDRESS:SIZE",
        help="zero a target memory range after warmup and before measurement",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.size <= 0 or args.chunk_size <= 0:
        parser.error("--size and --chunk-size must be positive")
    if args.warmup_seconds < 0 or args.run_seconds <= 0 or args.response_timeout <= 0:
        parser.error("warmup must be >= 0; run/response timeouts must be > 0")
    if args.min_samples < 0:
        parser.error("--min-samples must be >= 0")
    if args.min_samples and args.sample_count_address is None:
        parser.error("--min-samples requires --sample-count-address")
    max_run_seconds = args.max_run_seconds or args.run_seconds
    if max_run_seconds < args.run_seconds:
        parser.error("--max-run-seconds cannot be shorter than --run-seconds")

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
            raise RuntimeError("GDB server does not advertise QPassSignals support")
        pass_reply = client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}")
        print(f"Guest exception pass-through: {pass_reply.decode('ascii', errors='replace')}")
        if pass_reply != b"OK":
            raise RuntimeError(f"target rejected QPassSignals: {pass_reply!r}")

        if args.warmup_seconds:
            validate_stop(
                client.continue_then_interrupt(args.warmup_seconds),
                "Warmup stop",
            )

        for zero_address, zero_size in args.zero:
            client.zero_memory(zero_address, zero_size, args.chunk_size)
            print(f"Zeroed {zero_size} byte(s) at 0x{zero_address:08X}")

        for write_address, write_data in args.write:
            client.write_memory(write_address, write_data)
            verify = client.read_memory(write_address, len(write_data), len(write_data))
            if verify != write_data:
                raise RuntimeError(
                    f"memory write verification failed at 0x{write_address:08X}: "
                    f"wrote {write_data.hex()}, read {verify.hex()}"
                )
            print(
                f"Patched {len(write_data)} byte(s) at 0x{write_address:08X}: "
                f"{write_data.hex()}"
            )

        measured_seconds = 0.0
        window = 0
        while True:
            remaining = max_run_seconds - measured_seconds
            if remaining <= 0:
                break
            duration = min(args.run_seconds, remaining)
            window += 1
            validate_stop(
                client.continue_then_interrupt(duration),
                f"Measured stop #{window}",
            )
            measured_seconds += duration

            if not args.min_samples:
                break

            sample_count = read_be_u32(client, args.sample_count_address)
            print(
                f"Samples after {measured_seconds:g}s measured wall time: "
                f"{sample_count} (target {args.min_samples})"
            )
            if sample_count >= args.min_samples:
                break

        data = client.read_memory(args.address, args.size, args.chunk_size)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
        print(
            f"Captured {len(data)} bytes from 0x{args.address:08X} "
            f"to {args.output} after {measured_seconds:g}s measured wall time"
        )

        # Detach is best-effort; CI terminates the emulator process afterwards.
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
