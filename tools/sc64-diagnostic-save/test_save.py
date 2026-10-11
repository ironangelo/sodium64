#!/usr/bin/env python3
"""Compile the real reservation helper against a failing host FATFS shim."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys,tempfile
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--json-output',type=Path)
a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='s64-save-test-') as d:
    binary=Path(d)/('test-save.exe' if os.name=='nt' else 'test-save')
    compiler=os.environ.get('CC','cc')
    # Native Windows GCC lacks ASan; Linux CI continues to use both sanitizers.
    sanitize=[] if os.name=='nt' else ['-fsanitize=address,undefined']
    subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror',*sanitize,'-g','-I'+str(root/'host'),'-I'+str(root),str(root/'diagnostic_save.c'),str(root/'diagnostic_pool.c'),str(root/'host/test_save.c'),'-o',str(binary)],check=True)
    result=subprocess.run([str(binary),d],text=True,capture_output=True)
    print(result.stdout,end='')
    if result.stderr: print(result.stderr,end='',file=sys.stderr)
    result.check_returncode()
    match=re.search(r'SC64_CONTINUOUS_POOL PASS (\d+) cases:',result.stdout)
    assert match and int(match[1])>0 and 'SC64_DIAGNOSTIC_SAVE PASS' in result.stdout
    assert 'SC64_CURSOR PASS one read-only scan, 96 existing captures + 16 slots = 16 exclusive-create attempts' in result.stdout
    proof=dict(passed=True,pool_cases=int(match[1]),legacy_reservation_regressions=True,
        directory_scan_read_only=True,directory_scans_per_pool=1,
        cursor_existing_captures=96,cursor_exclusive_create_attempts=16,
        scan_open_read_close_failures_rejected=True,post_scan_collision_preserved=True,
        hardware_mocked=True,native_launch_time_qualified=False,
        sanitizers=['address','undefined'] if sanitize else [],
        descriptor_header_bytes=72,slot_bytes=264,maximum_slots=16,maximum_descriptor_bytes=4296,
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
            ('diagnostic_save.c','diagnostic_save.h','diagnostic_pool.c',
             'continuous_save_abi.h','host/fatfs/ff.h','host/test_save.c')})
    if a.json_output:
        a.json_output.parent.mkdir(parents=True,exist_ok=True)
        a.json_output.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
