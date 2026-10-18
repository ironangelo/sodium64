#!/usr/bin/env python3
"""Execute CPU overlay publication, including uncached fallback descriptors.

This checks the linked instructions and their exact writes. RSP consumption,
cache/DMA timing and rasterized pixels need their own contracts.
"""
import argparse
import json
from pathlib import Path

from check_faithful_renderer_owners import read_macros
from linked_cpu_regression import CPU, load_elf
from test_faithful_rom_cache import word, put_word


def check(memory, symbols, macros):
    def source(name, offset=0):
        return (symbols[name+'_text_start']+offset) & 0xffffffff

    def slot(name):
        return 0xa4000000+macros.name('OVERLAY_'+name+'_SRC')

    def descriptor(name):
        return (symbols[name+'_data_start'] | 0x20000000) & 0xffffffff

    expected = [(slot('OBJECT_CACHE'), source('rsp_object_cache')),
                (slot('MODE7'), source('rsp_mode7_window')),
                (slot('MODE7_DRAW'), source('rsp_mode7', 0x3a8)),
                (slot('MAIN'), source('rsp_main', 0x3a8)),
                (slot('HCOMP'), source('rsp_hcomp')),
                (descriptor('rsp_hcomp_fixed_window'), source('rsp_hcomp_math')),
                (descriptor('rsp_hcomp_rdp_fixed'), source('rsp_hcomp_fixed_window')),
                (descriptor('rsp_hcomp_rdp'), source('rsp_hcomp_rdp_fixed')),
                (slot('HCOMP_MATH'), source('rsp_hcomp_rdp')),
                (slot('HCOMP_SETUP'), source('rsp_hcomp_setup')),
                (slot('HCOMP_FAST'), source('rsp_hcomp_fast')),
                (slot('HCOMP_TLUT'), source('rsp_hcomp_tlut'))]
    stores = []
    for ordinal in range(4):
        cpu = CPU(memory.copy())
        cpu.pattern(ordinal)
        cpu.allow_rcp_writes = True
        original = cpu.regs.copy(), cpu.hi, cpu.lo, cpu.cp.copy()
        writes = []
        stores = []
        for at in range(symbols['faithful_overlay_bind_begin'], symbols['faithful_overlay_bind_end'], 4):
            instruction = word(memory, at)
            if instruction >> 26 == 43:
                base = instruction >> 21 & 31
                immediate = instruction & 65535
                if immediate & 32768:
                    immediate -= 65536

                def observe(c, base=base, immediate=immediate, at=at):
                    writes.append((c.regs[base]+immediate) & 0xffffffff)
                    stores.append(at)
                cpu.before_instruction[at] = observe
        cpu.execute(symbols['faithful_overlay_bind_begin'],
                    stop=symbols['faithful_overlay_bind_end'], max_steps=100)
        assert writes == [address for address, _ in expected], 'uncached overlay publication'
        assert cpu.memory_writes == [(address & 0x1fffffff, 4, value)
                                     for address, value in expected], 'overlay publication'
        assert all(cpu.regs[i] == original[0][i] for i in range(32) if i not in (1, 8, 9, 10)), 'binding register ownership'
        assert (cpu.hi, cpu.lo, cpu.cp) == original[1:], 'binding special register ownership'
    return stores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path, nargs='+')
    parser.add_argument('--defines', type=Path, default=Path(__file__).resolve().parents[1]/'src/defines.h')
    parser.add_argument('--cc')
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    macros = read_macros(args.defines, args.cc)
    variants = []
    for path in args.elf:
        memory, symbols = load_elf(path)
        stores = check(memory, symbols, macros)
        span = range(symbols['faithful_overlay_bind_begin'], symbols['faithful_overlay_bind_end'], 4)
        ors = [at for at in span if word(memory, at) == (9 << 21 | 10 << 16 | 9 << 11 | 0x25)]
        assert len(stores) == 12 and len(ors) == 3, 'linked publication anchors drifted'
        faults = [('missing_Mode7_source', stores[1], 0),
                  ('missing_fallback_descriptor', stores[5], 0),
                  ('wrong_fallback_source', stores[5], word(memory, stores[5]) ^ (1 << 16)),
                  ('cached_fallback_descriptor', ors[0], 0)]
        rejected = []
        for name, at, value in faults:
            changed = memory.copy()
            put_word(changed, at, value)
            try:
                check(changed, symbols, macros)
            except AssertionError as error:
                assert str(error) in ('uncached overlay publication', 'overlay publication'), str(error)
                rejected.append(name)
            else:
                raise AssertionError(('emitted binding fault escaped', name))
        variants.append({'elf': str(path), 'linked_register_cases': 4,
                         'writes_per_case': 12, 'faults_rejected': rejected})
    report = {'passed': True, 'variants': variants, 'physical_acceptance': False,
              'scope': 'CPU source/uncached descriptor publication and register ownership only; no RSP DMA, rasterization or timing model.'}
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
