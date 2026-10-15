#!/usr/bin/env python3
"""Replay frozen first-hand PI saves after correcting an audio oracle only.

The original job stopped at hw_profile_done after uninterrupted execution;
both source/cart equality, graphics-source copies, chronological PCM, yellow
reference and five budgets passed BEFORE its incorrect unequal-channel oracle.
Current ROM/ELF must equal those original executed bytes. This is a host-only
oracle replay, not a newly executed hardware/emulator run.
"""
import argparse
import hashlib
import json
from pathlib import Path
from decode_stage2_probe import decode,qualify_workload

PINS={
 'hardware/sodium64-stage2-visual.z64':'aab1917d2a638294b908f095518388b6bfabf4cf190580255c951381d4363f0a',
 'hardware/sodium64-stage2-mixed.z64':'f70e227691c384ffdf2b7a15f971a603c7a24bae312628ff1c6719faa4c04cdb',
 'qualified/hw-profile/sodium64.z64':'e1ce6c335bc8d7f2ecfcba7dd127c9073c1b313e2ce9f8f1032f865b405e4d4e',
 'qualified/hw-profile/build/sodium64.elf':'4cd6133e42c78c11607d73169edfa24914b437ac0fd4a052c31b87aedca41d23',
}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--artifact',type=Path,required=True)
    ap.add_argument('--current',type=Path,default=Path('.'))
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for path,pin in PINS.items():
        for root in [args.artifact,args.current]:
            assert hashlib.sha256((root/path).read_bytes()).hexdigest()==pin,(root,path)
    for mode in ['visual','mixed']:
        saved=(args.artifact/'captures'/mode/'cart.sav').read_bytes()
        r,raw,_,_=decode(saved);r['workload']=qualify_workload(r,raw,mode=='mixed')
        r['first_hand_execution']=dict(sha='47398d7016d98058c9841b319ee90e28953319f5',
                                     run=36716662088,job=109891143876,artifact=11097390096,
                                     source='Actual PI cart bytes after continuous finalization')
        r['classification']='S64V_NATIVE_PROBE_TRANSPORT_AND_ORACLE_VALIDATED'
        r['validation']='Host-only corrected-oracle replay; runtime bytes identical to executed build'
        (args.output/(mode+'.json')).write_text(json.dumps(r,indent=2)+'\n')
        print(mode,r['classification'],r['workload'])

if __name__=='__main__':main()
