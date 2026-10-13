#!/usr/bin/env python3
"""Actual linked post-submit continuation and O64 bridge; synthetic owners only."""
import argparse
import json
from pathlib import Path
from test_native_diag_continuous import CPU, load_elf, RETURN, sx32
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros


def run(base,s,*,queue=0,status=0x401,pending=1,fault=None):
    m=base.copy();cpu=CPU(m);cpu.pattern(0x5341);cpu.allow_rcp_writes=True
    cpu.regs[12]=sx32(RETURN);cpu.regs[13]=queue;cpu.regs[4]=225
    cpu.cp.update({12:status,14:0x80123456})
    addr=parse_macros(Path(__file__).resolve().parents[1]).name
    fb=addr('FRAMEBUFFER1');cpu.write(0xa4000000+addr('FRAMEBUFFER')+queue,fb)
    cpu.write(s['remote_scene_pending'],pending);cpu.write(s['remote_paused'],0)
    cpu.write(s['remote_arm_pending'],0);cpu.write(s['remote_guest_frames'],20);cpu.write(s['remote_render_frames'],20)
    if fault=='missing_submit':cpu.write(s['scene_state_submit_hook']+8,0)
    elif fault=='wrong_bridge_kind':cpu.write(s['remote_scene_bridge'],0x241b0001)
    original=cpu.regs.copy();old_hi,old_lo,old_epc=cpu.hi,cpu.lo,cpu.cp[14]
    calls=[]
    def parked(c):
        assert c.read(0xa4040010)==1,'park entered without submitted frame'
        assert c.regs[4]&0xffffffff==fb and c.regs[29]&15==0 and c.regs[29]!=queue
        calls.append('parked')
        for i in range(1,32):c.regs[i]=0xfedcba0000000000+i
        c.hi=0x1234;c.lo=0x5678;c.cp[14]=0x800dead0
        c.write(s['remote_scene_pending'],0);c.write(s['remote_paused'],1)
    def idle(c):
        calls.append('idle');c.write(s['remote_paused'],0)
        for i in range(1,32):c.regs[i]=0xbadc0f0000000000+i
    def incorrect_frame(c):raise AssertionError('canonical park invoked normal frame counter hook')
    cpu.hooks[s['remote_scene_parked']]=parked
    cpu.hooks[s['remote_control_idle']]=idle
    cpu.hooks[s['remote_control_frame']]=incorrect_frame
    assert cpu.execute(s['scene_state_submit_hook'])=='return'
    assert calls==(['parked','idle'] if pending else [])
    assert cpu.read(s['remote_guest_frames'])==cpu.read(s['remote_render_frames'])==20
    assert all(cpu.regs[i]==original[i] for i in range(32) if i not in (1,4,8,9,26,27,31)), 'guest/queue/continuation changed'
    assert (cpu.hi,cpu.lo,cpu.cp[14],cpu.cp[12])==(old_hi,old_lo,old_epc,status)
    rcp=[(a,n,v) for a,n,v in cpu.memory_writes if 0x04000000<=a<0x05000000]
    assert rcp[-1]==(0x04040010,4,1) and len([x for x in rcp if x[0]==0x04040010])==1,'forced halt or duplicate submit'


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args();base,s=load_elf(a.elf);cases=0
    for queue in (0,4):
        for status in (0x401,0x403,0x9401,0x9403):
            for pending in (0,1):run(base,s,queue=queue,status=status,pending=pending);cases+=1
    rejected=[]
    for fault in ('missing_submit','wrong_bridge_kind'):
        try:run(base,s,fault=fault)
        except AssertionError:rejected.append(fault)
        else:raise AssertionError('escaped actual boundary mutation: '+fault)
    result=dict(passed=True,actual_linked_cases=cases,mutations_rejected=rejected,
                architectural_GPR64_HI_LO_EPC_Status_preserved=True,normal_frame_counters_unchanged=True,
                natural_submit_only=True,RCP_timing_mocked=True,native_acceptance=False,serializer=False,restore=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
