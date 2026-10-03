#!/usr/bin/env python3
"""Execute v3 compiled IRQ-prefix and append helpers using original inputs."""
import argparse,json,struct
from pathlib import Path
from test_native_diag_arm import load_elf

def execute(memory,pc,regs,cp,stop=0xdead0000,terminal_rcp=False):
    pending=None
    def read(a,n):return int.from_bytes(bytes(memory.get((a+i)&0x1fffffff,0) for i in range(n)),'big')
    def write(a,v,n):
        if terminal_rcp and (a&0x1fffffff)==0x04040010 and v==2:
            v=1 # SET_HALT is acknowledged immediately by this test device.
        for i,c in enumerate((v&((1<<(n*8))-1)).to_bytes(n,'big')):memory[(a+i)&0x1fffffff]=c
    for step in range(2000):
        if pc==stop:return step
        w=read(pc,4);op=w>>26;rs=w>>21&31;rt=w>>16&31;rd=w>>11&31;imm=w&65535
        si=imm if imm<32768 else imm-65536;target=None
        if op==0:
            fn=w&63
            if fn==0:regs[rd]=regs[rt]<<(w>>6&31)
            elif fn==2:regs[rd]=regs[rt]>>(w>>6&31)
            elif fn==8:target=regs[rs]
            elif fn in (32,33):regs[rd]=regs[rs]+regs[rt]
            elif fn in (34,35):regs[rd]=regs[rs]-regs[rt]
            elif fn==36:regs[rd]=regs[rs]&regs[rt]
            elif fn==37:regs[rd]=regs[rs]|regs[rt]
            elif fn==43:regs[rd]=int(regs[rs]<regs[rt])
            else:raise AssertionError((hex(pc),hex(w)))
        elif op==2:target=((pc+4)&0xf0000000)|(w&0x3ffffff)<<2
        elif op in (4,5):
            if (regs[rs]==regs[rt])==(op==4):target=pc+4+(si<<2)
        elif op in (8,9):regs[rt]=regs[rs]+si
        elif op==11:regs[rt]=int(regs[rs]<(si&0xffffffff))
        elif op==12:regs[rt]=regs[rs]&imm
        elif op==13:regs[rt]=regs[rs]|imm
        elif op==15:regs[rt]=imm<<16
        elif op==16:
            assert rs==0,'trace prefix must not modify CP0'
            regs[rt]=cp[rd]
        elif op in (35,36,37,40,41,43):
            a=(regs[rs]+si)&0xffffffff;n=4 if op in (35,43) else 2 if op in (37,41) else 1
            if op in (35,36,37):regs[rt]=read(a,n)
            else:write(a,regs[rt],n)
        else:raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None,'control transfer in delay slot'
        regs[:]=[v&0xffffffff for v in regs];regs[0]=0
        pc=(pending if pending is not None else pc+4)&0xffffffff;pending=target
    raise AssertionError('compiled helper did not return')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf')
    ap.add_argument('--json-output',type=Path);a=ap.parse_args()
    base,s=load_elf(a.elf);state=s['native_diag_state']&0x1fffffff;sram=s['sram']&0x1fffffff
    assert all(n in s for n in ('native_diag_trace_event','native_diag_trace_second','native_diag_sample_bookkeeping'))
    def put(m,a,v):m.update((a+i,b) for i,b in enumerate((v&0xffffffff).to_bytes(4,'big')))
    def get(m,a,n=4):return int.from_bytes(bytes(m.get(a+i,0) for i in range(n)),'big')
    guest=bytes((i*43+7)&255 for i in range(0x2000));cases=0
    for index in (0,1,63,127,255,399,400,401):
      for start,now in ((0,2343750),(0xffff0000,0x0023a34e)):
        m=base.copy();m.update((sram+i,v) for i,v in enumerate(guest+bytes([0xa5])*0x6000))
        put(m,sram+0x212c,0);put(m,state,start);put(m,state+40,index)
        put(m,state+8,3210);put(m,state+24,155);put(m,state+56,2620)
        controls=bytes((i*7+3)&255 for i in range(32));m.update((0x04000ba0+i,b) for i,b in enumerate(controls))
        put(m,0x04000ef0,2);put(m,0x04000ec4,17);m[0x04000ec8]=1
        put(m,0x04040010,0x2345);put(m,0x0410000c,0x1234);put(m,0x04080000,0xf5c)
        before=bytes(m[sram+i] for i in range(0x8000));r=[0x80000100+i for i in range(32)];r[0]=0;r[31]=0xdead0000
        r[8]=s['native_diag_state'];r[9]=now
        execute(m,s['native_diag_trace_event'],r,{})
        assert bytes(m[sram+i] for i in range(0x2000))==guest
        if index<400:
            w=struct.unpack('>12I',bytes(m[sram+0x3200+index*48+i] for i in range(48)))
            expected=((now-start)&0xffffffff,155,2620,3210|0xf5c<<16,
                0x2345|controls[29]<<16|controls[30]<<24,0x1234|controls[28]<<16|1<<24,
                int.from_bytes(controls[4:6],'big')<<16|int.from_bytes(controls[14:16],'big'),
                int.from_bytes(controls[16:18],'big')<<16|int.from_bytes(controls[6:8],'big'),
                int.from_bytes(controls[20:24],'big'),int.from_bytes(controls[24:28],'big'),2,
                int.from_bytes(controls[8:10],'big')<<16|17)
            assert w==expected,(w,expected);assert get(m,state+40)==index+1
            after=bytes(m[sram+i] for i in range(0x8000));lo=0x3200+index*48
            assert after[:lo]==before[:lo] and after[lo+48:]==before[lo+48:]
        else:
            assert get(m,state+40)==index and get(m,sram+0x212c)==1
            assert bytes(m[sram+0x3200+i] for i in range(0x4b00))==before[0x3200:0x7d00]
        cases+=1
    for index in (0,1,19,20,21):
        m=base.copy();put(m,state,0xffff0000);put(m,state+44,index);put(m,state+24,59);put(m,state+56,75)
        put(m,sram+0x212c,0);counts=(350,21,10,40,279,320,100,300,4)
        for i,v in enumerate(counts):put(m,state+64+i*4,v)
        r=[0]*32;r[8]=s['native_diag_state'];r[9]=0x2cb8170;r[31]=0xdead0000
        execute(m,s['native_diag_trace_second'],r,{})
        if index<20:
            b=bytes(m.get(sram+0x7d00+index*32+i,0) for i in range(32))
            assert struct.unpack('>3I',b[:12])==((0x2cb8170-0xffff0000)&0xffffffff,59,75)
            assert struct.unpack('>9H',b[12:30])==counts and int.from_bytes(b[30:],'big')==index+1
            assert all(get(m,state+64+i*4)==0 for i in range(9))
        else:assert get(m,sram+0x212c)==4 and get(m,state+44)==index
        cases+=1
    for ordinal in (0,1,7,8,1023,7152,8192):
      for cursor in (0,4092,4096):
        m=base.copy();put(m,state+8,ordinal);put(m,state+12,cursor);put(m,sram+0x212c,0)
        put(m,sram+0x2200+(cursor%4096),0xabcdef12)
        r=[0x80000100+i for i in range(32)];r[0]=0;before=r.copy();epc=0x80012340
        execute(m,s['native_diag_interrupt'],r,{9:0x12345678,14:epc},s['native_diag_sample_bookkeeping'])
        assert all(r[i]==before[i] for i in set(range(32))-{26,27})
        kept=ordinal%8==0 and cursor<4096
        assert get(m,state+12)==cursor+(4 if kept else 0)
        assert get(m,sram+0x2200+(cursor%4096))==(epc if kept else 0xabcdef12)
        assert get(m,sram+0x212c)==(2 if ordinal%8==0 and cursor==4096 else 0)
        cases+=1
    # Exercise the compiled terminal path through its body checksum boundary.
    # All populated guest/PC/event/second regions must survive finalization;
    # only the dedicated header is writable. This catches legacy v2 palette,
    # GPR or RSP-memory copies that would overlap the new trace geometry.
    m=base.copy();payload=bytes((i*43+7)&255 for i in range(0x8000))
    m.update((sram+i,v) for i,v in enumerate(payload));put(m,state,0)
    for off in (0x18,0x14):put(m,0x04040000+off,0)
    r=[0]*32;r[24]=2
    execute(m,s['native_diag_finalize'],r,{9:937600000,12:0x8000,13:0,14:0x80012340},
            s['native_diag_sum_guest'],terminal_rcp=True)
    after=bytes(m[sram+i] for i in range(0x8000))
    assert after[:0x2000]==payload[:0x2000] and after[0x2200:]==payload[0x2200:]
    cases+=1
    proof=dict(passed=True,cases=cases,
      append_only=True,overflow_marked=True,guest_sram_preserved=True,irq_registers_preserved=True,
      count_wrap=True,compact_seconds=True,terminal_trace_preserved=True,native_fps_authority=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print('NATIVE_DIAG_TRACE_COMPILED PASS',json.dumps(proof))

if __name__=='__main__':main()
