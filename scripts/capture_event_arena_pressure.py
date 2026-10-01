#!/usr/bin/env python3
"""Read real high-count producer streams in both slots; never seed runtime state."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capture_stage2_publication import load_symbols
from capture_gate_c_stage1_ares import set_breakpoint, require_fenced_boundary
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop
from test_gate_c_cgram_rsp_consumer_clean_contract import rgb555_to_rgba5551


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--elf', type=Path, required=True)
    ap.add_argument('--guest', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rom = args.guest.read_bytes()
    expected = [rgb555_to_rgba5551(int.from_bytes(rom[i:i+2], 'little') & 0x7fff)
                for i in range(0, 32768, 2)]
    syms = load_symbols(args.elf)
    c = connect_with_retry('127.0.0.1', args.port, 30, 240)
    results = {}
    consumed = {}
    observations = []
    previous = None
    stop = syms['frame_wait']+0x14
    try:
        c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS) == b'OK'
        set_breakpoint(c, stop, True)
        validate_stop(c.request('c'), 'first natural pressure prelaunch')
        for attempt in range(24):
            engine = require_fenced_boundary(c, stage=f'pressure prelaunch {attempt}')
            if previous is not None:
                name, raw_base = previous
                raw = c.read_memory(raw_base, 0x800, 0x400)
                want = b''.join(struct.pack('>H', value)*4 for value in expected[-256:])
                assert raw == want, ('RSP final raw palette', name)
                (args.output/(name+'-consumed-raw.bin')).write_bytes(raw)
                consumed[name] = dict(passed=True, raw_base=hex(raw_base),
                                      sha256=hashlib.sha256(raw).hexdigest(), engine=engine)
                previous = None
            if len(results) == 2 and len(consumed) == 2:
                break
            count = int.from_bytes(c.read_memory(syms['hcomp_cgram_event_count']|0x20000000, 2, 2), 'big')
            observation = dict(attempt=attempt, count=count,
                guest_bursts=int.from_bytes(c.read_memory(syms['wram']+0x1010, 1, 1), 'big'))
            observations.append(observation)
            (args.output/'observations.json').write_text(json.dumps(observations, indent=2)+'\n')
            print(json.dumps(observation), flush=True)
            if count < 16384:
                set_breakpoint(c, stop+4, True)
                set_breakpoint(c, stop, False)
                validate_stop(c.request('c'), 'pre-jr pressure handoff')
                set_breakpoint(c, stop, True)
                set_breakpoint(c, stop+4, False)
                validate_stop(c.request('c'), 'next pressure prelaunch')
                continue
            assert count <= 0x6000, count
            pointer = int.from_bytes(c.read_memory(syms['hcomp_cgram_event_ptr']|0x20000000, 4, 4), 'big')
            base = pointer-count*4
            assert base in (0xa00c2e00, 0xa03e8000), hex(base)
            data = c.read_memory(base, count*4, 0x400)
            records = struct.unpack('>'+str(count)+'I', data)
            colors = [v for v in records if not (v & 0x8000)]
            assert len(colors) == 16384, (hex(base), count, len(colors))
            for i, (value, want) in enumerate(zip(colors, expected)):
                assert value == ((want<<16) | ((i%256)*8)), (hex(base), i, hex(value), hex(want))
            assert all((v & 0xffff) == 0x8000 for v in records if v & 0x8000)
            # Adjacent lower-Q1 gap was naturally zeroed at boot and has no owner.
            assert c.read_memory(0xa00dae00, 0x100, 0x100) == bytes(0x100)
            name = 'q1' if base == 0xa00c2e00 else 'q2'
            (args.output/(name+'-stream.bin')).write_bytes(data)
            results[name] = dict(base=hex(base), records=count, color_records=len(colors),
                                 section_markers=count-len(colors), sha256=hashlib.sha256(data).hexdigest())
            previous = (name, 0xa00ef000 if name == 'q1' else 0xa00ef800)
            set_breakpoint(c, stop+4, True)
            set_breakpoint(c, stop, False)
            validate_stop(c.request('c'), 'pre-jr pressure handoff')
            set_breakpoint(c, stop, True)
            set_breakpoint(c, stop+4, False)
            validate_stop(c.request('c'), 'next pressure prelaunch')
        assert len(results) == 2 and len(consumed) == 2, (results, consumed)
        result = dict(passed=True, queues=results, consumed=consumed, memory_seeded=False,
                      guest_state_written=False, cadence_authority=False,
                      expectation='exact original DMA data, 16384 colors per handed frame')
        (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
    finally:
        c.close()


if __name__ == '__main__':
    main()
