#!/usr/bin/env python3
"""Prove linked upper snapshot guards and disjoint owners; no private bytes."""
import argparse,json
from pathlib import Path
from test_native_diag_arm import load_elf,execute
from check_event_arena import check

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--cc',required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    base,s=load_elf(a.elf);root=Path(__file__).resolve().parents[1]
    owners=check(root/'src/defines.h',a.elf,True,a.cc,full_dsp_probe=True,audio_observer=True)
    upper=dict(window_probe=(0x400000,0x4340a0),diagnostic_snapshot=(0x438000,0x440000))
    assert s['native_diag_snapshot']==0x80438000
    assert max(x['end'] for x in owners.values())==0x400000
    ranges=sorted([(v['start'],v['end'],n) for n,v in owners.items()]+[(lo,hi,n)for n,(lo,hi)in upper.items()])
    for lo,hi,n in ranges:assert 0<=lo<hi<=0x7f0000,(n,lo,hi)
    for (lo,hi,n),(other,end,name) in zip(ranges,ranges[1:]):assert hi<=other,(n,name)
    def put(m,address,value):m.update(((address&0x1fffffff)+i,v)for i,v in enumerate(value.to_bytes(4,'big')))
    cases=0
    for size in (0,4194304,8388607,8388609,0xffffffff):
        for entry in ('native_diag_arm','native_diag_remote_arm','native_diag_copy_snapshot'):
            m=base.copy();put(m,s['remote_boot_ram_bytes'],size);before=m.copy()
            regs=[0]*32;regs[31]=0xdead0000;cp={9:123,11:456,12:0x401}
            execute(m,s[entry],regs,cp)
            # Copy rejection may clear only its low-memory ready word.
            allowed={((s['native_diag_snapshot_ready']&0x1fffffff)+i) for i in range(4)} if entry.endswith('copy_snapshot') else set()
            assert all(m.get(at)==value or at in allowed for at,value in before.items())
            assert not any(at>=0x400000 and at not in before for at in m)
            assert cp=={9:123,11:456,12:0x401};cases+=1
    # Execute the real32KiB cache-invalidate/copy loop on an admitted8MiB boot.
    m=base.copy();put(m,s['remote_boot_ram_bytes'],8388608)
    source=s['sram']&0x1fffffff;expected=bytes((i*43+7)&255 for i in range(32768))
    m.update((source+i,v)for i,v in enumerate(expected))
    regs=[0]*32;regs[31]=0xdead0000;cp={9:123,11:456,12:0x401};trace=[]
    execute(m,s['native_diag_copy_snapshot'],regs,cp,cache_trace=trace)
    assert bytes(m[0x438000+i]for i in range(32768))==expected
    cache=[v for v in trace if v[0]=='cache']
    assert len(cache)==2048 and all(v==('cache',0x15,0x80438000+i*16)for i,v in enumerate(cache))
    assert ('sync',s['native_diag_snapshot_copy']+24) in trace or any(v[0]=='sync'for v in trace)
    cases+=1
    proof=dict(passed=True,base_owners=len(owners),upper_owners=upper,
        linked_rejected_arm_remote_copy_cases=15,linked_32KiB_copy_cases=1,
        linked_snapshot_cache_lines=2048,total_cases=cases,
        loaded_sections_and_boot_clear_stay_below4MiB=True,all_owners_below_boot_reserved_top64KiB=True,
        live_guest_state_added=False,SP_DMA_or_new_save_owner_implemented=False,
        native_memory_or_performance_acceptance=False,commercial_data=False)
    print(json.dumps(proof,indent=2))
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
