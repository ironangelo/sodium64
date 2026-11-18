#!/usr/bin/env python3
"""Check compiled VRAM publication operations and the renderer's dirty handoff."""
import argparse
import random

from linked_cpu_regression import CPU, load_elf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    dirty = symbols['vram_table']
    vram = symbols['vram']
    boot = symbols['vram_publish_full']
    queues = CPU(memory)
    queue_addresses = [queues.read(symbols['dirty_queues'] + slot) for slot in (0, 4)]
    assert queues.read(boot, 1) == 1
    assert vram % 16 == 0

    rng = random.Random(0x6411)
    clean = bytes(1024)
    patterns = [clean, bytes([31]) * 1024]
    for index in (0, 1, 7, 8, 511, 512, 1016, 1023):
        pattern = bytearray(1024)
        pattern[index] = 31
        patterns.append(pattern)
    for density in (1, 10, 50):
        patterns.append(bytes(31 if rng.randrange(100) < density else 0 for _ in range(1024)))

    instruction_counts = []
    for slot, queue in enumerate(queue_addresses):
        other_queue = queue_addresses[1 - slot]
        for force in (0, 1):
            for pattern in patterns:
                cpu = CPU(memory.copy())
                for offset in range(0, len(pattern), 8):
                    cpu.write(dirty + offset, int.from_bytes(pattern[offset:offset + 8], 'big'), 8)
                if not force:
                    cpu.write(boot, 0, 1)
                cpu.memory_writes.clear()
                cpu.pattern()
                cpu.regs[13] = slot * 4  # t5 selects the handed queue.
                before = cpu.regs.copy()
                expected = [(0x19, vram + offset) for offset in range(0, 65536, 16)
                            if force or any(pattern[(offset // 512) * 8:(offset // 512 + 1) * 8])]
                cpu.execute(symbols['vram_flush_begin'], stop=symbols['rsp_wait'], max_steps=9089)
                assert cpu.cache_ops == expected
                assert cpu.blob(queue, 1024) == pattern
                assert cpu.blob(other_queue, 1024) == queues.blob(other_queue, 1024)
                assert cpu.blob(dirty, 1024) == clean
                assert cpu.read(boot, 1) == 0
                expected_writes = []
                for offset in range(0, len(pattern), 8):
                    value = int.from_bytes(pattern[offset:offset + 8], 'big')
                    expected_writes.extend((((dirty + offset) & 0x1fffffff, 8, 0),
                                            ((queue + offset) & 0x1fffffff, 8, value)))
                expected_writes.append((boot & 0x1fffffff, 1, 0))
                assert cpu.memory_writes == expected_writes
                assert all(cpu.regs[i] == before[i] for i in range(32)
                           if i not in (1, 3, 8, 9, 10, 11, 14))
                instruction_counts.append(cpu.steps - 1)  # execute counts reaching the stop.

    # The former loops ran 128 × 7 dirty-copy and 2048 × 4 cache instructions.
    assert max(instruction_counts) < 128 * 7 + 2048 * 4
    print(f'VRAM_PUBLICATION PASS {len(instruction_counts)} cases, '
          f'{min(instruction_counts)}-{max(instruction_counts)} instructions, '
          '0 clean lines and 4096 boot/full lines')


if __name__ == '__main__':
    main()
