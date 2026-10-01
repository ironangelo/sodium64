#!/usr/bin/env python3
"""Executed synthetic admission for a private SMW probe, without a game claim."""
import argparse,hashlib,json
from pathlib import Path
from check_hcomp_band_scope import validate
from capture_hcomp_fullheight import classify
from make_hcomp_fullheight import CASES

def audit(qualified,captures):
    validate(qualified)
    cases={}
    for case in CASES:
        root=captures/f'full-{case}'
        result=json.loads((root/'result.json').read_text())
        frame=(root/'frame.bin').read_bytes()
        assert len(frame)==280*240*2
        assert result['case']==case and result['passed']
        assert result['checked_pixels']==224*256
        assert result['image_sha256']==hashlib.sha256(frame).hexdigest()
        assert classify(frame,case)['passed'],case
        assert result['compact_guards_passed']
        keys={hex(x) for start in (0xe2000,0xe4000,0xe6000) for x in (start-64,start+0x1180)}
        assert set(result['compact_guards'])==keys
        assert all(value=='00'*64 for value in result['compact_guards'].values())
        assert len(bytes.fromhex(result['delivered_controls']))==4
        assert not result['framebuffer_seeding'] and not result['guest_state_writes']
        assert not result['cadence_authority']
        engine=result['engine']
        assert engine['rsp_halted'] and engine['rdp_commands_complete']
        assert not any(engine[k] for k in ('rdp_tmem_busy','rdp_pipe_busy','rdp_buffer_busy'))
        cases[case]=dict(passed=True,pixels=224*256,image_sha256=result['image_sha256'])
    sram=json.loads((captures/'full-sram/result.json').read_text())
    assert sram['ordinary_sram_import_and_pi_save_passed']
    saved=(captures/'full-sram/cart.sav').read_bytes()
    expected=bytearray(32768);expected[:8]=b'S64GAME!';expected[8]=expected[16]=0xa7
    assert saved==expected,'ordinary SRAM import echo, game writes or unchanged cart tail differ'
    return dict(smw_private_probe_ready=True,normal_profile=True,diagnostic_hooks_absent=True,
                geometry_admission='VALIDATED_SYNTHETIC_224_AND_SHORT_SECTIONS',cases=cases,
                ordinary_sram_import_and_pi_save_passed=True,
                normal_elf_sha256=hashlib.sha256((qualified/'normal/build/sodium64.elf').read_bytes()).hexdigest(),
                commercial_rom_executed=False,smw_compatibility_or_iris_pass=False,
                native_hue_closed=False,real_n64_cadence_or_performance_qualified=False)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qualified',type=Path,required=True)
    ap.add_argument('--captures',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();r=audit(a.qualified,a.captures)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,sort_keys=True),flush=True)
    print('PRIVATE_SMW_PROBE_ADMISSION PASS; synthetic geometry, colors and ordinary SRAM; game/hardware pending')
