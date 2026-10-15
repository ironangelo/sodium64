"""Read-only guard for the pinned paired-menu ROM/DFS and asset versions.

Uses the ROMPAK TOC and DragonFS 2.1 hash index, then decompresses DCA5/LZ4
fonts in memory. No external asset tools, FAT operations or asset exports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

PIN = "55aac1355773169d87e45424b772faf0dfb9432a"
REQUIRED = ("Firple-Bold.font64", "cursorsound.wav64", "back.wav64",
            "settings.wav64", "enter.wav64", "error.wav64", "bgm.wav64")
MAX_BYTES = 64 * 1024 * 1024
MAX_ASSET = 4 * 1024 * 1024


class InvalidPackage(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise InvalidPackage(reason)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bounded(data: bytes, offset: int, size: int, label: str) -> bytes:
    require(offset >= 0 and size >= 0 and offset <= len(data) and
            size <= len(data) - offset, f"{label}: extent outside input")
    return data[offset:offset + size]


def cstring(data: bytes, label: str) -> str:
    require(b"\0" in data, f"{label}: missing NUL")
    try:
        return data.split(b"\0", 1)[0].decode("ascii")
    except UnicodeError as exc:
        raise InvalidPackage(f"{label}: non-ASCII package name") from exc


def rom_entries(data: bytes) -> tuple[int, list[dict]]:
    require(data[:4] == bytes.fromhex("80371240"), "ROM: native z64 magic required")
    toc = next((offset for offset in range(0x1000, 0x2000, 16)
                if data[offset:offset + 4] == b"TOC0"), None)
    require(toc is not None, "ROM: TOC0 absent from runtime search range")
    _, _, toc_size, entry_size, count = struct.unpack(">4sIIHH", bounded(data, toc, 16, "TOC header"))
    require(16 <= entry_size < 1024 and 0 < count < 1024 and
            16 + entry_size * count <= toc_size <= 16384, "ROM: invalid TOC dimensions")
    bounded(data, toc, toc_size, "TOC")
    entries = []
    names = set()
    for index in range(count):
        entry = bounded(data, toc + 16 + index * entry_size, entry_size, "TOC entry")
        offset, size = struct.unpack_from(">II", entry)
        name = cstring(entry[8:], "TOC name")
        require(name and name not in names, "ROM: empty or duplicate TOC name")
        names.add(name)
        require(size > 0 and offset >= toc + toc_size, f"ROM: bad extent for {name}")
        bounded(data, offset, size, name)
        for previous in entries:
            require(offset + size <= previous["offset"] or
                    previous["offset"] + previous["bytes"] <= offset,
                    f"ROM: overlapping entries {name}/{previous['name']}")
        entries.append({"name": name, "offset": offset, "bytes": size})
    return toc, entries


def unpack_rom(data: bytes, expected_pin: str) -> tuple[bytes, dict]:
    toc, entries = rom_entries(data)
    dfs = [entry for entry in entries if entry["name"].endswith(".dfs")]
    require(len(dfs) == 1, "ROM: exactly one DFS is required")
    version = [entry for entry in entries if entry["name"] == "libdragon.version"]
    require(len(version) == 1, "ROM: libdragon.version is required")
    try:
        stamp = json.loads(bounded(data, version[0]["offset"], version[0]["bytes"], "version"))
    except (ValueError, UnicodeError) as exc:
        raise InvalidPackage("ROM: invalid libdragon.version JSON") from exc
    require(stamp.get("hash") == expected_pin and stamp.get("dirty") is False,
            "ROM: libdragon pin/dirty stamp differs from the trusted pin")
    symbols = [entry for entry in entries if entry["name"].endswith(".sym")]
    require(len(symbols) == 1, "ROM: exactly one SYMT is required")
    symbol_header = bounded(data, symbols[0]["offset"], 8, "SYMT header")
    require(symbols[0]["bytes"] >= 8 and symbol_header[:4] == b"SYMT" and
            struct.unpack_from(">I", symbol_header, 4)[0] == 5,
            "ROM: symbol table must be SYMT version 5")
    entry = dfs[0]
    return bounded(data, entry["offset"], entry["bytes"], "DFS"), {
        "toc_offset": toc, "toc_entries": entries, "libdragon": stamp, "symt_version": 5,
        "dfs_rom_offset": entry["offset"], "dfs_rom_bytes": entry["bytes"]}


def path_hash(path: bytes) -> int:
    result = 0
    for value in path:
        result = (result * 31 + value) & 0xffffffff
    return result


def dfs_files(data: bytes) -> dict[str, bytes]:
    lookup_bytes, flags, lookup_offset = struct.unpack(">III", bounded(data, 0, 12, "DFS root"))
    require(flags == 0xffffffff and cstring(bounded(data, 12, 32, "DFS root name"), "DFS root") == "DragonFS 2.1",
            "DFS: requires DragonFS 2.1 (runtime rejects older packaging)")
    require(lookup_offset % 2 == 0 and lookup_offset >= 26, "DFS: unaligned/bad lookup pointer")
    lookup = bounded(data, lookup_offset, lookup_bytes, "DFS index")
    count, paths_offset = struct.unpack(">II", bounded(lookup, 0, 8, "DFS index header"))
    require(0 < count <= 1024 and lookup_bytes == 8 + count * 16,
            "DFS: invalid index dimensions")
    require(paths_offset >= lookup_offset + lookup_bytes and paths_offset <= len(data),
            "DFS: invalid path table pointer")
    files = {}
    prior_hash = -1
    extents = []
    for index in range(count):
        checksum, packed_path, offset, size = struct.unpack_from(">IIII", lookup, 8 + index * 16)
        length, path_offset = packed_path >> 20, packed_path & 0xfffff
        require(2 <= length <= 256 and path_offset % 2 == 0, "DFS: invalid indexed path")
        encoded = bounded(data, paths_offset + path_offset, length, "DFS path")
        name = cstring(encoded, "DFS path")
        require(len(name) + 1 == length and name not in files and
                not name.startswith("/") and all(part not in ("", ".", "..") for part in name.split("/")),
                "DFS: duplicate/noncanonical indexed path")
        require(checksum == path_hash(encoded[:-1]) and checksum >= prior_hash,
                f"DFS: invalid hash/order for {name}")
        prior_hash = checksum
        require(offset % 2 == 0 and offset >= 26 and offset + size <= lookup_offset,
                f"DFS: invalid data extent for {name}")
        payload = bounded(data, offset, size, name)
        for previous_offset, previous_size in extents:
            require(offset + size <= previous_offset or previous_offset + previous_size <= offset,
                    f"DFS: overlapping asset data at {name}")
        extents.append((offset, size))
        files[name] = payload
    return files


def varint(data: bytes, offset: int) -> tuple[int, int]:
    result = 0
    for shift in range(0, 35, 7):
        require(offset < len(data), "DCA5: truncated varint")
        value = data[offset]
        offset += 1
        result |= (value & 127) << shift
        if not value & 128:
            require(result <= 0xffffffff, "DCA5: oversized varint")
            return result, offset
    raise InvalidPackage("DCA5: oversized varint")


def lz4_block(data: bytes, size: int) -> bytes:
    require(4 <= size <= MAX_ASSET, "DCA5: decompressed size outside limit")
    output = bytearray()
    position = 0

    def length(base: int) -> int:
        nonlocal position
        if base == 15:
            while True:
                require(position < len(data), "LZ4: truncated length")
                value = data[position]
                position += 1
                base += value
                require(base <= size, "LZ4: length exceeds output size")
                if value < 255:
                    break
        return base

    while position < len(data):
        token = data[position]
        position += 1
        literals = length(token >> 4)
        require(literals <= size - len(output), "LZ4: literal output overflow")
        output.extend(bounded(data, position, literals, "LZ4 literals"))
        position += literals
        if position == len(data):
            break
        distance = struct.unpack("<H", bounded(data, position, 2, "LZ4 distance"))[0]
        position += 2
        require(0 < distance <= len(output), "LZ4: invalid match distance")
        match = length(token & 15) + 4
        require(match <= size - len(output), "LZ4: match output overflow")
        pattern = bytes(output[-distance:])
        output.extend((pattern * ((match + distance - 1) // distance))[:match])
    require(len(output) == size, "LZ4: decompressed length mismatch")
    return bytes(output)


def asset_payload(data: bytes) -> tuple[bytes, str]:
    if not data.startswith(b"DCA"):
        return data, "none"
    require(data[:4] == b"DCA5" and len(data) >= 6, "asset: DCA5 is required")
    require((data[4] >> 4) & 3 == 1, "asset: only initialized LZ4 compression is admitted")
    position = 5
    compressed, position = varint(data, position)
    original, position = varint(data, position)
    _, position = varint(data, position)
    position = (position + 1) & ~1
    require(position < 17 and compressed == len(data) - position, "DCA5: incorrect compressed extent/header")
    return lz4_block(data[position:], original), "DCA5/LZ4"


def source_versions(libdragon: Path) -> dict:
    checks = {
        "dfs": ("src/dfs_internal.h", r'#define\s+ROOT_PATH\s+"([^"]+)"', "DragonFS 2.1"),
        "wav64": ("src/audio/wav64.c", r'head\.version\s*==\s*(\d+)', "10"),
        "font64": ("src/rdpq/rdpq_font.c", r'fnt->version\s*==\s*(\d+)', "11"),
        "dca": ("src/asset.c", r"base\.version\s*!=\s*'([^']+)'", "5"),
    }
    result = {}
    for name, (filename, pattern, expected) in checks.items():
        found = re.search(pattern, (libdragon / filename).read_text(encoding="utf-8"))
        require(found is not None and found.group(1) == expected,
                f"pinned source: {name} expected version differs")
        result[name] = found.group(1)
    return result


def validate_dfs(data: bytes) -> dict:
    files = dfs_files(data)
    require(all(name in files for name in REQUIRED), "DFS: missing required menu resource")
    resources = []
    for name in REQUIRED:
        encoded = files[name]
        payload, compression = asset_payload(encoded)
        if name.endswith(".wav64"):
            require(len(payload) >= 32 and payload[:4] == b"WV64" and payload[4] == 10,
                    f"{name}: requires WV64 version 10")
            start = struct.unpack_from(">I", payload, 24)[0]
            require(payload[5] < 4 and payload[6] in (1, 2) and payload[7] in (8, 16) and
                    32 <= start < len(payload), f"{name}: invalid WAV64 header")
            version = 10
        else:
            require(len(payload) >= 116 and payload[:4] == b"FNT\x0b",
                    f"{name}: requires FNT version 11")
            version = 11
        resources.append({"name": name, "bytes": len(encoded), "sha256": sha(encoded),
                          "decoded_bytes": len(payload), "compression": compression, "version": version})
    return {"dfs_bytes": len(data), "dfs_sha256": sha(data), "dfs_version": "2.1",
            "dfs_index_entries": len(files), "resources": resources}


def read_input(path: Path, expected_pin: str) -> tuple[bytes, dict]:
    require(0 < path.stat().st_size <= MAX_BYTES, "input: size outside 64 MiB limit")
    data = path.read_bytes()
    metadata = {"input": str(path.resolve()), "input_bytes": len(data), "input_sha256": sha(data)}
    if data[:4] == bytes.fromhex("80371240"):
        dfs, rom = unpack_rom(data, expected_pin)
        return dfs, {**metadata, "kind": "rom", **rom}
    require(len(data) >= 26 and data[4:8] == b"\xff" * 4, "input: not a native ROM or DFS")
    return data, {**metadata, "kind": "dfs"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Native menu ROM or standalone DFS")
    parser.add_argument("--reference-rom", type=Path, help="Require DFS identity with a trusted working ROM")
    parser.add_argument("--libdragon", type=Path, default=Path(__file__).resolve().parents[1] / "libdragon")
    parser.add_argument("--expected-pin", default=PIN)
    parser.add_argument("--json", type=Path, help="Optional local validation report")
    args = parser.parse_args()
    try:
        versions = source_versions(args.libdragon)
        dfs, metadata = read_input(args.input, args.expected_pin)
        report = {"ok": True, **metadata, **validate_dfs(dfs), "source_versions": versions,
                  "expected_pin": args.expected_pin}
        if args.reference_rom:
            reference_data = args.reference_rom.read_bytes()
            reference, reference_metadata = unpack_rom(reference_data, args.expected_pin)
            validate_dfs(reference)
            require(dfs == reference, "DFS: differs from trusted working assets")
            report["reference_rom_sha256"] = sha(reference_data)
            report["reference_dfs_rom_offset"] = reference_metadata["dfs_rom_offset"]
            report["reference_dfs_equal"] = True
    except (InvalidPackage, OSError, struct.error, UnicodeError) as exc:
        report = {"ok": False, "input": str(args.input), "error": str(exc)}
    rendered = json.dumps(report, indent=2)
    if args.json:
        args.json.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
