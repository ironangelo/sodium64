#!/usr/bin/env python3
"""Record lightweight, reproducible metadata for a Sodium64 build."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fmt_size(size: int) -> str:
    return f"{size} bytes"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--elf", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    required = [args.rom, args.elf]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("missing required build outputs: " + ", ".join(missing))

    source_files = sorted(Path("src").glob("*.S")) + sorted(Path("src").glob("*.h"))
    source_bytes = sum(path.stat().st_size for path in source_files)
    maps = sorted(args.build_dir.glob("*.map"))

    lines = [
        "# Sodium64 build metrics",
        "",
        f"commit: {os.environ.get('GITHUB_SHA', 'local')}",
        f"ref: {os.environ.get('GITHUB_REF', 'local')}",
        f"rom_size: {fmt_size(args.rom.stat().st_size)}",
        f"rom_sha256: {sha256(args.rom)}",
        f"elf_size: {fmt_size(args.elf.stat().st_size)}",
        f"source_files: {len(source_files)}",
        f"source_bytes: {source_bytes}",
        f"map_files: {len(maps)}",
    ]

    for path in maps:
        lines.append(f"map.{path.name}: {fmt_size(path.stat().st_size)}")

    text = "\n".join(lines) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
