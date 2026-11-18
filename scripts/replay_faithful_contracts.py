#!/usr/bin/env python3
"""Replay immutable R17 window/OBJ/Math contracts against the actual port ELFs.

The emulator build has no historical Git dependency. This optional proof uses
only original numeric fixtures and pinned test interpreters; no ROM, capture,
modified menu or physical console is involved.
"""
import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from check_faithful_reference import ROOT, SOURCE, FLAGS, original


PINNED = ('scripts/test_rsp_window_spans_compiled.py',
    'scripts/test_hcomp_obj_rows.py', 'scripts/test_hcomp_aligned_targets.py',
    'scripts/test_rsp_math_fullrow.py', 'scripts/test_rsp_math_dma.py',
    'scripts/test_rsp_sparse_vram.py', 'scripts/test_hcomp_packed_math.py',
    'scripts/test_hcomp_eligibility_tags.py', 'scripts/test_hcomp_sub_presence.py',
    'docs/gate-c-a3/test_hcomp_direct_backdrop.py',
    'scripts/check_rsp_branch_delay_slots.py', 'scripts/native_diag_report.py',
    'scripts/test_gate_c_cgram_rsp_consumer_clean_contract.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--cc')
    parser.add_argument('--json-output', type=Path)
    parser.add_argument('--fixture-dir', type=Path, help='preserve a fresh original-data fixture for diagnosis')
    args = parser.parse_args()
    build = args.build.resolve()/'src'
    compiler = args.cc or shutil.which('mips64-elf-gcc')
    if not compiler:
        prefix = Path(os.environ.get('N64_INST', 'C:/n64-toolchain'))
        compiler = str(prefix/'bin'/('mips64-elf-gcc.exe' if os.name == 'nt' else 'mips64-elf-gcc'))
    prefix = Path(compiler).resolve().parents[1]
    env = os.environ.copy()
    env['PATH'] = str(prefix/'bin')+os.pathsep+env['PATH']
    report = {'passed': False, 'fixture_source': SOURCE,
              'physical_acceptance': False, 'results': {},
              'fixture_input_adaptations': ['Aligned Phase pointer: actual production descriptors carry no historical observer bank tag.'],
              'scope': 'Linked window/OBJ and seeded full-row Math with delayed RSP DMA; no RDP rasterizer, CPU cache, native timing or title model.'}
    if args.fixture_dir:
        args.fixture_dir.mkdir(parents=True, exist_ok=False)
    context = nullcontext(str(args.fixture_dir.resolve())) if args.fixture_dir else tempfile.TemporaryDirectory(prefix='s64-faithful-contracts-')
    with context as directory:
        stage = Path(directory)
        for name in PINNED:
            path = stage/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(subprocess.check_output(['git', '-C', str(ROOT), 'show', SOURCE+':'+name]))
        # The frozen fixture seeded observer ID3 in the Phase pointer. Actual
        # production CPU publications are untagged/aligned (linked ABI proof).
        # Adapt that input, never the VM's alignment or ownership assertions.
        fixture = stage/'scripts/test_rsp_math_fullrow.py'
        text = fixture.read_text()
        tagged = "put(d, addr('OVERLAY_HCOMP_SRC'), PHASE_BANK | 3)"
        assert text.count(tagged) == 1, 'frozen Phase-input anchor drifted'
        fixture.write_text(text.replace(tagged, "put(d, addr('OVERLAY_HCOMP_SRC'), PHASE_BANK)"))
        (stage/'src').mkdir()
        shutil.copyfile(ROOT/'src/renderer/defines.h', stage/'src/defines.h')
        reference = stage/'reference'
        reference.mkdir()
        for name in ('rsp_hcomp_math.S', 'rsp_hcomp_packed_math.inc', 'rsp_hcomp.ld', 'defines.h'):
            (reference/name).write_bytes(original(name))
        flags = ['-D'+name+'=1' for name in FLAGS if name != 'SODIUM64_HCOMP_FULL_ROW_MATH']
        flags += ['-DSODIUM64_HCOMP_FULL_ROW_MATH=0', '-DSODIUM64_TMEM_ATLAS_BITS=3', '-DSODIUM64_PROFILE=1']
        baseline = reference/'math-ordinary.elf'
        subprocess.run([compiler, '-march=mips1', '-mabi=32', '-Wa,--fatal-warnings',
            *flags, '-L'+str(prefix/'mips64-elf/lib'), '-nostartfiles',
            '-Wl,-T'+str(reference/'rsp_hcomp.ld'), '-Wl,--gc-sections',
            '-o', str(baseline), str(reference/'rsp_hcomp_math.S')], check=True, env=env)
        main, mode7 = build/'rsp_main.elf', build/'rsp_mode7.elf'
        cases = [('windows', 'test_rsp_window_spans_compiled.py', [main, mode7]),
                 ('OBJ_rows', 'test_hcomp_obj_rows.py', [main, mode7]),
                 ('fullrow_Math_DMA', 'test_rsp_math_fullrow.py',
                  [main, build/'rsp_hcomp_math.elf', build/'rsp_hcomp.elf', '--baseline', baseline])]
        for name, script, arguments in cases:
            output = stage/(name+'.json')
            result = subprocess.run([sys.executable, str(stage/'scripts'/script),
                *map(str, arguments), '--output', str(output)], check=False,
                capture_output=True, text=True, env=env)
            if result.returncode:
                report['failed_contract'] = name
                report['failure'] = result.stdout+result.stderr
                if args.json_output:
                    args.json_output.write_text(json.dumps(report, indent=2)+'\n')
                raise RuntimeError(name+'\n'+result.stdout+result.stderr)
            data = json.loads(output.read_text())
            if name == 'windows':
                assert data['passed'] and data['compiled_cases'] == 1792 and data['negative_mutations_rejected'] == 2
            elif name == 'OBJ_rows':
                assert data['passed'] and data['objects'] == 28672 and data['drawn_rows'] > 0 and data['culled_rows'] > 0
            else:
                assert data['candidate_passed'] and not data['baseline_only'] and data['cases'] > 0 and data['pixels'] > 0 and len(data['negative_guards']) == 3
            report['results'][name] = data
            print(result.stdout, end='')
        report['passed'] = True
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': report['passed'], 'contracts': list(report['results']),
                      'physical_acceptance': False, 'scope': report['scope']}))


if __name__ == '__main__':
    main()
