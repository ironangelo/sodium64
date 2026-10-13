#!/usr/bin/env python3
"""Production C transaction executes actual RSP binaries via synthetic MMIO/PI.

Original numeric context only. No serial, ROM or physical timing acceptance.
"""
import argparse,ctypes as c,json,os,random,struct,subprocess,tempfile
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_scene_rsp_context import execute,state
U32=c.POINTER(c.c_uint32)
Read=c.CFUNCTYPE(c.c_uint32,c.c_uint32)
Write=c.CFUNCTYPE(None,c.c_uint32,c.c_uint32)
Transfer=c.CFUNCTYPE(c.c_int,U32,c.c_uint32,c.c_int)
Wait=c.CFUNCTYPE(c.c_int)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path)
    ap.add_argument('--cc',default=os.environ.get('CC','gcc'));ap.add_argument('--output',type=Path)
    a=ap.parse_args();root=Path(__file__).resolve().parents[1];cases=0
    _,capture=read_text(a.build/'src/rsp_scene_capture.elf');_,restore=read_text(a.build/'src/rsp_scene_restore.elf')
    def array(blob):return (c.c_uint32*(len(blob)//4))(*struct.unpack('>'+str(len(blob)//4)+'I',blob))
    cap,res=array(capture),array(restore)
    with tempfile.TemporaryDirectory(prefix='s64-rsp-ctx-') as directory:
        dll=Path(directory)/('context.dll' if os.name=='nt' else 'context.so')
        cmd=[a.cc,'-std=c11','-O2','-shared','-Wall','-Wextra','-Werror']
        cmd+=['-Wl,--export-all-symbols'] if os.name=='nt' else ['-fPIC']
        subprocess.run(cmd+[str(root/'src/scene_rsp_context.c'),'-o',str(dll)],check=True)
        lib=c.CDLL(str(dll));fn=lib.scene_rsp_context_roundtrip
        fn.argtypes=[U32,U32,c.c_uint,U32,c.c_uint,Read,Write,Transfer,Wait];fn.restype=c.c_uint32
        def test(*,fail=0,corrupt=0,wait_fault=0,bad_stop=False,SP_busy=False,readback_fault=False):
            nonlocal cases
            rng=random.Random(4560);sp=bytearray(rng.randbytes(8192));cart=bytearray(9216)
            struct.pack_into('>III',sp,0x13c0,0x40882000,0x0900040f,0)
            struct.pack_into('>I',sp,0x13bc,0x24080002)
            saved=bytes(sp);machine=list(state(4500));machine[0][8]=2
            before=([*machine[0]],[x.copy() for x in machine[1]],machine[2].copy(),machine[3].copy())
            status=0x1801;pc=0x3c8 if not bad_stop else 0x3c0
            calls=waits=writes=0;trace=[];errors=[]
            @Read
            def read(address):
                try:
                    if address==0xa4040010:return status
                    if address==0xa4080000:return pc
                    if address in (0xa4040018,0xa4040014):return int(SP_busy)
                    assert 0xa4000000<=address<0xa4002000 and address%4==0,hex(address)
                    return struct.unpack_from('>I',sp,address-0xa4000000)[0]
                except Exception as e:errors.append(e);return 0
            @Write
            def write(address,value):
                nonlocal writes,status,pc
                try:
                    writes+=1
                    if address==0xa4040010:
                        assert value in (5,6)
                        if value==5:status&=~3
                        else:status=(status|1)&~2
                    elif address==0xa4080000:pc=value
                    else:
                        assert 0xa4000000<=address<0xa4002000 and address%4==0,hex(address)
                        if readback_fault and calls>76 and address==0xa4000020:value^=1
                        struct.pack_into('>I',sp,address-0xa4000000,value)
                except Exception as e:errors.append(e)
            @Transfer
            def transfer(buffer,offset,to_cart):
                nonlocal calls
                try:
                    calls+=1;trace.append((calls,offset,to_cart))
                    assert offset%512==0 and offset+512<=len(cart)
                    if calls==fail:return 0
                    if to_cart:cart[offset:offset+512]=struct.pack('>128I',*(buffer[i] for i in range(128)))
                    else:
                        values=struct.unpack_from('>128I',cart,offset)
                        for i,value in enumerate(values):buffer[i]=value
                    if calls==corrupt:buffer[10]^=1
                    return 1
                except Exception as e:errors.append(e);return 0
            @Wait
            def wait():
                nonlocal waits,status
                try:
                    waits+=1
                    if waits==wait_fault:return 0
                    assert pc==0 and not status&3
                    d=bytearray(sp[:4096]);code=bytes(sp[4096:])
                    execute(code,d,*machine);sp[:4096]=d;status|=3;return 1
                except Exception as e:errors.append(e);return 0
            scratch=(c.c_uint32*128)()
            actual=fn(scratch,cap,len(cap),res,len(res),read,write,transfer,wait)
            assert not errors,errors
            expected=0 if bad_stop or SP_busy or 0<fail<=48 or 0<corrupt<=48 else 2 if fail or corrupt or wait_fault or readback_fault else 1
            assert actual==expected,(cases,actual,expected,calls,waits)
            if actual==0:assert not writes and bytes(sp)==saved and tuple(machine)==before,'mutation before full backup'
            if actual==1:
                assert calls==92 and waits==5 and bytes(sp)==saved and tuple(machine)==before
                assert status==0x1801 and pc==0x3c
            cases+=1;return trace
        trace=test()
        for position in range(1,93):test(fail=position)
        for position,offset,to_cart in trace:
            if not to_cart:test(corrupt=position)
        for wait in range(1,6):test(wait_fault=wait)
        test(bad_stop=True);test(SP_busy=True);test(readback_fault=True)
        result=dict(passed=True,cases=cases,production_C_and_actual_RSP_binaries=True,
            transfer_fault_positions=92,read_corruptions=sum(not x[2] for x in trace),wait_fault_positions=5,
            pre_mutation_full_backup=True,deliberate_zero_context_proved=True,
            full700byte_register_recapture_exact=True,SP8KiB_restore_checksum_readback=True,
            no_DP_AI_guest_SD_or_ROM_access=True,callback_exceptions_fail=True,
            hardware_timing_mocked=True,native_acceptance=False,complete_machine_restore=False)
        if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        if os.name=='nt':c.windll.kernel32.FreeLibrary(c.c_void_p(lib._handle))
if __name__=='__main__':main()
