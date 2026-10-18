#!/usr/bin/env python3
"""Recompile frozen R17 plus the integrated decoder repair; compare all RSP bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
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
              'scope': 'Complete linked RSP text/data/extents; CPU producer, RDP rasterization and native timing are separate gates.',
              'physical_acceptance': False, 'banks': {}}
    with tempfile.TemporaryDirectory(prefix='s64-faithful-reference-') as directory:
        stage = Path(directory)
        source_names = [name+'.S' for name in BANKS]
        source_names += ['defines.h', 'rsp_hcomp.ld', 'rsp_hcomp_packed_math.inc',
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
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'banks'} |
                     {'banks_identical': len(report['banks'])}))


if __name__ == '__main__':
    main()
