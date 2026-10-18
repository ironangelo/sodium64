#!/usr/bin/env python3
"""Keep the rolling release separate from the opt-in laboratory builds.

Inspect the unstripped linked ELF, including allocated BSS, before packaging.
This checks the project's diagnostic symbol/owner contracts and an exact ZIP
allowlist. It is not a gameplay, performance or fidelity qualification.
"""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from linked_cpu_regression import load_elf


PREFIXES = ('remote_', 'profile_', 'hw_profile_')
CORE_SYMBOLS = {'main', 'exception_handler', 'rsp_main_text_start',
                'rsp_mode7_text_start'}
MEMBERS = ('sodium64.z64', 'rom-converter.py')


def check_elf(path):
    memory, symbols = load_elf(path)
    if not CORE_SYMBOLS <= symbols.keys() or not memory:
        raise ValueError('the unstripped linked emulator ELF is required')
    diagnostics = sorted(name for name in symbols if name.startswith(PREFIXES))
    if diagnostics:
        raise ValueError('laboratory symbols in release ELF: ' + ', '.join(diagnostics[:8]))
    # USB lease [440000,442000), profiler lease [448000,44d000).
    # Include NOBITS: an uninitialized diagnostic buffer still consumes RAM.
    occupied = sorted(address for address in memory
                      if 0x440000 <= address < 0x442000
                      or 0x448000 <= address < 0x44d000)
    if occupied:
        raise ValueError('allocated diagnostic lease in release ELF: ' + hex(occupied[0]))
    return {'linked_symbols': len(symbols), 'allocated_bytes': len(memory),
            'laboratory_symbols': [], 'allocated_diagnostic_leases': []}


def check_archive(path, payloads):
    with zipfile.ZipFile(path) as archive:
        if sorted(archive.namelist()) != sorted(MEMBERS):
            raise ValueError('release ZIP must contain exactly sodium64.z64 and rom-converter.py')
        for name in MEMBERS:
            if archive.read(name) != payloads[name]:
                raise ValueError('release ZIP differs from normal build: ' + name)
    return list(MEMBERS)


def check_rom(path):
    data = path.read_bytes()
    if len(data) < 4096 or data[:4] != bytes.fromhex('80371240'):
        raise ValueError('expected a complete big-endian N64 ROM')
    # n64sym is appended to the distributed ROM. Check it as well as the ELF.
    for prefix in PREFIXES:
        if prefix.encode('ascii') in data:
            raise ValueError('laboratory symbol text in release ROM: ' + prefix)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--elf', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--converter', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--package', type=Path, help='create a new, strictly allowlisted ZIP')
    mode.add_argument('--archive', type=Path, help='verify an existing ZIP')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = check_elf(args.elf)
        payloads = {'sodium64.z64': check_rom(args.rom),
                    'rom-converter.py': args.converter.read_bytes()}
        if not payloads['rom-converter.py']:
            raise ValueError('ROM converter is empty')
        if args.package:
            # Exclusive creation avoids accidentally retaining an earlier ZIP.
            with zipfile.ZipFile(args.package, 'x', zipfile.ZIP_DEFLATED) as archive:
                for name in MEMBERS:
                    archive.writestr(name, payloads[name])
        archive = args.package or args.archive
        if archive:
            report['archive_members'] = check_archive(archive, payloads)
        report['sha256'] = {name: hashlib.sha256(data).hexdigest()
                            for name, data in payloads.items()}
        report['elf_sha256'] = hashlib.sha256(args.elf.read_bytes()).hexdigest()
        report['status'] = 'PASS'
        text = json.dumps(report, indent=2) + '\n'
        if args.output:
            args.output.write_text(text, encoding='utf-8')
        print(text, end='')
    except (AssertionError, OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, 'Release isolation failed: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
