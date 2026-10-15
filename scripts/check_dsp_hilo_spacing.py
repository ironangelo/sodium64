#!/usr/bin/env python3
"""Check NEC VR4300 HI/LO spacing in linked DSP code, with a real bad mutation.

Static checks inspect straight-line predecessors; executed dry/scheduler tests
also check dynamic branch/delay-slot history. Neither simulates interrupts or
establishes an analog-output fault. No commercial inputs are used.
"""
import argparse
import hashlib
import json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU


def read_product(word):
    return word>>26 == 0 and word&63 in (16,18)


def write_product(word):
    return word>>26 == 0 and 24 <= word&63 <= 31


def audit(cpu,s):
    start,end=s['native_diag_dsp_start'],s['native_diag_dsp_end']
    bad=[];writes=0
    for pc in range(start,end,4):
        if not write_product(cpu.read(pc)): continue
        writes+=1
        for distance in (1,2):
            before=pc-4*distance
            if before>=start and read_product(cpu.read(before)):
                bad.append({'writer_pc':hex(pc),'reader_pc':hex(before),
                            'intervening_instructions':distance-1})
    return writes,bad


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path)
    p.add_argument('--expect-unsafe',action='store_true')
    p.add_argument('--json-output',type=Path)
    args=p.parse_args()
    memory,s=load_elf(args.elf);cpu=CPU(memory)
    writers,bad=audit(cpu,s)
    if args.expect_unsafe:
        assert bad, 'unsafe reference unexpectedly passed'
        result={'passed':True,'unsafe_reference_rejected':True,'violations':bad,
                'does_not_prove_observed_corruption':True}
    else:
        assert not bad, ('linked DSP HI/LO violation',bad)
        # Construct the exact old MFLO/SRA/MULT master sequence by moving
        # the two existing left signed16 casts back after the right scale.
        start,end=s['dsp_dry_output_begin'],s['dsp_dry_output_end']
        words=[cpu.read(pc) for pc in range(start,end,4)]
        left_read=next(i for i,w in enumerate(words) if read_product(w) and w>>11&31==13)
        right_mul=next(i for i,w in enumerate(words) if write_product(w) and w>>21&31==12)
        assert right_mul==left_read+4
        assert words[left_read+2] == ((13<<16)|(13<<11)|(16<<6))
        assert words[left_read+3] == ((13<<16)|(13<<11)|(16<<6)|3)
        altered=words[:left_read+2]+words[right_mul:right_mul+3]+words[left_read+2:right_mul]+words[right_mul+3:]
        assert len(altered)==len(words)
        for i,word in enumerate(altered): cpu.write(start+4*i,word)
        _,mutation_bad=audit(cpu,s)
        assert mutation_bad
        for value,register in ((96,12),(64,28),(0,108)):
            cpu.write(s['dsp_regs']+register,value,1)
        def probe(enforce):
            cpu.enforce_hilo_spacing=enforce;cpu.pattern()
            cpu.regs[13]=8192;cpu.regs[12]=4096
            cpu.execute(start,stop=end)
            return cpu.regs[13],cpu.regs[12]
        functional_bad=probe(False)
        rejected=False
        try: probe(True)
        except AssertionError as error:
            assert error.args[0][0]=='VR4300 HI/LO spacing'
            rejected=True
        assert rejected
        for i,word in enumerate(words): cpu.write(start+4*i,word)
        assert probe(True)==functional_bad
        result={'passed':True,'linked_DSP_product_writers':writers,
                'straight_line_predecessors_checked':2,'violations':0,
                'unsafe_master_mutation_rejected':True,
                'same_functional_arithmetic_does_not_prove_hardware_spacing':True,
                'dynamic_delay_slot_guard_enabled_in_dry_and_paired_tests':True,
                'interrupts_or_DAC_waveform_verified':False,'commercial_data':False}
    result['elf_sha256']=hashlib.sha256(args.elf.read_bytes()).hexdigest()
    result['primary_manual']='NEC U10504EJ7V0UM00 p479; entire-pipeline multiply stall p76'
    if args.json_output: args.json_output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
