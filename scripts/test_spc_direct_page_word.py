#!/usr/bin/env python3
"""Execute SPC700 word instructions through the linked JIT and its bus helpers."""
import argparse
from dataclasses import dataclass

from linked_cpu_regression import CPU, load_elf

PC = 0x400
JIT_START = 0xa01c0000
START_DEBT = 1_000_000
WORD_OPS = (
    ('movw_load', 0xba, 5), ('movw_store', 0xda, 5),
    ('addw', 0x7a, 5), ('subw', 0x9a, 5), ('cmpw', 0x5a, 4),
    ('incw', 0x3a, 6), ('decw', 0x1a, 6),
)


@dataclass(frozen=True)
class Case:
    name: str
    opcode: int
    cycles: int
    flags: int
    offset: int
    ya: int
    value: int
    dsp_alias: bool = False


def nz(result):
    return (0x80 if result & 0x8000 else 0) | (2 if result == 0 else 0)


def model(case, low, high):
    ya, value, flags = case.ya, case.value, case.flags
    output = {}
    read_low, read_high = ('r', low), ('r', high)
    bus = [read_low, read_high]
    if case.name == 'movw_store':
        output = {low: ya & 0xff, high: ya >> 8}
        bus = [read_low, ('w', low, output[low]), ('w', high, output[high])]
    elif case.name == 'movw_load':
        ya = value
        flags = (flags & ~0x82) | nz(ya)
    elif case.name in ('incw', 'decw'):
        adjust = 1 if case.name == 'incw' else -1
        result = (value + adjust) & 0xffff
        output = {low: result & 0xff, high: result >> 8}
        bus = [read_low, ('w', low, output[low]), read_high, ('w', high, output[high])]
        flags = (flags & ~0x82) | nz(result)
    else:
        adding = case.name == 'addw'
        result = (ya + value if adding else ya - value) & 0xffff
        carry = ya + value > 0xffff if adding else ya >= value
        if case.name == 'cmpw':
            flags = (flags & ~0x83) | nz(result) | int(carry)
        else:
            half = (ya & 0xfff) + (value & 0xfff) > 0xfff if adding else (
                (ya & 0xfff) >= (value & 0xfff))
            same_input_sign = not ((ya ^ value) & 0x8000)
            overflow = (same_input_sign == adding) and bool((ya ^ result) & 0x8000)
            flags = (flags & ~0xcb) | nz(result) | int(carry) | (int(half) << 3) | (int(overflow) << 6)
            ya = result
    return bus, output, ya, flags


