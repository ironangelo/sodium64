#!/usr/bin/env python3
"""Compare actual linked DSP sampling with an identical index-based reference."""
import argparse
import hashlib
import json
from pathlib import Path

from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU, signed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--reference-elf', type=Path, required=True)
    parser.add_argument('--brr-group', action='store_true',
                        help='Both artifacts use voice pointers; compare group to scalar BRR.')
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    models = [(CPU(m), s) for m, s in
              (load_elf(args.reference_elf), load_elf(args.elf))]
    if args.brr_group:
        assert 'dsp_voice_base' in models[0][1]
        assert 'brr_group_dispatch' not in models[0][1]
        assert 'brr_group_dispatch' in models[1][1]
    else:
        assert 'dsp_voice_base' not in models[0][1]
    assert 'dsp_voice_base' in models[1][1]
    modes = ('attack_mode', 'decay_mode', 'sustain_mode', 'gain_mode', 'release_mode')
    optimized, symbols = models[1]
    optimized.enforce_hilo_spacing=True
    fields = ('mode_funcs','next_steps','dsp_pitches','counters','envelopes','cur_addrs','dsp_regs')
    offsets = {symbols[name]-symbols['mode_funcs'] for name in fields}
    offsets.update(symbols['dsp_regs']+extra-symbols['mode_funcs'] for extra in (1,4))
    assert all(-32768 <= value <= 32767 for value in offsets)
    accesses = set()
    for pc in range(symbols['next_voice'], symbols['end_voice'],4):
        word = optimized.read(pc)
        if word>>26 in (32,35,36,37,41) and word>>21&31 == 24:
            accesses.add(signed(word&65535,16))
    assert accesses == offsets, ('linked field offsets',accesses,offsets)

    def put(cpu, symbols, name, value, size=4, offset=0):
        cpu.write(symbols[name]+offset, value, size)

    def state(cpu, symbols):
        names = {symbols[name]: name for name in modes}
        result = {name: cpu.blob(symbols[name], length) for name, length in
                  (('dsp_regs',128), ('dsp_buffer',8192), ('cur_samples',64),
                   ('dsp_pitches',128))}
        for name in ('enabled', 'noise_sample', 'noise_step', 'dsp_timer', 'dsp_pointer'):
            result[name] = cpu.read(symbols[name], 1 if name == 'enabled' else 2)
        for name in ('envelopes', 'next_steps', 'counters', 'cur_addrs'):
            result[name] = [cpu.read(symbols[name]+16*i,2) for i in range(8)]
        result['modes'] = [names[cpu.read(symbols['mode_funcs']+16*i)] for i in range(8)]
        for name, size in (('dsp_audio_blocks',4), ('dsp_audio_idle',4),
                           ('dsp_audio_full',4), ('dsp_audio_gap_max',4),
                           ('dsp_audio_last_count',4), ('dsp_release_steps',4),
                           ('dsp_release_last',4), ('dsp_brr_next',4),
                           ('dsp_brr_count',4), ('dsp_brr_records',512),
                           ('dsp_mix_records',80), ('dsp_mix_count',4), ('dsp_mix_ready',4)):
            if name in symbols: result[name] = cpu.blob(symbols[name],size)
        return result

    def setup(seed, mask, trigger, endflags):
        for cpu, symbols in models:
            put(cpu,symbols,'enabled',mask,1)
            put(cpu,symbols,'audio_set',4,1)
            put(cpu,symbols,'dsp_timer',(seed*997)%0x7800,2)
            timer = (seed*997)%0x7800-1
            if timer < 0: timer += 0x7800
            put(cpu,symbols,'noise_step',timer if seed&1 else 65535,2)
            put(cpu,symbols,'noise_sample',(seed*1103)&32767,2)
            put(cpu,symbols,'dsp_pointer',(0,0xffc,0x1ffc,0x200)[seed&3],2)
            cpu.allow_rcp_writes = True
            for address in range(128): put(cpu,symbols,'dsp_regs',(seed*71+address*13)&255,1,address)
            put(cpu,symbols,'dsp_regs',0x10,1,0x5d)
            put(cpu,symbols,'dsp_regs',((seed*79)&255) if seed&2 else 0,1,0x3d)
            for voice in range(8):
                mode = modes[(seed+voice)%len(modes)]
                put(cpu,symbols,'mode_funcs',symbols[mode],4,16*voice)
                put(cpu,symbols,'envelopes',(seed*337+voice*151)&2047,2,16*voice)
                put(cpu,symbols,'next_steps',timer if trigger else 65535,2,16*voice)
                counter = 0x3ff0 if seed&4 else 0xfff0
                put(cpu,symbols,'counters',counter,2,16*voice)
                put(cpu,symbols,'dsp_pitches',32+(seed&31),2,16*voice)
                put(cpu,symbols,'cached_vols',0x13572468,4,16*voice)
                start = 0x2000+voice*128
                put(cpu,symbols,'cur_addrs',start,2,16*voice)
                put(cpu,symbols,'dsp_regs',voice,1,16*voice+4)
                # Force all gain families and direct gain over the case matrix.
                put(cpu,symbols,'dsp_regs',((seed+voice)&7)*32+((seed*3+voice)&31),1,16*voice+7)
                for block in range(4):
                    base = start+9*block
                    header = (((seed+voice)&15)<<4) | ((((seed>>4)+voice)&3)<<2) | endflags
                    put(cpu,symbols,'apu_ram',header,1,base)
                    for index in range(1,9):
                        put(cpu,symbols,'apu_ram',(seed*41+voice*19+index*29)&255,1,base+index)
                loop = start+9
                put(cpu,symbols,'apu_ram',(loop&255)<<8 | loop>>8,2,0x1000+voice*4+2)
                for index in range(4):
                    put(cpu,symbols,'cur_samples',(seed*271+voice*511+index*883)&32767,2,8*voice+2*index)
            for name in ('dsp_audio_blocks','dsp_audio_idle','dsp_audio_full',
                         'dsp_audio_gap_max','dsp_audio_last_count','dsp_release_steps',
                         'dsp_release_last','dsp_brr_next','dsp_brr_count',
                         'dsp_mix_count','dsp_mix_ready'):
                if name in symbols: put(cpu,symbols,name,0)

    def run():
        counts = []
        for cpu, symbols in models:
            cpu.pattern(); cpu.regs[7] = 100000
            before = cpu.regs.copy(); cpu.memory_writes.clear(); cpu.cp_writes.clear()
            start = cpu.steps
            cpu.execute(symbols['dsp_sample'],stop=symbols['apu_execute'],max_steps=10000)
            counts.append(cpu.steps-start-1)
            assert cpu.regs[7] == 100000-672
            for i in (2,5,6,18,19,20,21,22,23,26,27,30):
                assert cpu.regs[i] == before[i], ('unowned register',i)
            assert not cpu.cp_writes
            ram = symbols['apu_ram'] & 0x1fffffff
            assert all(not (address < ram+65536 and address+size > ram)
                       for address,size,_ in cpu.memory_writes)
            for voice in range(8):
                assert cpu.read(symbols['cached_vols']+16*voice) == 0x13572468
        assert state(*models[0]) == state(*models[1])
        return counts

    samples = 0
    totals = [0,0]
    maxima = [0,0]
    decoded_headers = set()
    reference_cpu, reference_symbols = models[0]
    def observe_decode(cpu):
        header = cpu.read(reference_symbols['apu_ram']+(cpu.regs[8]&65535),1)
        decoded_headers.add((header>>4,(header>>2)&3))
        cpu.before_instruction[reference_symbols['decode_samples']] = observe_decode
    reference_cpu.before_instruction[reference_symbols['decode_samples']] = observe_decode
    for mask in range(256):
        for trigger in (False,True):
            for flags in range(4):
                setup(mask,mask,trigger,flags)
                counts = run()
                for i in range(2):
                    totals[i] += counts[i]; maxima[i] = max(maxima[i],counts[i])
                samples += 1
    assert decoded_headers == {(shift,filter) for shift in range(16) for filter in range(4)}
    # A broken pointer/index transition must fail the same real scheduler path.
    cpu,symbols = models[1]
    mutations = []
    for label in ('dsp_voice_base','dsp_voice_envelope_index','dsp_voice_restore_base'):
        pc = symbols[label]
        old = cpu.read(pc)
        cpu.write(pc,0)
        rejected = False
        try:
            setup(20,255,True,3)
            run()
        except (AssertionError,KeyError):
            rejected = True
        finally:
            cpu.write(pc,old)
        assert rejected, 'escaped mutation: '+label
        mutations.append(label)
    proof = {'passed':True, 'paired_actual_scheduler_samples':samples,
             'enabled_masks':256, 'envelope_rate_calls':True, 'noise_steps':True,
             'all_BRR_filters_and_ranges':True, 'block_loop_end_flags':4,
             'both_AI_half_submissions':True, 'PCM_active_state_equal':True,
             'unused_cache_preserved':True, 'guest_cycle_debit':672,
             'actual_decoded_range_filter_pairs':len(decoded_headers),
             'linked_field_offsets_checked':len(offsets),
             'negative_mutations_rejected':mutations,
             'instructions_total_reference_optimized':totals,
             'maximum_sample_instructions_reference_optimized':maxima,
             'timing_or_native_fidelity_claim':False, 'commercial_data':False,
             'reference_elf_sha256':hashlib.sha256(args.reference_elf.read_bytes()).hexdigest(),
             'optimized_elf_sha256':hashlib.sha256(args.elf.read_bytes()).hexdigest()}
    if args.json_output: args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__ == '__main__': main()
