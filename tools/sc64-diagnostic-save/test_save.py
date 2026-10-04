#!/usr/bin/env python3
"""Compile the real reservation helper against a failing host FATFS shim."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='s64-save-test-') as d:
    binary=Path(d)/'test-save'
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I'+str(root/'host'),'-I'+str(root),str(root/'diagnostic_save.c'),str(root/'host/test_save.c'),'-o',str(binary)],check=True)
    subprocess.run([str(binary),d],check=True)
