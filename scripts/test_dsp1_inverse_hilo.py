#!/usr/bin/env python3
"""Check linked DSP-1 inverse byte protocol, parity and VR4300 HI/LO spacing."""
import argparse

from linked_cpu_regression import CPU, load_elf
from test_dsp1_vector_hilo import OUTPUTS, transact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    parser.add_argument('--baseline', help='Earlier ELF for full layout and arithmetic comparison')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    # Reconstruct the previous schedule for the negative control and CI oracle.
    cpu = CPU(memory.copy())
    start = symbols['inverse_refine']
    words = [cpu.read(start + n*4) for n in range(5)]
    assert words == [0x00880018, 0x00004812, 0x00094bc3, 0x00085022, 0x012a0018], words
    for n, word in enumerate((words[0], words[3], words[1], words[2], words[4])):
        cpu.write(start+n*4, word)
    previous = cpu.memory
    reference, names = load_elf(args.baseline) if args.baseline else (previous, symbols)
    if args.baseline:
        assert symbols == names, 'linked symbol positions changed'
        assert memory.keys() == reference.keys(), 'allocated section layout changed'
        differences = {address for address in memory if memory[address] != reference[address]}
        assert differences, 'baseline does not contain the earlier schedule'
        allowed = {(start+n) & 0x1fffffff for n in range(4,16)}
        assert differences <= allowed, 'bytes outside reordered helper changed'
        assert reference == previous, 'baseline is not exactly the previous helper schedule'
    OUTPUTS.update({0x10: 2, 0x30: 2})
    cases = 0
    for command in (0x10, 0x30):
        for coefficient in (0, 1, -1, 123, -123, 0x2000, -0x2000,
                            0x3fff, -0x3fff, 0x4000, -0x4000,
                            0x5000, -0x5000, 0x7fff, -0x8000):
            for exponent in (-8, -1, 0, 1, 8):
                values = (coefficient, exponent)
                actual = transact(memory, symbols, command, values)
                assert actual == transact(reference, names, command, values, False), (command, values)
                cases += 1
    faults = 0
    for command in (0x10, 0x30):
        try:
            transact(reference, names, command, (0x5000, 0))
        except AssertionError as error:
            assert 'VR4300 HI/LO spacing' in str(error), error
            faults += 1
        else:
            raise AssertionError('baseline inverse hazard was accepted')
    print(f'DSP1_INVERSE_HILO PASS cases={cases} commands=2 rejected_faults={faults} layout={bool(args.baseline)}')


if __name__ == '__main__':
    main()
