#!/usr/bin/env python3
"""Private physical-console bench using the installed SC64 deployer.

No direct PC SD mount while powered on; no commercial inputs are bundled.
An OK response is an application receipt, never proof of visual correctness.
"""
from __future__ import annotations
import argparse
import binascii
import hashlib
import json
import queue
import re
import secrets
import subprocess
import threading
import time
from pathlib import Path

DEFAULT_EXE = 'sc64deployer'
ANSI = re.compile(r'\x1b\[[0-9;]*m')
RESPONSE = re.compile(r'S64 ([0-9a-fA-F]{8}) (OK|ERR|ITEM)(?: (.*))?$')

class BenchError(RuntimeError):
    pass

def parse_response(line):
    m = RESPONSE.search(ANSI.sub('', line).strip())
    if not m:
        return None
    return {'id': m[1].lower(), 'kind': m[2], 'text': m[3] or ''}

def fields(text):
    return dict(token.split('=', 1) for token in text.split() if '=' in token)

def cadence(before, after):
    """Count wrap supported for windows shorter than one 32-bit clock period."""
    before, after = before.copy(), after.copy()
    aliases = {'count32': 'count', 'guest_frame_id': 'guest',
               'render_frame_id': 'render', 'new_presentations': 'present'}
    for source, target in aliases.items():
        for data in (before, after):
            if source in data:
                data[target] = data[source]
    hz = int(after.get('count_hz', '46875000'), 0)
    dt = (int(after['count'], 0) - int(before['count'], 0)) & 0xffffffff
    if dt == 0 or hz != 46875000:
        raise BenchError('Invalid Count interval/frequency')
    seconds = dt / hz
    out = {'duration_s': seconds, 'presentation_is_software_observation': True}
    for key in ('guest', 'render', 'vi', 'present'):
        if key in before and key in after:
            delta = (int(after[key], 0) - int(before[key], 0)) & 0xffffffff
            out[key + '_delta'] = delta
            out[key + '_per_second'] = delta / seconds
    return out

