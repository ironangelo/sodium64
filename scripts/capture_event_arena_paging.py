#!/usr/bin/env python3
"""Read-only capture of the original paging guest and reserved queue tail."""
import argparse
import hashlib
import json
from pathlib import Path
from capture_stage2_publication import load_symbols
from capture_gate_c_stage1_ares import set_breakpoint
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--elf', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    syms = load_symbols(args.elf)
    c = connect_with_retry('127.0.0.1', args.port, 30, 240)
    try:
        c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS) == b'OK'
        set_breakpoint(c, syms['tlbl_rom'], True)
        validate_stop(c.request('c'), 'first natural ROM page miss')
        before = c.read_memory(0xa03e8100, 0x17f00, 0x400)
        (args.output/'reserved-tail-before.bin').write_bytes(before)
        set_breakpoint(c, syms['tlbl_rom'], False)
        status = 0
        for _ in range(20):
            validate_stop(c.continue_then_interrupt(2), 'original paging guest')
            raw = c.read_memory((syms['wram']|0x20000000)+0x1000, 4, 4)
            status = int.from_bytes(raw[:2], 'little')
            if status in (0xc0de, 0xbad0):
                break
        assert status == 0xc0de, (hex(status), raw.hex())
        after = c.read_memory(0xa03e8100, 0x17f00, 0x400)
        (args.output/'reserved-tail-after.bin').write_bytes(after)
        assert after == before, 'ROM DMA crossed into reserved Q2 tail'
        ptr = int.from_bytes(c.read_memory(syms['rom_pointer']|0x20000000, 1, 1), 'big')
        assert ptr < 244, ptr
        result = dict(passed=True, guest_status=hex(status), rom_bytes=0x400000,
                      checked_reads=640, unique_pages=512, resident_slots=244,
                      rom_pointer=ptr, reserved_tail_bytes=len(before),
                      reserved_tail_sha256=hashlib.sha256(before).hexdigest(),
                      memory_seeded=False, cadence_authority=False)
        (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
    finally:
        c.close()


if __name__ == '__main__':
    main()
