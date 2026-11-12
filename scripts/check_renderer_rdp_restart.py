#!/usr/bin/env python3
"""Check the linked faithful renderer sender after the diagnostic RDP drain."""
import argparse
from pathlib import Path
import sys


DP_START, DP_END, DP_CURRENT, DP_STATUS = 8, 9, 10, 11


def run_sender(cpu, entry):
    start, end = 0x180, 0x1A0
    # A previous submission can have the same END as the new one.
    samples = ((0x600, end), (0, end - 8), (0, end))
    status_reads = []
    current_reads = []
    writes = [(DP_START, start), (DP_END, end)]

    def status(_steps):
        assert cpu.cp_writes == writes, 'poll before fresh START and END'
        index = len(status_reads)
        assert index < len(samples), 'sender failed to retire the new list'
        status_reads.append(index)
        return samples[index][0]

    def current(_steps):
        assert cpu.cp_writes == writes and status_reads, 'CURRENT before fresh submission'
        index = status_reads[-1]
        current_reads.append(index)
        return samples[index][1]

    cpu.pattern()
    cpu.regs[4], cpu.regs[5] = start, end
    cpu.cp[DP_STATUS], cpu.cp[DP_CURRENT] = status, current
    assert cpu.execute(entry, max_steps=80) == 'return'
    assert status_reads == current_reads == [0, 1, 2], 'returned before the new list was fetched'
    assert cpu.cp_writes == writes and not cpu.memory_writes


def check_bank(path, cpu_class, load_elf):
    memory, symbols = load_elf(path)
    entry, emitter, wait = (symbols[name] for name in ('rdp_send', 'rdp_emit_owned', 'rdp_fetch_wait'))
    assert entry == 0xA4001F5C
    cpu = cpu_class(memory)
    pointer_reads = []
    for pc in range(0xA4001000, 0xA4002000, 4):
        word = cpu.read(pc)
        if word >> 21 == (16 << 5) and ((word >> 11) & 31) in (DP_START, DP_END, DP_CURRENT):
            pointer_reads.append(pc)
    assert pointer_reads == [wait + 12], 'unaccounted RDP pointer read'
    run_sender(cpu, entry)

    mutants = (emitter + 4, emitter + 8, wait + 8, wait + 16)
    for address in mutants:
        faulty = cpu_class(memory.copy())
        faulty.allow_rcp_writes = True
        faulty.write(address, 0)
        faulty.memory_writes.clear()
        try:
            run_sender(faulty, entry)
        except AssertionError:
            continue
        raise AssertionError(f'RDP restart mutation at {address:#x} escaped')
    print(f'{path.parent.parent.parent.name}/{path.name}: fresh submission and retirement pass, {len(mutants)} faults rejected')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('banks', type=Path, nargs='+')
    args = parser.parse_args()
    sys.path.insert(0, str((args.repo / 'scripts').resolve()))
    from linked_cpu_regression import CPU, load_elf

    for bank in args.banks:
        check_bank(bank, CPU, load_elf)


if __name__ == '__main__':
    main()
