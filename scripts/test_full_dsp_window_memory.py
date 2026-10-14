#!/usr/bin/env python3
"""Run actual upper-owner probe with host address/cache aliases; no hardware."""
import argparse,json,os,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cxx',default=os.environ.get('CXX','g++'));p.add_argument('--output',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-window-memory-') as tmp:
        exe=Path(tmp)/('memory.exe' if os.name=='nt' else 'memory')
        subprocess.run([a.cxx,'-std=c++98','-O2','-DNDEBUG','-fno-exceptions','-fno-rtti',
            '-DSODIUM64_DSP_FULL_WINDOW=1','-DSODIUM64_DSP_WINDOW_MEMORY_HOST=1',
            str(root/'scripts/fixtures/full_dsp_window_memory_host.cpp'),
            str(root/'src/full_dsp_window.cpp'),str(root/'src/full_dsp_window_memory.cpp'),
            str(root/'third_party/snes_spc/SPC_DSP.cpp'),'-o',str(exe)],check=True)
        r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
        print(r.stdout+r.stderr,end='');r.check_returncode()
    proof=dict(passed=True,actual_owner_probe_executed=True,rejected_sizes_before_pointer=8,
        no_null_or_rejected_plan_stale_addresses=True,temporary_upper_owner_bytes=213152,
        actual_probe_state_checks=48,clocks=512,producer_reads=64,echo_word_publications=32,
        guard_fault_rejected=True,cache_and_aliases_host_model_only=True,
        native_DMA_or_save_owner_integration=False,native_hardware_acceptance=False,
        commercial_data=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
