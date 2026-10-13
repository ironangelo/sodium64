#!/usr/bin/env python3
"""Execute the register-group decoder against scalar code and BRR arithmetic."""
import argparse
import json
from pathlib import Path

from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU
from test_dsp_brr_accuracy import cases, reference, run, mutate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--reference-elf', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--observer-smoke', action='store_true')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    old_memory, old_symbols = load_elf(args.reference_elf)
    assert 'brr_group_dispatch' in symbols and 'brr_group_dispatch' not in old_symbols
    assert symbols['cur_samples'] % 8 == 0, 'four-store loop requires aligned voice buffers'
    cpu, scalar = CPU(memory), CPU(old_memory)
    counts, totals, maxima = 0, [0,0], [0,0]
    filter_counts = {i: [0,0] for i in range(4)}
    matrix = cases()
    if args.observer_smoke:
        assert 'dsp_brr_records' in symbols
        matrix = [([1,-4,7,-8],shift,kind,16383,-16384)
                  for shift in range(16) for kind in range(4)]
    for case in matrix:
        expected = reference(*case)
        baseline, old_steps = run(scalar, old_symbols, case)
        assert baseline == expected
        for voice in range(8):
            actual, steps = run(cpu, symbols, case, voice)
            assert actual == expected, (voice, case, actual, expected)
            totals[0] += old_steps; totals[1] += steps
            maxima[0] = max(maxima[0],old_steps); maxima[1] = max(maxima[1],steps)
            filter_counts[case[2]][0] += old_steps; filter_counts[case[2]][1] += steps
            assert cpu.regs[3] & 0xffffffff == symbols['cur_samples'] + voice*8
            counts += 1
    # The smoke compares an instrumented candidate to the uninstrumented
    # scalar control. Its observer stores are outside the speed comparison.
    if not args.observer_smoke:
        assert all(new < old for old,new in filter_counts.values()), filter_counts
    mutations = [
        ('signed_filter_floor',symbols['filter_1'],symbols['filter_2'],
         lambda w:w == ((17<<16)|(15<<11)|35),lambda w:0,
         ([-8]*4,0,1,1,-1)),
        ('invalid_range_mask',symbols['decode_samples'],symbols['brr_group_dispatch'],
         lambda w:w>>26==12 and w&65535==0x8888,lambda w:(w&~65535)|65535,
         ([1,4,-7,-1],13,0,0,0)),
        ('saturation',symbols['filter_2'],symbols['filter_3'],
         lambda w:w>>26==14 and w&65535==0x7fff,lambda w:(w&~65535)|0x7ffe,
         ([7]*4,12,2,16383,-16384)),
        ('signed15_storage',symbols['filter_1'],symbols['filter_2'],
         lambda w:w>>26==0 and w&63==0 and w>>6&31==17,
         lambda w:(w&~(31<<6))|(16<<6),([7]*4,12,1,16383,0)),
        ('history_recurrence',symbols['filter_2'],symbols['filter_3'],
         lambda w:w>>26==0 and w&63 in (33,37) and w>>21&31==8 and w>>16&31==0 and w>>11&31==17,
         lambda w:0,([1,4,-7,-1],8,2,11,-5)),
        ('four_store_extent',symbols['filter_2'],symbols['filter_3'],
         lambda w:w>>26==12 and w&65535==6,lambda w:(w&~65535)|4,
         ([1,4,-7,-1],8,2,11,-5)),
    ]
    rejected = []
    for name,start,end,predicate,transform,case in mutations:
        pc, old = mutate(cpu,start,end,predicate,transform)
        try:
            rejected_fault = False
            try:
                actual, _ = run(cpu,symbols,case,7)
                rejected_fault = actual != reference(*case)
            except AssertionError:
                rejected_fault = True
            assert rejected_fault, ('mutation escaped oracle/ownership',name)
        finally:
            cpu.write(pc,old)
        rejected.append(name)
    result = dict(passed=True, compiled_voice_cases=counts,
                  all_filters_ranges_and_voices=True, history_loads_per_chunk_at_most=2,
                  independent_arithmetic_and_scalar_match=True,
                  write_extent_GPR_HI_LO_CP0_and_buffer_base_preserved=True,
                  negative_mutations_rejected=rejected,
                  instructions_total_reference_group=totals,
                  maximum_decoder_instructions_reference_group=maxima,
                  instructions_by_filter_reference_group=filter_counts,
                  BRR_observer_owned_bytes_checked='dsp_brr_records' in symbols,
                  observer_smoke=args.observer_smoke,
                  instruction_comparison_has_equal_observer_configuration=not args.observer_smoke,
                  native_performance_and_full_audio_fidelity_claim=False)
    if args.output: args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('BRR_GROUP PASS',json.dumps(result))


if __name__ == '__main__': main()
