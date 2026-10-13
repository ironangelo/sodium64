#!/usr/bin/env python3
"""Compile the production parser against original synthetic fixtures. No USB."""
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc',default=os.environ.get('CC','gcc'))
    parser.add_argument('--json-output',type=Path)
    parser.add_argument('--audio-observer',action='store_true')
    parser.add_argument('--brr-observer',action='store_true')
    parser.add_argument('--koff-release',action='store_true')
    parser.add_argument('--mix-observer',action='store_true')
    parser.add_argument('--gain-probe',action='store_true')
    parser.add_argument('--full-dsp-probe',action='store_true')
    parser.add_argument('--full-dsp-pc-profile',action='store_true')
    parser.add_argument('--scene-state',action='store_true')
    parser.add_argument('--scene-rsp-rebind',action='store_true')
    parser.add_argument('--scene-rsp-context',action='store_true')
    parser.add_argument('--scene-slot',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-runtime-model-') as directory:
        executable=Path(directory)/('remote.exe' if os.name=='nt' else 'remote')
        cmd=[args.cc,'-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-DREMOTE_CONTROL_HOST']
        if args.audio_observer:cmd+=['-DSODIUM64_AUDIO_OBSERVER=1']
        if args.brr_observer:cmd+=['-DSODIUM64_AUDIO_OBSERVER=1','-DSODIUM64_BRR_OBSERVER=1']
        if args.koff_release:cmd+=['-DSODIUM64_AUDIO_OBSERVER=1','-DSODIUM64_DSP_KOFF_RELEASE=1']
        if args.mix_observer:cmd+=['-DSODIUM64_AUDIO_OBSERVER=1','-DSODIUM64_MIX_OBSERVER=1']
        if args.gain_probe:cmd+=['-DSODIUM64_AUDIO_OBSERVER=1','-DSODIUM64_MIX_OBSERVER=1','-DSODIUM64_DSP_GAIN_PROBE=1']
        if args.full_dsp_probe:cmd+=['-DSODIUM64_AUDIO_OBSERVER=1','-DSODIUM64_FULL_DSP_PROBE=1']
        if args.full_dsp_pc_profile:cmd+=['-DSODIUM64_AUDIO_OBSERVER=1','-DSODIUM64_FULL_DSP_PROBE=1','-DSODIUM64_FULL_DSP_PC_PROFILE=1']
        if args.scene_state or args.scene_rsp_rebind or args.scene_rsp_context or args.scene_slot:
            (Path(directory)/'regdef.h').write_text('/* Host C ABI fixture; no MIPS register macros. */\n')
            cmd+=['-DSODIUM64_SCENE_STATE=1','-DSODIUM64_NATIVE_DIAG_TRACE=1','-I',directory]
        if args.scene_rsp_rebind:cmd+=['-DSODIUM64_SCENE_RSP_REBIND=1']
        if args.scene_rsp_context:cmd+=['-DSODIUM64_SCENE_RSP_CONTEXT=1']
        if args.scene_slot:cmd+=['-DSODIUM64_SCENE_RSP_CONTEXT=1','-DSODIUM64_SCENE_SLOT=1']
        if os.name!='nt':cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        cmd += [str(root/'src/remote_control.c'),str(root/'scripts/fixtures/remote_control_host.c'),'-o',str(executable)]
        subprocess.run(cmd,check=True)
        result=subprocess.run([str(executable)],capture_output=True,text=True)
        if result.returncode:
            print(result.stdout+result.stderr,end='')
            result.check_returncode()
        print(result.stdout,end='')
        match=re.search(r'PASS cases=(\d+) fuzz=(\d+)',result.stdout);assert match
        proof=dict(passed=True,cases=int(match[1]),fuzz=int(match[2]),production_parser=True,
                   hardware_mocked=True,physical_acceptance=False,
                   source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in
                                  ('src/remote_control.c','src/remote_control.S','src/remote_control.h',
                                   'scripts/fixtures/remote_control_host.c')})
        if args.json_output:args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
