#!/usr/bin/env python3
"""Linked private RSP capture/restore programs; original synthetic registers.

Instruction semantics checked against ares9408cb43 RSP SISD source. This does
not execute a game, DMA/DP/AI, CPU pipeline or physical hardware.
"""
import argparse,itertools,json,random,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
MASK=(1<<48)-1
def signed(value,bits):return value if value<(1<<(bits-1)) else value-(1<<bits)

def execute(code,d,r,v,acc,flags,stop=None,pending_entry=None):
    pc=steps=0;pending=pending_entry
    while pc<len(code):
        if pc==stop:return steps
        w=struct.unpack_from('>I',code,pc)[0]
        op,rs,rt,rd,vd,fn=w>>26,w>>21&31,w>>16&31,w>>11&31,w>>6&31,w&63
        imm=w&65535;si=signed(imm,16)
        if op==0 and fn==13:return steps+1
        if w==0:pass
        elif op in (35,43):
            address=(r[rs]+si)&4095;assert address%4==0
            if op==35:r[rt]=struct.unpack_from('>I',d,address)[0]
            else:struct.pack_into('>I',d,address,r[rt]&0xffffffff)
        elif op in (50,58):
            assert w>>11&31==4 and w>>7&15==0,'unsupported vector memory element'
            address=(r[rs]+signed(w&127,7)*16)&4095;assert address%16==0
            if op==50:v[rt]=list(struct.unpack_from('>8H',d,address))
            else:struct.pack_into('>8H',d,address,*v[rt])
        elif op==18:
            if rs==2:
                assert rd<3
                r[rt]=signed(flags[rd],16)&0xffffffff
            elif rs==6:
                assert rd<3
                flags[rd]=r[rt]&([65535,65535,255][rd])
            elif rs>=16:
                e=rs-16
                if fn==0x1d:
                    assert e in (8,9,10)
                    v[vd]=[(x>>((10-e)*16))&65535 for x in acc]
                else:
                    assert e==0 and fn in (5,6,15,16,20,40),('unproved vector arithmetic',hex(w))
                    a,b=v[rd].copy(),v[rt].copy()
                    if fn==5: # VMUDM: signed VS * unsigned VT, result ACC MID.
                        acc[:]=[(signed(x,16)*y)&MASK for x,y in zip(a,b)]
                        v[vd]=[(x>>16)&65535 for x in acc]
                    elif fn==6:
                        acc[:]=[(x*signed(y,16))&MASK for x,y in zip(a,b)]
                        v[vd]=[x&65535 for x in acc]
                    elif fn==15:
                        acc[:]=[(old+((signed(x,16)*signed(y,16))<<16))&MASK for old,x,y in zip(acc,a,b)]
                        v[vd]=[max(-32768,min(32767,signed(x>>16,32)))&65535 for x in acc]
                    elif fn==16: # VADD includes VCOL; clears both VCO halves.
                        values=[signed(x,16)+signed(y,16)+((flags[0]>>i)&1) for i,(x,y) in enumerate(zip(a,b))]
                        acc[:]=[(old&~65535)|(x&65535) for old,x in zip(acc,values)]
                        v[vd]=[max(-32768,min(32767,x))&65535 for x in values];flags[0]=0
                    elif fn==20: # VADDC wraps and publishes unsigned carry only.
                        values=[x+y for x,y in zip(a,b)]
                        acc[:]=[(old&~65535)|(x&65535) for old,x in zip(acc,values)]
                        v[vd]=[x&65535 for x in values]
                        flags[0]=sum((x>>16)<<i for i,x in enumerate(values))
                    else: # VAND changes ACC low, not its upper32 bits.
                        values=[x&y for x,y in zip(a,b)]
                        acc[:]=[(old&~65535)|x for old,x in zip(acc,values)];v[vd]=values
            else:raise AssertionError(('unproved COP2 operation',hex(w)))
        else:raise AssertionError(('unexpected control/RCP write',pc,hex(w)))
        r[0]=0
        pc=pending if pending is not None else pc+4;pending=None;steps+=1
        assert steps<512,'program did not stop'
    raise AssertionError('no BREAK')

def encoded(r,v,acc,flags):
    return (struct.pack('>32I',*r)+b''.join(struct.pack('>8H',*x) for x in v)+
            b''.join(struct.pack('>8H',*((a>>shift)&65535 for a in acc)) for shift in (32,16,0))+
            struct.pack('>3I',*(signed(f,16)&0xffffffff for f in flags)))
def helpers(d,acc):
    values=[(-((x>>32)+((x>>31)&1)))&65535 for x in acc]
    struct.pack_into('>8H',d,0x2c0,*values)
    struct.pack_into('>8H',d,0x2d0,*([1]*8))
    struct.pack_into('>8H',d,0x2e0,*([0x8000]*8))
