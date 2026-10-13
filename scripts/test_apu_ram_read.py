#!/usr/bin/env python3
"""Differential execution of linked RAM emitters and real SPC700 JIT blocks.

The unchanged general-reader ELF is the independent execution control. This
does not model cache timing or native speed. Ordinary guest reads, I/O/ROM
fallbacks, per-access cycle position and scheduler bounds remain mandatory.
"""
import argparse
import json
from pathlib import Path

from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU, RETURN, sx32


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--reference-elf', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    models = [load_elf(args.reference_elf), load_elf(args.elf)]
    assert 'jit_emit_ram_read' not in models[0][1]
    assert 'jit_emit_ram_read' in models[1][1]
    counts = {'direct': 0, 'absolute': 0, 'blocks': 0, 'cycle_position': 0}
    work = {}

    def setup(index, clock, page, rom, program, address):
        memory, symbols = models[index]
        cpu = CPU(memory.copy())
        cpu.pattern()
        cpu.write(symbols['apu_clock'], clock, 1)
        cpu.write(symbols['apu_flags'], page | 0x81, 1)
        cpu.write(symbols['apu_map'] + 0x3ff, rom, 1)
        cpu.write(symbols['apu_ram'] + address, 0x63, 1)
        cpu.write(symbols['apu_inputs'], 0x23456789)
        cpu.write(symbols['apu_ram'] + 0xf2, 0x02, 1)
        cpu.write(symbols['dsp_regs'] + 2, 0xb7, 1)
        cpu.write(symbols['apu_ram'] + 0x400, int.from_bytes(program, 'big'), len(program))
        cpu.write(symbols['jit_block_cycles'], 1)
        cpu.regs[4] = 0x400
        cpu.regs[5] = sx32(0xa01c1000)
        cpu.regs[6] = sx32(0xa0200000)
        cpu.regs[16] = 0x3ff
        cpu.regs[17] = 0
        cpu.regs[18] = 0
        cpu.regs[25] = 0x410
        cpu.regs[28] = RETURN
        return cpu, symbols

    def state(cpu, symbols):
        return dict(gprs=[cpu.regs[i] for i in (2, 4, 17, 19, 20, 21, 22, 23, 29, 30)],
                    guest=cpu.blob(symbols['apu_ram'], 65536),
                    tags=cpu.blob(symbols['jit_tags'], 4096),
                    timers=cpu.blob(symbols['apu_cycle1'], 40),
                    dsp=cpu.blob(symbols['dsp_regs'], 128))

    def emit(index, direct, operand, clock, page, rom):
        address = operand | (0x100 if page else 0) if direct else operand
        program = bytes([operand]) if direct else operand.to_bytes(2, 'little')
        cpu, symbols = setup(index, clock, page, rom, program, address)
        start = cpu.regs[5] & 0xffffffff
        cpu.execute(symbols['apu_dirr' if direct else 'apu_absr'])
        end = cpu.regs[5] & 0xffffffff
        budget = cpu.read(symbols['jit_block_cycles'])
        debit = cpu.regs[18]
        words = [cpu.read(pc) for pc in range(start, end, 4)]
        calls_reader = any(word >> 26 == 3 and
                           ((((start - 0x20000000) & 0xf0000000) | ((word & 0x3ffffff) << 2)) == symbols['apu_read8'])
                           for word in words)
        safe = operand < 0xf0 if direct else (operand < 0xffc0 and not 0xf0 <= operand <= 0xff)
        assert calls_reader == (not index or not safe), (direct, hex(operand), 'admission')
        cpu.pattern()
        cpu.regs[19] = 0
        before = cpu.steps
        cpu.execute(start - 0x20000000, stop=end - 0x20000000)
        cpu.test_span = start - 0x20000000, end - 0x20000000
        assert cpu.regs[4] == address and cpu.regs[19] == sx32(-clock)
        assert budget == (3 if direct else 4)
        assert debit == sx32(-clock * (1 if direct else 2))
        return cpu, symbols, cpu.steps - before, safe

    absolute = sorted(set(range(0xef, 0x101)) |
                      {0, 1, 0xee, 0x1ef, 0x1f0, 0x1ff, 0x200, 0x400, 0x7fff,
                       0x8000, 0xff00, 0xffbf, 0xffc0, 0xffc1, 0xfffe, 0xffff})
    for direct, operands in ((True, range(256)), (False, absolute)):
        for operand in operands:
            for page in (0, 0x20):
                clock = 21 if operand & 1 else 42
                rom = 0x40 if operand & 2 else 0
                executions = [emit(i, direct, operand, clock, page, rom) for i in (0, 1)]
                left, right = executions
                assert state(left[0], left[1]) == state(right[0], right[1]), ('semantics', direct, hex(operand), page)
                kind = 'direct' if direct else 'absolute'
                counts[kind] += 1
                if right[3]:
                    work.setdefault(kind, (left[2], right[2]))
                    assert right[2] < left[2], ('work not removed', kind, left[2], right[2])

    # Run complete production compile/execute loops, including real RMW
    # handlers and following I/O. Their ordinary RAM read must not move its
    # debit after a subsequent timer read or out of the scheduler budget.
    programs = [bytes([0xe4, 0x20]), bytes([0xe5, 0x00, 0x20]),
                bytes([0xab, 0x20]), bytes([0xac, 0x00, 0x20]),
                bytes([0x8b, 0x20]), bytes([0x0b, 0x20]),
                bytes([0x02, 0x20]), bytes([0x12, 0x20]),
                bytes([0xe4, 0x20, 0xe4, 0xfd]),
                bytes([0xe5, 0x00, 0x20, 0xe4, 0xfd])]
    for program in programs:
        for page in (0, 0x20):
            states, budgets, positions = [], [], []
            for index in (0, 1):
                cpu, symbols = setup(index, 21, page, 0x40,
                                     program + bytes(20), 0x120 if page else 0x20)
                cpu.write(symbols['apu_ram'] + 0x2000, 0x63, 1)
                cpu.write(symbols['jit_pointer'], 0xa01c0000)
                cpu.regs[16] = 0x400
                cpu.regs[19] = 0
                observed = []
                def timer_entry(model):
                    observed.append(model.regs[19])
                cpu.before_instruction[symbols['read_t0out']] = timer_entry
                cpu.execute(symbols['compile_block'], stop=symbols['cpu_execute'])
                states.append(state(cpu, symbols))
                budgets.append(cpu.read(symbols['jit_block_cycles']))
                positions.append(observed)
                assert 20 < budgets[-1] <= 32
            assert states[0] == states[1], ('full block semantics', program.hex(), page)
            assert budgets[0] == budgets[1] and positions[0] == positions[1]
            counts['blocks'] += 1
            if positions[0]: counts['cycle_position'] += 1

    # Corrupt the actual emitted debit and RAM relocation separately. The
    # same oracle checks must reject both, rather than accepting a faster read
    # with altered timing/value.
    mutations = []
    cpu, symbols, _, _ = emit(1, True, 0x20, 21, 0, 0)
    for name, selected in (('missing_bus_debit', lambda w: w == 0x02689822),
                           ('wrong_RAM_byte', lambda w: w >> 26 == 36 and w >> 16 & 31 == 2)):
        start, end = cpu.test_span
        words = [(pc, cpu.read(pc)) for pc in range(start, end, 4)]
        matches = [(pc, word) for pc, word in words if selected(word)]
        assert len(matches) == 1, (name, matches)
        mutated = CPU(cpu.memory.copy())
        pc, word = matches[0]
        mutated.write(pc, 0 if name == 'missing_bus_debit' else word + 1)
        mutated.pattern(); mutated.regs[19] = 0
        mutated.execute(start, stop=end)
        assert mutated.regs[19] != sx32(-21) or mutated.regs[2] != 0x63, name
        mutations.append(name)
    result = dict(passed=True, cases=counts, actual_runtime_instruction_counts=work,
                  negative_mutations_rejected=mutations, guest_bus_debit_moved=False,
                  scheduler_worst_case_limit=32, native_speed_claim=False)
    if args.output: args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('APU_RAM_READ PASS', json.dumps(result))


if __name__ == '__main__': main()
