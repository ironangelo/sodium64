#!/usr/bin/env python3
"""Execute the compiled sender against asynchronous command/source readers.

This catches premature DMEM reuse that synchronous ares DMA cannot expose.
Exercise transient DMA-idle gaps and a stale CURRENT matching a repeated END.
Pointer retirement follows the RCP command FIFO protocol in:
https://hcs64.com/files/RSPCOP0.pdf (Controlling the RDP).
The model checks the ownership protocol, not real-N64 timing or crash causality.
"""
import argparse
import struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text

EXIT=0x12345678

class DelayedDPC:
    def __init__(self,dmem,latency,busy,mode='continuous'):
        self.dmem=dmem;self.latency=latency;self.busy=busy
        self.mode=mode;self.latch=0;self.queued_start=None
        self.start=None;self.end=None;self.delay=0;self.pos=None;self.captured=bytearray()
        self.start_writes=0
    def status(self):
        pending=self.pos is not None and self.pos<self.end
        # Between DMA reads, neither a pending pointer nor an active burst
        # need be reported. The lease still lasts until CURRENT reaches END.
        dma=0x700 if self.mode=='continuous' and pending else (0x100 if pending and not self.delay else 0)
        return 0x81|(0x40 if self.busy else 0)|dma|(0x600 if self.latch else 0)
    def read(self,reg):
        if reg==10:return self.pos or 0
        assert reg==11
        return self.status()
    def write(self,reg,value):
        if reg==8:
            assert not self.latch,'pending START overwritten'
            assert self.pos is None or self.pos==self.end,'unfinished list replaced'
            self.start=value;self.start_writes+=1
        elif reg==9:
            self.end=value;self.delay=self.latency
            if self.mode=='stale-end':
                # Repeat a packet with the same END. CURRENT is initially
                # the old END until the double-buffered START is adopted.
                self.pos=value;self.queued_start=self.start;self.latch=20
            else:self.pos=self.start
        else:raise AssertionError(('unexpected DPC write',reg))
    def tick(self):
        if self.busy:self.busy-=1
        if self.latch:
            self.latch-=1
            if not self.latch:self.pos=self.queued_start
            return
        if self.pos is None or self.pos==self.end:return
        if self.delay:self.delay-=1;return
        self.captured.extend(self.dmem[self.pos:self.pos+8]);self.pos+=8
        self.delay=self.latency


def execute(text,dpc,start,end,entry=0xf5c,size=0):
    r=[0]*32;r[4]=start;r[5]=end;r[6]=size;r[31]=EXIT
    pc=entry;pending=None
    for cycles in range(10000):
        if pc==EXIT:return cycles,r
        w=struct.unpack_from('>I',text,pc)[0]
        op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31;rd=(w>>11)&31;imm=w&0xffff
        branch=None
        if w==0:pass
        elif op==0x10:
            if rs==0:r[rt]=dpc.read(rd)
            elif rs==4:dpc.write(rd,r[rt])
            else:raise AssertionError(hex(w))
        elif op==0xc:r[rt]=r[rs]&imm
        elif op in (8,9):r[rt]=(r[rs]+(imm if imm<0x8000 else imm-0x10000))&0xffffffff
        elif op in (4,5):
            take=(r[rs]==r[rt]) if op==4 else (r[rs]!=r[rt])
            if take:branch=pc+4+((imm if imm<0x8000 else imm-0x10000)<<2)
        elif op==0 and w&63==8:branch=r[rs]
        else:raise AssertionError(('unexpected instruction',hex(pc),hex(w)))
        assert pending is None or branch is None,'control instruction in delay slot'
        pc=pending if pending is not None else pc+4;pending=branch
        r[0]=0;dpc.tick()
    raise AssertionError('sender did not return')


