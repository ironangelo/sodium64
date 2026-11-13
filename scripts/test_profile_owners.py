#!/usr/bin/env python3
"""Execute emitted profiling boot/ISR/terminal owners; no native timing model."""
import argparse,json
from pathlib import Path
from linked_cpu_regression import CPU,load_elf,sx32,RETURN

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path,nargs='+');p.add_argument('--normal-elf',type=Path,required=True)
    p.add_argument('--parent-normal-elf',type=Path);p.add_argument('--legacy-hw-elf',type=Path)
    p.add_argument('--json-output',type=Path);a=p.parse_args();normal,ns=load_elf(a.normal_elf)
    if a.parent_normal_elf:assert normal==load_elf(a.parent_normal_elf)[0]
    cases=0;variants=[]
    def fresh(memory):
        c=CPU(memory.copy());c.pattern();c.allow_rcp_writes=True;return c
    def boot(memory,s,size,complete=False):
        c=fresh(memory);c.write(0xa4000000,size);c.memory_writes=[]
        c.execute(s['main'],stop=s['pi_wait1'] if complete else s['profile_upper_initialized'] if size==8388608 else s['profile_boot_ram_rejected'],max_steps=1000000)
        return c
    for path in a.elf:
        memory,s=load_elf(path);hw='hw_profile_header' in s
        arena=s.get('renderer_cgram_owner_begin',0xbe200)
        assert arena in (0xbe200,0xd2000), 'unqualified CGRAM owner'
        assert s['__bss_end']<=0x80000000+arena and max(memory)<arena
        assert not any(0x400000<=at<0x800000 for at in memory)
        for size in (0,4194304,8388607,8388609,0xffffffff,8388608):
            c=boot(memory,s,size)
            writes=[(at,n,v)for at,n,v in c.memory_writes if 0x400000<=at<0x800000]
            if size!=8388608:assert not writes and not c.cache_ops
            else:
                assert len(c.cache_ops)==1280
                assert writes and all(0x448000<=at and at+n<=0x44d000 for at,n,v in writes)
                assert c.read(s['profile_magic'])==0x53363450 and c.read(s['profile_capacity'])==4096
                assert c.read(s['profile_write_ptr'])==s['profile_sample_buffer']
                assert all(c.read(at+i*4)==0x50363447 for at in (0xa0448000,0xa044cfe0) for i in range(8))
                if hw:assert c.read(s['hw_profile_header']+4)==2
            cases+=1
        # Run the real base-arena clear, then verify every embedded RSP bank is
        # intact. The old linked HW build is an actual failing counterexample.
        c=boot(memory,s,8388608,complete=True)
        bank_sections=sorted(name for name in s if name.startswith('rsp_') and
                             name.endswith(('_text_start','_data_start')))
        assert bank_sections, 'no embedded renderer sections checked'
        for symbol in bank_sections:
            end=symbol[:-6]+'_end'
            size=s[end]-s[symbol]
            assert 0<size<=4096 and ns[end]-ns[symbol]==size
            assert c.blob(s[symbol],size)==bytes(normal[(ns[symbol]+i)&0x1fffffff] for i in range(size))
            cases+=1
        c.pattern();c.cp[9]=100;c.cp[12]=0x403;c.write(0xa8000000,0x53363448)
        c.execute(s['profile_init'])
        assert c.read(s['profile_sample_count'])==0
        if hw:
            assert c.read(0xa8000000)==0 and c.read(s['apu_clock'],1)==21 and c.read(s['underclk_set'],1)==0
        for wrap in (False,True):
            c.pattern();original=c.regs.copy();hi,lo=c.hi,c.lo;c.cp[14]=RETURN;c.cp[12]=0x403
            c.write(s['profile_write_ptr'],s['profile_sample_buffer_end']-4 if wrap else s['profile_sample_buffer'])
            c.write(s['profile_sample_count'],123);c.write(s['fps_native'],0,1)
            at=c.read(s['profile_write_ptr']);c.execute(s['profile_interrupt'])
            assert c.read(at)==RETURN and c.read(s['profile_sample_count'])==124
            assert c.read(s['profile_write_ptr'])==(s['profile_sample_buffer'] if wrap else at+4)
            assert all(c.regs[i]==original[i] for i in range(32) if i not in (26,27))
            assert c.hi==hi and c.lo==lo
            cases+=1
        if hw:
            valid=boot(memory,s,8388608);valid.pattern();valid.cp[9]=100
            valid.execute(s['profile_init']);valid.write(s['profile_sample_count'],1200)
            valid.execute(s['hw_profile_finalize'],stop=s['hw_profile_done'],max_steps=500000)
            assert valid.read(s['hw_profile_hdr_complete'])==1 and valid.read(s['hw_profile_hdr_guards_ok'])==1
            from hw_profile_report import parse_capture
            header=valid.blob(s['hw_profile_header'],128);snapshot=valid.blob(s['profile_magic'],16416)
            capture,_=parse_capture(header+bytes(128)+snapshot,expected_warmup_seconds=int.from_bytes(header[8:12],'big'))
            assert capture.version==2 and capture.sample_count==1200
            cases+=1
            for address in (0xa0448000,0xa044cfe0):
                broken=boot(memory,s,8388608);broken.write(address,0);broken.write(0xa8000000,0)
                broken.execute(s['hw_profile_finalize'],stop=s['hw_profile_guard_failed'])
                assert broken.read(s['hw_profile_hdr_complete'])==0 and broken.read(0xa8000000)==0
                cases+=1
        variants.append({'hw':hw,'static_end':hex(s['__bss_end']),
                         'first_CGRAM_owner':hex(arena),'embedded_sections_checked':len(bank_sections),
                         'upper_lease':[0x448000,0x44d000]})
    legacy=None
    if a.legacy_hw_elf:
        old,os=load_elf(a.legacy_hw_elf);c=fresh(old)
        c.execute(os['main'],stop=os['pi_wait1'],max_steps=1000000)
        damaged={}
        for name in ('rsp_mode7_text_start','rsp_mode7_data_start'):
            before=bytes(old[(os[name]+i)&0x1fffffff] for i in range(4096))
            damaged[name]=sum(x!=y for x,y in zip(before,c.blob(os[name],4096)))
        assert all(damaged.values());legacy={'static_end':hex(os['__bss_end']),'damaged_nonzero_bytes':damaged}
    proof={'passed':True,'linked_cases':cases,'normal_loaded_image_identical':bool(a.parent_normal_elf),
           'unknown_and_4MiB_rejected_before_upper_or_VI':True,'all_rsp_banks_survive_actual_boot_clear':True,
           'both_guards_fail_closed':True,'variants':variants,'legacy_actual_linked_counterexample':legacy,
           'physical_acceptance':False}
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
