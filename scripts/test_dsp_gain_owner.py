#!/usr/bin/env python3
"""Execute linked GAIN handlers with independent stereo-accumulator sentinels."""
import argparse
from linked_cpu_regression import CPU, load_elf


def check(memory, symbols):
    cpu = CPU(memory.copy())
    cases = 0
    for voice in range(8):
        for gain in range(256):
            offset = voice*16
            cpu.write(symbols['dsp_regs']+offset+7, gain, 1)
            cpu.write(symbols['envelopes']+offset, 1024, 2)
            cpu.write(symbols['next_steps']+offset, 0x1234, 2)
            cpu.pattern(voice+gain)
            cpu.regs[14] = voice
            # Distinct 64-bit values catch clobbers and accidental truncation.
            cpu.regs[12] = 0xabcdef0123456789
            cpu.regs[13] = 0x123456789abcdef0
            before = cpu.regs.copy()
            product, cp = (cpu.hi, cpu.lo), cpu.cp.copy()
            cpu.memory_writes.clear()
            target = symbols['update_vols'] if gain < 128 else symbols['update_step']
            cpu.execute(symbols['gain_time'], stop=target)
            assert cpu.regs[12:14] == before[12:14], ('stereo accumulator clobber', voice, gain)
            assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1, 4, 8, 9, 10))
            if gain < 128:
                assert cpu.read(symbols['envelopes']+offset, 2) == gain*16
                assert cpu.read(symbols['next_steps']+offset, 2) == 0xffff
                expected = {(symbols[name]+offset) & 0x1fffffff for name in ('envelopes', 'next_steps')}
                assert len(cpu.memory_writes) == 2
                assert {address for address, _, _ in cpu.memory_writes} == expected
                assert all(width == 2 for _, width, _ in cpu.memory_writes)
            else:
                assert cpu.regs[4] == (gain & 31)*4
                assert not cpu.memory_writes
            assert (cpu.hi, cpu.lo) == product and cpu.cp == cp and not cpu.cp_writes
            cases += 1
    return cases


def scheduler_check(memory, symbols):
    """Exercise the unchanged legacy mixer across actual due-envelope calls."""
    cpu = CPU(memory.copy())
    for due_voice in range(8):
        for gain in range(256):
            cpu.write(symbols['enabled'], 255, 1)
            cpu.write(symbols['audio_set'], 4, 1)
            cpu.write(symbols['dsp_timer'], 100, 2)
            cpu.write(symbols['noise_step'], 65535, 2)
            cpu.write(symbols['dsp_pointer'], 0x200, 2)
            cpu.write(symbols['dsp_regs']+0x3d, 0, 1)
            total = 0
            for voice in range(8):
                offset = voice*16
                cpu.write(symbols['envelopes']+offset, 1024, 2)
                cpu.write(symbols['mode_funcs']+offset, symbols['gain_mode'])
                cpu.write(symbols['next_steps']+offset, 99 if voice == due_voice else 65535, 2)
                cpu.write(symbols['dsp_regs']+offset+7, gain if voice == due_voice else 64, 1)
                cpu.write(symbols['dsp_regs']+offset, 64, 1)
                cpu.write(symbols['dsp_regs']+offset+1, 64, 1)
                cpu.write(symbols['dsp_regs']+offset+2, 0, 2)
                cpu.write(symbols['cached_vols']+offset, 4096, 2)
                cpu.write(symbols['cached_vols']+offset+2, 4096, 2)
                cpu.write(symbols['counters']+offset, 0, 2)
                for sample in range(4):
                    cpu.write(symbols['cur_samples']+voice*8+sample*2, 1000, 2)
                env = 1024
                if voice == due_voice:
                    if gain < 128:
                        env = gain*16
                    else:
                        env = (992, 1020, 1056, 1056)[(gain >> 5) & 3]
                # Independent expression for the legacy cached mixer. This is
                # not the full-precision dry-mix oracle or full DSP fidelity.
                total += 1000*(64*(env//16))//16384
            cpu.pattern()
            cpu.execute(symbols['dsp_sample'], stop=symbols['apu_execute'])
            word = cpu.read(symbols['dsp_buffer']+0x200)
            assert word == (total << 16 | total), ('scheduled stereo', due_voice, gain, word, total)
            assert not cpu.cp_writes
    return 2048


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    cases = check(memory, symbols)
    scheduled = scheduler_check(memory, symbols)
    # Put the old destination register back in the actual linked SLL. The
    # independent sentinel invariant must reject it even if arithmetic agrees.
    entry = symbols['gain_time'] & 0x1fffffff
    candidates = []
    for pc in range(entry, entry+16, 4):
        word = int.from_bytes(bytes(memory.get(pc+i, 0) for i in range(4)), 'big')
        if word >> 26 == 0 and word & 63 == 0 and (word >> 16 & 31) == 14 and (word >> 6 & 31) == 4:
            candidates.append((pc, word))
    assert len(candidates) == 1
    pc, word = candidates[0]
    mutant = memory.copy()
    for i, byte in enumerate(((word & ~(31 << 11)) | (12 << 11)).to_bytes(4, 'big')):
        mutant[pc+i] = byte
    try:
        check(mutant, symbols)
    except AssertionError:
        pass
    else:
        raise AssertionError('old accumulator clobber accepted')
    print(f'DSP_GAIN_OWNER PASS voices=8 GAIN_values=256 handler_cases={cases} scheduled_stereo={scheduled} faults=1; full waveform remains outside this gate')


if __name__ == '__main__':
    main()