def state(seed):
    rng=random.Random(seed)
    return ([0]+[rng.getrandbits(32) for _ in range(31)],
            [[rng.randrange(65536) for _ in range(8)] for _ in range(32)],
            [rng.getrandbits(48) for _ in range(8)],
            [rng.randrange(65536),rng.randrange(65536),rng.randrange(256)])
def case(capture,restore,seed,override=None,pending_entry=None):
    r,v,acc,flags=state(seed)
    if override is not None:acc[:]=override
    golden=encoded(r,v,acc,flags)
    before=([*r],[x.copy() for x in v],acc.copy(),flags.copy())
    d=bytearray((i*31+97)&255 for i in range(4096));guard=bytes(d[700:])
    capture_steps=execute(capture,d,r,v,acc,flags,pending_entry=pending_entry)
    assert (r,v,acc,flags)==before,'capture changed architectural state'
    assert d[:700]==golden and bytes(d[700:])==guard,'capture owner/guard mismatch'
    helpers(d,acc);memory=bytes(d)
    r,v,acc,flags=state(seed+10000)
    restore_steps=execute(restore,d,r,v,acc,flags,pending_entry=pending_entry)
    assert (r,v,acc,flags)==before,'restored architectural context differs'
    assert bytes(d)==memory,'restore unexpectedly changed DMEM'
    return capture_steps,restore_steps

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args();_,capture=read_text(a.build/'src/rsp_scene_capture.elf');_,restore=read_text(a.build/'src/rsp_scene_restore.elf')
    prefix=0x3c
    assert capture[:prefix]==restore[:prefix]==bytes(prefix),'safe shared pending entry moved'
    banks=0
    for path in a.build.glob('src/rsp_*.elf'):
        if path.stem.startswith('rsp_scene_'):continue
        _,text=read_text(path)
        for w in struct.unpack('>'+str(len(text)//4)+'I',text):
            assert not (w>>26==18 and w>>21&31>=16 and w&63 in (0x30,0x31,0x32,0x34,0x35,0x36)), 'DIV unit ownership opened: '+path.name
        banks+=1
    counts=set();cases=0
    for pending_entry in (None,0x3c):
        for seed in range(256):counts.add(case(capture,restore,seed,pending_entry=pending_entry));cases+=1
    edges=(0,1,0x7fff,0x8000,0xffff)
    for hi,mid,lo in itertools.product(edges,repeat=3):
        x=hi<<32|mid<<16|lo;counts.add(case(capture,restore,cases,[x]*8));cases+=1
    # Every MID16 value reaches the signed-carry compensation path in actual
    # linked arithmetic. HI/LO rotate independently across their edge values.
    mid_sweep=0
    for base in range(0,65536,8):
        values=[edges[(base//8+i)%5]<<32|(base+i)<<16|edges[(base//16+i)%5] for i in range(8)]
        d=bytearray(4096);struct.pack_into('>8H',d,0x290,*((x>>16)&65535 for x in values))
        struct.pack_into('>8H',d,0x2a0,*(x&65535 for x in values));helpers(d,values)
        r,v,acc,flags=state(base);execute(restore,d,r,v,acc,flags,stop=prefix+36)
        assert acc==values,'MID signed-carry reconstruction';mid_sweep+=8
    faults=[]
    words=lambda b:list(struct.unpack('>'+str(len(b)//4)+'I',b))
    cw,rw=words(capture),words(restore)
    for name,side,index in [('missing_GPR_capture','capture',5),('missing_vector_capture','capture',40),
        ('missing_ACC_capture','capture',64),('missing_capture_t0_restore','capture',77),
        ('missing_ACC_mid_add','restore',6),('missing_ACC_high_add','restore',8),
        ('missing_vector_restore','restore',13),('missing_flag_restore','restore',42),
        ('missing_GPR_restore','restore',55)]:
        changed=(cw if side=='capture' else rw).copy();changed[prefix//4+index]=0
        blob=struct.pack('>'+str(len(changed))+'I',*changed)
        try:case(blob if side=='capture' else capture,blob if side=='restore' else restore,321,
                 [0xffff80001234,0x80007fffffff,0x1234fedc9876]*2+[0,0xabcdef012345])
        except AssertionError:faults.append(name)
        else:raise AssertionError('escaped context mutation '+name)
    result=dict(passed=True,actual_binary_roundtrips=cases,ACC_MID_values=mid_sweep,
                instruction_counts=[list(x) for x in counts],mutations_rejected=faults,
                GPR32_vector32_flags3_ACC48x8_exact=True,context_bytes=700,
                capture_preserves_context=True,restore_DMEM_readonly=True,
                delayed_entry_3C_and_ordinary_entry_tested=True,
                current_banks_without_DIV_instructions=banks,
                reference='ares9408cb43 RSP SISD vector semantics',
                CPU_hardware_transaction_tested=False,native_acceptance=False,
                full_serializer_or_machine_restore=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
