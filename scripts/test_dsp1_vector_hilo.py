#!/usr/bin/env python3
"""Exercise DSP-1 vector commands through the byte ports and HI/LO guard."""
import argparse

from linked_cpu_regression import CPU, load_elf


MATRICES = ((0x4000, -0x2000, 0x1000),
            (-0x1000, 0x3000, 0x0800),
            (0x2000, 0x1000, -0x4000))
OUTPUTS = {0x04: 2, 0x24: 2, 0x0c: 2, 0x2c: 2,
           0x08: 2, 0x18: 1, 0x28: 1,
           0x0b: 1, 0x1b: 1, 0x2b: 1, 0x3b: 1}


def call(cpu, entry, value=None):
    cpu.pattern()
    if value is not None:
        cpu.regs[5] = value
    cpu.execute(entry)
    return cpu.regs[2] & 255


def transact(memory, symbols, command, parameters, enforce=True):
    cpu = CPU(memory.copy())
    cpu.enforce_hilo_spacing = enforce
    for matrix, values in zip(('matrix_a', 'matrix_b', 'matrix_c'), MATRICES):
        for row, value in enumerate(values):
            cpu.write(symbols[matrix] + row*6, value, 2)
    call(cpu, symbols['write_dsp1dr'], command)
    assert cpu.read(symbols['dsp1_sr'], 2) & 0x1400 == 0, 'command did not enter low-byte input'
    for index, word in enumerate(parameters):
        call(cpu, symbols['write_dsp1dr'], word & 255)
        assert cpu.read(symbols['dsp1_sr'], 2) & 0x1000, 'low input byte did not select high byte'
        call(cpu, symbols['write_dsp1dr'], (word >> 8) & 255)
        assert not cpu.read(symbols['dsp1_sr'], 2) & 0x1000, 'high input byte did not finish word'
        expected = parameters[:index+1]
        count = len(parameters)
        for n, value in enumerate(expected):
            assert cpu.read(symbols['input_buf'] + 2*(count-1-n), 2) == value & 65535, 'input word endian/order'
    result = []
    for _ in range(OUTPUTS[command]):
        low = call(cpu, symbols['read_dsp1dr'])
        high = call(cpu, symbols['read_dsp1dr'])
        result.append(low | (high << 8))
    assert cpu.read(symbols['dsp1_sr'], 2) & 0x400, 'command did not return to command-byte mode'
    assert cpu.read(symbols['dsp1_dr'], 2) == 0x80, 'command completion marker'
    assert not cpu.cp_writes and not cpu.cache_ops
    return result


def expected(command, values):
    if command == 0x08:
        value = 2*sum(x*x for x in values)
        return [value & 65535, value >> 16]
    if command == 0x18:
        x, y, z, radius = values
        return [((x*x+y*y+z*z-radius*radius) >> 15) & 65535]
    if command in (0x0b, 0x1b, 0x2b, 0x3b):
        matrix = MATRICES[{0x0b: 0, 0x1b: 1, 0x2b: 2, 0x3b: 0}[command]]
        return [(sum(x*y for x, y in zip(values, matrix)) >> 15) & 65535]
    if command == 0x28 and not any(values):
        return [0]
    if command in (0x04, 0x24) and values[0] == 0:
        return [0, (32767*values[1] >> 15) & 65535]
    if command in (0x0c, 0x2c) and values[0] == 0:
        return [(32767*values[1] >> 15) & 65535,
                (32767*values[2] >> 15) & 65535]
    return None


def vectors():
    for command in (0x04, 0x24):
        for angle in (0, 1, -1, 0x1000, -0x1000, 0x4000, -0x4000, 0x7fff, -0x8000):
            for radius in (0, 1, -1, 123, -456, 0x2000):
                yield command, (angle, radius)
    for command in (0x0c, 0x2c):
        for angle in (0, 1, -1, 0x1000, -0x1000, 0x4000, -0x4000):
            for x, y in ((0, 0), (1, -1), (123, -456), (-789, 234), (4096, 2048)):
                yield command, (angle, x, y)
    for command in (0x08, 0x28, 0x0b, 0x1b, 0x2b, 0x3b):
        for value in ((0, 0, 0), (1, 2, 3), (-1, 2, -3), (123, -456, 789),
                      (4096, 2048, -1024), (-8192, 2048, 0)):
            yield command, value
    for value in ((0, 0, 0, 0), (1, 2, 3, 4), (123, -456, 789, 512),
                  (4096, 2048, -1024, 8192), (-8192, 2048, 0, 2048)):
        yield 0x18, value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    parser.add_argument('--baseline', help='Compare arithmetic to an earlier ELF without spacing enforcement')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    reference, names = load_elf(args.baseline) if args.baseline else (memory, symbols)
    cases = 0
    samples = list(vectors())
    for command, parameters in samples:
        actual = transact(memory, symbols, command, parameters)
        original = transact(reference, names, command, parameters, False)
        assert actual == original, ('arithmetic changed', hex(command), parameters, actual, original)
        oracle = expected(command, parameters)
        if oracle is not None:
            assert actual == oracle, ('independent arithmetic', hex(command), parameters, actual, oracle)
        cases += 1
    faults = 0
    if args.baseline:
        for command, parameters in ((4, (0x1000, 123)), (12, (0x1000, 123, -456)),
                                    (8, (1, 2, 3)), (24, (1, 2, 3, 4)),
                                    (40, (1, 2, 3)), (11, (1, 2, 3))):
            try:
                transact(reference, names, command, parameters)
            except AssertionError as error:
                assert 'VR4300 HI/LO spacing' in str(error), error
                faults += 1
        assert faults == 6, 'baseline no longer reproduces all six vector hazards'
    # An explicit instruction fault keeps the spacing check useful in CI,
    # where an earlier baseline artifact need not be available.
    cpu = CPU(memory.copy())
    entry = symbols['dsp1_radius']
    multiplies = [pc for pc in range(entry, entry+128, 4) if cpu.read(pc) & 0xfc00003f == 24]
    assert len(multiplies) >= 2
    cpu.write(multiplies[1]-4, 0x00004012)  # MFLO t0 immediately before MULT.
    try:
        transact(cpu.memory, symbols, 8, (1, 2, 3))
    except AssertionError as error:
        assert 'VR4300 HI/LO spacing' in str(error), error
        faults += 1
    else:
        raise AssertionError('injected HI/LO hazard was accepted')
    print(f'DSP1_VECTOR_HILO PASS cases={cases} commands={len(OUTPUTS)} rejected_faults={faults}')


if __name__ == '__main__':
    main()
