#!/usr/bin/env python3
"""Execute the complete linked ROM refill/eviction handler with delayed PI.

Original synthetic cartridge pages only. The PI/TLB devices are functional
models, not R4300 cache, bus timing or coprocessor-hazard qualification. Native
cache coherency and representative title behavior remain physical gates.
"""
import argparse
import hashlib
import json
from pathlib import Path

from linked_cpu_regression import CPU, load_elf
from test_faithful_rom_cache import word, put_word


BASE, END, SLOTS = 0x200000, 0x384000, 194
PAGE = 8192
CART = {0x10000000+i*PAGE: hashlib.shake_256(
    ('sodium64-original-pager-'+str(i)).encode()).digest(PAGE) for i in range(97)}


def prove_probe_model():
    code = dict(enumerate(bytes.fromhex('42000008'), 0x1000))
    cases = 0
    for index in (0, 31):
        for asid, lo0, lo1, match in ((0x55, 0, 0, True), (0x33, 1, 1, True),
                                     (0x33, 1, 0, False), (0x33, 0, 1, False)):
            cpu = CPU(code.copy())
            cpu.tlb = [(0x80000000, 0, 0, 0)]*32
            cpu.tlb[index] = (0x1234000 | asid, lo0, lo1, 0)
            cpu.cp.update({5: 0, 10: 0x1234055})
            cpu.execute(0x80001000, stop=0x80001004)
            assert cpu.cp[0] == (index if match else 0x80000000), 'TLBP model truth table'
            cases += 1
    cpu.tlb[0] = cpu.tlb[31] = (0x1234055, 1, 1, 0)
    try:
        cpu.execute(0x80001000, stop=0x80001004)
    except AssertionError as error:
        assert 'multiple matches' in str(error)
    else:
        raise AssertionError('undefined multiple TLBP matches accepted')
    cpu.cp[5] = 0x6000
    try:
        cpu.execute(0x80001000, stop=0x80001004)
    except AssertionError as error:
        assert 'requires 4KiB pages' in str(error)
    else:
        raise AssertionError('out-of-scope TLBP page size accepted')
    return cases+2


class PagerCPU(CPU):
    def __init__(self, memory):
        super().__init__(memory.copy())
        self.allow_rcp_writes = True
        self.rdram = bytearray(0x200000)
        self.rdram[END-BASE:] = b'\xa5'*(0x400000-END)
        self.pending = None
        self.delay = 0
        self.transfers = []
        self.tlb = [(0x80000000, 0, 0, 0)]*32

    def read(self, address, size=4):
        physical = address & 0x1fffffff
        if physical == 0x04600010 and self.pending is not None:
            destination, cartridge, length, remaining = self.pending
            if remaining:
                self.pending = destination, cartridge, length, remaining-1
                return 1
            self.rdram[destination-BASE:destination-BASE+length] = CART[cartridge]
            self.pending = None
            return 0
        return super().read(address, size)

    def write(self, address, value, size=4):
        super().write(address, value, size)
        if address & 0x1fffffff == 0x0460000c:
            destination = super().read(0x04600000)
            cartridge = super().read(0x04600004)
            length = (value & 0xffffffff)+1
            assert self.pending is None, 'overlapping PI transfer'
            assert length == PAGE, 'PI refill length'
            assert BASE <= destination < destination+length <= END, 'PI refill escaped ROM owner'
            assert cartridge in CART, 'PI cartridge source'
            self.transfers.append((destination, cartridge, length))
            self.pending = destination, cartridge, length, self.delay


