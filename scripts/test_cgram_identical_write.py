#!/usr/bin/env python3
"""Exercise the linked CGRAM bus writer and typed epoch transitions."""
import argparse

from linked_cpu_regression import CPU, load_elf, signed


CAPACITY = 0x6000


def rgba5551(raw):
    return ((raw & 31) << 11) | ((raw & 0x3e0) << 1) | ((raw & 0x7c00) >> 9) | 1


def commit(cpu, s, index, previous, raw, phase, parity, *, wrap=False):
    def put(name, value, width):
        cpu.write(s[name], value, width)

    def get(name, width):
        return cpu.read(s[name], width)

    def owner(name, width):
        return (s[name] & 0x1fffffff, width)

    address = 0xfffe if wrap else index*2
    assert not wrap or index == 255
    palette = s['cgram'] + 2*index
    queue = cpu.read(s['hcomp_cgram_event_queues'] + 4*parity)
    count = CAPACITY if phase == 'full' else 3
    cursor = queue + 4*count
    marker = 0xfeed8000
    pending_section = 0x100 if parity else 0
    put('cgadd', address, 2)
    put('cg_lsb', 0xff, 1)
    put('hvbjoy', 0x80 if phase == 'vblank' else 0, 1)
    put('frame_done', int(phase == 'closed'), 1)
    put('hcomp_cgram_event_count', count, 2)
    put('hcomp_cgram_event_ptr', cursor, 4)
    put('hcomp_cgram_event_overflow', 0, 1)
    put('sect_status', pending_section, 2)
    cpu.write(palette, previous, 2)
    cpu.write(cursor-4, marker)
    cpu.write(cursor, 0xdecafbad)

    cpu.pattern()
    cpu.regs[5] = raw & 255
    cpu.memory_writes.clear()
    cpu.execute(s['write_cgdata'])
    assert get('cgadd', 2) == address+1 and get('cg_lsb', 1) == raw & 255
    assert cpu.read(palette, 2) == previous
    assert {(at, n) for at, n, _ in cpu.memory_writes} == {owner('cgadd', 2), owner('cg_lsb', 1)}

    cpu.pattern()
    cpu.regs[5] = raw >> 8
    cpu.memory_writes.clear()
    if index == 0:
        # The backdrop entry still goes through the original fill update.
        cpu.execute(s['write_cgdata'], stop=s['update_fill'])
    else:
        cpu.execute(s['write_cgdata'])
    assert get('cgadd', 2) == (address+2) & 0xffff and get('cg_lsb', 1) == raw & 255
    assert cpu.read(palette, 2) == raw
    assert cpu.read(cursor-4) == marker, 'previous marker changed'
    expected = {owner('cgadd', 2), (palette & 0x1fffffff, 2)}
    append = raw != previous and phase == 'active'
    overflow = raw != previous and phase == 'full'
    if append:
        expected.update(((cursor & 0x1fffffff,4), owner('hcomp_cgram_event_count',2),
                         owner('hcomp_cgram_event_ptr',4), owner('sect_status',2)))
    if overflow:
        expected.update((owner('hcomp_cgram_event_overflow',1),owner('sect_status',2)))
    assert {(at, n) for at, n, _ in cpu.memory_writes} == expected, 'wrong epoch writes'
    assert get('hcomp_cgram_event_count', 2) == count + int(append)
    assert get('hcomp_cgram_event_ptr', 4) == cursor + 4*int(append)
    assert get('hcomp_cgram_event_overflow', 1) == int(overflow)
    assert get('sect_status', 2) == (0x100 if append or overflow else pending_section)
    assert cpu.read(cursor) == (((rgba5551(raw)<<16) | (index*8)) if append else 0xdecafbad)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    args = parser.parse_args()
    memory, s = load_elf(args.elf)
    cpu = CPU(memory)
    cases = 0
    for index in range(256):
        raw = (index*251+0x1234) & 0xffff
        for phase in ('active','vblank','closed','full'):
            for parity in (0,1):
                for old in (raw,raw^0x1f,raw^0x8000):
                    commit(cpu, s, index, old, raw, phase, parity)
                    cases += 1
    commit(cpu,s,255,0xbabe,0xbabe,'active',0,wrap=True)
    commit(cpu,s,255,0xbabe,0x3abe,'active',1,wrap=True)
    cases += 2
    branch = []
    for at in range(s['cg_high'], s['cg_epoch_done'], 4):
        word = cpu.read(at)
        registers = (word >> 21 & 31, word >> 16 & 31)
        target = at + 4 + (signed(word & 0xffff, 16) << 2)
        if word >> 26 == 4 and registers == (10, 9) and target == s['cg_epoch_done']:
            branch.append(at)
    assert len(branch) == 1
    instruction = cpu.read(branch[0])
    for fault, old in ((0,0x1234),(instruction | (1<<26),0x1235)):
        cpu.write(branch[0],fault)
        try:
            commit(cpu,s,5,old,0x1234,'active',1)
        except AssertionError as error:
            assert str(error) == 'wrong epoch writes'
        else:
            raise AssertionError('emitted equality-branch fault escaped')
        finally:
            cpu.write(branch[0],instruction)
    print(f'CGRAM_IDENTICAL_WRITE PASS cases={cases} emitted_faults=2')


if __name__ == '__main__':
    main()
