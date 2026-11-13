#!/usr/bin/env python3
"""Execute actual cursor/EntryLo0 publication. PI/TLB execution is outside scope."""
import argparse
import json
from pathlib import Path

from linked_cpu_regression import CPU, load_elf


def word(memory, address):
    address &= 0x1fffffff
    return int.from_bytes(bytes(memory[address+i] for i in range(4)), 'big')


def put_word(memory, address, value):
    address &= 0x1fffffff
    memory.update((address+i, byte) for i, byte in enumerate(value.to_bytes(4, 'big')))


def check(memory, symbols):
    cpu = CPU(memory.copy())
    slots = symbols['faithful_rom_cache_slots']
    base = symbols['faithful_rom_cache_buffer']
    assert slots == 194 and base+slots*8192 == 0x384000

    def run(cursor):
        cpu.pattern()
        cpu.write(symbols['rom_pointer'], cursor, 1)
        cpu.memory_writes = []
        before, hi, lo, cp = cpu.regs.copy(), cpu.hi, cpu.lo, cpu.cp.copy()
        cpu.execute(symbols['faithful_rom_cursor_begin'],
                    stop=symbols['faithful_rom_entry_ready'], max_steps=40)
        expected = (cursor+1) % slots
        assert cpu.read(symbols['rom_pointer'], 1) == expected, 'cache pointer escaped selected slots'
        assert cpu.regs[26] == cursor, 'current page index changed'
        assert cpu.regs[27] == (((base//8192)+cursor) << 7 | 0x1b), 'EntryLo0 publication'
        assert cpu.memory_writes == [(symbols['rom_pointer'] & 0x1fffffff, 1, expected)]
        assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1, 26, 27)), 'unexpected register clobber'
        assert (cpu.hi, cpu.lo, cpu.cp) == (hi, lo, cp)
        return expected

    for cursor in range(slots):
        run(cursor)
    cursor = 0
    for _ in range(3*slots):
        cursor = run(cursor)
    assert cursor == 0
    return slots*4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path, nargs='+')
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    variants = []
    for path in args.elf:
        memory, symbols = load_elf(path)
        cases = check(memory, symbols)
        addresses = range(symbols['faithful_rom_cursor_begin'], symbols['faithful_rom_entry_ready'], 4)
        limits = [at for at in addresses if word(memory, at) >> 26 in (9, 13)
                  and (word(memory, at) >> 16 & 1023) == 27 and word(memory, at) & 65535 == 193]
        resets = [at for at in addresses if word(memory, at) >> 26 == 0
                  and word(memory, at) & 63 in (0x21, 0x25)
                  and (word(memory, at) >> 21 & 31) == (word(memory, at) >> 16 & 31) == 0
                  and (word(memory, at) >> 11 & 31) == 27]
        permissions = [at for at in addresses if word(memory, at) >> 26 == 13
                       and word(memory, at) >> 21 & 31 == word(memory, at) >> 16 & 31 == 27
                       and word(memory, at) & 65535 == 0x1b]
        assert len(limits) == len(resets) == len(permissions) == 1, 'compiled pager anchors drifted'
        faults = [('late_wrap', limits[0], (word(memory, limits[0]) & ~65535) | 194),
                  ('early_wrap', limits[0], (word(memory, limits[0]) & ~65535) | 192),
                  ('missing_wrap', resets[0], 0),
                  ('writable_ROM_entry', permissions[0], word(memory, permissions[0]) | 4)]
        rejected = []
        for name, address, value in faults:
            changed = memory.copy()
            put_word(changed, address, value)
            try:
                check(changed, symbols)
            except AssertionError as error:
                assert str(error) in ('cache pointer escaped selected slots', 'EntryLo0 publication'), str(error)
                rejected.append(name)
            else:
                raise AssertionError(('emitted pager fault escaped', name))
        variants.append({'elf': str(path), 'linked_cases': cases, 'faults_rejected': rejected})
    report = {'passed': True, 'variants': variants,
              'scope': 'Actual 194-slot cursor and readonly EntryLo0 construction; no PI, TLB replacement, title or native performance claim.',
              'physical_acceptance': False}
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
