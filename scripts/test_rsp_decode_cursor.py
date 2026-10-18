#!/usr/bin/env python3
"""Execute linked RSP decoder scalar flow, including every branch delay slot.

Vector-only instructions are replaced with NOPs after checking their encoding:
they cannot write scalar registers. This checks row count and live GPR ownership,
not vector arithmetic, pixels, RSP timing or the surrounding renderer.
"""
import argparse
import json
from pathlib import Path

from linked_cpu_regression import CPU, RETURN, load_elf, sx32
from check_rsp_branch_delay_slots import read_text


FAMILIES = ('shared_decode4', 'shared_decode16', 'shared_decode256')
OAM_VALUES = (0, 1, 0x10, 0x1fe, 0x1ff, 0x200, 0x3ff, 0x400,
              0x8000, 0xffff, 0x12345678, 0x80000000, 0xffffffff)


def word(memory, address):
    address &= 0x1fffffff
    return int.from_bytes(bytes(memory[address+i] for i in range(4)), 'big')


def put(memory, address, value):
    address &= 0x1fffffff
    memory.update((address+i, b) for i, b in enumerate(value.to_bytes(4, 'big')))


def scalar_image(path):
    memory, symbols = load_elf(path)
    _, text = read_text(Path(path))
    assert len(text) == 4096, 'renderer IMEM must still fit its 4 KiB bank'
    start, end = symbols['shared_decode'], symbols['calc_color_window_segments']
    vectors = []
    for address in range(start, end, 4):
        value = word(memory, address)
        op, rs = value >> 26, value >> 21 & 31
        if op in (50, 58) or (op == 18 and rs >= 16):
            vectors.append(value)
            put(memory, address, 0)
        else:
            assert op != 18, 'COP2 scalar transfer needs an explicit model'
    assert len(vectors) == 37, ('unexpected vector decoder body', len(vectors))
    return memory, symbols, vectors


class ScalarCPU(CPU):
    def __init__(self, memory, row):
        super().__init__(memory)
        self.row, self.rows = row & 0x1fffffff, 0

    def read(self, address, size=4):
        if address & 0x1fffffff == self.row:
            self.rows += 1
        return super().read(address, size)


def run(memory, symbols, family, cursor, oam):
    cpu = ScalarCPU(memory, symbols[family])
    cpu.pattern()
    cpu.regs = [sx32(value) for value in cpu.regs]
    cpu.regs[7], cpu.regs[14] = sx32(cursor), sx32(oam)
    cpu.regs[12] = sx32(symbols[family])
    before = cpu.regs.copy()
    cpu.execute(symbols['shared_decode'], max_steps=700)
    assert cpu.rows == 8, ('tile row count', family, cpu.rows)
    assert cpu.regs[15] == 0, 'texture cursor did not reach zero'
    initial_character = word(memory, symbols['shared_decode']+4) & 0xffff
    assert cpu.regs[9] == sx32(initial_character-16), 'character cursor mismatch'
    assert not cpu.memory_writes, 'scalar decoder wrote memory'
    for register in range(32):
        if register not in (9, 15):
            assert cpu.regs[register] == before[register], (
                'live GPR clobbered', family, register, hex(cursor), hex(oam))
    assert cpu.regs[31] == sx32(RETURN)


def check(path, baseline=None):
    memory, symbols, vectors = scalar_image(path)
    slot = symbols['calc_color_window_segments']-4
    assert word(memory, slot-4) == 0x01800008, 'expected decoder JR t4'
    assert word(memory, slot) == 0, 'decoder must own its delay slot'
    cases = 0
    for family in FAMILIES:
        for cursor in range(0x240, 0x440, 4):
            for oam in OAM_VALUES:
                run(memory, symbols, family, cursor, oam)
                cases += 1
    mutants = 0
    for instruction in (0x01c03825, 0x03e0c825):  # clobber a3 / t9
        changed = memory.copy()
        put(changed, slot, instruction)
        try:
            run(changed, symbols, 'shared_decode16', 0x240, 0x1ff)
        except AssertionError as error:
            assert 'live GPR clobbered' in str(error), str(error)
            mutants += 1
        else:
            raise AssertionError('emitted delay-slot mutant escaped')
    result = {'elf': str(path), 'cases': cases, 'mutants_rejected': mutants,
              'vector_instructions_unmodelled': len(vectors), 'imem_bytes': 4096}
    if baseline:
        old, old_symbols, old_vectors = scalar_image(baseline)
        assert old_vectors == vectors, 'vector arithmetic/load/store changed'
        assert word(old, old_symbols['calc_color_window_segments']) == 0x01c03825
        failures = 0
        for family in FAMILIES:
            for cursor in range(0x240, 0x440, 4):
                for oam in OAM_VALUES:
                    try:
                        run(old, old_symbols, family, cursor, oam)
                    except AssertionError as error:
                        assert 'live GPR clobbered' in str(error), str(error)
                        failures += 1
        assert failures > 0, 'original linked decoder did not reproduce the fault'
        result.update(baseline_failures=failures, vector_words_identical=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', nargs=2, type=Path)
    parser.add_argument('--baseline', nargs=2, type=Path)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    results = [check(path, args.baseline[i] if args.baseline else None)
               for i, path in enumerate(args.elf)]
    receipt = {'scope': 'linked scalar control and GPR ownership only',
               'status': 'PASS', 'banks': results}
    if args.json_output:
        args.json_output.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
