"""Execute the exact linked JIT pair, including an epoch wrap and cached reuse."""
import argparse
import json
from pathlib import Path

from linked_cpu_regression import CPU, load_elf

PC = 0x0480
RETURN = 0x0490
OWNER = 0x80441CD4


def run_elf(elf, exact):
    memory, symbols = load_elf(elf)
    cpu = CPU(memory)
    cases = 0
    for clock in (1, 21, 42, 255):
        cpu.write(symbols["apu_clock"], clock, 1)
        cpu.write(symbols["remote_boot_ram_bytes"], 0x800000)
        cpu.write(symbols["dsp_addr"], 8, 1)
        cpu.write(symbols["dsp_regs"] + 8, 0x4D, 1)
        for i, opcode in enumerate(bytes.fromhex("e4f3e4f36f")):
            cpu.write(symbols["apu_ram"] + PC + i, opcode, 1)
        for begin in (0x1000, 0xFFFFFFFF - clock):
            cpu.write(symbols["jit_pointer"], 0xA01C0000)
            cpu.write(symbols["jit_lookup"] + 4 * PC, 0)
            for _ in range(2):  # cold then warm at each epoch
                cpu.write(OWNER, (begin + 0x100000) & 0xFFFFFFFF)
                for i in range(4, 24, 4):
                    cpu.write(OWNER + i, 0)
                for name, value in (("apu_halt", 0), ("apu_flags", 0), ("apu_stack", 0x7D)):
                    cpu.write(symbols[name], value, 1)
                cpu.write(symbols["apu_ram"] + 0x17E, RETURN & 0xFF, 1)
                cpu.write(symbols["apu_ram"] + 0x17F, RETURN >> 8, 1)
                cpu.write(symbols["apu_count"], PC, 2)
                cpu.regs[7], cpu.regs[19] = 0, 0x100000
                jit = cpu.read(symbols["jit_lookup"] + 4 * PC)
                cpu.execute(symbols["apu_execute"], stop=symbols["cpu_execute"])
                assert cpu.read(symbols["apu_count"], 2) == RETURN
                assert cpu.read(symbols["apu_accum"], 1) == 0x4D
                assert 0x100000 - cpu.regs[19] == 11 * clock
                assert cpu.read(OWNER + 4) == 0  # pair consumed
                assert cpu.read(OWNER + 12) == 1
                assert cpu.read(OWNER + 16) == exact
                assert cpu.read(OWNER + 20) == (not exact)
                if jit:
                    assert cpu.read(symbols["jit_lookup"] + 4 * PC) == jit
                cases += 1
    return cases


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("legacy", type=Path)
    p.add_argument("prefix", type=Path)
    a = p.parse_args()
    print(json.dumps({"legacy_register_pair_cases": run_elf(a.legacy, False),
                      "prefix_register_pair_cases": run_elf(a.prefix, True),
                      "same_total_block_cycles": 11,
                      "clocks": [1, 21, 42, 255],
                      "cold_warm_and_epoch_wrap": True}, indent=2))
