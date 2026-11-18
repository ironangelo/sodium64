#!/usr/bin/env python3
"""Check compiled VRAM publication operations and the renderer's dirty handoff."""
import argparse
import random

from linked_cpu_regression import CPU, load_elf


class VRAMWriterCPU(CPU):
    def read(self, address, size=4):
        # Start with VRAM copying complete. SP semaphore bus timing is covered
        # separately by the hardware trial.
        if address & 0x1fffffff == 0x0404001c:
            assert size == 4
            return 0
        return super().read(address, size)


def check_writer_handoff(memory, symbols, queue_addresses):
    vram = symbols['vram']
    dirty = symbols['vram_table']
    positions = (0, 0x1f, 0x20, 0xff, 0x100, 0x1ff, 0x200, 0x3ff,
                 0x400, 0x3fff, 0x4000, 0x7fff)
    cases = 0
    for mode in range(4):
        for lane, handler in enumerate(('write_vmdatah', 'write_vmdatal')):
            for position in positions:
                cpu = VRAMWriterCPU(memory.copy())
                cpu.allow_rcp_writes = True
                cpu.pattern()
                cpu.regs[5] = (mode << 2) | (0x80 if lane == 0 else 0)
                cpu.execute(symbols['write_vmain'])
                cpu.write(symbols['vmadd'], position, 2)
                cpu.write(symbols['vram_publish_full'], 0, 1)
                cpu.regs[5] = 0xa5
                cpu.memory_writes.clear()
                cpu.execute(symbols[handler])

                translated = position
                if mode:
                    shift = mode + 4
                    mask = (1 << (shift + 3)) - 1
                    translated = ((position & ~mask)
                                  | ((position & (mask >> 3)) << 3)
                                  | ((position >> shift) & 7))
                offset = (translated << 1) + lane
                block = offset // 64
                group_offset = (offset // 512) * 512
                assert cpu.memory_writes[:3] == [
                    (0x0404001c, 4, 0),
                    ((vram + offset) & 0x1fffffff, 1, 0xa5),
                    ((dirty + block) & 0x1fffffff, 1, 31),
                ], (handler, mode, position, cpu.memory_writes)
                dirty_pattern = bytearray(1024)
                dirty_pattern[block] = 31
                cpu.regs[13] = lane * 4
                cpu.execute(symbols['vram_flush_begin'], stop=symbols['rsp_wait'])
                assert cpu.cache_ops == [(0x19, vram + address)
                                         for address in range(group_offset, group_offset + 512, 16)]
                assert cpu.blob(queue_addresses[lane], 1024) == dirty_pattern
                assert cpu.blob(dirty, 1024) == bytes(1024)
                cases += 1
    return cases


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

    writer_cases = check_writer_handoff(memory, symbols, queue_addresses)

    # The former loops ran 128 × 7 dirty-copy and 2048 × 4 cache instructions.
    assert max(instruction_counts) < 128 * 7 + 2048 * 4
    print(f'VRAM_PUBLICATION PASS {len(instruction_counts)} map cases and {writer_cases} writer cases, '
          f'{min(instruction_counts)}-{max(instruction_counts)} instructions, '
          '0 clean lines and 4096 boot/full lines')


if __name__ == '__main__':
    main()
