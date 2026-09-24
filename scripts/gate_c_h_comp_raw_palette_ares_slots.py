#!/usr/bin/env python3
"""Capture both raw-palette RSP frame-slot records from pinned ares."""
from __future__ import annotations
import argparse
import json
import socket
import time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gdb_rsp_dump import RSPClient, connect_with_retry, validate_stop, ARES_N64_GUEST_SIGNALS

M0=0xA00F0040
M4=0xA00F0080
RAW0=0xA00EF000
RAW4=0xA00EF800

def run_for_then_query_stop(c:RSPClient,seconds:float)->tuple[bytes,list[dict[str,object]]]:
    """Accumulate a real running window, resuming through any early stop packets."""
    previous_timeout=c.sock.gettimeout()
    ran=0.0
    events:list[dict[str,object]]=[]
    try:
        while ran < seconds:
            if len(events) >= 32:
                raise RuntimeError("too many early GDB stops while accumulating run window")
            remaining=seconds-ran
            c._send_packet_bytes(b"c")
            started=time.monotonic()
            c.sock.settimeout(remaining)
            try:
                reply=c._read_packet()
            except socket.timeout:
                elapsed=time.monotonic()-started
                ran+=elapsed
                print(f"Run window timeout after {elapsed:.6f}s; accumulated {ran:.6f}s")
                break

            elapsed=time.monotonic()-started
            ran+=elapsed
            text=reply.decode("ascii",errors="replace")
            events.append({"elapsed_seconds":elapsed,"accumulated_seconds":ran,"packet":text})
            print(f"Early stop #{len(events)} after {elapsed:.6f}s: {text}; accumulated {ran:.6f}s")
            validate_stop(reply,f"Early run stop #{len(events)}")

        # If the duration ended by timeout the target is still running; halt it
        # synchronously. If an early stop itself carried us over the duration,
        # the target is already stopped and that packet is the final stop.
        if ran >= seconds and events and events[-1]["accumulated_seconds"] >= seconds:
            return reply,events
        c.sock.settimeout(previous_timeout)
        return c.request("?"),events
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

        stop,events=run_for_then_query_stop(c,5.0)
        validate_stop(stop,"Both-slot proof stop")
        (out/"run-window.json").write_text(json.dumps({"requested_seconds":5.0,"early_stops":events},indent=2)+"\n",encoding="utf-8")
        data0=c.read_memory(M0,48,48); data4=c.read_memory(M4,48,48)
        raw0=c.read_memory(RAW0,40,40); raw4=c.read_memory(RAW4,40,40)
        (out/"rsp-slot0.bin").write_bytes(data0)
        (out/"rsp-slot4.bin").write_bytes(data4)
        (out/"raw-q1.bin").write_bytes(raw0)
        (out/"raw-q2.bin").write_bytes(raw4)
        print(f"Final slot0: {data0.hex()}")
        print(f"Final slot4: {data4.hex()}")
        if data0==base0:
            raise RuntimeError("slot0 mailbox did not change from baseline")
        if data4==base4:
            raise RuntimeError("slot4 mailbox did not change from baseline")
        try: c.request("D")
        except Exception: pass
    finally: c.close()
    return 0
if __name__=="__main__": raise SystemExit(main())
