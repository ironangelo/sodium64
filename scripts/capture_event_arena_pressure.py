#!/usr/bin/env python3
"""Read real high-count producer streams in both slots; never seed runtime state."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capture_stage2_publication import load_symbols
from capture_gate_c_stage1_ares import set_breakpoint
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
    try:
        c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS) == b'OK'
        set_breakpoint(c, syms['rsp_frame'], True)
        for attempt in range(24):
            validate_stop(c.request('c'), f'natural pressure handoff {attempt}')
            count = int.from_bytes(c.read_memory(syms['hcomp_cgram_event_count']|0x20000000, 2, 2), 'big')
            if count < 16384:
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
            if len(results) == 2:
                break
        assert len(results) == 2, results
        result = dict(passed=True, queues=results, memory_seeded=False,
                      guest_state_written=False, cadence_authority=False,
                      expectation='exact original DMA data, 16384 colors per handed frame')
        (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
    finally:
        c.close()


if __name__ == '__main__':
    main()
