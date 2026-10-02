#!/usr/bin/env python3
"""Execute the compiled sender against delayed command fetches.

This catches premature DMEM reuse that synchronous ares DMA cannot expose.
The model checks the ownership protocol, not real-N64 timing or crash causality.
"""
import argparse
import struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text

EXIT=0x12345678

class DelayedDPC:
    def __init__(self,dmem,latency,busy):
        self.dmem=dmem;self.latency=latency;self.busy=busy
        self.start=None;self.end=None;self.delay=0;self.pos=None;self.captured=bytearray()
        self.start_writes=0
    def status(self):
        pending=self.pos is not None and self.pos<self.end
        return 0xa1|(0x40 if self.busy else 0)|(0x700 if pending else 0)
    def write(self,reg,value):
        if reg==8:
            assert self.busy==0,'START changed while prior commands were busy'
            assert self.pos is None or self.pos==self.end,'unfinished list replaced'
            self.start=value;self.start_writes+=1
        elif reg==9:
            self.end=value;self.pos=self.start;self.delay=self.latency
        else:raise AssertionError(('unexpected DPC write',reg))
    def tick(self):
        if self.busy:self.busy-=1
        if self.pos is None or self.pos==self.end:return
        if self.delay:self.delay-=1;return
        self.captured.extend(self.dmem[self.pos:self.pos+8]);self.pos+=8
        self.delay=self.latency


def execute(text,dpc,start,end):
    r=[0]*32;r[4]=start;r[5]=end;r[31]=EXIT
    pc=0xf5c;pending=None
    for cycles in range(10000):
        if pc==EXIT:return cycles,r
        w=struct.unpack_from('>I',text,pc)[0]
        op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31;rd=(w>>11)&31;imm=w&0xffff
        branch=None
        if w==0:pass
        elif op==0x10:
            if rs==0:r[rt]=dpc.status();assert rd==11
            elif rs==4:dpc.write(rd,r[rt])
            else:raise AssertionError(hex(w))
        elif op==0xc:r[rt]=r[rs]&imm
        elif op in (4,5):
            take=(r[rs]==r[rt]) if op==4 else (r[rs]!=r[rt])
            if take:branch=pc+4+((imm if imm<0x8000 else imm-0x10000)<<2)
        elif op==0 and w&63==8:branch=r[rs]
        else:raise AssertionError(('unexpected instruction',hex(pc),hex(w)))
        assert pending is None or branch is None,'control instruction in delay slot'
        pc=pending if pending is not None else pc+4;pending=branch
        r[0]=0;dpc.tick()
    raise AssertionError('sender did not return')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('elves',nargs=2,type=Path);args=ap.parse_args()
    texts=[read_text(p)[1] for p in args.elves]
    assert all(len(t)==4096 for t in texts)
    assert texts[0][0x2cc:0x2fc]==texts[1][0x2cc:0x2fc],'resident ownership helper differs'
    assert texts[0][0xf08:0xfa8]==texts[1][0xf08:0xfa8],'resident DMA/loader differs'
    cases=0
    for text in texts:
        for latency in (0,1,7,100):
            for busy in (0,5,20):
                for size in (8,16,40,64):
                    memory=bytearray(4096);start=0xc98;end=start+size
                    original=bytes((i*17+3)&255 for i in range(size));memory[start:end]=original
                    dpc=DelayedDPC(memory,latency,busy)
                    _,r=execute(text,dpc,start,end)
                    assert dpc.start_writes==1
                    assert dpc.pos==end,'sender returned before its DMEM lease ended'
                    memory[start:end]=bytes([0xe7])*size
                    for _ in range(500):dpc.tick()
                    assert dpc.captured==original,'caller mutations changed a submitted list'
                    assert r[4]==start and r[5]==end and r[31]==EXIT
                    cases+=1
    print(f'RDP_DMEM_LIFETIME PASS cases={cases} native_cadence_authority=false')

if __name__=='__main__':main()
