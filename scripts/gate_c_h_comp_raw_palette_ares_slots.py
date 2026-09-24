#!/usr/bin/env python3
"""Capture both raw-palette RSP frame-slot records from pinned ares."""
from __future__ import annotations
import argparse
import socket
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gdb_rsp_dump import RSPClient, connect_with_retry, validate_stop, ARES_N64_GUEST_SIGNALS

M0=0xA00F0040
M4=0xA00F0080
RAW0=0xA00EF000
RAW4=0xA00EF800

def continue_then_query_stop(c:RSPClient,seconds:float)->bytes:
    """Run for up to seconds, then use pinned ares' synchronous '?' halt."""
    c._send_packet_bytes(b"c")
    previous_timeout=c.sock.gettimeout()
    try:
        c.sock.settimeout(seconds)
        try:
            return c._read_packet()
        except socket.timeout:
            c.sock.settimeout(previous_timeout)
            return c.request("?")
    finally:
        c.sock.settimeout(previous_timeout)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",type=int,default=9149)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    out=args.output_dir; out.mkdir(parents=True,exist_ok=True)
    c=connect_with_retry("127.0.0.1",args.port,30.0,30.0)
    try:
        # AwaitGDBClient resumes ares immediately when the TCP client connects.
        # Re-establish a synchronous stopped state with the supported '?' packet.
        validate_stop(c.request("?"),"Initial observation stop")
        supported=c.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        if b"QPassSignals+" not in supported: raise RuntimeError("QPassSignals unsupported")
        if c.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}")!=b"OK": raise RuntimeError("QPassSignals rejected")

        # Read-only proof: debugger writes are LAB-LIMITED on this pinned ares.
        # Preserve each fresh-process mailbox baseline and require runtime change.
        base0=c.read_memory(M0,48,48); base4=c.read_memory(M4,48,48)
        (out/"baseline-slot0.bin").write_bytes(base0)
        (out/"baseline-slot4.bin").write_bytes(base4)
        print(f"Baseline slot0: {base0.hex()}")
        print(f"Baseline slot4: {base4.hex()}")

        validate_stop(continue_then_query_stop(c,5.0),"Both-slot proof stop")
        data0=c.read_memory(M0,48,48); data4=c.read_memory(M4,48,48)
        if data0==base0:
            raise RuntimeError("slot0 mailbox did not change from baseline")
        if data4==base4:
            raise RuntimeError("slot4 mailbox did not change from baseline")
        (out/"rsp-slot0.bin").write_bytes(data0)
        (out/"rsp-slot4.bin").write_bytes(data4)
        (out/"raw-q1.bin").write_bytes(c.read_memory(RAW0,40,40))
        (out/"raw-q2.bin").write_bytes(c.read_memory(RAW4,40,40))
        try: c.request("D")
        except Exception: pass
    finally: c.close()
    return 0
if __name__=="__main__": raise SystemExit(main())
