#!/usr/bin/env python3
"""Verify default-off native assembler sections against the exact R61 source."""
import argparse,json,subprocess,tempfile
from pathlib import Path
from check_full_dsp_window_build import sections

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cc',required=True)
    p.add_argument('--output',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[1]
    baseline='61505bc6c3a0a40b3c293bde214b0248851c0fb0';checked=[]
    with tempfile.TemporaryDirectory(prefix='s64-spc-clock-build-') as tmp:
        stage=Path(tmp)
        for unit in ('apu_emitter','apu_address'):
            original=stage/(unit+'.S');original.write_bytes(subprocess.check_output(['git','show',baseline+':src/'+unit+'.S'],cwd=root))
            objects=[]
            for index,source in enumerate((original,root/'src'/(unit+'.S'))):
                obj=stage/(unit+str(index)+'.o')
                subprocess.run([a.cc,'-c','-mtune=vr4300','-march=vr4300','-Wa,--fatal-warnings',
                    '-I'+str(root/'src'),str(source),'-o',str(obj)],check=True)
                objects.append(sections(obj))
            assert objects[0]==objects[1],(unit,'default-off sections changed')
            checked.append(unit)
    proof=dict(passed=True,baseline_source=baseline,default_off_allocated_sections_byte_exact=checked,
               native_runtime_or_performance_acceptance=False,commercial_data=False)
    print(json.dumps(proof))
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
