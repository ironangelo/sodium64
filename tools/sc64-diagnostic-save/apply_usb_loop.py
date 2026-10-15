#!/usr/bin/env python3
"""Apply the archived USB menu overlay to a clean pinned upstream checkout."""
from pathlib import Path
import argparse
import shutil
import subprocess

PIN = "e28c26e1aeae3c18851fc24118080e23e5a86a9f"
HELPERS = ("diagnostic_save.c", "diagnostic_save.h", "diagnostic_pool.c",
           "diagnostic_pool.h", "diagnostic_pool_menu.c", "continuous_save_abi.h")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    repo = args.checkout.resolve()
    source = Path(__file__).resolve().parent
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    if head != PIN:
        parser.error("upstream pin mismatch")
    dirty = subprocess.run(["git", "diff", "--quiet", "--ignore-submodules=all",
                            "HEAD", "--"], cwd=repo)
    if dirty.returncode:
        parser.error("upstream tracked files must be clean; preserve other work first")
    overlay = source / "usb-menu" / "overlay"
    planned = [(p, repo / p.relative_to(overlay))
               for p in sorted(overlay.rglob("*")) if p.is_file()]
    planned += [(source / name, repo / "src/menu" / name) for name in HELPERS]
    planned += [(source / "usb-menu/usb-loop.mk", repo / "usb-loop.mk")]
    # Validate all inputs and destinations before modifying any file.
    for original, target in planned:
        if not original.is_file() or not target.resolve().is_relative_to(repo):
            parser.error("invalid overlay input or destination")
        if target.is_symlink():
            parser.error("refusing to replace a symlink")
        if target.exists():
            relative = target.relative_to(repo).as_posix()
            tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", relative],
                                     cwd=repo, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
            if tracked.returncode and target.read_bytes() != original.read_bytes():
                parser.error("conflicting untracked file: " + relative)
    for original, target in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
    print("Applied pinned menu source snapshot; full build/asset/ABI checks still required.")

if __name__ == "__main__":
    main()
