#!/usr/bin/env python3
"""Full private envelope store/load, odd owner extents and failed commits."""
import argparse,ctypes as c,json,os,random,struct,subprocess,tempfile,zlib
from pathlib import Path
Byte=c.POINTER(c.c_ubyte)
Block=c.CFUNCTYPE(c.c_int,c.c_uint32,Byte,c.c_int)
IO=c.CFUNCTYPE(c.c_int,c.c_uint,c.c_uint32,c.c_uint,Byte,c.c_int)
class Work(c.Structure):
    _fields_=[('bytes',c.c_uint32),('stage',c.c_uint32),('block',c.c_ubyte*512),('piece',c.c_ubyte*512)]
class Binding(c.Structure):_fields_=[(x,c.c_uint32) for x in ('rom','code','layout','config')]
class Owner(c.Structure):_fields_=[('id',c.c_uint32),('bytes',c.c_uint32)]
class Progress(c.Structure):_fields_=[('guest',c.c_uint32),('render',c.c_uint32)]
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cc',default=os.environ.get('CC','gcc'))
    ap.add_argument('--output',type=Path);a=ap.parse_args();root=Path(__file__).resolve().parents[1];cases=0
    with tempfile.TemporaryDirectory(prefix='s64-slot-') as directory:
        dll=Path(directory)/('slot.dll' if os.name=='nt' else 'slot.so')
        cmd=[a.cc,'-O2','-std=c11','-shared','-Wall','-Wextra','-Werror']
        cmd+=['-Wl,--export-all-symbols'] if os.name=='nt' else ['-fPIC']
        subprocess.run(cmd+[str(root/'src/scene_slot.c'),str(root/'src/scene_state_format.c'),'-o',str(dll)],check=True)
        lib=c.CDLL(str(dll));store=lib.scene_slot_store;load=lib.scene_slot_load
        base=[c.POINTER(Work),Block,IO,c.POINTER(Binding),c.POINTER(Owner),c.c_uint]
        store.argtypes=base+[Progress];load.argtypes=base+[c.POINTER(Progress)]
        store.restype=load.restype=c.c_int
        def test(seed=600,fail=0,owner_fail=0,corrupt=None,bad_binding=None,write_corruption=False):
            nonlocal cases
            rng=random.Random(seed);sizes=[7,513,100,1025,32]
            if seed!=600:sizes=[rng.randrange(1,2001) for _ in range(rng.randrange(1,30))]
            owners=(Owner*len(sizes))(*(Owner(i+1,n) for i,n in enumerate(sizes)))
            original=[rng.randbytes(n) for n in sizes];machine=[bytearray(x) for x in original]
            cart=bytearray(64+12*len(sizes)+sum(sizes)+512);errors=[];calls=changes=io_calls=0;trace=[]
            @Block
            def block(offset,buffer,write):
                nonlocal calls
                try:
                    calls+=1;trace.append((calls,offset,write,changes))
                    assert offset%512==0 and offset+512<=len(cart)
                    if calls==fail:return 0
                    if write:cart[offset:offset+512]=c.string_at(buffer,512)
                    else:c.memmove(buffer,bytes(cart[offset:offset+512]),512)
                    return 1
                except Exception as e:errors.append(e);return 0
            @IO
            def io(owner,offset,n,buffer,write):
                nonlocal changes,io_calls
                try:
                    io_calls+=1
                    assert owner<len(machine) and offset+n<=len(machine[owner])
                    if io_calls==owner_fail:return 0
                    if write:
                        changes+=1;machine[owner][offset:offset+n]=c.string_at(buffer,n)
                        if write_corruption:machine[owner][offset]^=1
                    else:c.memmove(buffer,bytes(machine[owner][offset:offset+n]),n)
                    return 1
                except Exception as e:errors.append(e);return 0
            work=Work();binding=Binding(1,2,3,4)
            # Faults below apply only to load; save must first close its readback.
            pending=(fail,owner_fail);fail=owner_fail=0
            assert store(c.byref(work),block,io,c.byref(binding),owners,len(sizes),Progress(600,600))==1
            assert not errors and [bytes(x) for x in machine]==original
            data=bytes(cart[:work.bytes]);header=struct.unpack_from('>16I',data)
            assert header[:5]==(0x53363453,1,64,len(sizes),sum(sizes))
            assert header[11]==zlib.crc32(data[64:])
            normalized=bytearray(data[:64]);normalized[48:52]=b'\0'*4
            assert header[12]==zlib.crc32(normalized)
            machine=[bytearray(rng.randbytes(n)) for n in sizes];advanced=[bytes(x) for x in machine]
            if corrupt is not None:cart[corrupt%work.bytes]^=1
            if bad_binding is not None:setattr(binding,bad_binding,99)
            calls=changes=io_calls=0;trace=[];fail,owner_fail=pending
            output=Progress(900,900)
            result=load(c.byref(work),block,io,c.byref(binding),owners,len(sizes),c.byref(output))
            assert not errors,errors
            if fail or corrupt is not None or bad_binding is not None:
                assert result in (0,2)
                if result==0:assert not changes and [bytes(x) for x in machine]==advanced
            elif owner_fail or write_corruption:assert result==2
            else:
                assert result==1 and [bytes(x) for x in machine]==original
                assert (output.guest,output.render)==(600,600)
            if result!=1:assert (output.guest,output.render)==(900,900)
            cases+=1;return trace,io_calls,work.bytes
        trace,io_calls,bytes_=test()
        for position,_,_,_ in trace:test(fail=position)
        for position in range(1,io_calls+1):test(owner_fail=position)
        for offset in range(bytes_):test(corrupt=offset)
        for key in ('rom','code','layout','config'):test(bad_binding=key)
        test(write_corruption=True)
        for seed in range(50):test(seed=seed)
        result=dict(passed=True,cases=cases,production_C_envelope_and_transaction=True,
            odd_extents_cross_512_blocks=True,advanced_memory_restored=True,
            all_bytes_corruption_rejected_before_mutation=True,destination_readback_verified=True,
            callback_exceptions_fail=True,native_acceptance=False)
        if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        if os.name=='nt':c.windll.kernel32.FreeLibrary(c.c_void_p(lib._handle))
if __name__=='__main__':main()
