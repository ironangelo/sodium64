#!/usr/bin/env python3
"""Exercise release admission with actual normal/laboratory linked builds."""

import argparse
import json
from pathlib import Path
import struct
import tempfile
import zipfile

from check_release_package import check_archive, check_elf, check_rom, MEMBERS


def rejected(call, reason):
    try:
        call()
    except ValueError as error:
        if reason not in str(error):
            raise AssertionError(('wrong rejection', str(error), reason)) from error
    else:
        raise AssertionError('invalid release was admitted: ' + reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normal-elf', type=Path, required=True)
    parser.add_argument('--laboratory-elf', type=Path, action='append', required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--converter', type=Path, required=True)
    args = parser.parse_args()
    check_elf(args.normal_elf)
    for path in args.laboratory_elf:
        rejected(lambda: check_elf(path), 'laboratory symbols')
    payloads = {'sodium64.z64': check_rom(args.rom),
                'rom-converter.py': args.converter.read_bytes()}
    with tempfile.TemporaryDirectory(prefix='sodium64-release-') as temp:
        root = Path(temp)
        linked = args.normal_elf.read_bytes()
        header = struct.unpack_from('>16sHHIIIIIHHHHHH', linked)
        sections = [(header[6] + i * header[11],
                     struct.unpack_from('>IIIIIIIIII', linked, header[6] + i * header[11]))
                    for i in range(header[12])]
        bss = next(offset for offset, section in sections
                   if section[1] == 8 and section[2] & 2 and section[5])
        for address in (0x80440000, 0x80448000):
            data = bytearray(linked)
            struct.pack_into('>I', data, bss + 12, address)
            bad = root / (hex(address) + '.elf')
            bad.write_bytes(data)
            rejected(lambda: check_elf(bad), 'allocated diagnostic lease')
        data = bytearray(linked)
        for offset, section in sections:
            if section[1] == 2:
                struct.pack_into('>I', data, offset + 4, 0)
        stripped = root / 'missing-symbols.elf'
        stripped.write_bytes(data)
        rejected(lambda: check_elf(stripped), 'unstripped linked emulator ELF')

        def archive(name, records):
            path = root / (name + '.zip')
            with zipfile.ZipFile(path, 'x') as result:
                for member, data in records:
                    result.writestr(member, data)
            return path

        valid = archive('valid', payloads.items())
        assert check_archive(valid, payloads) == list(MEMBERS)
        for label, extra in [('usb', 'sodium64-usb-bench.z64'),
                             ('capture', 'capture.png'), ('menu', 'menu.z64'),
                             ('path', '../sodium64.z64')]:
            bad = archive(label, [*payloads.items(), (extra, b'original test data')])
            rejected(lambda: check_archive(bad, payloads), 'must contain exactly')
        for member in MEMBERS:
            changed = dict(payloads)
            changed[member] += b'original test mutation'
            bad = archive(member.replace('.', '-'), changed.items())
            rejected(lambda: check_archive(bad, payloads), 'differs from normal build')
        missing = archive('missing', [('sodium64.z64', payloads['sodium64.z64'])])
        rejected(lambda: check_archive(missing, payloads), 'must contain exactly')
        for prefix in ('remote_', 'profile_', 'hw_profile_'):
            bad = root / (prefix + '.z64')
            bad.write_bytes(payloads['sodium64.z64'] + prefix.encode('ascii'))
            rejected(lambda: check_rom(bad), 'laboratory symbol text')
    print(json.dumps({'status': 'PASS', 'normal_linked_builds': 1,
                      'actual_laboratory_builds_rejected': len(args.laboratory_elf),
                      'linked_owner_and_symbol_mutants_rejected': 3,
                      'package_cases': 8, 'ROM_symbol_mutants_rejected': 3,
                      'scope': 'release isolation only; no runtime or native performance claim'}))


if __name__ == '__main__':
    main()
