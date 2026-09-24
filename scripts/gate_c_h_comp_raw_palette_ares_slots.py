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
FRAME_COUNT=0x800686A9
FPS_EMULATE=0x800686A5
SKIP_EMULATE=0x800686A8
CUR_LINE=0x800B75FA
QUEUE_ID=0x800B7600
BG_MODE=0x800B767D
WRAM0=0x80071000
SP_STATUS=0xA4040010
SP_PC=0xA4080000
SP_DMA_FULL=0xA4040014
SP_DMA_BUSY=0xA4040018

def read_reg_u64(c:RSPClient,index_hex:str)->int:
    reply=c.request(f"p{index_hex}")
    if len(reply)==3 and reply.startswith(b"E"):
        raise RuntimeError(f"target rejected register p{index_hex}: {reply!r}")
    try:
        return int(reply.decode("ascii"),16)
    except ValueError as exc:
        raise RuntimeError(f"invalid register p{index_hex} reply: {reply!r}") from exc

def snapshot(c:RSPClient,out:Path,label:str)->dict[str,object]:
    m0=c.read_memory(M0,48,48)
    m4=c.read_memory(M4,48,48)
    q1=c.read_memory(RAW0,40,40)
    q2=c.read_memory(RAW4,40,40)
    (out/f"{label}-rsp-slot0.bin").write_bytes(m0)
    (out/f"{label}-rsp-slot4.bin").write_bytes(m4)
    (out/f"{label}-raw-q1.bin").write_bytes(q1)
    (out/f"{label}-raw-q2.bin").write_bytes(q2)
    state={
        "r4300_pc":f"0x{read_reg_u64(c,'25'):016X}",
        "sp_status":f"0x{int.from_bytes(c.read_memory(SP_STATUS,4,4),'big'):08X}",
        "sp_pc":f"0x{int.from_bytes(c.read_memory(SP_PC,4,4),'big'):08X}",
        "sp_dma_full":int.from_bytes(c.read_memory(SP_DMA_FULL,4,4),"big"),
        "sp_dma_busy":int.from_bytes(c.read_memory(SP_DMA_BUSY,4,4),"big"),
        "frame_count":c.read_memory(FRAME_COUNT,1,1)[0],
        "fps_emulate":c.read_memory(FPS_EMULATE,1,1)[0],
        "skip_emulate":c.read_memory(SKIP_EMULATE,1,1)[0],
        "cur_line":int.from_bytes(c.read_memory(CUR_LINE,2,2),"big"),
        "queue_id":c.read_memory(QUEUE_ID,1,1)[0],
        "bg_mode":c.read_memory(BG_MODE,1,1)[0],
        "guest_phase_wram0":c.read_memory(WRAM0,1,1)[0],
        "slot0_changed":any(m0),
        "slot4_changed":any(m4),
        "q1_nonzero":any(q1),
        "q2_nonzero":any(q2),
    }
    (out/f"{label}-state.json").write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    print(f"{label} state: {json.dumps(state,sort_keys=True)}")
    return {"state":state,"m0":m0,"m4":m4,"q1":q1,"q2":q2}


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

        stop5,events5=run_for_then_query_stop(c,5.0)
        validate_stop(stop5,"5s diagnostic stop")
        snap5=snapshot(c,out,"t5")

        stop20,events15=run_for_then_query_stop(c,15.0)
        validate_stop(stop20,"20s diagnostic stop")
        snap20=snapshot(c,out,"t20")
        (out/"run-window.json").write_text(json.dumps({
            "windows":[
                {"requested_seconds":5.0,"early_stops":events5},
                {"requested_seconds":15.0,"early_stops":events15},
            ],
            "total_requested_seconds":20.0,
        },indent=2)+"\n",encoding="utf-8")

        data0=snap20["m0"]; data4=snap20["m4"]
        raw0=snap20["q1"]; raw4=snap20["q2"]
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
