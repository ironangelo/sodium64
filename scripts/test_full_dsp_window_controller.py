#!/usr/bin/env python3
"""Semantic bus-window proof using unchanged immediate production DSP as oracle."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cxx', default=os.environ.get('CXX', 'g++'))
    p.add_argument('--output', type=Path)
    p.add_argument('--mutations', action='store_true')
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    flags = ['-std=c++98', '-O2', '-DNDEBUG', '-fno-exceptions', '-fno-rtti']
    mutants = {
        'future_RAM_visible': ('else events[count++] = event;',
                               'else { if (!reg) shadow[addr] = (unsigned char)data; events[count++] = event; }'),
        'late_event_replay': ('if (event.clock > cursor) core->run(event.clock - cursor);',
                              'apply(event); if (event.clock > cursor) core->run(event.clock - cursor);'),
        'missing_echo_RAM_barrier': ('if (echo_hazard(addr)) flush();', '(void)addr;'),
        'wrong_post_latch_echo_pointer': ('core->m.phase <= 22 ?', 'core->m.phase <= 30 ?'),
        'missing_DSP_register_read_barrier': ('flush();\n    return core->read(addr);', 'return core->read(addr);'),
        'FIFO_drops_old_events': ('if (count == event_capacity) flush();', 'if (count == event_capacity) count = 0;'),
        'missing_echo_publication': ('self->cpu[addr] = bytes[0]; self->cpu[addr + 1] = bytes[1];', '(void)bytes;'),
        'missing_PCM_consumption_barrier': ('int SPC_DSP_Window::sample_count() { flush();', 'int SPC_DSP_Window::sample_count() {'),
        'missing_export_barrier': ('flush(); core->copy_state(io, copy);', 'core->copy_state(io, copy);'),
        'missing_soft_reset_barrier': ('void SPC_DSP_Window::soft_reset() { flush();', 'void SPC_DSP_Window::soft_reset() {'),
    }
    rejected = []
    with tempfile.TemporaryDirectory(prefix='s64-full-window-') as tmp:
        stage = Path(tmp)
        (stage/'third_party/snes_spc').mkdir(parents=True)
        (stage/'src').mkdir()
        (stage/'scripts/fixtures').mkdir(parents=True)
        for f in (root/'third_party/snes_spc').glob('*.h'):
            shutil.copy2(f, stage/'third_party/snes_spc'/f.name)
        for rel in ['third_party/snes_spc/SPC_DSP.cpp', 'src/full_dsp_window.h',
                    'src/full_dsp_window.cpp', 'scripts/fixtures/full_dsp_window_controller_host.cpp']:
            shutil.copy2(root/rel, stage/rel)
        core = stage/'third_party/snes_spc/SPC_DSP.cpp'
        window = stage/'src/full_dsp_window.cpp'
        fixture = stage/'scripts/fixtures/full_dsp_window_controller_host.cpp'
        reference, candidate, host = [stage/(n+'.o') for n in ['reference', 'candidate', 'fixture']]
        def compile_obj(src, out, defines):
            subprocess.run([a.cxx, *flags, *defines, '-c', str(src), '-o', str(out)], check=True)
        compile_obj(core, reference, ['-DSPC_DSP=Reference_DSP', '-DSPC_State_Copier=Reference_State_Copier'])
        compile_obj(core, candidate, ['-DSODIUM64_DSP_FULL_WINDOW=1'])
        compile_obj(fixture, host, [])
        def run():
            obj, exe = stage/'window.o', stage/('window.exe' if os.name == 'nt' else 'window')
            compile_obj(window, obj, ['-DSODIUM64_DSP_FULL_WINDOW=1', '-Wall', '-Wextra', '-Werror'])
            subprocess.run([a.cxx, str(reference), str(candidate), str(host), str(obj), '-o', str(exe)], check=True)
            return subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
        result = run()
        print(result.stdout+result.stderr, end='')
        result.check_returncode()
        counts = dict((k, int(v)) for k, v in re.findall(r'(\w+)=(\d+)', result.stdout))
        assert counts['state_checks'] > 4096 and counts['producer_reads'] > 4096
        assert counts['FIFO_overflow'] == 31 and counts['original_hazards'] == 4
        original = window.read_text()
        if a.mutations:
            for name, (old, new) in mutants.items():
                assert old in original, name
                window.write_text(original.replace(old, new))
                mutant = run()
                assert mutant.returncode != 0 and 'FAIL ' in mutant.stderr, (name, mutant.stdout, mutant.stderr)
                rejected.append(name)
                print('MUTANT REJECTED '+name+' '+mutant.stderr.strip())
                window.write_text(original)
    proof = dict(passed=True, status='IMPLEMENTED semantic window controller', counts=counts,
                 original_immediate_core_reference=True, separate_CPU_DSP_RAM=True,
                 timestamped_ordered_event_replay=True, full_normalized_state_RAM_PCM=True,
                 echo_publish_cache_JIT_callback_semantics=True, rejected_mutations=rejected,
                 live_SPC_JIT_timestamps_implemented=False, native_memory_owner_assigned=False,
                 resident_RSP_complete_DSP_implemented=False, native_performance_acceptance=False,
                 commercial_data=False)
    if a.output:
        a.output.write_text(json.dumps(proof, indent=2)+'\n')


if __name__ == '__main__':
    main()
