#!/usr/bin/env python3
"""Observe a continuously running HW_PROFILE ROM before final red fill.

No framebuffer seeds, guest-state writes, CPU single steps or per-frame stops.
Capture the actual VI-selected buffer after the five measured windows.
"""
import argparse
import json
import struct
import subprocess
from pathlib import Path

from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop
from capture_gate_c_stage1_ares import read_u, read_engine_state, set_breakpoint, FRAMEBUFFER_ADDRS
from make_gate_c_stage1 import window


def load_symbols(elf):
    rows = [l.split() for l in subprocess.check_output(['nm', '-n', str(elf)], text=True).splitlines()]
    return {r[2]: int(r[0], 16) for r in rows if len(r) == 3}


def classify_band(data):
    words = struct.unpack('>4480H', data[:8960])
    rows = [list(words[y*280+12:y*280+268]) for y in range(8, 16)]
    first = rows[0]
    black = [i for i, p in enumerate(first) if p == 1]
    bounds = [min(black), max(black)] if black else None
    phases = [n for n in range(256) if list(window(n)) == bounds]
    colors = {f'0x{p:04x}': first.count(p) for p in set(first)}
    reference = [1 if bounds and bounds[0] <= x <= bounds[1] else 0x7bc1 for x in range(256)]
    passed = len(phases) == 1 and all(row == reference for row in rows)
    return dict(passed=passed, colors=colors, window=bounds, phases=phases,
                differing_pixels=sum(a != b for row in rows for a, b in zip(row, reference)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--elf', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    syms = load_symbols(args.elf)
    # Stop before finalization modifies the displayed buffer. Up to this point
    # execution, RSP work, VI publication and profiling have been uninterrupted.
    stop = syms['hw_profile_finalize']
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    c = connect_with_retry('127.0.0.1', args.port, 30, 90)
    try:
        supported = c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        c.request('?')
        if b'QPassSignals+' not in supported or c.request('QPassSignals:' + ARES_N64_GUEST_SIGNALS) != b'OK':
            raise RuntimeError('guest exception pass-through unavailable')
        set_breakpoint(c, stop, True)
        validate_stop(c.request('c'), 'uninterrupted HW_PROFILE window')
        origin = read_u(c, 0xa4400004, 4) & 0xffffff
        addr = origin | 0xa0000000
        if addr not in FRAMEBUFFER_ADDRS:
            raise RuntimeError(f'unexpected VI_ORIGIN: {origin:#x}')
        image = c.read_memory(addr, 280*240*2, 0x400)
        (out/'vi-framebuffer.bin').write_bytes(image)
        hdr = c.read_memory(syms['hw_profile_header'], 128, 128)
        words = struct.unpack('>32I', hdr)
        packet = c.read_memory(0xa00f0000, 16, 16)
        (out/'output-input.bin').write_bytes(packet)
        result = dict(vi_origin=f'0x{origin:06x}', frame_budgets=list(words[8:13]),
                      guest_counter=read_u(c, syms['wram'], 1), engine=read_engine_state(c),
                      band=classify_band(image), framebuffer_seeding=False,
                      per_frame_breakpoints=False)
        for key, size in [('dsp_pointer', 2), ('enabled', 1), ('apu_outputs', 4)]:
            result[key] = read_u(c, syms[key], size)
        for name, start, size in [('audio-pcm.bin', syms['dsp_buffer'], 8192),
                                  ('dsp-regs.bin', syms['dsp_regs'], 128),
                                  ('sub.bin', 0xa00e4000, 4480),
                                  ('provenance.bin', 0xa00e2000, 4480),
                                  ('ts-provenance.bin', 0xa00e6000, 4480)]:
            (out/name).write_bytes(c.read_memory(start, size, 0x400))
        # The loader's original static RSP source image should survive execution.
        from check_rsp_branch_delay_slots import read_text
        mode7 = read_text(args.elf.parent/'src/rsp_mode7.elf')[1]
        live = c.read_memory(syms['rsp_mode7_text_start'] | 0x20000000, len(mode7), 0x400)
        (out/'mode7-source-live.bin').write_bytes(live)
        result['mode7_source_intact'] = live == mode7
        (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
    finally:
        c.close()


if __name__ == '__main__':
    main()
