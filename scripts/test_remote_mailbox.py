#!/usr/bin/env python3
"""Execute the emitted fatal-mailbox code, including bounded PI backpressure."""
import argparse,json
from pathlib import Path
from linked_cpu_regression import CPU,load_elf,sx32

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--json-output',type=Path);a=p.parse_args();memory,s=load_elf(a.elf)
    class Device(CPU):
        def __init__(self):
            super().__init__(memory.copy());self.stall_after=None;self.pio=[]
        def read(self,address,size=4):
            at=address&0x1fffffff
            self.cp[9]=(self.cp.get(9,0)+1)&0xffffffff
            if at==0x4600010:
                if self.stall_after is not None and len(self.pio)>=self.stall_after:
                    self.cp[9]=(self.cp[9]+50000)&0xffffffff;return 1
                return 0
            return super().read(address,size)
        def write(self,address,value,size=4):
            at=address&0x1fffffff
            if 0x8000000<=at<0x8010000:
                assert not self.cp[12]&1 and size==4 and 0x8007f80<=at<0x8007fc0
                self.pio.append((at,value&0xffffffff))
            super().write(address,value,size)
    cases=0
    for phase in (1,3):
        for status in (0x403,0x401,0x400):
            for blocked in (None,0,5):
                c=Device();c.pattern();c.regs[29]=sx32(0x804411e0);c.regs[4]=phase
                c.cp[12]=status;c.cp[9]=0xfffffff0;c.stall_after=blocked
                c.write(s['remote_render_frames'],123)
                for offset,value in ((0,99),(3,7),(7,1),(10,0x53437632),(11,117),(12,0x80000000),(13,42)):
                    c.write(0x80441c60+offset*4,value)
                c.execute(s['mailbox_publish'],max_steps=3000)
                assert c.cp[12]==status
                if blocked is None:
                    words=[c.read(0xa8007f80+i*4) for i in range(16)]
                    assert words[:12]==[0x53363452,1,phase,1,7,0x53437632,123,99,117,0x80000000,42,0]
                    assert sum(words)&0xffffffff==0
                    assert c.pio[0]==(0x8007f80,0) and c.pio[-1]==(0x8007f80,0x53363452)
                    assert len(c.pio)==17
                elif blocked==0:assert not c.pio
                else:assert c.pio and c.read(0xa8007f80)==0 and len(c.pio)==5
                cases+=1
    proof={'passed':True,'linked_cases':cases,'original_numeric_inputs':True,
           'signature_committed_last':True,'partial_write_rejected':True,
           'single_bounded_PI_budget_wrap_safe':True,'IRQs_excluded_and_Status_restored':True,
           'physical_acceptance':False}
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
