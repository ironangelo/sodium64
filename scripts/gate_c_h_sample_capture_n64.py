#!/usr/bin/env python3
"""Capture the completed Sodium64 section queue for the Gate-C H-SAMPLE test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gdb_rsp_dump import (
    ARES_N64_GUEST_SIGNALS,
    RSPClient,
    connect_with_retry,
    validate_stop,
)

SECTION_SIZE = 0x40
SECTION_QUEUE_SIZE = 0x5000
WH0_OFFSET = 0x2E
WH1_OFFSET = 0x2F
END_LINE_OFFSET = 0x3F
VISIBLE_FINAL_END_LINE = 224
PROBE_SIZE = 224


def parse_int(text: str) -> int:
    return int(text, 0)


def read_uint(client: RSPClient, address: int, size: int) -> int:
    return int.from_bytes(client.read_memory(address, size, size), "big")


def parse_records(data: bytes) -> list[dict[str, int]]:
    if len(data) != SECTION_QUEUE_SIZE:
        raise ValueError(f"expected 0x{SECTION_QUEUE_SIZE:X} queue bytes")
    records: list[dict[str, int]] = []
    for index in range(SECTION_QUEUE_SIZE // SECTION_SIZE):
        offset = index * SECTION_SIZE
        record = {
            "index": index,
            "wh0": data[offset + WH0_OFFSET],
            "wh1": data[offset + WH1_OFFSET],
            "end_line": data[offset + END_LINE_OFFSET],
        }
        records.append(record)
        if record["end_line"] >= VISIBLE_FINAL_END_LINE:
            break
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9142)
    parser.add_argument("--connect-timeout", type=float, default=30.0)
    parser.add_argument("--response-timeout", type=float, default=30.0)
    parser.add_argument("--warmup-seconds", type=float, default=2.0)
    parser.add_argument("--sect-queues-address", required=True, type=parse_int)
    parser.add_argument("--section-ptr-address", required=True, type=parse_int)
    parser.add_argument("--queue-id-address", required=True, type=parse_int)
    parser.add_argument("--precision-address", required=True, type=parse_int)
    parser.add_argument(
        "--force-precision",
        type=parse_int,
        choices=(0, 4, 8, 12, 16, 20),
        help="optional diagnostic-only precision_set byte to patch after runtime initialization",
    )
    parser.add_argument("--cur-line-address", required=True, type=parse_int)
    parser.add_argument("--whx-address", required=True, type=parse_int)
    parser.add_argument("--cooldown-address", required=True, type=parse_int)
    parser.add_argument("--sect-status-address", required=True, type=parse_int)
    parser.add_argument("--frame-counter-address", required=True, type=parse_int)
    parser.add_argument("--probe-address", required=True, type=parse_int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    client = connect_with_retry(
        args.host, args.port, args.connect_timeout, args.response_timeout
    )
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        if b"QPassSignals+" not in supported:
            raise RuntimeError("GDB server does not advertise QPassSignals support")
        if client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}") != b"OK":
            raise RuntimeError("target rejected QPassSignals")

        initial = client.request("?")
        print(f"Initial target state: {initial.decode('ascii', errors='replace')}")
        boot_precision = read_uint(client, args.precision_address, 1)
        print(f"Pre-init precision_set: {boot_precision}")

        validate_stop(
            client.continue_then_interrupt(args.warmup_seconds),
            "H-SAMPLE initialization warmup stop",
        )

        initial_precision = read_uint(client, args.precision_address, 1)
        print(f"Initialized precision_set: {initial_precision}")
        if args.force_precision is not None:
            client.write_memory(args.precision_address, bytes([args.force_precision]))
            forced = read_uint(client, args.precision_address, 1)
            if forced != args.force_precision:
                raise RuntimeError(
                    f"precision patch failed after init: expected {args.force_precision}, got {forced}"
                )
            print(f"Forced precision_set={forced} after runtime initialization")
            validate_stop(
                client.continue_then_interrupt(args.warmup_seconds),
                "H-SAMPLE forced-precision settle stop",
            )

        queue_table = client.read_memory(args.sect_queues_address, 8, 8)
        queue_bases = [
            int.from_bytes(queue_table[0:4], "big"),
            int.from_bytes(queue_table[4:8], "big"),
        ]
        section_ptr = read_uint(client, args.section_ptr_address, 4)
        current_index = None
        for index, base in enumerate(queue_bases):
            if base <= section_ptr < base + SECTION_QUEUE_SIZE:
                current_index = index
                break
        if current_index is None:
            raise RuntimeError(
                f"section_ptr 0x{section_ptr:08X} is outside queue ranges "
                + ", ".join(f"0x{base:08X}" for base in queue_bases)
            )
        completed_index = 1 - current_index
        completed_base = queue_bases[completed_index]
        queue = client.read_memory(completed_base, SECTION_QUEUE_SIZE, 0x400)
        probe = client.read_memory(args.probe_address, PROBE_SIZE, 0x100)

        result = {
            "queue_bases": queue_bases,
            "section_ptr": section_ptr,
            "current_queue_index": current_index,
            "completed_queue_index": completed_index,
            "completed_queue_base": completed_base,
            "queue_id": read_uint(client, args.queue_id_address, 1),
            "boot_precision_set": boot_precision,
            "initial_precision_set": initial_precision,
            "forced_precision_set": args.force_precision,
            "precision_set": read_uint(client, args.precision_address, 1),
            "cur_line": read_uint(client, args.cur_line_address, 2),
            "live_wh0": read_uint(client, args.whx_address, 1),
            "cooldown": read_uint(client, args.cooldown_address, 1),
            "sect_status": read_uint(client, args.sect_status_address, 2),
            "frame_counter": read_uint(client, args.frame_counter_address, 1),
            "probe_bytes": list(probe),
            "records": parse_records(queue),
        }

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            f"Captured completed queue {completed_index} at 0x{completed_base:08X}: "
            f"{len(result['records'])} records; frame_counter={result['frame_counter']} "
            f"cur_line={result['cur_line']} precision={result['precision_set']}"
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
