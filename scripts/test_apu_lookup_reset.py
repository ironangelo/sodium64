#!/usr/bin/env python3
"""Execute the linked reset and require complete invalidation with exact bounds."""
import argparse
from linked_cpu_regression import CPU, load_elf


def check(memory, symbols):
    cpu = CPU(memory.copy())
    start, end = symbols['jit_lookup'], symbols['jit_pointer']
    assert start % 8 == end % 8 == 0 and end-start == 0x40000
    lo, hi = start & 0x1fffffff, end & 0x1fffffff
    # Every pointer, including stale or never-replayed entries, starts nonzero.
    # Both sentinels include adjacent live metadata, not just unused padding.
    cpu.memory.update((lo-32+i, 0xa5) for i in range(hi-lo+64))
    cpu.pattern()
    before = cpu.regs.copy()
    cp, product = cpu.cp.copy(), (cpu.hi, cpu.lo)
    cpu.execute(symbols['reset_buffer'], stop=symbols['compile_block'])
    assert cpu.blob(start, hi-lo) == bytes(hi-lo), 'lookup entry survived reset'
    assert cpu.blob(start-32, 32) == bytes([0xa5])*32, 'leading owner overwritten'
    assert cpu.blob(end+4, 28) == bytes([0xa5])*28, 'trailing owner overwritten'
    assert cpu.read(end) == 0xa01c0000, 'JIT pointer was not reset'
    assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1, 8, 9))
    assert (cpu.hi, cpu.lo) == product and cpu.cp == cp and not cpu.cp_writes
    coverage = set()
    for address, width, value in cpu.memory_writes:
        assert value == 0 or address == hi, 'nonzero lookup publication during reset'
        assert lo <= address and address+width <= hi+4, 'write escaped lookup/pointer owner'
        if address < hi:
            assert not coverage.intersection(range(address, address+width)), 'duplicate clear'
            coverage.update(range(address, address+width))
    assert len(coverage) == 0x40000, 'incomplete lookup invalidation'
    return cpu.steps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    steps = check(memory, symbols)
    # Real emitted-code faults: omit a store, omit the delay-slot store, or
    # stop one batch early. All must fail independently of the positive run.
    begin, end = symbols['reset_loop'], symbols['compile_block']
    words = [(pc, int.from_bytes(bytes(memory.get((pc+i) & 0x1fffffff, 0) for i in range(4)), 'big'))
             for pc in range(begin, begin+80, 4)]
    stores = [(pc, word) for pc, word in words if word >> 26 == 63]
    assert len(stores) == 8, 'expected eight linked SD stores'
    mutants = [(stores[0][0], 0), (stores[-1][0], 0)]
    for pc, word in words:
        if word >> 26 in (8, 9) and (word >> 16 & 31) == 8 and (word & 65535) == 64:
            mutants.append((pc, (word & ~65535) | 128))
    assert len(mutants) == 3
    for pc, replacement in mutants:
        bad = memory.copy()
        for i, byte in enumerate(replacement.to_bytes(4, 'big')):
            bad[(pc+i) & 0x1fffffff] = byte
        try:
            check(bad, symbols)
        except AssertionError:
            continue
        raise AssertionError('reset fault accepted')
    print(f'APU_LOOKUP_RESET PASS entries=65536 bytes=262144 faults=3 instructions={steps}; no N64 timing claim')


if __name__ == '__main__':
    main()