class Session:
    def __init__(self, exe, port, output, timeout=20):
        self.exe, self.port = str(exe), port
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.next_id = secrets.randbits(32) or 1
        self.lines = queue.Queue()
        self.history = []
        self.process = None
        self.log = None

    def __enter__(self):
        self.log = (self.output / 'transport.log').open('a', encoding='utf-8')
        self.process = subprocess.Popen(
            [self.exe, '-p', self.port, 'debug', '--no-writeback'],
            cwd=self.output, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', bufsize=1)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        return self

    def _read(self):
        for line in self.process.stdout:
            line = ANSI.sub('', line)
            self.log.write(line)
            self.log.flush()
            self.lines.put(line)
        self.lines.put(None)

    def request(self, verb, args='', timeout=None):
        if any(c in verb + args for c in ('\n', '\r', '\0')):
            raise BenchError('Multiline/NUL command rejected')
        rid = f'{self.next_id:08x}'
        self.next_id = (self.next_id + 1) & 0xffffffff or 1
        command = f's64 {rid} {verb}' + (' ' + args if args else '')
        record = {'id': rid, 'verb': verb, 'args': args, 'rows': []}
        started = time.monotonic()
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        deadline = started + (self.timeout if timeout is None else timeout)
        try:
            while time.monotonic() < deadline:
                try:
                    line = self.lines.get(timeout=max(.01, deadline - time.monotonic()))
                except queue.Empty:
                    break
                if line is None:
                    raise BenchError('Deployer exited before application receipt')
                if 'dropped due to timeout' in line or line.lstrip().startswith('Error:'):
                    raise BenchError(line.strip())
                response = parse_response(line)
                if not response or response['id'] != rid:
                    continue
                if response['kind'] == 'ITEM':
                    record['rows'].append(response['text'])
                    continue
                record.update(response, elapsed_s=time.monotonic() - started)
                if response['kind'] == 'ERR':
                    raise BenchError(response['text'])
                return record
            raise BenchError(f'No matching application receipt for {verb} ({rid})')
        except Exception as e:
            record['failure'] = str(e)
            raise
        finally:
            self.history.append(record)
            (self.output / 'requests.json').write_text(json.dumps(self.history, indent=2), encoding='utf-8')

    def state(self):
        return fields(self.request('status')['text'])

    def wait_mode(self, wanted, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            info = fields(self.request('hello', timeout=max(1, deadline - time.monotonic()))['text'])
            if info.get('mode', '').lower() == wanted:
                return info
            time.sleep(.1)
        raise BenchError(f'Expected application mode {wanted}')

    def ensure_menu(self):
        info = fields(self.request('hello')['text'])
        if info.get('mode', '').lower() == 'emu':
            self.request('menu')
            time.sleep(3)  # Let the bootloader load and initialize the menu.
        return self.wait_mode('menu')

    def install(self, candidate, remote='/menu/emulators/sodium64-remote.z64'):
        if not re.fullmatch(r'/menu/emulators/[A-Za-z0-9_-]+\.z64', remote):
            raise BenchError('Install target is outside the emulator directory')
        return self._install(candidate, remote, 0x102000,
                             'Expected empty z64 emulator fitting before the handoff')

    def install_menu(self, candidate):
        return self._install(candidate, '/sc64menu.n64', 4 * 1024 * 1024,
                             'Expected z64 menu between 4096 bytes and 4 MiB')

    def _install(self, candidate, remote, max_bytes, invalid_candidate):
        candidate = Path(candidate).resolve()
        data = candidate.read_bytes()
        if not data.startswith(b'\x80\x37\x12\x40') or not 4096 <= len(data) <= max_bytes:
            raise BenchError(invalid_candidate)
        if '@' in str(candidate):
            raise BenchError('Deployer file token cannot contain @')
        crc = binascii.crc32(data) & 0xffffffff
        receipt = self.request('install', f'{remote} {crc:08x} @{candidate}@', timeout=45)
        receipt['candidate'] = {'bytes': len(data), 'crc32': f'{crc:08x}',
                                'sha256': hashlib.sha256(data).hexdigest()}
        try:
            f = fields(receipt['text'])
            if f.get('verified') != '1' or f.get('installed') != '1':
                raise BenchError('Install lacks verified content/commit receipt')
            if f.get('bytes') != str(len(data)) or f.get('crc32', '').lower() != f'{crc:08x}':
                raise BenchError('Install receipt does not match candidate bytes/CRC32')
            receipt['host_validation'] = 'passed'
            return receipt
        except BenchError as e:
            receipt.update(host_validation='failed', failure=str(e))
            raise
        finally:
            (self.output / 'requests.json').write_text(json.dumps(self.history, indent=2), encoding='utf-8')

    def export(self, verb, suffix, timeout=20):
        previous = {str(p): (p.stat().st_size, p.stat().st_mtime_ns)
                    for p in self.output.glob('*' + suffix)}
        receipt = self.request(verb, timeout=timeout)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for p in self.output.glob('*' + suffix):
                state = (p.stat().st_size, p.stat().st_mtime_ns)
                if state[0] and previous.get(str(p)) != state:
                    # Deployer reports the file only after its write completes.
                    data = p.read_bytes()
                    receipt['artifact'] = {'path': str(p), 'bytes': len(data),
                                           'sha256': hashlib.sha256(data).hexdigest()}
                    return receipt
            time.sleep(.05)
        raise BenchError(f'{verb}: no exported artifact')

    def __exit__(self, *_):
        if self.process:
            try:
                self.process.stdin.write('\n')
                self.process.stdin.flush()
                self.process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait(timeout=3)
        if self.process:
            self.reader.join(timeout=3)
        if self.log:
            self.log.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deployer', default=DEFAULT_EXE)
    parser.add_argument('--port', default='serial://COM3')
    parser.add_argument('--output', type=Path, required=True, help='Private local artifact directory')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    cmd = sub.add_parser('request'); cmd.add_argument('verb'); cmd.add_argument('args', nargs='?', default='')
    cmd.add_argument('--timeout', type=float, default=20)
    cmd = sub.add_parser('install'); cmd.add_argument('candidate', type=Path)
    cmd = sub.add_parser('install-menu'); cmd.add_argument('candidate', type=Path)
    args = parser.parse_args()
    with Session(args.deployer,args.port,args.output) as session:
        if args.command == 'status': result = session.state()
        elif args.command == 'request': result = session.request(args.verb,args.args,timeout=args.timeout)
        elif args.command == 'install': session.ensure_menu();result = session.install(args.candidate)
        else: session.ensure_menu();result = session.install_menu(args.candidate)
        print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
