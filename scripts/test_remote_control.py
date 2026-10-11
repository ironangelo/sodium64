#!/usr/bin/env python3
"""Compile the production parser against original synthetic fixtures. No USB."""
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc',default=os.environ.get('CC','gcc'))
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-runtime-model-') as directory:
        executable=Path(directory)/('remote.exe' if os.name=='nt' else 'remote')
        cmd=[args.cc,'-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-DREMOTE_CONTROL_HOST']
        if os.name!='nt':cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        cmd += [str(root/'src/remote_control.c'),str(root/'scripts/fixtures/remote_control_host.c'),'-o',str(executable)]
        subprocess.run(cmd,check=True)
        result=subprocess.run([str(executable)],check=True,capture_output=True,text=True)
        print(result.stdout,end='')
        match=re.search(r'PASS cases=(\d+) fuzz=(\d+)',result.stdout);assert match
        proof=dict(passed=True,cases=int(match[1]),fuzz=int(match[2]),production_parser=True,
                   hardware_mocked=True,physical_acceptance=False,
                   source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in
                                  ('src/remote_control.c','src/remote_control.S','src/remote_control.h',
                                   'scripts/fixtures/remote_control_host.c')})
        if args.json_output:args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
