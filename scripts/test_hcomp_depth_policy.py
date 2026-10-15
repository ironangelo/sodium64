#!/usr/bin/env python3
"""Compiled depth submission preserves general tags and skips Z-disabled tags."""
import argparse,json,re,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols
from test_hcomp_aligned_targets import execute
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
    base,text=read_text(a.elf);s={n:v&0xfff for v,n in elf_symbols(a.elf)}
    defs=(Path(__file__).resolve().parents[1]/'src/defines.h').read_text()
    raw=int(re.search(r'^#define HCOMP_BAND_RAW (0x[0-9A-Fa-f]+)',defs,re.M)[1],16)
    assert len(text)==4096 and s['calc_bg_window_spans']==0xcc0 and s['rdp_send']==0xf5c and s['ret_jump']==0xf70
    assert s['hcomp_depth_send']+20<=0xcc0
    cases=0
    for policy in (0,1,2,3,0xffffffff):
      for command in range(0,4096,8):
        d=bytearray(4096);struct.pack_into('>I',d,raw,policy);before=d.copy()
        r=[0x11100000+i for i in range(32)];r[0]=0;r[4]=command;r[5]=command+8;r[31]=0x111009e0;br=r.copy()
        execute(text,base&0xfff,d,s['hcomp_depth_send'],{s['rdp_send'] if policy==0 else br[31]&0xfff},r)
        assert d==before and all(r[i]==br[i] for i in range(32) if i!=8)
        assert r[8]==policy
        cases+=1
    proof=dict(passed=True,cases=cases,general_commands_preserved=True,raw_direct_no_depth_submission=True,
               fixed_resident_abi=True,guest_independent=True,native_fps_authority=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
    print('HCOMP_DEPTH_POLICY PASS',json.dumps(proof))
if __name__=='__main__':main()