class TextureDPC:
    """A texture load retains its RDRAM source after command fetch completes."""
    def __init__(self,latency,flag,source=0,target=0xa0200000):
        self.left=latency;self.flag=flag;self.fence=False;self.done=False
        self.source=source;self.expected_target=target
        self.ram=bytearray(range(64));self.original=bytes(self.ram)
        self.captured=None;self.sp=None;self.target=None;self.dma_writes=0
    def read(self,reg):
        if reg==6:return 0
        assert reg==11
        return 0x81|(self.flag if not self.done else 0)|(0x700 if self.fence and not self.done else 0)
    def write(self,reg,value):
        if reg==8:assert value==0xf20
        elif reg==9:
            assert value==0xf28
            self.fence=True
        elif reg==0:self.sp=value
        elif reg==1:self.target=value
        elif reg==3:
            assert value==63 and self.sp==self.source and self.target==self.expected_target
            if self.expected_target==0xa0200000:
                assert self.done,'cached texture overwritten while LoadBlock retained it'
                self.ram[:]=bytes([0xee])*64
            self.dma_writes+=1
        else:raise AssertionError(reg)
    def tick(self):
        if self.done:return
        if self.left:self.left-=1
        elif self.fence:
            self.captured=bytes(self.ram);self.done=True


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('elves',nargs=2,type=Path);args=ap.parse_args()
    texts=[read_text(p)[1] for p in args.elves]
    assert all(len(t)==4096 for t in texts)
    assert texts[0][0x2cc:0x33c]==texts[1][0x2cc:0x33c],'resident ownership/retirement helper differs'
    assert texts[0][0x2cc:0x2d0]==bytes(4),'CGRAM branch delay slot submits a spurious DP_START'
    assert texts[0][0xf08:0xfa8]==texts[1][0xf08:0xfa8],'resident DMA/loader differs'
    cases=0
    for text in texts:
        for latency in (0,1,7,100):
            for busy in (0,5,20):
                for size in (8,16,40,64):
                    for mode in ('continuous','dma-gap','stale-end'):
                        memory=bytearray(4096);start=0xc98;end=start+size
                        original=bytes((i*17+3)&255 for i in range(size));memory[start:end]=original
                        dpc=DelayedDPC(memory,latency,busy,mode)
                        _,r=execute(text,dpc,start,end)
                        assert dpc.start_writes==1
                        assert dpc.pos==end and not dpc.latch,'sender returned before its DMEM lease ended'
                        memory[start:end]=bytes([0xe7])*size
                        for _ in range(500):dpc.tick()
                        assert dpc.captured==original,'caller mutations changed a submitted list'
                        assert r[4]==start and r[5]==end and r[31]==EXIT
                        cases+=1
    texture_cases=0
    palette_cases=0;independent_cases=0
    for text in texts:
        for latency in (0,1,7,100):
            for flag in (0x10,0x20,0x40):
                dpc=TextureDPC(latency,flag)
                _,r=execute(text,dpc,0,0xa0200000,entry=0xf08,size=63)
                assert dpc.captured==dpc.original and dpc.dma_writes==1
                assert (r[4],r[5],r[6],r[31])==(0,0xa0200000,63,EXIT)
                texture_cases+=1
                # The palette replay path calls the same source fence
                # explicitly, bypassing the generic source-address filter.
                dpc=TextureDPC(latency,flag,source=0xeb0)
                _,r=execute(text,dpc,0xeb0,0xa0200000,entry=0x2fc,size=63)
                assert dpc.captured==dpc.original and dpc.dma_writes==1
                assert (r[4],r[5],r[6],r[31])==(0xeb0,0xa0200000,63,EXIT)
                palette_cases+=1
                for source in (0x40,0xc00,0xc80):
                    dpc=TextureDPC(latency,flag,source=source,target=0xa00e6000)
                    _,r=execute(text,dpc,source,0xa00e6000,entry=0xf08,size=63)
                    assert dpc.dma_writes==1 and not dpc.fence,'independent DMA serialized against RDP'
                    assert dpc.ram==dpc.original
                    assert (r[4],r[5],r[6],r[31])==(source,0xa00e6000,63,EXIT)
                    independent_cases+=1
    print(f'RDP_LIFETIME PASS command_cases={cases} texture_cases={texture_cases} palette_cases={palette_cases} independent_dma_cases={independent_cases} native_cadence_authority=false')

if __name__=='__main__':main()
