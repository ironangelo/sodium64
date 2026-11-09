#!/usr/bin/env python3
"""Recompile frozen R17 plus the integrated decoder repair; compare all RSP bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

from linked_cpu_regression import CPU, load_elf
from check_rsp_branch_delay_slots import read_text

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '238170abf956da705806f979f9cc256fbc565ac0'
FLAGS = ('SODIUM64_HCOMP_WIDE_MATH', 'SODIUM64_ELIGIBILITY_TAGS',
    'SODIUM64_HCOMP_MASK_SCAN', 'SODIUM64_HCOMP_TLUT_SHADER',
    'SODIUM64_HCOMP_FULL_ROW_MATH', 'SODIUM64_HCOMP_RDP_HALF_MATH',
    'SODIUM64_HCOMP_FIXED_WINDOW_MATH', 'SODIUM64_HCOMP_RDP_FIXED_MATH',
    'SODIUM64_TMEM_ATLAS', 'SODIUM64_TMEM_COORD_ATLAS')
BANKS = ('rsp_main', 'rsp_mode7', 'rsp_hcomp', 'rsp_hcomp_math',
    'rsp_hcomp_fast', 'rsp_hcomp_setup', 'rsp_hcomp_tlut', 'rsp_hcomp_rdp',
    'rsp_hcomp_fixed_window', 'rsp_hcomp_rdp_fixed', 'rsp_mode7_window', 'rsp_object_cache')


def original(name):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', SOURCE+':src/'+name])


def fold_laboratory_limit(name, text):
    """Explicit reference delta: the retained ordinary path always used zero.

    Fold seven old diagnostic reads/branches, preserving register effects and
    instruction counts so fixed IMEM slots and caller entry points stay put.
    Execution contracts independently check the resulting production behavior.
    """
    branches = {'rsp_main.S': ('t0', 'hcomp_resident_admit_fallback'),
        'rsp_hcomp_fixed_window.S': ('t0', 'hcomp_fixed_window_fallback'),
        'rsp_hcomp_fast.S': ('t2', 'hcomp_fast_return'),
        'rsp_hcomp_rdp.S': ('t0', 'hcomp_rdp_fallback'),
        'rsp_hcomp_rdp_fixed.S': ('t0', 'hcomp_rdp_fixed_fallback'),
        'rsp_hcomp_tlut.S': ('t0', 'hcomp_tlut_reject')}
    if name == 'rsp_hcomp.S':
        old = ('    lw t0, HCOMP_DIAG_COMPOSE_LIMIT\n    beqz t0, hcomp_dispatch_policy\n'
               '    sltu t1, k0, t0\n    bnez t1, hcomp_dispatch_policy\n'
               '    nop\n    li t0, 1\n    sw t0, HCOMP_BAND_RAW\n')
        new = ('    move t0, zero\n    b hcomp_dispatch_policy\n    move t1, zero\n'
               '    nop\n    nop\n    nop\n    nop\n')
    elif name in branches:
        register, target = branches[name]
        old = f'    lw {register}, HCOMP_DIAG_COMPOSE_LIMIT\n    bnez {register}, {target}\n'
        new = f'    move {register}, zero\n    nop\n'
    else:
        return text
    assert text.count(old) == 1, (name, 'frozen laboratory-limit anchor drifted')
    return text.replace(old, new)


def repair_depth_sender(name, text):
    if name != 'rsp_main.S':
        return text
    old = ('bg_window_depth_send:\n    j hcomp_depth_send\n    move ra, v1\n')
    new = ('bg_window_depth_send:\n    move ra, v1\n    .org 0xC4C\n    nop\n')
    assert text.count(old) == 1, 'frozen depth-sender anchor drifted'
    return text.replace(old, new)


def prove_depth_sender(build):
    """Run the emitted overlay call with each resident bank and a poisoned v1."""
    overlay = build/'src/rsp_hcomp.elf'
    base, text = read_text(overlay)
    fixed_entry = 0xa4001c4c
    jal = 0x0c000000 | ((fixed_entry >> 2) & 0x03ffffff)
    calls = [base+i for i in range(0, len(text), 4)
             if int.from_bytes(text[i:i+4], 'big') == jal]
    assert len(calls) == 1, 'expected one overlay depth call'
    call = calls[0]
    slot, _ = load_elf(overlay)

    def run(memory, helper, poison):
        cpu = CPU(memory)
        cpu.pattern()
        cpu.regs[3] = poison
        cpu.regs[4] = 0xf48

        def check_return(machine):
            assert machine.regs[31] & 0xffffffff == call+8, 'depth sender lost overlay ra'
            assert machine.regs[4:6] == [0xf48, 0xf50], 'depth arguments changed'

        cpu.hooks[helper] = check_return
        cpu.execute(call, stop=call+8, max_steps=12)

    cases = 0
    for name in ('rsp_main', 'rsp_mode7'):
        resident, symbols = load_elf(build/'src'/(name+'.elf'))
        assert symbols['hcomp_depth_send_entry'] == fixed_entry, (name, 'depth entry shifted')
        helper = symbols['hcomp_eligibility_depth_send']
        memory = resident | slot
        for poison in (0, 0xa4001c10, 0xdeadbeef):
            run(memory, helper, poison)
            cases += 1
        if name == 'rsp_main':
            # Restore the original Main tail whose window delay slot was called
            # as an entry. The real overlay call must catch its clobbered ra.
            old_tail = bytes.fromhex('0060f8250900041200000000')
            first = fixed_entry & 0x1fffffff
            mutant = memory | {first+i: value for i, value in enumerate(old_tail)}
            try:
                run(mutant, helper, 0xa4001c10)
            except AssertionError as error:
                assert str(error) == 'depth sender lost overlay ra', error
            else:
                raise AssertionError('original Main overlay return fault escaped')
    return {'linked_overlay_cases': cases, 'original_Main_return_fault_rejected': True,
            'common_IMEM_entry': hex(fixed_entry & 0xfff)}


def prove_limit_elision(before, after):
    """Execute only the changed scalar span; compare ordinary zero-limit state.

    Poison the retired word in the new code to prove it is never read. This is
    scalar state/read ownership, not RSP pipeline, vector or native timing proof.
    """
    base, old = read_text(before)
    new_base, new = read_text(after)
    assert base == new_base and len(old) == len(new)
    _, symbols = load_elf(before)
    words = struct.unpack('>'+str(len(old)//4)+'I', old)
    reads = [i for i, word in enumerate(words) if word >> 26 == 35
             and word >> 21 & 31 == 0 and word & 65535 == 0xecc]
    assert len(reads) == 1, 'expected exactly one frozen limit read per folded bank'
    entry = base+4*reads[0]
    phase = before.name.startswith('rsp_hcomp-before')
    end = symbols['hcomp_dispatch_policy'] if phase else entry+12

    class TraceCPU(CPU):
        def __init__(self, memory):
            super().__init__(memory)
            self.limit_reads = 0

        def read(self, address, size=4):
            if address & 0x1fffffff == 0xecc:
                self.limit_reads += 1
            return super().read(address, size)

    cases = 0
    for pattern in range(4):
        results = []
        for code, poison in [(old, 0), *((new, value) for value in (0, 1, 0xdeadbeef, 0xffffffff))]:
            memory = {i: (i*37+pattern*11) & 255 for i in range(4096)}
            memory.update(((base+i) & 0x1fffffff, value) for i, value in enumerate(code))
            memory.update((0xecc+i, value) for i, value in enumerate(poison.to_bytes(4, 'big')))
            cpu = TraceCPU(memory)
            cpu.pattern(pattern)
            cpu.execute(entry, stop=end, max_steps=12)
            assert not cpu.memory_writes, 'fold changed DMEM ownership'
            results.append((cpu.regs, cpu.hi, cpu.lo, cpu.cp))
            assert cpu.limit_reads == (1 if code is old else 0), 'retired laboratory word accessed'
        assert all(result == results[0] for result in results[1:]), 'fold changed ordinary scalar state'
        cases += 4
    changed = sum(a != b for a, b in zip(words, struct.unpack('>'+str(len(new)//4)+'I', new)))
    assert changed == (6 if phase else 2), 'unexpected executable change outside limit fold'
    return {'scalar_cases': cases, 'poison_values': 4, 'changed_instruction_words': changed,
            'ordinary_register_state_identical': True, 'production_limit_reads': 0}


def relocatable_image(path):
    """Retain section identity and normalize relocation symbol indexes.

    CPU object sections share address zero, so load_elf's final-image memory
    dictionary cannot compare this producer safely. Include all ALLOC sections
    and relocation targets/addends rather than comparing only instruction text.
    """
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x01\x02', 'expected big-endian ELF32 object'
    header = struct.unpack_from('>16sHHIIIIIHHHHHH', data)
    sections = [struct.unpack_from('>IIIIIIIIII', data, header[6]+i*header[11])
                for i in range(header[12])]
    strings = sections[header[13]]
    names = data[strings[4]:strings[4]+strings[5]]
    labels = [names[s[0]:].split(b'\0', 1)[0].decode() for s in sections]
    allocated = {labels[i]: (s[1], s[3], bytes(s[5]) if s[1] == 8
                            else data[s[4]:s[4]+s[5]])
                 for i, s in enumerate(sections) if s[2] & 2}
    tables = {}
    for i, s in enumerate(sections):
        if s[1] != 2:
            continue
        strings = sections[s[6]]
        names = data[strings[4]:strings[4]+strings[5]]
        table = []
        for at in range(s[4], s[4]+s[5], s[9]):
            name, value, _, info, _, index = struct.unpack_from('>IIIBBH', data, at)
            label = names[name:].split(b'\0', 1)[0].decode() if name else (
                '@'+labels[index] if index < len(labels) else '')
            table.append((label, value, info))
        tables[i] = table
    relocations = []
    for s in sections:
        if s[1] not in (4, 9):
            continue
        for at in range(s[4], s[4]+s[5], s[9]):
            offset, info = struct.unpack_from('>II', data, at)
            addend = struct.unpack_from('>i', data, at+8)[0] if s[1] == 4 else None
            relocations.append((labels[s[7]], offset, info & 255,
                                tables[s[6]][info >> 8], addend))
    return allocated, relocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--cc')
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    compiler = args.cc or shutil.which('mips64-elf-gcc')
    if not compiler:
        prefix = Path(os.environ.get('N64_INST', 'C:/n64-toolchain'))
        compiler = str(prefix/'bin'/('mips64-elf-gcc.exe' if os.name == 'nt' else 'mips64-elf-gcc'))
    prefix = Path(compiler).resolve().parents[1]
    flags = ['-D'+name+'=1' for name in FLAGS]
    # Frozen PROFILE selects D2000 and introduces no RSP observation code.
    flags += ['-DSODIUM64_TMEM_ATLAS_BITS=3', '-DSODIUM64_PROFILE=1']
    env = os.environ.copy()
    env['PATH'] = str(prefix/'bin')+os.pathsep+env['PATH']
    report = {'passed': True, 'source': SOURCE,
              'reference_patches': 'Decoder JR return NOPs; seven laboratory limit folds; fixed Main/Mode 7 depth sender entry at C4C.',
              'scope': 'Complete linked RSP text/data/extents and PPU object sections/relocations; execution, RDP rasterization and native timing are separate gates.',
              'physical_acceptance': False, 'banks': {}, 'laboratory_limit_elision': {}}
    with tempfile.TemporaryDirectory(prefix='s64-faithful-reference-') as directory:
        stage = Path(directory)
        source_names = [name+'.S' for name in BANKS]
        source_names += ['ppu.S', 'defines.h', 'rsp_hcomp.ld', 'rsp_hcomp_packed_math.inc',
                         'rsp_tmem_atlas.inc', 'rsp_tmem_coord.inc']
        before_sources = {}
        for name in source_names:
            text = original(name).decode()
            if name in ('rsp_main.S', 'rsp_mode7.S'):
                start = text.index('shared_decode4:')
                end = text.index('jr t4', start)+len('jr t4')
                text = text[:end]+'\n    nop\n'+text[end:]
            text = repair_depth_sender(name, text)
            before_sources[name] = text
            text = fold_laboratory_limit(name, text)
            (stage/name).write_text(text)
        for name in BANKS:
            resident = name in ('rsp_main', 'rsp_mode7')
            script = str(prefix/'mips64-elf/lib/rsp.ld') if resident else str(stage/'rsp_hcomp.ld')
            binary = stage/(name+'.elf')
            result = subprocess.run([compiler, '-march=mips1', '-mabi=32', '-Wa,--fatal-warnings',
                *flags, '-L'+str(prefix/'mips64-elf/lib'), '-nostartfiles', '-Wl,-T'+script,
                '-Wl,--gc-sections', '-o', str(binary), str(stage/(name+'.S'))],
                check=False, capture_output=True, text=True, env=env)
            if result.returncode:
                raise RuntimeError(result.stdout+result.stderr)
            candidate = args.build/'src'/(name+'.elf')
            reference_bytes, _ = load_elf(binary)
            candidate_bytes, _ = load_elf(candidate)
            assert reference_bytes == candidate_bytes, (name, 'complete reference text/data drift')
            text = read_text(candidate)[1]
            assert len(text) == (4096 if resident else 1000), (name, 'fixed bank size')
            words = struct.unpack('>'+str(len(text)//4)+'I', text)
            assert not any(word >> 26 == 35 and word >> 21 & 31 == 0
                           and word & 65535 == 0xecc for word in words), (name, 'laboratory limit read retained')
            report['banks'][name] = {'all_allocated_bytes_and_addresses_identical': True,
                'allocated_bytes': len(candidate_bytes), 'text_bytes': len(text),
                'text_sha256': hashlib.sha256(text).hexdigest()}
            source_name = name+'.S'
            if fold_laboratory_limit(source_name, before_sources[source_name]) != before_sources[source_name]:
                before_source = stage/(name+'-before.S')
                before_source.write_text(before_sources[source_name])
                before_binary = stage/(name+'-before.elf')
                result = subprocess.run([compiler, '-march=mips1', '-mabi=32', '-Wa,--fatal-warnings',
                    *flags, '-L'+str(prefix/'mips64-elf/lib'), '-nostartfiles', '-Wl,-T'+script,
                    '-Wl,--gc-sections', '-o', str(before_binary), str(before_source)],
                    check=False, capture_output=True, text=True, env=env)
                if result.returncode:
                    raise RuntimeError(result.stdout+result.stderr)
                report['laboratory_limit_elision'][name] = prove_limit_elision(before_binary, candidate)
        assert len(report['laboratory_limit_elision']) == 7
        report['depth_sender'] = prove_depth_sender(args.build)
        candidate_sections, candidate_relocations = relocatable_image(args.build/'src/ppu.o')
        ppu_flags = list(flags)
        if any(relocation[3][0].startswith('remote_') for relocation in candidate_relocations):
            ppu_flags.append('-DSODIUM64_REMOTE=1')
        producer = stage/'ppu.o'
        result = subprocess.run([compiler, '-c', '-mtune=vr4300', '-march=vr4300',
            '-Wa,--fatal-warnings', *ppu_flags, '-o', str(producer), str(stage/'ppu.S')],
            check=False, capture_output=True, text=True, env=env)
        if result.returncode:
            raise RuntimeError(result.stdout+result.stderr)
        reference_sections, reference_relocations = relocatable_image(producer)
        assert reference_sections == candidate_sections, 'complete PPU allocated-section drift'
        assert reference_relocations == candidate_relocations, 'PPU relocation target/addend drift'
        report['PPU_producer'] = {'all_allocated_sections_and_relocations_identical': True,
            'sections': {name: len(value[2]) for name, value in candidate_sections.items()},
            'normalized_relocations': len(candidate_relocations),
            'USB_callsite_selected': '-DSODIUM64_REMOTE=1' in ppu_flags}
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'banks'} |
                     {'banks_identical': len(report['banks'])}))


if __name__ == '__main__':
    main()
