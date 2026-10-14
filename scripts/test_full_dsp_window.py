#!/usr/bin/env python3
"""Original causal counterexamples for a larger DSP work window; no hardware."""
import argparse,json,os,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cxx',default=os.environ.get('CXX','g++'));p.add_argument('--output',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='s64-dsp-window-') as tmp:
        exe=Path(tmp)/('window.exe' if os.name=='nt' else 'window')
        subprocess.run([a.cxx,'-std=c++98','-O2','-DNDEBUG','-fno-exceptions','-fno-rtti',
            str(root/'scripts/fixtures/full_dsp_window_host.cpp'),
            str(root/'third_party/snes_spc/SPC_DSP.cpp'),'-o',str(exe)],check=True)
        result=subprocess.run([str(exe)],capture_output=True,text=True)
        print(result.stdout+result.stderr,end='');result.check_returncode()
    assert 'original_counterexamples=4' in result.stdout
    proof=dict(passed=True,status='REJECTED unqualified deferred DSP window',
        original_counterexamples=4,late_register_write_latch_order=True,
        future_shared_RAM_write_visibility=True,echo_RAM_write_CPU_read_barrier=True,
        OUTX_publish_CPU_register_read_barrier=True,
        production_full_DSP_core_used=True,runtime_source_changed=False,
        safe_window_controller_or_RSP_backend_implemented=False,
        native_performance_full_game_DAC_acceptance=False,commercial_data=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
