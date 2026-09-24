#!/usr/bin/env python3
"""Capture both raw-palette RSP frame-slot records from pinned ares."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gdb_rsp_dump import RSPClient, connect_with_retry, validate_stop, ARES_N64_GUEST_SIGNALS

M0=0xA00F0040
M4=0xA00F0080
RAW0=0xA00EF000
RAW4=0xA00EF800

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",type=int,default=9149)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    out=args.output_dir; out.mkdir(parents=True,exist_ok=True)
    c=connect_with_retry("127.0.0.1",args.port,30.0,30.0)
    try:
        # AwaitGDBClient resumes ares immediately when the TCP client connects.
        # This pinned ares revision does not handle raw async Ctrl-C, but its
        # standard '?' packet explicitly halts the program and replies T05.
        validate_stop(c.request("?"),"Initial seed stop")
        supported=c.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        if b"QPassSignals+" not in supported: raise RuntimeError("QPassSignals unsupported")
        if c.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}")!=b"OK": raise RuntimeError("QPassSignals rejected")
        # Pinned ares has a distinct debugger write path for payloads >8 B.
        # Seed through the proven 4-byte cpu.writeDebug path, then verify all48 B.
        for off in range(0,48,4):
            c.write_memory(M0+off,bytes([0xC3])*4)
            c.write_memory(M4+off,bytes([0x3C])*4)
        seed0=c.read_memory(M0,48,48); seed4=c.read_memory(M4,48,48)
        (out/"seed-slot0.bin").write_bytes(seed0)
        (out/"seed-slot4.bin").write_bytes(seed4)
        if seed0!=bytes([0xC3])*48:
            raise RuntimeError(f"slot0 seed verification failed: {seed0.hex()}")
        if seed4!=bytes([0x3C])*48:
            raise RuntimeError(f"slot4 seed verification failed: {seed4.hex()}")
        print("Seed mailboxes verified while target stopped")
        validate_stop(c.continue_then_interrupt(5.0),"Both-slot proof stop")
        data0=c.read_memory(M0,48,48); data4=c.read_memory(M4,48,48)
        if data0==bytes([0xC3])*48 or data4==bytes([0x3C])*48:
            raise RuntimeError("one or both slot mailboxes were never written")
        (out/"rsp-slot0.bin").write_bytes(data0)
        (out/"rsp-slot4.bin").write_bytes(data4)
        (out/"raw-q1.bin").write_bytes(c.read_memory(RAW0,40,40))
        (out/"raw-q2.bin").write_bytes(c.read_memory(RAW4,40,40))
        try: c.request("D")
        except Exception: pass
    finally: c.close()
    return 0
if __name__=="__main__": raise SystemExit(main())
