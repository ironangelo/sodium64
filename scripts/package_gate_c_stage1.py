#!/usr/bin/env python3
"""Bundle the exact qualified Stage 1 builds, guests and existing decoders."""
import hashlib
import json
import shutil
import struct
import subprocess
import zlib
import zipfile
from pathlib import Path
from check_gate_c_stage1_ares import pixel
from make_gate_c_stage1 import window

BASELINE = '7cc8facfe8643fb85888f301f79995575830521d'


def png(path, phase):
    left, right = window(phase)
    row = bytearray()
    for x in range(256):
        p = pixel('both', x, left, right)
        rgb = bytes((((p >> 11) & 31)*255//31, ((p >> 6) & 31)*255//31,
                     ((p >> 1) & 31)*255//31))
        row.extend(rgb * 4)
    raw = (b'\0' + row) * 32
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag+data))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', 1024, 32, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def main():
    root = Path('stage1-package')
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()
    for directory in ('hardware', 'diagnostic'):
        shutil.copytree(directory, root / directory)
    for variant in ('normal', 'hw-profile', 'baseline-hw-profile'):
        src = Path('qualified') / variant
        dst = root / src
        for path in sorted(src.rglob('*')):
            if path.is_file() and path.suffix in ('.elf', '.map', '.z64'):
                target = dst / path.relative_to(src)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        assert (dst / 'build/sodium64.elf').is_file()
        assert (dst / 'build/sodium64.map').is_file()
    (root / 'scripts').mkdir()
    for name in ('hw_profile_report.py', 'profile_report.py'):
        shutil.copyfile(Path('scripts') / name, root / 'scripts' / name)
    shutil.copyfile('docs/GATE_C_STAGE1_HARDWARE.md', root / 'README.md')
    (root / 'evidence').mkdir()
    for name in ('result.json', 'motion-result.json'):
        result = json.loads((Path('captures') / name).read_text())
        assert result['passed'] is True, name
        shutil.copyfile(Path('captures') / name, root / 'evidence' / name)
    for name in ('executable-contract.txt', 'delay-slots.txt', 'runtime.sha256', 'qualified-hashes.sha256', 'ares-version.txt'):
        shutil.copyfile(name, root / 'evidence' / name)
    (root / 'expected').mkdir()
    for phase in (0, 32, 64, 127):
        png(root / 'expected' / f'phase-{phase:03d}-4x.png', phase)
    # An audible chronological lab excerpt, not an exhaustive PCM oracle.
    shutil.copyfile('captures/mixed/frame-007/audio.wav', root / 'expected/mixed-audio.wav')
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    manifest = dict(candidate_sha=sha, baseline_sha=BASELINE,
                    ares_sha='17813a3ccda21ab9bd45f09bfc2f91196dbf50ff',
                    settings=dict(frameskip=0, apu_clock=21, audio=4, precision=8),
                    scope='First section, 256x8 BG1/BG2, full brightness, half-add',
                    hardware_status='NOT_MEASURED',
                    files={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(root.rglob('*')) if p.is_file()})
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    hashes = [(hashlib.sha256(p.read_bytes()).hexdigest(), str(p.relative_to(root)))
              for p in sorted(root.rglob('*')) if p.is_file()]
    (root / 'SHA256SUMS').write_text(''.join(f'{h}  {p}\n' for h, p in hashes))
    archive = Path('gate-c-stage1-hardware.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                out.write(path, path.relative_to(root))
    print(sha, hashlib.sha256(archive.read_bytes()).hexdigest(), archive)


if __name__ == '__main__':
    main()
