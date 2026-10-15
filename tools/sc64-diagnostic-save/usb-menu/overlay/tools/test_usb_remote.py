"""Compile real menu USB/loader code and run bounded synthetic host checks."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
compiler = shutil.which("gcc") or (r"C:\msys64\mingw64\bin\gcc.exe" if os.name == "nt" else "gcc")
environment = dict(os.environ)
environment["PATH"] = str(Path(compiler).parent) + os.pathsep + environment.get("PATH", "")
with tempfile.TemporaryDirectory(prefix="s64-menu-usb-") as folder:
    work = Path(folder)
    (work / "menu" / "emulators").mkdir(parents=True)
    (work / "SNES").mkdir()
    executable = work / ("tests.exe" if os.name == "nt" else "tests")
    command = [compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-sign-compare",
               "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
               "-I", str(root / "tools/usb-remote-tests/stubs"),
               "-I", str(root / "src"), "-I", str(root / "src/libs/miniz"),
               "-I", str(root / "libdragon/include"),
               str(root / "tools/usb-remote-tests/test_remote.c"),
               str(root / "src/menu/usb_comm.c"), str(root / "src/menu/cart_load.c"),
               str(root / "src/menu/path.c"), str(root / "src/menu/ini_parser.c"),
               str(root / "src/utils/fs.c"), "-o", str(executable)]
    subprocess.run(command, check=True, env=environment)
    subprocess.run([str(executable), work.as_posix()], check=True, env=environment)