def check(memory, symbols):
    assert symbols['faithful_rom_cache_slots'] == SLOTS
    assert symbols['faithful_rom_cache_buffer'] == BASE
    cpu = PagerCPU(memory)
    requests = list(range(3*SLOTS))+list(range(64))
    guests = set(requests)
    expected = {guest: 0x10000000+(guest % 97)*PAGE for guest in guests}
    for guest, cartridge in expected.items():
        cpu.write(symbols['memory_map']+guest*4, cartridge)
    cpu.write(symbols['rom_pointer'], 0, 1)
    cpu.cp.update({0: 31, 5: 0})
    owners = [None]*SLOTS
    found = absent = cold = 0
    for ordinal, guest in enumerate(requests):
        cursor = ordinal % SLOTS
        old = owners[cursor]
        cartridge = expected[guest]
        assert cartridge in CART, 'test requested a still-resident page'
        initial_index = cpu.cp[0]
        cpu.pattern(ordinal)
        cpu.cp.update({2: 0x1111, 3: 0x2222, 8: guest*PAGE+(ordinal*137 & 8191),
                       10: guest*PAGE | 0x55, 12: 0x403, 13: 8, 14: 0x80012340})
        initial_hi = cpu.cp[10]
        victim_index = None
        if old is not None:
            victim, old_cartridge = old
            for index, entry in enumerate(cpu.tlb):
                if entry[0] & 0xffffe000 == victim*PAGE:
                    cpu.tlb[index] = (0x80000000, 0, 0, 0)
            if ordinal & 1:
                victim_index = (initial_index+7) & 31
                old_lo = ((BASE+cursor*PAGE) >> 6) | 0x1b
                cpu.tlb[victim_index] = (victim*PAGE | 0x33, old_lo, old_lo+0x40, 0)
                found += 1
            else:
                absent += 1
        else:
            cold += 1
        tlb = cpu.tlb.copy()
        if victim_index is not None:
            tlb[victim_index] = (0x80000000, 0x1111, 0x2222, 0)
        lo = ((BASE+cursor*PAGE) >> 6) | 0x1b
        tlb[initial_index] = (initial_hi, lo, lo+0x40, 0)
        initial, hi, low = cpu.regs.copy(), cpu.hi, cpu.lo
        cpu.memory_writes = []
        cpu.tlb_probes = []
        cpu.delay = (0, 1, 7)[ordinal % 3]

        def retired(c):
            assert c.pending is None, 'TLB published before PI completion'
        cpu.before_instruction[symbols['tlbl_set']] = retired
        assert cpu.execute(symbols['tlbl_exception'], max_steps=300) == 'eret'
        assert cpu.pending is None, 'PI transfer left pending'
        assert cpu.transfers[-1] == (BASE+cursor*PAGE, cartridge, PAGE), 'PI publication'
        assert cpu.rdram[cursor*PAGE:(cursor+1)*PAGE] == CART[cartridge], 'refilled page content'
        assert cpu.tlb == tlb, 'TLB victim/new mapping ownership'
        probes = [] if old is None else [(old[0]*PAGE, victim_index if victim_index is not None else 0x80000000)]
        assert cpu.tlb_probes == probes, 'victim probe path'
        assert cpu.cp[0] == (initial_index+1) & 31, 'TLB replacement index'
        assert cpu.cp[10] == initial_hi and cpu.cp[14] == 0x80012340 and cpu.cp[12] == 0x401, 'exception register ownership'
        assert all(cpu.regs[i] == initial[i] for i in range(32) if i not in (1, 4, 8, 9, 10, 11, 26, 27)), 'refill GPR ownership'
        assert (cpu.hi, cpu.lo) == (hi, low), 'refill HI/LO ownership'
        allowed = {(0x04600004, 4), (0x04600000, 4), (0x0460000c, 4),
                   (symbols['rom_pointer'] & 0x1fffffff, 1),
                   ((symbols['rom_entries']+cursor*4) & 0x1fffffff, 4),
                   ((symbols['rom_addrs']+cursor*4) & 0x1fffffff, 4),
                   ((symbols['memory_map']+guest*4) & 0x1fffffff, 4)}
        if old is not None:
            expected[old[0]] = old[1]
            assert cpu.read(symbols['memory_map']+old[0]*4) == old[1], 'evicted memory-map restoration'
            allowed.add(((symbols['memory_map']+old[0]*4) & 0x1fffffff, 4))
        assert all((at, size) in allowed for at, size, _ in cpu.memory_writes), 'refill wrote outside owned state'
        expected[guest] = lo
        owners[cursor] = guest, cartridge
        assert cpu.read(symbols['memory_map']+guest*4) == lo, 'new memory-map publication'
        assert cpu.read(symbols['rom_entries']+cursor*4) == cartridge, 'saved cartridge owner'
        assert cpu.read(symbols['rom_addrs']+cursor*4) == guest*4, 'saved virtual owner'
        assert cpu.read(symbols['rom_pointer'], 1) == (cursor+1) % SLOTS, 'ROM cursor rollover'
    assert all(cpu.read(symbols['memory_map']+guest*4) == value for guest, value in expected.items()), 'final map ownership'
    assert cpu.rdram[END-BASE:] == b'\xa5'*(0x400000-END), 'composition surface changed'
    for cursor, (guest, cartridge) in enumerate(owners):
        assert cpu.rdram[cursor*PAGE:(cursor+1)*PAGE] == CART[cartridge], 'resident page alias corruption'
    return {'refills': len(requests), 'cold': cold, 'victim_present': found,
            'victim_absent': absent, 'PI_bytes': len(requests)*PAGE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', nargs='+', type=Path)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    probe_cases = prove_probe_model()
    variants = []
    for path in args.elf:
        memory, symbols = load_elf(path)
        result = check(memory, symbols)
        addresses = range(symbols['tlbl_rom'], symbols['tlbl_io'], 4)
        probes = [at for at in addresses if word(memory, at) == 0x42000008]
        restores = [at for at in addresses if at < symbols['set_entry'] and word(memory, at) >> 26 == 43 and word(memory, at) >> 16 & 31 == 8]
        indexes = [at for at in addresses if word(memory, at) == (16 << 26 | 4 << 21 | 11 << 16)]
        waits = [at for at in addresses if word(memory, at) >> 26 == 5 and word(memory, at) >> 21 & 31 == 26 and word(memory, at) >> 16 & 31 == 0]
        lengths = [at for at in addresses if word(memory, at) >> 26 in (9, 13) and word(memory, at) >> 16 & 1023 == 27 and word(memory, at) & 65535 == 8191]
        assert all(len(x) == 1 for x in (probes, restores, indexes, waits, lengths)), 'linked refill anchors drifted'
        faults = [('missing_victim_probe', probes[0], 0),
                  ('missing_old_map_restore', restores[0], 0),
                  ('missing_index_restore', indexes[0], 0),
                  ('missing_PI_wait', waits[0], 0),
                  ('short_PI_refill', lengths[0], word(memory, lengths[0])-1)]
        rejected = []
        for name, address, value in faults:
            changed = memory.copy()
            put_word(changed, address, value)
            try:
                check(changed, symbols)
            except AssertionError as error:
                assert str(error) in ('TLB victim/new mapping ownership', 'victim probe path',
                    'evicted memory-map restoration', 'TLB replacement index',
                    'TLB published before PI completion', 'PI refill length'), str(error)
                rejected.append(name)
            else:
                raise AssertionError(('emitted refill fault escaped', name))
        variants.append({'elf': str(path), **result, 'faults_rejected': rejected})
    report = {'passed': True, 'TLBP_model_cases': probe_cases, 'variants': variants, 'physical_acceptance': False,
              'scope': 'Complete emitted refill/eviction with functional PI/TLB, delayed completion, alias/owner checks; no cache, bus timing or hazard model.'}
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
