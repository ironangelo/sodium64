#!/usr/bin/env python3
"""Check actual CPU tables and embedded RSP DMA owners in extended observers."""
import argparse
import hashlib
import json
from pathlib import Path
from check_event_arena import selected_macros
from check_remote_boot import elf
from check_runtime_arena import allocated_sections


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(path, cpu_overrides=None, bank_overrides=None):
    symbols, original = elf(path)
    full_probe=bool({'full_dsp_probe_execute','full_dsp_probe_execute_mode'} & symbols.keys())
    require('dsp_audio_blocks' in symbols or 'dsp_brr_records' in symbols or 'dsp_mix_records' in symbols or full_probe, 'expected linked extended observer')
    cpu_overrides = cpu_overrides or {}
    word = lambda address: cpu_overrides.get(address, original(address))
    defines = Path(__file__).resolve().parents[1] / 'src/defines.h'
    macros = selected_macros(defines, diagnostic_trace=True,
                             brr_observer='dsp_brr_records' in symbols,
                             mix_observer='dsp_mix_records' in symbols,
                             full_dsp_probe=full_probe,
                             audio_observer='dsp_audio_blocks' in symbols)
    tables = [('hcomp_cgram_base_queues', 'BASE'),
              ('hcomp_cgram_sideband_queues', 'SIDEBAND'),
              ('hcomp_cgram_event_queues', 'EVENT')]
    for symbol, kind in tables:
        for queue in (1, 2):
            expected = macros.name(f'HCOMP_CGRAM_{kind}_QUEUE{queue}') & 0xffffffff
            actual = word(symbols[symbol] + 4 * (queue-1))
            require(actual == expected, f'CPU {kind}{queue} {actual:#x} != {expected:#x}')
    backup = macros.name('HCOMP_CGRAM_SIDEBAND_QUEUE1') & 0xffffffff
    require(backup + 1024 <= macros.name('HCOMP_CGRAM_SIDEBAND_QUEUE2'), 'backup extent')
    vram_table = macros.name('VRAM_TABLE')
    owners = list(allocated_sections(path))
    sites = []
    bank_bindings = []
    for bank in ('rsp_hcomp_math', 'rsp_hcomp_fixed_window'):
        bank_path = path.parent / 'src' / (bank + '.elf')
        _, bank_original = elf(bank_path)
        replacements = (bank_overrides or {}).get(bank, {})
        bank_word = lambda address: replacements.get(address, bank_original(address))
        start, end = symbols[bank+'_text_start'], symbols[bank+'_text_end']
        require(end-start == 0x3e8, bank+' slot size')
        for offset in range(0, end-start, 4):
            require(word(start+offset) == bank_word(0xa40013a8+offset), bank+' embedded text mismatch')
        bank_sites = []
        for pc in range(0xa40013b4, 0xa400178c, 4):
            instruction = bank_word(pc)
            if instruction >> 26 != 3:
                continue
            target = ((pc+4) & 0xf0000000) | ((instruction & 0x3ffffff) << 2)
            if target not in (0xa4001f08, 0xa4001f40):
                continue
            if bank_word(pc-12) != (0x24040000 | vram_table):
                continue
            # Execute the literal address construction at the actual DMA call.
            hi, lo = bank_word(pc-8), bank_word(pc-4)
            require(hi >> 16 == 0x3c05 and lo >> 16 == 0x34a5, bank+' backup address construction')
            require(bank_word(pc+4) == 0x240603ff, bank+' backup DMA length')
            actual = ((hi & 0xffff) << 16) | (lo & 0xffff)
            require(actual == backup, f'{bank} DMA backup {actual:#x} != CPU owner {backup:#x}')
            lo_address = actual & 0x1fffffff
            for name, begin, stop in owners:
                require(not (begin < lo_address+1024 and stop > lo_address), bank+' DMA overlaps '+name)
            bank_sites.append({'pc': f'{pc:08x}', 'direction': 'write' if target==0xa4001f08 else 'read',
                               'rdram_start': f'{actual:08x}', 'bytes': 1024})
        require(len(bank_sites)==2 and {s['direction'] for s in bank_sites}=={'write','read'}, bank+' missing backup/restore DMA')
        sites.extend(bank_sites)
        bank_bindings.append((bank, start, bank_path))
    return {'passed': True, 'cpu_queue_words': 6, 'embedded_banks': 2,
            'actual_dma_sites': sites, 'linked_elf_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, bank_bindings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    proof, bindings = inspect(args.elf)
    symbols, word = elf(args.elf)
    rejected = []
    changes = [('CPU_queue_disagreement', {symbols['hcomp_cgram_base_queues']: word(symbols['hcomp_cgram_base_queues']) ^ 0x2000}, {})]
    bank, embedded, bank_path = bindings[0]
    _, rsp_word = elf(bank_path)
    pc = int(proof['actual_dma_sites'][0]['pc'], 16)-4
    offset = pc-0xa40013a8
    changed = (rsp_word(pc) & ~0xffff) | 0x2400
    changes.append(('stale_RSP_backup', {embedded+offset: changed}, {bank: {pc: changed}}))
    changes.append(('embedded_bank_disagreement', {embedded+offset: changed}, {}))
    for name, cpu_change, rsp_change in changes:
        try:
            inspect(args.elf, cpu_change, rsp_change)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('escaped mutation: '+name)
    proof['negative_mutations_rejected'] = rejected
    proof['physical_acceptance'] = False
    if args.json_output:
        args.json_output.write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    try:
        main()
    except ValueError as error:
        raise SystemExit(str(error))
