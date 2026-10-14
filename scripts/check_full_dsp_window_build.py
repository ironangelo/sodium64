#!/usr/bin/env python3
"""Bounded O64 build/default-off identity gate; no console or private inputs."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import tempfile


def sections(path):
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x01\x02', 'expected big-endian ELF32/O64'
    h = struct.unpack_from('>16sHHIIIIIHHHHHH', data)
    sh = [struct.unpack_from('>10I', data, h[6]+i*h[11]) for i in range(h[12])]
    names = data[sh[h[13]][4]:sh[h[13]][4]+sh[h[13]][5]]
    result = {}
    for s in sh:
        if s[2] & 2:
            name = names[s[0]:names.index(b'\0', s[0])].decode()
            result[name] = (s[1], s[2], s[5], b'' if s[1] == 8 else data[s[4]:s[4]+s[5]])
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cxx', required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    flags = ['-c', '-O2', '-std=c++98', '-march=vr4300', '-mtune=vr4300', '-mabi=o64',
             '-mno-abicalls', '-fno-pic', '-G0', '-fno-builtin', '-fno-stack-protector',
             '-fno-exceptions', '-fno-rtti', '-ffunction-sections', '-fdata-sections',
             '-DNDEBUG', '-DBLARGG_BIG_ENDIAN=1', '-Wno-implicit-fallthrough']
    baseline = '6dc6a034362c1cab8f972b353e09f1f8e1b5376c'
    with tempfile.TemporaryDirectory(prefix='s64-window-build-') as tmp:
        stage = Path(tmp)
        original = stage/'original.cpp'
        original.write_bytes(subprocess.check_output(['git', 'show', baseline+':third_party/snes_spc/SPC_DSP.cpp'], cwd=root))
        def build(src, out, enabled):
            subprocess.run([a.cxx, *flags, '-I'+str(root/'third_party/snes_spc'),
                            *(['-DSODIUM64_DSP_FULL_WINDOW=1'] if enabled else []),
                            str(src), '-o', str(out)], check=True)
            return sections(out)
        before = build(original, stage/'before.o', False)
        after = build(root/'third_party/snes_spc/SPC_DSP.cpp', stage/'after.o', False)
        assert before == after, 'default-off allocated sections changed'
        enabled_core = build(root/'third_party/snes_spc/SPC_DSP.cpp', stage/'core.o', True)
        enabled_window = build(root/'src/full_dsp_window.cpp', stage/'window.o', True)
        build(root/'src/full_dsp_probe.cpp', stage/'probe.o', True)
        empty_window = build(root/'src/full_dsp_window.cpp', stage/'empty.o', False)
        assert not any(s[2] for n, s in empty_window.items() if n.startswith(('.text', '.data', '.bss', '.rodata')))
        assert not any(s[2] for s in enabled_window.values() if s[1] & 1), 'controller has global writable allocation'
    proof = dict(passed=True, baseline_source=baseline, O64_core_controller_probe_compile=True,
                 default_off_allocated_sections_exact=len(before),
                 default_off_controller_has_no_code_or_data=True,
                 enabled_controller_has_no_global_RAM_owner=True,
                 enabled_core_text_bytes=sum(s[2] for n, s in enabled_core.items() if n.startswith('.text')),
                 enabled_controller_text_bytes=sum(s[2] for n, s in enabled_window.items() if n.startswith('.text')),
                 native_ROM_or_hardware_execution=False, performance_acceptance=False,
                 commercial_data=False)
    print(json.dumps(proof, indent=2))
    if a.output:
        a.output.write_text(json.dumps(proof, indent=2)+'\n')


if __name__ == '__main__':
    main()
