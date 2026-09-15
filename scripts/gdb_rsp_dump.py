#!/usr/bin/env python3
"""Run a remote target briefly through GDB RSP and capture a memory region.

This intentionally implements only the small subset needed by Sodium64 CI:
connect to a GDB server, continue execution, interrupt it, read memory in
bounded chunks, and detach. Keeping the client here avoids depending on a
particular host GDB build or interactive command timing.
"""

from __future__ import annotations

import argparse
import socket
import time
from pathlib import Path


def checksum(payload: bytes) -> bytes:
    return f"{sum(payload) & 0xFF:02x}".encode("ascii")


class RSPClient:
    def __init__(self, host: str, port: int, timeout: float = 10.0) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)

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
        encoded = payload.encode("ascii")
        self._send_packet_bytes(encoded)

        # In ACK mode, the server first acknowledges our packet. Some servers
        # can reply immediately without an explicit '+'; _read_packet handles
        # either form by skipping acknowledgements until '$'.
        return self._read_packet()

    def continue_then_interrupt(self, seconds: float) -> bytes:
        self._send_packet_bytes(b"c")
        time.sleep(seconds)
        # Raw 0x03 is the GDB remote asynchronous interrupt character.
        self.sock.sendall(b"\x03")
        return self._read_packet()

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


def connect_with_retry(host: str, port: int, deadline: float) -> RSPClient:
    end = time.monotonic() + deadline
    last_error: OSError | None = None
    while time.monotonic() < end:
        try:
            return RSPClient(host, port)
        except OSError as exc:
            last_error = exc
            time.sleep(0.25)
    raise ConnectionError(
        f"could not connect to GDB RSP server at {host}:{port} within {deadline}s"
    ) from last_error


def parse_int(text: str) -> int:
    return int(text, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9123)
    parser.add_argument("--connect-timeout", type=float, default=30.0)
    parser.add_argument("--run-seconds", type=float, default=3.0)
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--size", required=True, type=parse_int)
    parser.add_argument("--chunk-size", type=parse_int, default=0x400)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.size <= 0 or args.chunk_size <= 0:
        parser.error("--size and --chunk-size must be positive")

    client = connect_with_retry(args.host, args.port, args.connect_timeout)
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        print(f"GDB server capabilities: {supported.decode('ascii', errors='replace')}")

        initial = client.request("?")
        print(f"Initial target state: {initial.decode('ascii', errors='replace')}")

        stopped = client.continue_then_interrupt(args.run_seconds)
        print(f"Stopped target state: {stopped.decode('ascii', errors='replace')}")
        if not stopped.startswith((b"S", b"T")):
            raise RuntimeError(f"unexpected stop reply: {stopped!r}")

        data = client.read_memory(args.address, args.size, args.chunk_size)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
        print(
            f"Captured {len(data)} bytes from 0x{args.address:08X} "
            f"to {args.output}"
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
