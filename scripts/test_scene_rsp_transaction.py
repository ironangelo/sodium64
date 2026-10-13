#!/usr/bin/env python3
"""Production transaction, synthetic SP/PI callbacks and failure positions."""
import argparse,json,os,re,subprocess,tempfile
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cc',default=os.environ.get('CC','gcc'));ap.add_argument('--output',type=Path)
    a=ap.parse_args();root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-scene-rsp-') as d:
        exe=Path(d)/('probe.exe' if os.name=='nt' else 'probe')
        cmd=[a.cc,'-std=c11','-O2','-Wall','-Wextra','-Werror']
        if os.name!='nt':cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        cmd += [str(root/'src/scene_rsp_probe.c'),str(root/'scripts/fixtures/scene_rsp_probe_host.c'),'-o',str(exe)]
        subprocess.run(cmd,check=True);r=subprocess.run([str(exe)],capture_output=True,text=True)
        print(r.stdout+r.stderr,end='');r.check_returncode()
        cases=int(re.search(r'PASS cases=(\d+)',r.stdout)[1])
        result=dict(passed=True,cases=cases,production_transaction=True,
                    prevalidation_before_mutation=True,restore_readback=True,
                    complete_backup_hash_checked=True,hardware_mocked=True,native_acceptance=False)
        if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
