#!/usr/bin/env python3
"""Read all 256 original guest phases at natural completed-frame boundaries.

No buffer seeds, guest writes or CPU single steps. Per-frame read stops are
semantic coverage evidence only; uninterrupted profiler runs measure cadence.
"""
import argparse
import hashlib
import json
import re
import socket
from pathlib import Path
from capture_stage2_publication import load_symbols, classify_frame
from capture_gate_c_stage1_ares import (FRAMEBUFFER_ADDRS, read_u, set_breakpoint,
                                      require_fenced_boundary)
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop

VULNERABLE = {p for start in (16, 32, 144, 160) for p in range(start, start+4)}


def memory_chunk(supported):
    # Memory replies use two hex characters per byte. Stay below the server's
    # advertised packet size and retain the established 1KB fallback.
    match = re.search(rb'(?:^|;)PacketSize=([0-9a-fA-F]+)(?:;|$)', supported)
    if not match:
        return 0x400
    maximum = (int(match[1], 16)-16)//2
    if maximum < 1:
        raise ValueError('invalid advertised GDB packet size')
    return min(0x4000, maximum)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--elf', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    syms = load_symbols(args.elf)
    stop = syms['frame_wait']+0x14
    args.output.mkdir(parents=True, exist_ok=True)
    records = {}
    c = connect_with_retry('127.0.0.1', args.port, 30, 120)
    try:
        c.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        supported = c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        chunk = memory_chunk(supported)
        print('GDB framebuffer read chunk:', chunk, flush=True)
        c.request('?')
        assert b'QPassSignals+' in supported
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS) == b'OK'
        set_breakpoint(c, stop, True)
        validate_stop(c.request('c'), 'first natural prelaunch')
        for attempt in range(300):
            engine = require_fenced_boundary(c, stage=f'frame {attempt}')
            origin = read_u(c, 0xa4400004, 4) & 0xffffff
            address = origin | 0xa0000000
            if address in FRAMEBUFFER_ADDRS:
                image = c.read_memory(address, 280*240*2, chunk)
                result = classify_frame(image)
                if result['band']['passed']:
                    phase = result['band']['phases'][0]
                    assert result['passed'], (phase, result)
                    if phase not in records:
                        result.update(phase=phase, vi_origin=hex(origin), engine=engine,
                                      guest_counter=read_u(c, syms['wram'], 1),
                                      sha256=hashlib.sha256(image).hexdigest())
                        records[phase] = result
                        if phase in VULNERABLE or phase in (0, 64, 128, 255):
                            (args.output/f'phase-{phase:03d}.bin').write_bytes(image)
                        if len(records) % 32 == 0:
                            print('qualified phases:', len(records), flush=True)
            if len(records) == 256:
                break
            # Leave the breakpoint through the same audited inert LUI / JR
            # handoff used by the original Stage1 capture. No single stepping.
            set_breakpoint(c, stop+4, True)
            set_breakpoint(c, stop, False)
            validate_stop(c.request('c'), 'pre-jr handoff')
            require_fenced_boundary(c, stage='pre-jr')
            set_breakpoint(c, stop, True)
            set_breakpoint(c, stop+4, False)
            validate_stop(c.request('c'), 'next natural prelaunch')
        assert len(records) == 256, sorted(records)
        result = dict(passed=True, phases=256, lower_pixels_per_phase=216*256,
                      vulnerable_phases=sorted(VULNERABLE),
                      framebuffer_seeding=False, guest_state_writes=False,
                      per_frame_breakpoints=True, cadence_authority=False,
                      memory_read_chunk=chunk,
                      records=[records[p] for p in range(256)])
        (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print('STAGE2_ALL_PHASE_LOWER_FRAME PASS')
    finally:
        c.close()


if __name__ == '__main__':
    main()
