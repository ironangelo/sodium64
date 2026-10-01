#!/usr/bin/env python3
"""Validate real typed streams and consumed palettes at natural RSP handoffs."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capture_stage2_publication import load_symbols
from capture_stage2_rows import memory_chunk
from capture_gate_c_stage1_ares import set_breakpoint, require_fenced_boundary
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop
from test_gate_c_cgram_rsp_consumer_clean_contract import rgb555_to_rgba5551

BASES = {0xa00c2e00: ('q1', 0xa00ef000), 0xa03e8000: ('q2', 0xa00ef800)}
CAPACITY = 0x6000
DMA_BYTES = 32768


def advance(c, stop):
    # Established inert LUI/JR handoff; no CPU single stepping or state writes.
    set_breakpoint(c, stop+4, True)
    set_breakpoint(c, stop, False)
    validate_stop(c.request('c'), 'pre-jr pressure handoff')
    set_breakpoint(c, stop, True)
    set_breakpoint(c, stop+4, False)
    validate_stop(c.request('c'), 'next natural pressure prelaunch')


def decode_stream(data, expected):
    """A complete exact DMA sequence followed by its genuine section marker.

    Stop at that delimiter; trailing reserved bytes are never valid records.
    Scalars in CPU-cached .data cannot bound an uncached debugger RAM read.
    The slot itself is uncached and the real DMEM cursor publishes its owner.
    """
    records = struct.unpack('>'+str(len(data)//4)+'I', data)
    first = next((v for v in records[:8] if not (v & 0x8000)), None)
    if first != expected[0]<<16:
        return None  # Initial prelaunch before the guest has produced a burst.
    color_count = 0
    markers = 0
    for i, value in enumerate(records):
        if value & 0x8000:
            assert (value & 0xffff) == 0x8000, (i, hex(value))
            markers += 1
            if color_count == len(expected):
                return i+1, color_count, markers
            continue
        assert color_count < len(expected), (i, 'missing post-DMA marker')
        want = (expected[color_count]<<16) | ((color_count%256)*8)
        assert value == want, (i, color_count, hex(value), hex(want))
        color_count += 1
    raise AssertionError(('incomplete typed stream', color_count, markers))


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
                for i in range(0, DMA_BYTES, 2)]
    syms = load_symbols(args.elf)
    c = connect_with_retry('127.0.0.1', args.port, 30, 240)
    results, consumed, observations = {}, {}, []
    previous = None
    stop = syms['frame_wait']+0x14
    try:
        supported = c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        chunk = memory_chunk(supported)
        c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS) == b'OK'
        set_breakpoint(c, stop, True)
        validate_stop(c.request('c'), 'first natural pressure prelaunch')
        for attempt in range(12):
            engine = require_fenced_boundary(c, stage=f'pressure prelaunch {attempt}')
            if previous is not None:
                name, raw_base = previous
                raw = c.read_memory(raw_base, 0x800, chunk)
                want = b''.join(struct.pack('>H', value)*4 for value in expected[-256:])
                assert raw == want, ('RSP final raw palette', name)
                (args.output/(name+'-consumed-raw.bin')).write_bytes(raw)
                consumed[name] = dict(passed=True, raw_base=hex(raw_base),
                                      sha256=hashlib.sha256(raw).hexdigest(), engine=engine)
                previous = None
            if len(results) == 2 and len(consumed) == 2:
                break
            # The CPU has already published this real stream base into DMEM,
            # but has not unhalted the RSP. Read hardware publication, not a
            # stale uncached alias of CPU-private cached producer metadata.
            base = int.from_bytes(c.read_memory(0xa4000ea0, 4, 4), 'big')
            assert base in BASES, hex(base)
            data = c.read_memory(base, CAPACITY*4, chunk)
            decoded = decode_stream(data, expected)
            ram_count = int.from_bytes(c.read_memory(syms['hcomp_cgram_event_count']|0x20000000, 2, 2), 'big')
            observation = dict(attempt=attempt, published_base=hex(base),
                               uncached_counter_copy=ram_count, burst_present=decoded is not None)
            observations.append(observation)
            (args.output/'observations.json').write_text(json.dumps(observations, indent=2)+'\n')
            print(json.dumps(observation), flush=True)
            if decoded is not None:
                count, colors, markers = decoded
                assert count <= CAPACITY and colors == 16384
                assert c.read_memory(0xa00dae00, 0x100, 0x100) == bytes(0x100)
                name, raw_base = BASES[base]
                stream = data[:count*4]
                (args.output/(name+'-stream.bin')).write_bytes(stream)
                results[name] = dict(base=hex(base), records=count, color_records=colors,
                    section_markers=markers, sha256=hashlib.sha256(stream).hexdigest(),
                    uncached_counter_copy=ram_count,
                    extent_authority='bounded exact typed DMA prefix and following section delimiter')
                previous = (name, raw_base)
            advance(c, stop)
        assert len(results) == 2 and len(consumed) == 2, (results, consumed)
        result = dict(passed=True, queues=results, consumed=consumed,
            memory_seeded=False, guest_state_written=False, cadence_authority=False,
            expectation='exact original DMA data, 16384 colors per handed frame',
            producer_counter_ram_copy_is_not_an_extent_authority=True)
        (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
    finally:
        c.close()


if __name__ == '__main__':
    main()
