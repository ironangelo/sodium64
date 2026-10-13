#!/usr/bin/env python3
"""Compare all clocked DSP state/RAM/PCM, including zero/nonzero boundaries."""
import argparse,json,os,re,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cxx',default=os.environ.get('CXX','g++'))
    p.add_argument('--json-output',type=Path)
    p.add_argument('--full-brr-group',action='store_true')
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    flags=['-std=c++98','-O2','-DNDEBUG','-fno-exceptions','-fno-rtti',
           '-I'+str(root/'third_party/snes_spc')]
    with tempfile.TemporaryDirectory(prefix='s64-signal-elide-') as tmp:
        directory=Path(tmp);reference=directory/'reference.o'
        source=root/'third_party/snes_spc/SPC_DSP.cpp'
        def compile_object(path,target,name,elide):
            cmd=[a.cxx,*flags,'-DSPC_DSP='+name,
                 '-DSPC_State_Copier='+name.replace('_DSP','_State_Copier')]
            if elide:cmd+=['-DSODIUM64_DSP_SIGNAL_ELIDE=1']
            if elide and a.full_brr_group:cmd+=['-DSODIUM64_DSP_FULL_BRR_GROUP=1']
            subprocess.run([*cmd,'-c',str(path),'-o',str(target)],check=True)
        compile_object(source,reference,'Reference_DSP',False)
        rejected=[];positive=None
        text=source.read_text()
        variants=[('positive',text),
                  ('env_one_boundary',text.replace('if ( v->env )','if ( v->env > 1 )')),
                  ('noise_substitution',text.replace('int output = (m.t_non & v->vbit) ?',
                                                   'int output = (m.t_non & 0) ?'))]
        assert text.count('if ( v->env )')==1
        assert text.count('int output = (m.t_non & v->vbit) ?')==1
        if a.full_brr_group:
            assert text.count('p2=p1>>1;')==1
            assert text.count('pos[i+SPC_DSP::brr_buf_size]=pos[i]=s;')==1
            variants += [('BRR_history',text.replace('p2=p1>>1;','p2=p1;')),
                         ('BRR_mirror',text.replace('pos[i+SPC_DSP::brr_buf_size]=pos[i]=s;','pos[i]=s;')),
                         ('BRR_invalid_range',text.replace('nybbles&=0x8888;shift=9;','nybbles&=0xffff;shift=9;'))]
        for name,content in variants:
            path=directory/(name+'.cpp');path.write_text(content)
            target=directory/(name+'.o');exe=directory/(name+('.exe' if os.name=='nt' else ''))
            compile_object(path,target,'Optimized_DSP',True)
            fixture_flags=['-DSODIUM64_TEST_FULL_BRR_GROUP=1'] if a.full_brr_group else []
            subprocess.run([a.cxx,*flags,*fixture_flags,str(root/'scripts/fixtures/dsp_signal_elide_host.cpp'),
                            str(reference),str(target),'-o',str(exe)],check=True)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            if name=='positive':
                assert result.returncode==0,result.stderr
                match=re.search(r'directed=(\d+) slices=(\d+) frames=(\d+) state_checks=(\d+)',result.stdout)
                assert match,result.stdout
                positive=dict(zip(('directed_V3c_cases','clock_slices','output_stereo_frames','all_state_checks'),map(int,match.groups())))
                assert positive['directed_V3c_cases']==12288 and positive['clock_slices']==8192
                if a.full_brr_group:
                    count=re.search(r'FULL_BRR_GROUP PASS cases=(\d+)',result.stdout)
                    assert count and int(count[1])==82944
                    positive['directed_V4_independent_BRR_cases']=int(count[1])
                print(result.stdout,end='')
            else:
                assert result.returncode!=0 and 'mismatch all core state' in result.stderr,(name,result)
                rejected.append(name)
    proof=dict(passed=True,**positive,negative_mutations_rejected=rejected,
               all_core_state_after_host_pointer_normalization=True,
               full_APURAM_bytes=65536,all_DSP_registers=128,PCM_full_extent_equal=True,
               arbitrary_clock_phases_and_internal_output_buffer=True,
               PMON_KON_KOFF_envelope_noise_BRR_echo_and_reset_exercised=True,
               pinned_core_is_flag0_reference=True,native_timing_or_gameplay_claim=False,
               full_brr_group=a.full_brr_group,
               commercial_data=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))

if __name__=='__main__':main()
