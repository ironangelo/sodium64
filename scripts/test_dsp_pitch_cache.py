#!/usr/bin/env python3
"""Check the linked pitch cache against little-endian DSP register arithmetic."""
import argparse
import json
from pathlib import Path

from linked_cpu_regression import CPU, load_elf


def pitch(low, high):
    return (low | (high << 8)) & 0x3fff


def accesses(cpu):
    return {(address, width) for address, width, _ in cpu.memory_writes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--reference-elf', type=Path)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    cpu = CPU(memory)
    cache = symbols['dsp_pitches']
    regs = symbols['dsp_regs']
    addr = symbols['dsp_addr']
    assert cache % 16 == 0 and cpu.blob(cache, 128) == bytes(128)
    assert cpu.blob(regs, 128) == bytes(128)

    def write(voice, byte, value, low, high, expected):
        offset = 16*voice
        register = offset+2+byte
        cpu.write(addr, register, 1)
        cpu.write(regs+offset+2, low, 1)
        cpu.write(regs+offset+3, high, 1)
        cpu.write(cache+offset, (high << 8) | low, 2)
        cpu.pattern()
        cpu.regs[5] = value
        before = cpu.regs.copy()
        cpu.memory_writes.clear()
        step = cpu.steps
        cpu.execute(symbols['write_dspdata'])
        assert cpu.read(regs+register, 1) == value
        assert cpu.read(cache+offset, 2) == expected
        assert cpu.read(cache+offset+byte, 1) == (high if byte == 0 else low), 'sibling byte changed'
        assert accesses(cpu) == {((regs+register)&0x1fffffff,1), ((cache+offset+(1-byte))&0x1fffffff,1)}
        assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1,8,9,10))
        return cpu.steps-step-1

    entry = symbols['get_pitch']
    load_instructions = 0
    for voice in range(8):
        cpu.pattern()
        cpu.regs[24] = voice*16
        cpu.memory_writes.clear()
        steps = cpu.steps
        cpu.execute(entry, stop=symbols['get_pitch_counter'])
        assert cpu.regs[8] == 0 and not cpu.memory_writes, 'cold pitch is nonzero'
        load_instructions = max(load_instructions, cpu.steps-steps-1)

    # Exercise independently ordered writes from the linked zeroed data.
    mixed = CPU(memory.copy())
    # CPU uses the original loaded image here, not the exhaustive-write state.
    for voice in range(8):
        mixed.write(cache+voice*16, 0, 2)
        mixed.write(regs+voice*16+2, 0, 2)
    for index in range(128):
        voice = (index*5) & 7
        byte = (index >> 3) & 1
        value = (index*73+0xc1) & 255
        mixed.write(addr, voice*16+2+byte, 1)
        mixed.pattern()
        mixed.regs[5] = value
        mixed.execute(symbols['write_dspdata'])
        for sample in range(8):
            low = mixed.read(regs+sample*16+2, 1)
            high = mixed.read(regs+sample*16+3, 1)
            assert mixed.read(cache+sample*16, 2) == low | (high << 8)
            mixed.pattern()
            mixed.regs[24] = sample*16
            mixed.execute(entry, stop=symbols['get_pitch_counter'])
            assert mixed.regs[8] == pitch(low, high), 'mixed pitch writes'

    maximum = 0
    for other in range(256):
        for value in range(256):
            voice = (other+value) & 7
            maximum = max(maximum,
                          write(voice,0,value,value^0x5a,other,value | (other << 8)),
                          write(voice,1,value,other,value^0xa5,other | (value << 8)))

    entry = symbols['get_pitch']
    for voice in range(8):
        for raw in range(65536):
            expected = pitch(raw&255, raw>>8)
            cpu.write(cache+16*voice, raw, 2)
            cpu.pattern()
            cpu.regs[24] = 16*voice
            before = cpu.regs.copy()
            cpu.memory_writes.clear()
            cpu.execute(entry, stop=symbols['get_pitch_counter'])
            assert cpu.regs[8] == expected and not cpu.memory_writes, (voice, raw, cpu.regs[8], expected, cpu.memory_writes)
            assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (8,25))
            assert cpu.regs[25] & 0xffffffff == (symbols['counters'] + 0x8000) & 0xffff0000

    for invalid in range(128,256):
        cpu.write(addr, invalid, 1)
        cpu.pattern()
        cpu.regs[5] = 0xff
        before = cpu.regs.copy()
        cpu.memory_writes.clear()
        cpu.execute(symbols['write_dspdata'])
        assert not cpu.memory_writes
        assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1,8,9)), 'invalid write GPRs'

    for voice in range(8):
        offset = 16*voice
        cpu.write(cache+offset, cpu.read(regs+offset+2,1) | (cpu.read(regs+offset+3,1) << 8), 2)
        for byte in (0,1):
            for clock in (21,42):
                register = offset+2+byte
                cpu.write(addr, register, 1)
                cpu.write(symbols['apu_clock'],clock,1)
                cpu.write(symbols['jit_tags']+12,0x12345678)
                cpu.pattern()
                cpu.regs[4],cpu.regs[5],cpu.regs[19] = 0xf3,0xd7,1000
                before = cpu.regs.copy()
                cpu.memory_writes.clear()
                cpu.execute(symbols['apu_write8'])
                assert cpu.regs[19] == 1000-clock and cpu.read(symbols['jit_tags']+12) == 0x12345679
                assert cpu.read(symbols['apu_ram']+0xf3,1) == cpu.read(regs+register,1) == 0xd7
                assert cpu.read(cache+offset,2) == cpu.read(regs+offset+2,1) | (cpu.read(regs+offset+3,1) << 8)
                assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1,8,9,10,19))
                assert accesses(cpu) == {
                    ((symbols['jit_tags']+12)&0x1fffffff,4), ((symbols['apu_ram']+0xf3)&0x1fffffff,1),
                    ((regs+register)&0x1fffffff,1), ((cache+offset+(1-byte))&0x1fffffff,1)}
        for register in (offset+4,offset+6,offset+7,offset+8):
            cpu.write(addr,register,1)
            cpu.pattern()
            cpu.regs[5] = 0xa5
            before = cpu.regs.copy()
            cpu.memory_writes.clear()
            cpu.execute(symbols['write_dspdata'])
            assert accesses(cpu) == {((regs+register)&0x1fffffff,1)}
            assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1,8,9)), 'ordinary write GPRs'
        write(voice,0,0xfe,0,0x8f,0x8ffe)
        write(voice,1,0xff,0xfe,0x8f,0xfffe)
        cpu.write(addr,offset+3|0x80,1)
        cpu.pattern()
        before = cpu.regs.copy()
        cpu.memory_writes.clear()
        cpu.execute(symbols['read_dspdata'])
        assert cpu.regs[2] == 0xff and not cpu.memory_writes
        assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1,2,8)), 'mirrored read GPRs'

    def load_check():
        cpu.write(cache+7*16, 0xfffe, 2)
        cpu.pattern()
        cpu.regs[24] = 7*16
        cpu.execute(entry, stop=symbols['get_pitch_counter'])
        assert cpu.regs[8] == 0x3ffe, 'pitch load mask'

    def reject(pc, replacement, check, label):
        original = cpu.read(pc)
        cpu.write(pc, replacement)
        try:
            check()
        except AssertionError:
            pass
        else:
            raise AssertionError(label + ' mutation escaped')
        finally:
            cpu.write(pc, original)

    masks = [pc for pc in range(entry, symbols['get_pitch_counter'], 4)
             if cpu.read(pc)>>26 == 12 and cpu.read(pc)&0xffff == 0x3fff]
    assert len(masks) == 1
    reject(masks[0], 0, load_check, 'load mask')
    for label, byte, displacement, low, high in (
        ('write_pitch', 0, -1, 0, 0x8f),
        ('write_pitch_high', 1, 1, 0xfe, 0x8f),
    ):
        stores = [pc for pc in range(symbols[label], symbols[label]+16, 4)
                  if cpu.read(pc)>>26 == 40]
        assert len(stores) == 1, 'expected one cached byte store'
        word = cpu.read(stores[0])
        other_lane = (word & 0xffff0000) | ((word + displacement) & 0xffff)
        expected = 0x8fff if byte == 0 else 0xfffe
        reject(stores[0], other_lane,
               lambda: write(7, byte, 0xff, low, high, expected), label + ' byte lane')
    raw_stores = [pc for pc in range(symbols['write_dspdata'], symbols['write_reg'], 4)
                  if cpu.read(pc)>>26 == 40]
    assert len(raw_stores) == 1
    reject(raw_stores[0], 0, lambda: write(7,1,0xff,0xfe,0x8f,0xfffe), 'raw register')

    reference_cases=0
    if args.reference_elf:
        previous,old=load_elf(args.reference_elf)
        control=CPU(previous)
        assert 'dsp_pitches' not in old
        for raw in range(65536):
            voice=raw&7
            control.write(old['dsp_regs']+16*voice+2,raw&255,1)
            control.write(old['dsp_regs']+16*voice+3,raw>>8,1)
            control.pattern()
            control.regs[24]=16*voice
            control.execute(old['get_pitch'],stop=old['get_pitch']+28)
            assert control.regs[8] == pitch(raw&255,raw>>8)
            reference_cases+=1

    report={'passed':True,'compiled_write_cases':131072,'compiled_load_cases':524288,
            'reference_cases':reference_cases,'apu_port_cases':32,'invalid_write_cases':128,
            'ordinary_write_cases':32,'mixed_cold_writes':128,'cold_load_cases':8,'mirrored_read_cases':8,'emitted_faults_rejected':4,
            'pitch_load_instructions':load_instructions,'maximum_pitch_write_instructions':maximum}
    if args.json_output:
        args.json_output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
