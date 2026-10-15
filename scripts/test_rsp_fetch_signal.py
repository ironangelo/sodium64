#!/usr/bin/env python3
"""Check the optional sender marker against delayed command ownership.

SIG0 marks sender entry through fetch retirement, including submission and
polling. It does not measure primitive execution, DMA, or an instruction PC.
Numeric mock evidence only; native raw-status events must verify usefulness.
"""
import argparse
import json
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_rsp_rdp_dmem_lifetime import DelayedDPC, execute, EXIT


class MarkedDPC(DelayedDPC):
    def __init__(self, *args):
        super().__init__(*args)
        self.spstatus = self.original_status = 0x3f95
        self.marks = []

    def write(self, reg, value):
        if reg == 4:
            assert value in (0x200, 0x400), 'changed an unrelated control bit'
            if value == 0x400:
                self.spstatus |= 128
            else:
                assert self.pos == self.end and not self.latch, 'marker cleared before fetch retirement'
                self.spstatus &= ~128
            assert self.spstatus & ~128 == self.original_status & ~128
            self.marks.append(value)
        else:
            assert self.spstatus & 128, 'unmarked command submission'
            super().write(reg, value)

    def tick(self):
        if self.pos is not None and (self.pos != self.end or self.latch):
            assert self.spstatus & 128, 'unmarked pending command reader'
        super().tick()


def case(code, latency, busy, size, mode):
    memory = bytearray(4096)
    start, end = 0xc98, 0xc98 + size
    payload = bytes((i * 17 + 3) & 255 for i in range(size))
    memory[start:end] = payload
    dpc = MarkedDPC(memory, latency, busy, mode)
    _, regs = execute(code, dpc, start, end)
    assert dpc.captured == payload and dpc.marks == [0x400, 0x200]
    assert not dpc.spstatus & 128
    assert (regs[4], regs[5], regs[31]) == (start, end, EXIT)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('elf', type=Path)
    ap.add_argument('--baseline', required=True, type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    _, code = read_text(args.elf)
    _, baseline = read_text(args.baseline)
    assert len(code) == len(baseline) == 4096
    assert all(code[i] == baseline[i] for i in range(4096)
               if not 0x2ec <= i < 0x2f8 and not 0xf60 <= i < 0xf70)
    assert code[0x2cc:0x2d0] == code[0xf5c:0xf60] == bytes(4)
    cases = 0
    for latency in (0, 1, 7, 100):
        for busy in (0, 5, 20):
            for size in (8, 16, 40, 64):
                for mode in ('continuous', 'dma-gap', 'stale-end'):
                    case(code, latency, busy, size, mode)
                    cases += 1
    broken = bytearray(code)
    broken[0x2e8:0x2ec] = bytes(4)  # Remove CURRENT==END guard.
    try:
        case(broken, 100, 0, 64, 'dma-gap')
    except AssertionError as error:
        assert 'marker cleared before fetch retirement' in str(error), str(error)
    else:
        raise AssertionError('accepted premature marker clear')
    result = dict(passed=True, cases=cases, negative_guards=1,
                  status_bits_preserved=True, frozen_entries_preserved=True,
                  scope='sender entry through command-fetch retirement',
                  hardware_timing_claim=False)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
