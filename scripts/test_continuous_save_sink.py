#!/usr/bin/env python3
"""Compile the actual production SD algorithm against an original card model.

No microSD is accessed. Linux uses ASan/UBSan; --cc supports a local host GCC.
This proves protocol decisions/error handling, not physical SD durability.
"""
import argparse, hashlib, json, os, re, subprocess, tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cc',default=os.environ.get('CC','gcc'))
    p.add_argument('--json-output',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-continuous-sink-') as tmp:
        exe=Path(tmp)/('sink.exe' if os.name=='nt' else 'sink')
        cmd=[a.cc,'-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-DCONTINUOUS_SAVE_HOST']
        if os.name!='nt':cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        cmd += [str(root/'src/continuous_save.c'),str(root/'scripts/fixtures/continuous_save_host.c'),'-o',str(exe)]
        subprocess.run(cmd,check=True)
        result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
        print(result.stdout,end='')
        match=re.search(r'PASS cases=(\d+) operations=(\d+)',result.stdout)
        assert match and int(match[1])>0
        proof=dict(passed=True,cases=int(match[1]),operations_per_success=int(match[2]),
                   actual_production_c_algorithm=True,hardware_boundary_mocked=True,
                   fragmented_maps=True,no_overwrite=True,explicit_sector_readback=True,
                   incomplete_header_before_body_complete_header_last=True,
                   failure_blocks_reuse=True,soft_restart_skips_used_slots=True,
                   native_sd_persistence_authority=False,
                   source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in
                                  ('src/continuous_save.c','scripts/fixtures/continuous_save_host.c')})
        if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')

if __name__=='__main__':main()
