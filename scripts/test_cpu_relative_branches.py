#!/usr/bin/env python3
"""Check the linked 65C816 relative branches through opcode dispatch."""
import argparse
from pathlib import Path

from linked_cpu_regression import CPU, load_elf, signed


BRANCHES = (
    (0x80, "bra", 0, False),
    (0x82, "brl", 0, False),
    (0x10, "bpl", 0x80, False),
    (0x30, "bmi", 0x80, True),
    (0x50, "bvc", 0x40, False),
    (0x70, "bvs", 0x40, True),
    (0x90, "bcc", 0x01, False),
    (0xB0, "bcs", 0x01, True),
    (0xD0, "bne", 0x02, False),
    (0xF0, "beq", 0x02, True),
)
MODE_TABLES = (("opcodes_e", 0x130), ("opcodes_16", 0))
POSITIONS = (0x0000, 0x0001, 0x007E, 0x8000, 0xFF7D, 0xFFFC, 0xFFFE, 0xFFFF)
DISPLACEMENTS = {1: range(256), 2: (0, 1, 0x7FFF, 0x8000, 0x8001, 0xFFFE, 0xFFFF)}


class BranchCPU(CPU):
    def __init__(self, memory, instruction_pc, instruction):
        super().__init__(memory)
        self.instruction = {instruction_pc + i: byte for i, byte in enumerate(instruction)}
        self.operand_reads = []

    def read(self, address, size=4):
        address &= 0x1FFFFFFF
        if address in self.instruction:
            assert size == 1
            self.operand_reads.append(address)
            return self.instruction[address]
        return super().read(address, size)


def execute(memory, symbols, opcode, handler, table, flags, pc, operand, taken):
    cpu = BranchCPU(memory, pc, bytes((opcode,)) + operand)
    cpu.regs[19] = 0                  # APU scheduling threshold
    cpu.regs[20] = flags
    cpu.regs[21] = 256                # Guest clock units before the next event
    cpu.regs[22] = symbols[table]
    cpu.regs[23] = pc
    dispatch = symbols["cpu_execute"]
    entry = symbols["cpu_" + handler]
    cpu.execute(dispatch, stop=entry, max_steps=24)
    cpu.execute(entry, stop=dispatch, max_steps=40)

    next_pc = pc + 1 + len(operand)
    expected = next_pc
    if taken:
        displacement = signed(int.from_bytes(operand, "little"), 8 * len(operand))
        # The emulator's existing fetch/advance rules own the bank. Displacement
        # arithmetic must change only the low 16 bits of the post-operand PC.
        expected = (next_pc & ~0xFFFF) | ((next_pc + displacement) & 0xFFFF)
    assert cpu.regs[23] == expected, ("relative destination", handler, pc, operand.hex(), flags)
    assert cpu.regs[20:23] == [flags, 256 - (1 + len(operand)) * 8, symbols[table]]
    assert cpu.operand_reads == list(range(pc, next_pc))
    assert cpu.memory_writes == [] and cpu.cache_ops == []
    return cpu.steps


def check(memory, symbols, reference):
    total = shorter = 0
    for opcode, handler, flag, flag_set in BRANCHES:
        size = 2 if handler == "brl" else 1
        for table, mode_flags in MODE_TABLES:
            for bank in (0x20, 0x7E, 0xFF):
                for position in POSITIONS:
                    pc = (bank << 16) | position
                    for displacement in DISPLACEMENTS[size]:
                        # BEQ's existing CLI/LDA idle detector reads at -4.
                        # Its inputs here contain no matching LDA/CLI pair.
                        operand = displacement.to_bytes(size, "little")
                        for condition in ((False, True) if flag else (False,)):
                            taken = not flag or condition == flag_set
                            flags = mode_flags | (flag if condition else 0)
                            args = (opcode, handler, table, flags, pc, operand, taken)
                            steps = execute(memory, symbols, *args)
                            if reference:
                                original_steps = execute(*reference, *args)
                                assert original_steps - steps == int(taken and handler != "beq")
                            total += 1
                            shorter += int(taken and handler != "beq")
    return total, shorter


def check_mutation(memory, symbols):
    # Remove the emitted BRA jump delay slot. The cross-bank case must fail
    # specifically at the relative-destination assertion.
    entry = symbols["cpu_bra"] & 0x1FFFFFFF
    delay = entry + 7 * 4
    assert CPU(memory).read(delay - 4) >> 26 == 2
    assert CPU(memory).read(delay) & 63 == 38  # XOR
    fault = memory.copy()
    for offset in range(4):
        fault[delay + offset] = 0
    try:
        execute(fault, symbols, 0x80, "bra", "opcodes_e", 0x130, 0x20FFFD, b"\x01", True)
    except AssertionError as error:
        assert error.args[0][0] == "relative destination", error
    else:
        raise AssertionError("missing BRA delay slot escaped")


def check_beq_idle(memory, symbols):
    pc = 0x208002
    dispatch = symbols["cpu_execute"]
    entry = symbols["cpu_beq"]
    for cli, halted in ((0x58, True), (0xEA, False)):
        cpu = BranchCPU(memory, pc - 2, bytes((0xA5, 0, 0xF0, 0xFC, cli)))
        flags = 0x132
        cpu.regs[20:24] = [flags, 256, symbols["opcodes_e"], pc]
        cpu.execute(dispatch, stop=entry, max_steps=24)
        cpu.execute(entry, stop=dispatch, max_steps=40)
        assert cpu.regs[23] == pc - 2
        assert cpu.regs[20:22] == [flags | (0x200 if halted else 0), 0 if halted else 240]
        reads = [pc, pc + 1, pc + 2]
        if halted:
            reads.append(pc - 2)
        assert cpu.operand_reads == reads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    reference = load_elf(args.reference) if args.reference else None
    total, shorter = check(memory, symbols, reference)
    check_beq_idle(memory, symbols)
    check_mutation(memory, symbols)
    instruction_count = f", {shorter} one-instruction reductions against reference" if reference else ""
    print(f"CPU_RELATIVE_BRANCHES PASS: {total} branch cases, two BEQ idle cases, one emitted fault rejected{instruction_count}")


if __name__ == "__main__":
    main()
