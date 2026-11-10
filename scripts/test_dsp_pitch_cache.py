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
        cpu.write(cache+offset, 0xdead, 2)
        cpu.pattern()
        cpu.regs[5] = value
        before = cpu.regs.copy()
        cpu.memory_writes.clear()
        step = cpu.steps
        cpu.execute(symbols['write_dspdata'])
        assert cpu.read(regs+register, 1) == value
        assert cpu.read(cache+offset, 2) == expected
        assert accesses(cpu) == {((regs+register)&0x1fffffff,1), ((cache+offset)&0x1fffffff,2)}
        assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1,8,9,10))
        return cpu.steps-step-1

    maximum = 0
    for other in range(256):
        for value in range(256):
            voice = (other+value) & 7
            maximum = max(maximum,
                          write(voice,0,value,value^0x5a,other,pitch(value,other)),
                          write(voice,1,value,other,value^0xa5,pitch(other,value)))
    assert maximum == 26

    entry = symbols['get_pitch']
    for voice in range(8):
        for raw in range(65536):
            expected = pitch(raw&255, raw>>8)
            cpu.write(cache+16*voice, expected, 2)
            cpu.pattern()
            cpu.regs[24] = 16*voice
            before = cpu.regs.copy()
            cpu.memory_writes.clear()
            cpu.execute(entry, stop=entry+12)
            assert cpu.regs[8] == expected and not cpu.memory_writes
            assert all(cpu.regs[i] == before[i] for i in range(32) if i != 8)

    for invalid in range(128,256):
        cpu.write(addr, invalid, 1)
        cpu.pattern()
        cpu.regs[5] = 0xff
        cpu.memory_writes.clear()
        cpu.execute(symbols['write_dspdata'])
        assert not cpu.memory_writes

    for voice in range(8):
        offset = 16*voice
        for byte in (0,1):
            register = offset+2+byte
            cpu.write(addr, register, 1)
            cpu.write(symbols['apu_clock'],21,1)
            cpu.write(symbols['jit_tags']+12,0x12345678)
            cpu.pattern()
            cpu.regs[4],cpu.regs[5],cpu.regs[19] = 0xf3,0xd7,1000
            before = cpu.regs.copy()
            cpu.memory_writes.clear()
            cpu.execute(symbols['apu_write8'])
            assert cpu.regs[19] == 979 and cpu.read(symbols['jit_tags']+12) == 0x12345679
            assert cpu.read(symbols['apu_ram']+0xf3,1) == cpu.read(regs+register,1) == 0xd7
            assert cpu.read(cache+offset,2) == pitch(cpu.read(regs+offset+2,1),cpu.read(regs+offset+3,1))
            assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1,8,9,10,19))
            assert accesses(cpu) == {
                ((symbols['jit_tags']+12)&0x1fffffff,4), ((symbols['apu_ram']+0xf3)&0x1fffffff,1),
                ((regs+register)&0x1fffffff,1), ((cache+offset)&0x1fffffff,2)}
        for register in (offset+4,offset+6,offset+7,offset+8):
            cpu.write(addr,register,1)
            cpu.pattern()
            cpu.regs[5] = 0xa5
            cpu.memory_writes.clear()
            cpu.execute(symbols['write_dspdata'])
            assert accesses(cpu) == {((regs+register)&0x1fffffff,1)}
        write(voice,0,0xfe,0,0x8f,pitch(0xfe,0x8f))
        write(voice,1,0xff,0xfe,0x8f,pitch(0xfe,0xff))
        cpu.write(addr,offset+3|0x80,1)
        cpu.pattern()
        cpu.memory_writes.clear()
        cpu.execute(symbols['read_dspdata'])
        assert cpu.regs[2] == 0xff and not cpu.memory_writes

    masks=[pc for pc in range(symbols['write_pitch'],symbols['write_pitch']+48,4)
           if cpu.read(pc)>>26 == 12 and cpu.read(pc)&0xffff == 0x3fff]
    assert len(masks)==1
    instruction=cpu.read(masks[0])
    cpu.write(masks[0],instruction|0xc000)
    try:
        write(7,1,0xff,0xfe,0,pitch(0xfe,0xff))
    except AssertionError:
        pass
    else:
        raise AssertionError('Mask mutation escaped the numerical check')
    finally:
        cpu.write(masks[0],instruction)

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
            'reference_cases':reference_cases,'apu_port_cases':16,'invalid_write_cases':128,
            'ordinary_write_cases':32,'mirrored_read_cases':8,'emitted_mask_faults_rejected':1,
            'pitch_load_instructions':3,'maximum_pitch_write_instructions':maximum}
    if args.json_output:
        args.json_output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
