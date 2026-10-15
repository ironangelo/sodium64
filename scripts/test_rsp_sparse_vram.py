#!/usr/bin/env python3
"""Execute linked RSP snapshot/overlay/DMA instructions against full VRAM.

Original numeric memory only. Delayed DMA checks buffer ownership, startup,
both queues and accumulated cache dirtiness; it does not model hardware cycles.
The independent output oracle is the complete current 64KiB guest VRAM image.
"""
import argparse
import hashlib
import json
import random
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_sub_presence import section

ROOT = Path(__file__).resolve().parents[1]
GUEST, SNAPSHOT = 0x110000, 0x122000
DIRTY1, DIRTY2 = 0x134000, 0x135000
MAIN_BANK, SETUP_BANK = 0x140000, 0x141000


class RspVM:
    def __init__(self, code, dmem, ram, regs, vectors, delay, snapshot_oracle):
        self.code, self.dmem, self.ram = bytearray(code), dmem, ram
        self.r, self.v = regs, vectors
        self.delay, self.snapshot_oracle = delay, snapshot_oracle
        self.pc, self.branch = 0x03C, None
        self.vco_hi, self.vco_lo, self.vcc = [True] * 8, [True] * 8, [False] * 8
        self.spaddr = self.ramaddr = 0
        self.dma = None
        self.transfers, self.semaphores = [], 0
        self.signal_profile = struct.unpack_from('>I', code, 0xC60)[0] == 0x3C08002A
        self.sp_status = 0x4780 | 1 << 11 | 0x40
        self.initial_sp_status, self.sp_irq = self.sp_status, 1
        self.signal_writes, self.completed_overlay_bank = [], None

    def write_status(self, mask):
        assert self.signal_profile and not mask & ~0x007E0000, 'unowned SP status control'
        before = self.sp_status
        for bit in range(3):
            clear, set_bit = 1 << (17 + bit * 2), 1 << (18 + bit * 2)
            assert bool(mask & clear) != bool(mask & set_bit), 'ambiguous clear/set pair'
            if mask & clear: self.sp_status &= ~(1 << (11 + bit))
            if mask & set_bit: self.sp_status |= 1 << (11 + bit)
        assert self.sp_status & ~(7 << 11) == before & ~(7 << 11)
        bank = self.sp_status >> 11 & 7
        if bank:
            assert self.dma is None and bank == self.completed_overlay_bank, 'bank published before correct overlay retired'
            self.completed_overlay_bank = None
        else:
            assert self.dma is None and self.completed_overlay_bank is None
        self.signal_writes.append(bank)
        assert self.sp_irq == 1

    def check_dmem(self, address, size, write=False):
        assert 0 <= address <= 4096 - size
        if self.dma is not None:
            pending = self.dma
            if not pending['imem']:
                overlap = address < pending['sp'] + pending['size'] and pending['sp'] < address + size
                assert not overlap, ('scratch reused before DMA completed', self.pc, address, size, write)

    def queue_dma(self, write, length):
        assert self.dma is None, 'synchronous helper queued a second DMA'
        assert length >> 12 == 0, 'unexpected DMA count/skip fields'
        size = ((length & 0xFFF) | 7) + 1
        sp, ram = self.spaddr & 0xFFF, self.ramaddr & 0x1FFFFFFF
        assert sp % 8 == ram % 8 == 0 and sp + size <= 4096
        assert ram + size <= len(self.ram)
        imem = bool(self.spaddr & 0x1000)
        assert not imem or not write
        if imem and self.signal_profile:
            assert self.sp_status & (7 << 11) == 0, 'bank remained published while overwriting IMEM'
            assert self.signal_writes[-1] == 0 and self.completed_overlay_bank is None
        self.dma = dict(write=write, imem=imem, sp=sp, ram=ram, size=size, polls=self.delay)

    def poll_dma(self):
        if self.dma is None:
            return 0
        self.dma['polls'] -= 1
        if self.dma['polls']:
            return 1
        pending = self.dma
        target = self.code if pending['imem'] else self.dmem
        sp, ram, size = pending['sp'], pending['ram'], pending['size']
        if pending['write']:
            self.ram[ram:ram + size] = target[sp:sp + size]
        else:
            target[sp:sp + size] = self.ram[ram:ram + size]
        self.transfers.append({k: v for k, v in pending.items() if k != 'polls'})
        if pending['imem'] and self.signal_profile:
            assert self.sp_status & (7 << 11) == 0
            assert pending['ram'] in (MAIN_BANK, SETUP_BANK)
            self.completed_overlay_bank = 1 if pending['ram'] == MAIN_BANK else 7
        self.dma = None
        return 0

    def execute(self):
        for steps in range(30000):
            if self.pc == 0x09C:
                assert self.branch is None and self.dma is None
                if self.signal_profile:
                    assert self.sp_status == self.initial_sp_status
                    assert self.signal_writes == [0, 7, 0, 1]
                    assert self.completed_overlay_bank is None
                return steps
            if self.dma is not None and self.dma['imem']:
                pending = self.dma
                assert not pending['sp'] <= self.pc < pending['sp'] + pending['size'], 'executing overwritten slot'
            word = struct.unpack_from('>I', self.code, self.pc)[0]
            op, rs, rt, rd = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
            fn, shift = word & 63, word >> 6 & 31
            immediate = word & 65535
            signed = immediate if immediate < 32768 else immediate - 65536
            target = None
            if op == 0:
                if fn == 0: self.r[rd] = self.r[rt] << shift
                elif fn == 2: self.r[rd] = self.r[rt] >> shift
                elif fn == 8: target = self.r[rs] & 0xFFF
                elif fn in (32, 33): self.r[rd] = self.r[rs] + self.r[rt]
                elif fn == 36: self.r[rd] = self.r[rs] & self.r[rt]
                elif fn == 37: self.r[rd] = self.r[rs] | self.r[rt]
                elif fn == 43: self.r[rd] = int(self.r[rs] < self.r[rt])
                else: raise AssertionError(('special', hex(self.pc), hex(word)))
            elif op in (2, 3):
                if op == 3: self.r[31] = self.pc + 8
                target = word << 2 & 0xFFF
            elif op in (4, 5):
                if (self.r[rs] == self.r[rt]) == (op == 4):
                    target = self.pc + 4 + (signed << 2) & 0xFFF
            elif op in (8, 9): self.r[rt] = self.r[rs] + signed
            elif op == 12: self.r[rt] = self.r[rs] & immediate
            elif op == 13: self.r[rt] = self.r[rs] | immediate
            elif op == 15: self.r[rt] = immediate << 16
            elif op in (35, 37, 41, 43):
                address = (self.r[rs] + signed) & 0xFFF
                size = 4 if op in (35, 43) else 2
                self.check_dmem(address, size, op >= 40)
                if op < 40:
                    self.r[rt] = int.from_bytes(self.dmem[address:address + size], 'big')
                else:
                    self.dmem[address:address + size] = (self.r[rt] & ((1 << (size * 8)) - 1)).to_bytes(size, 'big')
            elif op in (50, 58):
                element, operation = word >> 7 & 15, word >> 11 & 31
                offset = word & 127
                offset = offset if offset < 64 else offset - 128
                address = self.r[rs] + offset * 16 & 0xFFF
                assert operation == 4 and element == 0 and address % 16 == 0
                self.check_dmem(address, 16, op == 58)
                if op == 50: self.v[rt] = list(struct.unpack_from('>8H', self.dmem, address))
                else: struct.pack_into('>8H', self.dmem, address, *self.v[rt])
            elif op == 18 and rs == 2:
                assert rd == 1
                self.r[rt] = sum(int(flag) << i for i, flag in enumerate(self.vcc))
            elif op == 18 and rs & 16:
                assert rs & 15 == 0
                a, b, vd = self.v[rd][:], self.v[rt][:], shift
                if fn == 0x2A: result = [x | y for x, y in zip(a, b)]
                elif fn in (0x22, 0x23):
                    if fn == 0x22:
                        condition = [x != y or hi for x, y, hi in zip(a, b, self.vco_hi)]
                    else:
                        def s16(value): return value - 65536 if value & 32768 else value
                        condition = [s16(x) > s16(y) or (x == y and not (lo and hi))
                                     for x, y, lo, hi in zip(a, b, self.vco_lo, self.vco_hi)]
                    result = [x if flag else y for x, y, flag in zip(a, b, condition)]
                    self.vcc, self.vco_hi, self.vco_lo = condition, [False] * 8, [False] * 8
                else: raise AssertionError(('vector', hex(self.pc), hex(word)))
                self.v[vd] = result
            elif op == 16:
                if rs == 0:
                    assert rd in (6, 11)
                    self.r[rt] = self.poll_dma() if rd == 6 else 0
                elif rs == 4:
                    if rd == 0: self.spaddr = self.r[rt]
                    elif rd == 1: self.ramaddr = self.r[rt]
                    elif rd in (2, 3): self.queue_dma(rd == 3, self.r[rt])
                    elif rd == 4: self.write_status(self.r[rt])
                    elif rd == 7:
                        assert self.r[rt] == 0 and self.dma is None
                        assert self.ram[SNAPSHOT:SNAPSHOT + 65536] == self.snapshot_oracle, 'released CPU before complete snapshot'
                        self.semaphores += 1
                    else: raise AssertionError(('cop0 write', rd))
                else: raise AssertionError(('cop0', rs))
            else:
                raise AssertionError(('instruction', hex(self.pc), hex(word)))
            assert self.branch is None or target is None, 'control in control delay slot'
            self.r[:] = [value & 0xFFFFFFFF for value in self.r]
            self.r[0] = 0
            self.pc, self.branch = (self.branch if self.branch is not None else self.pc + 4), target
        raise AssertionError('snapshot did not finish')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('main', type=Path)
    parser.add_argument('setup', type=Path)
    parser.add_argument('--control', action='store_true', help='expect the compiled full-copy control')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    addr = parse_macros(ROOT).name
    main_base, main_code = read_text(args.main)
    setup_base, setup_code = read_text(args.setup)
    main_symbols = {name: address & 0xFFF for address, name in elf_symbols(args.main)}
    setup_symbols = {name: address & 0xFFF for address, name in elf_symbols(args.setup)}
    initial_dmem = section(args.main, '.data')
    assert len(main_code) == len(initial_dmem) == 4096 and len(setup_code) == 1000
    assert main_base & 0xFFF == 0 and setup_base & 0xFFF == 0x3A8
    assert main_symbols['draw_frame'] == 0x03C and main_symbols['vram_snapshot_return'] == 0x09C
    assert main_symbols['next_section'] == 0x0C0 and main_symbols['dma_read'] == 0xF40
    assert main_symbols['dma_write'] == 0xF08 and main_symbols['rdp_send'] == 0xF5C
    assert setup_symbols['hcomp_vram_snapshot'] == 0x628
    assert setup_symbols['hcomp_screen_switch'] == 0x760 and setup_symbols['draw_mode7_entry'] == 0x788
    ready = addr('HCOMP_VRAM_SNAPSHOT_READY')
    assert ready == 0xF2C and ready >= addr('OVERLAY_HCOMP_FAST_SRC') + 4
    assert ready + 4 <= addr('HCOMP_PROOF_RDP_CMDS')
    assert initial_dmem[ready:ready + 4] == bytes(4)
    original = bytes((i * 37 + i // 4096 * 11) & 255 for i in range(65536))
    rng = random.Random(0x5356524D)
    patterns = [bytes(1024), bytes([31]) * 1024]
    # Every dirty64-byte block is independently exercised, including all
    # positions within every1KiB group and both halves of the64-bit bitmap.
    for index in range(1024):
        dirty = bytearray(1024)
        dirty[index] = (1, 2, 4, 8, 16, 31)[index % 6]
        patterns.append(bytes(dirty))
    patterns.extend(bytes(rng.randrange(32) if rng.randrange(100) < density else 0
                          for _ in range(1024)) for density in (1, 10, 50, 100))
    statistics = []

    def run_case(dirty, first, slot, case_id):
        dmem = bytearray(initial_dmem)
        ram = bytearray(0x142000)
        guest = bytearray(original)
        for index, changed in enumerate(dirty):
            if changed:
                start = index * 64
                guest[start:start + 64] = bytes(value ^ ((case_id % 255) + 1)
                                               for value in guest[start:start + 64])
        ram[GUEST:GUEST + 65536] = guest
        ram[SNAPSHOT:SNAPSHOT + 65536] = bytes([0xA5]) * 65536 if first else original
        ram[SNAPSHOT - 32:SNAPSHOT] = bytes([0x5A]) * 32
        ram[SNAPSHOT + 65536:SNAPSHOT + 65568] = bytes([0x5A]) * 32
        ram[DIRTY1:DIRTY1 + 1024] = bytes([0xA5]) * 1024
        ram[DIRTY2:DIRTY2 + 1024] = bytes([0xA5]) * 1024
        dirty_address = DIRTY1 if slot == 0 else DIRTY2
        ram[dirty_address:dirty_address + 1024] = dirty
        ram[MAIN_BANK:MAIN_BANK + 1000] = main_code[0x3A8:0x790]
        ram[SETUP_BANK:SETUP_BANK + 1000] = setup_code
        for name, value in (('VRAM_ADDRS', SNAPSHOT), ('VRAM_ADDRS_PLUS_SOURCE', GUEST),
                            ('OVERLAY_MAIN_SRC', MAIN_BANK | 1),
                            ('OVERLAY_HCOMP_SETUP_SRC', SETUP_BANK | 7)):
            offset = addr('VRAM_ADDRS') + 4 if name == 'VRAM_ADDRS_PLUS_SOURCE' else addr(name)
            struct.pack_into('>I', dmem, offset, value)
        struct.pack_into('>II', dmem, addr('DIRTY_PTR'), DIRTY1, DIRTY2)
        struct.pack_into('>I', dmem, ready, 0 if first else 1)
        prior_dirty = bytes(rng.randrange(32) for _ in range(1024))
        dmem[addr('VRAM_TABLE'):addr('VRAM_TABLE') + 1024] = prior_dirty
        before_dmem = bytes(dmem)
        registers = [0xCAFE0000 + i for i in range(32)]
        registers[0], registers[29] = 0, slot
        vectors = [[rng.randrange(65536) for _ in range(8)] for _ in range(32)]
        vectors[31] = [0] * 8
        vector_constants = [vector[:] for vector in vectors[23:32]]
        vm = RspVM(main_code, dmem, ram, registers, vectors, (case_id % 3) + 1, guest)
        steps = vm.execute()
        assert ram[SNAPSHOT:SNAPSHOT + 65536] == guest
        assert ram[GUEST:GUEST + 65536] == guest
        assert ram[dirty_address:dirty_address + 1024] == dirty
        assert ram[SNAPSHOT - 32:SNAPSHOT] == ram[SNAPSHOT + 65536:SNAPSHOT + 65568] == bytes([0x5A]) * 32
        assert dmem[addr('VRAM_TABLE'):addr('VRAM_TABLE') + 1024] == bytes(x | y for x, y in zip(prior_dirty, dirty))
        permitted = set(range(addr('TILE_TABLE'), addr('VRAM_TABLE') + 1024))
        if args.control:
            # The exact historical control compares its loop pointer before
            # the delay-slot increment and writes a65th vector into OAM.
            # Measure precisely that legacy behavior, never permit it in the
            # sparse candidate or weaken the complete64KiB VRAM oracle.
            oam = addr('OAM')
            combined = bytes(x | y for x, y in zip(prior_dirty[:16], dirty[:16]))
            assert dmem[oam:oam + 16] == bytes(x | y for x, y in zip(before_dmem[oam:oam + 16], combined))
            permitted.update(range(oam, oam + 16))
        else:
            permitted.update(range(ready, ready + 4))
            permitted.update(range(addr('NATIVE_DIAG_RSP_BANK'), addr('NATIVE_DIAG_RSP_BANK') + 2))
        assert all(dmem[i] == before_dmem[i] for i in range(4096) if i not in permitted), 'DMEM owner changed'
        assert vm.code == main_code, 'Main slot did not restore exactly'
        assert vectors[23:32] == vector_constants and registers[29] == slot
        assert vm.semaphores == 1
        expected_groups = list(range(63, -1, -1)) if first or args.control else [
            group for group in range(63, -1, -1) if any(dirty[group * 16:group * 16 + 16])]
        reads = [transfer for transfer in vm.transfers if not transfer['imem'] and not transfer['write']
                 and GUEST <= transfer['ram'] < GUEST + 65536]
        writes = [transfer for transfer in vm.transfers if transfer['write']]
        assert [(transfer['ram'] - GUEST) // 1024 for transfer in reads] == expected_groups
        assert [(transfer['ram'] - SNAPSHOT) // 1024 for transfer in writes] == expected_groups
        assert all(transfer['size'] == 1024 for transfer in reads + writes)
        overlay_reads = [transfer for transfer in vm.transfers if transfer['imem']]
        assert len(overlay_reads) == (0 if args.control else 2)
        dirty_reads = [transfer for transfer in vm.transfers if transfer['ram'] == dirty_address]
        assert len(dirty_reads) == 1 and dirty_reads[0]['size'] == 1024
        if not args.control:
            assert int.from_bytes(dmem[ready:ready + 4], 'big') == 1
        return (dict(first=first, slot=slot, copied_groups=len(reads), vram_dma_bytes=2048 * len(reads),
                     total_dma_bytes=sum(transfer['size'] for transfer in vm.transfers), instructions=steps), vm)

    for slot in (0, 4):
        for dirty in (bytes(1024), bytes([31]) * 1024, patterns[2], patterns[1025]):
            statistics.append(run_case(dirty, True, slot, len(statistics))[0])
    for i, dirty in enumerate(patterns):
        statistics.append(run_case(dirty, False, (i & 1) * 4, len(statistics))[0])
    # Repeated empty captures have dirty cache bits left from previous frames,
    # but no guest VRAM modification and therefore must perform no VRAM DMA.
    for slot in (0, 4):
        statistics.append(run_case(bytes(1024), False, slot, len(statistics))[0])
    # Continue the same actual machine state rather than reconstructing a
    # ready flag. Alternate handed queues while previous mutations survive.
    initial_case, previous = run_case(bytes(1024), True, 0, len(statistics))
    statistics.append(initial_case)
    sequence_frames = 0
    for frame in range(16):
        slot = (frame & 1) * 4
        dirty = bytearray(1024)
        if frame % 4:
            for index in (0, 15, 16, 511, 512, 1023):
                dirty[(index + frame * 17) % 1024] = 31
        guest = bytearray(previous.ram[GUEST:GUEST + 65536])
        for index, changed in enumerate(dirty):
            if changed:
                offset = index * 64
                guest[offset:offset + 64] = bytes(value ^ (frame + 1) for value in guest[offset:offset + 64])
        previous.ram[GUEST:GUEST + 65536] = guest
        dirty_address = DIRTY1 if slot == 0 else DIRTY2
        previous.ram[dirty_address:dirty_address + 1024] = dirty
        prior_dirty = bytes(previous.dmem[addr('VRAM_TABLE'):addr('VRAM_TABLE') + 1024])
        previous.r[29] = slot
        vm = RspVM(main_code, previous.dmem, previous.ram, previous.r, previous.v, 3, guest)
        steps = vm.execute()
        assert vm.ram[SNAPSHOT:SNAPSHOT + 65536] == guest
        assert vm.dmem[addr('VRAM_TABLE'):addr('VRAM_TABLE') + 1024] == bytes(x | y for x, y in zip(prior_dirty, dirty))
        assert vm.semaphores == 1 and vm.code == main_code
        copies = [transfer for transfer in vm.transfers if transfer['write']]
        expected_count = 64 if args.control else sum(any(dirty[group * 16:group * 16 + 16]) for group in range(64))
        assert len(copies) == expected_count
        assert vm.ram[SNAPSHOT - 32:SNAPSHOT] == vm.ram[SNAPSHOT + 65536:SNAPSHOT + 65568] == bytes([0x5A]) * 32
        assert vm.r[29] == slot and vm.v[23:32] == previous.v[23:32]
        statistics.append(dict(first=False, slot=slot, copied_groups=len(copies),
                               vram_dma_bytes=2048 * len(copies),
                               total_dma_bytes=sum(transfer['size'] for transfer in vm.transfers), instructions=steps))
        previous = vm
        sequence_frames += 1
    clean = [case for case in statistics if not case['first'] and case['copied_groups'] == (64 if args.control else 0)]
    report = dict(passed=True, cases=len(statistics), control_full_copy=args.control,
                  signal_profile=previous.signal_profile,
                  signal_bank_publication_after_overlay_dma=previous.signal_profile,
                  main_elf_sha256=hashlib.sha256(args.main.read_bytes()).hexdigest(),
                  setup_elf_sha256=hashlib.sha256(args.setup.read_bytes()).hexdigest(),
                  all_dirty_64byte_blocks=1024, full_vram_bytes_compared=65536 * len(statistics),
                  queues=[0, 4], dirty_or_exact=True, initial_full_copy_independent=True,
                  continuous_state_frames=sequence_frames,
                  dmem_owners_preserved=not args.control,
                  legacy_control_oam_overrun_bytes=16 if args.control else 0,
                  legacy_control_oam_overrun_or_exact=args.control,
                  main_slot_restored=True, dma_completion_before_reuse=True,
                  cpu_semaphore_release_after_snapshot=True, stale_vector_carry_covered=True,
                  clean_frame_total_dma_bytes=min(case['total_dma_bytes'] for case in clean),
                  dirty_frame_max_total_dma_bytes=max(case['total_dma_bytes'] for case in statistics),
                  max_instructions=max(case['instructions'] for case in statistics),
                  native_timing_authority=False, private_inputs=False)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('RSP_SPARSE_VRAM_COMPILED PASS', json.dumps(report))


if __name__ == '__main__':
    main()
