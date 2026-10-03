#!/usr/bin/env python3
"""Execute the compiled dormant init/manual arm with original memory and CP0.

Check guest SRAM preservation, no unarmed timer, modulo-Count deadlines,
one-shot behavior and renderer register preservation. No commercial data.
"""
import argparse, json, struct
from pathlib import Path
from native_diag_report import elf_symbols

def load_elf(path):
    b=Path(path).read_bytes();h=struct.unpack_from('>16sHHIIIIIHHHHHH',b)
    assert b[:6]==b'\x7fELF\x01\x02'
    memory={}
    for i in range(h[12]):
        s=struct.unpack_from('>IIIIIIIIII',b,h[6]+i*h[11])
        if s[2]&2:
            raw=b[s[4]:s[4]+s[5]] if s[1]!=8 else bytes(s[5])
            memory.update((s[3]+j&0x1fffffff,v) for j,v in enumerate(raw))
    return memory,dict((n,v&0xffffffff) for v,n in elf_symbols(path))

def execute(memory,pc,regs,cp):
    writes=[];pending=None
    def read(a,n):return int.from_bytes(bytes(memory.get((a+i)&0x1fffffff,0) for i in range(n)),'big')
    def write(a,v,n):
        for i,c in enumerate((v&((1<<(n*8))-1)).to_bytes(n,'big')):memory[(a+i)&0x1fffffff]=c
    for step in range(100000):
        if pc==0xdead0000:return writes
        w=read(pc,4);op=w>>26;rs=w>>21&31;rt=w>>16&31;rd=w>>11&31
        imm=w&65535;si=imm if imm<32768 else imm-65536;target=None
        if op==0:
            fn=w&63
            if fn==0:regs[rd]=regs[rt]<<(w>>6&31)
            elif fn==8:target=regs[rs]
            elif fn in (32,33):regs[rd]=regs[rs]+regs[rt]
            elif fn in (34,35):regs[rd]=regs[rs]-regs[rt]
            elif fn==36:regs[rd]=regs[rs]&regs[rt]
            elif fn==37:regs[rd]=regs[rs]|regs[rt]
            else:raise AssertionError((hex(pc),hex(w)))
        elif op in (4,5):
            if (regs[rs]==regs[rt])==(op==4):target=pc+4+(si<<2)
        elif op in (8,9):regs[rt]=regs[rs]+si
        elif op==12:regs[rt]=regs[rs]&imm
        elif op==13:regs[rt]=regs[rs]|imm
        elif op==15:regs[rt]=imm<<16
        elif op==16:
            if rs==0:regs[rt]=cp[rd]
            elif rs==4:
                cp[rd]=regs[rt];writes.append((rd,regs[rt]))
            else:raise AssertionError((hex(pc),hex(w)))
        elif op in (35,36,40,43):
            a=(regs[rs]+si)&0xffffffff;n=4 if op in (35,43) else 1
            if op in (35,36):regs[rt]=read(a,n)
            else:write(a,regs[rt],n)
        elif op==47:pass # Cache maintenance has no alias effects in this VM
        else:raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None,'control transfer in delay slot'
        regs[:]=[v&0xffffffff for v in regs];regs[0]=0
        pc=(pending if pending is not None else pc+4)&0xffffffff;pending=target
    raise AssertionError('compiled arm/init did not return')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path)
    a=ap.parse_args();base,s=load_elf(a.elf)
    assert all(n in s for n in ('native_diag_init','native_diag_arm','native_diag_state'))
    state=s['native_diag_state']&0x1fffffff;sram=s['sram']&0x1fffffff
    def word(m,a):return int.from_bytes(bytes(m.get(a+i,0) for i in range(4)),'big')
    count=0
    for now in (0,0x12345678,0xffff0000):
        for status in (0x401,0x403,0x1401,0x9403):
            m=base.copy();guest=bytes((i*43+7)&255 for i in range(0x2000))
            m.update((sram+i,v) for i,v in enumerate(guest+bytes([0xab])*0x6000))
            r=[0x80000100+i for i in range(32)];r[0]=0;r[31]=0xdead0000
            cp={9:now,11:0xdeadbeef,12:status}
            writes=execute(m,s['native_diag_init'],r,cp)
            assert cp[11]==0xdeadbeef and not writes,'dormant init must not arm Compare'
            assert bytes(m[sram+i] for i in range(0x2000))==guest
            assert bytes(m[sram+i] for i in range(0x2000,0x8000))==bytes(0x6000)
            assert word(m,state+112)==0 and m[s['precision_set']&0x1fffffff]==20
            # Simulate gameplay counters before starting: arm must zero them.
            for i in range(128):m[state+i]=0xab if not 112<=i<116 else 0
            r=[0x80000100+i for i in range(32)];r[0]=0;r[31]=0xdead0000;before=r.copy()
            writes=execute(m,s['native_diag_arm'],r,cp)
            assert cp[11]==(now+131071)&0xffffffff and cp[12]==status|0x8000
            assert writes[0]==(12,status&~1) and writes[-1]==(12,status|0x8000)
            for i in set(range(32))-{8,9,10,11,26,27}:assert r[i]==before[i],('register',i)
            expected={0:now,16:(now+2343750)&0xffffffff,20:(now+46875000)&0xffffffff,36:now,112:1}
            for i in range(0,128,4):assert word(m,state+i)==expected.get(i,0),(i,word(m,state+i))
            saved=bytes(m[state+i] for i in range(128));cp[9]=(now+999999)&0xffffffff
            r[31]=0xdead0000;again=execute(m,s['native_diag_arm'],r,cp)
            assert not any(reg==11 for reg,value in again),'second Start must not reset Compare'
            assert bytes(m[state+i] for i in range(128))==saved,'one-shot arm changed counters'
            count+=1
    print('NATIVE_DIAG_ARM PASS',json.dumps(dict(cases=count,guest_sram_preserved=True,
          dormant_init=True,one_shot=True,count_wrap=True,renderer_registers_preserved=True)))

if __name__=='__main__':main()
