#!/usr/bin/env python3
"""Rebuild the exact Gate-B hardware ROMs from public source + prep artifact.

Supported host: Ubuntu 24.04 / WSL Ubuntu. This script never downloads a
commercial ROM. It consumes the non-ROM gate-b-hardware-milestone-prep artifact,
rebuilds the two qualified public-source guests, applies the already-validated
patches, wraps them with the exact HW_PROFILE Sodium64 runtime, and refuses to
emit final Z64 files unless every pinned hash matches.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SRS_REPO = "https://github.com/undisbeliever/space-rescue-squad.git"
SRS_SHA = "e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865"
SRS_BASS_SHA = "9db6088a378061afc7b82f50997a5b9a1d951175"
SRS_UNTECH_EDITOR_SHA = "4c72dc69619c0c246aa7e6325b18b6fb3c219821"
SRS_TAD_SHA = "17823e5a55893e8442917abadb4e84feb216e5ad"
SRS_RELEASE_ROM_SHA256 = "d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0"
SRS_ROUTE_PATCH_SHA256 = "b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935"
SRS_ROUTE_ROM_SHA256 = "2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46"

NOVA_REPO = "https://github.com/NovaSquirrel/NovaTheSquirrel2.git"
NOVA_SHA = "94385f1812f3b322f939f79a29502a1a3ee6d87f"
NOVA_BASE_ROM_SHA256 = "fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a"
NOVA_BUILD_PATCH_SHA256 = "c33a2f6f2f39ca4328d702dab087dfb98bd1005d83feae897a7ace7b9b0b2e51"
NOVA_ROUTE_PATCH_SHA256 = "8c691e664976ccef3f299bb52530a626520a49c60c51a264fca29dce74797b4a"
NOVA_ROUTE_ROM_SHA256 = "4a996af6a93e997fdedf8ccd3d26ee4756b3ec12abb06ce023928a2519e20be6"


def run(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=cwd, env=env, check=True)


def output(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise SystemExit(f"{label} hash mismatch\nexpected: {expected}\nactual:   {actual}")
    print(f"{label}={actual}")


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing prep-artifact input: {path}")


def parse_manifest(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        if "=" in raw:
            k, v = raw.split("=", 1)
            result[k] = v
    return result


def apply_patch(repo: Path, patch: Path) -> None:
    run(["git", "-C", str(repo), "apply", "--check", str(patch)])
    run(["git", "-C", str(repo), "apply", str(patch)])


def clone_exact(url: str, dest: Path, sha: str) -> None:
    run(["git", "clone", "--filter=blob:none", url, str(dest)])
    run(["git", "-C", str(dest), "checkout", "--detach", sha])
    actual = output(["git", "-C", str(dest), "rev-parse", "HEAD"])
    if actual != sha:
        raise SystemExit(f"checkout mismatch for {dest}: {actual} != {sha}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prep_dir", type=Path, help="Extracted gate-b-hardware-milestone-prep artifact")
    ap.add_argument("output_dir", type=Path, nargs="?", default=Path("gate-b-hardware-roms"))
    ap.add_argument("--nova-python", default=os.environ.get("NOVA_PYTHON", "python3.8"))
    ns = ap.parse_args()

    prep = ns.prep_dir.resolve()
    out_dir = ns.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    base = prep / "hardware/base/sodium64.z64"
    converter = prep / "hardware/base/rom-converter.py"
    manifest_path = prep / "hardware/gate-b-hardware-manifest.txt"
    srs_patch = prep / "srs-v5-route.patch"
    nova_build_patch = prep / "nova2-deterministic-build.patch"
    nova_route_patch = prep / "nova2-firstlevel-route.patch"
    srs_wrapped_sha_file = prep / "hardware/srs-v5-wrapped.sha256"
    nova_wrapped_sha_file = prep / "hardware/nova2-wrapped.sha256"

    for path in [
        base, converter, manifest_path, srs_patch, nova_build_patch,
        nova_route_patch, srs_wrapped_sha_file, nova_wrapped_sha_file,
    ]:
        require_file(path)

    for cmd in ["git", "gcc", "make", "cmake", "ninja", "cargo", "ca65", "lz4"]:
        if shutil.which(cmd) is None:
            raise SystemExit(
                f"missing command: {cmd}\n"
                "Ubuntu/WSL packages used by CI: build-essential cc65 cmake git "
                "libgl1-mesa-dev libmsgsl-dev libsdl2-dev lz4 ninja-build cargo"
            )
    nova_python = shutil.which(ns.nova_python)
    if nova_python is None:
        raise SystemExit(
            f"missing Nova2 Python 3.8 executable: {ns.nova_python}\n"
            "Install Python 3.8 or pass --nova-python /path/to/python3.8"
        )

    require_hash(srs_patch, SRS_ROUTE_PATCH_SHA256, "srs_route_patch_sha256")
    require_hash(nova_build_patch, NOVA_BUILD_PATCH_SHA256, "nova_build_patch_sha256")
    require_hash(nova_route_patch, NOVA_ROUTE_PATCH_SHA256, "nova_route_patch_sha256")

    manifest = parse_manifest(manifest_path)
    required_manifest = {
        "hw_profile": "1",
        "warmup_windows": "2",
        "measured_windows": "5",
        "forced_frameskip": "0",
        "forced_apu_clock": "21",
        "forced_audio": "4",
        "forced_precision": "8",
    }
    for key, expected in required_manifest.items():
        if manifest.get(key) != expected:
            raise SystemExit(f"prep manifest mismatch: {key}={manifest.get(key)!r}, expected {expected!r}")
    base_expected = manifest.get("base_sodium64_sha256")
    if not base_expected:
        raise SystemExit("prep manifest lacks base_sodium64_sha256")
    require_hash(base, base_expected, "base_sodium64_sha256")

    srs_wrapped_expected = srs_wrapped_sha_file.read_text().split()[0]
    nova_wrapped_expected = nova_wrapped_sha_file.read_text().split()[0]
    for label, value in [
        ("srs_wrapped_z64_sha256", srs_wrapped_expected),
        ("nova_wrapped_z64_sha256", nova_wrapped_expected),
    ]:
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise SystemExit(f"invalid {label} in prep artifact: {value!r}")

    jobs = str(max(1, os.cpu_count() or 1))

    with tempfile.TemporaryDirectory(prefix="s64-gate-b-") as tmp_s:
        tmp = Path(tmp_s)

        print("== Rebuild Space Rescue Squad ==")
        srs = tmp / "space-rescue-squad"
        clone_exact(SRS_REPO, srs, SRS_SHA)
        run(["git", "-C", str(srs), "submodule", "update", "--init", "--recursive"])
        submodules = {
            "bass-untech": SRS_BASS_SHA,
            "untech-editor": SRS_UNTECH_EDITOR_SHA,
            "terrific-audio-driver": SRS_TAD_SHA,
        }
        for rel, expected in submodules.items():
            actual = output(["git", "-C", str(srs / rel), "rev-parse", "HEAD"])
            if actual != expected:
                raise SystemExit(f"SRS submodule mismatch {rel}: {actual} != {expected}")

        ue_build = srs / "untech-editor/build"
        run(["cmake", "-S", str(srs / "untech-editor"), "-B", str(ue_build),
             "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release"])
        run(["cmake", "--build", str(ue_build), "--parallel", jobs, "--target",
             "untech-compiler", "untech-lz4c", "untech-png2snes",
             "untech-png2tileset", "untech-write-sfc-checksum"])
        run(["make", f"-j{jobs}", "-C", str(srs / "terrific-audio-driver/wiz")])
        run(["cargo", "build", "--quiet", "--release", "--manifest-path",
             str(srs / "terrific-audio-driver/Cargo.toml"), "--package", "tad-compiler"])
        for png in (srs / "game/resources").rglob("*.png"):
            png.touch()
        run(["make", "-C", str(srs / "game"), "directories"])
        run(["make", "-C", str(srs / "game"), "bin/space-rescue-squad.sfc"])
        srs_rom = srs / "game/bin/space-rescue-squad.sfc"
        require_hash(srs_rom, SRS_RELEASE_ROM_SHA256, "srs_release_rom_sha256")

        apply_patch(srs, srs_patch)
        run(["make", "-C", str(srs / "game"), "bin/space-rescue-squad.sfc"])
        require_hash(srs_rom, SRS_ROUTE_ROM_SHA256, "srs_route_rom_sha256")

        print("== Rebuild Nova the Squirrel 2 ==")
        nova = tmp / "nova-the-squirrel-2"
        clone_exact(NOVA_REPO, nova, NOVA_SHA)
        apply_patch(nova, nova_build_patch)
        run([nova_python, "-m", "pip", "install", "--disable-pip-version-check", "Pillow==7.1.2"])
        run(["gcc", str(nova / "audio/brr/gssbrr.c"), "-lm", "-o", str(nova / "audio/brr/gssbrr")])
        (nova / "obj/snes").mkdir(parents=True, exist_ok=True)

        shim = tmp / "nova-python"
        shim.mkdir()
        (shim / "python3").symlink_to(Path(nova_python))
        nova_env = os.environ.copy()
        nova_env["PYTHONHASHSEED"] = "0"
        nova_env["PATH"] = f"{shim}:{nova_env['PATH']}"

        run(["make", "-C", str(nova), "-j1", "nova-the-squirrel-2.sfc"], env=nova_env)
        nova_rom = nova / "nova-the-squirrel-2.sfc"
        require_hash(nova_rom, NOVA_BASE_ROM_SHA256, "nova_base_rom_sha256")

        apply_patch(nova, nova_route_patch)
        run(["make", "-C", str(nova), "-j1", "nova-the-squirrel-2.sfc"], env=nova_env)
        require_hash(nova_rom, NOVA_ROUTE_ROM_SHA256, "nova_route_rom_sha256")

        def wrap(guest: Path, guest_name: str, final_name: str, expected: str) -> Path:
            wrap_dir = tmp / f"wrap-{guest_name}"
            wrap_dir.mkdir()
            shutil.copy2(base, wrap_dir / "sodium64.z64")
            shutil.copy2(converter, wrap_dir / "rom-converter.py")
            shutil.copy2(guest, wrap_dir / f"{guest_name}.smc")
            subprocess.run(
                [sys.executable, "rom-converter.py"],
                cwd=wrap_dir,
                input=b"",
                check=True,
            )
            wrapped = wrap_dir / "out" / f"{guest_name}.z64"
            require_file(wrapped)
            require_hash(wrapped, expected, f"{guest_name}_wrapped_z64_sha256")
            final = out_dir / final_name
            shutil.copy2(wrapped, final)
            return final

        print("== Wrap exact HW_PROFILE workloads ==")
        srs_final = wrap(srs_rom, "gate-b-srs-v5", "gate-b-srs-v5.z64", srs_wrapped_expected)
        nova_final = wrap(nova_rom, "gate-b-nova2", "gate-b-nova2.z64", nova_wrapped_expected)

        local_manifest = out_dir / "LOCAL_REBUILD_MANIFEST.txt"
        local_manifest.write_text(
            "\n".join([
                f"source_prep_manifest_sha256={sha256(manifest_path)}",
                f"base_sodium64_sha256={sha256(base)}",
                f"srs_guest_rom_sha256={sha256(srs_rom)}",
                f"srs_wrapped_z64_sha256={sha256(srs_final)}",
                f"nova_guest_rom_sha256={sha256(nova_rom)}",
                f"nova_wrapped_z64_sha256={sha256(nova_final)}",
                "forced_frameskip=0",
                "forced_apu_clock=21",
                "forced_audio=4",
                "forced_precision=8",
                "warmup_windows=2",
                "measured_windows=5",
                "",
            ])
        )

    print("\nValidated hardware ROMs:")
    print(f"  {srs_final}")
    print(f"  {nova_final}")
    print(f"  {local_manifest}")
    print("All pinned hashes matched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
