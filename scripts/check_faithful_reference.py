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

from linked_cpu_regression import load_elf
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
              'reference_patches': 'Explicit NOP after shared_decode4 JR t4 in each resident bank.',
              'scope': 'Complete linked RSP text/data/extents and PPU object sections/relocations; execution, RDP rasterization and native timing are separate gates.',
              'physical_acceptance': False, 'banks': {}}
    with tempfile.TemporaryDirectory(prefix='s64-faithful-reference-') as directory:
        stage = Path(directory)
        source_names = [name+'.S' for name in BANKS]
        source_names += ['ppu.S', 'defines.h', 'rsp_hcomp.ld', 'rsp_hcomp_packed_math.inc',
                         'rsp_tmem_atlas.inc', 'rsp_tmem_coord.inc']
        for name in source_names:
            text = original(name).decode()
            if name in ('rsp_main.S', 'rsp_mode7.S'):
                start = text.index('shared_decode4:')
                end = text.index('jr t4', start)+len('jr t4')
                text = text[:end]+'\n    nop\n'+text[end:]
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
            report['banks'][name] = {'all_allocated_bytes_and_addresses_identical': True,
                'allocated_bytes': len(candidate_bytes), 'text_bytes': len(text),
                'text_sha256': hashlib.sha256(text).hexdigest()}
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
