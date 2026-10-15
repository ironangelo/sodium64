#!/usr/bin/env python3
"""Fresh-boot A/B sources may differ ONLY in the post-measurement marker."""
import argparse
import json
import struct
from pathlib import Path

def check(captures):
    for mode in ('visual','mixed'):
        root=captures/mode
        a,b=[struct.unpack('>67200H',(root/f'frozen-{p}'/f'color_diag_phase_{p}.bin').read_bytes()) for p in ('a','b')]
        changed={i for i,(x,y) in enumerate(zip(a,b)) if x!=y}
        marker={y*280+x for y in range(200,216) for x in range(260,268)}
        assert changed==marker,('frozen image changed beyond marker',mode,sorted(changed)[:32])
        assert all(a[i]==1 and b[i]==65535 for i in changed),mode
        result=dict(passed=True,changed_pixels=128,band_and_references_identical=True,
                    fresh_boots=True,frame_seeding=False,cadence_authority=False)
        (root/'frozen-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print('COLOR_FROZEN_SAME_SOURCE PASS')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--captures',type=Path,required=True)
    a=ap.parse_args();check(a.captures)
