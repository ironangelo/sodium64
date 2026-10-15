#!/usr/bin/env python3
"""Execute compiled v4 observers with original memory, CP0 and 64-bit GPRs."""
import argparse,json,struct
from pathlib import Path
from test_native_diag_arm import load_elf

MASK=(1<<64)-1
def sx(v):
    v&=0xffffffff
    return (v if v<0x80000000 else v-0x100000000)&MASK

def execute(memory,pc,regs,cp,stop=0xdead0000,terminal_rcp=False,inject_irq=False,rsp=False):
    pending=None;lo=0
    def read(a,n):
        a&=0x1fffffff
        if rsp and a<0x1000:a+=0x04000000
        assert a!=0x0404001c,'observer must not acquire SP semaphore'
        return int.from_bytes(bytes(memory.get((a+i)&0x1fffffff,0) for i in range(n)),'big')
    def write(a,v,n):
        a&=0x1fffffff
        if rsp and a<0x1000:a+=0x04000000
        if 0x04000000<=a<0x05000000:
            assert terminal_rcp,'live observer must not write RCP'
            if a==0x04040010 and v==2:v=1
        for i,c in enumerate((v&((1<<(n*8))-1)).to_bytes(n,'big')):memory[(a+i)&0x1fffffff]=c
    for step in range(100000):
        if pc==stop:return step
        w=read(pc,4);op=w>>26;rs=w>>21&31;rt=w>>16&31;rd=w>>11&31;imm=w&65535
        si=imm if imm<32768 else imm-65536;target=None
        if op==0:
            fn=w&63
            if fn==0:regs[rd]=sx((regs[rt]&0xffffffff)<<(w>>6&31))
            elif fn==2:regs[rd]=sx((regs[rt]&0xffffffff)>>(w>>6&31))
            elif fn==4:regs[rd]=sx((regs[rt]&0xffffffff)<<(regs[rs]&31))
            elif fn==8:target=regs[rs]&0xffffffff
            elif fn==9:
                target=regs[rs]&0xffffffff;regs[rd]=sx(pc+8)
            elif fn==18:regs[rd]=sx(lo)
            elif fn==24:lo=(regs[rs]*regs[rt])&0xffffffff
            elif fn in (32,33):regs[rd]=sx(regs[rs]+regs[rt])
            elif fn in (34,35):regs[rd]=sx(regs[rs]-regs[rt])
            elif fn==36:regs[rd]=regs[rs]&regs[rt]
            elif fn==37:regs[rd]=regs[rs]|regs[rt]
            elif fn==38:regs[rd]=regs[rs]^regs[rt]
            elif fn==39:regs[rd]=~(regs[rs]|regs[rt])&MASK
            elif fn==42:
                left=regs[rs] if regs[rs]<1<<63 else regs[rs]-(1<<64)
                right=regs[rt] if regs[rt]<1<<63 else regs[rt]-(1<<64)
                regs[rd]=int(left<right)
            elif fn==43:regs[rd]=int(regs[rs]<regs[rt])
            else:raise AssertionError(('forbidden/unhandled special instruction',hex(pc),hex(w)))
        elif op in (2,3):
            if op==3:regs[31]=sx(pc+8)
            target=((pc+4)&0xf0000000)|(w&0x3ffffff)<<2
        elif op in (4,5):
            if (regs[rs]==regs[rt])==(op==4):target=pc+4+(si<<2)
        elif op==1:
            assert rt in (0,1)
            signed=regs[rs] if regs[rs]<1<<63 else regs[rs]-(1<<64)
            if (signed<0)==(rt==0):target=pc+4+(si<<2)
        elif op in (8,9):regs[rt]=sx(regs[rs]+si)
        elif op==11:regs[rt]=int(regs[rs]<(si&MASK))
        elif op==12:regs[rt]=regs[rs]&imm
        elif op==13:regs[rt]=regs[rs]|imm
        elif op==14:regs[rt]=regs[rs]^imm
        elif op==15:regs[rt]=sx(imm<<16)
        elif op==16:
            if rs==0:
                value=cp[rd](step) if callable(cp[rd]) else cp[rd]
                regs[rt]=sx(value)
            elif rs==4:cp[rd]=regs[rt]&0xffffffff
            elif w==0x42000018:return step+1
            else:raise AssertionError((hex(pc),hex(w)))
        elif op in (32,35,36,37,40,41,43,55,63):
            adr=(regs[rs]+si)&0xffffffff;n=8 if op in (55,63) else 4 if op in (35,43) else 2 if op in (37,41) else 1
            if op in (32,35,36,37,55):
                value=read(adr,n);regs[rt]=sx(value) if op==35 else sx(value-256 if value>=128 else value) if op==32 else value
            else:write(adr,regs[rt],n)
        elif op==47:pass
        else:raise AssertionError((hex(pc),hex(w)))
        assert pending is None or target is None,'control transfer in delay slot'
        regs[:]=[v&MASK for v in regs];regs[0]=0
        if inject_irq and cp.get(12,0)&3==1:
            regs[26]=0x123456789abcdef0;regs[27]=0xabcdef0123456789
        pc=(pending if pending is not None else pc+4)&0xffffffff;pending=target
    raise AssertionError('compiled observer did not return')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf');ap.add_argument('--json-output',type=Path)
    ap.add_argument('--rsp-main',type=Path,required=True);ap.add_argument('--rsp-mode7',type=Path,required=True)
    ap.add_argument('--rsp-hcomp',type=Path,required=True)
    a=ap.parse_args();base,s=load_elf(a.elf)
    assert 'native_diag_frame_complete' in s,'v4 trace ELF required'
    rb,rs=load_elf(a.rsp_main);mb,ms=load_elf(a.rsp_mode7)
    for name,address,extent in (('dma_wait',0xf4c,12),('rdp_fetch_wait',0x2d8,24),('rdp_texture_wait',0x31c,16)):
        assert rs[name]&0xfff==address and ms[name]&0xfff==address
        pc=0x04001000+address
        code=bytes(rb[pc+i] for i in range(extent))
        assert code==bytes(mb[pc+i] for i in range(extent)),name
        # The next instruction retires the loop (JR RA or first DMA write).
        next_word=int.from_bytes(bytes(rb[pc+extent+i] for i in range(4)),'big')
        assert next_word in (0x03e00008,0x40840000),(name,hex(next_word))
    hb,hs=load_elf(a.rsp_hcomp)
    assert hs['hcomp_fence_wait']&0xfff==0x3e4
    for banksym in ('native_diag_overlay_load','native_diag_overlay_main_return'):
        assert rs[banksym]==ms[banksym]
    assert rs['native_diag_overlay_load']&0xfff==0xc60
    assert rs['overlay_load_slot']&0xfff==0xf7c and rs['overlay_load_main']&0xfff==0xf90
    state=s['native_diag_state']&0x1fffffff;sram=s['sram']&0x1fffffff;cases=0
    def put(m,adr,v,n=4):m.update((adr+i,b) for i,b in enumerate((v&((1<<(n*8))-1)).to_bytes(n,'big')))
    def get(m,adr,n=4):return int.from_bytes(bytes(m.get(adr+i,0) for i in range(n)),'big')
    def registers():
        r=[(0xabcdef0000000000+i*0x123456789)&MASK for i in range(32)];r[0]=0;r[31]=0xdead0000;return r
    guest=bytes((i*43+7)&255 for i in range(0x2000))
    def memory():
        m=base.copy();m.update((sram+i,v) for i,v in enumerate(guest+bytes(0x6000)))
        for off in range(0,320,4):put(m,state+off,0)
        return m
    for bankmem,bs in ((rb,rs),(mb,ms)):
      for epoch in (0,0x1230,0xfff0):
       for bank in range(1,8):
        m=bankmem.copy();put(m,0x04000eca,epoch|1,2)
        r=[0]*32;r[5]=0x80123458|bank;r[25]=0xdead0000
        cp={6:0}
        execute(m,bs['native_diag_overlay_load'],r,cp,stop=bs['dma_read'],terminal_rcp=True,rsp=True)
        assert get(m,0x04000eca,2)==epoch|8|bank
        assert (r[4]&0xffffffff,r[5]&0xffffffff,r[6]&0xffffffff)==(0x13a8,0x80123458,0x3e7)
        # Re-enter the caller after the actual resident DMA loop returns.
        r[8]=0
        execute(m,r[31]&0xffffffff,r,cp,terminal_rcp=True,rsp=True)
        assert get(m,0x04000eca,2)==((epoch+16)&0xffff)|bank and (r[8]&15)==bank
        cases+=1
    for index in (0,1,99,159,160,161):
      for start,now in ((0,4687500),(0xffff0000,0x004686ac)):
        m=memory();m.update((sram+0x2200+i,0xa5) for i in range(0x5e00))
        put(m,state,start);put(m,state+40,index);put(m,state+24,155);put(m,state+56,90000)
        counts=(4,10,5,2,7,3,4,0)
        for i,v in enumerate(counts):
            put(m,state+136+i*4,v);put(m,state+268+i*4,v)
        for off,val in ((0xbb7,0x12),(0xbb8,0x20),(0xbb9,2),(0xbba,0x15),(0xbbb,0),(0xbbc,0),(0xbbd,1),(0xbbe,0x80)):
            put(m,0x04000000+off,val,1)
        put(m,0x04000ef0,2);put(m,0x04000ec4,8);put(m,0x04000ec8,1,1)
        put(m,state+264,0xf4c);put(m,state+300,0x2345);put(m,0x04040010,0x2345);put(m,0x0410000c,0x1234);put(m,0x04080000,0xf4c)
        before=bytes(m.get(sram+i,0) for i in range(0x8000))
        r=registers();r[8]=s['native_diag_state'];r[9]=sx(now)
        execute(m,s['native_diag_trace_event'],r,{})
        after=bytes(m.get(sram+i,0) for i in range(0x8000));assert after[:0x2000]==guest
        if index<160:
            rec=struct.pack('>2I2H2BH6BH16B',(now-start)&0xffffffff,90000,155,0xf4c,0x45,0xe1,0x1234,0x12,0x20,2,0x15,0,0,8,*counts,*counts)
            lo=0x6200+index*40;assert after[lo:lo+40]==rec,(after[lo:lo+40].hex(),rec.hex())
            assert after[:lo]==before[:lo] and after[lo+40:]==before[lo+40:]
            assert all(get(m,state+136+i*4)==0 for i in range(8))
        else:assert after[0x2200:]==before[0x2200:] and get(m,sram+0x212c)==1
        cases+=1
    for index in (0,1,19,20,21):
        m=memory();put(m,state+44,index);put(m,state+128,17)
        counts=(350,21,10,40,279,320,100,300,4);modules=(40,60,50,30,80,21,10,59)
        for i,v in enumerate(counts):put(m,state+64+i*4,v)
        for i,v in enumerate(modules):put(m,state+168+i*4,v)
        for off,v in ((236,5),(240,11),(244,20),(104,91),(228,12)):put(m,state+off,v)
        r=registers();r[8]=s['native_diag_state'];r[9]=46875000
        execute(m,s['native_diag_trace_second'],r,{})
        if index<20:
            b=bytes(m.get(sram+0x7b00+index*64+i,0) for i in range(64))
            assert struct.unpack_from('>9H',b,12)==counts and struct.unpack_from('>8H',b,32)==modules
            assert struct.unpack_from('>4H2I',b,48)==(17,5,11,20,91,12)
            assert all(get(m,state+64+i*4)==0 for i in range(9))
            assert all(get(m,state+168+i*4)==0 for i in range(8))
        else:assert get(m,sram+0x212c)==4 and get(m,state+44)==index
        cases+=1
    for cursor in (0,1,1279,1280,1281):
      for status in (0x401,0x403,0x9401,0x9403):
        m=memory();put(m,state+112,1);put(m,state+216,1);put(m,state+212,cursor)
        put(m,state,0xffff0000);put(m,state+200,0xfffe0000)
        put(m,state+204,3100);put(m,state+208,4700)
        r=registers();before=r.copy();cp={9:0x000d0000,12:status}
        execute(m,s['native_diag_frame_complete'],r,cp,inject_irq=True)
        assert cp[12]==status
        assert all(r[i]==before[i] for i in set(range(32))-{8,9,10,11,26,27})
        assert bytes(m[sram+i] for i in range(0x2000))==guest
        if cursor<1280:
            assert struct.unpack('>3I',bytes(m[sram+0x2600+cursor*12+i] for i in range(12)))==(0xe0000,3100,4700)
            assert get(m,state+212)==cursor+1
        else:assert get(m,state+212)==cursor and get(m,sram+0x212c)==8
        cases+=1
    for armed in (0,1):
        m=memory();put(m,state+112,armed);r=registers();cp={9:100,12:0x401}
        execute(m,s['native_diag_frame_complete'],r,cp)
        assert get(m,state+212)==0 and get(m,state+24)==1
        assert get(m,state+216)==armed and get(m,state+252)==armed
        cases+=1
    sites=[(s['native_diag_rsp_wait'],5),(s['native_diag_frame_wait'],6),(0x801c0100,1),(0x80000000,7)]
    for group,idx in (('cpu',0),('apu',1),('dsp',2),('dma',3),('ppu',4)):
        lo,hi=s['native_diag_'+group+'_start'],s['native_diag_'+group+'_end'];assert lo<hi
        sites.extend([(lo,idx),(hi-4,idx)])
    for epc,idx in sites:
      for pc,stage in ((0xf4c,236),(0xf54,236),(0x2d8,240),(0x2ec,240),(0x31c,244),(0x328,244),(0x3a8,None)):
        m=memory();put(m,state+16,0x60000000);put(m,0x04080000,pc)
        r=registers();before=r.copy()
        execute(m,s['native_diag_interrupt'],r,{9:1,14:epc,12:0x403,11:0})
        assert all(r[i]==before[i] for i in set(range(32))-{26,27}),('IRQ register',epc,pc)
        assert sum(get(m,state+136+i*4) for i in range(8))==1
        assert get(m,state+136+idx*4)==1 and get(m,state+168+idx*4)==1
        assert [get(m,state+off) for off in (236,240,244)]==[int(off==stage) for off in (236,240,244)]
        assert sum(get(m,state+268+i*4) for i in range(8))==1
        cases+=1
    for bank in range(8):
      for pc in (0x3a8,0x3e4,0xf4c,0xccc):
        m=memory();put(m,state+16,0x60000000);put(m,0x04080000,pc);put(m,0x04000eca,0x120+bank,2)
        r=registers();execute(m,s['native_diag_interrupt'],r,{9:1,14:s['native_diag_cpu_start']})
        idx=2 if pc==0xf4c else 7 if pc==0xccc else 3 if bank==3 and pc==0x3e4 else {0:1,1:7,2:7,3:4,4:6,5:5,6:4,7:4}[bank]
        assert get(m,state+268+idx*4)==1,(bank,pc,idx)
        assert get(m,state+264)==pc|(bank<<12)
        cases+=1
    for tag,cp9 in ((0x12b,1),(0x120,1),(0x121,lambda step:step*100000)):
        m=memory();put(m,state+16,0x60000000);put(m,0x04080000,0x400);put(m,0x04000eca,tag,2)
        r=registers();execute(m,s['native_diag_interrupt'],r,{9:cp9,14:s['native_diag_cpu_start']})
        assert get(m,state+272)==1 and get(m,state+264)==0x400,(tag,get(m,state+272),get(m,state+264))
        cases+=1
    m=memory();put(m,state+16,0x60000000);put(m,0x04040010,1)
    execute(m,s['native_diag_interrupt'],registers(),{9:1,14:s['native_diag_cpu_start']})
    assert get(m,state+268)==1 and get(m,state+264)==0;cases+=1
    for ordinal in (0,1,31,32,1023,7152,8192):
      for cursor in (0,1020,1024):
        m=memory();put(m,state+8,ordinal);put(m,state+12,cursor);put(m,sram+0x2200+(cursor%1024),0xabcdef12)
        r=registers();before=r.copy();epc=0x80012340
        execute(m,s['native_diag_interrupt'],r,{9:1,14:epc},s['native_diag_sample_bookkeeping'])
        kept=ordinal%32==0 and cursor<1024
        assert get(m,state+12)==cursor+(4 if kept else 0)
        assert get(m,sram+0x2200+(cursor%1024))==(epc if kept else 0xabcdef12)
        assert get(m,sram+0x212c)==(2 if ordinal%32==0 and cursor==1024 else 0)
        assert all(r[i]==before[i] for i in set(range(32))-{26,27})
        cases+=1
    m=memory();payload=bytes((i*43+7)&255 for i in range(0x8000));m.update((sram+i,v) for i,v in enumerate(payload))
    r=registers();r[24]=2
    execute(m,s['native_diag_finalize'],r,{9:937600000,12:0x8000,13:0,14:0x80012340},s['native_diag_sum_guest'],terminal_rcp=True)
    after=bytes(m[sram+i] for i in range(0x8000));assert after[:0x2000]==payload[:0x2000] and after[0x2200:]==payload[0x2200:]
    cases+=1
    proof=dict(passed=True,cases=cases,format_version=4,append_only=True,overflow_marked=True,
        all_frame_timings=True,guest_sram_preserved=True,irq_64bit_registers_preserved=True,
        frame_caller_registers_and_exl_preserved=True,asynchronous_irq_before_mask=True,
        count_wrap=True,all_irq_cpu_modules=True,resident_rsp_wait_samples=True,resident_wait_pc_contract=True,
        terminal_trace_preserved=True,rsp_bank_epoch_bookending=True,all_irq_rsp_stages=True,native_fps_authority=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print('NATIVE_DIAG_V4_COMPILED PASS',json.dumps(proof))

if __name__=='__main__':main()
