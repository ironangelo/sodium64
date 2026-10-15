#!/usr/bin/env python3
"""Execute the production retired-frame parser against original numeric inputs."""
import argparse,json,os,re,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cc',default=os.environ.get('CC','gcc'))
    p.add_argument('--json-output',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-usb-control-') as directory:
        executable=Path(directory)/('control.exe' if os.name=='nt' else 'control')
        cmd=[a.cc,'-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-DREMOTE_CONTROL_HOST']
        if os.name!='nt':cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        cmd += [str(root/'src/remote_control.c'),str(root/'scripts/fixtures/remote_control_host.c'),'-o',str(executable)]
        subprocess.run(cmd,check=True)
        result=subprocess.run([str(executable)],capture_output=True,text=True)
        if result.returncode:
            print(result.stdout+result.stderr,end='');result.check_returncode()
        print(result.stdout,end='')
        match=re.search(r'PASS cases=(\d+) fuzz=(\d+)',result.stdout);assert match
        proof={'passed':True,'cases':int(match[1]),'fuzz':int(match[2]),'production_parser':True,
               'hardware_mocked':True,'physical_acceptance':False,'commercial_data':False}
        assert proof['cases']>=50 and proof['fuzz']==32000
        if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
