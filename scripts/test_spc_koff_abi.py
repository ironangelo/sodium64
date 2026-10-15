#!/usr/bin/env python3
"""Execute real SPC code and the real KOFF release handler; no game inputs."""
import argparse,hashlib,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run
from test_native_diag_continuous import signed
from check_full_dsp_window_build import sections

def setup(c,s):
    c.write(s['enabled'],255,1);c.write(s['dsp_timer'],0x1234,2)
    for v in range(8):
        c.write(s['mode_funcs']+16*v,0x11223344+4*v)
        c.write(s['next_steps']+16*v,0x300+v,2)
        c.write(s['envelopes']+16*v,0x400+v,2)
def observe(c,s):
    return dict(enabled=c.read(s['enabled'],1),voices=[
        [c.read(s['mode_funcs']+16*v),c.read(s['next_steps']+16*v,2),c.read(s['envelopes']+16*v,2)]for v in range(8)])
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--require-exact',action='store_true')
    p.add_argument('--baseline',type=Path)
    a=p.parse_args();base,s=load_elf(a.elf);assert 'release_mode'in s;results=[]
    for accum in (0x11,0x80,255):
        for mask in (0,1,0x80,0x55,255):
            for source in ('immediate','X'):
                code=bytes([0xe8,accum,0x8f,mask,0xf3,0xc4,0x20,0x2f,0xf7]) if source=='immediate' else bytes([0xe8,accum,0xcd,mask,0xd8,0xf3,0xc4,0x20,0x2f,0xf6])
                r=run(base,s,code,observe_data=True,memory_values=((0x20,0xee),),dsp_address=0x5c,extra_setup=setup,extra_outcome=observe)
                expected=[[s['release_mode'] if mask>>v&1 else 0x11223344+4*v,
                           0x1233 if mask>>v&1 else 0x300+v,0x400+v]for v in range(8)]
                assert r['outcome']['extra']==dict(enabled=255,voices=expected),'release voice side effect changed'
                assert r['total_cycles']==(15 if source=='immediate' else 16)
                preserved=r['outcome']['registers']['apu_accum']==accum and r['outcome']['memory']['0x20']==accum
                assert r['outcome']['registers']['apu_reg_x']==(4 if source=='immediate' else mask)
                assert r['outcome']['registers']['apu_reg_y']==6 and r['outcome']['registers']['apu_stack']==0x7f
                item=dict(A=accum,mask=mask,source=source,A_after=r['outcome']['registers']['apu_accum'],stored_A=r['outcome']['memory']['0x20'],guest_preserved=preserved,voice_side_effects_exact=True)
                results.append(item)
                if a.require_exact:assert preserved,item
    failures=sum(not x['guest_preserved']for x in results)
    if not a.require_exact:assert failures>0,'baseline unexpectedly preserves every case'
    handlers=[];changed_words=None
    if a.require_exact:
        def word(at):return int.from_bytes(bytes(base[(at+i)&0x1fffffff]for i in range(4)),'big')
        entry=s['write_dspdata'];hi=word(entry+32);lo=word(entry+40)
        assert hi>>16==0x3c01 and lo>>16==0x8c29
        table=((hi&65535)<<16)+signed(lo&65535,16)
        assert word(table+0x5c*4)==s['write_koff']
        unique={}
        for reg in range(128):unique.setdefault(word(table+reg*4),reg)
        for handler,reg in unique.items():
            r=run(base,s,bytes.fromhex('e8118f01f3c4202ff7'),observe_data=True,memory_values=((0x20,0xee),),dsp_address=reg)
            assert r['outcome']['registers']['apu_accum']==r['outcome']['memory']['0x20']==17
            assert r['outcome']['registers']['apu_reg_x']==4 and r['outcome']['registers']['apu_reg_y']==6
            handlers.append(dict(register=reg,handler=hex(handler),A_X_Y_preserved=True))
        if a.baseline:
            before=sections(a.baseline);after=sections(a.elf)
            assert before['.data']==after['.data']
            x,y=before['.text'][3],after['.text'][3];assert len(x)==len(y)
            changed_words=sum(x[i:i+4]!=y[i:i+4]for i in range(0,len(x),4));assert changed_words==2
    proof=dict(passed=True,status='IMPLEMENTED KOFF guest preservation'if a.require_exact else'REJECTED KOFF clobbers live SPC accumulator',
        cases=results,case_count=len(results),guest_preservation_failures=failures,
        real_linked_JIT_and_release_handler=True,all_voice_masks_deadlines_envelopes_exact=True,
        all_total_cycles_and_cached_outcomes_exact=True,ELF_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest(),
        distinct_DSP_write_handlers=handlers,changed_text_words_vs_baseline=changed_words,
        native_hardware_gameplay_DAC_acceptance=False,commercial_data=False)
    print('SPC_KOFF_ABI cases='+str(len(results))+' A_preservation_failures='+str(failures)+' release_side_effects=exact')
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
