#!/usr/bin/env python3
"""Linked projection protocol/parity. Setup 02 is deliberately NOT spacing-qualified."""
import argparse
from linked_cpu_regression import CPU, load_elf, signed
from test_dsp1_vector_hilo import call

# Reverse only the instruction permutations, retaining linked load relocations.
PERMUTATIONS = ((0xb8, (1, 0)), (0xd0, (2, 3, 4, 5, 0, 1, 8, 6, 7)),
                (0xfc, (2, 0, 1)), (0x110, (1, 0)),
                (0x1c8, (2, 0, 1)), (0x1d8, (2, 0, 1)),
                (0x230, (2, 0, 3, 4, 5, 6, 7, 9, 8, 1)))
HAZARDS = tuple(offset for offset, _ in PERMUTATIONS)
SETUPS = ((0, 0, 256, 128, 256, 0, 0),
          (128, -256, 512, 256, 512, 0x1000, 0x2000),
          (-128, 64, 1024, 512, 768, -0x1000, 0x3000))
POINTS = ((123, 456, 789), (-123, -456, -789), (0, 0, 0),
          (1, -1, 1), (4096, 2048, -1024), (-2048, 4096, 2048))


def port(cpu, symbols, command, parameters, count):
    call(cpu, symbols['write_dsp1dr'], command)
    assert cpu.read(symbols['dsp1_sr'], 2) & 0x1400 == 0
    for index, word in enumerate(parameters):
        call(cpu, symbols['write_dsp1dr'], word & 255)
        assert cpu.read(symbols['dsp1_sr'], 2) & 0x1000
        call(cpu, symbols['write_dsp1dr'], (word >> 8) & 255)
        assert not cpu.read(symbols['dsp1_sr'], 2) & 0x1000
        for n, value in enumerate(parameters[:index+1]):
            assert cpu.read(symbols['input_buf']+2*(len(parameters)-1-n), 2) == value & 65535
    result = [call(cpu, symbols['read_dsp1dr']) |
              (call(cpu, symbols['read_dsp1dr']) << 8) for _ in range(count)]
    assert cpu.read(symbols['dsp1_sr'], 2) & 0x400
    assert cpu.read(symbols['dsp1_dr'], 2) == 0x80
    assert not cpu.cp_writes and not cpu.cache_ops
    return result


def prepared(memory, symbols, setup):
    cpu = CPU(memory.copy())
    # Parameters have independent pre-existing hazards, outside this change.
    cpu.enforce_hilo_spacing = False
    port(cpu, symbols, 2, setup, 4)
    cpu.memory_writes.clear()
    return cpu


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    parser.add_argument('--baseline', help='Same-configuration ELF before projection reorder')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    entry, end = symbols['dsp1_projec'], symbols['dsp1_unimpl']
    old = CPU(memory.copy())
    for offset, permutation in PERMUTATIONS:
        words = [old.read(entry+offset+4*n) for n in range(len(permutation))]
        for n, index in enumerate(permutation):
            old.write(entry+offset+4*n, words[index])
    reference, names = load_elf(args.baseline) if args.baseline else (old.memory, symbols)
    if args.baseline:
        assert symbols == names, 'linked symbols/owner boundaries changed'
        assert memory.keys() == reference.keys(), 'allocated layout changed'
        assert reference == old.memory, 'changes outside exact projection permutations'
        assert all(memory[a] == reference[a] for a in memory
                   if not (entry & 0x1fffffff) <= a < (end & 0x1fffffff)), 'outside-function bytes changed'
    # Confirm exactly seven old static hazards and no new static hazards.
    def hazards(image):
        cpu = CPU(image)
        return {pc-entry for pc in range(entry, end, 4)
                if cpu.read(pc) >> 26 == 0 and 24 <= cpu.read(pc) & 63 <= 31
                and any(cpu.read(q) >> 26 == 0 and cpu.read(q) & 63 in (16, 18)
                        for q in (pc-8, pc-4))}
    assert hazards(reference) == set(HAZARDS)
    assert not hazards(memory)
    branches = {}
    def watch_branch(cpu, pc, word):
        op, rs, rt = word >> 26, word >> 21 & 31, word >> 16 & 31
        left, right = cpu.regs[rs], cpu.regs[rt]
        taken = ((left == right) if op == 4 else (left != right) if op == 5
                 else (signed(left) >= 0) if op == 1 and rt == 1
                 else (signed(left) < 0) if op == 1 and rt == 0
                 else None)
        assert taken is not None, ('unhandled branch', hex(word))
        branches.setdefault(pc-entry, set()).add(taken)
    cases = 0
    for command in (6, 0x16, 0x26, 0x36):
        for setup in SETUPS:
            for point in POINTS:
                actual = prepared(memory, symbols, setup)
                actual.enforce_hilo_spacing = True
                for pc in range(entry, end, 4):
                    word = actual.read(pc)
                    if word >> 26 in (1, 4, 5):
                        actual.before_instruction[pc] = lambda cpu, pc=pc, word=word: watch_branch(cpu, pc, word)
                result = port(actual, symbols, command, point, 3)
                baseline = prepared(reference, names, setup)
                expected = port(baseline, names, command, point, 3)
                assert result == expected, (command, setup, point, result, expected)
                assert actual.memory_writes == baseline.memory_writes, 'observable write sequence changed'
                cases += 1
    varying_branches = sum(len(outcomes) == 2 for outcomes in branches.values())
    assert varying_branches >= 2, ('insufficient branch diversity', branches)
    faults = 0
    for offset in HAZARDS:
        baseline = prepared(reference, names, SETUPS[0])
        # Other old sites execute architecturally; qualify each targeted site.
        baseline.before_instruction[entry+offset-8] = lambda cpu: setattr(cpu, 'enforce_hilo_spacing', True)
        try:
            port(baseline, names, 6, POINTS[0], 3)
        except AssertionError as error:
            assert 'VR4300 HI/LO spacing' in str(error) and hex(entry+offset) in str(error), error
            faults += 1
        else:
            raise AssertionError(('baseline hazard not reached', hex(offset)))
    print(f'DSP1_PROJECTION_HILO PASS cases={cases} aliases=4 rejected_sites={faults} varying_branches={varying_branches} setup02_enforced=False layout={bool(args.baseline)}')


if __name__ == '__main__':
    main()
