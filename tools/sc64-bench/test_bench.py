"""Host transport/measurement regressions; these do not qualify hardware."""
import contextlib
import binascii
import io
import json
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import bench

class BenchTests(unittest.TestCase):
    def session(self, lines):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        s = bench.Session('unused', 'serial://COM3', temp.name, timeout=.03)
        s.next_id = 1
        s.process = SimpleNamespace(stdin=io.StringIO())
        for line in lines:
            s.lines.put(line)
        return s

    def test_only_matching_receipt_completes_request(self):
        s = self.session(['S64 deadbeef OK mode=emu\n',
                          'S64 00000001 ITEM f 32 /private path.sav\n',
                          'S64 00000001 OK mode=menu count=1\n'])
        response = s.request('list', '/SNES')
        self.assertEqual(response['rows'], ['f 32 /private path.sav'])
        self.assertEqual(bench.fields(response['text'])['mode'], 'menu')
        self.assertEqual(s.process.stdin.getvalue(), 's64 00000001 list /SNES\n')

    def test_error_receipt_is_not_success(self):
        s = self.session(['S64 00000001 ERR SD_LOCKED 0x02000017\n'])
        with self.assertRaisesRegex(bench.BenchError, 'SD_LOCKED'):
            s.request('capture', 'sd')
        self.assertIn('failure', s.history[0])

    def test_timeout_does_not_repeat_mutation(self):
        s = self.session([])
        with self.assertRaisesRegex(bench.BenchError, 'No matching'):
            s.request('install', '/menu/emulators/remote.z64')
        self.assertEqual(s.process.stdin.getvalue().count('\n'), 1)

    def test_transport_timeout_terminates_request(self):
        s = self.session(['Error: Debug data write dropped due to timeout\n'])
        with self.assertRaisesRegex(bench.BenchError, 'dropped'):
            s.request('hello')

    def test_command_injection_rejected(self):
        s = self.session([])
        for args in ['/SNES/a\nmenu', 'a\0b', 'a\rb']:
            with self.assertRaises(bench.BenchError):
                s.request('launch', args)
        self.assertEqual(s.process.stdin.getvalue(), '')

    def test_count_wrap_and_distinct_presentation(self):
        before = {'count': str(0xffff0000), 'guest': '100', 'render': '100', 'vi': '100', 'present': '100'}
        after = {'count': str((0xffff0000 + 46875000) & 0xffffffff),
                 'guest': '160', 'render': '140', 'vi': '160', 'present': '120', 'count_hz': '46875000'}
        result = bench.cadence(before, after)
        self.assertEqual(result['duration_s'], 1)
        self.assertEqual(result['guest_per_second'], 60)
        self.assertEqual(result['render_per_second'], 40)
        self.assertEqual(result['present_per_second'], 20)

    def test_degenerate_clock_rejected(self):
        with self.assertRaises(bench.BenchError):
            bench.cadence({'count': '4'}, {'count': '4'})
        with self.assertRaises(bench.BenchError):
            bench.cadence({'count': '0'}, {'count': '10', 'count_hz': '0'})

    def test_install_requires_verified_commit_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.z64'
            p.write_bytes(bytes.fromhex('80371240') + bytes(4092))
            s = self.session([])
            with patch.object(s, 'request', return_value={'text': 'verified=1 installed=0'}):
                with self.assertRaisesRegex(bench.BenchError, 'commit receipt'):
                    s.install(p)

    def test_install_requires_matching_bytes_and_crc_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.z64'
            p.write_bytes(bytes.fromhex('80371240') + bytes(4092))
            s = self.session([])
            invalid = [
                'bytes=4095 crc32=05bafb65',
                'bytes=4096 crc32=05bafb64',
                'crc32=05bafb65',
                'bytes=4096',
                'bytes=invalid crc32=05bafb65',
                'bytes=4096 crc32=invalid',
            ]
            for detail in invalid:
                with self.subTest(receipt=detail):
                    with patch.object(s, 'request', return_value={
                            'text': 'installed=1 verified=1 ' + detail}):
                        with self.assertRaisesRegex(bench.BenchError, 'bytes/CRC32'):
                            s.install(p)

    def test_install_matching_receipt_preserves_emulator_default(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.z64'
            p.write_bytes(bytes.fromhex('80371240') + bytes(4092))
            s = self.session([])
            with patch.object(s, 'request', return_value={
                    'text': 'installed=1 verified=1 bytes=4096 crc32=05BAFB65 previous=1'}) as request:
                result = s.install(p)
            request.assert_called_once_with('install',
                f'/menu/emulators/sodium64-remote.z64 05bafb65 @{p.resolve()}@', timeout=45)
            self.assertEqual(result['candidate']['bytes'], 4096)
            self.assertEqual(result['candidate']['crc32'], '05bafb65')
            self.assertEqual(len(result['candidate']['sha256']), 64)

    def test_install_persists_candidate_and_host_validation(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.z64'
            p.write_bytes(bytes.fromhex('80371240') + bytes(4092))
            for method in ('install', 'install_menu'):
                for text, expected in [
                    ('installed=1 verified=1 bytes=4096 crc32=05bafb65', 'passed'),
                    ('installed=1 verified=1 bytes=4096 crc32=05bafb64', 'failed'),
                    ('installed=0 verified=1 bytes=4096 crc32=05bafb65', 'failed'),
                ]:
                    with self.subTest(method=method, receipt=text):
                        s = self.session([f'S64 00000001 OK {text}\n'])
                        if expected == 'failed':
                            with self.assertRaises(bench.BenchError):
                                getattr(s, method)(p)
                        else:
                            getattr(s, method)(p)
                        saved = json.loads((s.output / 'requests.json').read_text(encoding='utf-8'))[0]
                        self.assertEqual(saved['kind'], 'OK')
                        self.assertEqual(saved['text'], text)
                        self.assertEqual(saved['host_validation'], expected)
                        self.assertEqual(saved['candidate']['bytes'], 4096)
                        self.assertEqual(saved['candidate']['crc32'], '05bafb65')
                        self.assertEqual(len(saved['candidate']['sha256']), 64)
                        if expected == 'failed':
                            self.assertTrue(saved['failure'])
                        else:
                            self.assertNotIn('failure', saved)

    def test_install_menu_accepts_four_mib_and_uses_fixed_target(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'menu.n64'
            data = bytes.fromhex('80371240') + bytes(4 * 1024 * 1024 - 4)
            p.write_bytes(data)
            crc = f'{binascii.crc32(data) & 0xffffffff:08x}'
            s = self.session([])
            with patch.object(s, 'request', return_value={
                    'text': f'installed=1 verified=1 bytes={len(data)} crc32={crc} previous=1'}) as request:
                result = s.install_menu(p)
            request.assert_called_once_with('install',
                f'/sc64menu.n64 {crc} @{p.resolve()}@', timeout=45)
            self.assertEqual(result['candidate']['bytes'], 4 * 1024 * 1024)

    def test_install_accepts_emulator_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.z64'
            data = bytes.fromhex('80371240') + bytes(0x102000 - 4)
            p.write_bytes(data)
            crc = f'{binascii.crc32(data) & 0xffffffff:08x}'
            s = self.session([])
            with patch.object(s, 'request', return_value={
                    'text': f'installed=1 verified=1 bytes={len(data)} crc32={crc}'}):
                self.assertEqual(s.install(p)['candidate']['bytes'], 0x102000)

    def test_install_menu_rejects_invalid_image_before_request(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'menu.n64'
            s = self.session([])
            for magic, size in [(bytes.fromhex('80371240'), 4095),
                                (bytes.fromhex('80371240'), 4 * 1024 * 1024 + 1),
                                (bytes.fromhex('37804012'), 4096)]:
                with self.subTest(magic=magic.hex(), size=size):
                    p.write_bytes(magic + bytes(size - 4))
                    with patch.object(s, 'request') as request:
                        with self.assertRaisesRegex(bench.BenchError, 'z64 menu'):
                            s.install_menu(p)
                        request.assert_not_called()

    def test_install_rejects_file_token_delimiter_before_request(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate@.z64'
            p.write_bytes(bytes.fromhex('80371240') + bytes(4092))
            s = self.session([])
            for install in (s.install, s.install_menu):
                with self.subTest(install=install.__name__):
                    with patch.object(s, 'request') as request:
                        with self.assertRaisesRegex(bench.BenchError, 'token'):
                            install(p)
                        request.assert_not_called()

    def test_install_menu_cli_dispatches_in_menu_mode(self):
        with patch('sys.argv', ['bench.py', '--output', 'unused', 'install-menu', 'menu.n64']), \
                patch.object(bench, 'Session') as session, contextlib.redirect_stdout(io.StringIO()):
            s = session.return_value.__enter__.return_value
            s.install_menu.return_value = {'installed': 1}
            bench.main()
            s.ensure_menu.assert_called_once_with()
            s.install_menu.assert_called_once_with(Path('menu.n64'))
            s.install.assert_not_called()

    def test_install_rejects_guest_area_and_save_target(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.z64'
            p.write_bytes(bytes.fromhex('80371240') + bytes(0x102000 - 3))
            s = self.session([])
            with self.assertRaises(bench.BenchError):
                s.install(p)
            p.write_bytes(bytes.fromhex('80371240') + bytes(4092))
            with self.assertRaises(bench.BenchError):
                s.install(p, '/SNES/game.sav')

if __name__ == '__main__':
    unittest.main()
