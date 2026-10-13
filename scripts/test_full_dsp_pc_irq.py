#!/usr/bin/env python3
"""Execute actual scoped sampler, checking ring, CP0 ownership and GPR64 ABI."""
import argparse,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--json-output',type=Path);a=p.parse_args()
    memory,s=load_elf(a.elf);c=CPU(memory)
    ring=0xa0200000;next_out=0x80201000;ret=0x90000400
    active=s['full_dsp_profile_active'];base=s['full_dsp_profile_base']
    write=s['full_dsp_profile_write'];samples=s['full_dsp_profile_samples']
    def call(name):
        c.regs[31]=ret
        assert c.execute(s[name],stop=ret,max_steps=250)=='return'
    accepted=denied=interrupts=0
    for status in (0x400,0x401,0x20000400,0x24000401):
        for start in (0,0xfffffff0):
            c.pattern();c.cp.update({9:start,11:123456,12:status,13:0})
            c.write(active,0);c.regs[4]=ring
            before=c.regs.copy();hi,lo=c.hi,c.lo
            call('full_dsp_profile_begin')
            assert c.regs[2]==1 and c.read(active)==1
            assert c.read(base)==c.read(write)==ring and c.read(samples)==0
            assert c.cp[12]==((status&~0xff00)|0x8001)
            assert c.cp[11]==(start+65521)&0xffffffff
            assert all(c.regs[i]==before[i] for i in range(32) if i not in {1,2,8,9,10,31})
            assert (hi,lo)==(c.hi,c.lo)
            for index,total in ((0,0),(126,126),(127,127),(127,0xffffffff)):
                c.pattern();c.cp.update({9:start,14:0x80015004})
                c.write(write,ring+index*4);c.write(samples,total)
                before=c.regs.copy();hi,lo=c.hi,c.lo
                c.memory_writes.clear();c.cp_writes.clear()
                assert c.execute(s['full_dsp_profile_interrupt'])=='eret'
                assert c.read(ring+index*4)==0x80015004
                assert c.read(write)==ring+((index+1)&127)*4
                assert c.read(samples)==(total+1)&0xffffffff
                assert c.cp_writes==[(11,(start+65521)&0xffffffff)]
                assert all(c.regs[i]==before[i] for i in range(32) if i not in (26,27))
                assert (hi,lo)==(c.hi,c.lo)
                owned={(ring+index*4+i)&0x1fffffff for i in range(4)}
                for addr in (write,samples):owned.update((addr+i)&0x1fffffff for i in range(4))
                touched={addr+i for addr,n,_ in c.memory_writes for i in range(n)}
                assert touched==owned
                interrupts+=1
            # The existing native dispatcher must route the owned synthetic
            # timer without touching its ordinary flight-recorder state.
            c.pattern();c.cp.update({9:start,14:0x80015008})
            c.write(write,ring);c.write(samples,0)
            before=[c.read(s['native_diag_state']+i*4) for i in range(80)]
            assert c.execute(s['native_diag_interrupt'])=='eret'
            assert c.read(ring)==0x80015008 and c.read(samples)==1
            assert [c.read(s['native_diag_state']+i*4) for i in range(80)]==before
            c.write(write,ring);c.write(samples,0)
            c.regs[4]=next_out;call('full_dsp_profile_end')
            assert c.regs[2]==0 and c.read(next_out)==0 and c.read(active)==0
            assert c.cp[11]==123456 and c.cp[12]==status
            accepted+=1
    for status in (0x8001,0x403,0x405,0x407):
        c.pattern();c.cp[12]=status;c.write(active,0);c.regs[4]=ring
        c.cp_writes.clear();c.memory_writes.clear();call('full_dsp_profile_begin')
        assert c.regs[2]==0 and not c.cp_writes and not c.memory_writes;denied+=1
    for ptr,already in ((0,0),(ring+1,0),(ring,1)):
        c.pattern();c.cp[12]=0x401;c.write(active,already);c.regs[4]=ptr
        c.cp_writes.clear();c.memory_writes.clear();call('full_dsp_profile_begin')
        assert c.regs[2]==0 and not c.cp_writes and not c.memory_writes;denied+=1
    proof=dict(passed=True,accepted_begin_end_cases=accepted,denied_without_side_effects=denied,
               actual_IRQ_cases=interrupts,GPR64_HI_LO_preserved=True,
               only_ring_slot_and_metadata_written=True,Count_monotonic_Compare_Status_restored=True,
               masked_pending_IP7_acknowledgement_not_an_exact_Cause_restore=True,
               native_profile_or_gameplay_claim=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))
if __name__=='__main__':main()