def check(cpu, symbols, case, clock, mutation=None):
    s = symbols
    lookup = s['jit_lookup'] + 4 * PC
    page = (case.flags & 0x20) << 3
    low, high = page + case.offset, page + ((case.offset + 1) & 0xff)
    alias = page + 0x100
    timer_output = low == 0xff
    bus, writes, ya, flags = model(case, low, high)
    cpu.write(s['jit_pointer'], JIT_START)
    cpu.write(lookup, 0)
    cpu.write(s['apu_clock'], clock, 1)
    for index, byte in enumerate((case.opcode, case.offset, 0x2f, 0xfc)):
        cpu.write(s['apu_ram'] + PC + index, byte, 1)
    events = []

    def observe(kind):
        address = s['apu_read8' if kind == 'r' else 'apu_write8']

        def hook(machine):
            target = machine.regs[4] & 0xffff
            event = (kind, target)
            if kind == 'w':
                event += (machine.regs[5] & 0xff,)
            events.append(event)
            machine.before_instruction[address] = hook

        return hook

    for kind, helper in [('r', 'apu_read8'), ('w', 'apu_write8')]:
        cpu.before_instruction[s[helper]] = observe(kind)

    def execute():
        events.clear()
        original_low = 0xad if timer_output or case.dsp_alias else case.value & 0xff
        original_high = 0xbe if case.dsp_alias else case.value >> 8
        for address, byte in ((alias, 0x69), (low, original_low), (high, original_high)):
            cpu.write(s['apu_ram'] + address, byte, 1)
        if timer_output:
            cpu.write(s['apu_tmouts'] + 2, case.value & 0xff, 1)
            cpu.write(s['apu_ocycles'] + 8, 0x80000000)
        if case.dsp_alias:
            cpu.write(s['dsp_addr'], case.value & 0xff, 1)
            cpu.write(s['dsp_regs'] + 0x1e, 0x87, 1)
            cpu.write(s['dsp_regs'] + 0x1f, case.value >> 8, 1)
        for key, byte in {
            'apu_accum': case.ya & 0xff, 'apu_reg_y': case.ya >> 8, 'apu_flags': case.flags,
            'apu_reg_x': 0x96, 'apu_stack': 0x8f, 'apu_halt': 0,
        }.items():
            cpu.write(s[key], byte, 1)
        cpu.write(s['apu_count'], PC, 2)
        cpu.regs[19], cpu.regs[7] = START_DEBT, 0
        cpu.execute(s['apu_execute'], stop=s['cpu_execute'])
        assert cpu.read(s['apu_count'], 2) == PC, 'guest PC'
        assert START_DEBT - cpu.regs[19] == (case.cycles + 4) * clock, 'cycle debit'
        assert events == bus, ('bus', events, bus)
        assert cpu.read(s['apu_accum'], 1) == ya & 0xff, 'accumulator'
        assert cpu.read(s['apu_reg_y'], 1) == ya >> 8, 'Y'
        assert cpu.read(s['apu_flags'], 1) == flags, 'flags'
        assert cpu.read(s['apu_reg_x'], 1) == 0x96 and cpu.read(s['apu_stack'], 1) == 0x8f, 'X/SP'
        assert cpu.read(s['apu_ram'] + alias, 1) == 0x69, 'next-page canary'
        assert cpu.read(s['apu_ram'] + low, 1) == writes.get(low, original_low), 'low RAM byte'
        assert cpu.read(s['apu_ram'] + high, 1) == writes.get(high, original_high), 'high RAM byte'
        if timer_output:
            assert cpu.read(s['apu_tmouts'] + 2, 1) == 0, 'timer read side effect'
        if case.dsp_alias:
            assert cpu.read(s['dsp_addr'], 1) == 0x1f, 'DSP address latch'
            assert cpu.read(s['dsp_regs'] + 0x1e, 1) == 0x87, 'old DSP register'
            assert cpu.read(s['dsp_regs'] + 0x1f, 1) == writes[high], 'new DSP register'
        return cpu.read(lookup), cpu.read(s['jit_pointer'])

    compiled = execute()
    if mutation is not None:
        code, end = (compiled[0] + 12, compiled[1] - 0x20000000)
        address = next(at for at in range(code, end, 4) if cpu.read(at) == mutation)
        cpu.write(address, 0)
    assert compiled == execute(), 'cached block was replaced'
    cpu.memory_writes.clear()
    cpu.cache_ops.clear()


def scenarios():
    for flags in (0, 0x20, 0xdf, 0xff):
        for offset in (0x23, 0xfe, 0xff):
            for name, opcode, cycles in WORD_OPS:
                for value in (0, 1, 0xff, 0x100, 0x7fff, 0x8000, 0xfffe, 0xffff):
                    if not flags & 0x20 and offset >= 0xfe:
                        continue
                    yield Case(name, opcode, cycles, flags, offset, 0x8101, value)
    for name, opcode, cycles in WORD_OPS:
        for value in (0x0000, 0x7f01, 0x800e):
            yield Case(name, opcode, cycles, 0, 0xff, 0x1234, value)
    # The low write selects a different DSP register before the high read.
    yield Case('incw', 0x3a, 6, 0, 0xf2, 0x1234, 0x361e, dsp_alias=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    parser.add_argument('--expect-unfixed', action='store_true')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    cpu = CPU(memory)
    passed = failures = 0
    for case in scenarios():
        for clock in (21, 42):
            try:
                check(cpu, symbols, case, clock)
            except AssertionError as error:
                if not args.expect_unfixed:
                    raise AssertionError((case, clock, str(error))) from error
                failures += 1
                if failures <= 8:
                    print(f'OPEN {case.name} P={bool(case.flags & 0x20)} dp={case.offset:02x}: {error}')
            else:
                passed += 1
    if args.expect_unfixed:
        assert passed and failures
    else:
        for case, word in (
            (Case('movw_load', 0xba, 5, 0x20, 0xff, 0, 0x1234), 0x308400ff),
            (Case('incw', 0x3a, 6, 0x20, 0x23, 0, 0xffff),
             0x0c000000 | ((symbols['apu_write8'] >> 2) & 0x03ffffff)),
        ):
            try:
                check(CPU(memory.copy()), symbols, case, 21, mutation=word)
            except AssertionError as error:
                assert error.args[0] == 'cycle debit' or error.args[0][0] == 'bus', error
            else:
                raise AssertionError(f'{case.name} mutation escaped')
        print('SPC_DIRECT_PAGE_WORD rejected emitted faults=2')
    print(f'SPC_DIRECT_PAGE_WORD linked cases={passed + failures} pass={passed} mismatches={failures}')


if __name__ == '__main__':
    main()
