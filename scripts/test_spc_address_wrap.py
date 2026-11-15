#!/usr/bin/env python3
"""Execute linked SPC compiler and generated code at the guest address boundary."""
import argparse

from linked_cpu_regression import CPU, load_elf

RAM_MASK = 0xffff
BLOCK_START = 0xa01c0000
START_DEBT = 1_000_000
REGISTERS = {'apu_flags': 0, 'apu_accum': 0x11, 'apu_reg_x': 4,
             'apu_reg_y': 6, 'apu_stack': 0x7f, 'apu_halt': 0}


def case(cpu, s, pc, code, target, cycles, *, clock=21, flags=0, initial=None,
         ram=(), expected=None, reads=(), tag_test=False):
    initial_regs = dict(REGISTERS, apu_flags=flags)
    initial_regs.update(initial or {})
    final_regs = initial_regs | (expected or {})
    final_ram = dict(ram)
    final_ram.update(final_regs.pop('ram', ()))
    source = bytes.fromhex(code)
    memory_bytes = {(pc + n) & RAM_MASK: value for n, value in enumerate(source)}
    memory_bytes.update(ram)
    end = (pc + len(source)) & RAM_MASK
    assert s['apu_ram'] + 0x10000 <= s['jit_lookup']
    cpu.write(s['apu_map'] + 0x3ff, 0, 1)
    cpu.write(s['jit_pointer'], BLOCK_START)
    lookup = s['jit_lookup'] + 4 * pc
    cpu.write(lookup, 0)
    cpu.write(s['apu_clock'], clock, 1)
    bus_reads = []

    def observe(machine):
        bus_reads.append(machine.regs[4] & 0xffffffff)
        machine.before_instruction[s['apu_read8']] = observe

    def execute():
        for address, value in memory_bytes.items():
            cpu.write(s['apu_ram'] + address, value, 1)
        for name, value in initial_regs.items():
            cpu.write(s[name], value, 1)
        cpu.write(s['apu_count'], pc, 2)
        cpu.regs[19] = START_DEBT
        cpu.regs[7] = 0
        bus_reads.clear()
        cpu.before_instruction[s['apu_read8']] = observe
        cpu.execute(s['apu_execute'], stop=s['cpu_execute'])
        assert cpu.read(s['apu_count'], 2) == target, 'incorrect guest target'
        assert START_DEBT - cpu.regs[19] == cycles * clock, 'incorrect cycle debit'
        header = cpu.read(lookup)
        assert header and cpu.read(header, 2) == (pc >> 6) * 4, 'incorrect source start tag'
        assert cpu.read(header + 2, 2) == (end >> 6) * 4, 'incorrect source end tag'
        assert bus_reads == list(reads), 'incorrect data bus addresses'
        assert {key: cpu.read(s[key], 1) for key in final_regs} == final_regs, 'changed guest registers'
        assert {at: cpu.read(s['apu_ram'] + at, 1) for at in final_ram} == final_ram, 'changed guest RAM'
        return header, cpu.read(s['jit_pointer'])

    first = execute()
    assert first == execute(), 'unchanged compiled block was not reused'
    if tag_test:
        tag = s['jit_tags'] + ((end >> 6) * 4)
        cpu.write(tag, cpu.read(tag) + 1)
        assert execute() != first, 'wrapped source page did not invalidate the JIT block'
    cpu.memory_writes.clear()
    cpu.cache_ops.clear()


