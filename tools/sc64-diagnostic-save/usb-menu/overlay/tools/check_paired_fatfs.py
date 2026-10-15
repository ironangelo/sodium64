"""Reject the installed FatFs ABI fallback before deploying the pinned menu."""
import argparse, hashlib, json, re
from pathlib import Path

def check(menu, build, reference):
    headers = {}
    for name in ('ff.h', 'ffconf.h', 'diskio.h'):
        data = (menu/'pinned_include/fatfs'/name).read_bytes()
        if data != (reference/'src/fatfs'/name).read_bytes():
            raise ValueError('FatFs header differs from linked library source: ' + name)
        headers[name] = hashlib.sha256(data).hexdigest()
    version = (menu/'pinned_include/fatfs/ff.h').read_text()
    if not re.search(r'#define\s+FF_DEFINED\s+80386\b', version):
        raise ValueError('Expected pinned FatFs R0.16 revision 80386')
    owners = []
    for source in (menu/'src').rglob('*.c'):
        if source.name != 'flashcart_utils.c' and not re.search(r'#include\s*<fatfs/', source.read_text(encoding='utf-8')):
            continue
        relative = source.relative_to(menu/'src')
        dependency = build/relative.with_suffix('.d')
        text = dependency.read_text().replace('\\', '/')
        for name in ('ff.h', 'ffconf.h'):
            if f'pinned_include/fatfs/{name}' not in text:
                raise ValueError(f'Object lacks pinned dependency: {relative}, {name}')
        owners.append(relative.as_posix())
    if not owners:
        raise ValueError('No compiled FatFs owners inspected')
    return dict(ok=True, fatfs_revision=80386, header_sha256=headers,
                compiled_owners=sorted(owners), build=str(build))

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--json', type=Path)
    a = p.parse_args()
    proof = check(Path(__file__).resolve().parents[1], a.build.resolve(), a.reference.resolve())
    if a.json: a.json.write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps(proof, indent=2))
