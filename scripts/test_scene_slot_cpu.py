#!/usr/bin/env python3
"""Actual linked indexed TLB snapshot/restore and complete cache sweeps."""
import argparse,json,random
from pathlib import Path
from test_native_diag_continuous import CPU,load_elf,sx32
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args();base,s=load_elf(a.elf);cases=0
    for seed in range(64):
        rng=random.Random(seed);cpu=CPU(base.copy());cpu.pattern(seed)
        cpu.cp.update({i:rng.getrandbits(32) for i in (0,10,2,3,5)});cpu.cp[0]&=31
        cpu.tlb=[(rng.getrandbits(32)&0xffffe0ff,rng.getrandbits(30),rng.getrandbits(30),rng.choice((0,0x6000,0x1e000))) for _ in range(32)]
        current_cp=cpu.cp.copy();original=cpu.tlb.copy();hi,lo=cpu.hi,cpu.lo;preserved=cpu.regs.copy()
        cpu.regs[4]=sx32(0x800db000)
        assert cpu.execute(s['scene_slot_tlb_save'])=='return'
        assert cpu.cp==current_cp and cpu.tlb==original and (cpu.hi,cpu.lo)==(hi,lo)
        assert all(cpu.regs[i]==preserved[i] for i in range(16,32))
        saved=cpu.blob(0x800db000,532)
        assert saved[:20]==b''.join(current_cp[i].to_bytes(4,'big') for i in (0,10,2,3,5))
        assert saved[20:]==b''.join(v.to_bytes(4,'big') for entry in original for v in entry)
        cpu.tlb=[(0,0,0,0)]*32;cpu.cp.update({i:0 for i in (0,10,2,3,5)})
        assert cpu.execute(s['scene_slot_tlb_load'])=='return'
        assert cpu.tlb==original and cpu.cp==current_cp and (cpu.hi,cpu.lo)==(hi,lo)
        assert all(cpu.regs[i]==preserved[i] for i in range(16,32))
        assert cpu.execute(s['scene_slot_cache_sync'])=='return'
        assert cpu.cache_ops==[(1,0x80000000+16*i) for i in range(512)]+[(0,0x80000000+32*i) for i in range(512)]
        cases+=1
    result=dict(passed=True,cases=cases,actual_linked_MIPS=True,indexed_32_entries_restored=True,
        current_CP0_fields_preserved_on_save=True,callee_GPR64_HILO_preserved=True,
        full_D_writeback_invalidate_I_invalidate=True,hardware_hazards_mocked=True,native_acceptance=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