def scenarios():
    yield 0xffff, '00', 0, 2, {}
    yield 0xfffe, '0000', 0, 4, {}
    yield 0xfffe, 'e835', 0, 2, {'expected': {'apu_accum': 0x35}}
    yield 0xffff, 'e835', 1, 2, {'expected': {'apu_accum': 0x35}, 'tag_test': True}
    yield 0xffff, '4f34', 0xff34, 6, {
        'expected': {'apu_stack': 0x7d, 'ram': ((0x17f, 0), (0x17e, 1))}}
    yield 0xfffe, '3f0006', 0x600, 8, {
        'expected': {'apu_stack': 0x7d, 'ram': ((0x17f, 0), (0x17e, 1))}, 'tag_test': True}
    yield 0xfffd, '3f0006', 0x600, 8, {
        'expected': {'apu_stack': 0x7d, 'ram': ((0x17f, 0), (0x17e, 0))}}
    yield 0x400, '1ffbff', 0x600, 6, {'ram': ((0xffff, 0), (0, 6)), 'reads': (0xffff, 0)}
    yield 0x400, '1f0004', 0x6234, 6, {'ram': ((0x404, 0x34), (0x405, 0x62)), 'reads': (0x404, 0x405)}
    flag_branches = ((0x10, 0x80, False), (0x30, 0x80, True), (0x50, 0x40, False),
                     (0x70, 0x40, True), (0x90, 1, False), (0xb0, 1, True),
                     (0xd0, 2, False), (0xf0, 2, True))
    for pc in (0, 0xff7f, 0xfffe, 0xffff):
        fallthrough = (pc + 2) & RAM_MASK
        for displacement in (0, 1, 0x7f, 0x80, 0xff):
            relative = displacement if displacement < 128 else displacement - 256
            target = (fallthrough + relative) & RAM_MASK
            yield pc, bytes((0x2f, displacement)).hex(), target, 4, {}
            for opcode, mask, when_set in flag_branches:
                for taken in (False, True):
                    flags = mask if taken == when_set else 0
                    yield pc, bytes((opcode, displacement)).hex(), target if taken else fallthrough, (
                        4 if taken else 2), {'flags': flags}
    for pc in (0, 0xfffd, 0xffff):
        for taken in (False, True):
            for op, name, operand, not_taken in (
                (0x13, 'bbc', 0, 5), (0x03, 'bbs', 1, 5),
                (0x2e, 'cbne', 0x12, 5), (0xde, 'cbne_x', 0x12, 6),
                (0x6e, 'dbnz_dp', 2, 5), (0xfe, 'dbnz_y', 6, 4),
            ):
                code = bytes((op, 0x3c if name == 'cbne_x' else 0x40, 0x80))
                if name == 'dbnz_y':
                    code = bytes((op, 0x80))
                fallthrough = (pc + len(code)) & RAM_MASK
                inputs = {}
                if name == 'dbnz_y':
                    inputs['initial'] = {'apu_reg_y': operand if taken else 1}
                    inputs['expected'] = {'apu_reg_y': 5 if taken else 0}
                else:
                    other = {'bbc': 1, 'bbs': 0, 'cbne': 0x11, 'cbne_x': 0x11, 'dbnz_dp': 1}[name]
                    value = operand if taken else other
                    inputs['ram'] = ((0x40, value),)
                    inputs['reads'] = (0x40,)
                    if name == 'dbnz_dp':
                        inputs['expected'] = {'ram': ((0x40, value - 1),)}
                yield pc, code.hex(), (fallthrough - 128) & RAM_MASK if taken else fallthrough, (
                    not_taken + 2 if taken else not_taken), inputs


def reject_faults(memory, s):
    # Mutate the actual linked machine words. Each test uses a case that passed
    # on the intact ELF and exercises a separate reason for masking the PC.
    faults = (
        ('jit_read8', 'jit_charge_cycles', 0x3084ffff, 0xffff, 'e835', 1, 2,
         {'expected': {'apu_accum': 0x35}}),
        ('apu_bra', 'apu_jmp', 0x314affff, 0, '2f80', 0xff82, 4, {}),
        ('apu_bne', 'apu_beq', 0x3042ffff, 0, 'd080', 0xff82, 4, {}),
    )
    for begin, end, word, pc, code, target, cycles, kwargs in faults:
        cpu = CPU(memory.copy())
        address, = (at for at in range(s[begin], s[end], 4) if cpu.read(at) == word)
        cpu.write(address, 0)
        try:
            case(cpu, s, pc, code, target, cycles, **kwargs)
        except AssertionError as error:
            assert str(error) == 'incorrect guest target', (begin, error)
        else:
            raise AssertionError(f'{begin} mutation escaped')
    return len(faults)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    parser.add_argument('--expect-unfixed', action='store_true')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    cpu = CPU(memory)
    passed = failures = 0
    for pc, code, target, cycles, kwargs in scenarios():
        for clock in (21, 42):
            try:
                case(cpu, symbols, pc, code, target, cycles, clock=clock, **kwargs)
            except AssertionError as error:
                if not args.expect_unfixed:
                    raise AssertionError((hex(pc), code, hex(target), clock, str(error))) from error
                failures += 1
                if failures <= 8:
                    print(f'OPEN PC={pc:04x} bytes={code} clock={clock}: {error}')
            else:
                passed += 1
    if args.expect_unfixed:
        assert passed and failures
    else:
        faults = reject_faults(memory, symbols)
        print(f'SPC_ADDRESS_WRAP rejected linked faults={faults}')
    print(f'SPC_ADDRESS_WRAP linked cases={passed + failures} pass={passed} mismatches={failures}')


if __name__ == '__main__':
    main()
