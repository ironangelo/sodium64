#!/usr/bin/env python3
"""Execute compiled continuous recorder control with original data and a mocked transport.

The real transport has separate SD/error/uniqueness tests. This scalar MIPS VM
executes the linked recorder, including IRQ seal and safe-boundary service;
it is not a hardware timing, cache, SD or complete renderer implementation.
"""
import argparse
import json
from pathlib import Path

from test_native_diag_arm import load_elf

MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1
RETURN = 0xDEAD0000
HZ = 46875000
LIMIT = 20 * HZ
SAMPLE = 131071
READY, RECORDING, SEALED, COMMITTING, ERROR, EXHAUSTED = range(6)


def signed(value, width=64):
    value &= (1 << width) - 1
    return value if value < 1 << (width - 1) else value - (1 << width)


def sx32(value):
    return signed(value, 32) & MASK64


class CPU:
    """Small architectural interpreter: fail on unhandled instructions or RCP writes."""

    def __init__(self, memory):
        self.memory = memory
        self.regs = [0] * 32
        self.cp = {9: 0, 11: 0, 12: 0x401, 13: 0, 14: 0x80012340}
        self.hi = 0x13579BDF2468ACE0
        self.lo = 0xFEDCBA9876543210
        self.cp_writes = []
        self.memory_writes = []
        self.cache_ops = []
        self.hooks = {}
        self.before_instruction = {}
        self.allow_rcp_writes = False
        self.steps = 0

    def read(self, address, size=4):
        address &= 0x1FFFFFFF
        assert address != 0x0404001C, 'recorder acquired the SP semaphore'
        return int.from_bytes(bytes(self.memory.get(address + i, 0)
                                    for i in range(size)), 'big')

    def write(self, address, value, size=4):
        address &= 0x1FFFFFFF
        if 0x04000000 <= address < 0x05000000:
            assert self.allow_rcp_writes, ('continuous path wrote RCP', hex(address), hex(value))
        value &= (1 << (8 * size)) - 1
        self.memory_writes.append((address, size, value))
        # Model legacy SET_HALT becoming an observed HALT, only in terminal tests.
        if address == 0x04040010 and value == 2:
            value = 1
        for i, byte in enumerate(value.to_bytes(size, 'big')):
            self.memory[address + i] = byte

    def blob(self, address, size):
        address &= 0x1FFFFFFF
        return bytes(self.memory.get(address + i, 0) for i in range(size))

    def pattern(self, ordinal=0):
        self.regs = [(0xABCDEF0000000000 + (i + ordinal) * 0x123456789) & MASK64
                     for i in range(32)]
        self.regs[0] = 0
        self.regs[29] = sx32(0x807F0000)
        self.regs[31] = sx32(RETURN)

    def execute(self, entry, stop=RETURN, max_steps=200000):
        pc = entry & MASK32
        pending = None
        for step in range(max_steps):
            self.steps += 1
            if pc == stop:
                return 'return'
            if pc in self.hooks:
                assert pending is None, 'hook entered in a delay slot'
                caller_return = self.regs[31] & MASK32
                self.hooks[pc](self)
                self.regs[0] = 0
                pc = caller_return
                continue
            if pc in self.before_instruction:
                assert pending is None, 'instruction injection in delay slot'
                self.before_instruction.pop(pc)(self)
            word = self.read(pc)
            op, rs, rt, rd = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
            imm, shamt, fn = word & 65535, word >> 6 & 31, word & 63
            offset = signed(imm, 16)
            target = None
            r = self.regs
            if op == 0:
                if fn == 0: r[rd] = sx32((r[rt] & MASK32) << shamt)
                elif fn == 2: r[rd] = sx32((r[rt] & MASK32) >> shamt)
                elif fn == 3: r[rd] = sx32(signed(r[rt], 32) >> shamt)
                elif fn == 4: r[rd] = sx32((r[rt] & MASK32) << (r[rs] & 31))
                elif fn == 6: r[rd] = sx32((r[rt] & MASK32) >> (r[rs] & 31))
                elif fn == 7: r[rd] = sx32(signed(r[rt], 32) >> (r[rs] & 31))
                elif fn == 8: target = r[rs] & MASK32
                elif fn == 9:
                    target = r[rs] & MASK32
                    r[rd] = sx32(pc + 8)
                elif fn == 15: pass  # SYNC has no timing model.
                elif fn == 16: r[rd] = self.hi
                elif fn == 17: self.hi = r[rs]
                elif fn == 18: r[rd] = self.lo
                elif fn == 19: self.lo = r[rs]
                elif fn in (24, 25):
                    product = (signed(r[rs], 32) * signed(r[rt], 32) if fn == 24
                               else (r[rs] & MASK32) * (r[rt] & MASK32)) & MASK64
                    self.lo, self.hi = sx32(product), sx32(product >> 32)
                elif fn in (32, 33): r[rd] = sx32(r[rs] + r[rt])
                elif fn in (34, 35): r[rd] = sx32(r[rs] - r[rt])
                elif fn == 36: r[rd] = r[rs] & r[rt]
                elif fn == 37: r[rd] = r[rs] | r[rt]
                elif fn == 38: r[rd] = r[rs] ^ r[rt]
                elif fn == 39: r[rd] = ~(r[rs] | r[rt]) & MASK64
                elif fn == 42: r[rd] = int(signed(r[rs]) < signed(r[rt]))
                elif fn == 43: r[rd] = int(r[rs] < r[rt])
                elif fn in (44, 45): r[rd] = (r[rs] + r[rt]) & MASK64
                elif fn in (46, 47): r[rd] = (r[rs] - r[rt]) & MASK64
                elif fn == 56: r[rd] = (r[rt] << shamt) & MASK64
                elif fn == 58: r[rd] = r[rt] >> shamt
                elif fn == 59: r[rd] = (signed(r[rt]) >> shamt) & MASK64
                elif fn == 60: r[rd] = (r[rt] << (shamt + 32)) & MASK64
                elif fn == 62: r[rd] = r[rt] >> (shamt + 32)
                elif fn == 63: r[rd] = (signed(r[rt]) >> (shamt + 32)) & MASK64
                else: raise AssertionError(('unhandled SPECIAL', hex(pc), hex(word)))
            elif op in (2, 3):
                if op == 3: r[31] = sx32(pc + 8)
                target = ((pc + 4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2)
            elif op == 1:
                assert rt in (0, 1), ('unhandled REGIMM', hex(pc), hex(word))
                if (signed(r[rs]) < 0) == (rt == 0): target = pc + 4 + (offset << 2)
            elif op in (4, 5):
                if (r[rs] == r[rt]) == (op == 4): target = pc + 4 + (offset << 2)
            elif op in (6, 7):
                if (signed(r[rs]) <= 0) == (op == 6): target = pc + 4 + (offset << 2)
            elif op in (8, 9): r[rt] = sx32(r[rs] + offset)
            elif op == 10: r[rt] = int(signed(r[rs]) < offset)
            elif op == 11: r[rt] = int(r[rs] < (offset & MASK64))
            elif op == 12: r[rt] = r[rs] & imm
            elif op == 13: r[rt] = r[rs] | imm
            elif op == 14: r[rt] = r[rs] ^ imm
            elif op == 15: r[rt] = sx32(imm << 16)
            elif op == 16:
                if word == 0x42000018:
                    assert pending is None, 'ERET in delay slot'
                    self.cp[12] &= ~2
                    return 'eret'
                if rs == 0:
                    value = self.cp.get(rd, 0)
                    r[rt] = sx32(value(self.steps) if callable(value) else value)
                elif rs == 4:
                    self.cp[rd] = r[rt] & MASK32
                    self.cp_writes.append((rd, r[rt] & MASK32))
                else: raise AssertionError(('unhandled COP0', hex(pc), hex(word)))
            elif op in (24, 25): r[rt] = (r[rs] + offset) & MASK64
            elif op in (32, 33, 35, 36, 37, 39, 40, 41, 43, 55, 63):
                address = (r[rs] + offset) & MASK32
                size = 8 if op in (55, 63) else 4 if op in (35, 39, 43) else 2 if op in (33, 37, 41) else 1
                if op in (32, 33, 35, 36, 37, 39, 55):
                    value = self.read(address, size)
                    r[rt] = (signed(value, size * 8) & MASK64) if op in (32, 33, 35) else value
                else: self.write(address, r[rt], size)
            elif op == 47: self.cache_ops.append((rt, (r[rs] + offset) & MASK32))
            else: raise AssertionError(('unhandled opcode', hex(pc), hex(word)))
            assert pending is None or target is None, 'control transfer in delay slot'
            r[:] = [v & MASK64 for v in r]
            r[0] = 0
            pc = (pending if pending is not None else pc + 4) & MASK32
            pending = target & MASK32 if target is not None else None
        raise AssertionError(('compiled path did not terminate', hex(pc), max_steps))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    base, symbols = load_elf(args.elf)
    required = ('native_diag_init', 'native_diag_arm', 'native_diag_interrupt',
                'native_diag_frame_complete', 'native_diag_service',
                'native_diag_continuous_mode', 'native_diag_phase',
                'native_diag_notice_count', 'native_diag_ok_deadline',
                'native_diag_sealed_wait_stall',
                'continuous_save_available', 'continuous_save_capture_bridge',
                'continuous_save_capture')
    assert all(name in symbols for name in required), 'continuous trace ELF required'
    state = symbols['native_diag_state'] & 0x1FFFFFFF
    sram = symbols['sram'] & 0x1FFFFFFF
    phase = symbols['native_diag_phase'] & 0x1FFFFFFF
    mode = symbols['native_diag_continuous_mode'] & 0x1FFFFFFF
    guest = bytes((i * 43 + 7) & 255 for i in range(0x2000))
    commits = []
    cases = 0

    def fresh(now, status, availability=1):
        cpu = CPU(base.copy())
        cpu.guest = guest
        for i, value in enumerate(guest + bytes([0xAB]) * 0x6000):
            cpu.memory[sram + i] = value
        cpu.write(symbols['continuous_save_available'], availability)
        cpu.cp.update({9: now, 11: 0xDEADBEEF, 12: status})
        cpu.pattern()
        cpu.execute(symbols['native_diag_init'])
        assert cpu.cp[11] == 0xDEADBEEF, 'init armed timer'
        assert cpu.blob(sram, 0x2000) == cpu.guest
        assert cpu.blob(sram + 0x2000, 0x6000) == bytes(0x6000)
        cpu.cp_writes.clear()
        cpu.memory_writes.clear()
        return cpu

    def call(cpu, name, ordinal=0):
        cpu.pattern(ordinal)
        before = (cpu.regs.copy(), cpu.hi, cpu.lo, cpu.cp[12])
        result = cpu.execute(symbols[name])
        return before, result

    def preserve(cpu, before, excluded=(26, 27)):
        regs, hi, lo, status = before
        corrupt = [(i, hex(regs[i]), hex(cpu.regs[i]))
                   for i in set(range(32)) - set(excluded) if cpu.regs[i] != regs[i]]
        assert not corrupt, ('64-bit caller GPR corruption', corrupt)
        assert (cpu.hi, cpu.lo) == (hi, lo), 'HI/LO corruption'
        assert cpu.cp[12] == status, 'Status/EXL corruption'

    def bridge(cpu, outcome=1, terminal=False):
        assert cpu.read(phase) == (SEALED if terminal else COMMITTING)
        assert cpu.regs[4] & MASK32 == (symbols['sram'] | 0x20000000) & MASK32
        assert cpu.regs[5] == 32768
        assert cpu.cp[12] & 1 == 0, 'transport entered with interrupts enabled'
        payload = cpu.blob(sram, 0x8000)
        assert payload[:0x2000] == cpu.guest
        assert int.from_bytes(payload[0x2000:0x2004], 'big') == 0x53363444
        assert int.from_bytes(payload[0x2004:0x2008], 'big') == 5
        assert int.from_bytes(payload[0x2008:0x200C], 'big') == 1
        checksum = sum(int.from_bytes(payload[i:i + 4], 'big')
                       for lo, hi in ((0, 0x2000), (0x2200, 0x8000))
                       for i in range(lo, hi, 4)) & MASK32
        assert int.from_bytes(payload[0x20F0:0x20F4], 'big') == checksum
        commits.append(payload)
        # Model the ABI's allowed volatile and HI/LO clobbers. SD protocol,
        # allocation/readback and failure injection are tested in real C code.
        for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25, 26, 27):
            cpu.regs[i] = (0x65432100ABCDEF00 + i) & MASK64
        cpu.hi, cpu.lo = 0x0102030405060708, 0x8877665544332211
        cpu.cp[9] = (cpu.cp[9] + HZ // 4) & MASK32  # Simulated synchronous SD pause.
        cpu.regs[2] = sx32(outcome)

    def arm(cpu, now, ordinal):
        # Retired payload must be cleaned in full, not merely reset cursors.
        for i in range(0x6000): cpu.memory[sram + 0x2000 + i] = (i * 17 + 0xA5) & 255
        cpu.cp[9] = now
        before, result = call(cpu, 'native_diag_arm', ordinal)
        assert result == 'return' and cpu.read(phase) == RECORDING
        preserve(cpu, (before[0], before[1], before[2], before[3] | 0x8000), (8, 9, 10, 11, 26, 27))
        assert cpu.read(state) == now and cpu.read(state + 112) == 1
        assert cpu.cp[11] == (now + SAMPLE) & MASK32
        assert cpu.blob(sram, 0x2000) == cpu.guest
        assert cpu.blob(sram + 0x2000, 0x6000) == bytes(0x6000)
        snapshot = cpu.blob(state, 320), cpu.blob(sram, 0x8000), cpu.cp[11]
        call(cpu, 'native_diag_arm', ordinal + 1)
        assert snapshot == (cpu.blob(state, 320), cpu.blob(sram, 0x8000), cpu.cp[11]), 'held Start rearmed'

    def seal(cpu, start, ordinal):
        # First complete boundary excludes the pre-arm partial interval.
        cpu.cp[9] = (start + 800000) & MASK32
        call(cpu, 'native_diag_frame_complete', ordinal)
        assert cpu.read(state + 212) == 0 and cpu.read(state + 216) == 1
        cpu.write(state + 204, 3100)
        cpu.write(state + 208, 4700)
        cpu.cp[9] = (start + 1600000) & MASK32
        call(cpu, 'native_diag_frame_complete', ordinal + 1)
        assert cpu.read(state + 212) == 1
        # A timer sample immediately before the 20 s limit must still return
        # to RECORDING. This also exercises the wrap-safe comparison's edge.
        before_limit = (start + LIMIT - 1) & MASK32
        cpu.cp.update({9: before_limit, 12: cpu.cp[12] | 3,
                       14: symbols['native_diag_cpu_start']})
        cpu.write(state + 16, before_limit)
        before, result = call(cpu, 'native_diag_interrupt', ordinal + 2)
        assert result == 'eret' and cpu.read(phase) == RECORDING
        preserve(cpu, (before[0], before[1], before[2], before[3] & ~2), (26, 27))
        assert cpu.read(state + 112) == 1, 'capture sealed before the limit'
        cutoff = (start + LIMIT + 17) & MASK32
        cpu.cp.update({9: cutoff, 12: cpu.cp[12] | 3, 14: symbols['native_diag_cpu_start']})
        cpu.write(state + 16, cutoff)  # Exercise the real slow-IRQ limit branch.
        before, result = call(cpu, 'native_diag_interrupt', ordinal + 2)
        assert result == 'eret' and cpu.read(phase) == SEALED
        preserve(cpu, (before[0], before[1], before[2], (before[3] & ~0x8000) & ~2), (26, 27))
        assert cpu.read(state + 112) == 0, 'sealed interval stayed armed'
        assert cpu.read(sram + 0x2004) == 5 and cpu.read(sram + 0x2008) == 0
        assert cpu.read(sram + 0x200C) == 2
        assert cpu.read(sram + 0x2000 + 0x1E4) == cutoff
        assert cpu.read(sram + 0x2000 + 52) == LIMIT + 17
        frozen = cpu.blob(sram, 0x8000)
        cpu.cp[9] = (cutoff + 1700000) & MASK32
        call(cpu, 'native_diag_frame_complete', ordinal + 3)
        assert cpu.blob(sram, 0x8000) == frozen, 'post-cutoff frame mutated retained interval'
        assert cpu.read(state + 212) == 1
        call(cpu, 'native_diag_arm', ordinal + 4)
        assert cpu.blob(sram, 0x8000) == frozen and cpu.read(phase) == SEALED
        return cutoff

    # Repeated capture stays within the same guest session; Count wrapping and
    # TLB-style EXL states are deliberately varied at arm and service boundaries.
    for initial_count in (0, 0x12345678, 0xFFFF0000):
        for status in (0x401, 0x403, 0x9401, 0x9403):
            cpu = fresh(initial_count, status)
            assert cpu.read(mode) == 1 and cpu.read(phase) == READY
            cpu.hooks[symbols['continuous_save_capture']] = bridge
            for ordinal in range(3):
                # Model normal guest SRAM progress between captures. A rearm
                # must retain the new value, rather than reinstalling boot data.
                cpu.guest = bytes((i * 43 + 7 + ordinal) & 255 for i in range(0x2000))
                for i, value in enumerate(cpu.guest): cpu.memory[sram + i] = value
                now = (initial_count + ordinal * (LIMIT + 2 * HZ + 7000000)) & MASK32
                arm(cpu, now, ordinal * 10)
                cutoff = seal(cpu, now, ordinal * 10 + 2)
                cpu.cp[9] = (cutoff + 1700000) & MASK32
                # The compiled UI caller excludes IRQs before service entry.
                cpu.cp[12] = status & ~1
                service_count = cpu.cp[9]
                retained_body = cpu.blob(sram + 0x2200, 0x5E00)
                before, result = call(cpu, 'native_diag_service', ordinal * 10 + 8)
                assert result == 'return'
                preserve(cpu, before)
                assert cpu.read(phase) == READY
                assert cpu.read(symbols['native_diag_notice_count']) == ordinal + 1
                assert cpu.read(symbols['native_diag_ok_deadline']) == (cpu.cp[9] + 2 * HZ) & MASK32
                assert cpu.blob(sram, 0x2000) == cpu.guest
                assert cpu.read(sram + 0x2000 + 0x1E8) == service_count
                assert cpu.read(sram + 0x2000 + 76) == cutoff
                assert cpu.read(sram + 0x2000 + 52) == LIMIT + 17
                assert cpu.blob(sram + 0x2200, 0x5E00) == retained_body
                committed = cpu.blob(sram, 0x8000)
                before, _ = call(cpu, 'native_diag_service', ordinal * 10 + 9)
                preserve(cpu, before)
                assert cpu.blob(sram, 0x8000) == committed, 'READY service rewrote payload'
                cases += 1
            assert not any(0x04000000 <= address < 0x05000000
                           for address, _, _ in cpu.memory_writes)

    for outcome, terminal_phase in ((0, ERROR), (-1, EXHAUSTED)):
        for status in (0x401, 0x403, 0x9401, 0x9403):
            cpu = fresh(0xFFFF0000, status)
            cpu.hooks[symbols['continuous_save_capture']] = lambda c, result=outcome: bridge(c, result)
            arm(cpu, 0xFFFF0000, 100)
            cutoff = seal(cpu, 0xFFFF0000, 102)
            cpu.cp[9] = (cutoff + 1700000) & MASK32
            cpu.cp[12] = status & ~1
            before, _ = call(cpu, 'native_diag_service', 108)
            preserve(cpu, before)
            assert cpu.read(phase) == terminal_phase
            frozen, deadline = cpu.blob(sram, 0x8000), cpu.cp[11]
            before, _ = call(cpu, 'native_diag_service', 109)
            preserve(cpu, before)
            call(cpu, 'native_diag_arm', 110)
            assert cpu.blob(sram, 0x8000) == frozen and cpu.cp[11] == deadline
            assert cpu.read(phase) == terminal_phase, 'save failure allowed rearm'
            cases += 1

    # Execute the real O64 bridge with Sodium's queue-slot sp values rather than
    # a usable C stack. The C boundary deliberately clobbers ABI volatile state.
    bridge_cases = 0
    for queue in (0, 4):
        for status in (0x401, 0x403, 0x9401, 0x9403):
            for outcome in (1, 0, -1):
                cpu = fresh(100, status)
                for i, value in enumerate(commits[0]): cpu.memory[sram + i] = value
                cpu.guest = commits[0][:0x2000]
                cpu.write(phase, COMMITTING)
                cpu.pattern(300)
                cpu.regs[4] = sx32(symbols['sram'] | 0x20000000)
                cpu.regs[5] = 32768
                cpu.regs[29] = queue
                before = cpu.regs.copy(), cpu.hi, cpu.lo, cpu.cp[12]
                def capture_c(c, result=outcome):
                    assert c.regs[29] & 15 == 0, 'C private stack is not aligned'
                    assert c.regs[29] != queue, 'bridge reused queue-slot sp as C stack'
                    bridge(c, result)
                cpu.hooks[symbols['continuous_save_capture']] = capture_c
                cpu.execute(symbols['continuous_save_capture_bridge'])
                preserve(cpu, before, (2, 26, 27))
                assert cpu.regs[2] == sx32(outcome)
                bridge_cases += 1
                cases += 1

    # An advertised but invalid handoff must fail closed, not silently use
    # legacy auto-writeback or allow a capture that cannot be committed safely.
    for status in (0x400, 0x402, 0x9400, 0x9402):
        cpu = fresh(0, status, availability=-1)
        assert cpu.read(mode) == 1 and cpu.read(phase) == ERROR
        frozen, compare = cpu.blob(sram, 0x8000), cpu.cp[11]
        call(cpu, 'native_diag_arm', 350)
        assert cpu.blob(sram, 0x8000) == frozen and cpu.cp[11] == compare
        before, _ = call(cpu, 'native_diag_service', 351)
        preserve(cpu, before)
        assert cpu.read(phase) == ERROR
        cases += 1

    # A real renderer stall AFTER the normal seal cannot reach the natural
    # boundary service. Its explicit terminal path preserves the retained
    # interval and records the later fault independently before bounded stop.
    post_seal_faults = 0
    for status in (0x401, 0x9403):
        for wait_name in ('native_diag_rsp_wait', 'native_diag_frame_wait'):
            cpu = fresh(0xFFFF0000, status)
            arm(cpu, 0xFFFF0000, 400)
            cutoff = seal(cpu, 0xFFFF0000, 402)
            retained_body = cpu.blob(sram + 0x2200, 0x5E00)
            fault_count = (cutoff + 2 * HZ + 333) & MASK32
            cpu.cp.update({9: fault_count, 12: status})
            cpu.pattern(408)
            cpu.regs[4] = sx32(symbols[wait_name])
            cpu.allow_rcp_writes = True
            def fault_c(c):
                assert c.read(sram + 0x200C) == 1
                assert c.read(sram + 0x2000 + 0x1F0) == 3
                assert c.read(sram + 0x2000 + 0x1F4) == fault_count
                assert c.read(sram + 0x2000 + 0x1F8) == symbols[wait_name]
                assert c.read(sram + 0x2000 + 0x1FC) == status
                assert c.read(sram + 0x2000 + 76) == cutoff
                assert c.read(sram + 0x2000 + 52) == LIMIT + 17
                assert c.blob(sram + 0x2200, 0x5E00) == retained_body
                bridge(c, terminal=True)
            cpu.hooks[symbols['continuous_save_capture']] = fault_c
            result = cpu.execute(symbols['native_diag_sealed_wait_stall'],
                                 stop=symbols['native_diag_screen'])
            assert result == 'return' and cpu.read(phase) == SEALED
            assert cpu.blob(sram, 0x2000) == cpu.guest
            assert any(address == 0x04040010 and value == 2
                       for address, _, value in cpu.memory_writes)
            assert any(address == 0x0410000C and value == 8
                       for address, _, value in cpu.memory_writes)
            post_seal_faults += 1
            cases += 1

    # Execute a real cutoff IRQ after the frame helper has saved old Status,
    # immediately before its first MTC0 mask. It must see SEALED under exclusion,
    # avoid a late record/counter update and clear the inherited old Compare bit.
    frame_mask = next(symbols['native_diag_frame_complete'] + offset
                      for offset in range(0, 64, 4)
                      if (CPU(base).read(symbols['native_diag_frame_complete'] + offset) >> 26) == 16
                      and ((CPU(base).read(symbols['native_diag_frame_complete'] + offset) >> 21) & 31) == 4
                      and ((CPU(base).read(symbols['native_diag_frame_complete'] + offset) >> 11) & 31) == 12)
    frame_seal_races = 0
    for initial_count in (0, 0xFFFF0000):
        cpu = fresh(initial_count, 0x401)
        arm(cpu, initial_count, 500)
        cpu.cp.update({9: (initial_count + 1600000) & MASK32, 12: 0x8401})
        cpu.pattern(502)
        before = cpu.regs.copy(), cpu.hi, cpu.lo, cpu.cp[12]
        sealed = {}
        def cutoff_irq(c):
            now = (initial_count + LIMIT + 17) & MASK32
            c.cp.update({9: now, 12: c.cp[12] | 2, 14: frame_mask})
            c.write(state + 16, now)
            assert c.execute(symbols['native_diag_interrupt']) == 'eret'
            assert c.read(phase) == SEALED
            sealed['payload'] = c.blob(sram, 0x8000)
            sealed['state'] = c.blob(state, 320)
        cpu.before_instruction[frame_mask] = cutoff_irq
        cpu.execute(symbols['native_diag_frame_complete'])
        preserve(cpu, (before[0], before[1], before[2], before[3] & ~0x8000),
                 (8, 9, 10, 11, 26, 27))
        assert cpu.blob(sram, 0x8000) == sealed['payload']
        assert cpu.blob(state, 320) == sealed['state'], 'raced helper appended after seal'
        # A further stale Compare interrupt must neither sample nor mutate the
        # sealed payload/state; it only removes IM7 and returns through ERET.
        cpu.cp[12] = 0x8403
        before, result = call(cpu, 'native_diag_interrupt', 504)
        assert result == 'eret'
        preserve(cpu, (before[0], before[1], before[2], 0x401), (26, 27))
        assert cpu.blob(sram, 0x8000) == sealed['payload']
        assert cpu.blob(state, 320) == sealed['state']
        frame_seal_races += 1
        cases += 1

    # A menu with no continuous handoff retains terminal v4/one-shot behavior.
    cpu = fresh(0x12345678, 0x401, availability=0)
    assert cpu.read(mode) == 0
    cpu.cp[9] = 0x12345678
    call(cpu, 'native_diag_arm', 200)
    old = cpu.blob(state, 320), cpu.cp[11]
    call(cpu, 'native_diag_arm', 201)
    assert old == (cpu.blob(state, 320), cpu.cp[11]), 'legacy one-shot changed'
    before, _ = call(cpu, 'native_diag_service', 202)
    preserve(cpu, before)
    assert cpu.read(mode) == 0
    cpu.allow_rcp_writes = True
    cpu.pattern(203)
    cpu.regs[24] = 2
    cpu.cp.update({9: (0x12345678 + LIMIT + 17) & MASK32, 12: 0x8003})
    cpu.execute(symbols['native_diag_finalize'], stop=symbols['native_diag_sum_guest'])
    assert cpu.read(sram + 0x2004) == 4, 'legacy format changed'
    assert any(address == 0x04040010 and value == 2 for address, _, value in cpu.memory_writes), 'legacy halt missing'
    assert any(address == 0x0410000C for address, _, _ in cpu.memory_writes), 'legacy DP freeze missing'
    assert cpu.blob(sram, 0x2000) == cpu.guest
    cases += 1

    proof = dict(passed=True, cases=cases, repeated_captures=36, failure_cases=8,
                 full_64bit_ordinary_service_gprs=True, hi_lo_and_status_exl_preserved=True,
                 irq_nonreserved_gprs_preserved=True, count_wrap=True,
                 irq_cutoff_then_natural_boundary_service=True,
                 no_early_seal_at_limit_minus_one=True,
                 sd_pause_excluded_from_retained_capture=True,
                 no_forced_rsp_halt_or_dp_freeze=True, full_payload_cleared_each_arm=True,
                 guest_sram_preserved=True, save_failure_blocks_rearm=True,
                 in_session_guest_progress_preserved=True, invalid_handoff_fails_closed=True,
                 legacy_v4_one_shot_terminal_preserved=True,
                 post_seal_terminal_faults=post_seal_faults,
                 sealed_interval_preserved_on_later_fault=True,
                 compiled_irq_inside_frame_helper_races=frame_seal_races,
                 stale_compare_irq_does_not_mutate_sealed_window=True,
                 actual_o64_bridge_cases=bridge_cases, queue_slot_sp_restored=True,
                 c_transport_mocked=True,
                 sd_writeback_authority=False, native_fps_authority=False)
    if args.json_output:
        args.json_output.write_text(json.dumps(proof, indent=2) + '\n')
    print('NATIVE_DIAG_CONTINUOUS_COMPILED PASS', json.dumps(proof))


if __name__ == '__main__':
    main()
