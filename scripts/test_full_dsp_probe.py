#!/usr/bin/env python3
"""Run the original synthetic full-core/backup transaction on the host."""
import argparse,json,os,re,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cxx',default=os.environ.get('CXX','g++'))
    p.add_argument('--signal-elide',action='store_true')
    p.add_argument('--cache-probe',action='store_true')
    p.add_argument('--snapshot-core',action='store_true')
    p.add_argument('--json-output',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    if a.cache_probe and not a.snapshot_core:p.error('--cache-probe requires --snapshot-core')
    with tempfile.TemporaryDirectory(prefix='s64-full-dsp-') as tmp:
        exe=Path(tmp)/('probe.exe' if os.name=='nt' else 'probe')
        cmd=[a.cxx,'-std=c++98','-O2','-DNDEBUG','-fno-exceptions','-fno-rtti',
             str(root/'src/full_dsp_probe.cpp'),str(root/'third_party/snes_spc/SPC_DSP.cpp'),
             str(root/'scripts/fixtures/full_dsp_probe_host.cpp'),'-o',str(exe)]
        if a.signal_elide:cmd.insert(1,'-DSODIUM64_DSP_SIGNAL_ELIDE=1')
        if a.cache_probe:cmd.insert(1,'-DSODIUM64_DSP_FULL_CACHE_PROBE=1')
        if a.snapshot_core:cmd.insert(1,'-DSODIUM64_FULL_DSP_SNAPSHOT_CORE=1')
        subprocess.run(cmd,check=True)
        result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
    print(result.stdout,end='')
    scenarios=[dict(zip(('case','frames','checksum','nonzero'),map(int,m))) for m in
               re.findall(r'case(\d+) frames=(\d+) checksum=(\d+) nonzero=(\d+)',result.stdout)]
    assert len(scenarios)==(24 if a.cache_probe else 3) and 'FULL_DSP_PROBE PASS' in result.stdout
    for start in range(0,len(scenarios),3):
        assert [x['checksum'] for x in scenarios[start:start+3]]==[10420156,4185267178,422544410]
        assert [x['nonzero'] for x in scenarios[start:start+3]]==[4056,4080,4096]
    if a.cache_probe:scenarios=scenarios[:3]
    proof=dict(passed=True,synthetic_scenarios=scenarios,unmodified_complete_core=not(a.signal_elide or a.cache_probe),
               signal_elide=a.signal_elide,
               cache_probe=a.cache_probe,
               cache_modes_checked=8 if a.cache_probe else 1,
               core_color=4096 if a.cache_probe else None,PCM_color=7168 if a.cache_probe else None,
               Gaussian_color=6144 if a.cache_probe else None,Gaussian_lease_reset_and_all512_coefficients_exact=a.cache_probe,
               distinct_core_PCM_leases_and_all_other_snapshot_bytes_unchanged=a.cache_probe,
               snapshot_core=a.snapshot_core,
               memory_restoration_bytes=65536,backup_readback_blocks=128,
               restore_blocks=128,backup_fault_positions=16,restore_fault_positions=2,
               backup_corruption_rejected=True,invalid_inputs=5,
               native_performance_or_game_audio_claim=False,commercial_data=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')

if __name__=='__main__':main()
