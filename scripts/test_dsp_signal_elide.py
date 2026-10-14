#!/usr/bin/env python3
"""Compare all clocked DSP state/RAM/PCM, including zero/nonzero boundaries."""
import argparse,json,os,re,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cxx',default=os.environ.get('CXX','g++'))
    p.add_argument('--json-output',type=Path)
    p.add_argument('--gauss-batch',action='store_true')
    p.add_argument('--brr-batch',action='store_true')
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
            if elide and a.gauss_batch:cmd+=['-DSODIUM64_DSP_FULL_GAUSS_BATCH=1']
            if elide and a.brr_batch:cmd+=['-DSODIUM64_DSP_FULL_BRR_BATCH=1']
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
        if a.gauss_batch:
            assert text.count('gaussian_cache [i] = interpolate( v );')==1
            assert text.count('cached_index = (v->regs - m.regs) >> 4;')==1
            variants += [('batch_value',text.replace('gaussian_cache [i] = interpolate( v );','gaussian_cache [i] = interpolate( v ) + 64;')),
                         ('voice_identity',text.replace('cached_index = (v->regs - m.regs) >> 4;','cached_index = ((v->regs - m.regs) >> 4) ^ 1;'))]
            prefix='void SPC_DSP::soft_reset_common()\n{\n#ifdef SODIUM64_DSP_FULL_GAUSS_BATCH\n\tgaussian_valid = 0;'
            assert text.count(prefix)==1
            variants += [('reset_cache',text.replace(prefix,prefix.replace('gaussian_valid = 0;','/* deliberately stale */')))]
        if a.brr_batch:
            substitutions=[('brr_input','job.header = m.t_brr_header;','job.header = m.t_brr_header ^ 4;'),
                ('brr_history','job.previous1 = v->buf [v->buf_pos + brr_buf_size - 1];','job.previous1 = v->buf [v->buf_pos + brr_buf_size - 1] + 2;'),
                ('brr_duplicate','pos [n + brr_buf_size] = pos [n] = s;','pos [n] = s;'),
                ('brr_return_flush','\t// arbitrary single-clock slices. No pending work crosses an external write.\n\tflush_brr_batch();',
                 '\t// arbitrary single-clock slices. No pending work crosses an external write.\n\t/* missing return flush */'),
                ('brr_soft_reset','\t// Soft reset retains decoded history, unlike load/hard reset.\n\tflush_brr_batch();',
                 '\t// Soft reset retains decoded history, unlike load/hard reset.\n\tbrr_pending = 0;')]
            for name,before,after in substitutions:
                assert text.count(before)==1;variants.append((name,text.replace(before,after)))
        for name,content in variants:
            path=directory/(name+'.cpp');path.write_text(content)
            target=directory/(name+'.o');exe=directory/(name+('.exe' if os.name=='nt' else ''))
            compile_object(path,target,'Optimized_DSP',True)
            fixture_flags=['-DSODIUM64_TEST_GAUSS_BATCH=1'] if a.gauss_batch else []
            if a.brr_batch:fixture_flags+=['-DSODIUM64_TEST_BRR_BATCH=1']
            subprocess.run([a.cxx,*flags,*fixture_flags,str(root/'scripts/fixtures/dsp_signal_elide_host.cpp'),
                            str(reference),str(target),'-o',str(exe)],check=True)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            if name=='positive':
                assert result.returncode==0,result.stderr
                match=re.search(r'directed=(\d+) slices=(\d+) frames=(\d+) state_checks=(\d+)',result.stdout)
                assert match,result.stdout
                positive=dict(zip(('directed_V3c_cases','clock_slices','output_stereo_frames','all_state_checks'),map(int,match.groups())))
                assert positive['directed_V3c_cases']==12288 and positive['clock_slices']==8192
                if a.gauss_batch or a.brr_batch:
                    phase=re.search(r'GAUSS_BATCH_PHASE PASS cases=(\d+) frames=(\d+)',result.stdout)
                    assert phase and int(phase[1])==9216
                    positive['directed_phase_cases']=int(phase[1]);positive['directed_phase_stereo_frames']=int(phase[2])
                if a.brr_batch:
                    marker=re.search(r'BRR_BATCH_BOUNDARY PASS width=(\d+)',result.stdout)
                    assert marker and int(marker[1])==8
                    positive['closed_input_peak_voices']=8
                    directed=re.search(r'BRR_BATCH_DIRECTED PASS cases=(\d+)',result.stdout)
                    assert directed and int(directed[1])==12288
                    positive['directed_V4_cases']=12288
                print(result.stdout,end='')
            else:
                error='mismatch Gauss reset invalidation' if name=='reset_cache' else 'mismatch all core state'
                assert result.returncode!=0 and error in result.stderr,(name,result)
                rejected.append(name)
    proof=dict(passed=True,**positive,negative_mutations_rejected=rejected,
               all_core_state_after_host_pointer_normalization=True,
               full_APURAM_bytes=65536,all_DSP_registers=128,PCM_full_extent_equal=True,
               arbitrary_clock_phases_and_internal_output_buffer=True,
               PMON_KON_KOFF_envelope_noise_BRR_echo_and_reset_exercised=True,
               pinned_core_is_flag0_reference=True,native_timing_or_gameplay_claim=False,
               gauss_batch=a.gauss_batch,brr_batch=a.brr_batch,
               derived_cache_is_outside_original_logical_state=a.gauss_batch or a.brr_batch,commercial_data=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))

if __name__=='__main__':main()
