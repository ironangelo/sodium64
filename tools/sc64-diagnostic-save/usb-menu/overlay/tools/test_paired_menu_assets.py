"""Synthetic failure cases for the paired-menu packaging guard."""
import json
import struct
import unittest

import check_paired_menu_assets as guard


def uleb(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return result


def compressed_literal(payload):
    literal = bytearray([min(len(payload), 15) << 4])
    if len(payload) >= 15:
        remaining = len(payload) - 15
        while remaining >= 255:
            literal.append(255)
            remaining -= 255
        literal.append(remaining)
    literal.extend(payload)
    header = bytearray(b"DCA5\x13") + uleb(len(literal)) + uleb(len(payload)) + uleb(0)
    if len(header) & 1:
        header.append(0)
    return bytes(header + literal)


def resources():
    wav = bytearray(40)
    wav[:8] = b"WV64\x0a\x00\x01\x10"
    struct.pack_into(">I", wav, 24, 32)
    font = b"FNT\x0b" + bytes(112)
    return {name: compressed_literal(font) if name.endswith(".font64") else bytes(wav)
            for name in guard.REQUIRED}


def make_dfs(files):
    data = bytearray(32)
    data[12:25] = b"DragonFS 2.1\0"
    entries = []
    paths = bytearray()
    for name, payload in sorted(files.items(), key=lambda pair: guard.path_hash(pair[0].encode())):
        if len(data) & 1:
            data.append(0)
        offset = len(data)
        data.extend(payload)
        encoded = name.encode() + b"\0"
        entries.append((guard.path_hash(encoded[:-1]), (len(encoded) << 20) | len(paths), offset, len(payload)))
        paths.extend(encoded)
        if len(paths) & 1:
            paths.append(0)
    if len(data) & 1:
        data.append(0)
    lookup_offset = len(data)
    lookup_bytes = 8 + 16 * len(entries)
    struct.pack_into(">III", data, 0, lookup_bytes, 0xffffffff, lookup_offset)
    data.extend(struct.pack(">II", len(entries), lookup_offset + lookup_bytes))
    for entry in entries:
        data.extend(struct.pack(">IIII", *entry))
    data.extend(paths)
    return bytes(data)


def make_rom(dfs, pin=guard.PIN, dirty=False, symbols=5):
    data = bytearray(0x1400)
    data[:4] = bytes.fromhex("80371240")
    content = [("menu.elf.stripped", b"\x7fELFfixture"),
               ("menu.elf.sym", b"SYMT" + struct.pack(">I", symbols)),
               ("menu.dfs", dfs),
               ("libdragon.version", json.dumps({"hash": pin, "dirty": dirty}).encode())]
    struct.pack_into(">4sIIHH", data, 0x1000, b"TOC0", 0, 1024, 64, len(content))
    for index, (name, payload) in enumerate(content):
        data.extend(bytes((-len(data)) % 16))
        offset = len(data)
        data.extend(payload)
        struct.pack_into(">II", data, 0x1010 + index * 64, offset, len(payload))
        encoded = name.encode() + b"\0"
        data[0x1018 + index * 64:0x1018 + index * 64 + len(encoded)] = encoded
    return bytes(data)


class Packaging(unittest.TestCase):
    def test_valid_dfs(self):
        result = guard.validate_dfs(make_dfs(resources()))
        self.assertEqual(len(result["resources"]), 7)
        self.assertEqual(result["resources"][0]["compression"], "DCA5/LZ4")

    def test_valid_rom(self):
        dfs = make_dfs(resources())
        actual, report = guard.unpack_rom(make_rom(dfs), guard.PIN)
        self.assertEqual(actual, dfs)
        self.assertEqual(report["symt_version"], 5)

    def test_old_dfs(self):
        data = bytearray(make_dfs(resources()))
        data[23] = ord("0")
        with self.assertRaisesRegex(guard.InvalidPackage, "DragonFS 2.1"):
            guard.validate_dfs(bytes(data))

    def test_missing_resource(self):
        files = resources()
        files.pop("bgm.wav64")
        with self.assertRaisesRegex(guard.InvalidPackage, "missing"):
            guard.validate_dfs(make_dfs(files))

    def test_old_wav(self):
        files = resources()
        wav = bytearray(files["cursorsound.wav64"])
        wav[4] = 4
        files["cursorsound.wav64"] = bytes(wav)
        with self.assertRaisesRegex(guard.InvalidPackage, "WV64 version 10"):
            guard.validate_dfs(make_dfs(files))

    def test_old_font(self):
        files = resources()
        files["Firple-Bold.font64"] = compressed_literal(b"FNT\x0a" + bytes(112))
        with self.assertRaisesRegex(guard.InvalidPackage, "FNT version 11"):
            guard.validate_dfs(make_dfs(files))

    def test_old_dca(self):
        with self.assertRaisesRegex(guard.InvalidPackage, "DCA5"):
            guard.asset_payload(b"DCA3" + bytes(32))

    def test_hash_mismatch(self):
        data = bytearray(make_dfs(resources()))
        index = struct.unpack_from(">I", data, 8)[0]
        data[index + 8] ^= 1
        with self.assertRaisesRegex(guard.InvalidPackage, "hash/order"):
            guard.validate_dfs(bytes(data))

    def test_truncated_extent(self):
        with self.assertRaises(guard.InvalidPackage):
            guard.validate_dfs(make_dfs(resources())[:-20])

    def test_lz4_bad_distance(self):
        with self.assertRaisesRegex(guard.InvalidPackage, "distance"):
            guard.lz4_block(b"\x00\x01\x00", 4)

    def test_lz4_bad_size(self):
        with self.assertRaisesRegex(guard.InvalidPackage, "overflow"):
            guard.lz4_block(b"\x50hello", 4)

    def test_pin_mismatch(self):
        with self.assertRaisesRegex(guard.InvalidPackage, "pin/dirty"):
            guard.unpack_rom(make_rom(make_dfs(resources()), pin="old"), guard.PIN)

    def test_dirty_pin(self):
        with self.assertRaisesRegex(guard.InvalidPackage, "pin/dirty"):
            guard.unpack_rom(make_rom(make_dfs(resources()), dirty=True), guard.PIN)

    def test_old_symbols(self):
        with self.assertRaisesRegex(guard.InvalidPackage, "SYMT version 5"):
            guard.unpack_rom(make_rom(make_dfs(resources()), symbols=2), guard.PIN)

    def test_missing_toc(self):
        data = bytearray(make_rom(make_dfs(resources())))
        data[0x1000:0x1004] = b"bad!"
        with self.assertRaisesRegex(guard.InvalidPackage, "TOC0 absent"):
            guard.unpack_rom(bytes(data), guard.PIN)

    def test_overlapping_toc(self):
        data = bytearray(make_rom(make_dfs(resources())))
        struct.pack_into(">I", data, 0x1050, struct.unpack_from(">I", data, 0x1010)[0])
        with self.assertRaisesRegex(guard.InvalidPackage, "overlapping"):
            guard.unpack_rom(bytes(data), guard.PIN)


if __name__ == "__main__":
    unittest.main()
