#!/usr/bin/env python3
"""Execute linked SIG1 loader/CPU sampling with delayed overlay DMA.

Original numeric data only. Checks atomic SIG4..6 ownership, actual IMEM
replacement before publication, single-status IRQ classification, protocol
metadata and payload checksum. This does not model hardware timing/coherence.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols, parse, HEADER
from native_diag_v4 import SIGNAL_STAGES
from test_hcomp_sub_presence import section
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU
from test_native_diag_v4_report import make_blob, checksum, field

MASKS = (0x002A, 0x002C, 0x0032, 0x0034, 0x004A, 0x004C, 0x0052, 0x0054)
SIGNALS = 7 << 11
CONTROL_BITS = 0x007E0000
BUCKET = (1, 2, 3, 4, 6, 5, 3, 7)
SOURCE, EXIT = 0x140000, 0xABC


def status_write(status, mask):
    assert not mask & ~CONTROL_BITS, ('changed another SP control', hex(mask))
    for bit in range(3):
        clear, set_bit = 1 << (17 + bit * 2), 1 << (18 + bit * 2)
        assert bool(mask & clear) != bool(mask & set_bit), 'ambiguous clear/set pair'
        if mask & clear: status &= ~(1 << (11 + bit))
        if mask & set_bit: status |= 1 << (11 + bit)
    return status


class LoaderVM:
    def __init__(self, code, dmem, bank, previous, delay):
        self.code, self.dmem = bytearray(code), bytearray(dmem)
        self.source = bytes((i * 37 + bank * 19) & 255 for i in range(1000))
        self.r = [0x12340000 + i for i in range(32)]
        self.r[0], self.r[5], self.r[25] = 0, SOURCE | bank, EXIT
        self.status, self.original_status = previous, previous
        self.irq, self.semaphore = 1, 0x55
        self.pc, self.pending = 0xC60, None
        self.spaddr = self.ramaddr = 0
        self.delay, self.dma = delay, None
        self.writes, self.busy_polls, self.completed = [], 0, False

    def execute(self):
        for steps in range(1000):
            if self.pc == EXIT:
                assert self.pending is None and self.dma is None
                assert self.code[0x3A8:0x790] == self.source
                assert self.completed and len(self.writes) == 2
                assert self.writes[0] == (0x002A0000, False)
                assert self.writes[1][1], 'publication preceded DMA retirement'
                assert self.status & ~SIGNALS == self.original_status & ~SIGNALS
                assert (self.irq, self.semaphore) == (1, 0x55)
                return steps
            if self.dma:
                assert not 0x3A8 <= self.pc < 0x790, 'executing DMA target slot'
                assert self.status & SIGNALS == 0, 'published a bank during DMA'
            word = struct.unpack_from('>I', self.code, self.pc)[0]
            op, rs, rt, rd = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
            shift, fn, imm = word >> 6 & 31, word & 63, word & 65535
            signed = imm if imm < 32768 else imm - 65536
            target = None
            if op == 0:
                if fn == 0: self.r[rd] = self.r[rt] << shift
                elif fn == 8: target = self.r[rs] & 0xFFF
                elif fn == 36: self.r[rd] = self.r[rs] & self.r[rt]
                else: raise AssertionError(('RSP SPECIAL', hex(self.pc), hex(word)))
            elif op in (2, 3):
                if op == 3: self.r[31] = self.pc + 8
                target = word << 2 & 0xFFF
            elif op in (4, 5):
                if (self.r[rs] == self.r[rt]) == (op == 4): target = self.pc + 4 + (signed << 2) & 0xFFF
            elif op in (8, 9): self.r[rt] = self.r[rs] + signed
            elif op == 12: self.r[rt] = self.r[rs] & imm
            elif op == 15: self.r[rt] = imm << 16
            elif op in (37, 41):
                address = self.r[rs] + signed & 0xFFF
                if op == 37: self.r[rt] = int.from_bytes(self.dmem[address:address + 2], 'big')
                else:
                    assert address == 0xECA, 'loader wrote an unowned DMEM cell'
                    self.dmem[address:address + 2] = (self.r[rt] & 65535).to_bytes(2, 'big')
            elif op == 16:
                if rs == 0:
                    assert rd == 6
                    self.busy_polls += 1
                    if self.dma:
                        self.dma -= 1
                        if self.dma == 0:
                            self.code[0x3A8:0x790] = self.source
                            self.completed = True
                            self.dma = None
                    self.r[rt] = int(bool(self.dma))
                elif rs == 4:
                    if rd == 0: self.spaddr = self.r[rt]
                    elif rd == 1: self.ramaddr = self.r[rt]
                    elif rd == 2:
                        assert self.status & SIGNALS == 0 and len(self.writes) == 1
                        assert (self.spaddr, self.ramaddr, self.r[rt]) == (0x13A8, SOURCE, 999)
                        assert self.dma is None and not self.completed
                        self.dma = self.delay
                    elif rd == 4:
                        mask = self.r[rt]
                        if len(self.writes): assert self.completed and not self.dma, 'early bank publication'
                        self.status = status_write(self.status, mask)
                        self.writes.append((mask, self.completed))
                    else: raise AssertionError(('RSP CP0 write', rd))
                else: raise AssertionError(('RSP CP0', rs))
            else: raise AssertionError(('RSP opcode', hex(self.pc), hex(word)))
            assert self.pending is None or target is None, 'control transfer in delay slot'
            self.r[:] = [value & 0xFFFFFFFF for value in self.r]
            self.r[0] = 0
            self.pc, self.pending = self.pending if self.pending is not None else self.pc + 4, target
        raise AssertionError('loader did not return')


class SignalCPU(CPU):
    def __init__(self, memory, status):
        super().__init__(memory)
        self.status = status
        self.status_reads, self.status_writes = 0, []

    def read(self, address, size=4):
        physical = address & 0x1FFFFFFF
        assert not 0x04000000 <= physical < 0x04001000, 'SIG1 read live RSP DMEM'
        assert physical != 0x04080000, 'SIG1 read live RSP PC'
        if physical == 0x04040010:
            assert size == 4
            self.status_reads += 1
            return self.status
        return super().read(address, size)

    def write(self, address, value, size=4):
        if address & 0x1FFFFFFF == 0x04040010:
            assert size == 4
            self.status = status_write(self.status, value & 0xFFFFFFFF)
            self.status_writes.append(value & 0xFFFFFFFF)
        else: super().write(address, value, size)


def decoder_guard():
    blob = make_blob()
    field(blob, 'version', 5)
    field(blob, 'sp_status_after', 1)
    struct.pack_into('>2I', blob, HEADER + 0x1D8, 0, 0x53494731)
    struct.pack_into('>5I', blob, HEADER + 0x1E0, 0x434F4E35, 0, 0, 1, 1)
    for i in range(160):
        offset, bank = 0x6200 + i * 40, i % 8
        count = sum(blob[offset + 24:offset + 32])
        struct.pack_into('>H', blob, offset + 10, bank << 12)
        blob[offset + 32:offset + 40] = bytes(8)
        blob[offset + 32 + BUCKET[bank]] = count
    for i in range(20):
        struct.pack_into('>3H', blob, 0x7B00 + i * 64 + 50, 0, 0, 0)
    checksum(blob)
    result, _ = parse(blob)
    h = result['header']
    assert h['rsp_bank_protocol'] == 'SIG1' and h['rsp_bank_atomic_with_halt']
    assert h['continuous_capture'] and not h['rsp_live_pc_available']
    assert not h['rsp_resident_wait_counters_available']
    assert sum(h['rsp_stage_samples_total'].values()) == h['sample_count']
    assert tuple(h['rsp_stage_samples_total']) == SIGNAL_STAGES
    assert all(e['sp_pc_live'] is None and not e['sp_pc_recorded'] and e['rsp_bank_atomic_with_halt'] for e in result['events'])
    assert all(s['rsp_resident_wait_samples'] is None for s in result['seconds'])
    for kind in ('body_checksum', 'fake_pc', 'resident_counter', 'protocol'):
        bad = blob.copy()
        if kind == 'body_checksum': bad[0x6300] ^= 1
        elif kind == 'fake_pc': struct.pack_into('>H', bad, 0x620A, 0x1004); checksum(bad)
        elif kind == 'resident_counter': struct.pack_into('>H', bad, 0x7B32, 1); checksum(bad)
        else: struct.pack_into('>I', bad, HEADER + 0x1D8, 46875)
        try: parse(bad)
        except ValueError: pass
        else: raise AssertionError(('decoder accepted corrupt SIG1', kind))
    # Retain and exercise the original BAN4 decoder path as well.
    assert parse(make_blob())[0]['header']['rsp_bank_protocol'] == 'BAN4'
    return 6


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cpu', type=Path)
    ap.add_argument('main_rsp', type=Path)
    ap.add_argument('mode7_rsp', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    base, symbols = load_elf(args.cpu)
    _, main_code = read_text(args.main_rsp)
    _, mode7_code = read_text(args.mode7_rsp)
    dmem = section(args.main_rsp, '.data')
    ms = dict((name, address & 0xFFF) for address, name in elf_symbols(args.main_rsp))
    ws = dict((name, address & 0xFFF) for address, name in elf_symbols(args.mode7_rsp))
    assert len(main_code) == len(mode7_code) == len(dmem) == 4096
    assert ms['native_diag_overlay_load'] == ws['native_diag_overlay_load'] == 0xC60
    assert ms['native_diag_overlay_main_return'] == ws['native_diag_overlay_main_return'] == 0xC9C
    assert main_code[0xC60:0xC9C] == mode7_code[0xC60:0xC9C]
    assert ms['native_diag_signal_masks'] == 0xEFC
    assert struct.unpack_from('>8H', dmem, 0xEFC) == MASKS
    assert all(ms[name] == address for name, address in (('draw_frame', 0x03C), ('next_section', 0x0C0), ('dma_read', 0xF40), ('dma_wait', 0xF4C), ('rdp_send', 0xF5C)))
    cases = 0
    # Exercise every previous/next bank, both states of each preserved low
    # flag/other signal and three delayed DMA completion schedules.
    statuses = [flags | previous << 11 | other for previous in range(8)
                for flags in (0, 1, 0x7F)
                for other in (0, 0x4000, 0x780, 0x4780)]
    for code in (main_code, mode7_code):
        for bank in range(8):
            for previous in statuses:
                for delay in (1, 3, 11):
                    vm = LoaderVM(code, dmem, bank, previous, delay)
                    vm.execute()
                    assert vm.status >> 11 & 7 == bank
                    assert vm.writes[-1][0] == MASKS[bank] << 16
                    assert vm.busy_polls == delay
                    assert vm.dmem[:0xECA] == dmem[:0xECA] and vm.dmem[0xECC:] == dmem[0xECC:]
                    cases += 1
    state = symbols['native_diag_state']
    cpu_cases = 0
    for status in statuses:
        cpu = SignalCPU(base.copy(), status)
        for i in range(304): cpu.write(state + i, 0, 1)
        cpu.pattern(cpu_cases)
        before = cpu.regs.copy()
        cpu.execute(symbols['native_diag_sp_sample'], stop=symbols['native_diag_sp_counted'])
        assert cpu.status_reads == 1 and not cpu.status_writes
        assert cpu.read(state + 300) == status
        assert cpu.read(state + 84) == int(not status & 1)
        bucket = 0 if status & 1 else BUCKET[status >> 11 & 7]
        assert [cpu.read(state + 268 + i * 4) for i in range(8)] == [int(i == bucket) for i in range(8)]
        assert cpu.read(state + 264) == (0 if status & 1 else (status & SIGNALS) << 1)
        assert not any(cpu.read(state + off) for off in (236, 240, 244))
        assert all(cpu.regs[i] == before[i] for i in set(range(32)) - {26, 27})
        cpu_cases += 1
    irq_cases = 0
    for irq_status in (0x403, 0x1403, 0x9403, 0xFF03):
        for status in statuses:
            cpu = SignalCPU(base.copy(), status)
            for i in range(304): cpu.write(state + i, 0, 1)
            cpu.write(symbols['native_diag_continuous_mode'], 1)
            cpu.write(symbols['native_diag_phase'], 1)
            cpu.write(state + 16, 5859375) # Stay in the fast IRQ; no live PPU observation.
            cpu.pattern(irq_cases)
            cpu.cp.update({9: 131071, 12: irq_status, 14: symbols['native_diag_cpu_start']})
            before = cpu.regs.copy(), cpu.hi, cpu.lo
            assert cpu.execute(symbols['native_diag_interrupt']) == 'eret'
            assert cpu.status_reads == 1 and not cpu.status_writes
            assert cpu.cp[12] == irq_status & ~2 and cpu.cp[11] == 262142
            assert cpu.cp[14] == symbols['native_diag_cpu_start']
            assert (cpu.hi, cpu.lo) == before[1:]
            assert all(cpu.regs[i] == before[0][i] for i in set(range(32)) - {26, 27})
            bucket = 0 if status & 1 else BUCKET[status >> 11 & 7]
            assert [cpu.read(state + 268 + i * 4) for i in range(8)] == [int(i == bucket) for i in range(8)]
            irq_cases += 1
    for status in statuses:
        cpu = SignalCPU(base.copy(), status)
        cpu.pattern()
        cpu.execute(symbols['native_diag_signal_main_initial'], stop=symbols['native_diag_signal_main_initial_done'])
        assert cpu.status == status & ~SIGNALS | 1 << 11
        assert cpu.status_writes == [0x002C0000] and cpu.status_reads == 0
    cpu = SignalCPU(base.copy(), 0)
    cpu.regs[16] = 0x801F0000
    cpu.execute(symbols['native_diag_bank_protocol_header'], stop=symbols['native_diag_bank_protocol_header_done'])
    assert (cpu.read(0x801F01D8), cpu.read(0x801F01DC)) == (0, 0x53494731)
    proof = dict(result='PASS', protocol='SIG1', overlay_dma_cases=cases,
                 single_status_cpu_sample_cases=cpu_cases, initial_main_cases=len(statuses),
                 compiled_irq_state_cases=irq_cases,
                 decoder_protocol_checksum_cases=decoder_guard(),
                 loader_instruction_count=15, fixed_imem_entries_preserved=True,
                 unrelated_status_irq_semaphore_preserved=True,
                 live_pc_and_dmem_bank_reads_absent=True,
                 hardware_timing_or_access_coherence_proven=False,
                 elf_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (args.cpu, args.main_rsp, args.mode7_rsp)})
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof))


if __name__ == '__main__': main()
