#!/usr/bin/env python3
"""Decode and symbolicate a Sodium64 PROFILE=1 sampling snapshot.

The snapshot is expected to begin at the `profile_magic` address and extend
through `profile_sample_buffer_end`. It can come from an emulator memory dump
or, later, a hardware extraction path.

Some N64 emulators expose RDRAM through their debugger in host-word order,
which reverses the bytes inside every 32-bit word relative to the canonical
big-endian N64 byte stream. The decoder auto-detects and normalizes that format.

When the matching GNU linker map is supplied, samples are also classified by
Sodium64 object/module and by broad subsystem. This keeps runtime profiling raw
and cheap while allowing the host tooling to answer Phase 1 budget questions.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import json
import re
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MAGIC = 0x53363450  # S64P
HEADER_WORDS = 8
HEADER_SIZE = HEADER_WORDS * 4
JIT_START = 0x801C0000
JIT_END = 0x80200000

MAP_RANGE_RE = re.compile(
    r"^\s+\.(?:text|boot)\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)\s+(\S+\.o)\s*$"
)


@dataclass(frozen=True)
class Symbol:
    address: int
    name: str


@dataclass(frozen=True)
class TextRange:
    start: int
    end: int
    object_name: str


def load_symbols(elf: Path, nm_command: str) -> tuple[list[int], list[Symbol], dict[str, int]]:
    proc = subprocess.run(
        [nm_command, "-n", str(elf)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    symbols: list[Symbol] = []
    named: dict[str, int] = {}
    for raw_line in proc.stdout.splitlines():
        parts = raw_line.split()
        if len(parts) < 3:
            continue
        try:
            address = int(parts[0], 16)
        except ValueError:
            continue
        name = parts[-1]
        symbols.append(Symbol(address, name))
        named[name] = address

    symbols.sort(key=lambda item: item.address)
    addresses = [item.address for item in symbols]
    return addresses, symbols, named


def load_text_ranges(linker_map: Path) -> tuple[list[int], list[TextRange]]:
    """Parse R4300 .boot/.text contributions from a GNU ld map file."""
    ranges: list[TextRange] = []
    for raw_line in linker_map.read_text(encoding="utf-8", errors="replace").splitlines():
        match = MAP_RANGE_RE.match(raw_line)
        if not match:
            continue
        start = int(match.group(1), 16)
        size = int(match.group(2), 16)
        if start == 0 or size == 0:
            # GNU ld also lists discarded input sections at address zero.
            continue
        ranges.append(
            TextRange(
                start=start,
                end=start + size,
                object_name=Path(match.group(3)).name,
            )
        )

    ranges.sort(key=lambda item: item.start)
    return [item.start for item in ranges], ranges


def object_for_pc(pc: int, starts: list[int], ranges: list[TextRange]) -> str | None:
    idx = bisect.bisect_right(starts, pc) - 1
    if idx < 0:
        return None
    item = ranges[idx]
    if item.start <= pc < item.end:
        return item.object_name
    return None


def nearest_symbol(pc: int, addresses: list[int], symbols: list[Symbol]) -> str:
    if JIT_START <= pc < JIT_END:
        return "[APU JIT generated code]"

    idx = bisect.bisect_right(addresses, pc) - 1
    if idx < 0:
        return "[unknown]"

    symbol = symbols[idx]
    offset = pc - symbol.address
    if offset == 0:
        return symbol.name
    return f"{symbol.name}+0x{offset:X}"


def base_symbol_name(symbolicated: str) -> str:
    if symbolicated.startswith("["):
        return symbolicated
    return symbolicated.split("+", 1)[0]


def symbol_offset(symbolicated: str) -> int | None:
    """Return the +0xNN offset from a symbolicated name, or zero at its entry."""
    if symbolicated.startswith("["):
        return None
    if "+0x" not in symbolicated:
        return 0
    try:
        return int(symbolicated.rsplit("+0x", 1)[1], 16)
    except ValueError:
        return None


def subsystem_for_sample(pc: int, symbolicated: str, object_name: str | None) -> str:
    """Classify one sampled EPC into a stable Phase 1 subsystem bucket."""
    base = base_symbol_name(symbolicated)

    # Waits are decision-relevant by themselves, even though their instructions
    # live inside another module such as ppu.o or main.o.
    if base == "rsp_wait":
        return "RSP wait"
    if base == "frame_wait":
        return "frame/VI wait"

    # The first four instructions of write_vmdatal/write_vmdatah are not PPU
    # work: they spin on SP_SEMAPHORE until the RSP finishes copying the frame's
    # VRAM snapshot. Keep only that 0x00..0x0C guard in a distinct wait bucket;
    # the rest of each function remains genuine PPU/VRAM work.
    offset = symbol_offset(symbolicated)
    if base in {"write_vmdatal", "write_vmdatah"} and offset is not None and offset < 0x10:
        return "RSP/VRAM semaphore wait"

    if JIT_START <= pc < JIT_END:
        return "APU JIT generated"

    if object_name is None:
        return "runtime/unknown"
    if object_name.startswith("cpu"):
        return "S-CPU interpreter"
    if object_name.startswith("apu"):
        return "APU/SPC700 static"
    if object_name == "dsp.o":
        return "DSP/audio"
    if object_name == "ppu.o":
        return "PPU/events/frame prep"
    if object_name == "dma.o":
        return "DMA/HDMA"
    if object_name == "memory.o":
        return "SNES memory/I/O"
    if object_name == "mul_div.o":
        return "SNES math unit"
    if object_name == "main.o":
        return "scheduler/core"
    if object_name == "profile.o":
        return "profiler overhead"
    if object_name.startswith("xcop_"):
        return "enhancement chip"
    if object_name == "input.o":
        return "input"
    if object_name in {"menu.o", "font.o"}:
        return "UI"
    if object_name.startswith("rsp"):
        return "RSP embedded code/data"
    return "runtime/other"


def normalize_snapshot(blob: bytes) -> tuple[bytes, str]:
    """Return canonical big-endian profiler bytes plus a format description."""
    if len(blob) < 4:
        raise ValueError("snapshot is too short to contain profiler magic")

    magic_be = struct.unpack_from(">I", blob, 0)[0]
    if magic_be == MAGIC:
        return blob, "canonical big-endian"

    if len(blob) % 4:
        raise ValueError(
            "snapshot magic is not canonical and byte length is not divisible by 4; "
            "cannot test 32-bit word-swapped format"
        )

    # Mupen64Plus' debugger exposes the same 32-bit RDRAM word with the four
    # bytes reversed on little-endian hosts. Normalize every word, not just the
    # header, because pointers and sampled EPC values are affected too.
    swapped_magic = struct.unpack_from("<I", blob, 0)[0]
    if swapped_magic == MAGIC:
        normalized = b"".join(
            blob[offset : offset + 4][::-1]
            for offset in range(0, len(blob), 4)
        )
        return normalized, "32-bit word-swapped"

    raise ValueError(
        f"bad profiler magic 0x{magic_be:08X}; expected 0x{MAGIC:08X} "
        "in canonical or 32-bit word-swapped form"
    )


def read_u32_be(blob: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(blob):
        raise ValueError(f"snapshot is too short for 32-bit read at offset 0x{offset:X}")
    return struct.unpack_from(">I", blob, offset)[0]


def reconstruct_samples(
    blob: bytes,
    magic_address: int,
    buffer_address: int,
    buffer_end_address: int,
) -> tuple[dict[str, int | str], list[int]]:
    if len(blob) < HEADER_SIZE:
        raise ValueError("snapshot is shorter than the profiling header")

    blob, snapshot_format = normalize_snapshot(blob)
    header = struct.unpack_from(">8I", blob, 0)
    magic, version, interval, capacity, write_ptr, sample_count, last_epc, reserved = header
    if magic != MAGIC:
        raise ValueError(f"bad profiler magic 0x{magic:08X}; expected 0x{MAGIC:08X}")
    if capacity == 0:
        raise ValueError("profiler capacity is zero")

    buffer_offset = buffer_address - magic_address
    buffer_bytes = buffer_end_address - buffer_address
    if buffer_offset < HEADER_SIZE:
        raise ValueError("profile_sample_buffer overlaps the profiler header")
    if buffer_bytes != capacity * 4:
        raise ValueError(
            f"ELF buffer size ({buffer_bytes} bytes) does not match snapshot capacity "
            f"({capacity * 4} bytes)"
        )
    if buffer_offset + buffer_bytes > len(blob):
        raise ValueError(
            f"snapshot is {len(blob)} bytes but {buffer_offset + buffer_bytes} bytes are required"
        )
    if not (buffer_address <= write_ptr <= buffer_end_address):
        raise ValueError(f"write pointer 0x{write_ptr:08X} is outside the sample buffer")
    if (write_ptr - buffer_address) % 4:
        raise ValueError("write pointer is not word-aligned within the sample buffer")

    ring = [
        read_u32_be(blob, buffer_offset + index * 4)
        for index in range(capacity)
    ]
    valid = min(sample_count, capacity)
    write_index = (write_ptr - buffer_address) // 4
    if write_index == capacity:
        # `profile_write_ptr` should normally wrap immediately to the beginning,
        # but tolerate an end pointer in externally captured/intermediate data.
        write_index = 0

    if sample_count < capacity:
        samples = ring[:valid]
    elif valid:
        samples = ring[write_index:] + ring[:write_index]
    else:
        samples = []

    meta: dict[str, int | str] = {
        "snapshot_format": snapshot_format,
        "version": version,
        "interval": interval,
        "capacity": capacity,
        "write_ptr": write_ptr,
        "sample_count": sample_count,
        "last_epc": last_epc,
        "reserved": reserved,
        "valid_samples": valid,
    }
    return meta, samples


def print_counter(title: str, counts: collections.Counter[str], total: int, limit: int | None = None) -> None:
    print(f"\n{title}:")
    items = counts.most_common(limit)
    for name, count in items:
        percentage = count * 100.0 / total
        print(f"  {percentage:6.2f}%  {count:5d}  {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "snapshot",
        type=Path,
        help="raw profiler memory snapshot (canonical N64 or supported emulator word order)",
    )
    parser.add_argument("elf", type=Path, help="matching PROFILE=1 sodium64 ELF")
    parser.add_argument(
        "--nm",
        default="mips64-elf-nm",
        help="nm executable for the N64 toolchain (default: mips64-elf-nm)",
    )
    parser.add_argument(
        "--map",
        dest="linker_map",
        type=Path,
        help="matching GNU ld map for object/subsystem classification",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="optional machine-readable profile summary path",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="number of hottest symbols to print (default: 30)",
    )
    args = parser.parse_args()

    addresses, symbols, named = load_symbols(args.elf, args.nm)
    required = ["profile_magic", "profile_sample_buffer", "profile_sample_buffer_end"]
    missing = [name for name in required if name not in named]
    if missing:
        raise SystemExit(f"matching ELF is missing profiler symbols: {', '.join(missing)}")

    blob = args.snapshot.read_bytes()
    meta, samples = reconstruct_samples(
        blob,
        named["profile_magic"],
        named["profile_sample_buffer"],
        named["profile_sample_buffer_end"],
    )

    print("Sodium64 statistical profile")
    print(f"  snapshot format: {meta['snapshot_format']}")
    print(f"  version:         {meta['version']}")
    print(f"  interval:        {meta['interval']} Count ticks")
    print(f"  total samples:   {meta['sample_count']}")
    print(f"  valid samples:   {meta['valid_samples']}")
    print(f"  last EPC:        0x{int(meta['last_epc']):08X}")

    result: dict[str, object] = {
        "meta": meta,
        "symbols": {},
        "objects": {},
        "subsystems": {},
    }

    if not samples:
        print("\nNo samples available.")
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return 0

    symbolicated = [nearest_symbol(pc, addresses, symbols) for pc in samples]
    symbol_counts = collections.Counter(base_symbol_name(item) for item in symbolicated)
    total = len(samples)

    print_counter("Hottest sampled symbols/regions", symbol_counts, total, max(args.top, 0))
    result["symbols"] = dict(symbol_counts)

    if args.linker_map:
        starts, text_ranges = load_text_ranges(args.linker_map)
        object_counts: collections.Counter[str] = collections.Counter()
        subsystem_counts: collections.Counter[str] = collections.Counter()

        for pc, symbolicated_name in zip(samples, symbolicated, strict=True):
            if JIT_START <= pc < JIT_END:
                object_name = "[APU JIT generated code]"
            else:
                object_name = object_for_pc(pc, starts, text_ranges) or "[unknown object]"
            object_counts[object_name] += 1
            subsystem_counts[
                subsystem_for_sample(
                    pc,
                    symbolicated_name,
                    None if object_name.startswith("[") else object_name,
                )
            ] += 1

        print_counter("Sampled subsystems", subsystem_counts, total)
        print_counter("Sampled R4300 objects", object_counts, total)
        result["objects"] = dict(object_counts)
        result["subsystems"] = dict(subsystem_counts)

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or str(exc), file=sys.stderr)
        raise SystemExit(exc.returncode or 1)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
