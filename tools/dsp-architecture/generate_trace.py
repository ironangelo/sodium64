#!/usr/bin/env python3
"""Build complete-DSP bus/PCM fixtures. This does not time a resident backend."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from trace_format import read_trace
from validate_corpus import validate_corpus

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / 'vendor/snes_spc'


def instrument(source):
    """Patch only observation points in a temporary copy; fail on source drift."""
    replacements = [
        ('#include "blargg_source.h"', '#include "blargg_source.h"\n'
         'extern "C" unsigned char arch_read8(unsigned char*, unsigned);\n'
         'extern "C" unsigned arch_read16(unsigned char*, unsigned char const*);\n'
         'extern "C" void arch_write16(unsigned char*, unsigned char*, int);\n'
         'extern "C" void arch_phase(unsigned);\n'
         'extern "C" void arch_work(unsigned, unsigned);\n'
         'extern "C" bool arch_recording();'),
        ('m.ram [(v->brr_addr + v->brr_offset + 1) & 0xFFFF]',
         'arch_read8(m.ram, (v->brr_addr + v->brr_offset + 1) & 0xFFFF)'),
        ('m.t_brr_next_addr = GET_LE16A( entry );',
         'm.t_brr_next_addr = arch_read16(m.ram, entry);'),
        ('m.ram [(v->brr_addr + v->brr_offset) & 0xFFFF]',
         'arch_read8(m.ram, (v->brr_addr + v->brr_offset) & 0xFFFF)'),
        ('m.ram [v->brr_addr]', 'arch_read8(m.ram, v->brr_addr)'),
        ('int s = GET_LE16SA( ECHO_PTR( ch ) );',
         'int s = (BOOST::int16_t) arch_read16(m.ram, ECHO_PTR(ch));'),
        ('SET_LE16A( ECHO_PTR( ch ), m.t_echo_out [ch] );',
         'arch_write16(m.ram, ECHO_PTR(ch), m.t_echo_out[ch]);'),
        ('#define PHASE( n ) if ( n && !--clocks_remain ) break; case n:',
         '#define PHASE( n ) if ( n && !--clocks_remain ) break; case n: arch_phase(n);'),
        ('inline void SPC_DSP::decode_brr( voice_t* v )\n{',
         'inline void SPC_DSP::decode_brr( voice_t* v )\n{\n'
         '\tarch_work(0, (unsigned)(v-m.voices));'),
        ('inline int SPC_DSP::interpolate( voice_t const* v )\n{',
         'inline int SPC_DSP::interpolate( voice_t const* v )\n{\n'
         '\tarch_work(1, (unsigned)(v-m.voices));'),
        ('inline void SPC_DSP::run_envelope( voice_t* const v )\n{',
         'inline void SPC_DSP::run_envelope( voice_t* const v )\n{\n'
         '\tarch_work(2, (unsigned)(v-m.voices));'),
        ('if ( m.t_pmon & v->vbit )\n\t\tm.t_pitch += ((m.t_output >> 5) * m.t_pitch) >> 10;',
         'if ( m.t_pmon & v->vbit ) {\n'
         '\t\tarch_work(3, (unsigned)(v-m.voices));\n'
         '\t\tm.t_pitch += ((m.t_output >> 5) * m.t_pitch) >> 10;\n\t}'),
        ('if ( m.t_non & v->vbit )\n\t\t\toutput = (int16_t) (m.noise * 2);',
         'if ( m.t_non & v->vbit ) {\n'
         '\t\t\tarch_work(4, (unsigned)(v-m.voices));\n'
         '\t\t\toutput = (int16_t) (m.noise * 2);\n\t\t}'),
        ('#define CALC_FIR( i, ch )   ((ECHO_FIR( i + 1 ) [ch] * (int8_t) REG(fir + i * 0x10)) >> 6)',
         '#define CALC_FIR( i, ch )   (arch_work(5, ch), '
         '((ECHO_FIR( i + 1 ) [ch] * (int8_t) REG(fir + i * 0x10)) >> 6))'),
    ]
    for before, after in replacements:
        assert source.count(before) == 1, ('reference observation anchor drift', before)
        source = source.replace(before, after)
    # The remaining array expression constructs the directory pointer, not a read.
    assert source.count('m.ram [') == 2, 'an APURAM access was not classified'
    return source


MUTANTS = {
    'omit_BRR_decode': ('decode_brr( v );', 'if(!arch_recording()) decode_brr( v );'),
    'omit_Gaussian': ('int output = interpolate( v );', 'int output = arch_recording()?0:interpolate( v );'),
    'omit_PMON': ('m.t_pitch += ((m.t_output >> 5) * m.t_pitch) >> 10;',
                  'if(!arch_recording()) m.t_pitch += ((m.t_output >> 5) * m.t_pitch) >> 10;'),
    'omit_noise': ('output = (int16_t) (m.noise * 2);',
                   'output = arch_recording()?0:(int16_t)(m.noise * 2);'),
    'omit_echo_write': ('arch_write16(m.ram, ECHO_PTR(ch), m.t_echo_out[ch]);',
                        'if(!arch_recording()) arch_write16(m.ram, ECHO_PTR(ch), m.t_echo_out[ch]);'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cxx', default='g++')
    parser.add_argument('--frames', type=int, default=512)
    parser.add_argument('--mutations', action='store_true')
    args = parser.parse_args()
    assert 32 <= args.frames <= 2048
    compiler=shutil.which(args.cxx)
    if compiler is None:
        parser.error('C++ compiler not found; pass --cxx with its executable path')
    args.cxx=str(Path(compiler).resolve())
    args.output.mkdir(parents=True, exist_ok=False)
    upstream = json.loads((VENDOR.parent/'UPSTREAM.json').read_text())
    expected=json.loads((ROOT/'default_corpus.json').read_text())
    assert expected['upstream_commit']==upstream['upstream_commit']
    for name, digest in upstream['unmodified_source_files'].items():
        assert hashlib.sha256((VENDOR/name).read_bytes()).hexdigest() == digest, name
    env = os.environ.copy()
    if os.name == 'nt':
        env['PATH'] = str(Path(args.cxx).resolve().parent)+';'+env['PATH']
    rejected, cases, negative_corpus = [], [], None
    with tempfile.TemporaryDirectory(prefix='s64-integral-dsp-') as temporary:
        stage = Path(temporary)
        for header in VENDOR.glob('*.h'):
            shutil.copy2(header, stage/header.name)
        source = (VENDOR/'SPC_DSP.cpp').read_text()
        traced = instrument(source)
        (stage/'reference.cpp').write_text(source)
        (stage/'traced.cpp').write_text(traced)
        flags = ['-std=c++98', '-O2', '-fwrapv', '-fno-strict-aliasing',
                 '-fno-rtti', '-fno-exceptions', '-I'+str(stage)]
        def compile_one(name, definitions):
            file = ROOT/'fixture.cpp' if name == 'fixture' else stage/(name+'.cpp')
            subprocess.run([args.cxx, *flags, *definitions, '-c', str(file),
                            '-o', str(stage/(name+'.o'))], check=True, env=env)
        compile_one('reference', ['-DSPC_DSP=Reference_DSP', '-DSPC_State_Copier=Reference_State_Copier'])
        compile_one('fixture', [])
        exe = stage/('fixture.exe' if os.name == 'nt' else 'fixture')
        def link_traced():
            compile_one('traced', ['-DSPC_DSP=Trace_DSP', '-DSPC_State_Copier=Trace_State_Copier'])
            subprocess.run([args.cxx, str(stage/'reference.o'), str(stage/'traced.o'),
                            str(stage/'fixture.o'), '-o', str(exe)], check=True, env=env)
        link_traced()
        for scenario in range(4):
            path = args.output/('scenario-'+str(scenario)+'.s64darc')
            result = subprocess.run([str(exe), str(scenario), str(args.frames), str(path)],
                                    capture_output=True, text=True, env=env, timeout=60)
            if result.returncode:
                raise RuntimeError(result.stdout+result.stderr)
            counts = {key:int(value) for key,value in re.findall(r'(\w+)=(\d+)', result.stdout)}
            decoded = read_trace(path)
            replay = subprocess.run([str(exe),'replay',str(path)],capture_output=True,
                                    text=True,env=env,timeout=60)
            if replay.returncode:
                raise RuntimeError(replay.stdout+replay.stderr)
            repeated=stage/('repeat-'+str(scenario)+'.s64darc')
            repeat=subprocess.run([str(exe),str(scenario),str(args.frames),str(repeated)],
                                  capture_output=True,text=True,env=env,timeout=60)
            if repeat.returncode:
                raise RuntimeError(repeat.stdout+repeat.stderr)
            assert path.read_bytes()==repeated.read_bytes(),'nondeterministic fixture payload'
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if args.frames==expected['frames']:
                assert digest==expected['sha256'][path.name],('canonical corpus drift',path.name,digest)
            assert counts['clocks'] == args.frames*32
            assert counts['phase_mask'] == 0xffffffff
            assert counts['full_state_checks'] == args.frames*32+2
            assert counts['pcm_frames'] == args.frames and counts['nonzero_pcm'] > 0
            assert counts['max_active_mask'] == (1 if scenario == 0 else 255), counts
            assert all(counts['brr'+str(i)] > 0 for i in range(8))
            if scenario >= 2:
                assert counts['pmon'] > 0 and counts['noise'] > 0 and counts['echo_writes'] > 0
                if args.frames >= 512:
                    assert counts['echo_wraps'] > 0
            cases.append(dict(scenario=scenario, counts=counts, artifact=path.name,
                              sha256=digest,
                              bytes=path.stat().st_size, decoded=decoded,
                              complete_reference_replay=True,byte_exact_repeated_generation=True))
            print(result.stdout.strip())
        if args.mutations:
            negative_corpus=validate_corpus(
                [args.output/case['artifact'] for case in cases],
                lambda path:subprocess.run([str(exe),'replay',str(path)],capture_output=True,
                                          text=True,env=env,timeout=60),stage)
            for name,(before,after) in MUTANTS.items():
                assert traced.count(before) == 1, name
                (stage/'traced.cpp').write_text(traced.replace(before,after))
                link_traced()
                result = subprocess.run([str(exe),'2',str(args.frames),str(stage/'mutant.bin')],
                                        capture_output=True,text=True,env=env,timeout=60)
                assert result.returncode != 0 and 'FAIL ' in result.stderr, (name,result.stdout,result.stderr)
                rejected.append(name)
                print('REJECTED '+name+': '+result.stderr.strip())
    report = {'status':'COMPLETE_DSP_REFERENCE_FIXTURES_VALIDATED',
              'native_integral_cost_status':'NOT_MEASURED',
              'resident_complete_RSP_backend':False,
              'live_SPC_bridge_implemented':False,
              'producer_scope':'Original synthetic bus schedule; not live SPC instruction execution.',
              'representativeness':'Three synthetic nominal controls plus one explicit bus/FIFO stress case; private live-driver coverage remains pending.',
              'core_scope':'Unmodified complete pinned DSP versus observation-only copy; full state/RAM/PCM every clock.',
              'directory_scope':'Admitted nonwrapping DIR/SRCN traces; known exhaustive R61 wrap requirement remains.',
              'runtime_scope':'Host reference tool only; no gameplay backend or native cost result.',
              'commercial_data':False,
              'sample_rate':32000,'frames_per_scenario':args.frames,
              'upstream_commit':upstream['upstream_commit'],
              'tool_sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                              for name in ('fixture.cpp','generate_trace.py','trace_format.py','validate_corpus.py')},
              'cases':cases,'actual_source_mutants_rejected':rejected,
              'negative_corpus_controls':negative_corpus}
    (args.output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Reference fixture proof complete. Native integral cost remains NOT_MEASURED.')


if __name__ == '__main__':
    main()
