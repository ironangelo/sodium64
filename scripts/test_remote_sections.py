#!/usr/bin/env python3
"""Compile the exact opt-in C observer against synthetic halted owners."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cc', default=os.environ.get('CC', 'gcc'))
    ap.add_argument('--json-output', type=Path)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-sections-model-') as directory:
        temp = Path(directory)
        # defines.h supplies the production ABI. Its register-name include
        # has no bearing on these C expressions and needs no host MIPS SDK.
        (temp / 'regdef.h').write_text('/* C host fixture: no assembly registers. */\n')
        exe = temp / ('sections.exe' if os.name == 'nt' else 'sections')
        cmd = [args.cc, '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
               '-DREMOTE_CONTROL_HOST', '-DSODIUM64_REMOTE_SECTION_OBSERVER=1',
               '-DSODIUM64_NATIVE_DIAG=1', '-DSODIUM64_NATIVE_DIAG_TRACE=1',
               '-I', str(temp)]
        if os.name != 'nt':
            cmd += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie']
        cmd += [str(root / 'scripts/fixtures/remote_sections_host.c'), '-o', str(exe)]
        subprocess.run(cmd, check=True)
        result = subprocess.run([str(exe)], check=True, capture_output=True, text=True)
        print(result.stdout, end='')
        cases = int(re.search(r'PASS sections_cases=(\d+)', result.stdout).group(1))
        proof = dict(passed=True, cases=cases, production_c_observer=True,
                     opt_in_only=True, hardware_mocked=True, physical_acceptance=False,
                     halted_aligned_dmem_only=True, retired_vs_next_guest_slots=True,
                     read_only=True, no_running_capture_reads=True,
                     source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                    for name in ('src/remote_control.c', 'src/remote_control.h',
                                                 'src/defines.h', 'scripts/fixtures/remote_sections_host.c')})
        if args.json_output:
            args.json_output.write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    main()
