#!/usr/bin/env python3
"""Linked CPU test support, extracted from the existing native diagnostic tests.

This executes architectural instructions for bounded regression checks. It is
not an N64 timing, cache, interrupt or audio waveform model. Unknown operations
fail closed. No runtime diagnostics or commercial data are linked into the ROM.
"""
from pathlib import Path
import struct


def load_elf(path):
    data = Path(path).read_bytes()
    assert data[:6] == b'\x7fELF\x01\x02', 'expected big-endian ELF32'
    header = struct.unpack_from('>16sHHIIIIIHHHHHH', data)
    sections = [struct.unpack_from('>IIIIIIIIII', data, header[6] + i*header[11])
                for i in range(header[12])]
    memory, symbols = {}, {}
    for section in sections:
        if section[2] & 2:
            raw = bytes(section[5]) if section[1] == 8 else data[section[4]:section[4]+section[5]]
            memory.update(((section[3]+i) & 0x1fffffff, byte) for i, byte in enumerate(raw))
        if section[1] == 2:
            strings = sections[section[6]]
            names = data[strings[4]:strings[4]+strings[5]]
            for offset in range(section[4], section[4]+section[5], section[9]):
                name, value, _, _, _, index = struct.unpack_from('>IIIBBH', data, offset)
                if name and index:
                    end = names.index(0, name)
                    symbols[names[name:end].decode()] = value & 0xffffffff
    return memory, symbols


MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1
RETURN = 0xDEAD0000
HZ = 46875000
LIMIT = 20 * HZ
SAMPLE = 131071
READY, RECORDING, SEALED, COMMITTING, ERROR, EXHAUSTED, USB_READY = range(7)


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
        self.tlb = [(0,0,0,0) for _ in range(32)]
        self.memory_writes = []
        self.cache_ops = []
        self.hooks = {}
        self.before_instruction = {}
        self.allow_rcp_writes = False
        self.steps = 0
        self.enforce_hilo_spacing = False

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
        recent_instructions = []
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
            if self.enforce_hilo_spacing:
                writes_product = word>>26 == 0 and 24 <= word&63 <= 31
                if writes_product:
                    assert not any(w>>26 == 0 and w&63 in (16,18)
                                   for _,w in recent_instructions), ('VR4300 HI/LO spacing',hex(pc),recent_instructions)
                recent_instructions = (recent_instructions+[(pc,word)])[-2:]
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
                elif fn in (26, 27):
                    # DSP timer scheduling uses ordinary32-bit division. Reject
                    # exceptional operands rather than inventing their behavior.
                    numerator = signed(r[rs],32) if fn == 26 else r[rs] & MASK32
                    denominator = signed(r[rt],32) if fn == 26 else r[rt] & MASK32
                    assert denominator and not (numerator == -2147483648 and denominator == -1)
                    quotient = abs(numerator) // abs(denominator)
                    if (numerator < 0) != (denominator < 0): quotient = -quotient
                    self.lo = sx32(quotient)
                    self.hi = sx32(numerator - quotient * denominator)
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
                elif word == 0x42000001: # TLBR, timing/hazards not modeled.
                    for index,value in zip((10,2,3,5),self.tlb[self.cp[0]&31]):self.cp[index]=value
                elif word == 0x42000002: # Indexed TLBWI; no random replacement.
                    self.tlb[self.cp[0]&31]=tuple(self.cp.get(index,0) for index in (10,2,3,5))
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
