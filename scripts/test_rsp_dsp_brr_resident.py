#!/usr/bin/env python3
"""Bounded raw-job DMA adapter against the unchanged R58 BRR arithmetic."""
import argparse,hashlib,json,random,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_rsp_dsp_brr import CONSTANTS,oracle
from test_scene_rsp_context import execute,state

class DMAStalled(Exception):pass

class ResidentDMA:
    """Only the declared128-byte read and64-byte private write, no bus timing."""
    def __init__(self,d,memory,*,read_fault=False,output_fault=False,stalled=None,on_transfer=None):
        assert len(memory)==192
        self.d=d;self.memory=memory;self.pending=[0,0];self.current=[0,0,0xff8,0xff8]
        self.active=None;self.delay=0;self.trace=[];self.read_fault=read_fault
        self.output_fault=output_fault;self.stalled=stalled;self.on_transfer=on_transfer

    def control(self,write,rd,value):
        if not write:
            assert rd==6
            if not self.active:return 0
            if self.stalled==self.active[0]:raise DMAStalled(self.stalled)
            if self.delay:self.delay-=1;return 1
            kind,sp,dram,length=self.active
            if kind=='input':
                self.d[sp:sp+length]=self.memory[:128]
                if self.read_fault:self.d[sp+3]^=0x80
            else:
                if self.output_fault:self.d[sp]^=1
                self.memory[128:]=self.d[sp:sp+length]
            self.current[:]=[sp+length,dram+length,0xff8,0xff8]
            self.trace.append((kind,sp,dram,length));self.active=None
            if self.on_transfer:self.on_transfer(kind,self.current,self.memory)
            return 0
        if rd in (0,1):self.pending[rd]=value;return 0
        assert rd in (2,3) and self.active is None,'DMA overlap or unrelated RCP write'
        sp,dram=self.pending
        expected=(0x180,0x10000,127) if rd==2 else (0x120,0x10080,63)
        assert (sp,dram,value)==expected,('DMA ownership escaped',sp,dram,value)
        assert len(self.trace)==(0 if rd==2 else 1),'missing input wait or duplicate transfer'
        self.active=('input' if rd==2 else 'output',sp,dram,value+1);self.delay=3
        return 0

def packet(code,cases,seed):
    d=bytearray((i*31+97)&255 for i in range(4096))
    for i,value in enumerate(CONSTANTS):struct.pack_into('>8H',d,96+i*16,*([value]*8))
    for shift in range(16):struct.pack_into('>I',d,0x240+4*shift,((1<<(shift+3))<<16)|1 if shift<=12 else 0x10800)
    struct.pack_into('>I',d,0x200,0x10000)
    source=b''.join(struct.pack('>4I',word,header,p1&0xffffffff,p2&0xffffffff) for word,header,p1,p2 in cases)
    memory=bytearray(source+bytes([0x55])*64);before=bytes(d)
    dma=ResidentDMA(d,memory);steps=execute(code,d,*state(seed),rcp=dma.control)
    assert not dma.active and dma.trace==[('input',0x180,0x10000,128),('output',0x120,0x10080,64)]
    assert memory[:128]==source
    expected=[oracle(word&65535,header,p1,p2) for word,header,p1,p2 in cases]
    output=struct.pack('>32H',*(expected[lane][n]&65535 for n in range(4) for lane in range(8)))
    assert memory[128:]==output
    for first,last in ((0x60,0x120),(0x160,0x180),(0x200,4096)):
        assert d[first:last]==before[first:last],('DMEM owner escaped',first,last)
    return steps

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    _,code=read_text(a.elf);_,baseline=read_text(a.baseline)
    assert len(code)==1028 and len(baseline)==444
    assert code[137*4:247*4]==baseline[:-4],'R58 arithmetic body changed'
    edges=(-32768,-32767,-1,0,1,32766,32767);counts=set();packets=0
    for shift in range(16):
        for kind in range(4):
            for rotation in range(7):
                cases=[(((lane*15583+rotation*29519)&65535)|((0x6000+lane)<<16),
                    (shift<<4)|(kind<<2)|lane%4,edges[(lane+rotation)%7],edges[(lane*3+rotation)%7]) for lane in range(8)]
                counts.add(packet(code,cases,packets));packets+=1
    rng=random.Random(0x60b44);negative=[]
    for n in range(1024):
        cases=[(rng.getrandbits(32),rng.randrange(256),rng.randrange(-32768,32768),rng.randrange(-32768,32768)) for _ in range(8)]
        if n<32:negative.append(cases)
        counts.add(packet(code,cases,packets));packets+=1
    words=list(struct.unpack('>257I',code));faults=[]
    mutants=[('wrong_job_history',11,lambda w:w+4),('wrong_range_table',18,lambda w:w+4),
        ('missing_input_wait',7,lambda w:0),('wrong_input_extent',4,lambda w:(w&~65535)|135),
        ('wrong_output_address',248,lambda w:(w&~65535)|136),('missing_output_wait',254,lambda w:0)]
    for name,index,mutate in mutants:
        changed=words.copy();changed[index]=mutate(changed[index]);binary=struct.pack('>257I',*changed)
        for cases in negative:
            try:packet(binary,cases,999)
            except (AssertionError,DMAStalled):faults.append(name);break
        else:raise AssertionError('escaped mutation '+name)
    assert counts=={275}
    proof=dict(passed=True,linked_kernel_bytes=1028,minimum_program_instructions=257,
        delayed_DMA_model_instructions=275,packets=packets,original_samples=packets*32,
        original_R58_110_instruction_body_byte_exact=True,all16_ranges_all4_filters_signed_odd_histories=True,
        raw32bit_word_upper_bits_ignored=True,input128_readonly_output64_only=True,
        DMEM_plane96_output64_raw128_owners_only=True,input_output_waits_required=True,
        negative_mutations_rejected=faults,kernel_sha256=hashlib.sha256(code).hexdigest(),
        primary_reference='ares9408cb43d4948fc3ea6e152a307a34348df3fe04 RSP IPU/SCC/io',
        hardware_timing_cache_and_bus_mocked=True,native_acceptance=False,commercial_data=False)
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))
if __name__=='__main__':main()
