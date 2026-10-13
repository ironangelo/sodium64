#!/usr/bin/env python3
"""Separate RSP store/load after a deliberately changed architectural machine.

Production C, actual linked microcode, synthetic MMIO; no native timing claim.
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
class Saved(c.Structure):
    _fields_=[(x,c.c_uint32) for x in ('memory_hash','context_hash','status')]
def words(blob):return (c.c_uint32*(len(blob)//4))(*struct.unpack('>'+str(len(blob)//4)+'I',blob))
class Machine:
    def __init__(self,seed=4500):
        self.sp=bytearray(random.Random(seed).randbytes(8192));self.cart=bytearray(9216)
        struct.pack_into('>IIII',self.sp,0x13bc,0x24080002,0x40882000,0x0900040f,0)
        self.registers=list(state(seed));self.registers[0][8]=2
        self.status=0x1801;self.pc=0x3c8;self.calls=self.waits=self.writes=0
        self.trace=[];self.errors=[];self.fail=self.corrupt=self.wait_fault=0
        def guarded(fn,fallback):
            def call(*args):
                try:return fn(*args)
                except Exception as error:self.errors.append(error);return fallback
            return call
        self.read=Read(guarded(self._read,0));self.write=Write(guarded(self._write,None))
        self.transfer=Transfer(guarded(self._transfer,0));self.wait=Wait(guarded(self._wait,0))
    def _read(self,address):
        if address==0xa4040010:return self.status
        if address==0xa4080000:return self.pc
        if address in (0xa4040018,0xa4040014):return 0
        assert 0xa4000000<=address<0xa4002000 and address%4==0
        return struct.unpack_from('>I',self.sp,address-0xa4000000)[0]
    def _write(self,address,value):
        self.writes+=1
        if address==0xa4040010:
            if value&1:self.status&=~1
            if value&2:self.status|=1
            if value&4:self.status&=~2
            if value&0x20:self.status&=~0x20
            if value&0x40:self.status|=0x20
            if value&0x80:self.status&=~0x40
            if value&0x100:self.status|=0x40
            for i in range(8):
                if value&(0x200<<(2*i)):self.status&=~(0x80<<i)
                if value&(0x400<<(2*i)):self.status|=0x80<<i
        elif address==0xa4080000:self.pc=value
        else:
            assert 0xa4000000<=address<0xa4002000 and address%4==0
            struct.pack_into('>I',self.sp,address-0xa4000000,value)
    def _transfer(self,buffer,offset,to_cart):
        self.calls+=1;self.trace.append((self.calls,offset,to_cart))
        assert offset>=0x40000 and offset%512==0
        offset-=0x40000;assert offset+512<=len(self.cart)
        if self.calls==self.fail:return 0
        if to_cart:self.cart[offset:offset+512]=struct.pack('>128I',*(buffer[i] for i in range(128)))
        else:
            for i,value in enumerate(struct.unpack_from('>128I',self.cart,offset)):buffer[i]=value
        if self.calls==self.corrupt:buffer[10]^=1
        return 1
    def _wait(self):
        self.waits+=1
        if self.waits==self.wait_fault:return 0
        assert self.pc==0 and not self.status&3
        d=bytearray(self.sp[:4096]);execute(bytes(self.sp[4096:]),d,*self.registers,pending_entry=0x3c)
        self.sp[:4096]=d;self.status|=3;return 1
    def snapshot(self):
        return bytes(self.sp),json.dumps(self.registers),self.status
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path)
    ap.add_argument('--cc',default=os.environ.get('CC','gcc'));ap.add_argument('--output',type=Path)
    a=ap.parse_args();root=Path(__file__).resolve().parents[1]
    cap=words(read_text(a.build/'src/rsp_scene_capture.elf')[1])
    res=words(read_text(a.build/'src/rsp_scene_restore.elf')[1]);cases=0
    with tempfile.TemporaryDirectory(prefix='s64-rsp-slot-') as directory:
        dll=Path(directory)/('slot.dll' if os.name=='nt' else 'slot.so')
        cmd=[a.cc,'-O2','-std=c11','-shared','-Wall','-Wextra','-Werror','-DSODIUM64_SCENE_SLOT=1']
        cmd+=['-Wl,--export-all-symbols'] if os.name=='nt' else ['-fPIC']
        subprocess.run(cmd+[str(root/'src/scene_rsp_context.c'),'-o',str(dll)],check=True)
        lib=c.CDLL(str(dll));store=lib.scene_rsp_context_store;load=lib.scene_rsp_context_load
        store.argtypes=[U32,c.c_uint32,c.POINTER(Saved),U32,c.c_uint,Read,Write,Transfer,Wait]
        load.argtypes=[U32,c.c_uint32,c.POINTER(Saved),U32,c.c_uint,U32,c.c_uint,Read,Write,Transfer,Wait]
        store.restype=load.restype=c.c_uint32
        def run(kind,fail=0,corrupt=0,wait_fault=0,bad=False):
            nonlocal cases
            initial=Machine();before=initial.snapshot();scratch=(c.c_uint32*128)();saved=Saved()
            if kind=='store':machine=initial
            else:
                assert store(scratch,0x40000,c.byref(saved),cap,len(cap),initial.read,initial.write,initial.transfer,initial.wait)==1
                assert not initial.errors and initial.snapshot()==before
                machine=Machine(4560);machine.cart=initial.cart.copy();machine.status=0x3001
            advanced=machine.snapshot();machine.fail=fail;machine.corrupt=corrupt;machine.wait_fault=wait_fault
            if bad:machine.pc=0x3c0
            args=[scratch,0x40000,c.byref(saved),cap,len(cap)]
            if kind=='load':args+=[res,len(res)]
            actual=(store if kind=='store' else load)(*args,machine.read,machine.write,machine.transfer,machine.wait)
            assert not machine.errors,machine.errors
            cutoff=48 if kind=='store' else 18
            expected=0 if bad or 0<fail<=cutoff or 0<corrupt<=cutoff else 2 if fail or corrupt or wait_fault else 1
            assert actual==expected,(kind,fail,corrupt,wait_fault,actual,expected,machine.calls)
            if actual==0:assert not machine.writes and machine.snapshot()==advanced
            if actual==1:assert machine.snapshot()==before and machine.pc==0x3c
            cases+=1;return machine.trace,machine.waits
        for kind in ('store','load'):
            trace,waits=run(kind)
            for position,_,to_cart in trace:
                run(kind,fail=position)
                if not to_cart:run(kind,corrupt=position)
            for position in range(1,waits+1):run(kind,wait_fault=position)
            run(kind,bad=True)
        result=dict(passed=True,cases=cases,production_C_actual_RSP=True,
            changed_context_memory_and_signals_restored=True,prevalidation_before_mutation=True,
            callback_exceptions_fail=True,complete_machine_restore=False,native_acceptance=False)
        if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        if os.name=='nt':c.windll.kernel32.FreeLibrary(c.c_void_p(lib._handle))
if __name__=='__main__':main()
